"""
NEXUS Platform - Test Configuration and Fixtures
"""
import pytest
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from backend.app.db.base import Base
from backend.app.main import app
from backend.app.db.session import get_db
from backend.app.models.attribution import (
    Channel,
    Journey,
    Touchpoint,
    Conversion,
    AttributionModel,
    ChannelType,
    TouchpointType,
    ConversionType,
    AttributionModelType,
)


# Test database URL (SQLite in-memory)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_engine():
    """Create test database engine."""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine,
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create test client with dependency overrides."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def test_channel(db_session: Session) -> Channel:
    """Create test channel."""
    channel = Channel(
        name="Test Channel",
        channel_type=ChannelType.PAID_SEARCH,
        description="Test channel description",
        cost_per_click=1.50,
        monthly_budget=10000.0,
        is_active=True,
    )
    db_session.add(channel)
    db_session.commit()
    db_session.refresh(channel)
    return channel


@pytest.fixture
def test_journey(db_session: Session) -> Journey:
    """Create test journey."""
    from datetime import datetime

    journey = Journey(
        user_id="test_user_123",
        session_id="test_session_456",
        start_time=datetime.utcnow(),
        total_touchpoints=0,
        conversion_value=0.0,
        has_conversion=False,
    )
    db_session.add(journey)
    db_session.commit()
    db_session.refresh(journey)
    return journey


@pytest.fixture
def test_touchpoint(
    db_session: Session, test_journey: Journey, test_channel: Channel
) -> Touchpoint:
    """Create test touchpoint."""
    from datetime import datetime

    touchpoint = Touchpoint(
        journey_id=test_journey.id,
        channel_id=test_channel.id,
        touchpoint_type=TouchpointType.CLICK,
        timestamp=datetime.utcnow(),
        position_in_journey=1,
        time_spent_seconds=60,
        pages_viewed=3,
        engagement_score=0.75,
        cost=1.50,
    )
    db_session.add(touchpoint)

    # Update journey
    test_journey.total_touchpoints = 1

    db_session.commit()
    db_session.refresh(touchpoint)
    return touchpoint


@pytest.fixture
def test_conversion(db_session: Session, test_journey: Journey) -> Conversion:
    """Create test conversion."""
    from datetime import datetime

    conversion = Conversion(
        journey_id=test_journey.id,
        conversion_type=ConversionType.PURCHASE,
        timestamp=datetime.utcnow(),
        revenue=100.0,
        quantity=1,
        product_name="Test Product",
    )
    db_session.add(conversion)

    # Update journey
    test_journey.has_conversion = True
    test_journey.conversion_value = 100.0

    db_session.commit()
    db_session.refresh(conversion)
    return conversion


@pytest.fixture
def test_attribution_model(db_session: Session) -> AttributionModel:
    """Create test attribution model."""
    model = AttributionModel(
        name="Test Linear Model",
        model_type=AttributionModelType.LINEAR,
        description="Test linear attribution model",
        is_active=True,
        is_default=False,
    )
    db_session.add(model)
    db_session.commit()
    db_session.refresh(model)
    return model


@pytest.fixture
def complete_test_journey(
    db_session: Session, test_journey: Journey, test_channel: Channel
) -> Journey:
    """Create a complete test journey with touchpoints and conversion."""
    from datetime import datetime, timedelta

    # Add multiple touchpoints
    base_time = datetime.utcnow()

    for i in range(3):
        touchpoint = Touchpoint(
            journey_id=test_journey.id,
            channel_id=test_channel.id,
            touchpoint_type=TouchpointType.CLICK,
            timestamp=base_time + timedelta(minutes=i * 30),
            position_in_journey=i + 1,
            time_spent_seconds=60 + (i * 10),
            engagement_score=0.5 + (i * 0.1),
            cost=1.0 + (i * 0.5),
        )
        db_session.add(touchpoint)

    # Add conversion
    conversion = Conversion(
        journey_id=test_journey.id,
        conversion_type=ConversionType.PURCHASE,
        timestamp=base_time + timedelta(hours=2),
        revenue=150.0,
    )
    db_session.add(conversion)

    # Update journey
    test_journey.total_touchpoints = 3
    test_journey.has_conversion = True
    test_journey.conversion_value = 150.0
    test_journey.end_time = base_time + timedelta(hours=2)

    db_session.commit()
    db_session.refresh(test_journey)

    return test_journey
