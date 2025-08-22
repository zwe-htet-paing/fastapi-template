import redis.asyncio as redis
from fastapi import Request, HTTPException
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

from app.utils.security import verify_token
from app.utils.redis_client import get_redis

import os

redis_client: redis.Redis | None = None

async def init_limiter():
    """
    Initialize Redis-backed async rate limiter.
    Call this in FastAPI startup event.
    """
    redis_client = await get_redis()
    await FastAPILimiter.init(redis_client)


# --- Extract user identifier from request ---
async def user_identifier(request: Request) -> str:
    auth: str = request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth.split(" ")[1]
    payload = verify_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    return f"user:{payload['sub']}"


def per_user_limiter(times: int = 5, seconds: int = 60):
    """
    Returns a list of dependencies for a route to apply rate limiting.
    """
    return RateLimiter(times=times, seconds=seconds, identifier=user_identifier)

