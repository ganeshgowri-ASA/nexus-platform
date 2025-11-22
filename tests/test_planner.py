"""
Tests for content planner module.
"""
import pytest
from datetime import datetime, timedelta

from modules.content_calendar.planner import ContentPlanner
from modules.content_calendar.calendar_types import (
    CalendarEvent,
    ScheduleConfig,
    ContentFormat,
    Priority,
    ApprovalStatus,
)


class TestContentPlanner:
    """Test ContentPlanner class."""

    def test_create_event(self, db_session, sample_user):
        """Test creating a calendar event."""
        planner = ContentPlanner(db_session)

        schedule = ScheduleConfig(
            scheduled_time=datetime.utcnow() + timedelta(days=1),
            timezone="UTC",
        )

        event = CalendarEvent(
            title="Test Event",
            content="Test content",
            content_type=ContentFormat.TEXT,
            status=ApprovalStatus.DRAFT,
            priority=Priority.MEDIUM,
            schedule=schedule,
            creator_id=sample_user.id,
        )

        created_event = planner.create_event(event, sample_user.id)

        assert created_event.id is not None
        assert created_event.title == "Test Event"
        assert created_event.creator_id == sample_user.id

    def test_get_calendar_view(self, db_session, sample_content, sample_user):
        """Test getting calendar view."""
        planner = ContentPlanner(db_session)

        start_date = datetime.utcnow()
        end_date = datetime.utcnow() + timedelta(days=7)

        events = planner.get_calendar_view(
            start_date=start_date,
            end_date=end_date,
            user_id=sample_user.id,
        )

        assert isinstance(events, list)
        assert len(events) > 0

    def test_move_event(self, db_session, sample_content):
        """Test moving an event."""
        planner = ContentPlanner(db_session)

        new_datetime = datetime.utcnow() + timedelta(days=2)
        moved_event = planner.move_event(
            event_id=sample_content.id,
            new_datetime=new_datetime,
        )

        assert moved_event.id == sample_content.id
        # Note: The actual datetime comparison would need proper handling

    def test_delete_event(self, db_session, sample_content):
        """Test deleting an event."""
        planner = ContentPlanner(db_session)

        success = planner.delete_event(sample_content.id)

        assert success is True

    def test_duplicate_event(self, db_session, sample_content):
        """Test duplicating an event."""
        planner = ContentPlanner(db_session)

        duplicated = planner.duplicate_event(sample_content.id)

        assert duplicated.id != sample_content.id
        assert "Copy" in duplicated.title
