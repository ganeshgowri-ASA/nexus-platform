"""Pytest configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from modules.ab_testing.api.main import app
from modules.ab_testing.models.base import Base, get_db


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://nexus:password@localhost:5432/nexus_test_db"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database override."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_experiment_data() -> dict:
    """Sample experiment data for testing."""
    return {
        "name": "Test Experiment",
        "description": "Testing experiment creation",
        "hypothesis": "Red button will increase conversions",
        "type": "ab",
        "target_sample_size": 1000,
        "confidence_level": 0.95,
        "traffic_allocation": 1.0,
        "auto_winner_enabled": True,
    }


@pytest.fixture
def sample_variant_data() -> dict:
    """Sample variant data for testing."""
    return {
        "experiment_id": 1,
        "name": "Control",
        "description": "Original design",
        "is_control": True,
        "traffic_weight": 1.0,
        "config": {"button_color": "blue"},
    }


@pytest.fixture
def sample_metric_data() -> dict:
    """Sample metric data for testing."""
    return {
        "experiment_id": 1,
        "name": "Conversion Rate",
        "description": "Primary conversion metric",
        "type": "conversion",
        "is_primary": True,
    }
