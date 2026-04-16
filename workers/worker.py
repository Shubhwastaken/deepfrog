import asyncio, os
import redis.asyncio as aioredis
from workers.queue.task_router import route_task

async def main():
    print("Worker started...")
    r = await aioredis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
    while True:
        _, payload = await r.blpop("job_queue")
        job_id, file_path = payload.decode().split("::", 1)
        print(f"Processing job: {job_id}")
        await route_task(job_id, file_path)

if __name__ == "__main__":
    asyncio.run(main())
