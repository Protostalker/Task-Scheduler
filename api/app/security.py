from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Request

from app.settings import settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

ALGO = "HS256"
TOKEN_TTL_MINUTES = 90 * 24 * 60  # 90 days (≈3 months)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

def create_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=TOKEN_TTL_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGO)

def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[ALGO])
    except JWTError:
        return None

def random_temp_password(length: int = 14) -> str:
    # URL-safe, user-friendly enough
    return secrets.token_urlsafe(length)[:length]

def client_ip(request: Request) -> str:
    # Simple best-effort
    xf = request.headers.get("x-forwarded-for")
    if xf:
        return xf.split(",")[0].strip()
    return request.client.host if request.client else ""
