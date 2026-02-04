from __future__ import annotations

import os
from pathlib import Path
import secrets

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models import User, Role
from app.security import hash_password

def bootstrap_superadmin(db: Session, *, username: str, write_path: str) -> None:
    # If a super_admin exists, do nothing.
    existing = db.execute(select(User).where(User.role == Role.super_admin)).scalar_one_or_none()
    if existing:
        return

    password = secrets.token_urlsafe(18)
    root = User(
        username=username,
        display_name="Super Admin",
        role=Role.super_admin,
        password_hash=hash_password(password),
        must_change_password=False,
        disabled=False,
    )
    db.add(root)
    db.commit()

    # Write password to mounted file.
    p = Path(write_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    # Don't overwrite if it already exists for any reason.
    if not p.exists():
        p.write_text(f"username: {username}\npassword: {password}\n", encoding="utf-8")
