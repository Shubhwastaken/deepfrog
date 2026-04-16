import redis.asyncio as aioredis, os

_redis = None

async def get_redis():
    global _redis
    if _redis is None:
        _redis = await aioredis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
    return _redis
