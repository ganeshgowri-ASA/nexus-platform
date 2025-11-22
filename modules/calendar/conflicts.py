"""
Conflict Detection Module

Detects and resolves scheduling conflicts between events.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from .event_manager import Event, EventManager


class ConflictSeverity(Enum):
    """Severity level of a conflict."""
    HARD = "hard"  # Complete overlap, cannot be resolved
    SOFT = "soft"  # Partial overlap, might be acceptable
    ADJACENT = "adjacent"  # Back-to-back, no travel time


@dataclass
class Conflict:
    """
    Represents a scheduling conflict between events.

    Attributes:
        event1: First conflicting event
        event2: Second conflicting event
        severity: Conflict severity
        overlap_minutes: Number of minutes of overlap
        overlap_start: Start of overlap period
        overlap_end: End of overlap period
        reason: Human-readable reason for conflict
    """
    event1: Event
    event2: Event
    severity: ConflictSeverity
    overlap_minutes: int
    overlap_start: datetime
    overlap_end: datetime
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert conflict to dictionary."""
        return {
            "event1_id": self.event1.id,
            "event1_title": self.event1.title,
            "event2_id": self.event2.id,
            "event2_title": self.event2.title,
            "severity": self.severity.value,
            "overlap_minutes": self.overlap_minutes,
            "overlap_start": self.overlap_start.isoformat(),
            "overlap_end": self.overlap_end.isoformat(),
            "reason": self.reason,
        }


class ConflictDetector:
    """
    Detects and analyzes scheduling conflicts.

    Features:
    - Detect overlapping events
    - Identify travel time conflicts
    - Suggest conflict resolutions
    - Check for back-to-back meetings
    """

    def __init__(
        self,
        event_manager: Optional[EventManager] = None,
        travel_time_minutes: int = 15,
    ):
        """
        Initialize the conflict detector.

        Args:
            event_manager: Event manager instance
            travel_time_minutes: Default travel time between events
        """
        self.event_manager = event_manager or EventManager()
        self.travel_time_minutes = travel_time_minutes

    def check_event_conflicts(
        self,
        event: Event,
        calendar_ids: Optional[List[str]] = None,
        include_tentative: bool = False,
    ) -> List[Conflict]:
        """
        Check if an event conflicts with existing events.

        Args:
            event: Event to check
            calendar_ids: Optional list of calendar IDs to check against
            include_tentative: Whether to include tentative events

        Returns:
            List of conflicts
        """
        conflicts = []

        # Get events in the same time range
        start_buffer = event.start_time - timedelta(minutes=self.travel_time_minutes)
        end_buffer = event.end_time + timedelta(minutes=self.travel_time_minutes)

        existing_events = self.event_manager.list_events(
            calendar_id=calendar_ids[0] if calendar_ids else None,
            start_date=start_buffer,
            end_date=end_buffer,
        )

        for existing in existing_events:
            # Skip self
            if existing.id == event.id:
                continue

            # Skip tentative if not included
            if not include_tentative and existing.status.value == "tentative":
                continue

            # Check for overlap
            conflict = self._detect_overlap(event, existing)
            if conflict:
                conflicts.append(conflict)

        return conflicts

    def _detect_overlap(
        self,
        event1: Event,
        event2: Event
    ) -> Optional[Conflict]:
        """
        Detect if two events overlap.

        Args:
            event1: First event
            event2: Second event

        Returns:
            Conflict if overlap detected, None otherwise
        """
        # Check for time overlap
        overlap_start = max(event1.start_time, event2.start_time)
        overlap_end = min(event1.end_time, event2.end_time)

        if overlap_start >= overlap_end:
            # No overlap, but check for adjacent meetings
            if self._are_adjacent(event1, event2):
                return Conflict(
                    event1=event1,
                    event2=event2,
                    severity=ConflictSeverity.ADJACENT,
                    overlap_minutes=0,
                    overlap_start=overlap_start,
                    overlap_end=overlap_end,
                    reason="Back-to-back meetings with no travel time",
                )
            return None

        # Calculate overlap duration
        overlap_duration = overlap_end - overlap_start
        overlap_minutes = int(overlap_duration.total_seconds() / 60)

        # Determine severity
        event1_duration = (event1.end_time - event1.start_time).total_seconds() / 60
        event2_duration = (event2.end_time - event2.start_time).total_seconds() / 60

        # Complete overlap if events fully overlap
        if (overlap_minutes >= event1_duration * 0.9 or
            overlap_minutes >= event2_duration * 0.9):
            severity = ConflictSeverity.HARD
            reason = "Complete time overlap"
        else:
            severity = ConflictSeverity.SOFT
            reason = f"Partial overlap ({overlap_minutes} minutes)"

        return Conflict(
            event1=event1,
            event2=event2,
            severity=severity,
            overlap_minutes=overlap_minutes,
            overlap_start=overlap_start,
            overlap_end=overlap_end,
            reason=reason,
        )

    def _are_adjacent(self, event1: Event, event2: Event) -> bool:
        """
        Check if two events are back-to-back.

        Args:
            event1: First event
            event2: Second event

        Returns:
            True if events are adjacent with insufficient travel time
        """
        # Check if event1 ends when event2 starts
        if event1.end_time == event2.start_time:
            # Check if different locations
            if event1.location and event2.location and event1.location != event2.location:
                return True

        # Check if event2 ends when event1 starts
        if event2.end_time == event1.start_time:
            if event1.location and event2.location and event1.location != event2.location:
                return True

        return False

    def detect_all_conflicts(
        self,
        start_date: datetime,
        end_date: datetime,
        calendar_ids: Optional[List[str]] = None,
    ) -> List[Conflict]:
        """
        Detect all conflicts within a date range.

        Args:
            start_date: Start of range
            end_date: End of range
            calendar_ids: Optional list of calendar IDs

        Returns:
            List of all conflicts
        """
        conflicts = []

        # Get all events in range
        events = self.event_manager.list_events(
            calendar_id=calendar_ids[0] if calendar_ids else None,
            start_date=start_date,
            end_date=end_date,
        )

        # Check each pair of events
        checked_pairs: Set[Tuple[str, str]] = set()

        for i, event1 in enumerate(events):
            for event2 in events[i + 1:]:
                # Create a unique pair ID
                pair_id = tuple(sorted([event1.id, event2.id]))

                if pair_id in checked_pairs:
                    continue

                checked_pairs.add(pair_id)

                # Check for conflict
                conflict = self._detect_overlap(event1, event2)
                if conflict:
                    conflicts.append(conflict)

        return conflicts

    def suggest_resolutions(self, conflict: Conflict) -> List[Dict[str, Any]]:
        """
        Suggest ways to resolve a conflict.

        Args:
            conflict: Conflict to resolve

        Returns:
            List of resolution suggestions
        """
        suggestions = []

        if conflict.severity == ConflictSeverity.HARD:
            # Suggest moving one event
            suggestions.append({
                "type": "move",
                "event_id": conflict.event1.id,
                "suggestion": f"Move '{conflict.event1.title}' to after '{conflict.event2.title}'",
                "new_start": conflict.event2.end_time + timedelta(minutes=self.travel_time_minutes),
            })

            suggestions.append({
                "type": "move",
                "event_id": conflict.event2.id,
                "suggestion": f"Move '{conflict.event2.title}' to after '{conflict.event1.title}'",
                "new_start": conflict.event1.end_time + timedelta(minutes=self.travel_time_minutes),
            })

            # Suggest canceling one event
            suggestions.append({
                "type": "cancel",
                "event_id": conflict.event1.id,
                "suggestion": f"Cancel '{conflict.event1.title}'",
            })

            suggestions.append({
                "type": "cancel",
                "event_id": conflict.event2.id,
                "suggestion": f"Cancel '{conflict.event2.title}'",
            })

        elif conflict.severity == ConflictSeverity.SOFT:
            # Suggest shortening events
            suggestions.append({
                "type": "shorten",
                "event_id": conflict.event1.id,
                "suggestion": f"Shorten '{conflict.event1.title}' to end before '{conflict.event2.title}' starts",
                "new_end": conflict.event2.start_time,
            })

            suggestions.append({
                "type": "shorten",
                "event_id": conflict.event2.id,
                "suggestion": f"Shorten '{conflict.event2.title}' to start after '{conflict.event1.title}' ends",
                "new_start": conflict.event1.end_time,
            })

        elif conflict.severity == ConflictSeverity.ADJACENT:
            # Suggest adding buffer time
            suggestions.append({
                "type": "buffer",
                "suggestion": f"Add {self.travel_time_minutes} minute buffer between events",
                "move_event_id": conflict.event2.id,
                "new_start": conflict.event1.end_time + timedelta(minutes=self.travel_time_minutes),
            })

        return suggestions

    def has_conflicts(
        self,
        event: Event,
        calendar_ids: Optional[List[str]] = None,
    ) -> bool:
        """
        Check if an event has any conflicts.

        Args:
            event: Event to check
            calendar_ids: Optional list of calendar IDs

        Returns:
            True if conflicts exist
        """
        conflicts = self.check_event_conflicts(event, calendar_ids)
        return len(conflicts) > 0

    def get_conflict_summary(
        self,
        start_date: datetime,
        end_date: datetime,
        calendar_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get a summary of conflicts in a date range.

        Args:
            start_date: Start of range
            end_date: End of range
            calendar_ids: Optional list of calendar IDs

        Returns:
            Conflict summary with counts and severity breakdown
        """
        conflicts = self.detect_all_conflicts(start_date, end_date, calendar_ids)

        hard_conflicts = [c for c in conflicts if c.severity == ConflictSeverity.HARD]
        soft_conflicts = [c for c in conflicts if c.severity == ConflictSeverity.SOFT]
        adjacent_conflicts = [c for c in conflicts if c.severity == ConflictSeverity.ADJACENT]

        return {
            "total_conflicts": len(conflicts),
            "hard_conflicts": len(hard_conflicts),
            "soft_conflicts": len(soft_conflicts),
            "adjacent_conflicts": len(adjacent_conflicts),
            "conflicts": [c.to_dict() for c in conflicts],
        }

    def find_free_slots(
        self,
        start_date: datetime,
        end_date: datetime,
        duration_minutes: int,
        calendar_ids: Optional[List[str]] = None,
        working_hours_start: int = 9,  # 9 AM
        working_hours_end: int = 17,  # 5 PM
    ) -> List[Dict[str, datetime]]:
        """
        Find free time slots within a date range.

        Args:
            start_date: Start of range
            end_date: End of range
            duration_minutes: Required duration in minutes
            calendar_ids: Optional list of calendar IDs
            working_hours_start: Start of working hours (24h format)
            working_hours_end: End of working hours (24h format)

        Returns:
            List of free slots with start and end times
        """
        free_slots = []

        # Get all events in range
        events = self.event_manager.list_events(
            calendar_id=calendar_ids[0] if calendar_ids else None,
            start_date=start_date,
            end_date=end_date,
        )

        # Sort events by start time
        events.sort(key=lambda e: e.start_time)

        # Check each day
        current_date = start_date.date()
        end_date_only = end_date.date()

        while current_date <= end_date_only:
            # Define working hours for this day
            day_start = datetime.combine(current_date, datetime.min.time()).replace(
                hour=working_hours_start
            )
            day_end = datetime.combine(current_date, datetime.min.time()).replace(
                hour=working_hours_end
            )

            # Get events for this day
            day_events = [
                e for e in events
                if e.start_time.date() == current_date
            ]

            if not day_events:
                # Entire day is free
                free_slots.append({
                    "start": day_start,
                    "end": day_end,
                    "duration_minutes": int((day_end - day_start).total_seconds() / 60),
                })
            else:
                # Check gaps between events
                current_time = day_start

                for event in day_events:
                    if event.start_time > current_time:
                        gap_duration = (event.start_time - current_time).total_seconds() / 60

                        if gap_duration >= duration_minutes:
                            free_slots.append({
                                "start": current_time,
                                "end": event.start_time,
                                "duration_minutes": int(gap_duration),
                            })

                    current_time = max(current_time, event.end_time)

                # Check time after last event
                if current_time < day_end:
                    gap_duration = (day_end - current_time).total_seconds() / 60

                    if gap_duration >= duration_minutes:
                        free_slots.append({
                            "start": current_time,
                            "end": day_end,
                            "duration_minutes": int(gap_duration),
                        })

            current_date += timedelta(days=1)

        return free_slots

    def validate_event_time(
        self,
        event: Event,
        calendar_ids: Optional[List[str]] = None,
        allow_conflicts: bool = False,
    ) -> Tuple[bool, List[str]]:
        """
        Validate if an event time is acceptable.

        Args:
            event: Event to validate
            calendar_ids: Optional list of calendar IDs
            allow_conflicts: Whether to allow conflicts

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        # Check basic time validation
        if event.end_time <= event.start_time:
            errors.append("End time must be after start time")

        # Check for conflicts
        if not allow_conflicts:
            conflicts = self.check_event_conflicts(event, calendar_ids)

            hard_conflicts = [c for c in conflicts if c.severity == ConflictSeverity.HARD]
            if hard_conflicts:
                for conflict in hard_conflicts:
                    errors.append(
                        f"Hard conflict with '{conflict.event2.title}' "
                        f"({conflict.overlap_minutes} minutes overlap)"
                    )

        return len(errors) == 0, errors
