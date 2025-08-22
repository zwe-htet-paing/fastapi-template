import redis.asyncio as redis
import os

redis_client: redis.Redis | None = None

async def get_redis() -> redis.Redis:
    global redis_client
    if not redis_client:
        redis_client = redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379"),
            encoding="utf-8",
            decode_responses=True
        )
    return redis_client

async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
        await redis_client.connection_pool.disconnect()
        redis_client = None