import json
import os
import uuid

from sqlalchemy import select

from app.db.models import Job
from app.db.session import get_session_factory


async def create_job(invoice_path: str, bill_of_lading_path: str, owner_email: str) -> str:
    """Create a queued job, persist it, and enqueue it for worker processing."""

    job_id = str(uuid.uuid4())
    queue_payload = json.dumps(
        {
            "job_id": job_id,
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
    await redis_client.aclose()
    return job_id


async def get_job(job_id: str) -> Job | None:
    """Fetch a persisted job by its identifier."""

    async with get_session_factory()() as session:
        result = await session.execute(select(Job).where(Job.id == job_id))
        return result.scalar_one_or_none()
