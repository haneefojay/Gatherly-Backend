import os
os.environ["TESTING"] = "True"

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import DBBase
from app.core.settings import get_settings
from app.common.dependencies import get_session

settings = get_settings()
settings.TESTING = True

from sqlalchemy.pool import NullPool

db_url = settings.POSTGRES_TEST_DATABASE_URL

if not db_url:
    db_url = settings.POSTGRES_DATABASE_URL

if "test" not in db_url.split("/")[-1].split("?")[0].lower() and not settings.ALLOW_NON_TEST_DB:
    raise RuntimeError(
        f"SAFETY ERROR: Tests serve to wipe data! Target DB '{db_url}' does not look like a test DB. "
        "Please set POSTGRES_TEST_DATABASE_URL in .env to a dedicated test database."
    )

engine = create_async_engine(db_url, echo=False, poolclass=NullPool)
TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
    """Override get_session for testing"""
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_session] = override_get_session

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create tables if needed and cleanup data after each test"""
    async with engine.begin() as conn:
        await conn.run_sync(DBBase.metadata.create_all)
    yield
    async with engine.begin() as conn:
        for table in reversed(DBBase.metadata.sorted_tables):
            await conn.execute(table.delete())

@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Isolated session for each test"""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async client for testing endpoints"""
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test",
        follow_redirects=True
    ) as ac:
        yield ac

@pytest.fixture
async def auth_headers(client: AsyncClient):
    """Helper to create a user and get auth headers"""
    import uuid
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    user_data = {
        "email": email,
        "full_name": "Test User",
        "password": "testpassword123",
        "role": "organizer"
    }
    signup_res = await client.post("/auth/signup", json=user_data)
    assert signup_res.status_code == 201, f"Signup failed: {signup_res.json()}"
    
    login_data = {"email": email, "password": "testpassword123"}
    response = await client.post("/auth/login", json=login_data)
    assert response.status_code == 200, f"Login failed: {response.json()}"
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
