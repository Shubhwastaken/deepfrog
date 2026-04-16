from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import Session as SyncSession
from app.core.config import settings

# ── Async engine (FastAPI) ──────────────────────────────────────
engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session


# ── Sync engine (Workers) ──────────────────────────────────────
sync_engine = create_engine(settings.SYNC_DATABASE_URL)
SyncSessionLocal = sessionmaker(bind=sync_engine, class_=SyncSession, expire_on_commit=False)


def get_sync_db_session():
    """Returns a sync session for worker processes."""
    session = SyncSessionLocal()
    try:
        yield session
    finally:
        session.close()
