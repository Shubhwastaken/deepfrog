"""Database persistence helpers used by the worker pipeline."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@lru_cache(maxsize=1)
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Create a cached async SQLAlchemy session factory."""

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required for worker job persistence.")

    engine = create_async_engine(database_url)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def update_job_processing(job_id: str) -> None:
    """Mark a job as in progress before running the pipeline."""

    await _execute_update(
        """
        UPDATE jobs
        SET status = :status,
            error_message = NULL
        WHERE id = :job_id
        """,
        {"job_id": job_id, "status": "processing"},
    )


async def update_job_completed(job_id: str, payload: dict[str, Any]) -> None:
    """Persist the final pipeline output for a completed job."""

    await _execute_update(
        """
        UPDATE jobs
        SET status = :status,
            results = CAST(:results AS JSON),
            report_path = :report_path,
            error_message = NULL
        WHERE id = :job_id
        """,
        {
            "job_id": job_id,
            "status": "completed",
            "results": json.dumps(payload["output_result"]),
            "report_path": payload.get("report_path"),
        },
    )


async def update_job_failed(job_id: str, error_message: str) -> None:
    """Persist failure information for a job."""

    await _execute_update(
        """
        UPDATE jobs
        SET status = :status,
            error_message = :error_message
        WHERE id = :job_id
        """,
        {
            "job_id": job_id,
            "status": "failed",
            "error_message": error_message[:4000],
        },
    )


async def _execute_update(query: str, parameters: dict[str, Any]) -> None:
    """Execute an update statement inside a managed async session."""

    session_factory = get_session_factory()
    async with session_factory() as session:
        await session.execute(text(query), parameters)
        await session.commit()
