"""
Scheduling Module

Handles meeting scheduling, finding optimal times, and coordinating between attendees.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass, field
from enum import Enum

from .event_manager import Event, EventManager, Attendee
from .availability import AvailabilityManager, TimeSlot, AvailabilityStatus
from .conflicts import ConflictDetector


class SchedulingPriority(Enum):
    """Priority for scheduling."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class SchedulingRequest:
    """
    Represents a request to schedule a meeting.

    Attributes:
        title: Meeting title
        duration_minutes: Meeting duration
        attendees: List of attendee emails
        organizer: Organizer email
        description: Meeting description
        location: Meeting location
        priority: Scheduling priority
        preferred_start_time: Preferred start time
        preferred_end_time: Preferred end time (latest acceptable)
        required_attendees: Emails of required attendees
        optional_attendees: Emails of optional attendees
    """
    title: str
    duration_minutes: int
    attendees: List[str]
    organizer: str
    description: Optional[str] = None
    location: Optional[str] = None
    priority: SchedulingPriority = SchedulingPriority.MEDIUM
    preferred_start_time: Optional[datetime] = None
    preferred_end_time: Optional[datetime] = None
    required_attendees: List[str] = field(default_factory=list)
    optional_attendees: List[str] = field(default_factory=list)


@dataclass
class SchedulingSuggestion:
    """
    Represents a suggested meeting time.

    Attributes:
        start_time: Suggested start time
        end_time: Suggested end time
        score: Quality score (0-100)
        available_attendees: Attendees available at this time
        unavailable_attendees: Attendees with conflicts
        conflicts: Number of conflicts
        reason: Reason for this suggestion
    """
    start_time: datetime
    end_time: datetime
    score: int
    available_attendees: List[str]
    unavailable_attendees: List[str]
    conflicts: int
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "score": self.score,
            "available_attendees": self.available_attendees,
            "unavailable_attendees": self.unavailable_attendees,
            "conflicts": self.conflicts,
            "reason": self.reason,
        }


class Scheduler:
    """
    Handles meeting scheduling and time optimization.

    Features:
    - Find optimal meeting times
    - Consider attendee availability
    - Respect working hours
    - Minimize conflicts
    - Suggest alternative times
    """

    def __init__(
        self,
        event_manager: Optional[EventManager] = None,
        availability_manager: Optional[AvailabilityManager] = None,
        conflict_detector: Optional[ConflictDetector] = None,
    ):
        """
        Initialize the scheduler.

        Args:
            event_manager: Event manager instance
            availability_manager: Availability manager instance
            conflict_detector: Conflict detector instance
        """
        self.event_manager = event_manager or EventManager()
        self.availability_manager = availability_manager or AvailabilityManager()
        self.conflict_detector = conflict_detector or ConflictDetector()

    def find_optimal_time(
        self,
        request: SchedulingRequest,
        calendar_ids: List[str],
        max_suggestions: int = 5,
    ) -> List[SchedulingSuggestion]:
        """
        Find optimal times for a meeting.

        Args:
            request: Scheduling request
            calendar_ids: Calendar IDs to check for all attendees
            max_suggestions: Maximum number of suggestions to return

        Returns:
            List of scheduling suggestions, sorted by score
        """
        suggestions = []

        # Determine search range
        if request.preferred_start_time:
            search_start = request.preferred_start_time
        else:
            search_start = datetime.now()

        if request.preferred_end_time:
            search_end = request.preferred_end_time
        else:
            search_end = search_start + timedelta(days=14)  # Search 2 weeks ahead

        # Find available slots
        available_slots = self.availability_manager.find_available_slots(
            calendar_ids=calendar_ids,
            start_date=search_start,
            end_date=search_end,
            duration_minutes=request.duration_minutes,
        )

        # Score each slot
        for slot in available_slots:
            score = self._score_time_slot(
                slot=slot,
                request=request,
                calendar_ids=calendar_ids,
            )

            # Check attendee availability
            available, unavailable, conflicts = self._check_attendee_availability(
                start_time=slot.start,
                end_time=slot.end,
                attendees=request.attendees,
                calendar_ids=calendar_ids,
            )

            # Generate reason
            if conflicts == 0:
                reason = "All attendees available"
            elif len(available) == len(request.attendees):
                reason = "No hard conflicts"
            else:
                reason = f"{len(unavailable)} attendees have conflicts"

            suggestions.append(SchedulingSuggestion(
                start_time=slot.start,
                end_time=slot.end,
                score=score,
                available_attendees=available,
                unavailable_attendees=unavailable,
                conflicts=conflicts,
                reason=reason,
            ))

        # Sort by score (highest first)
        suggestions.sort(key=lambda s: s.score, reverse=True)

        # Return top suggestions
        return suggestions[:max_suggestions]

    def _score_time_slot(
        self,
        slot: TimeSlot,
        request: SchedulingRequest,
        calendar_ids: List[str],
    ) -> int:
        """
        Score a time slot (0-100).

        Args:
            slot: Time slot to score
            request: Scheduling request
            calendar_ids: Calendar IDs

        Returns:
            Score from 0-100
        """
        score = 100

        # Penalty for conflicts
        available, unavailable, conflicts = self._check_attendee_availability(
            start_time=slot.start,
            end_time=slot.end,
            attendees=request.attendees,
            calendar_ids=calendar_ids,
        )

        # Heavy penalty for conflicts with required attendees
        required_unavailable = [
            email for email in unavailable
            if email in request.required_attendees
        ]
        if required_unavailable:
            score -= 40 * len(required_unavailable)

        # Light penalty for conflicts with optional attendees
        optional_unavailable = [
            email for email in unavailable
            if email in request.optional_attendees
        ]
        if optional_unavailable:
            score -= 10 * len(optional_unavailable)

        # Bonus for preferred time
        if request.preferred_start_time:
            time_diff = abs((slot.start - request.preferred_start_time).total_seconds() / 3600)
            if time_diff < 1:
                score += 20
            elif time_diff < 3:
                score += 10

        # Bonus for morning slots (generally preferred)
        hour = slot.start.hour
        if 9 <= hour < 12:
            score += 10
        elif 14 <= hour < 16:
            score += 5

        # Penalty for late afternoon
        if hour >= 16:
            score -= 10

        # Bonus based on priority
        if request.priority == SchedulingPriority.URGENT:
            # Prioritize earlier times
            days_away = (slot.start.date() - datetime.now().date()).days
            if days_away == 0:
                score += 20
            elif days_away == 1:
                score += 10

        return max(0, min(100, score))

    def _check_attendee_availability(
        self,
        start_time: datetime,
        end_time: datetime,
        attendees: List[str],
        calendar_ids: List[str],
    ) -> tuple[List[str], List[str], int]:
        """
        Check which attendees are available.

        Args:
            start_time: Meeting start time
            end_time: Meeting end time
            attendees: List of attendee emails
            calendar_ids: Calendar IDs

        Returns:
            Tuple of (available_emails, unavailable_emails, conflict_count)
        """
        # For this implementation, we'll assume all attendees share the same calendars
        # In a real system, each attendee would have their own calendar

        # Get events in this time range
        events = self.event_manager.list_events(
            start_date=start_time,
            end_date=end_time,
        )

        # Check for conflicts
        conflicts = 0
        for event in events:
            # Check if event overlaps with proposed time
            if event.start_time < end_time and event.end_time > start_time:
                conflicts += 1

        # Simplified: if there are conflicts, some attendees are unavailable
        if conflicts > 0:
            # In a real system, we'd check each attendee's calendar individually
            unavailable = attendees[:conflicts] if conflicts < len(attendees) else attendees
            available = [a for a in attendees if a not in unavailable]
        else:
            available = attendees
            unavailable = []

        return available, unavailable, conflicts

    def schedule_meeting(
        self,
        request: SchedulingRequest,
        calendar_id: str,
        auto_select_time: bool = False,
        time_slot: Optional[SchedulingSuggestion] = None,
    ) -> Optional[Event]:
        """
        Schedule a meeting.

        Args:
            request: Scheduling request
            calendar_id: Calendar ID to create event in
            auto_select_time: Automatically select best time
            time_slot: Specific time slot to use (if not auto-selecting)

        Returns:
            Created Event or None if scheduling failed
        """
        # Find optimal time if not provided
        if auto_select_time and not time_slot:
            suggestions = self.find_optimal_time(
                request=request,
                calendar_ids=[calendar_id],
                max_suggestions=1,
            )

            if not suggestions:
                return None

            time_slot = suggestions[0]

        if not time_slot:
            return None

        # Create attendees list
        attendees = []
        for email in request.attendees:
            attendees.append(Attendee(
                email=email,
                optional=email in request.optional_attendees,
                organizer=email == request.organizer,
            ))

        # Create event
        event = self.event_manager.create_event(
            title=request.title,
            start_time=time_slot.start_time,
            end_time=time_slot.end_time,
            description=request.description,
            location=request.location,
            calendar_id=calendar_id,
            organizer=request.organizer,
            attendees=attendees,
        )

        return event

    def find_common_availability(
        self,
        attendees: List[str],
        calendar_ids: List[str],
        duration_minutes: int,
        start_date: datetime,
        end_date: datetime,
    ) -> List[TimeSlot]:
        """
        Find times when all attendees are available.

        Args:
            attendees: List of attendee emails
            calendar_ids: Calendar IDs to check
            duration_minutes: Required duration
            start_date: Start of search range
            end_date: End of search range

        Returns:
            List of time slots when all are available
        """
        # Get all events in range
        all_events = self.event_manager.list_events(
            start_date=start_date,
            end_date=end_date,
        )

        # Find available slots
        available_slots = self.availability_manager.find_available_slots(
            calendar_ids=calendar_ids,
            start_date=start_date,
            end_date=end_date,
            duration_minutes=duration_minutes,
        )

        # Filter to only slots where all attendees are free
        common_slots = []
        for slot in available_slots:
            available, unavailable, conflicts = self._check_attendee_availability(
                start_time=slot.start,
                end_time=slot.end,
                attendees=attendees,
                calendar_ids=calendar_ids,
            )

            # Only include if all attendees are available
            if len(unavailable) == 0:
                common_slots.append(slot)

        return common_slots

    def reschedule_event(
        self,
        event_id: str,
        new_start_time: datetime,
        notify_attendees: bool = True,
    ) -> Optional[Event]:
        """
        Reschedule an existing event.

        Args:
            event_id: Event ID to reschedule
            new_start_time: New start time
            notify_attendees: Whether to notify attendees

        Returns:
            Updated Event or None if failed
        """
        event = self.event_manager.get_event(event_id)
        if not event:
            return None

        # Calculate new end time
        duration = event.end_time - event.start_time
        new_end_time = new_start_time + duration

        # Update event
        updated = self.event_manager.update_event(
            event_id=event_id,
            start_time=new_start_time,
            end_time=new_end_time,
        )

        # TODO: Send notifications if notify_attendees is True

        return updated

    def suggest_reschedule_times(
        self,
        event_id: str,
        calendar_ids: List[str],
        max_suggestions: int = 5,
    ) -> List[SchedulingSuggestion]:
        """
        Suggest alternative times for rescheduling an event.

        Args:
            event_id: Event ID to reschedule
            calendar_ids: Calendar IDs
            max_suggestions: Maximum number of suggestions

        Returns:
            List of scheduling suggestions
        """
        event = self.event_manager.get_event(event_id)
        if not event:
            return []

        # Create scheduling request from event
        duration_minutes = int((event.end_time - event.start_time).total_seconds() / 60)

        request = SchedulingRequest(
            title=event.title,
            duration_minutes=duration_minutes,
            attendees=[a.email for a in event.attendees],
            organizer=event.organizer or "",
            description=event.description,
            location=event.location,
            preferred_start_time=datetime.now(),
        )

        return self.find_optimal_time(
            request=request,
            calendar_ids=calendar_ids,
            max_suggestions=max_suggestions,
        )
