import os
import subprocess
from pathlib import Path

TEST_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/mcp_compass_test"
)

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("JWT_SECRET", "test-secret-key-at-least-32-bytes-long")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.security import create_access_token, hash_password
from app.db.session import get_session
from app.main import app
from app.models.user import User, Workspace, WorkspaceMembership

REPO_ROOT = Path(__file__).resolve().parent.parent


def auth_headers(user_id: int) -> dict[str, str]:
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session", autouse=True)
def _migrate_test_db():
    env = os.environ.copy()
    env["DATABASE_URL"] = TEST_DATABASE_URL
    subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        check=True,
        env=env,
        cwd=REPO_ROOT,
    )


@pytest_asyncio.fixture
async def session(_migrate_test_db):
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with engine.connect() as conn:
        await conn.begin()
        db_session = AsyncSession(
            bind=conn,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )
        yield db_session
        await db_session.close()
        await conn.rollback()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(session):
    async def _get_session_override():
        yield session

    app.dependency_overrides[get_session] = _get_session_override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def user1(session):
    user = User(email="user1@example.com", hashed_password=hash_password("password123"))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest_asyncio.fixture
async def user2(session):
    user = User(email="user2@example.com", hashed_password=hash_password("password123"))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest_asyncio.fixture
async def workspace_a(session):
    workspace = Workspace(name="workspace-a")
    session.add(workspace)
    await session.commit()
    await session.refresh(workspace)
    return workspace


@pytest_asyncio.fixture
async def workspace_b(session):
    workspace = Workspace(name="workspace-b")
    session.add(workspace)
    await session.commit()
    await session.refresh(workspace)
    return workspace


@pytest_asyncio.fixture
async def admin_membership(session, user1, workspace_a):
    membership = WorkspaceMembership(
        user_id=user1.id, workspace_id=workspace_a.id, role="admin"
    )
    session.add(membership)
    await session.commit()
    await session.refresh(membership)
    return membership


@pytest_asyncio.fixture
async def member_membership(session, user2, workspace_a):
    membership = WorkspaceMembership(
        user_id=user2.id, workspace_id=workspace_a.id, role="member"
    )
    session.add(membership)
    await session.commit()
    await session.refresh(membership)
    return membership
