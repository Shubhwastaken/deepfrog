import asyncio
import json
import os

import redis.asyncio as aioredis
from workers.queue.task_router import route_task
from workers.job_store import update_job_completed, update_job_failed, update_job_processing

async def main():
    print("Worker started...")
    r = await aioredis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
    while True:
        _, payload = await r.blpop("job_queue")
        job_payload = json.loads(payload.decode())
        job_id = job_payload["job_id"]
        document_paths = job_payload["document_paths"]
        print(f"Processing job: {job_id}")
        await update_job_processing(job_id)
        try:
            result = await route_task(job_id, document_paths)
        except Exception as exc:  # noqa: BLE001
            await update_job_failed(job_id, str(exc))
            print(f"Job {job_id} failed: {exc}")
        else:
            await update_job_completed(job_id, result)

if __name__ == "__main__":
    asyncio.run(main())
