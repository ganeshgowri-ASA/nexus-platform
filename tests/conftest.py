<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
"""Pytest configuration and fixtures."""

import pytest
import asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
=======
"""
Pytest configuration and fixtures for NEXUS DMS testing.

This module provides comprehensive test fixtures including:
- Database fixtures with test session management
- Test client for API testing
- Test user fixtures with various permission levels
- Mock services for external dependencies
- Sample data generators
"""

import asyncio
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.core.config import Settings, get_settings
from backend.database import Base, get_db
from backend.models.document import (
    AccessLevel,
    Document,
    DocumentPermission,
    DocumentStatus,
    DocumentVersion,
    Folder,
    Tag,
)
from backend.models.user import User
from backend.core.security import get_password_hash


# Test settings
@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Create test settings with SQLite database."""
    settings = Settings(
        TESTING=True,
        DATABASE_URL="sqlite:///./test_nexus.db",
        TEST_DATABASE_URL="sqlite:///./test_nexus.db",
        SECRET_KEY="test-secret-key-for-testing-only-minimum-32-chars-long",
        STORAGE_PATH="./test_storage",
        STORAGE_BACKEND="local",
        VERSION_MAX_HISTORY=50,
        DEBUG=True,
        DB_ECHO=False,
    )
    return settings


@pytest.fixture(scope="session")
def test_engine(test_settings):
    """Create test database engine."""
    engine = create_engine(
        test_settings.TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Enable SQLite foreign keys
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """
    Create a fresh database session for each test.

    This fixture:
    - Creates all tables before the test
    - Provides a clean session
    - Rolls back all changes after the test
    - Drops all tables after the test
    """
    # Create tables
    Base.metadata.create_all(bind=test_engine)

    # Create session
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )
    session = TestingSessionLocal()
=======
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
>>>>>>> origin/claude/nexus-platform-setup-01GgK8vgMUpRwMXvUmBp8eNW

    try:
        yield session
    finally:
<<<<<<< HEAD
        session.rollback()
        session.close()
        # Drop tables
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def test_app(db_session, test_settings) -> FastAPI:
    """Create test FastAPI application."""
    from backend.main import app

    # Override dependencies
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_settings():
        return test_settings

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = override_get_settings

    return app


@pytest.fixture(scope="function")
def client(test_app) -> TestClient:
    """Create test client for API testing."""
    return TestClient(test_app)


# User fixtures
@pytest.fixture
def test_password() -> str:
    """Default test password."""
    return "TestPass123!@#"


@pytest.fixture
def admin_user(db_session, test_password) -> User:
    """Create admin user for testing."""
    user = User(
        email="admin@test.com",
        username="admin",
        full_name="Admin User",
        hashed_password=get_password_hash(test_password),
        is_active=True,
        is_superuser=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def regular_user(db_session, test_password) -> User:
    """Create regular user for testing."""
    user = User(
        email="user@test.com",
        username="testuser",
        full_name="Test User",
        hashed_password=get_password_hash(test_password),
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def other_user(db_session, test_password) -> User:
    """Create another user for permission testing."""
    user = User(
        email="other@test.com",
        username="otheruser",
        full_name="Other User",
        hashed_password=get_password_hash(test_password),
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# Document fixtures
@pytest.fixture
def test_folder(db_session, regular_user) -> Folder:
    """Create test folder."""
    folder = Folder(
        name="Test Folder",
        description="Test folder for unit tests",
        path="/test",
        owner_id=regular_user.id,
        is_public=False,
    )
    db_session.add(folder)
    db_session.commit()
    db_session.refresh(folder)
    return folder


@pytest.fixture
def test_document(db_session, regular_user, test_folder, temp_storage_path) -> Document:
    """Create test document."""
    # Create test file
    test_file_path = temp_storage_path / "test_document.txt"
    test_file_path.write_text("Test document content")

    document = Document(
        title="Test Document",
        description="Test document for unit tests",
        file_name="test_document.txt",
        file_path=str(test_file_path),
        file_size=len("Test document content"),
        mime_type="text/plain",
        file_hash="abc123",
        status=DocumentStatus.ACTIVE,
        owner_id=regular_user.id,
        folder_id=test_folder.id,
        is_public=False,
        current_version=1,
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return document


@pytest.fixture
def public_document(db_session, regular_user, temp_storage_path) -> Document:
    """Create public test document."""
    test_file_path = temp_storage_path / "public_doc.txt"
    test_file_path.write_text("Public document content")

    document = Document(
        title="Public Document",
        description="Public test document",
        file_name="public_doc.txt",
        file_path=str(test_file_path),
        file_size=len("Public document content"),
        mime_type="text/plain",
        file_hash="def456",
        status=DocumentStatus.ACTIVE,
        owner_id=regular_user.id,
        is_public=True,
        current_version=1,
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return document


@pytest.fixture
def document_with_permission(
    db_session, regular_user, other_user, test_document
) -> tuple[Document, DocumentPermission]:
    """Create document with permission granted to another user."""
    permission = DocumentPermission(
        document_id=test_document.id,
        user_id=other_user.id,
        access_level=AccessLevel.EDIT,
        granted_by_id=regular_user.id,
    )
    db_session.add(permission)
    db_session.commit()
    db_session.refresh(permission)
    return test_document, permission


@pytest.fixture
def test_tag(db_session, regular_user) -> Tag:
    """Create test tag."""
    tag = Tag(
        name="test-tag",
        color="#FF5733",
        created_by_id=regular_user.id,
    )
    db_session.add(tag)
    db_session.commit()
    db_session.refresh(tag)
    return tag


# Storage fixtures
@pytest.fixture
def temp_storage_path() -> Generator[Path, None, None]:
    """Create temporary storage directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir)
        yield storage_path


@pytest.fixture
def mock_storage_backend():
    """Create mock storage backend."""
    mock = MagicMock()
    mock.upload_file = AsyncMock(return_value="test/path/file.txt")
    mock.download_file = AsyncMock(return_value=b"test content")
    mock.delete_file = AsyncMock(return_value=True)
    mock.file_exists = AsyncMock(return_value=True)
    mock.get_file_size = AsyncMock(return_value=1024)
    mock.list_files = AsyncMock(return_value=["file1.txt", "file2.txt"])
    mock.copy_file = AsyncMock(return_value="new/path/file.txt")
    return mock


# Sample data generators
@pytest.fixture
def sample_upload_file():
    """Create sample upload file for testing."""
    from io import BytesIO
    from fastapi import UploadFile

    def _create_upload_file(
        filename: str = "test.txt",
        content: bytes = b"test content",
        content_type: str = "text/plain",
    ) -> UploadFile:
        file = BytesIO(content)
        return UploadFile(
            file=file,
            filename=filename,
            headers={"content-type": content_type},
        )

    return _create_upload_file


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Generate minimal valid PDF bytes for testing."""
    # Minimal PDF structure
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000317 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
410
%%EOF
"""
    return pdf_content


@pytest.fixture
def sample_image_bytes() -> bytes:
    """Generate minimal valid PNG bytes for testing."""
    # Minimal 1x1 red PNG
    png_content = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf'
        b'\xc0\x00\x00\x00\x03\x00\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    return png_content


# Mock service fixtures
@pytest.fixture
def mock_permission_service():
    """Create mock permission service."""
    mock = MagicMock()
    mock.check_document_permission = AsyncMock(return_value=True)
    mock.get_document_access_level = AsyncMock(return_value=AccessLevel.ADMIN)
    mock.grant_document_permission = AsyncMock()
    mock.revoke_document_permission = AsyncMock()
    mock.list_document_permissions = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def mock_version_control_service():
    """Create mock version control service."""
    mock = MagicMock()
    mock.create_version = AsyncMock()
    mock.get_version = AsyncMock()
    mock.list_versions = AsyncMock(return_value=[])
    mock.get_version_content = AsyncMock(return_value=b"version content")
    mock.compare_versions = AsyncMock(return_value={})
    mock.rollback_to_version = AsyncMock()
    return mock


@pytest.fixture
def mock_search_service():
    """Create mock search service."""
    mock = MagicMock()
    mock.search = AsyncMock()
    mock.save_search = AsyncMock()
    mock.get_saved_searches = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def mock_workflow_engine():
    """Create mock workflow engine."""
    mock = MagicMock()
    mock.start_workflow = AsyncMock()
    mock.get_workflow = AsyncMock()
    mock.approve_step = AsyncMock()
    mock.reject_step = AsyncMock()
    mock.cancel_workflow = AsyncMock()
    return mock


@pytest.fixture
def mock_anthropic_client():
    """Create mock Anthropic API client."""
    mock = MagicMock()
    mock.messages.create = AsyncMock(
        return_value=MagicMock(
            content=[
                MagicMock(
                    text="AI generated summary of the document content.",
                    type="text"
                )
            ],
            stop_reason="end_turn",
        )
    )
    return mock


# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop():
=======
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
>>>>>>> origin/claude/ab-testing-module-01D3o2ivEGbVpUmsgesHtDjA
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


<<<<<<< HEAD
# Authentication helpers
@pytest.fixture
def auth_headers(client, regular_user, test_password):
    """Generate authentication headers for API requests."""
    def _get_headers(user: User = None, password: str = None) -> dict:
        user = user or regular_user
        password = password or test_password

        response = client.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": password},
        )

        if response.status_code == 200:
            token = response.json()["access_token"]
            return {"Authorization": f"Bearer {token}"}
        return {}

    return _get_headers


@pytest.fixture
def admin_headers(client, admin_user, test_password, auth_headers):
    """Generate admin authentication headers."""
    return auth_headers(admin_user, test_password)


# Data factory fixtures
@pytest.fixture
def document_factory(db_session):
    """Factory for creating test documents."""
    def _create_document(
        title: str = "Factory Document",
        owner: User = None,
        status: DocumentStatus = DocumentStatus.ACTIVE,
        is_public: bool = False,
        **kwargs
    ) -> Document:
        if owner is None:
            # Create temporary owner
            owner = User(
                email=f"owner_{datetime.utcnow().timestamp()}@test.com",
                username=f"owner_{datetime.utcnow().timestamp()}",
                full_name="Document Owner",
                hashed_password=get_password_hash("password"),
                is_active=True,
            )
            db_session.add(owner)
            db_session.commit()

        doc = Document(
            title=title,
            file_name=f"{title.lower().replace(' ', '_')}.txt",
            file_path=f"/test/{title.lower().replace(' ', '_')}.txt",
            file_size=1024,
            mime_type="text/plain",
            file_hash=f"hash_{datetime.utcnow().timestamp()}",
            status=status,
            owner_id=owner.id,
            is_public=is_public,
            current_version=1,
            **kwargs
        )
        db_session.add(doc)
        db_session.commit()
        db_session.refresh(doc)
        return doc

    return _create_document


@pytest.fixture
def user_factory(db_session):
    """Factory for creating test users."""
    def _create_user(
        email: str = None,
        username: str = None,
        is_superuser: bool = False,
        **kwargs
    ) -> User:
        timestamp = datetime.utcnow().timestamp()
        email = email or f"user_{timestamp}@test.com"
        username = username or f"user_{timestamp}"

        user = User(
            email=email,
            username=username,
            full_name=f"User {username}",
            hashed_password=get_password_hash("password"),
            is_active=True,
            is_superuser=is_superuser,
            is_verified=True,
            **kwargs
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _create_user


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_storage(temp_storage_path):
    """Automatically cleanup storage after each test."""
    yield
    # Cleanup is handled by TemporaryDirectory context manager


@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks after each test."""
    yield
    # Mocks are recreated for each test, so no explicit reset needed
=======
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
>>>>>>> origin/claude/nexus-platform-setup-01GgK8vgMUpRwMXvUmBp8eNW


# Pytest configuration
def pytest_configure(config):
<<<<<<< HEAD
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
>>>>>>> origin/claude/build-dms-module-01NEqPB75CF7J7XEDr4aawai
=======
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
>>>>>>> origin/claude/ab-testing-module-01D3o2ivEGbVpUmsgesHtDjA
=======
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
>>>>>>> origin/claude/nexus-platform-setup-01GgK8vgMUpRwMXvUmBp8eNW
=======
"""Pytest configuration and fixtures."""
import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database.base import Base
from core.auth.models import User


# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    """Create test database engine."""
    test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(test_engine)
    yield test_engine
    Base.metadata.drop_all(test_engine)


@pytest.fixture(scope="function")
def db_session(engine):
    """Create a new database session for a test."""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        full_name="Test User"
    )
    user.set_password("password123")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_dataframe():
    """Create sample DataFrame for testing."""
    import pandas as pd
    return pd.DataFrame({
        'A': [1, 2, 3, 4, 5],
        'B': ['a', 'b', 'c', 'd', 'e'],
        'C': [10.5, 20.3, 30.1, 40.8, 50.2]
    })
>>>>>>> origin/claude/excel-spreadsheet-editor-01ERQuTgtV3Kb8CMNgURhB2E
=======
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
>>>>>>> origin/claude/notes-taking-module-013StF1A3r6dn5NufjWAXYTn
