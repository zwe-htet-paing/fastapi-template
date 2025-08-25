from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

# Project root or directory where the DB should live
BASE_DIR = Path(__file__).resolve().parent.parent  # adjust as needed

DB_DRIVER = os.getenv("DB_DRIVER", "postgresql")  # "sqlite" or "postgresql"
DB_NAME = os.getenv("POSTGRES_DB", "test")

# Choose database URL
if DB_DRIVER == "sqlite":
    db_path = BASE_DIR / f"{DB_NAME}.db"  # e.g., /home/user/project/test.db
    DATABASE_URL_SYNC = f"sqlite:///{db_path}"
    DATABASE_URL_ASYNC = f"sqlite+aiosqlite:///{db_path}"
else:
    DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
    DB_USER = os.getenv("POSTGRES_USER", "test")
    DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    DATABASE_URL_SYNC = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    DATABASE_URL_ASYNC = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    

# Create SQLAlchemy engine (for sync operations)
engine = create_engine(
    DATABASE_URL_SYNC,
    connect_args={"check_same_thread": False} if DB_DRIVER == "sqlite" else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create async SQLAlchemy engine
async_engine = create_async_engine(DATABASE_URL_ASYNC, echo=False)
AsyncSessionLocal = sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)

# Base class for models
Base = declarative_base()

# Dependencies to get sessions
def get_session() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
