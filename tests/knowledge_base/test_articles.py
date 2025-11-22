"""
Unit Tests for Article Management

Comprehensive test coverage for article CRUD, versioning, and publishing.
"""

import pytest
from datetime import datetime
from uuid import uuid4

from modules.knowledge_base.articles import ArticleManager
from modules.knowledge_base.kb_types import ContentStatus, AccessLevel, Language


class TestArticleManager:
    """Test suite for ArticleManager."""

    @pytest.fixture
    def article_manager(self, db_session):
        """Create ArticleManager instance."""
        return ArticleManager(db_session)

    @pytest.fixture
    def author_id(self):
        """Create test author ID."""
        return uuid4()

    @pytest.mark.asyncio
    async def test_create_article(self, article_manager, author_id):
        """Test article creation."""
        article = await article_manager.create_article(
            title="Test Article",
            content="This is test content",
            author_id=author_id,
        )

        assert article is not None
        assert article.title == "Test Article"
        assert article.content == "This is test content"
        assert article.author_id == author_id
        assert article.status == ContentStatus.DRAFT.value

    @pytest.mark.asyncio
    async def test_create_article_with_slug(self, article_manager, author_id):
        """Test article creation with custom slug."""
        article = await article_manager.create_article(
            title="Test Article",
            content="Test content",
            author_id=author_id,
            slug="custom-slug",
        )

        assert article.slug == "custom-slug"

    @pytest.mark.asyncio
    async def test_update_article(self, article_manager, author_id):
        """Test article update."""
        # Create article
        article = await article_manager.create_article(
            title="Original Title",
            content="Original content",
            author_id=author_id,
        )

        # Update article
        updated = await article_manager.update_article(
            article.id,
            updated_by=author_id,
            title="Updated Title",
        )

        assert updated.title == "Updated Title"
        assert updated.content == "Original content"

    @pytest.mark.asyncio
    async def test_publish_article(self, article_manager, author_id):
        """Test article publishing."""
        # Create draft article
        article = await article_manager.create_article(
            title="Test Article",
            content="Test content",
            author_id=author_id,
        )

        assert article.status == ContentStatus.DRAFT.value

        # Publish article
        published = await article_manager.publish_article(article.id)

        assert published.status == ContentStatus.PUBLISHED.value
        assert published.published_at is not None

    @pytest.mark.asyncio
    async def test_get_article(self, article_manager, author_id):
        """Test getting article by ID."""
        # Create article
        article = await article_manager.create_article(
            title="Test Article",
            content="Test content",
            author_id=author_id,
        )

        # Get article
        retrieved = await article_manager.get_article(article_id=article.id)

        assert retrieved is not None
        assert retrieved.id == article.id
        assert retrieved.title == article.title

    @pytest.mark.asyncio
    async def test_get_article_by_slug(self, article_manager, author_id):
        """Test getting article by slug."""
        # Create article
        article = await article_manager.create_article(
            title="Test Article",
            content="Test content",
            author_id=author_id,
            slug="test-slug",
        )

        # Get by slug
        retrieved = await article_manager.get_article(slug="test-slug")

        assert retrieved is not None
        assert retrieved.slug == "test-slug"

    @pytest.mark.asyncio
    async def test_list_articles(self, article_manager, author_id):
        """Test listing articles."""
        # Create multiple articles
        for i in range(5):
            await article_manager.create_article(
                title=f"Article {i}",
                content=f"Content {i}",
                author_id=author_id,
            )

        # List articles
        result = await article_manager.list_articles(limit=10)

        assert result["total"] >= 5
        assert len(result["articles"]) >= 5

    @pytest.mark.asyncio
    async def test_list_articles_with_filters(self, article_manager, author_id):
        """Test listing articles with filters."""
        # Create published and draft articles
        for i in range(3):
            article = await article_manager.create_article(
                title=f"Article {i}",
                content=f"Content {i}",
                author_id=author_id,
            )

            if i % 2 == 0:
                await article_manager.publish_article(article.id)

        # Filter by status
        result = await article_manager.list_articles(
            status=ContentStatus.PUBLISHED,
        )

        assert all(a.status == ContentStatus.PUBLISHED.value for a in result["articles"])

    @pytest.mark.asyncio
    async def test_delete_article_soft(self, article_manager, author_id):
        """Test soft delete."""
        article = await article_manager.create_article(
            title="Test Article",
            content="Test content",
            author_id=author_id,
        )

        # Soft delete
        success = await article_manager.delete_article(
            article.id,
            soft_delete=True,
        )

        assert success is True

        # Check article is archived
        deleted = await article_manager.get_article(
            article_id=article.id,
            increment_views=False,
        )

        assert deleted.status == ContentStatus.ARCHIVED.value

    @pytest.mark.asyncio
    async def test_article_with_tags(self, article_manager, author_id):
        """Test article creation with tags."""
        article = await article_manager.create_article(
            title="Test Article",
            content="Test content",
            author_id=author_id,
            tags=["python", "tutorial", "api"],
        )

        assert len(article.tags) == 3
        assert any(tag.name == "python" for tag in article.tags)

    @pytest.mark.asyncio
    async def test_view_count_increment(self, article_manager, author_id):
        """Test view count increments."""
        article = await article_manager.create_article(
            title="Test Article",
            content="Test content",
            author_id=author_id,
        )

        initial_views = article.view_count

        # Get article (increments views)
        await article_manager.get_article(article_id=article.id)

        # Get again
        retrieved = await article_manager.get_article(
            article_id=article.id,
            increment_views=False,
        )

        assert retrieved.view_count == initial_views + 1


# Fixtures for database session (implement based on your setup)
@pytest.fixture
def db_session():
    """Create database session for testing."""
    # Implement your test database setup
    # Return a test database session
    pass


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
