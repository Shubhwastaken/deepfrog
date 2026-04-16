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

    postgres_user = os.getenv("POSTGRES_USER", "")
    postgres_password = os.getenv("POSTGRES_PASSWORD", "")
    postgres_host = os.getenv("POSTGRES_HOST", "localhost")
    postgres_db = os.getenv("POSTGRES_DB", "customs_brain")
    auth_segment = f"{postgres_user}:{postgres_password}@" if postgres_user and postgres_password else ""
    return f"postgresql+asyncpg://{auth_segment}{postgres_host}/{postgres_db}"


class Settings:
    DATABASE_URL: str = _get_database_url()
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    SHARED_DATA_DIR: str = os.getenv("SHARED_DATA_DIR", "data")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", os.path.join(SHARED_DATA_DIR, "uploads"))
    REPORT_DIR: str = os.getenv("REPORT_DIR", os.path.join(SHARED_DATA_DIR, "reports"))
    LOG_DIR: str = os.getenv("LOG_DIR", os.path.join(SHARED_DATA_DIR, "logs"))
    LOCAL_PIPELINE_MODE: bool = _get_bool_env("LOCAL_PIPELINE_MODE", "false")
    AUTH_DEBUG_OTP_ECHO: bool = _get_bool_env("AUTH_DEBUG_OTP_ECHO", "true" if LOCAL_PIPELINE_MODE else "false")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    PII_ENCRYPTION_KEY: str = os.getenv("PII_ENCRYPTION_KEY", SECRET_KEY)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    OTP_EXPIRE_MINUTES: int = int(os.getenv("OTP_EXPIRE_MINUTES", "5"))
    OTP_LENGTH: int = int(os.getenv("OTP_LENGTH", "6"))
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@customs.ai")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "")
    GENERAL_USER_EMAIL: str = os.getenv("GENERAL_USER_EMAIL", "")
    GENERAL_USER_PASSWORD: str = os.getenv("GENERAL_USER_PASSWORD", "")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", ADMIN_EMAIL)
    SMTP_USE_TLS: bool = _get_bool_env("SMTP_USE_TLS", "true")

settings = Settings()
