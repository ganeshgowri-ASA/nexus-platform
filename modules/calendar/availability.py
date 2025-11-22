"""
Availability Manager Module

Manages user availability, free/busy time, working hours, and booking links.
"""

from datetime import datetime, timedelta, time
from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass, field, asdict
from enum import Enum

from .event_manager import Event, EventManager


class AvailabilityStatus(Enum):
    """User availability status."""
    FREE = "free"
    BUSY = "busy"
    TENTATIVE = "tentative"
    OUT_OF_OFFICE = "out_of_office"


class DayOfWeek(Enum):
    """Days of the week."""
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


@dataclass
class WorkingHours:
    """
    Represents working hours for a specific day.

    Attributes:
        day: Day of week
        start_time: Start time (e.g., time(9, 0) for 9:00 AM)
        end_time: End time (e.g., time(17, 0) for 5:00 PM)
        enabled: Whether working hours are enabled for this day
    """
    day: DayOfWeek
    start_time: time = time(9, 0)  # 9:00 AM
    end_time: time = time(17, 0)  # 5:00 PM
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "day": self.day.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkingHours":
        """Create from dictionary."""
        return cls(
            day=DayOfWeek(data["day"]),
            start_time=time.fromisoformat(data["start_time"]),
            end_time=time.fromisoformat(data["end_time"]),
            enabled=data.get("enabled", True),
        )


@dataclass
class TimeSlot:
    """
    Represents a time slot with availability status.

    Attributes:
        start: Start datetime
        end: End datetime
        status: Availability status
        event_id: Associated event ID (if busy)
        event_title: Associated event title (if busy)
    """
    start: datetime
    end: datetime
    status: AvailabilityStatus
    event_id: Optional[str] = None
    event_title: Optional[str] = None

    def duration_minutes(self) -> int:
        """Get duration in minutes."""
        return int((self.end - self.start).total_seconds() / 60)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "status": self.status.value,
            "event_id": self.event_id,
            "event_title": self.event_title,
            "duration_minutes": self.duration_minutes(),
        }


@dataclass
class BookingLink:
    """
    Represents a booking link for scheduling meetings.

    Attributes:
        id: Unique booking link ID
        name: Link name/title
        duration_minutes: Meeting duration
        description: Link description
        link_code: Unique URL code
        active: Whether link is active
        buffer_minutes: Buffer time before/after meetings
        max_bookings_per_day: Maximum bookings per day
        advance_booking_days: How far in advance bookings are allowed
        working_hours: Working hours when bookings are allowed
        created_at: Creation timestamp
    """
    name: str
    duration_minutes: int
    id: str = field(default_factory=lambda: f"booking_{datetime.now().timestamp()}")
    description: Optional[str] = None
    link_code: str = field(default_factory=lambda: f"book_{datetime.now().timestamp()}")
    active: bool = True
    buffer_minutes: int = 0
    max_bookings_per_day: Optional[int] = None
    advance_booking_days: int = 30
    working_hours: List[WorkingHours] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "duration_minutes": self.duration_minutes,
            "description": self.description,
            "link_code": self.link_code,
            "active": self.active,
            "buffer_minutes": self.buffer_minutes,
            "max_bookings_per_day": self.max_bookings_per_day,
            "advance_booking_days": self.advance_booking_days,
            "working_hours": [wh.to_dict() for wh in self.working_hours],
            "created_at": self.created_at.isoformat(),
        }


class AvailabilityManager:
    """
    Manages user availability and free/busy time.

    Features:
    - Track working hours
    - Get free/busy time
    - Generate booking links
    - Find available time slots
    - Manage out-of-office periods
    """

    def __init__(
        self,
        event_manager: Optional[EventManager] = None,
    ):
        """
        Initialize the availability manager.

        Args:
            event_manager: Event manager instance
        """
        self.event_manager = event_manager or EventManager()
        self._working_hours: Dict[str, List[WorkingHours]] = {}  # user_id -> working hours
        self._booking_links: Dict[str, BookingLink] = {}
        self._out_of_office: Dict[str, List[Dict[str, datetime]]] = {}  # user_id -> OOO periods

        # Set default working hours (Monday-Friday, 9-5)
        self._default_working_hours = self._create_default_working_hours()

    def _create_default_working_hours(self) -> List[WorkingHours]:
        """Create default working hours (Mon-Fri 9-5)."""
        return [
            WorkingHours(DayOfWeek.MONDAY, time(9, 0), time(17, 0), True),
            WorkingHours(DayOfWeek.TUESDAY, time(9, 0), time(17, 0), True),
            WorkingHours(DayOfWeek.WEDNESDAY, time(9, 0), time(17, 0), True),
            WorkingHours(DayOfWeek.THURSDAY, time(9, 0), time(17, 0), True),
            WorkingHours(DayOfWeek.FRIDAY, time(9, 0), time(17, 0), True),
            WorkingHours(DayOfWeek.SATURDAY, time(9, 0), time(17, 0), False),
            WorkingHours(DayOfWeek.SUNDAY, time(9, 0), time(17, 0), False),
        ]

    def set_working_hours(
        self,
        user_id: str,
        working_hours: List[WorkingHours],
    ) -> None:
        """
        Set working hours for a user.

        Args:
            user_id: User ID
            working_hours: List of working hours for each day
        """
        self._working_hours[user_id] = working_hours

    def get_working_hours(
        self,
        user_id: str,
    ) -> List[WorkingHours]:
        """
        Get working hours for a user.

        Args:
            user_id: User ID

        Returns:
            List of working hours
        """
        return self._working_hours.get(user_id, self._default_working_hours)

    def get_free_busy(
        self,
        calendar_ids: List[str],
        start_date: datetime,
        end_date: datetime,
        slot_duration_minutes: int = 30,
    ) -> List[TimeSlot]:
        """
        Get free/busy time slots for a date range.

        Args:
            calendar_ids: Calendar IDs to check
            start_date: Start of range
            end_date: End of range
            slot_duration_minutes: Duration of each time slot

        Returns:
            List of time slots with availability status
        """
        slots = []

        # Get all events in range
        all_events = []
        for cal_id in calendar_ids:
            events = self.event_manager.list_events(
                calendar_id=cal_id,
                start_date=start_date,
                end_date=end_date,
            )
            all_events.extend(events)

        # Sort events by start time
        all_events.sort(key=lambda e: e.start_time)

        # Generate time slots
        current = start_date
        slot_delta = timedelta(minutes=slot_duration_minutes)

        while current < end_date:
            slot_end = current + slot_delta

            # Check if this slot overlaps with any event
            status = AvailabilityStatus.FREE
            event_id = None
            event_title = None

            for event in all_events:
                # Check for overlap
                if event.start_time < slot_end and event.end_time > current:
                    if event.status.value == "tentative":
                        status = AvailabilityStatus.TENTATIVE
                    else:
                        status = AvailabilityStatus.BUSY
                    event_id = event.id
                    event_title = event.title
                    break

            slots.append(TimeSlot(
                start=current,
                end=slot_end,
                status=status,
                event_id=event_id,
                event_title=event_title,
            ))

            current = slot_end

        return slots

    def find_available_slots(
        self,
        calendar_ids: List[str],
        start_date: datetime,
        end_date: datetime,
        duration_minutes: int,
        user_id: Optional[str] = None,
    ) -> List[TimeSlot]:
        """
        Find available time slots for scheduling.

        Args:
            calendar_ids: Calendar IDs to check
            start_date: Start of range
            end_date: End of range
            duration_minutes: Required duration
            user_id: Optional user ID for working hours

        Returns:
            List of available time slots
        """
        available = []
        working_hours = self.get_working_hours(user_id) if user_id else self._default_working_hours

        # Get free/busy time
        slots = self.get_free_busy(
            calendar_ids=calendar_ids,
            start_date=start_date,
            end_date=end_date,
            slot_duration_minutes=15,  # Check in 15-minute increments
        )

        # Find continuous free periods
        current_free_start = None
        current_free_duration = 0

        for slot in slots:
            # Check if slot is during working hours
            day_of_week = DayOfWeek(slot.start.weekday())
            work_hours = next((wh for wh in working_hours if wh.day == day_of_week), None)

            if not work_hours or not work_hours.enabled:
                current_free_start = None
                current_free_duration = 0
                continue

            # Check if slot time is within working hours
            slot_time = slot.start.time()
            if not (work_hours.start_time <= slot_time < work_hours.end_time):
                current_free_start = None
                current_free_duration = 0
                continue

            # Check if slot is free
            if slot.status == AvailabilityStatus.FREE:
                if current_free_start is None:
                    current_free_start = slot.start

                current_free_duration += slot.duration_minutes()

                # If we have enough free time, add it as available
                if current_free_duration >= duration_minutes:
                    available.append(TimeSlot(
                        start=current_free_start,
                        end=current_free_start + timedelta(minutes=duration_minutes),
                        status=AvailabilityStatus.FREE,
                    ))

                    # Move to next potential slot
                    current_free_start = slot.end
                    current_free_duration = 0
            else:
                current_free_start = None
                current_free_duration = 0

        return available

    def create_booking_link(
        self,
        name: str,
        duration_minutes: int,
        **kwargs
    ) -> BookingLink:
        """
        Create a booking link.

        Args:
            name: Link name
            duration_minutes: Meeting duration
            **kwargs: Additional booking link properties

        Returns:
            Created BookingLink instance
        """
        link = BookingLink(
            name=name,
            duration_minutes=duration_minutes,
            **kwargs
        )

        self._booking_links[link.id] = link
        return link

    def get_booking_link(self, link_id: str) -> Optional[BookingLink]:
        """
        Get a booking link by ID.

        Args:
            link_id: Booking link ID

        Returns:
            BookingLink instance or None
        """
        return self._booking_links.get(link_id)

    def get_booking_link_by_code(self, link_code: str) -> Optional[BookingLink]:
        """
        Get a booking link by its URL code.

        Args:
            link_code: Booking link code

        Returns:
            BookingLink instance or None
        """
        for link in self._booking_links.values():
            if link.link_code == link_code:
                return link
        return None

    def get_available_booking_slots(
        self,
        booking_link: BookingLink,
        calendar_ids: List[str],
        start_date: datetime,
        days: int = 7,
    ) -> List[TimeSlot]:
        """
        Get available slots for a booking link.

        Args:
            booking_link: Booking link
            calendar_ids: Calendar IDs to check
            start_date: Start date
            days: Number of days to show

        Returns:
            List of available time slots
        """
        end_date = start_date + timedelta(days=days)

        # Check advance booking limit
        max_date = datetime.now() + timedelta(days=booking_link.advance_booking_days)
        if end_date > max_date:
            end_date = max_date

        # Find available slots
        return self.find_available_slots(
            calendar_ids=calendar_ids,
            start_date=start_date,
            end_date=end_date,
            duration_minutes=booking_link.duration_minutes,
        )

    def add_out_of_office(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
        reason: Optional[str] = None,
    ) -> None:
        """
        Add an out-of-office period.

        Args:
            user_id: User ID
            start_date: Start of OOO period
            end_date: End of OOO period
            reason: Optional reason
        """
        if user_id not in self._out_of_office:
            self._out_of_office[user_id] = []

        self._out_of_office[user_id].append({
            "start": start_date,
            "end": end_date,
            "reason": reason,
        })

    def is_out_of_office(
        self,
        user_id: str,
        date: datetime,
    ) -> bool:
        """
        Check if a user is out of office on a specific date.

        Args:
            user_id: User ID
            date: Date to check

        Returns:
            True if user is out of office
        """
        if user_id not in self._out_of_office:
            return False

        for ooo in self._out_of_office[user_id]:
            if ooo["start"] <= date <= ooo["end"]:
                return True

        return False

    def get_availability_summary(
        self,
        calendar_ids: List[str],
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """
        Get a summary of availability for a date range.

        Args:
            calendar_ids: Calendar IDs to check
            start_date: Start of range
            end_date: End of range

        Returns:
            Availability summary with statistics
        """
        slots = self.get_free_busy(calendar_ids, start_date, end_date)

        free_slots = [s for s in slots if s.status == AvailabilityStatus.FREE]
        busy_slots = [s for s in slots if s.status == AvailabilityStatus.BUSY]
        tentative_slots = [s for s in slots if s.status == AvailabilityStatus.TENTATIVE]

        total_minutes = sum(s.duration_minutes() for s in slots)
        free_minutes = sum(s.duration_minutes() for s in free_slots)
        busy_minutes = sum(s.duration_minutes() for s in busy_slots)
        tentative_minutes = sum(s.duration_minutes() for s in tentative_slots)

        return {
            "total_minutes": total_minutes,
            "free_minutes": free_minutes,
            "busy_minutes": busy_minutes,
            "tentative_minutes": tentative_minutes,
            "free_percentage": (free_minutes / total_minutes * 100) if total_minutes > 0 else 0,
            "busy_percentage": (busy_minutes / total_minutes * 100) if total_minutes > 0 else 0,
            "total_slots": len(slots),
            "free_slots": len(free_slots),
            "busy_slots": len(busy_slots),
            "tentative_slots": len(tentative_slots),
        }
