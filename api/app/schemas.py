from __future__ import annotations
from datetime import date, datetime, time
from pydantic import BaseModel, Field

class MeOut(BaseModel):
    id: int
    username: str
    display_name: str
    role: str
    must_change_password: bool
    disabled: bool


# ---------------- Web Push ----------------

class PushSubscribeIn(BaseModel):
    endpoint: str
    keys: dict

class PushUnsubscribeIn(BaseModel):
    endpoint: str

class PushPublicKeyOut(BaseModel):
    public_key: str

class LoginIn(BaseModel):
    username: str
    password: str

class LoginOut(BaseModel):
    ok: bool

class ChangePasswordIn(BaseModel):
    new_password: str = Field(min_length=10, max_length=200)

class CompanyOut(BaseModel):
    slug: str
    name: str
    has_attention: bool = False
    due_count: int = 0

class TaskListItem(BaseModel):
    task_code: str
    title: str
    category: str
    task_date: date
    task_time: time | None = None
    status: str

class TaskDetailOut(BaseModel):
    task_code: str
    company_slug: str
    company_name: str
    title: str
    category: str
    task_date: date
    task_time: time | None = None
    maps_url: str
    patient_name: str = ""
    patient_address: str
    patient_phone: str
    bonus_details: str
    status: str
    completed_at: datetime | None = None

class MarkDoneIn(BaseModel):
    done: bool

# Admin
class AdminCreateUserIn(BaseModel):
    username: str
    display_name: str = ""
    mattermost_id: str = ""
    role: str = "employee"
    password: str = Field(min_length=10, max_length=200)
    company_slugs: list[str] = []

class AdminUserOut(BaseModel):
    id: int
    username: str
    display_name: str
    mattermost_id: str = ""
    role: str
    disabled: bool

class AdminResetPasswordOut(BaseModel):
    temp_password: str

class AdminDisableUserIn(BaseModel):
    disabled: bool

class AdminSetRoleIn(BaseModel):
    role: str

class AdminUpdateUserIn(BaseModel):
    display_name: str | None = None
    mattermost_id: str | None = None

class AdminCompanyIn(BaseModel):
    slug: str
    name: str

class AdminTaskBulkCreateIn(BaseModel):
    company_slug: str
    assignee_user_ids: list[int]
    task_date: date
    task_time: time | None = None
    category: str = "general"  # must be a category defined for the company
    title: str
    maps_url: str = ""
    patient_id: int | None = None
    patient_name: str = ""
    patient_address: str = ""
    patient_phone: str = ""
    bonus_details: str = ""


class AdminCompanyOut(BaseModel):
    id: int
    slug: str
    name: str


class AdminUserDetailOut(BaseModel):
    id: int
    username: str
    display_name: str
    mattermost_id: str = ""
    role: str
    disabled: bool
    company_slugs: list[str] = []


class CategoryOut(BaseModel):
    id: int
    name: str
    sort_order: int
    active: bool


class CategoryIn(BaseModel):
    name: str
    sort_order: int = 0


class PatientOut(BaseModel):
    id: int
    name: str
    phone: str
    address: str
    maps_url: str
    notes: str
    active: bool


class PatientIn(BaseModel):
    name: str
    phone: str = ""
    address: str = ""
    maps_url: str = ""
    notes: str = ""

class AdminTaskBulkCreateOut(BaseModel):
    created: list[str]  # task codes

# Stats
class AuditLogOut(BaseModel):
    timestamp: datetime
    actor_user_id: int | None
    action: str
    target_user_id: int | None
    company_id: int | None
    task_id: int | None
    ip: str
    user_agent: str
