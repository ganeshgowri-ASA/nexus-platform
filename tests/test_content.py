"""
Tests for content manager module.
"""
import pytest

from modules.content_calendar.content import ContentManager
from modules.content_calendar.calendar_types import ContentFormat


class TestContentManager:
    """Test ContentManager class."""

    def test_create_content(self, db_session, sample_user):
        """Test creating content."""
        manager = ContentManager(db_session)

        content = manager.create_content(
            title="Test Post",
            content="This is a test post",
            content_type=ContentFormat.TEXT,
            creator_id=sample_user.id,
        )

        assert content.id is not None
        assert content.title == "Test Post"
        assert content.creator_id == sample_user.id

    def test_get_content(self, db_session, sample_content):
        """Test getting content by ID."""
        manager = ContentManager(db_session)

        content = manager.get_content(sample_content.id)

        assert content is not None
        assert content.id == sample_content.id
        assert content.title == sample_content.title

    def test_search_content(self, db_session, sample_content):
        """Test searching content."""
        manager = ContentManager(db_session)

        results = manager.search_content(query="Test", limit=10)

        assert isinstance(results, list)
        assert len(results) > 0

    def test_create_template(self, db_session):
        """Test creating content template."""
        manager = ContentManager(db_session)

        template = manager.create_template(
            name="Test Template",
            description="Template for testing",
            content_type=ContentFormat.TEXT,
            template_content="Hello {{name}}!",
            variables=["name"],
        )

        assert template["id"] is not None
        assert template["name"] == "Test Template"
        assert "name" in template["variables"]

    def test_apply_template(self, db_session):
        """Test applying template."""
        manager = ContentManager(db_session)

        # Create template
        template = manager.create_template(
            name="Greeting",
            description="Greeting template",
            content_type=ContentFormat.TEXT,
            template_content="Hello {{name}}! Welcome to {{place}}.",
            variables=["name", "place"],
        )

        # Apply template
        content = manager.apply_template(
            template_id=template["id"],
            variables={"name": "John", "place": "NEXUS"},
        )

        assert "John" in content
        assert "NEXUS" in content
