from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None)

    database_url: str = Field(alias="DATABASE_URL")
    jwt_secret: str = Field(default="change-me", alias="JWT_SECRET")

    cookie_secure: bool = Field(default=False, alias="COOKIE_SECURE")
    cookie_domain: str = Field(default="", alias="COOKIE_DOMAIN")

    cors_origins: str = Field(default="http://localhost:8080", alias="CORS_ORIGINS")

    # --- Web Push (Chrome/Browser Push Notifications) ---
    # Public key is safe to expose to the frontend; private key must stay server-side.
    vapid_public_key: str = Field(default="", alias="VAPID_PUBLIC_KEY")
    vapid_private_key: str = Field(default="", alias="VAPID_PRIVATE_KEY")
    vapid_subject: str = Field(default="mailto:admin@example.com", alias="VAPID_SUBJECT")

    # Redis queue for push jobs (consumed by push-worker)
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    push_queue_key: str = Field(default="taskflow:push:queue", alias="PUSH_QUEUE_KEY")

    bootstrap_root_username: str = Field(default="root", alias="BOOTSTRAP_ROOT_USERNAME")
    bootstrap_write_path: str = Field(default="/data/bootstrap_superadmin.txt", alias="BOOTSTRAP_WRITE_PATH")

settings = Settings()
