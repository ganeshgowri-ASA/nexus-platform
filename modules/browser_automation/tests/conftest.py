"""Pytest configuration and fixtures"""
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from modules.browser_automation.models.database import Base
from modules.browser_automation.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session():
    """Create test database session"""
    # Use in-memory SQLite for tests
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with SessionLocal() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def sample_workflow_data():
    """Sample workflow data for testing"""
    return {
        "name": "Test Workflow",
        "description": "A test workflow",
        "is_active": True,
        "headless": True,
        "browser_type": "chromium",
        "timeout": 30000,
        "steps": [
            {
                "step_order": 0,
                "step_type": "navigate",
                "name": "Go to website",
                "value": "https://example.com",
                "selector": None,
                "selector_type": "css",
                "wait_before": 0,
                "wait_after": 1000,
                "error_handling": "stop",
                "max_retries": 3
            },
            {
                "step_order": 1,
                "step_type": "extract",
                "name": "Extract title",
                "selector": "h1",
                "selector_type": "css",
                "value": None,
                "wait_before": 0,
                "wait_after": 0,
                "error_handling": "stop",
                "max_retries": 3
            }
        ]
    }


@pytest.fixture
def sample_schedule_data():
    """Sample schedule data for testing"""
    return {
        "workflow_id": 1,
        "name": "Daily Schedule",
        "is_active": True,
        "cron_expression": "0 0 * * *",
        "timezone": "UTC",
        "max_concurrent_runs": 1,
        "retry_on_failure": True,
        "max_retries": 3,
        "notify_on_success": False,
        "notify_on_failure": True,
        "notification_emails": ["admin@example.com"]
    }
