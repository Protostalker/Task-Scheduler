from __future__ import annotations

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.security import decode_token
from app.models import User, Role

COOKIE_NAME = "taskflow_session"

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid session")
    user_id = int(payload.get("sub", "0") or "0")
    user = db.get(User, user_id)
    if not user or user.disabled:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role not in (Role.admin, Role.super_admin):
        raise HTTPException(status_code=403, detail="Forbidden")
    return user

def require_super_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != Role.super_admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    return user
