from __future__ import annotations

import enum
from datetime import datetime, date, time
from sqlalchemy import (
    Boolean, Date, DateTime, Enum, ForeignKey, Integer, Sequence,
    String, Text, Time, UniqueConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class Role(str, enum.Enum):
    employee = "employee"
    admin = "admin"
    super_admin = "super_admin"

task_num_seq = Sequence("task_num_seq", start=10, increment=1)

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(190), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(190), default="")
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.employee, index=True)
    password_hash: Mapped[str] = mapped_column(String(500))
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False)
    disabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Optional: Mattermost user id / username (for future bot integrations)
    mattermost_id: Mapped[str] = mapped_column(String(190), default="", nullable=False)

    companies = relationship("UserCompany", back_populates="user", cascade="all, delete-orphan")

    push_subscriptions = relationship(
        "PushSubscription",
        back_populates="user",
        cascade="all, delete-orphan",
    )

class Company(Base):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(190))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    users = relationship("UserCompany", back_populates="company", cascade="all, delete-orphan")


class TaskCategory(Base):
    __tablename__ = "task_categories"
    __table_args__ = (
        UniqueConstraint("company_id", "name", name="uq_category_company_name"),
        Index("ix_task_categories_company_id", "company_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(80))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    company = relationship("Company")


class Patient(Base):
    __tablename__ = "patients"
    __table_args__ = (
        Index("ix_patients_company_id", "company_id"),
        Index("ix_patients_active", "active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(190))
    phone: Mapped[str] = mapped_column(String(80), default="")
    address: Mapped[str] = mapped_column(String(500), default="")
    maps_url: Mapped[str] = mapped_column(String(500), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    company = relationship("Company")

class UserCompany(Base):
    __tablename__ = "user_companies"
    __table_args__ = (UniqueConstraint("user_id", "company_id", name="uq_user_company"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))

    user = relationship("User", back_populates="companies")
    company = relationship("Company", back_populates="users")

class TaskStatus(str, enum.Enum):
    todo = "todo"
    done = "done"

class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # sequential number from db sequence, unique
    task_num: Mapped[int] = mapped_column(Integer, server_default=task_num_seq.next_value(), unique=True, index=True)

    # Human-friendly code like T000010; stored for stable URLs
    task_code: Mapped[str] = mapped_column(String(16), unique=True, index=True, nullable=False)

    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), index=True)
    assigned_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)

    # Category is a simple string in v0.6; backed by admin-defined categories per company.
    category: Mapped[str] = mapped_column(String(60), default="general", index=True)
    task_date: Mapped[date] = mapped_column(Date, index=True)
    task_time: Mapped[time | None] = mapped_column(Time, nullable=True, index=True)

    title: Mapped[str] = mapped_column(String(200))
    maps_url: Mapped[str] = mapped_column(String(500), default="")
    patient_name: Mapped[str] = mapped_column(String(190), default="")
    patient_address: Mapped[str] = mapped_column(String(500), default="")
    patient_phone: Mapped[str] = mapped_column(String(80), default="")
    bonus_details: Mapped[str] = mapped_column(Text, default="")

    patient_id: Mapped[int | None] = mapped_column(ForeignKey("patients.id", ondelete="SET NULL"), nullable=True, index=True)

    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.todo, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    deleted_by_user_id: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    forced_done_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    forced_done_by_user_id: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)

    company = relationship("Company")
    assigned_user = relationship("User", foreign_keys=[assigned_user_id])
    deleted_by_user = relationship("User", foreign_keys=[deleted_by_user_id])
    forced_done_by_user = relationship("User", foreign_keys=[forced_done_by_user_id])
    patient = relationship("Patient")

Index("ix_tasks_company_user_date", Task.company_id, Task.assigned_user_id, Task.task_date)


class PushSubscription(Base):
    """Browser push subscription (Web Push / Push API).

    Stores the endpoint + keys needed to send a notification to a specific device.
    """

    __tablename__ = "push_subscriptions"
    __table_args__ = (
        UniqueConstraint("user_id", "endpoint", name="uq_push_user_endpoint"),
        Index("ix_push_subscriptions_user_id", "user_id"),
        Index("ix_push_subscriptions_active", "active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    endpoint: Mapped[str] = mapped_column(String(1000))
    p256dh: Mapped[str] = mapped_column(String(500))
    auth: Mapped[str] = mapped_column(String(500))

    user_agent: Mapped[str] = mapped_column(String(300), default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="push_subscriptions")

class AuditAction(str, enum.Enum):
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    CREATE_USER = "CREATE_USER"
    RESET_PASSWORD = "RESET_PASSWORD"
    CHANGE_PASSWORD = "CHANGE_PASSWORD"
    DISABLE_USER = "DISABLE_USER"
    SET_ROLE = "SET_ROLE"
    ASSIGN_COMPANY = "ASSIGN_COMPANY"
    CREATE_TASK = "CREATE_TASK"
    COMPLETE_TASK = "COMPLETE_TASK"
    UNCOMPLETE_TASK = "UNCOMPLETE_TASK"
    DELETE_TASK = "DELETE_TASK"
    FORCE_DONE_TASK = "FORCE_DONE_TASK"
    UNFORCE_DONE_TASK = "UNFORCE_DONE_TASK"

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction), index=True)

    target_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)

    ip: Mapped[str] = mapped_column(String(80), default="")
    user_agent: Mapped[str] = mapped_column(String(300), default="")
    # Keep metadata minimal; do NOT store PHI / full task details here.
    meta: Mapped[str] = mapped_column(Text, default="{}")