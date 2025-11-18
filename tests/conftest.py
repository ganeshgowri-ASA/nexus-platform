"""
PyTest Configuration and Fixtures
Shared test fixtures and configuration for all tests
"""

import pytest
import sys
from pathlib import Path
from typing import Generator

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import Settings
from database import Base, engine, SessionLocal


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """
    Fixture for test settings
    Returns a Settings instance configured for testing
    """
    return Settings(
        environment="testing",
        debug=True,
        database={"url": "sqlite:///:memory:", "echo": False},
        anthropic={"api_key": "test-key"},
    )


@pytest.fixture(scope="function")
def db_session() -> Generator:
    """
    Fixture for database session
    Creates a fresh database for each test and cleans up after
    """
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Create session
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Drop tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def mock_db():
    """
    Fixture for mocking database operations
    Useful for testing without actual database
    """
    class MockDB:
        def __init__(self):
            self.data = {}

        def add(self, obj):
            self.data[id(obj)] = obj

        def commit(self):
            pass

        def rollback(self):
            pass

        def close(self):
            pass

    return MockDB()


@pytest.fixture(scope="function")
def sample_user_data() -> dict:
    """
    Fixture for sample user data
    Returns common user data for testing
    """
    return {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "TestPassword123!",
    }


@pytest.fixture(scope="function")
def sample_document_data() -> dict:
    """
    Fixture for sample document data
    """
    return {
        "title": "Test Document",
        "content": "This is a test document content.",
        "author": "Test User",
        "tags": ["test", "sample"],
    }


@pytest.fixture(scope="session")
def temp_file_dir(tmp_path_factory) -> Path:
    """
    Fixture for temporary file directory
    Creates a temporary directory for file operations in tests
    """
    return tmp_path_factory.mktemp("test_files")


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch):
    """
    Fixture to reset environment variables for each test
    """
    # Store original environment
    import os
    original_env = os.environ.copy()

    # Set test environment variables
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("DEBUG", "true")

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_anthropic_client(monkeypatch):
    """
    Fixture to mock Anthropic API client
    """
    class MockAnthropicClient:
        def __init__(self, api_key: str):
            self.api_key = api_key

        def messages_create(self, **kwargs):
            class MockMessage:
                content = [type('obj', (object,), {'text': 'Mock AI response'})]

            return MockMessage()

    def mock_client(*args, **kwargs):
        return MockAnthropicClient("test-key")

    monkeypatch.setattr("anthropic.Anthropic", mock_client)
    return mock_client


@pytest.fixture
def capture_logs(caplog):
    """
    Fixture to capture log output
    """
    import logging
    caplog.set_level(logging.DEBUG)
    return caplog


# Pytest configuration
def pytest_configure(config):
    """
    PyTest configuration hook
    """
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "ui: marks tests as UI tests"
    )
