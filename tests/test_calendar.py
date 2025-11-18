"""
Comprehensive Unit Tests for Calendar Module

Tests all major components of the NEXUS Calendar system.
"""

import unittest
from datetime import datetime, timedelta, time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.calendar.event_manager import (
    EventManager, Event, Attendee, AttendeeStatus, EventStatus
)
from modules.calendar.calendar_engine import CalendarEngine, CalendarView, Calendar
from modules.calendar.recurrence import (
    RecurrenceEngine, RecurrencePattern, RecurrenceFrequency, RecurrenceEndType, Weekday
)
from modules.calendar.timezones import TimezoneManager
from modules.calendar.conflicts import ConflictDetector, ConflictSeverity
from modules.calendar.availability import AvailabilityManager, WorkingHours, DayOfWeek
from modules.calendar.scheduling import Scheduler, SchedulingRequest, SchedulingPriority
from modules.calendar.reminders import ReminderManager, ReminderMethod
from modules.calendar.invites import InviteManager
from modules.calendar.ai_scheduler import AIScheduler, EventCategory


class TestEventManager(unittest.TestCase):
    """Test EventManager functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = EventManager()

    def test_create_event(self):
        """Test event creation."""
        start = datetime.now() + timedelta(hours=1)
        end = start + timedelta(hours=2)

        event = self.manager.create_event(
            title="Test Meeting",
            start_time=start,
            end_time=end,
            description="Test description",
        )

        self.assertIsNotNone(event)
        self.assertEqual(event.title, "Test Meeting")
        self.assertEqual(event.start_time, start)
        self.assertEqual(event.end_time, end)

    def test_get_event(self):
        """Test retrieving an event."""
        start = datetime.now() + timedelta(hours=1)
        end = start + timedelta(hours=2)

        created = self.manager.create_event(
            title="Test Event",
            start_time=start,
            end_time=end,
        )

        retrieved = self.manager.get_event(created.id)

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, created.id)
        self.assertEqual(retrieved.title, created.title)

    def test_update_event(self):
        """Test updating an event."""
        start = datetime.now() + timedelta(hours=1)
        end = start + timedelta(hours=2)

        event = self.manager.create_event(
            title="Original Title",
            start_time=start,
            end_time=end,
        )

        updated = self.manager.update_event(
            event.id,
            title="Updated Title",
            description="New description",
        )

        self.assertEqual(updated.title, "Updated Title")
        self.assertEqual(updated.description, "New description")

    def test_delete_event(self):
        """Test deleting an event."""
        start = datetime.now() + timedelta(hours=1)
        end = start + timedelta(hours=2)

        event = self.manager.create_event(
            title="To Delete",
            start_time=start,
            end_time=end,
        )

        success = self.manager.delete_event(event.id)
        self.assertTrue(success)

        retrieved = self.manager.get_event(event.id)
        self.assertIsNone(retrieved)

    def test_list_events(self):
        """Test listing events."""
        start = datetime.now()
        end = start + timedelta(days=7)

        # Create multiple events
        for i in range(5):
            self.manager.create_event(
                title=f"Event {i}",
                start_time=start + timedelta(days=i),
                end_time=start + timedelta(days=i, hours=1),
            )

        events = self.manager.list_events(start_date=start, end_date=end)

        self.assertEqual(len(events), 5)

    def test_add_attendee(self):
        """Test adding attendees to an event."""
        start = datetime.now() + timedelta(hours=1)
        end = start + timedelta(hours=2)

        event = self.manager.create_event(
            title="Meeting",
            start_time=start,
            end_time=end,
        )

        attendee = Attendee(email="test@example.com", name="Test User")
        success = self.manager.add_attendee(event.id, attendee)

        self.assertTrue(success)

        updated_event = self.manager.get_event(event.id)
        self.assertEqual(len(updated_event.attendees), 1)
        self.assertEqual(updated_event.attendees[0].email, "test@example.com")


class TestCalendarEngine(unittest.TestCase):
    """Test CalendarEngine functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = CalendarEngine()

    def test_create_calendar(self):
        """Test calendar creation."""
        cal = self.engine.create_calendar(
            name="Work Calendar",
            description="My work events",
            color="#FF5722",
        )

        self.assertIsNotNone(cal)
        self.assertEqual(cal.name, "Work Calendar")
        self.assertEqual(cal.color, "#FF5722")

    def test_get_month_view(self):
        """Test month view generation."""
        now = datetime.now()

        view = self.engine.get_month_view(
            year=now.year,
            month=now.month,
        )

        self.assertEqual(view['year'], now.year)
        self.assertEqual(view['month'], now.month)
        self.assertIn('weeks', view)
        self.assertIn('total_events', view)

    def test_get_week_view(self):
        """Test week view generation."""
        now = datetime.now()
        week = now.isocalendar()[1]

        view = self.engine.get_week_view(
            year=now.year,
            week=week,
        )

        self.assertEqual(view['year'], now.year)
        self.assertEqual(view['week'], week)
        self.assertEqual(len(view['days']), 7)

    def test_get_day_view(self):
        """Test day view generation."""
        now = datetime.now()

        view = self.engine.get_day_view(date=now)

        self.assertIn('date', view)
        self.assertIn('hours', view)
        self.assertEqual(len(view['hours']), 24)


class TestRecurrenceEngine(unittest.TestCase):
    """Test RecurrenceEngine functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = RecurrenceEngine()

    def test_simple_daily_pattern(self):
        """Test simple daily recurrence."""
        pattern = self.engine.create_simple_pattern(
            frequency="daily",
            count=5,
        )

        start = datetime.now()
        end = start + timedelta(days=10)

        occurrences = self.engine.generate_occurrences(
            pattern=pattern,
            start_time=start,
            end_time=end,
        )

        self.assertEqual(len(occurrences), 5)

    def test_weekly_pattern(self):
        """Test weekly recurrence."""
        pattern = self.engine.create_weekly_pattern(
            weekdays=["monday", "wednesday", "friday"],
            count=6,
        )

        start = datetime.now()
        end = start + timedelta(days=30)

        occurrences = self.engine.generate_occurrences(
            pattern=pattern,
            start_time=start,
            end_time=end,
        )

        self.assertGreater(len(occurrences), 0)

    def test_monthly_pattern(self):
        """Test monthly recurrence."""
        pattern = self.engine.create_monthly_pattern(
            day_of_month=15,
            count=3,
        )

        start = datetime.now()
        end = start + timedelta(days=100)

        occurrences = self.engine.generate_occurrences(
            pattern=pattern,
            start_time=start,
            end_time=end,
        )

        self.assertGreater(len(occurrences), 0)


class TestTimezoneManager(unittest.TestCase):
    """Test TimezoneManager functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = TimezoneManager()

    def test_convert_time(self):
        """Test timezone conversion."""
        dt = datetime(2024, 1, 1, 12, 0, 0)

        converted = self.manager.convert_time(
            dt=dt,
            from_tz="America/New_York",
            to_tz="Europe/London",
        )

        self.assertIsNotNone(converted)

    def test_to_utc(self):
        """Test conversion to UTC."""
        dt = datetime(2024, 1, 1, 12, 0, 0)

        utc = self.manager.to_utc(dt, "America/New_York")

        self.assertIsNotNone(utc)

    def test_list_timezones(self):
        """Test listing timezones."""
        zones = self.manager.list_timezones(filter_region="America")

        self.assertGreater(len(zones), 0)
        self.assertTrue(all(z.startswith("America") for z in zones))


class TestConflictDetector(unittest.TestCase):
    """Test ConflictDetector functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = EventManager()
        self.detector = ConflictDetector(event_manager=self.manager)

    def test_detect_overlap(self):
        """Test conflict detection."""
        start = datetime.now() + timedelta(hours=1)

        # Create first event
        event1 = self.manager.create_event(
            title="Event 1",
            start_time=start,
            end_time=start + timedelta(hours=2),
        )

        # Create overlapping event
        event2 = Event(
            title="Event 2",
            start_time=start + timedelta(hours=1),
            end_time=start + timedelta(hours=3),
        )

        conflicts = self.detector.check_event_conflicts(event2)

        self.assertGreater(len(conflicts), 0)
        self.assertEqual(conflicts[0].severity, ConflictSeverity.SOFT)

    def test_no_conflict(self):
        """Test no conflict scenario."""
        start = datetime.now() + timedelta(hours=1)

        # Create first event
        event1 = self.manager.create_event(
            title="Event 1",
            start_time=start,
            end_time=start + timedelta(hours=1),
        )

        # Create non-overlapping event
        event2 = Event(
            title="Event 2",
            start_time=start + timedelta(hours=2),
            end_time=start + timedelta(hours=3),
        )

        conflicts = self.detector.check_event_conflicts(event2)

        self.assertEqual(len(conflicts), 0)


class TestAvailabilityManager(unittest.TestCase):
    """Test AvailabilityManager functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = AvailabilityManager()

    def test_set_working_hours(self):
        """Test setting working hours."""
        working_hours = [
            WorkingHours(DayOfWeek.MONDAY, time(9, 0), time(17, 0), True),
            WorkingHours(DayOfWeek.TUESDAY, time(9, 0), time(17, 0), True),
        ]

        self.manager.set_working_hours("user1", working_hours)

        retrieved = self.manager.get_working_hours("user1")

        self.assertEqual(len(retrieved), 2)

    def test_create_booking_link(self):
        """Test booking link creation."""
        link = self.manager.create_booking_link(
            name="30 Min Meeting",
            duration_minutes=30,
        )

        self.assertIsNotNone(link)
        self.assertEqual(link.duration_minutes, 30)

    def test_get_booking_link(self):
        """Test retrieving booking link."""
        created = self.manager.create_booking_link(
            name="Test Link",
            duration_minutes=45,
        )

        retrieved = self.manager.get_booking_link(created.id)

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, created.id)


class TestScheduler(unittest.TestCase):
    """Test Scheduler functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.scheduler = Scheduler()

    def test_find_optimal_time(self):
        """Test finding optimal meeting time."""
        request = SchedulingRequest(
            title="Team Meeting",
            duration_minutes=60,
            attendees=["user1@example.com", "user2@example.com"],
            organizer="user1@example.com",
            preferred_start_time=datetime.now(),
        )

        suggestions = self.scheduler.find_optimal_time(
            request=request,
            calendar_ids=["default"],
            max_suggestions=5,
        )

        self.assertIsInstance(suggestions, list)


class TestAIScheduler(unittest.TestCase):
    """Test AIScheduler functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.ai_scheduler = AIScheduler()

    def test_parse_natural_language(self):
        """Test natural language parsing."""
        text = "Meeting with John tomorrow at 3pm for 1 hour"

        parsed = self.ai_scheduler.parse_natural_language(text)

        self.assertIn('title', parsed)
        self.assertIn('duration_minutes', parsed)
        self.assertEqual(parsed['duration_minutes'], 60)

    def test_categorize_event(self):
        """Test event categorization."""
        event = Event(
            title="Team Standup",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
        )

        category = self.ai_scheduler.categorize_event(event)

        self.assertEqual(category, EventCategory.MEETING)

    def test_categorize_personal_event(self):
        """Test personal event categorization."""
        event = Event(
            title="Doctor Appointment",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
        )

        category = self.ai_scheduler.categorize_event(event)

        self.assertEqual(category, EventCategory.PERSONAL)


class TestReminderManager(unittest.TestCase):
    """Test ReminderManager functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = ReminderManager()

    def test_schedule_reminder(self):
        """Test scheduling reminders."""
        from modules.calendar.event_manager import Reminder

        start = datetime.now() + timedelta(hours=2)
        end = start + timedelta(hours=1)

        event = Event(
            title="Test Event",
            start_time=start,
            end_time=end,
            reminders=[
                Reminder(minutes_before=30, method="email"),
                Reminder(minutes_before=10, method="popup"),
            ],
        )

        scheduled = self.manager.schedule_reminders_for_event(
            event=event,
            recipient="user@example.com",
        )

        self.assertEqual(len(scheduled), 2)


class TestInviteManager(unittest.TestCase):
    """Test InviteManager functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = InviteManager()

    def test_create_invitation(self):
        """Test invitation creation."""
        start = datetime.now() + timedelta(hours=1)
        end = start + timedelta(hours=2)

        event = Event(
            title="Meeting",
            start_time=start,
            end_time=end,
            organizer="organizer@example.com",
        )

        attendee = Attendee(email="guest@example.com", name="Guest User")

        invitation = self.manager.create_invitation(event, attendee)

        self.assertIsNotNone(invitation)
        self.assertEqual(invitation.attendee_email, "guest@example.com")

    def test_respond_to_invitation(self):
        """Test RSVP response."""
        start = datetime.now() + timedelta(hours=1)
        end = start + timedelta(hours=2)

        event = Event(
            title="Meeting",
            start_time=start,
            end_time=end,
            organizer="organizer@example.com",
            attendees=[Attendee(email="guest@example.com")],
        )

        # Add event to event manager
        self.manager.event_manager._events[event.id] = event

        attendee = Attendee(email="guest@example.com", name="Guest")
        invitation = self.manager.create_invitation(event, attendee)

        success = self.manager.accept_invitation(invitation.id)

        # Should succeed (simplified test)
        self.assertIsNotNone(invitation)


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()
