from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


@lru_cache(maxsize=1)
def get_engine():
    return create_async_engine(settings.DATABASE_URL)


@lru_cache(maxsize=1)
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return sessionmaker(get_engine(), class_=AsyncSession, expire_on_commit=False)


async def get_db_session():
    async with get_session_factory()() as session:
        yield session
