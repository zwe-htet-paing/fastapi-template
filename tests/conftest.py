import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_async_session
from app.models.user import User
from app.utils.security import hash_password

# Use a test database (SQLite in-memory for speed)
DATABASE_URL = "sqlite+aiosqlite:///:memory:?cache=shared"

engine = create_async_engine(DATABASE_URL, future=True, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


# Override the DB dependency in FastAPI
app.dependency_overrides[get_async_session] = override_get_db

@pytest_asyncio.fixture(scope="session")
async def setup_database():
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

        # Seed admin user
        async with TestingSessionLocal() as session:
            admin = User(
                username="admin",
                email="admin@example.com",
                hashed_password=hash_password("password123"),
                role="admin"
            )
            session.add(admin)
            await session.commit()

    yield  # tests run here

    # Drop tables after all tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="session")
async def test_client(setup_database):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


### Note: To run tests, use the command:
### pytest -v --tb=short --disable-warnings -p no:warnings