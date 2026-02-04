from __future__ import annotations

import json
from datetime import datetime
from urllib.parse import quote_plus
from sqlalchemy.orm import Session
from sqlalchemy import select, func, text

from app.models import (
    User, Company, UserCompany, Task, TaskStatus,
    TaskCategory, Patient,
    AuditLog, AuditAction, Role,
    PushSubscription,
)
from app.security import hash_password, random_temp_password


def maps_url_from_address(address: str) -> str:
    addr = (address or "").strip()
    if not addr:
        return ""
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(addr)}"

def log(db: Session, *, actor_user_id: int | None, action: AuditAction, ip: str = "", user_agent: str = "",
        target_user_id: int | None = None, company_id: int | None = None, task_id: int | None = None, meta: dict | None = None):
    entry = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        target_user_id=target_user_id,
        company_id=company_id,
        task_id=task_id,
        ip=ip,
        user_agent=user_agent[:300],
        meta=json.dumps(meta or {}),
    )
    db.add(entry)

def ensure_company_slugs(db: Session, slugs: list[str]) -> list[Company]:
    if not slugs:
        return []
    rows = db.execute(select(Company).where(Company.slug.in_(slugs))).scalars().all()
    found = {c.slug for c in rows}
    missing = [s for s in slugs if s not in found]
    if missing:
        raise ValueError(f"Unknown company slugs: {missing}")
    return rows

def set_user_companies(db: Session, user: User, companies: list[Company]):
    # Replace set (safe against duplicates)
    ids = sorted({c.id for c in companies})
    db.query(UserCompany).filter(UserCompany.user_id == user.id).delete(synchronize_session=False)
    db.add_all([UserCompany(user_id=user.id, company_id=cid) for cid in ids])
    db.flush()

def create_user(db: Session, *, username: str, display_name: str, mattermost_id: str, role: Role, password: str, company_slugs: list[str],
                actor_user_id: int | None, ip: str, user_agent: str) -> User:
    u = User(username=username, display_name=display_name, mattermost_id=(mattermost_id or "").strip(), role=role, password_hash=hash_password(password))
    db.add(u)
    db.flush()  # get u.id
    companies = ensure_company_slugs(db, company_slugs)
    set_user_companies(db, u, companies)
    log(db, actor_user_id=actor_user_id, action=AuditAction.CREATE_USER, target_user_id=u.id, ip=ip, user_agent=user_agent)
    for c in companies:
        log(db, actor_user_id=actor_user_id, action=AuditAction.ASSIGN_COMPANY, target_user_id=u.id, company_id=c.id, ip=ip, user_agent=user_agent)
    return u



def update_user_mattermost_id(db: Session, *, target_user: User, mattermost_id: str):
    """Set/clear the user's Mattermost user identifier for future integrations."""
    target_user.mattermost_id = (mattermost_id or "").strip()

def reset_password(db: Session, *, target_user: User, actor_user: User, ip: str, user_agent: str) -> str:
    # Cannot reset super_admin password via API.
    if target_user.role == Role.super_admin:
        raise PermissionError("Cannot reset super_admin password via UI/API.")
    temp = random_temp_password()
    target_user.password_hash = hash_password(temp)
    target_user.must_change_password = True
    log(db, actor_user_id=actor_user.id, action=AuditAction.RESET_PASSWORD, target_user_id=target_user.id, ip=ip, user_agent=user_agent)
    return temp

def set_role(db: Session, *, target_user: User, new_role: Role, actor_user: User, ip: str, user_agent: str):
    if target_user.role == Role.super_admin:
        # don't allow changing super_admin role in MVP (DB-only)
        raise PermissionError("Cannot change super_admin via UI/API.")
    if new_role == Role.super_admin:
        if actor_user.role != Role.super_admin:
            raise PermissionError("Only super_admin can assign super_admin.")
    if new_role == Role.admin and actor_user.role not in (Role.admin, Role.super_admin):
        raise PermissionError("Only admin can assign admin.")
    target_user.role = new_role
    log(db, actor_user_id=actor_user.id, action=AuditAction.SET_ROLE, target_user_id=target_user.id, ip=ip, user_agent=user_agent,
        meta={"new_role": new_role.value})

def disable_user(db: Session, *, target_user: User, disabled: bool, actor_user: User, ip: str, user_agent: str):
    if target_user.role == Role.super_admin:
        raise PermissionError("Cannot disable super_admin via UI/API.")
    target_user.disabled = disabled
    log(db, actor_user_id=actor_user.id, action=AuditAction.DISABLE_USER, target_user_id=target_user.id, ip=ip, user_agent=user_agent,
        meta={"disabled": disabled})

def upsert_company(db: Session, *, slug: str, name: str, actor_user: User, ip: str, user_agent: str) -> Company:
    c = db.execute(select(Company).where(Company.slug == slug)).scalar_one_or_none()
    if c:
        c.name = name
    else:
        c = Company(slug=slug, name=name)
        db.add(c)
        db.flush()
        # Default categories for a new company
        defaults = [
            ("visits", 10),
            ("office", 20),
            ("notes", 30),
            ("general", 40),
        ]
        for n, order in defaults:
            db.add(TaskCategory(company_id=c.id, name=n, sort_order=order, active=True))
    return c

def create_tasks_bulk(
    db: Session,
    *,
    company: Company,
    assignee_ids: list[int],
    task_date,
    task_time,
    category: str,
    title: str,
    maps_url: str,
    patient_id: int | None,
    patient_name: str,
    patient_address: str,
    patient_phone: str,
    bonus_details: str,
    actor_user: User,
    ip: str,
    user_agent: str,
) -> list[Task]:
    # validate assignees exist
    users = db.execute(select(User).where(User.id.in_(assignee_ids))).scalars().all()
    found = {u.id for u in users}
    missing = [uid for uid in assignee_ids if uid not in found]
    if missing:
        raise ValueError(f"Unknown user ids: {missing}")

    # Validate category exists for the company (active or inactive allowed; admin may create tasks under inactive in edge cases)
    cat = db.execute(
        select(TaskCategory).where(TaskCategory.company_id == company.id, TaskCategory.name == category)
    ).scalar_one_or_none()
    if not cat:
        raise ValueError(f"Unknown category '{category}' for company '{company.slug}'. Create it first.")

    # Patient lookup (optional) + snapshot
    p: Patient | None = None
    if patient_id is not None:
        p = db.get(Patient, patient_id)
        if not p or p.company_id != company.id or not p.active:
            raise ValueError("Invalid patient for company")
        patient_name = p.name
        patient_address = p.address
        patient_phone = p.phone
        if not maps_url:
            maps_url = p.maps_url or maps_url_from_address(p.address)

    if not maps_url and patient_address:
        maps_url = maps_url_from_address(patient_address)

    created: list[Task] = []
    for uid in assignee_ids:
        t = Task(
            company_id=company.id,
            assigned_user_id=uid,
            category=category,
            task_date=task_date,
            task_time=task_time,
            title=title,
            maps_url=maps_url,
            patient_id=p.id if p else patient_id,
            patient_name=patient_name,
            patient_address=patient_address,
            patient_phone=patient_phone,
            bonus_details=bonus_details,
        )
        num = db.execute(text("select nextval('task_num_seq')")).scalar_one()
        t.task_num = int(num)
        t.task_code = f"T{t.task_num:06d}"
        db.add(t)
        db.flush()
        created.append(t)
        log(db, actor_user_id=actor_user.id, action=AuditAction.CREATE_TASK, target_user_id=uid, company_id=company.id, task_id=t.id,
            ip=ip, user_agent=user_agent, meta={"task_code": t.task_code, "category": category})
    return created

def tasks_due_count_for_user_company(db: Session, user_id: int, company_id: int, today) -> int:
    q = select(func.count(Task.id)).where(
        Task.assigned_user_id == user_id,
        Task.company_id == company_id,
        Task.status == TaskStatus.todo,
        Task.task_date <= today,
        Task.deleted_at.is_(None),
    )
    return int(db.execute(q).scalar_one())

def list_tasks_for_user_company(db: Session, user_id: int, company_id: int, today, days_ahead: int = 7) -> list[Task]:
    # show tasks from today-2 through today+days_ahead
    from datetime import timedelta
    start = today - timedelta(days=2)
    end = today + timedelta(days=days_ahead)
    q = select(Task).where(
        Task.assigned_user_id == user_id,
        Task.company_id == company_id,
        Task.task_date.between(start, end),
        Task.deleted_at.is_(None),
    ).order_by(Task.task_date.asc(), Task.task_time.asc().nulls_last(), Task.category.asc(), Task.task_num.asc())
    return db.execute(q).scalars().all()



def list_tasks_for_company(db: Session, company_id: int, today, days_ahead: int = 14, include_deleted: bool = False) -> list[Task]:
    # show tasks from today-7 through today+days_ahead
    from datetime import timedelta
    start = today - timedelta(days=7)
    end = today + timedelta(days=days_ahead)
    clauses = [
        Task.company_id == company_id,
        Task.task_date.between(start, end),
    ]
    if not include_deleted:
        clauses.append(Task.deleted_at.is_(None))
    q = select(Task).where(*clauses).order_by(Task.task_date.asc(), Task.task_time.asc().nulls_last(), Task.category.asc(), Task.task_num.asc())
    return db.execute(q).scalars().all()



def get_task_by_code(db: Session, task_code: str) -> Task | None:
    from app.utils import parse_task_code
    num = parse_task_code(task_code)
    if num is None:
        return None
    return db.execute(select(Task).where(Task.task_num == num)).scalar_one_or_none()


def soft_delete_task(db: Session, task: Task, *, actor_user: User):
    from datetime import datetime as _dt
    task.deleted_at = _dt.utcnow()
    task.deleted_by_user_id = actor_user.id



def force_done_task(db: Session, task: Task, *, actor_user: User, done: bool):
    from datetime import datetime as _dt
    if done:
        task.status = TaskStatus.done
        task.completed_at = _dt.utcnow()
        task.forced_done_at = _dt.utcnow()
        task.forced_done_by_user_id = actor_user.id
    else:
        task.status = TaskStatus.todo
        task.completed_at = None
        task.forced_done_at = None
        task.forced_done_by_user_id = None


# ---------------- Admin: categories ----------------

def list_categories(db: Session, company_id: int) -> list[TaskCategory]:
    q = select(TaskCategory).where(TaskCategory.company_id == company_id).order_by(TaskCategory.sort_order.asc(), TaskCategory.name.asc())
    return db.execute(q).scalars().all()


def create_category(db: Session, *, company: Company, name: str, sort_order: int = 0) -> TaskCategory:
    c = TaskCategory(company_id=company.id, name=name.strip(), sort_order=sort_order)
    db.add(c)
    return c


def set_category_active(db: Session, *, category: TaskCategory, active: bool):
    category.active = active


# ---------------- Admin: patients ----------------

def list_patients(db: Session, company_id: int, include_inactive: bool = False) -> list[Patient]:
    q = select(Patient).where(Patient.company_id == company_id)
    if not include_inactive:
        q = q.where(Patient.active == True)
    q = q.order_by(Patient.name.asc())
    return db.execute(q).scalars().all()


def create_patient(
    db: Session,
    *,
    company: Company,
    name: str,
    phone: str = "",
    address: str = "",
    maps_url: str = "",
    notes: str = "",
) -> Patient:
    if not maps_url and address:
        maps_url = maps_url_from_address(address)
    p = Patient(company_id=company.id, name=name.strip(), phone=phone.strip(), address=address.strip(), maps_url=maps_url.strip(), notes=notes)
    db.add(p)
    return p


def update_patient(
    db: Session,
    *,
    patient: Patient,
    name: str,
    phone: str,
    address: str,
    maps_url: str,
    notes: str,
    active: bool,
):
    patient.name = name.strip()
    patient.phone = (phone or "").strip()
    patient.address = (address or "").strip()
    patient.maps_url = (maps_url or "").strip() or (maps_url_from_address(address) if address else "")
    patient.notes = notes or ""
    patient.active = bool(active)


# ---------------- Web Push (subscriptions) ----------------

def upsert_push_subscription(
    db: Session,
    *,
    user: User,
    endpoint: str,
    p256dh: str,
    auth: str,
    user_agent: str = "",
) -> PushSubscription:
    endpoint = (endpoint or "").strip()
    p256dh = (p256dh or "").strip()
    auth = (auth or "").strip()

    if not endpoint or not p256dh or not auth:
        raise ValueError("Invalid push subscription")

    existing = db.execute(
        select(PushSubscription).where(PushSubscription.user_id == user.id, PushSubscription.endpoint == endpoint)
    ).scalar_one_or_none()

    now = datetime.utcnow()
    if existing:
        existing.p256dh = p256dh
        existing.auth = auth
        existing.user_agent = (user_agent or "")[:300]
        existing.active = True
        existing.updated_at = now
        return existing

    sub = PushSubscription(
        user_id=user.id,
        endpoint=endpoint,
        p256dh=p256dh,
        auth=auth,
        user_agent=(user_agent or "")[:300],
        active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(sub)
    return sub


def deactivate_push_subscription(db: Session, *, user: User, endpoint: str) -> bool:
    endpoint = (endpoint or "").strip()
    if not endpoint:
        return False
    sub = db.execute(
        select(PushSubscription).where(PushSubscription.user_id == user.id, PushSubscription.endpoint == endpoint)
    ).scalar_one_or_none()
    if not sub:
        return False
    sub.active = False
    sub.updated_at = datetime.utcnow()
    return True


def list_active_push_subscriptions(db: Session, *, user_id: int) -> list[PushSubscription]:
    q = select(PushSubscription).where(PushSubscription.user_id == user_id, PushSubscription.active == True)
    return db.execute(q).scalars().all()
