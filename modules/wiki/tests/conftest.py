"""
Pytest Configuration and Fixtures for Wiki Tests

This module provides shared fixtures for testing the NEXUS Wiki System including:
- Database session management
- Test data factories
- Mock users and authentication
- Cleanup utilities

Author: NEXUS Platform Team
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Generator, List
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from database import Base
from modules.wiki.models import (
    WikiPage, WikiCategory, WikiTag, WikiHistory, WikiPermission,
    WikiSection, WikiLink, WikiAttachment, WikiComment, WikiTemplate,
    WikiAnalytics, WikiMacro
)
from modules.wiki.wiki_types import (
    PageStatus, ContentFormat, PermissionLevel, ChangeType,
    LinkType, AttachmentType, TemplateCategory
)


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope='session')
def engine():
    """
    Create a test database engine using in-memory SQLite.

    Returns:
        SQLAlchemy Engine instance configured for testing
    """
    # Use in-memory SQLite for fast tests
    engine = create_engine(
        'sqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
        echo=False  # Set to True for SQL debugging
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope='function')
def db_session(engine) -> Generator[Session, None, None]:
    """
    Create a new database session for each test.

    This fixture provides transaction isolation - each test gets a fresh
    database state and changes are rolled back after the test completes.

    Args:
        engine: SQLAlchemy engine fixture

    Yields:
        Database session for testing
    """
    connection = engine.connect()
    transaction = connection.begin()

    # Create session
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    yield session

    # Rollback and cleanup
    session.close()
    transaction.rollback()
    connection.close()


# ============================================================================
# USER FIXTURES
# ============================================================================

@pytest.fixture
def mock_user():
    """
    Create a mock user for testing.

    Returns:
        Dictionary with user data
    """
    return {
        'id': 1,
        'username': 'testuser',
        'email': 'test@example.com',
        'roles': ['member', 'editor']
    }


@pytest.fixture
def mock_admin_user():
    """
    Create a mock admin user for testing.

    Returns:
        Dictionary with admin user data
    """
    return {
        'id': 2,
        'username': 'adminuser',
        'email': 'admin@example.com',
        'roles': ['admin', 'member']
    }


@pytest.fixture
def mock_viewer_user():
    """
    Create a mock viewer-only user for testing.

    Returns:
        Dictionary with viewer user data
    """
    return {
        'id': 3,
        'username': 'viewer',
        'email': 'viewer@example.com',
        'roles': ['viewer']
    }


# ============================================================================
# WIKI DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_category(db_session: Session) -> WikiCategory:
    """
    Create a sample category for testing.

    Args:
        db_session: Database session

    Returns:
        Created WikiCategory instance
    """
    category = WikiCategory(
        name='Documentation',
        slug='documentation',
        description='Technical documentation and guides',
        color='#3498db',
        order=1,
        is_active=True
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


@pytest.fixture
def sample_categories(db_session: Session) -> List[WikiCategory]:
    """
    Create multiple sample categories with hierarchy.

    Args:
        db_session: Database session

    Returns:
        List of created WikiCategory instances
    """
    categories = []

    # Root categories
    docs = WikiCategory(
        name='Documentation',
        slug='docs',
        description='Technical documentation',
        color='#3498db',
        order=1,
        is_active=True
    )
    db_session.add(docs)
    db_session.flush()
    categories.append(docs)

    tutorials = WikiCategory(
        name='Tutorials',
        slug='tutorials',
        description='Step-by-step guides',
        color='#2ecc71',
        order=2,
        is_active=True
    )
    db_session.add(tutorials)
    db_session.flush()
    categories.append(tutorials)

    # Child category
    api_docs = WikiCategory(
        name='API Documentation',
        slug='api-docs',
        description='API reference',
        parent_id=docs.id,
        color='#9b59b6',
        order=1,
        is_active=True
    )
    db_session.add(api_docs)
    db_session.flush()
    categories.append(api_docs)

    db_session.commit()
    return categories


@pytest.fixture
def sample_tags(db_session: Session) -> List[WikiTag]:
    """
    Create sample tags for testing.

    Args:
        db_session: Database session

    Returns:
        List of created WikiTag instances
    """
    tags = []
    tag_data = [
        ('python', '#3776ab', 'Python programming'),
        ('javascript', '#f7df1e', 'JavaScript programming'),
        ('tutorial', '#2ecc71', 'Tutorial content'),
        ('beginner', '#e67e22', 'Beginner level'),
    ]

    for name, color, description in tag_data:
        tag = WikiTag(name=name, color=color, description=description)
        db_session.add(tag)
        tags.append(tag)

    db_session.commit()
    return tags


@pytest.fixture
def sample_page(db_session: Session, sample_category: WikiCategory, mock_user) -> WikiPage:
    """
    Create a sample wiki page for testing.

    Args:
        db_session: Database session
        sample_category: Category fixture
        mock_user: User fixture

    Returns:
        Created WikiPage instance
    """
    page = WikiPage(
        title='Getting Started',
        slug='getting-started',
        content='# Getting Started\n\nWelcome to our wiki!',
        content_format=ContentFormat.MARKDOWN,
        summary='Introduction to the wiki system',
        status=PageStatus.PUBLISHED,
        category_id=sample_category.id,
        namespace='docs',
        author_id=mock_user['id'],
        current_version=1,
        published_at=datetime.utcnow()
    )
    db_session.add(page)
    db_session.commit()
    db_session.refresh(page)
    return page


@pytest.fixture
def sample_pages(db_session: Session, sample_category: WikiCategory, mock_user) -> List[WikiPage]:
    """
    Create multiple sample pages for testing.

    Args:
        db_session: Database session
        sample_category: Category fixture
        mock_user: User fixture

    Returns:
        List of created WikiPage instances
    """
    pages = []

    page_data = [
        ('Introduction', 'introduction', PageStatus.PUBLISHED, '# Introduction\n\nWelcome!'),
        ('Advanced Topics', 'advanced-topics', PageStatus.PUBLISHED, '# Advanced\n\nAdvanced content.'),
        ('Draft Page', 'draft-page', PageStatus.DRAFT, '# Draft\n\nWork in progress.'),
    ]

    for title, slug, status, content in page_data:
        page = WikiPage(
            title=title,
            slug=slug,
            content=content,
            content_format=ContentFormat.MARKDOWN,
            status=status,
            category_id=sample_category.id,
            author_id=mock_user['id'],
            current_version=1,
            published_at=datetime.utcnow() if status == PageStatus.PUBLISHED else None
        )
        db_session.add(page)
        pages.append(page)

    db_session.commit()
    return pages


@pytest.fixture
def sample_page_with_history(db_session: Session, sample_page: WikiPage, mock_user) -> WikiPage:
    """
    Create a page with version history.

    Args:
        db_session: Database session
        sample_page: Page fixture
        mock_user: User fixture

    Returns:
        WikiPage with history
    """
    # Create initial history entry
    history1 = WikiHistory(
        page_id=sample_page.id,
        version=1,
        title=sample_page.title,
        content='# Getting Started\n\nInitial content.',
        change_type=ChangeType.CREATED,
        change_summary='Initial creation',
        changed_by=mock_user['id'],
        content_size=len('# Getting Started\n\nInitial content.'.encode('utf-8'))
    )
    db_session.add(history1)

    # Create second version
    history2 = WikiHistory(
        page_id=sample_page.id,
        version=2,
        title=sample_page.title,
        content='# Getting Started\n\nWelcome to our wiki!',
        change_type=ChangeType.EDITED,
        change_summary='Updated welcome message',
        changed_by=mock_user['id'],
        content_size=len('# Getting Started\n\nWelcome to our wiki!'.encode('utf-8'))
    )
    db_session.add(history2)

    sample_page.current_version = 2
    db_session.commit()
    db_session.refresh(sample_page)

    return sample_page


@pytest.fixture
def sample_permissions(db_session: Session, sample_page: WikiPage, mock_user, mock_viewer_user) -> List[WikiPermission]:
    """
    Create sample permissions for testing.

    Args:
        db_session: Database session
        sample_page: Page fixture
        mock_user: User fixture
        mock_viewer_user: Viewer user fixture

    Returns:
        List of created WikiPermission instances
    """
    permissions = []

    # User permission
    perm1 = WikiPermission(
        page_id=sample_page.id,
        user_id=mock_user['id'],
        permission_level=PermissionLevel.EDIT,
        granted_by=mock_user['id']
    )
    db_session.add(perm1)
    permissions.append(perm1)

    # Role permission
    perm2 = WikiPermission(
        page_id=sample_page.id,
        role='viewer',
        permission_level=PermissionLevel.READ,
        granted_by=mock_user['id']
    )
    db_session.add(perm2)
    permissions.append(perm2)

    db_session.commit()
    return permissions


# ============================================================================
# HELPER FIXTURES
# ============================================================================

@pytest.fixture
def page_factory(db_session: Session, mock_user):
    """
    Factory for creating wiki pages in tests.

    Args:
        db_session: Database session
        mock_user: User fixture

    Returns:
        Function to create pages
    """
    def _create_page(
        title: str = 'Test Page',
        slug: str = None,
        content: str = '# Test\n\nTest content.',
        status: PageStatus = PageStatus.DRAFT,
        category_id: int = None,
        author_id: int = None
    ) -> WikiPage:
        """Create a wiki page with given parameters."""
        if slug is None:
            slug = title.lower().replace(' ', '-')

        page = WikiPage(
            title=title,
            slug=slug,
            content=content,
            status=status,
            category_id=category_id,
            author_id=author_id or mock_user['id'],
            current_version=1
        )
        db_session.add(page)
        db_session.commit()
        db_session.refresh(page)
        return page

    return _create_page


@pytest.fixture
def category_factory(db_session: Session):
    """
    Factory for creating categories in tests.

    Args:
        db_session: Database session

    Returns:
        Function to create categories
    """
    def _create_category(
        name: str = 'Test Category',
        slug: str = None,
        parent_id: int = None
    ) -> WikiCategory:
        """Create a category with given parameters."""
        if slug is None:
            slug = name.lower().replace(' ', '-')

        category = WikiCategory(
            name=name,
            slug=slug,
            parent_id=parent_id,
            is_active=True
        )
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)
        return category

    return _create_category


@pytest.fixture
def tag_factory(db_session: Session):
    """
    Factory for creating tags in tests.

    Args:
        db_session: Database session

    Returns:
        Function to create tags
    """
    def _create_tag(name: str = 'test-tag') -> WikiTag:
        """Create a tag with given name."""
        tag = WikiTag(name=name.lower())
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)
        return tag

    return _create_tag


# ============================================================================
# CLEANUP UTILITIES
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_database(db_session: Session):
    """
    Automatically cleanup database after each test.

    This fixture runs automatically after each test to ensure
    a clean state for the next test.

    Args:
        db_session: Database session
    """
    yield
    # Cleanup happens automatically via session rollback in db_session fixture


# ============================================================================
# MARKERS
# ============================================================================

def pytest_configure(config):
    """
    Register custom pytest markers.

    Args:
        config: Pytest config object
    """
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "permissions: marks tests related to permissions"
    )
