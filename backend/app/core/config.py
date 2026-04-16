import os
import re
from dotenv import load_dotenv

# Load environment variables from project root .env
_env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))
load_dotenv(dotenv_path=_env_path)


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./customs_brain.db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "3PZ-qN7-9fB-R6-xVQ7QY765-P5gG8c8kY6v4W-Xf3A=") # Default for development
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Convert async DB URL to sync equivalent for worker processes."""
        url = self.DATABASE_URL
        # PostgreSQL: asyncpg → psycopg2
        if "asyncpg" in url:
            return url.replace("+asyncpg", "+psycopg2")
        # SQLite: aiosqlite → pysqlite (default)
        if "aiosqlite" in url:
            return url.replace("+aiosqlite", "")
        return url


settings = Settings()
