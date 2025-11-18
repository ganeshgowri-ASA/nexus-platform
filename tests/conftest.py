"""Pytest configuration and fixtures."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from nexus.core.database import Base


@pytest.fixture(scope="function")
def db_session():
    """Create in-memory SQLite database for testing."""
    # Create in-memory database
    engine = create_engine("sqlite:///:memory:", echo=False)

    # Create all tables
    Base.metadata.create_all(engine)

    # Create session
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = SessionLocal()

    yield session

    # Cleanup
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def sample_user_id():
    """Sample user ID for testing."""
    return "test_user_123"


@pytest.fixture
def sample_note_data():
    """Sample note data for testing."""
    return {
        "title": "Test Note",
        "content": "This is a test note content.",
        "content_markdown": "# Test Note\n\nThis is a **test** note content.",
    }
