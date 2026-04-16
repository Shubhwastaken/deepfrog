import uuid, redis.asyncio as aioredis, os

async def create_job(file_path: str) -> str:
    job_id = str(uuid.uuid4())
    r = await aioredis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
    await r.rpush("job_queue", f"{job_id}::{file_path}")
    return job_id
