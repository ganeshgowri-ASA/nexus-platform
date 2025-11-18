"""
Pytest configuration and fixtures for testing.

This module provides test fixtures and configuration for the test suite.
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from src.core.database import Base
from src.models.base import Workspace, User


# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create test database session.

    Yields:
        Test database session
    """
    # Create async engine
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session

    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_workspace(test_db: AsyncSession):
    """Create test workspace."""
    workspace = Workspace(
        name="Test Workspace",
        slug="test-workspace",
        is_active=True,
    )

    test_db.add(workspace)
    await test_db.commit()
    await test_db.refresh(workspace)

    return workspace


@pytest.fixture
async def test_user(test_db: AsyncSession, test_workspace):
    """Create test user."""
    from src.core.utils import hash_password

    user = User(
        email="test@example.com",
        password_hash=hash_password("testpassword123"),
        first_name="Test",
        last_name="User",
        is_active=True,
        workspace_id=test_workspace.id,
    )

    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    return user


@pytest.fixture
def mock_llm_response():
    """Mock LLM API response."""
    return {
        "subject": "Test Subject",
        "body": "<h1>Test Email</h1><p>This is a test email.</p>",
    }
