"""
Pytest configuration and fixtures.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session."""
    # Create in-memory SQLite database for testing
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    from database import User

    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password="hashed_password",
        is_active=True,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def sample_content(db_session, sample_user):
    """Create sample content for testing."""
    from database import ContentItem, ContentType, ContentStatus
    from datetime import datetime, timedelta

    content = ContentItem(
        title="Test Content",
        content="This is test content",
        content_type=ContentType.SOCIAL_POST,
        status=ContentStatus.DRAFT,
        creator_id=sample_user.id,
        scheduled_at=datetime.utcnow() + timedelta(days=1),
        timezone="UTC",
        channels=["twitter"],
        tags=["test", "example"],
    )

    db_session.add(content)
    db_session.commit()
    db_session.refresh(content)

    return content
