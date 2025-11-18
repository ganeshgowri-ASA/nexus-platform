"""
Pytest Configuration and Fixtures

Shared fixtures for analytics module tests.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from modules.analytics.api.main import app
from modules.analytics.storage.database import Database, Base
from modules.analytics.core.tracker import EventTracker
from modules.analytics.core.aggregator import DataAggregator
from modules.analytics.core.processor import EventProcessor
from modules.analytics.processing.funnel import FunnelEngine
from modules.analytics.processing.cohort import CohortEngine
from modules.analytics.processing.attribution import AttributionEngine
from modules.analytics.processing.predictive import PredictiveEngine
from shared.utils import get_utc_now


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def test_engine():
    """Create in-memory SQLite engine for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """Create a new database session for each test."""
    TestSessionLocal = sessionmaker(bind=test_engine)
    session = TestSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@pytest.fixture(scope="function")
def test_db(test_engine) -> Database:
    """Create test database instance."""
    db = Database(connection_string="sqlite:///:memory:")
    db.engine = test_engine
    return db


# ============================================================================
# API Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def client(test_db) -> TestClient:
    """Create FastAPI test client."""
    # Override database dependency
    def override_get_db():
        try:
            session = test_db.session()
            yield session
        finally:
            session.close()

    app.dependency_overrides[Database] = lambda: test_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ============================================================================
# Core Component Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def tracker(test_db) -> EventTracker:
    """Create event tracker instance."""
    tracker = EventTracker(db=test_db, batch_size=10, auto_start=False)
    yield tracker
    tracker.stop(flush_remaining=False)


@pytest.fixture(scope="function")
def aggregator(test_db) -> DataAggregator:
    """Create data aggregator instance."""
    return DataAggregator(db=test_db)


@pytest.fixture(scope="function")
def processor(test_db) -> EventProcessor:
    """Create event processor instance."""
    return EventProcessor(db=test_db)


@pytest.fixture(scope="function")
def funnel_engine(test_db) -> FunnelEngine:
    """Create funnel engine instance."""
    return FunnelEngine(db=test_db)


@pytest.fixture(scope="function")
def cohort_engine(test_db) -> CohortEngine:
    """Create cohort engine instance."""
    return CohortEngine(db=test_db)


@pytest.fixture(scope="function")
def attribution_engine(test_db) -> AttributionEngine:
    """Create attribution engine instance."""
    return AttributionEngine(db=test_db)


@pytest.fixture(scope="function")
def predictive_engine(test_db) -> PredictiveEngine:
    """Create predictive engine instance."""
    return PredictiveEngine(db=test_db)


# ============================================================================
# Cache Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def mock_cache():
    """Mock cache implementation."""
    cache_data = {}

    class MockCache:
        async def get(self, key: str):
            return cache_data.get(key)

        async def set(self, key: str, value, ttl: int = 300):
            cache_data[key] = value

        async def delete(self, key: str):
            cache_data.pop(key, None)

        async def clear(self):
            cache_data.clear()

    return MockCache()


# ============================================================================
# Mock Data Fixtures
# ============================================================================

@pytest.fixture
def sample_event_data():
    """Sample event data for testing."""
    return {
        "name": "page_view",
        "event_type": "page_view",
        "properties": {
            "page": "/dashboard",
            "referrer": "https://google.com",
            "utm_source": "google",
            "utm_medium": "cpc"
        },
        "user_id": "user_123",
        "session_id": "session_456",
        "module": "analytics",
        "page_url": "https://example.com/dashboard",
        "page_title": "Dashboard",
        "user_agent": "Mozilla/5.0",
        "ip_address": "192.168.1.1",
        "country": "US",
        "city": "San Francisco",
        "device_type": "desktop",
        "browser": "Chrome",
        "os": "Windows"
    }


@pytest.fixture
def sample_events_batch(sample_event_data):
    """Sample batch of events."""
    events = []
    base_time = get_utc_now()

    for i in range(10):
        event = sample_event_data.copy()
        event["name"] = f"event_{i}"
        event["timestamp"] = base_time + timedelta(seconds=i)
        events.append(event)

    return events


@pytest.fixture
def sample_user_data():
    """Sample user data."""
    return {
        "user_id": "user_123",
        "email": "test@example.com",
        "name": "Test User",
        "signup_date": get_utc_now() - timedelta(days=30),
        "properties": {
            "plan": "premium",
            "company": "Test Corp"
        }
    }


@pytest.fixture
def sample_session_data():
    """Sample session data."""
    now = get_utc_now()
    return {
        "session_id": "session_456",
        "user_id": "user_123",
        "started_at": now,
        "ended_at": now + timedelta(minutes=15),
        "duration_seconds": 900,
        "page_views": 5,
        "events_count": 10,
        "is_bounce": False,
        "converted": True,
        "conversion_value": 99.99,
        "landing_page": "/home",
        "exit_page": "/checkout/complete"
    }


@pytest.fixture
def sample_funnel_data():
    """Sample funnel configuration."""
    return {
        "name": "Checkout Funnel",
        "description": "Main checkout flow",
        "steps": [
            {"name": "View Product", "event_type": "product_view", "order": 0},
            {"name": "Add to Cart", "event_type": "add_to_cart", "order": 1},
            {"name": "Checkout", "event_type": "checkout_start", "order": 2},
            {"name": "Complete", "event_type": "purchase", "order": 3}
        ]
    }


@pytest.fixture
def sample_cohort_data():
    """Sample cohort data."""
    return {
        "name": "Premium Users",
        "description": "Users on premium plan",
        "criteria": {
            "properties.plan": "premium"
        },
        "start_date": get_utc_now() - timedelta(days=30),
        "end_date": get_utc_now()
    }


@pytest.fixture
def sample_metric_data():
    """Sample metric data."""
    return {
        "name": "daily_active_users",
        "metric_type": "gauge",
        "value": 1250.0,
        "period": "day",
        "dimensions": {
            "module": "analytics",
            "region": "us-west"
        },
        "module": "analytics",
        "timestamp": get_utc_now()
    }


# ============================================================================
# Mock External Services
# ============================================================================

@pytest.fixture
def mock_celery():
    """Mock Celery task execution."""
    with patch('modules.analytics.processing.celery_app.celery') as mock:
        mock.send_task = MagicMock(return_value=AsyncMock())
        yield mock


@pytest.fixture
def mock_redis():
    """Mock Redis connection."""
    mock_client = MagicMock()
    mock_client.get = MagicMock(return_value=None)
    mock_client.set = MagicMock(return_value=True)
    mock_client.delete = MagicMock(return_value=True)
    mock_client.keys = MagicMock(return_value=[])

    with patch('redis.Redis', return_value=mock_client):
        yield mock_client


@pytest.fixture
def mock_s3():
    """Mock S3 client for export tests."""
    mock_client = MagicMock()
    mock_client.put_object = MagicMock(return_value={"ResponseMetadata": {"HTTPStatusCode": 200}})
    mock_client.get_object = MagicMock(return_value={"Body": MagicMock()})

    with patch('boto3.client', return_value=mock_client):
        yield mock_client


# ============================================================================
# Async Test Support
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Test Data Cleanup
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_data(db_session):
    """Clean up test data after each test."""
    yield
    # Cleanup is handled by session rollback in db_session fixture


# ============================================================================
# Parametrized Test Data
# ============================================================================

@pytest.fixture(params=["page_view", "click", "form_submit", "purchase"])
def event_type(request):
    """Parametrized event types for testing."""
    return request.param


@pytest.fixture(params=["day", "week", "month"])
def aggregation_period(request):
    """Parametrized aggregation periods."""
    return request.param


@pytest.fixture(params=[10, 50, 100])
def batch_size(request):
    """Parametrized batch sizes."""
    return request.param


# ============================================================================
# Time-based Fixtures
# ============================================================================

@pytest.fixture
def current_time():
    """Current UTC time for consistent testing."""
    return get_utc_now()


@pytest.fixture
def date_range():
    """Sample date range for queries."""
    end_date = get_utc_now()
    start_date = end_date - timedelta(days=30)
    return start_date, end_date


@pytest.fixture
def freeze_time(monkeypatch):
    """Freeze time for predictable testing."""
    frozen_time = datetime(2024, 1, 1, 12, 0, 0)

    def mock_utc_now():
        return frozen_time

    monkeypatch.setattr('shared.utils.get_utc_now', mock_utc_now)
    return frozen_time
