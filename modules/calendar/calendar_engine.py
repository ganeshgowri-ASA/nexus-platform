"""
Calendar Engine Module

Main calendar logic for managing calendars, views, and event organization.
"""

from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
import calendar
from dataclasses import dataclass, field, asdict

from .event_manager import Event, EventManager
from .recurrence import RecurrenceEngine, RecurrencePattern
from .timezones import TimezoneManager


class CalendarView(Enum):
    """Calendar view types."""
    MONTH = "month"
    WEEK = "week"
    DAY = "day"
    AGENDA = "agenda"
    YEAR = "year"
    SCHEDULE = "schedule"


class CalendarPermission(Enum):
    """Calendar sharing permissions."""
    OWNER = "owner"
    WRITE = "write"
    READ = "read"
    FREE_BUSY = "free_busy"


@dataclass
class Calendar:
    """
    Represents a calendar.

    Attributes:
        id: Unique calendar identifier
        name: Calendar name
        description: Calendar description
        color: Calendar color (hex code)
        timezone: Calendar timezone
        owner: Owner email/user ID
        visible: Whether calendar is visible
        default: Whether this is the default calendar
        shared_with: Dict of user emails to permissions
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    name: str
    id: str = field(default_factory=lambda: f"cal_{datetime.now().timestamp()}")
    description: Optional[str] = None
    color: str = "#039BE5"  # Light blue
    timezone: str = "UTC"
    owner: Optional[str] = None
    visible: bool = True
    default: bool = False
    shared_with: Dict[str, CalendarPermission] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert calendar to dictionary."""
        data = asdict(self)
        data["shared_with"] = {k: v.value for k, v in self.shared_with.items()}
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Calendar":
        """Create calendar from dictionary."""
        data["shared_with"] = {
            k: CalendarPermission(v) for k, v in data.get("shared_with", {}).items()
        }
        data["created_at"] = datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        data["updated_at"] = datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat()))
        return cls(**data)


class CalendarEngine:
    """
    Main calendar engine for managing calendars and views.

    Features:
    - Multiple calendar management
    - Calendar views (month, week, day, agenda, year)
    - Calendar sharing
    - Event organization
    - View generation
    """

    def __init__(
        self,
        event_manager: Optional[EventManager] = None,
        recurrence_engine: Optional[RecurrenceEngine] = None,
        timezone_manager: Optional[TimezoneManager] = None,
    ):
        """
        Initialize the calendar engine.

        Args:
            event_manager: Event manager instance
            recurrence_engine: Recurrence engine instance
            timezone_manager: Timezone manager instance
        """
        self.event_manager = event_manager or EventManager()
        self.recurrence_engine = recurrence_engine or RecurrenceEngine()
        self.timezone_manager = timezone_manager or TimezoneManager()
        self._calendars: Dict[str, Calendar] = {}

        # Create default calendar
        self.create_calendar("My Calendar", default=True)

    def create_calendar(
        self,
        name: str,
        description: Optional[str] = None,
        color: Optional[str] = None,
        timezone: str = "UTC",
        **kwargs
    ) -> Calendar:
        """
        Create a new calendar.

        Args:
            name: Calendar name
            description: Calendar description
            color: Calendar color
            timezone: Calendar timezone
            **kwargs: Additional calendar properties

        Returns:
            Created Calendar instance
        """
        cal = Calendar(
            name=name,
            description=description,
            color=color or "#039BE5",
            timezone=timezone,
            **kwargs
        )

        self._calendars[cal.id] = cal
        return cal

    def get_calendar(self, calendar_id: str) -> Optional[Calendar]:
        """
        Get a calendar by ID.

        Args:
            calendar_id: Calendar ID

        Returns:
            Calendar instance or None
        """
        return self._calendars.get(calendar_id)

    def update_calendar(self, calendar_id: str, **updates) -> Optional[Calendar]:
        """
        Update a calendar.

        Args:
            calendar_id: Calendar ID
            **updates: Fields to update

        Returns:
            Updated Calendar instance or None
        """
        cal = self.get_calendar(calendar_id)
        if not cal:
            return None

        for key, value in updates.items():
            if hasattr(cal, key):
                setattr(cal, key, value)

        cal.updated_at = datetime.now()
        return cal

    def delete_calendar(self, calendar_id: str) -> bool:
        """
        Delete a calendar.

        Args:
            calendar_id: Calendar ID

        Returns:
            True if deleted, False if not found
        """
        if calendar_id in self._calendars:
            # Delete all events in this calendar
            events = self.event_manager.list_events(calendar_id=calendar_id)
            for event in events:
                self.event_manager.delete_event(event.id)

            del self._calendars[calendar_id]
            return True
        return False

    def list_calendars(self, visible_only: bool = True) -> List[Calendar]:
        """
        List all calendars.

        Args:
            visible_only: Only return visible calendars

        Returns:
            List of calendars
        """
        calendars = list(self._calendars.values())

        if visible_only:
            calendars = [c for c in calendars if c.visible]

        return calendars

    def share_calendar(
        self,
        calendar_id: str,
        user_email: str,
        permission: CalendarPermission
    ) -> bool:
        """
        Share a calendar with a user.

        Args:
            calendar_id: Calendar ID
            user_email: User email to share with
            permission: Permission level

        Returns:
            True if shared successfully
        """
        cal = self.get_calendar(calendar_id)
        if not cal:
            return False

        cal.shared_with[user_email] = permission
        cal.updated_at = datetime.now()
        return True

    def unshare_calendar(self, calendar_id: str, user_email: str) -> bool:
        """
        Unshare a calendar with a user.

        Args:
            calendar_id: Calendar ID
            user_email: User email to unshare with

        Returns:
            True if unshared successfully
        """
        cal = self.get_calendar(calendar_id)
        if not cal or user_email not in cal.shared_with:
            return False

        del cal.shared_with[user_email]
        cal.updated_at = datetime.now()
        return True

    def get_month_view(
        self,
        year: int,
        month: int,
        calendar_ids: Optional[List[str]] = None,
        timezone: str = "UTC"
    ) -> Dict[str, Any]:
        """
        Generate a month view.

        Args:
            year: Year
            month: Month (1-12)
            calendar_ids: Optional list of calendar IDs to include
            timezone: Timezone for display

        Returns:
            Month view data with weeks and events
        """
        # Get first and last day of month
        first_day = datetime(year, month, 1)
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)

        # Get events for the month
        events = self._get_events_for_range(first_day, last_day, calendar_ids)

        # Build calendar grid
        cal = calendar.monthcalendar(year, month)
        weeks = []

        for week in cal:
            week_data = []
            for day_num in week:
                if day_num == 0:
                    week_data.append({
                        "day": None,
                        "events": [],
                        "is_today": False,
                    })
                else:
                    day_date = datetime(year, month, day_num)
                    day_events = [
                        e for e in events
                        if e.start_time.date() == day_date.date() or
                        (e.all_day and e.start_time.date() <= day_date.date() <= e.end_time.date())
                    ]
                    week_data.append({
                        "day": day_num,
                        "date": day_date,
                        "events": day_events,
                        "is_today": day_date.date() == datetime.now().date(),
                    })
            weeks.append(week_data)

        return {
            "year": year,
            "month": month,
            "month_name": first_day.strftime("%B"),
            "weeks": weeks,
            "total_events": len(events),
        }

    def get_week_view(
        self,
        year: int,
        week: int,
        calendar_ids: Optional[List[str]] = None,
        timezone: str = "UTC"
    ) -> Dict[str, Any]:
        """
        Generate a week view.

        Args:
            year: Year
            week: Week number (1-53)
            calendar_ids: Optional list of calendar IDs to include
            timezone: Timezone for display

        Returns:
            Week view data with days and events
        """
        # Get first day of week
        first_day = datetime.strptime(f"{year}-W{week:02d}-1", "%Y-W%W-%w")
        last_day = first_day + timedelta(days=6)

        # Get events for the week
        events = self._get_events_for_range(first_day, last_day, calendar_ids)

        # Build week grid
        days = []
        current = first_day

        for i in range(7):
            day_events = [
                e for e in events
                if e.start_time.date() == current.date() or
                (e.all_day and e.start_time.date() <= current.date() <= e.end_time.date())
            ]

            days.append({
                "date": current,
                "day_name": current.strftime("%A"),
                "events": day_events,
                "is_today": current.date() == datetime.now().date(),
            })

            current += timedelta(days=1)

        return {
            "year": year,
            "week": week,
            "start_date": first_day,
            "end_date": last_day,
            "days": days,
            "total_events": len(events),
        }

    def get_day_view(
        self,
        date: datetime,
        calendar_ids: Optional[List[str]] = None,
        timezone: str = "UTC"
    ) -> Dict[str, Any]:
        """
        Generate a day view.

        Args:
            date: Date to view
            calendar_ids: Optional list of calendar IDs to include
            timezone: Timezone for display

        Returns:
            Day view data with hourly slots and events
        """
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        # Get events for the day
        events = self._get_events_for_range(start_of_day, end_of_day, calendar_ids)

        # Build hourly slots
        hours = []
        current = start_of_day

        for hour in range(24):
            hour_start = current.replace(hour=hour)
            hour_end = hour_start + timedelta(hours=1)

            hour_events = [
                e for e in events
                if not e.all_day and (
                    (e.start_time <= hour_start < e.end_time) or
                    (hour_start <= e.start_time < hour_end)
                )
            ]

            hours.append({
                "hour": hour,
                "time": hour_start,
                "events": hour_events,
            })

        # Get all-day events
        all_day_events = [e for e in events if e.all_day]

        return {
            "date": date,
            "day_name": date.strftime("%A, %B %d, %Y"),
            "hours": hours,
            "all_day_events": all_day_events,
            "is_today": date.date() == datetime.now().date(),
            "total_events": len(events),
        }

    def get_agenda_view(
        self,
        start_date: datetime,
        days: int = 7,
        calendar_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate an agenda view (list of upcoming events).

        Args:
            start_date: Start date
            days: Number of days to show
            calendar_ids: Optional list of calendar IDs to include

        Returns:
            Agenda view data with events grouped by day
        """
        end_date = start_date + timedelta(days=days)
        events = self._get_events_for_range(start_date, end_date, calendar_ids)

        # Group events by day
        grouped = {}
        current = start_date

        for i in range(days):
            day_date = current.date()
            day_events = [
                e for e in events
                if e.start_time.date() == day_date or
                (e.all_day and e.start_time.date() <= day_date <= e.end_time.date())
            ]

            if day_events:  # Only include days with events
                grouped[day_date] = {
                    "date": current,
                    "day_name": current.strftime("%A, %B %d"),
                    "events": sorted(day_events, key=lambda e: e.start_time),
                    "is_today": day_date == datetime.now().date(),
                }

            current += timedelta(days=1)

        return {
            "start_date": start_date,
            "end_date": end_date,
            "days": days,
            "grouped_events": grouped,
            "total_events": len(events),
        }

    def get_year_view(
        self,
        year: int,
        calendar_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a year view.

        Args:
            year: Year to view
            calendar_ids: Optional list of calendar IDs to include

        Returns:
            Year view data with months and event counts
        """
        months = []

        for month in range(1, 13):
            month_view = self.get_month_view(year, month, calendar_ids)
            months.append({
                "month": month,
                "month_name": month_view["month_name"],
                "event_count": month_view["total_events"],
                "weeks": month_view["weeks"],
            })

        # Get total events for the year
        start = datetime(year, 1, 1)
        end = datetime(year, 12, 31, 23, 59, 59)
        total_events = len(self._get_events_for_range(start, end, calendar_ids))

        return {
            "year": year,
            "months": months,
            "total_events": total_events,
        }

    def _get_events_for_range(
        self,
        start: datetime,
        end: datetime,
        calendar_ids: Optional[List[str]] = None,
    ) -> List[Event]:
        """
        Get all events within a date range.

        Args:
            start: Start datetime
            end: End datetime
            calendar_ids: Optional list of calendar IDs to filter

        Returns:
            List of events
        """
        all_events = []

        # Get calendars to search
        if calendar_ids:
            calendars = [self.get_calendar(cid) for cid in calendar_ids]
            calendars = [c for c in calendars if c is not None]
        else:
            calendars = self.list_calendars()

        # Get events from each calendar
        for cal in calendars:
            events = self.event_manager.list_events(
                calendar_id=cal.id,
                start_date=start,
                end_date=end,
            )

            # Expand recurring events
            for event in events:
                if event.recurrence_pattern:
                    # Generate recurring occurrences
                    pattern = RecurrencePattern.from_dict(event.recurrence_pattern)
                    occurrences = self.recurrence_engine.generate_occurrences(
                        pattern=pattern,
                        start_time=event.start_time,
                        end_time=end,
                        exceptions=set(event.recurrence_exceptions),
                    )

                    # Create event instances for each occurrence
                    for occurrence in occurrences:
                        if start <= occurrence <= end:
                            # Calculate duration
                            duration = event.end_time - event.start_time
                            occurrence_event = Event(
                                id=f"{event.id}_{occurrence.isoformat()}",
                                title=event.title,
                                description=event.description,
                                start_time=occurrence,
                                end_time=occurrence + duration,
                                all_day=event.all_day,
                                calendar_id=event.calendar_id,
                                location=event.location,
                                video_link=event.video_link,
                                category=event.category,
                                color=event.color,
                                recurrence_id=event.id,
                            )
                            all_events.append(occurrence_event)
                else:
                    all_events.append(event)

        return all_events

    def get_default_calendar(self) -> Optional[Calendar]:
        """
        Get the default calendar.

        Returns:
            Default Calendar instance or None
        """
        for cal in self._calendars.values():
            if cal.default:
                return cal
        return None
