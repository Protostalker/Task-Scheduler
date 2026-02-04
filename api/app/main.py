from __future__ import annotations

from datetime import date, datetime
import os

import json
import redis as redis_lib

from fastapi import FastAPI, Depends, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.settings import settings
from app.db.session import get_db
from app.deps import get_current_user, require_admin, require_super_admin, COOKIE_NAME
from app.security import verify_password, create_token, client_ip, hash_password
from app import schemas
from app import crud
from app.models import User, Company, UserCompany, Task, TaskStatus, Role, AuditLog, AuditAction, TaskCategory, Patient
from app.utils import parse_task_code
from app.bootstrap import bootstrap_superadmin

app = FastAPI(title="TaskFlow API", version="0.1.0")


def _redis() -> redis_lib.Redis:
    return redis_lib.Redis.from_url(settings.redis_url, decode_responses=True)


def enqueue_push_for_user(*, db: Session, user_id: int, title: str, body: str, url: str, request: Request | None = None):
    """Enqueue a Web Push job for all active subscriptions of the given user.

    The push-worker container consumes the Redis list and performs the signed Web Push send.
    Payload MUST NOT contain PHI.
    """
    if not settings.vapid_public_key or not settings.vapid_private_key:
        return

    subs = crud.list_active_push_subscriptions(db, user_id=user_id)
    if not subs:
        return

    payload = {
        "notification": {
            "title": title,
            "body": body,
            "url": url,
        }
    }

    r = _redis()
    for s in subs:
        job = {
            "subscription": {
                "endpoint": s.endpoint,
                "keys": {"p256dh": s.p256dh, "auth": s.auth},
            },
            "payload": payload,
        }
        r.rpush(settings.push_queue_key, json.dumps(job))

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def _startup():
    # Create bootstrap superadmin if none exists
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        bootstrap_superadmin(db, username=settings.bootstrap_root_username, write_path=settings.bootstrap_write_path)
    finally:
        db.close()

@app.get("/api/health")
def health():
    return {"ok": True}

def set_cookie(response: Response, token: str):
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=bool(settings.cookie_secure),
        samesite="lax",
        domain=settings.cookie_domain or None,
                max_age=90 * 24 * 60 * 60,  # 90 days (≈3 months)
        path="/",
    )

def clear_cookie(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/", domain=settings.cookie_domain or None)

@app.post("/api/auth/login", response_model=schemas.LoginOut)
def login(payload: schemas.LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.username == payload.username)).scalar_one_or_none()
    if not user or user.disabled or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user.id, user.role.value)
    set_cookie(response, token)
    user.last_login_at = datetime.utcnow()
    crud.log(db, actor_user_id=user.id, action=AuditAction.LOGIN, ip=client_ip(request), user_agent=request.headers.get("user-agent",""))
    db.commit()
    return {"ok": True}

@app.post("/api/auth/logout", response_model=schemas.LoginOut)
def logout(request: Request, response: Response, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    clear_cookie(response)
    crud.log(db, actor_user_id=user.id, action=AuditAction.LOGOUT, ip=client_ip(request), user_agent=request.headers.get("user-agent",""))
    db.commit()
    return {"ok": True}

@app.get("/api/me", response_model=schemas.MeOut)
def me(user: User = Depends(get_current_user)):
    return schemas.MeOut(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        role=user.role.value,
        must_change_password=user.must_change_password,
        disabled=user.disabled,
    )


# ---------------- Web Push (browser push notifications) ----------------

@app.get("/api/push/public_key", response_model=schemas.PushPublicKeyOut)
def push_public_key(user: User = Depends(get_current_user)):
    # Safe to expose public key to authenticated clients.
    return {"public_key": settings.vapid_public_key or ""}


@app.post("/api/push/subscribe")
def push_subscribe(payload: schemas.PushSubscribeIn, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    keys = payload.keys or {}
    p256dh = str(keys.get("p256dh", ""))
    auth = str(keys.get("auth", ""))
    try:
        crud.upsert_push_subscription(
            db,
            user=user,
            endpoint=payload.endpoint,
            p256dh=p256dh,
            auth=auth,
            user_agent=request.headers.get("user-agent", ""),
        )
        db.commit()
        return {"ok": True}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/push/unsubscribe")
def push_unsubscribe(payload: schemas.PushUnsubscribeIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ok = crud.deactivate_push_subscription(db, user=user, endpoint=payload.endpoint)
    db.commit()
    return {"ok": ok}

@app.post("/api/push/test")
def push_test(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Send a test Web Push notification to the current user.

    This is safe (no PHI) and helps users verify browser permission + subscription.
    """
    try:
        base_url = os.environ.get("APP_BASE_URL", "")
        url = f"{base_url.rstrip('/')}/" if base_url else "/"
        enqueue_push_for_user(
            db=db,
            user_id=user.id,
            title="Salkhorian Design Task Scheduler",
            body="Test notification: you're all set.",
            url=url,
            request=request,
        )
    except Exception:
        # Never fail due to notifications.
        pass
    return {"ok": True}


@app.post("/api/auth/change_password")
def change_password(payload: schemas.ChangePasswordIn, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # super_admin password changes are DB-only in this MVP.
    if user.role == Role.super_admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    user.password_hash = hash_password(payload.new_password)
    user.must_change_password = False
    crud.log(db, actor_user_id=user.id, action=AuditAction.CHANGE_PASSWORD, ip=client_ip(request), user_agent=request.headers.get("user-agent",""))
    db.commit()
    return {"ok": True}

# Employee: companies list with attention
@app.get("/api/companies", response_model=list[schemas.CompanyOut])
def my_companies(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role in (Role.admin, Role.super_admin):
        comps = db.execute(select(Company).where(Company.active == True).order_by(Company.name.asc())).scalars().all()
        out = []
        today = date.today()
        for c in comps:
            cnt = crud.tasks_due_count_for_user_company(db, user.id, c.id, today) if user.role == Role.admin else 0
            out.append(schemas.CompanyOut(slug=c.slug, name=c.name, has_attention=cnt > 0, due_count=cnt))
        return out

    today = date.today()
    links = db.execute(select(UserCompany).where(UserCompany.user_id == user.id)).scalars().all()
    out = []
    for uc in links:
        c = db.get(Company, uc.company_id)
        if not c or not c.active:
            continue
        cnt = crud.tasks_due_count_for_user_company(db, user.id, c.id, today)
        out.append(schemas.CompanyOut(slug=c.slug, name=c.name, has_attention=cnt > 0, due_count=cnt))
    return out

# Employee: list tasks for a company (grouped in UI, returned flat)
@app.get("/api/company/{company_slug}/tasks", response_model=list[schemas.TaskListItem])
def list_tasks(company_slug: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    company = db.execute(select(Company).where(Company.slug == company_slug)).scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Not found")

    today = date.today()

    if user.role in (Role.admin, Role.super_admin):
        # Admin view: show all tasks for the company
        tasks = crud.list_tasks_for_company(db, company.id, today)
    else:
        # Ensure user is assigned to company
        link = db.execute(select(UserCompany).where(UserCompany.user_id == user.id, UserCompany.company_id == company.id)).scalar_one_or_none()
        if not link:
            raise HTTPException(status_code=403, detail="Forbidden")
        tasks = crud.list_tasks_for_user_company(db, user.id, company.id, today)

    return [schemas.TaskListItem(task_code=t.task_code, title=t.title, category=t.category, task_date=t.task_date, task_time=t.task_time, status=t.status.value) for t in tasks]

@app.get("/api/company/{company_slug}/tasks/{task_code}", response_model=schemas.TaskDetailOut)
def task_detail(company_slug: str, task_code: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    company = db.execute(select(Company).where(Company.slug == company_slug)).scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Not found")

    num = parse_task_code(task_code)
    if num is None:
        raise HTTPException(status_code=404, detail="Not found")

    task = db.execute(select(Task).where(Task.task_num == num)).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Not found")

    if task.company_id != company.id:
        raise HTTPException(status_code=404, detail="Not found")

    if user.role not in (Role.admin, Role.super_admin):
        if task.assigned_user_id != user.id:
            raise HTTPException(status_code=403, detail="Forbidden")
        link_ctx = db.execute(select(UserCompany).where(UserCompany.user_id == user.id, UserCompany.company_id == company.id)).scalar_one_or_none()
        if not link_ctx:
            raise HTTPException(status_code=403, detail="Forbidden")

    return schemas.TaskDetailOut(
        task_code=task.task_code,
        company_slug=company.slug,
        company_name=company.name,
        title=task.title,
        category=task.category,
        task_date=task.task_date,
        task_time=task.task_time,
        maps_url=task.maps_url,
        patient_name=task.patient_name,
        patient_address=task.patient_address,
        patient_phone=task.patient_phone,
        bonus_details=task.bonus_details,
        status=task.status.value,
        completed_at=task.completed_at,
    )

@app.post("/api/company/{company_slug}/tasks/{task_code}/done")
def mark_done(company_slug: str, task_code: str, payload: schemas.MarkDoneIn, request: Request,
              user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    company = db.execute(select(Company).where(Company.slug == company_slug)).scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Not found")

    num = parse_task_code(task_code)
    if num is None:
        raise HTTPException(status_code=404, detail="Not found")

    task = db.execute(select(Task).where(Task.task_num == num)).scalar_one_or_none()
    if not task or task.company_id != company.id:
        raise HTTPException(status_code=404, detail="Not found")

    # Only assigned user can mark their task
    if user.role in (Role.admin, Role.super_admin):
        # allow admins to mark for testing if they are the assignee
        if task.assigned_user_id != user.id:
            raise HTTPException(status_code=403, detail="Forbidden")
    else:
        if task.assigned_user_id != user.id:
            raise HTTPException(status_code=403, detail="Forbidden")

    if payload.done:
        task.status = TaskStatus.done
        task.completed_at = datetime.utcnow()
        crud.log(db, actor_user_id=user.id, action=AuditAction.COMPLETE_TASK, company_id=company.id, task_id=task.id,
                 ip=client_ip(request), user_agent=request.headers.get("user-agent",""), meta={"task_code": task.task_code})
    else:
        task.status = TaskStatus.todo
        task.completed_at = None
        crud.log(db, actor_user_id=user.id, action=AuditAction.UNCOMPLETE_TASK, company_id=company.id, task_id=task.id,
                 ip=client_ip(request), user_agent=request.headers.get("user-agent",""), meta={"task_code": task.task_code})
    db.commit()
    return {"ok": True}

# ---------------- Admin APIs ----------------

@app.post("/api/admin/companies")
def admin_create_company(payload: schemas.AdminCompanyIn, request: Request, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    c = crud.upsert_company(db, slug=payload.slug, name=payload.name, actor_user=admin, ip=client_ip(request), user_agent=request.headers.get("user-agent",""))
    db.commit()
    return {"ok": True, "company": {"slug": c.slug, "name": c.name}}

@app.get("/api/admin/users", response_model=list[schemas.AdminUserOut])
def admin_list_users(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.execute(select(User).order_by(User.id.asc())).scalars().all()
    return [schemas.AdminUserOut(id=u.id, username=u.username, display_name=u.display_name, mattermost_id=u.mattermost_id or "", role=u.role.value, disabled=u.disabled) for u in users]


@app.get("/api/admin/companies", response_model=list[schemas.AdminCompanyOut])
def admin_list_companies(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    comps = db.execute(select(Company).order_by(Company.name.asc())).scalars().all()
    return [schemas.AdminCompanyOut(id=c.id, slug=c.slug, name=c.name) for c in comps]


@app.get("/api/admin/users/{user_id}", response_model=schemas.AdminUserDetailOut)
def admin_user_detail(user_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="Not found")
    # company slugs
    links = db.execute(select(UserCompany).where(UserCompany.user_id == u.id)).scalars().all()
    slugs: list[str] = []
    for link in links:
        c = db.get(Company, link.company_id)
        if c:
            slugs.append(c.slug)
    return schemas.AdminUserDetailOut(
        id=u.id,
        username=u.username,
        display_name=u.display_name,
        mattermost_id=u.mattermost_id or "",
        role=u.role.value,
        disabled=u.disabled,
        company_slugs=sorted(set(slugs)),
    )

@app.post("/api/admin/users", response_model=schemas.AdminUserOut)
def admin_create_user(payload: schemas.AdminCreateUserIn, request: Request, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    # Only super_admin can create super_admin
    if payload.role == Role.super_admin.value and admin.role != Role.super_admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    role = Role(payload.role)
    try:
        u = crud.create_user(
            db,
            username=payload.username,
            display_name=payload.display_name,
            mattermost_id=payload.mattermost_id,
            role=role,
            password=payload.password,
            company_slugs=payload.company_slugs,
            actor_user_id=admin.id,
            ip=client_ip(request),
            user_agent=request.headers.get("user-agent",""),
        )
        db.commit()
        return schemas.AdminUserOut(id=u.id, username=u.username, display_name=u.display_name, mattermost_id=u.mattermost_id or "", role=u.role.value, disabled=u.disabled)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/admin/users/{user_id}/reset_password", response_model=schemas.AdminResetPasswordOut)
def admin_reset_password(user_id: int, request: Request, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        temp = crud.reset_password(db, target_user=target, actor_user=admin, ip=client_ip(request), user_agent=request.headers.get("user-agent",""))
        db.commit()
        return {"temp_password": temp}
    except PermissionError:
        raise HTTPException(status_code=403, detail="Forbidden")

@app.post("/api/admin/users/{user_id}/disable")
def admin_disable(user_id: int, payload: schemas.AdminDisableUserIn, request: Request, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        crud.disable_user(db, target_user=target, disabled=payload.disabled, actor_user=admin, ip=client_ip(request), user_agent=request.headers.get("user-agent",""))
        db.commit()
        return {"ok": True}
    except PermissionError:
        raise HTTPException(status_code=403, detail="Forbidden")

@app.post("/api/admin/users/{user_id}/role")
def admin_set_role(user_id: int, payload: schemas.AdminSetRoleIn, request: Request, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        crud.set_role(db, target_user=target, new_role=Role(payload.role), actor_user=admin, ip=client_ip(request), user_agent=request.headers.get("user-agent",""))
        db.commit()
        return {"ok": True}
    except PermissionError:
        raise HTTPException(status_code=403, detail="Forbidden")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.patch("/api/admin/users/{user_id}", response_model=schemas.AdminUserOut)
def admin_update_user(user_id: int, payload: schemas.AdminUpdateUserIn, request: Request, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="Not found")
    # Minimal editable fields for integrations
    if payload.display_name is not None:
        target.display_name = payload.display_name
    if payload.mattermost_id is not None:
        crud.update_user_mattermost_id(db, target_user=target, mattermost_id=payload.mattermost_id)
    db.commit()
    db.refresh(target)
    # Must return the updated user object to satisfy response_model
    return schemas.AdminUserOut(
        id=target.id,
        username=target.username,
        display_name=target.display_name,
        mattermost_id=target.mattermost_id or "",
        role=target.role.value,
        disabled=target.disabled,
    )


@app.put("/api/admin/users/{user_id}/companies")
def admin_set_user_companies(user_id: int, payload: dict, request: Request, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="Not found")
    company_slugs = payload.get("company_slugs") or []
    companies = crud.ensure_company_slugs(db, list(company_slugs))
    crud.set_user_companies(db, target, companies)
    for c in companies:
        crud.log(db, actor_user_id=admin.id, action=AuditAction.ASSIGN_COMPANY, target_user_id=target.id, company_id=c.id,
                 ip=client_ip(request), user_agent=request.headers.get("user-agent",""))
    db.commit()
    return {"ok": True}


@app.get("/api/admin/companies/{company_slug}/categories", response_model=list[schemas.CategoryOut])
def admin_list_categories(company_slug: str, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    company = db.execute(select(Company).where(Company.slug == company_slug)).scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Not found")
    cats = crud.list_categories(db, company.id)
    return [schemas.CategoryOut(id=c.id, name=c.name, sort_order=c.sort_order, active=c.active) for c in cats]


@app.post("/api/admin/companies/{company_slug}/categories", response_model=schemas.CategoryOut)
def admin_create_category(company_slug: str, payload: schemas.CategoryIn, request: Request, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    company = db.execute(select(Company).where(Company.slug == company_slug)).scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        c = crud.create_category(db, company=company, name=payload.name, sort_order=payload.sort_order)
        db.commit()
        return schemas.CategoryOut(id=c.id, name=c.name, sort_order=c.sort_order, active=c.active)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.patch("/api/admin/categories/{category_id}")
def admin_update_category(category_id: int, payload: dict, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    c = db.get(TaskCategory, category_id)
    if not c:
        raise HTTPException(status_code=404, detail="Not found")
    if "active" in payload:
        crud.set_category_active(db, category=c, active=bool(payload["active"]))
    if "name" in payload and str(payload["name"]).strip():
        c.name = str(payload["name"]).strip()
    if "sort_order" in payload:
        c.sort_order = int(payload["sort_order"])
    db.commit()
    return {"ok": True}


@app.get("/api/admin/companies/{company_slug}/patients", response_model=list[schemas.PatientOut])
def admin_list_patients(company_slug: str, include_inactive: bool = False, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    company = db.execute(select(Company).where(Company.slug == company_slug)).scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Not found")
    pts = crud.list_patients(db, company.id, include_inactive=include_inactive)
    return [schemas.PatientOut(id=p.id, name=p.name, phone=p.phone, address=p.address, maps_url=p.maps_url, notes=p.notes, active=p.active) for p in pts]


@app.post("/api/admin/companies/{company_slug}/patients", response_model=schemas.PatientOut)
def admin_create_patient(company_slug: str, payload: schemas.PatientIn, request: Request, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    company = db.execute(select(Company).where(Company.slug == company_slug)).scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        p = crud.create_patient(db, company=company, name=payload.name, phone=payload.phone, address=payload.address, maps_url=payload.maps_url, notes=payload.notes)
        db.commit()
        return schemas.PatientOut(id=p.id, name=p.name, phone=p.phone, address=p.address, maps_url=p.maps_url, notes=p.notes, active=p.active)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.patch("/api/admin/patients/{patient_id}")
def admin_update_patient(patient_id: int, payload: dict, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    p = db.get(Patient, patient_id)
    if not p:
        raise HTTPException(status_code=404, detail="Not found")
    crud.update_patient(
        db,
        patient=p,
        name=str(payload.get("name", p.name)),
        phone=str(payload.get("phone", p.phone or "")),
        address=str(payload.get("address", p.address or "")),
        maps_url=str(payload.get("maps_url", p.maps_url or "")),
        notes=str(payload.get("notes", p.notes or "")),
        active=bool(payload.get("active", p.active)),
    )
    db.commit()
    return {"ok": True}

@app.post("/api/admin/tasks/bulk", response_model=schemas.AdminTaskBulkCreateOut)
def admin_create_tasks_bulk(payload: schemas.AdminTaskBulkCreateIn, request: Request, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    company = db.execute(select(Company).where(Company.slug == payload.company_slug)).scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        tasks = crud.create_tasks_bulk(
            db,
            company=company,
            assignee_ids=payload.assignee_user_ids,
            task_date=payload.task_date,
            task_time=payload.task_time,
            category=payload.category,
            title=payload.title,
            maps_url=payload.maps_url,
            patient_id=payload.patient_id,
            patient_name=payload.patient_name,
            patient_address=payload.patient_address,
            patient_phone=payload.patient_phone,
            bonus_details=payload.bonus_details,
            actor_user=admin,
            ip=client_ip(request),
            user_agent=request.headers.get("user-agent",""),
        )
        # Safety: v3 threshold
        if any(t.task_num >= 999999 for t in tasks):
            raise HTTPException(status_code=500, detail="Task ID limit reached; deploy v3.")
        db.commit()

        # Push notif: only the assigned user gets it. Payload is generic (no PHI).
        # We enqueue after commit so the tasks exist.
        try:
            base_url = os.environ.get("APP_BASE_URL", "")  # optional, used for absolute URL
            rel_url = f"/company/{company.slug}"
            url = f"{base_url.rstrip('/')}{rel_url}" if base_url else rel_url
            for uid in set(payload.assignee_user_ids or []):
                enqueue_push_for_user(
                    db=db,
                    user_id=int(uid),
                    title="Salkhorian Design Task Scheduler",
                    body="You've got tasks.",
                    url=url,
                    request=request,
                )
        except Exception:
            # Never fail task creation due to notifications.
            pass
        return {"created": [t.task_code for t in tasks]}
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# ---------------- Admin: task management ----------------

@app.get("/api/admin/tasks")
def admin_list_tasks(company_slug: str | None = None, include_deleted: bool = False, limit: int = 200,
                     admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    today = date.today()
    tasks: list[Task] = []
    if company_slug:
        company = db.execute(select(Company).where(Company.slug == company_slug)).scalar_one_or_none()
        if not company:
            raise HTTPException(status_code=404, detail="Not found")
        tasks = crud.list_tasks_for_company(db, company.id, today, include_deleted=include_deleted)
    else:
        # default: show recent tasks across all companies
        from datetime import timedelta
        start = today - timedelta(days=7)
        end = today + timedelta(days=14)
        q = select(Task).where(Task.task_date.between(start, end))
        if not include_deleted:
            q = q.where(Task.deleted_at.is_(None))
        q = q.order_by(Task.task_date.desc(), Task.task_num.desc()).limit(min(limit, 1000))
        tasks = db.execute(q).scalars().all()

    # hydrate company slug + assignee username
    company_ids = {t.company_id for t in tasks}
    companies = {c.id: c for c in db.execute(select(Company).where(Company.id.in_(company_ids))).scalars().all()} if company_ids else {}
    user_ids = {t.assigned_user_id for t in tasks}
    users = {u.id: u for u in db.execute(select(User).where(User.id.in_(user_ids))).scalars().all()} if user_ids else {}

    return [{
        "task_code": t.task_code,
        "task_num": t.task_num,
        "company_slug": companies.get(t.company_id).slug if companies.get(t.company_id) else "",
        "assigned_user_id": t.assigned_user_id,
        "assigned_username": users.get(t.assigned_user_id).username if users.get(t.assigned_user_id) else "",
        "task_date": t.task_date,
        "task_time": t.task_time,
        "status": t.status.value,
        "category": t.category,
        "title": t.title,
        "deleted_at": t.deleted_at,
        "forced_done_at": t.forced_done_at,
    } for t in tasks]


@app.post("/api/admin/tasks/{task_code}/force_done")
def admin_force_done_task(task_code: str, payload: dict, request: Request, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    task = crud.get_task_by_code(db, task_code)
    if not task:
        raise HTTPException(status_code=404, detail="Not found")
    done = bool(payload.get("done", True))
    crud.force_done_task(db, task, actor_user=admin, done=done)
    crud.log(db, actor_user_id=admin.id, action=AuditAction.FORCE_DONE_TASK if done else AuditAction.UNFORCE_DONE_TASK,
             company_id=task.company_id, task_id=task.id, ip=client_ip(request), user_agent=request.headers.get("user-agent",""),
             meta={"task_code": task.task_code})
    db.commit()
    return {"ok": True}


@app.delete("/api/admin/tasks/{task_code}")
def admin_delete_task(task_code: str, request: Request, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    task = crud.get_task_by_code(db, task_code)
    if not task:
        raise HTTPException(status_code=404, detail="Not found")
    if task.deleted_at is None:
        crud.soft_delete_task(db, task, actor_user=admin)
        crud.log(db, actor_user_id=admin.id, action=AuditAction.DELETE_TASK, company_id=task.company_id, task_id=task.id,
                 ip=client_ip(request), user_agent=request.headers.get("user-agent",""), meta={"task_code": task.task_code})
    db.commit()
    return {"ok": True}


# ---------------- Stats ----------------
@app.get("/api/stats/audit", response_model=list[schemas.AuditLogOut])
def stats_audit(limit: int = 200, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.execute(select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(min(limit, 1000))).scalars().all()
    return [schemas.AuditLogOut(
        timestamp=r.timestamp,
        actor_user_id=r.actor_user_id,
        action=r.action.value,
        target_user_id=r.target_user_id,
        company_id=r.company_id,
        task_id=r.task_id,
        ip=r.ip,
        user_agent=r.user_agent,
    ) for r in rows]
