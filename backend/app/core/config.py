import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _get_bool_env(name: str, default: str = "false") -> bool:
    value = os.getenv(name, default).strip().lower()
    return value in {"1", "true", "yes", "on"}


def _get_database_url() -> str:
    configured_url = os.getenv("DATABASE_URL")
    if configured_url:
        return configured_url

    if _get_bool_env("LOCAL_PIPELINE_MODE", "false"):
        configured_path = Path(os.getenv("LOCAL_DB_PATH", "backend/data/customs_brain.db"))
        local_db_path = configured_path if configured_path.is_absolute() else (PROJECT_ROOT / configured_path)
        local_db_path = local_db_path.resolve()
        local_db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+aiosqlite:///{local_db_path.as_posix()}"

    return "postgresql+asyncpg://user:pass@localhost/customs_brain"


class Settings:
    DATABASE_URL: str = _get_database_url()
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    SHARED_DATA_DIR: str = os.getenv("SHARED_DATA_DIR", "data")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", os.path.join(SHARED_DATA_DIR, "uploads"))
    REPORT_DIR: str = os.getenv("REPORT_DIR", os.path.join(SHARED_DATA_DIR, "reports"))
    LOCAL_PIPELINE_MODE: bool = _get_bool_env("LOCAL_PIPELINE_MODE", "false")
    AUTH_DEBUG_OTP_ECHO: bool = _get_bool_env("AUTH_DEBUG_OTP_ECHO", "true" if LOCAL_PIPELINE_MODE else "false")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    OTP_EXPIRE_MINUTES: int = int(os.getenv("OTP_EXPIRE_MINUTES", "5"))
    OTP_LENGTH: int = int(os.getenv("OTP_LENGTH", "6"))
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@customs.ai")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "secret")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", ADMIN_EMAIL)
    SMTP_USE_TLS: bool = _get_bool_env("SMTP_USE_TLS", "true")

settings = Settings()
