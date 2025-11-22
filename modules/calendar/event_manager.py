"""
Event Manager Module

Handles CRUD operations for calendar events with support for:
- Single and multi-day events
- All-day events
- Event categories and colors
- Locations and video links
- Attachments and notes
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, field, asdict
import uuid
import json


class EventStatus(Enum):
    """Event status."""
    CONFIRMED = "confirmed"
    TENTATIVE = "tentative"
    CANCELLED = "cancelled"


class EventVisibility(Enum):
    """Event visibility."""
    PUBLIC = "public"
    PRIVATE = "private"
    CONFIDENTIAL = "confidential"


class AttendeeStatus(Enum):
    """Attendee response status."""
    NEEDS_ACTION = "needs_action"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    TENTATIVE = "tentative"


@dataclass
class Attendee:
    """Represents an event attendee."""
    email: str
    name: Optional[str] = None
    status: AttendeeStatus = AttendeeStatus.NEEDS_ACTION
    optional: bool = False
    organizer: bool = False
    comment: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "email": self.email,
            "name": self.name,
            "status": self.status.value,
            "optional": self.optional,
            "organizer": self.organizer,
            "comment": self.comment,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Attendee":
        """Create from dictionary."""
        return cls(
            email=data["email"],
            name=data.get("name"),
            status=AttendeeStatus(data.get("status", "needs_action")),
            optional=data.get("optional", False),
            organizer=data.get("organizer", False),
            comment=data.get("comment"),
        )


@dataclass
class Reminder:
    """Represents an event reminder."""
    minutes_before: int
    method: str = "email"  # email, popup, sms

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "minutes_before": self.minutes_before,
            "method": self.method,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Reminder":
        """Create from dictionary."""
        return cls(
            minutes_before=data["minutes_before"],
            method=data.get("method", "email"),
        )


@dataclass
class Event:
    """
    Represents a calendar event.

    Attributes:
        id: Unique event identifier
        title: Event title
        description: Event description
        start_time: Start datetime
        end_time: End datetime
        all_day: Whether this is an all-day event
        calendar_id: ID of the calendar this event belongs to
        location: Event location
        video_link: Video meeting link
        category: Event category
        color: Event color (hex code)
        status: Event status
        visibility: Event visibility
        organizer: Event organizer email
        attendees: List of attendees
        reminders: List of reminders
        recurrence_id: ID of parent recurring event (if this is a recurrence)
        recurrence_pattern: Recurrence pattern (if recurring)
        recurrence_exceptions: Exception dates for recurring events
        created_at: Creation timestamp
        updated_at: Last update timestamp
        tags: Event tags
        attachments: File attachments
        notes: Additional notes
    """
    title: str
    start_time: datetime
    end_time: datetime
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: Optional[str] = None
    all_day: bool = False
    calendar_id: str = "default"
    location: Optional[str] = None
    video_link: Optional[str] = None
    category: Optional[str] = None
    color: str = "#4285F4"  # Google Calendar blue
    status: EventStatus = EventStatus.CONFIRMED
    visibility: EventVisibility = EventVisibility.PUBLIC
    organizer: Optional[str] = None
    attendees: List[Attendee] = field(default_factory=list)
    reminders: List[Reminder] = field(default_factory=list)
    recurrence_id: Optional[str] = None
    recurrence_pattern: Optional[Dict[str, Any]] = None
    recurrence_exceptions: List[datetime] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    attachments: List[Dict[str, str]] = field(default_factory=list)
    notes: Optional[str] = None

    def __post_init__(self):
        """Validate event data after initialization."""
        if self.end_time <= self.start_time:
            raise ValueError("End time must be after start time")

    def duration(self) -> timedelta:
        """Get event duration."""
        return self.end_time - self.start_time

    def is_multi_day(self) -> bool:
        """Check if event spans multiple days."""
        return self.start_time.date() != self.end_time.date()

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        data = asdict(self)
        # Convert enums to strings
        data["status"] = self.status.value
        data["visibility"] = self.visibility.value
        # Convert datetime to ISO format
        data["start_time"] = self.start_time.isoformat()
        data["end_time"] = self.end_time.isoformat()
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        data["recurrence_exceptions"] = [dt.isoformat() for dt in self.recurrence_exceptions]
        # Convert attendees and reminders
        data["attendees"] = [a.to_dict() for a in self.attendees]
        data["reminders"] = [r.to_dict() for r in self.reminders]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary."""
        # Parse datetime fields
        data["start_time"] = datetime.fromisoformat(data["start_time"])
        data["end_time"] = datetime.fromisoformat(data["end_time"])
        data["created_at"] = datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        data["updated_at"] = datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat()))
        data["recurrence_exceptions"] = [
            datetime.fromisoformat(dt) for dt in data.get("recurrence_exceptions", [])
        ]
        # Parse enums
        data["status"] = EventStatus(data.get("status", "confirmed"))
        data["visibility"] = EventVisibility(data.get("visibility", "public"))
        # Parse attendees and reminders
        data["attendees"] = [Attendee.from_dict(a) for a in data.get("attendees", [])]
        data["reminders"] = [Reminder.from_dict(r) for r in data.get("reminders", [])]
        return cls(**data)


class EventManager:
    """
    Manages calendar events with CRUD operations.

    Features:
    - Create, read, update, delete events
    - Search and filter events
    - Manage attendees
    - Handle recurring events
    """

    def __init__(self, storage_backend: Optional[Any] = None):
        """
        Initialize the event manager.

        Args:
            storage_backend: Optional storage backend (e.g., database connection)
        """
        self.storage = storage_backend
        self._events: Dict[str, Event] = {}  # In-memory storage if no backend

    def create_event(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        **kwargs
    ) -> Event:
        """
        Create a new event.

        Args:
            title: Event title
            start_time: Start datetime
            end_time: End datetime
            **kwargs: Additional event properties

        Returns:
            Created Event instance
        """
        event = Event(
            title=title,
            start_time=start_time,
            end_time=end_time,
            **kwargs
        )

        self._events[event.id] = event

        if self.storage:
            self._save_to_storage(event)

        return event

    def get_event(self, event_id: str) -> Optional[Event]:
        """
        Get an event by ID.

        Args:
            event_id: Event ID

        Returns:
            Event instance or None if not found
        """
        if self.storage:
            return self._load_from_storage(event_id)
        return self._events.get(event_id)

    def update_event(self, event_id: str, **updates) -> Optional[Event]:
        """
        Update an event.

        Args:
            event_id: Event ID
            **updates: Fields to update

        Returns:
            Updated Event instance or None if not found
        """
        event = self.get_event(event_id)
        if not event:
            return None

        # Update fields
        for key, value in updates.items():
            if hasattr(event, key):
                setattr(event, key, value)

        event.updated_at = datetime.now()

        if self.storage:
            self._save_to_storage(event)
        else:
            self._events[event_id] = event

        return event

    def delete_event(self, event_id: str) -> bool:
        """
        Delete an event.

        Args:
            event_id: Event ID

        Returns:
            True if deleted, False if not found
        """
        if event_id in self._events:
            del self._events[event_id]

            if self.storage:
                self._delete_from_storage(event_id)

            return True
        return False

    def list_events(
        self,
        calendar_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        category: Optional[str] = None,
        status: Optional[EventStatus] = None,
    ) -> List[Event]:
        """
        List events with optional filters.

        Args:
            calendar_id: Filter by calendar ID
            start_date: Filter events starting after this date
            end_date: Filter events ending before this date
            category: Filter by category
            status: Filter by status

        Returns:
            List of matching events
        """
        events = list(self._events.values())

        # Apply filters
        if calendar_id:
            events = [e for e in events if e.calendar_id == calendar_id]

        if start_date:
            events = [e for e in events if e.start_time >= start_date]

        if end_date:
            events = [e for e in events if e.end_time <= end_date]

        if category:
            events = [e for e in events if e.category == category]

        if status:
            events = [e for e in events if e.status == status]

        # Sort by start time
        events.sort(key=lambda e: e.start_time)

        return events

    def search_events(self, query: str) -> List[Event]:
        """
        Search events by title, description, or location.

        Args:
            query: Search query

        Returns:
            List of matching events
        """
        query_lower = query.lower()
        results = []

        for event in self._events.values():
            if (
                query_lower in event.title.lower() or
                (event.description and query_lower in event.description.lower()) or
                (event.location and query_lower in event.location.lower())
            ):
                results.append(event)

        results.sort(key=lambda e: e.start_time)
        return results

    def add_attendee(self, event_id: str, attendee: Attendee) -> bool:
        """
        Add an attendee to an event.

        Args:
            event_id: Event ID
            attendee: Attendee to add

        Returns:
            True if added successfully
        """
        event = self.get_event(event_id)
        if not event:
            return False

        # Check if attendee already exists
        existing = [a for a in event.attendees if a.email == attendee.email]
        if existing:
            return False

        event.attendees.append(attendee)
        event.updated_at = datetime.now()

        if self.storage:
            self._save_to_storage(event)

        return True

    def remove_attendee(self, event_id: str, email: str) -> bool:
        """
        Remove an attendee from an event.

        Args:
            event_id: Event ID
            email: Attendee email

        Returns:
            True if removed successfully
        """
        event = self.get_event(event_id)
        if not event:
            return False

        original_count = len(event.attendees)
        event.attendees = [a for a in event.attendees if a.email != email]

        if len(event.attendees) < original_count:
            event.updated_at = datetime.now()
            if self.storage:
                self._save_to_storage(event)
            return True

        return False

    def update_attendee_status(
        self,
        event_id: str,
        email: str,
        status: AttendeeStatus
    ) -> bool:
        """
        Update an attendee's response status.

        Args:
            event_id: Event ID
            email: Attendee email
            status: New status

        Returns:
            True if updated successfully
        """
        event = self.get_event(event_id)
        if not event:
            return False

        for attendee in event.attendees:
            if attendee.email == email:
                attendee.status = status
                event.updated_at = datetime.now()
                if self.storage:
                    self._save_to_storage(event)
                return True

        return False

    def get_events_by_date(self, date: datetime) -> List[Event]:
        """
        Get all events on a specific date.

        Args:
            date: Target date

        Returns:
            List of events on that date
        """
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        return self.list_events(start_date=start_of_day, end_date=end_of_day)

    def _save_to_storage(self, event: Event) -> None:
        """Save event to storage backend."""
        if self.storage:
            # Implement storage backend logic here
            pass

    def _load_from_storage(self, event_id: str) -> Optional[Event]:
        """Load event from storage backend."""
        if self.storage:
            # Implement storage backend logic here
            pass
        return self._events.get(event_id)

    def _delete_from_storage(self, event_id: str) -> None:
        """Delete event from storage backend."""
        if self.storage:
            # Implement storage backend logic here
            pass
