import json
import os
import uuid

import redis.asyncio as aioredis
from sqlalchemy import func, select

from app.core.config import settings
from app.db.models import Job
from app.db.session import get_session_factory
from shared.utils.logger import get_logger
from shared.utils.request_context import get_request_id
from shared.utils.worker_runtime import (
    WORKER_EVENTS_KEY,
    WORKER_HEARTBEAT_KEY,
    build_worker_status,
    parse_runtime_payload,
)

logger = get_logger("customs_brain.jobs")


async def _close_redis_client(redis_client: aioredis.Redis | None) -> None:
    """Close Redis clients across redis-py versions."""

    if redis_client is None:
        return

    close_method = getattr(redis_client, "aclose", None)
    if close_method is not None:
        await close_method()
        return

    await redis_client.close()


async def create_job(invoice_path: str, bill_of_lading_path: str, owner_email: str) -> str:
    """Create a queued job, persist it, and enqueue it for worker processing."""

    job_id = str(uuid.uuid4())
    request_id = get_request_id()
    queue_payload = json.dumps(
        {
            "job_id": job_id,
            "request_id": request_id,
            "owner_email": owner_email,
            "document_paths": {
                "invoice": invoice_path,
                "bill_of_lading": bill_of_lading_path,
            },
        }
    )

    async with get_session_factory()() as session:
        session.add(
            Job(
                id=job_id,
                owner_email=owner_email,
                invoice_path=invoice_path,
                bill_of_lading_path=bill_of_lading_path,
                status="queued",
            )
        )
        await session.commit()

    import redis.asyncio as aioredis

    redis_client = await aioredis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
    await redis_client.rpush("job_queue", queue_payload)
    await _close_redis_client(redis_client)
    logger.info("Queued job for worker execution job_id=%s", job_id)
    return job_id


async def get_job(job_id: str) -> Job | None:
    """Fetch a persisted job by its identifier."""

    async with get_session_factory()() as session:
        result = await session.execute(select(Job).where(Job.id == job_id))
        return result.scalar_one_or_none()


async def rerun_job(source_job: Job, owner_email: str) -> str:
    """Queue a fresh job using the same document paths as a prior job."""

    return await create_job(
        invoice_path=source_job.invoice_path,
        bill_of_lading_path=source_job.bill_of_lading_path,
        owner_email=owner_email,
    )


async def get_pipeline_metrics() -> dict:
    """Return aggregate pipeline status counts from persistent storage."""

    async with get_session_factory()() as session:
        total_jobs = await session.scalar(select(func.count()).select_from(Job)) or 0
        grouped = await session.execute(select(Job.status, func.count()).group_by(Job.status))
        counts = {status: count for status, count in grouped.all()}

    completed = int(counts.get("completed", 0))
    failed = int(counts.get("failed", 0))
    processing = int(counts.get("processing", 0))
    queued = int(counts.get("queued", 0))
    completion_rate = round((completed / total_jobs), 4) if total_jobs else 0.0
    worker_runtime = await _get_worker_runtime_metrics()

    return {
        "total_jobs": int(total_jobs),
        "queued": queued,
        "processing": processing,
        "completed": completed,
        "failed": failed,
        "completion_rate": completion_rate,
        **worker_runtime,
    }


async def _get_worker_runtime_metrics() -> dict:
    redis_client = None
    try:
        redis_client = await aioredis.from_url(settings.REDIS_URL)
        raw_workers = await redis_client.hgetall(WORKER_HEARTBEAT_KEY)
        raw_events = await redis_client.lrange(WORKER_EVENTS_KEY, 0, 7)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not load worker runtime metrics: %s", exc)
        return {
            "worker_runtime_available": False,
            "active_workers": 0,
            "busy_workers": 0,
            "parallel_capacity_ready": False,
            "parallel_processing_live": False,
            "workers": [],
            "recent_worker_events": [],
        }
    finally:
        await _close_redis_client(redis_client)

    workers = []
    for raw_payload in raw_workers.values():
        payload = parse_runtime_payload(raw_payload)
        if payload is None:
            continue
        workers.append(build_worker_status(payload))

    workers.sort(key=lambda worker: worker["worker_name"])
    active_workers = [worker for worker in workers if worker["is_fresh"]]
    busy_workers = [worker for worker in active_workers if worker["status"] == "busy"]
    recent_worker_events = [payload for raw in raw_events if (payload := parse_runtime_payload(raw))]

    return {
        "worker_runtime_available": True,
        "active_workers": len(active_workers),
        "busy_workers": len(busy_workers),
        "parallel_capacity_ready": len(active_workers) >= 2,
        "parallel_processing_live": len(busy_workers) >= 2,
        "workers": workers,
        "recent_worker_events": recent_worker_events,
    }
