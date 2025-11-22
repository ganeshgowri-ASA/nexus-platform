"""
AI Scheduler Module

AI-powered scheduling features including smart suggestions, meeting optimization,
auto-categorization, and conflict resolution.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import re

from .event_manager import Event, EventManager
from .scheduling import Scheduler, SchedulingRequest, SchedulingSuggestion
from .availability import AvailabilityManager
from .conflicts import ConflictDetector, Conflict


class EventCategory(Enum):
    """AI-detected event categories."""
    MEETING = "meeting"
    INTERVIEW = "interview"
    PERSONAL = "personal"
    WORK = "work"
    SOCIAL = "social"
    APPOINTMENT = "appointment"
    TRAVEL = "travel"
    BREAK = "break"
    FOCUS_TIME = "focus_time"
    OTHER = "other"


class MeetingType(Enum):
    """Types of meetings."""
    ONE_ON_ONE = "1:1"
    TEAM = "team"
    ALL_HANDS = "all_hands"
    CLIENT = "client"
    INTERVIEW = "interview"
    STANDUP = "standup"
    REVIEW = "review"


@dataclass
class SmartSuggestion:
    """
    AI-generated smart suggestion.

    Attributes:
        type: Type of suggestion
        title: Suggestion title
        description: Suggestion description
        confidence: Confidence score (0-100)
        action: Recommended action
        data: Additional data
    """
    type: str
    title: str
    description: str
    confidence: int
    action: str
    data: Dict[str, Any]


class AIScheduler:
    """
    AI-powered scheduling assistant.

    Features:
    - Smart scheduling suggestions
    - Meeting time optimization
    - Auto-categorize events
    - Travel time detection
    - Conflict resolution
    - Natural language parsing
    - Meeting pattern analysis
    """

    def __init__(
        self,
        event_manager: Optional[EventManager] = None,
        scheduler: Optional[Scheduler] = None,
        availability_manager: Optional[AvailabilityManager] = None,
        conflict_detector: Optional[ConflictDetector] = None,
    ):
        """
        Initialize the AI scheduler.

        Args:
            event_manager: Event manager instance
            scheduler: Scheduler instance
            availability_manager: Availability manager instance
            conflict_detector: Conflict detector instance
        """
        self.event_manager = event_manager or EventManager()
        self.scheduler = scheduler or Scheduler()
        self.availability_manager = availability_manager or AvailabilityManager()
        self.conflict_detector = conflict_detector or ConflictDetector()

    def parse_natural_language(
        self,
        text: str,
    ) -> Dict[str, Any]:
        """
        Parse natural language event description.

        Args:
            text: Natural language text (e.g., "Meeting with John tomorrow at 3pm for 1 hour")

        Returns:
            Parsed event data
        """
        parsed = {
            "title": text,
            "start_time": None,
            "duration_minutes": 60,  # Default 1 hour
            "attendees": [],
            "location": None,
        }

        # Extract time patterns
        time_patterns = [
            (r'at (\d{1,2})(?::(\d{2}))?\s*(am|pm)?', self._parse_time),
            (r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', self._parse_time),
        ]

        for pattern, parser in time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                parsed["start_time"] = parser(match)
                break

        # Extract duration
        duration_patterns = [
            (r'for (\d+)\s*(?:hour|hr)s?', lambda m: int(m.group(1)) * 60),
            (r'for (\d+)\s*(?:minute|min)s?', lambda m: int(m.group(1))),
            (r'(\d+)\s*(?:hour|hr)s?\s+meeting', lambda m: int(m.group(1)) * 60),
        ]

        for pattern, parser in duration_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                parsed["duration_minutes"] = parser(match)
                break

        # Extract date
        date_patterns = [
            (r'tomorrow', lambda: datetime.now() + timedelta(days=1)),
            (r'today', lambda: datetime.now()),
            (r'next week', lambda: datetime.now() + timedelta(weeks=1)),
        ]

        date = None
        for pattern, parser in date_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                date = parser()
                break

        # Combine date and time
        if date and parsed["start_time"]:
            parsed["start_time"] = parsed["start_time"].replace(
                year=date.year,
                month=date.month,
                day=date.day
            )

        # Extract attendees (emails or names)
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        parsed["attendees"] = emails

        # Extract title (first part before time/date info)
        title_match = re.match(r'^([^@]+?)(?:\s+(?:at|on|tomorrow|today|next))', text, re.IGNORECASE)
        if title_match:
            parsed["title"] = title_match.group(1).strip()

        return parsed

    def _parse_time(self, match) -> datetime:
        """Parse time from regex match."""
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        meridiem = match.group(3).lower() if match.group(3) else None

        # Convert to 24-hour format
        if meridiem == 'pm' and hour != 12:
            hour += 12
        elif meridiem == 'am' and hour == 12:
            hour = 0

        now = datetime.now()
        return now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    def categorize_event(
        self,
        event: Event,
    ) -> EventCategory:
        """
        Auto-categorize an event using AI.

        Args:
            event: Event to categorize

        Returns:
            Detected category
        """
        title_lower = event.title.lower()
        description_lower = (event.description or "").lower()

        # Meeting indicators
        meeting_keywords = ['meeting', 'call', 'sync', 'standup', 'huddle', 'discussion']
        if any(kw in title_lower for kw in meeting_keywords):
            return EventCategory.MEETING

        # Interview indicators
        interview_keywords = ['interview', 'screening', 'candidate']
        if any(kw in title_lower for kw in interview_keywords):
            return EventCategory.INTERVIEW

        # Personal indicators
        personal_keywords = ['doctor', 'dentist', 'gym', 'workout', 'lunch', 'dinner', 'birthday']
        if any(kw in title_lower for kw in personal_keywords):
            return EventCategory.PERSONAL

        # Appointment indicators
        appointment_keywords = ['appointment', 'visit', 'consultation']
        if any(kw in title_lower for kw in appointment_keywords):
            return EventCategory.APPOINTMENT

        # Travel indicators
        travel_keywords = ['flight', 'train', 'travel', 'commute']
        if any(kw in title_lower for kw in travel_keywords):
            return EventCategory.TRAVEL

        # Focus time indicators
        focus_keywords = ['focus', 'deep work', 'coding', 'writing']
        if any(kw in title_lower for kw in focus_keywords):
            return EventCategory.FOCUS_TIME

        # Social indicators
        social_keywords = ['party', 'celebration', 'happy hour', 'team building']
        if any(kw in title_lower for kw in social_keywords):
            return EventCategory.SOCIAL

        return EventCategory.WORK

    def detect_meeting_type(
        self,
        event: Event,
    ) -> MeetingType:
        """
        Detect the type of meeting.

        Args:
            event: Event to analyze

        Returns:
            Detected meeting type
        """
        title_lower = event.title.lower()
        attendee_count = len(event.attendees)

        # One-on-one
        if attendee_count == 2 or '1:1' in title_lower or 'one-on-one' in title_lower:
            return MeetingType.ONE_ON_ONE

        # Interview
        if 'interview' in title_lower or 'screening' in title_lower:
            return MeetingType.INTERVIEW

        # Standup
        if 'standup' in title_lower or 'daily sync' in title_lower:
            return MeetingType.STANDUP

        # Review
        if 'review' in title_lower or 'retrospective' in title_lower:
            return MeetingType.REVIEW

        # All hands
        if 'all hands' in title_lower or 'town hall' in title_lower:
            return MeetingType.ALL_HANDS

        # Client meeting
        if 'client' in title_lower or 'customer' in title_lower:
            return MeetingType.CLIENT

        # Team meeting (default for multiple attendees)
        if attendee_count > 2:
            return MeetingType.TEAM

        return MeetingType.TEAM

    def detect_travel_time(
        self,
        event: Event,
        previous_event: Optional[Event] = None,
    ) -> Optional[int]:
        """
        Detect required travel time between events.

        Args:
            event: Current event
            previous_event: Previous event

        Returns:
            Travel time in minutes, or None if no travel needed
        """
        if not previous_event:
            return None

        # If both are virtual, no travel time needed
        if event.video_link and previous_event.video_link:
            return 0

        # If same location, no travel time
        if event.location and previous_event.location:
            if event.location.lower() == previous_event.location.lower():
                return 0

        # Different locations - estimate travel time
        if event.location and previous_event.location:
            # Simple heuristic: 15-30 minutes for different locations
            # In a real system, this would use a maps API
            return 30

        # One virtual, one in-person
        if event.video_link or previous_event.video_link:
            return 10  # Buffer time

        # Default buffer for location changes
        return 15

    def suggest_optimal_meeting_time(
        self,
        title: str,
        duration_minutes: int,
        attendees: List[str],
        calendar_ids: List[str],
        preferences: Optional[Dict[str, Any]] = None,
    ) -> List[SchedulingSuggestion]:
        """
        Suggest optimal meeting times using AI.

        Args:
            title: Meeting title
            duration_minutes: Meeting duration
            attendees: Attendee emails
            calendar_ids: Calendar IDs to check
            preferences: Optional scheduling preferences

        Returns:
            List of smart suggestions
        """
        preferences = preferences or {}

        # Create scheduling request
        request = SchedulingRequest(
            title=title,
            duration_minutes=duration_minutes,
            attendees=attendees,
            organizer=attendees[0] if attendees else "",
            preferred_start_time=preferences.get("preferred_start"),
            preferred_end_time=preferences.get("preferred_end"),
        )

        # Get suggestions from scheduler
        suggestions = self.scheduler.find_optimal_time(
            request=request,
            calendar_ids=calendar_ids,
            max_suggestions=10,
        )

        # Apply AI scoring
        ai_suggestions = []
        for suggestion in suggestions:
            # AI-enhanced scoring
            ai_score = self._ai_score_suggestion(
                suggestion=suggestion,
                title=title,
                duration_minutes=duration_minutes,
                preferences=preferences,
            )

            suggestion.score = ai_score
            ai_suggestions.append(suggestion)

        # Re-sort by AI score
        ai_suggestions.sort(key=lambda s: s.score, reverse=True)

        return ai_suggestions[:5]

    def _ai_score_suggestion(
        self,
        suggestion: SchedulingSuggestion,
        title: str,
        duration_minutes: int,
        preferences: Dict[str, Any],
    ) -> int:
        """
        Apply AI scoring to a suggestion.

        Args:
            suggestion: Scheduling suggestion
            title: Meeting title
            duration_minutes: Duration
            preferences: User preferences

        Returns:
            AI-enhanced score
        """
        score = suggestion.score

        # Analyze meeting title for optimal timing
        title_lower = title.lower()

        # Focus work best in morning
        if any(kw in title_lower for kw in ['focus', 'deep work', 'coding']):
            if 8 <= suggestion.start_time.hour < 12:
                score += 15

        # Client meetings better in afternoon
        if any(kw in title_lower for kw in ['client', 'customer', 'sales']):
            if 13 <= suggestion.start_time.hour < 16:
                score += 10

        # Avoid scheduling long meetings late in day
        if duration_minutes > 60 and suggestion.start_time.hour >= 16:
            score -= 20

        # Prefer mid-week for important meetings
        weekday = suggestion.start_time.weekday()
        if any(kw in title_lower for kw in ['review', 'planning', 'strategy']):
            if weekday in [1, 2, 3]:  # Tue-Thu
                score += 10

        # Apply user preferences
        if preferences.get("avoid_mondays") and weekday == 0:
            score -= 15

        if preferences.get("avoid_fridays") and weekday == 4:
            score -= 15

        return max(0, min(100, score))

    def suggest_smart_actions(
        self,
        event: Event,
    ) -> List[SmartSuggestion]:
        """
        Generate smart suggestions for an event.

        Args:
            event: Event to analyze

        Returns:
            List of smart suggestions
        """
        suggestions = []

        # Check for conflicts
        conflicts = self.conflict_detector.check_event_conflicts(event)
        if conflicts:
            hard_conflicts = [c for c in conflicts if c.severity.value == "hard"]
            if hard_conflicts:
                suggestions.append(SmartSuggestion(
                    type="conflict",
                    title="Scheduling Conflict Detected",
                    description=f"This event conflicts with {len(hard_conflicts)} other event(s)",
                    confidence=95,
                    action="resolve_conflict",
                    data={"conflicts": [c.to_dict() for c in hard_conflicts]},
                ))

        # Suggest adding video link
        if not event.video_link and len(event.attendees) > 1:
            suggestions.append(SmartSuggestion(
                type="video_link",
                title="Add Video Meeting Link",
                description="Consider adding a video meeting link for remote attendees",
                confidence=70,
                action="add_video_link",
                data={},
            ))

        # Suggest travel time
        # TODO: Check previous event and suggest travel buffer

        # Suggest appropriate duration based on meeting type
        meeting_type = self.detect_meeting_type(event)
        duration = (event.end_time - event.start_time).total_seconds() / 60

        if meeting_type == MeetingType.STANDUP and duration > 15:
            suggestions.append(SmartSuggestion(
                type="duration",
                title="Standup Too Long",
                description="Standups are typically 15 minutes or less",
                confidence=80,
                action="shorten_meeting",
                data={"suggested_duration": 15},
            ))

        # Suggest adding agenda for long meetings
        if duration > 60 and not event.description:
            suggestions.append(SmartSuggestion(
                type="agenda",
                title="Add Meeting Agenda",
                description="Consider adding an agenda for this long meeting",
                confidence=75,
                action="add_agenda",
                data={},
            ))

        return suggestions

    def optimize_calendar(
        self,
        calendar_ids: List[str],
        start_date: datetime,
        days: int = 7,
    ) -> List[SmartSuggestion]:
        """
        Analyze calendar and suggest optimizations.

        Args:
            calendar_ids: Calendar IDs to analyze
            start_date: Start date
            days: Number of days to analyze

        Returns:
            List of optimization suggestions
        """
        suggestions = []
        end_date = start_date + timedelta(days=days)

        # Get all events
        all_events = []
        for cal_id in calendar_ids:
            events = self.event_manager.list_events(
                calendar_id=cal_id,
                start_date=start_date,
                end_date=end_date,
            )
            all_events.extend(events)

        # Check for back-to-back meetings
        all_events.sort(key=lambda e: e.start_time)
        back_to_back_count = 0

        for i in range(len(all_events) - 1):
            if all_events[i].end_time == all_events[i + 1].start_time:
                back_to_back_count += 1

        if back_to_back_count > 3:
            suggestions.append(SmartSuggestion(
                type="breaks",
                title="Too Many Back-to-Back Meetings",
                description=f"You have {back_to_back_count} back-to-back meetings. Consider adding breaks.",
                confidence=85,
                action="add_breaks",
                data={"count": back_to_back_count},
            ))

        # Check for meeting overload
        meeting_hours = sum(
            (e.end_time - e.start_time).total_seconds() / 3600
            for e in all_events
        )

        if meeting_hours > days * 6:  # More than 6 hours of meetings per day
            suggestions.append(SmartSuggestion(
                type="overload",
                title="High Meeting Load",
                description=f"You have {meeting_hours:.1f} hours of meetings in {days} days",
                confidence=90,
                action="reduce_meetings",
                data={"meeting_hours": meeting_hours, "days": days},
            ))

        # Suggest focus time blocks
        has_focus_time = any(
            self.categorize_event(e) == EventCategory.FOCUS_TIME
            for e in all_events
        )

        if not has_focus_time and len(all_events) > 5:
            suggestions.append(SmartSuggestion(
                type="focus_time",
                title="Add Focus Time",
                description="Schedule blocks for focused work between meetings",
                confidence=80,
                action="add_focus_time",
                data={},
            ))

        return suggestions
