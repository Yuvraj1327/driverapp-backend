"""
Pytest fixtures: an in-memory SQLite async engine (via aiosqlite) overriding
the Postgres dependency so the test-suite runs without external services,
plus an httpx AsyncClient wired to the FastAPI app.
"""
import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.constants import RoleName
from app.core.security import hash_password
from app.database.session import get_db
from app.main import app
from app.models import Base
from app.models.role import Role
from app.models.user import User

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    admin_role = Role(name=RoleName.ADMIN.value, description="Administrator")
    manager_role = Role(name=RoleName.MANAGER.value, description="Manager")
    driver_role = Role(name=RoleName.DRIVER.value, description="Driver")
    db_session.add_all([admin_role, manager_role, driver_role])
    await db_session.flush()

    user = User(
        full_name="Test Admin",
        email="admin@test.com",
        hashed_password=hash_password("Password@123"),
        role_id=admin_role.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, admin_user: User) -> str:
    response = await client.post(
        "/api/v1/auth/login", json={"email": "admin@test.com", "password": "Password@123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]
