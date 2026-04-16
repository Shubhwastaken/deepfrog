"""
Jobs — Database interaction layer for job management.

All functions use synchronous SQLAlchemy sessions (workers are blocking processes).
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select

from app.db.models import Job
from app.db.session import SyncSessionLocal

logger = logging.getLogger(__name__)


def _get_session():
    return SyncSessionLocal()


def create_job(job_id: str, invoice_path: str, bol_path: str, file_hash: str) -> Job:
    """Insert a new job with status=queued."""
    session = _get_session()
    try:
        job = Job(
            id=job_id,
            status="queued",
            invoice_path=invoice_path,
            bol_path=bol_path,
            file_hash=file_hash,
            retries=0,
            queued_at=datetime.utcnow(),
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        logger.info(f"Created job {job_id} (hash={file_hash[:12]}...)")
        return job
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_job(job_id: str) -> Optional[Job]:
    """Fetch a job by its ID."""
    session = _get_session()
    try:
        result = session.execute(select(Job).where(Job.id == job_id))
        return result.scalar_one_or_none()
    finally:
        session.close()


def get_job_by_hash(file_hash: str) -> Optional[Job]:
    """Fetch a job by file hash (idempotency check)."""
    session = _get_session()
    try:
        result = session.execute(select(Job).where(Job.file_hash == file_hash))
        return result.scalar_one_or_none()
    finally:
        session.close()


def update_job_status(job_id: str, status: str, **kwargs):
    """Update job status and any additional fields (started_at, completed_at, etc.)."""
    session = _get_session()
    try:
        result = session.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            logger.error(f"Job {job_id} not found for status update")
            return
        job.status = status
        for key, value in kwargs.items():
            if hasattr(job, key):
                setattr(job, key, value)
        session.commit()
        logger.info(f"Job {job_id} → status={status}")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def save_job_result(job_id: str, result: dict):
    """Save pipeline result and mark job as completed."""
    session = _get_session()
    try:
        res = session.execute(select(Job).where(Job.id == job_id))
        job = res.scalar_one_or_none()
        if not job:
            logger.error(f"Job {job_id} not found for result save")
            return
        job.status = "completed"
        job.result = result
        job.completed_at = datetime.utcnow()
        session.commit()
        logger.info(f"Job {job_id} → completed (result saved)")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def increment_retry(job_id: str) -> int:
    """Increment retry counter and return new count."""
    session = _get_session()
    try:
        result = session.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            return 0
        job.retries += 1
        session.commit()
        return job.retries
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def mark_failed(job_id: str, error: str):
    """Mark job as permanently failed after exhausting retries."""
    session = _get_session()
    try:
        result = session.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            return
        job.status = "failed"
        job.error_message = error
        job.completed_at = datetime.utcnow()
        session.commit()
        logger.error(f"Job {job_id} → FAILED: {error}")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
