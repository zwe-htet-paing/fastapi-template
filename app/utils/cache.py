from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from app.utils.redis_client import get_redis

async def init_redis_cache():
    redis_client = await get_redis()
    FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
