from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.admin import router as admin_router
from app.api.user import router as user_router
from app.models.user import User
from app.utils.rbac import get_current_user
from app.schemas.auth import UserOut

from contextlib import asynccontextmanager
from fastapi_cache.decorator import cache

from app.utils.cache import init_redis_cache
from app.utils.rate_limit import init_limiter, per_user_limiter
from app.utils.redis_client import close_redis


from dotenv import load_dotenv
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
     # Initialize Redis cache
    await init_redis_cache()
    # Initialize Redis-based rate limiter
    await init_limiter()
    
    # print("Application started...")
    yield
    # shutdown
    await close_redis()
    # print("Application shutdown complete.")

app = FastAPI(
    title="Template API",
    version="1.0.0",
    openapi_version="3.1.0",
    root_path="/api",
    lifespan=lifespan
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include routers ---
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(user_router, prefix="/user", tags=["user"])


# --- Root & Health ---
@app.get("/")
async def read_root() -> dict:
    return {
        "message": "Template API root OK"
        }


@app.get("/health")
async def health_check() -> dict:
    return {
        "message": "Template API is healthy"
        }
    
@app.get("/cache-test")
@cache(expire=60)  # cache response for 60 seconds
async def cache_test():
    return {"message": "This response is cached for 60s"}


@app.get("/rate-limit-test", dependencies=[Depends(per_user_limiter(times=3, seconds=60))]) # Rate limit to 3 calls per minute
async def rate_limit_test(user: User = Depends(get_current_user)):
    return {"message": f"Hello {user.username}, you can call this 3 times per minute"}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
