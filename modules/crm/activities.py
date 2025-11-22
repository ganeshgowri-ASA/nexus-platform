"""
CRM Activities Module - Track calls, meetings, emails, and notes with timeline view.
"""

from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum


class ActivityType(Enum):
    """Activity types."""
    CALL = "call"
    MEETING = "meeting"
    EMAIL = "email"
    NOTE = "note"
    TASK = "task"
    SMS = "sms"
    LINKEDIN = "linkedin"
    OTHER = "other"


class ActivityStatus(Enum):
    """Activity status."""
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class CallOutcome(Enum):
    """Call outcomes."""
    CONNECTED = "connected"
    LEFT_VOICEMAIL = "left_voicemail"
    NO_ANSWER = "no_answer"
    BUSY = "busy"
    WRONG_NUMBER = "wrong_number"


@dataclass
class Activity:
    """Activity entity for tracking interactions."""
    id: str
    activity_type: ActivityType
    subject: str

    # Related entities
    contact_id: Optional[str] = None
    contact_name: Optional[str] = None
    company_id: Optional[str] = None
    company_name: Optional[str] = None
    deal_id: Optional[str] = None
    deal_name: Optional[str] = None

    # Activity details
    description: Optional[str] = None
    notes: Optional[str] = None
    status: ActivityStatus = ActivityStatus.COMPLETED

    # Scheduling
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None

    # For calls
    call_outcome: Optional[CallOutcome] = None
    call_recording_url: Optional[str] = None

    # For meetings
    location: Optional[str] = None
    meeting_url: Optional[str] = None
    attendees: List[str] = field(default_factory=list)

    # For emails
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    email_to: List[str] = field(default_factory=list)
    email_cc: List[str] = field(default_factory=list)
    email_opened: bool = False
    email_clicked: bool = False

    # Ownership
    owner_id: Optional[str] = None
    created_by: Optional[str] = None

    # Metadata
    tags: Set[str] = field(default_factory=set)
    custom_fields: Dict[str, Any] = field(default_factory=dict)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'activity_type': self.activity_type.value,
            'subject': self.subject,
            'contact_id': self.contact_id,
            'contact_name': self.contact_name,
            'company_id': self.company_id,
            'company_name': self.company_name,
            'deal_id': self.deal_id,
            'deal_name': self.deal_name,
            'description': self.description,
            'notes': self.notes,
            'status': self.status.value,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_minutes': self.duration_minutes,
            'call_outcome': self.call_outcome.value if self.call_outcome else None,
            'call_recording_url': self.call_recording_url,
            'location': self.location,
            'meeting_url': self.meeting_url,
            'attendees': self.attendees,
            'email_subject': self.email_subject,
            'email_body': self.email_body,
            'email_to': self.email_to,
            'email_cc': self.email_cc,
            'email_opened': self.email_opened,
            'email_clicked': self.email_clicked,
            'owner_id': self.owner_id,
            'created_by': self.created_by,
            'tags': list(self.tags),
            'custom_fields': self.custom_fields,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class ActivityManager:
    """Manage activities and interactions."""

    def __init__(self):
        """Initialize activity manager."""
        self.activities: Dict[str, Activity] = {}
        self._contact_index: Dict[str, List[str]] = {}  # contact_id -> [activity_ids]
        self._company_index: Dict[str, List[str]] = {}  # company_id -> [activity_ids]
        self._deal_index: Dict[str, List[str]] = {}  # deal_id -> [activity_ids]
        self._type_index: Dict[ActivityType, Set[str]] = {}  # type -> {activity_ids}
        self._owner_index: Dict[str, List[str]] = {}  # owner_id -> [activity_ids]
        self._tag_index: Dict[str, Set[str]] = {}  # tag -> {activity_ids}

    def create_activity(self, activity: Activity) -> Activity:
        """Create a new activity."""
        self.activities[activity.id] = activity

        # Update indexes
        if activity.contact_id:
            if activity.contact_id not in self._contact_index:
                self._contact_index[activity.contact_id] = []
            self._contact_index[activity.contact_id].append(activity.id)

        if activity.company_id:
            if activity.company_id not in self._company_index:
                self._company_index[activity.company_id] = []
            self._company_index[activity.company_id].append(activity.id)

        if activity.deal_id:
            if activity.deal_id not in self._deal_index:
                self._deal_index[activity.deal_id] = []
            self._deal_index[activity.deal_id].append(activity.id)

        if activity.activity_type not in self._type_index:
            self._type_index[activity.activity_type] = set()
        self._type_index[activity.activity_type].add(activity.id)

        if activity.owner_id:
            if activity.owner_id not in self._owner_index:
                self._owner_index[activity.owner_id] = []
            self._owner_index[activity.owner_id].append(activity.id)

        for tag in activity.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = set()
            self._tag_index[tag].add(activity.id)

        return activity

    def get_activity(self, activity_id: str) -> Optional[Activity]:
        """Get an activity by ID."""
        return self.activities.get(activity_id)

    def update_activity(self, activity_id: str, updates: Dict[str, Any]) -> Optional[Activity]:
        """Update an activity."""
        activity = self.activities.get(activity_id)
        if not activity:
            return None

        # Handle type change
        if 'activity_type' in updates:
            old_type = activity.activity_type
            new_type = updates['activity_type'] if isinstance(updates['activity_type'], ActivityType) else ActivityType(updates['activity_type'])
            if new_type != old_type:
                self._type_index[old_type].discard(activity_id)
                if new_type not in self._type_index:
                    self._type_index[new_type] = set()
                self._type_index[new_type].add(activity_id)

        # Update fields
        for key, value in updates.items():
            if hasattr(activity, key):
                # Handle enum conversions
                if key == 'activity_type' and isinstance(value, str):
                    value = ActivityType(value)
                elif key == 'status' and isinstance(value, str):
                    value = ActivityStatus(value)
                elif key == 'call_outcome' and isinstance(value, str):
                    value = CallOutcome(value)
                setattr(activity, key, value)

        activity.updated_at = datetime.now()
        return activity

    def delete_activity(self, activity_id: str) -> bool:
        """Delete an activity."""
        activity = self.activities.get(activity_id)
        if not activity:
            return False

        # Remove from indexes
        if activity.contact_id and activity.contact_id in self._contact_index:
            self._contact_index[activity.contact_id].remove(activity_id)

        if activity.company_id and activity.company_id in self._company_index:
            self._company_index[activity.company_id].remove(activity_id)

        if activity.deal_id and activity.deal_id in self._deal_index:
            self._deal_index[activity.deal_id].remove(activity_id)

        if activity.activity_type in self._type_index:
            self._type_index[activity.activity_type].discard(activity_id)

        if activity.owner_id and activity.owner_id in self._owner_index:
            self._owner_index[activity.owner_id].remove(activity_id)

        for tag in activity.tags:
            if tag in self._tag_index:
                self._tag_index[tag].discard(activity_id)

        del self.activities[activity_id]
        return True

    def list_activities(
        self,
        activity_type: Optional[ActivityType] = None,
        contact_id: Optional[str] = None,
        company_id: Optional[str] = None,
        deal_id: Optional[str] = None,
        owner_id: Optional[str] = None,
        status: Optional[ActivityStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Activity]:
        """List activities with filtering."""
        results = list(self.activities.values())

        # Apply filters
        if activity_type:
            results = [a for a in results if a.activity_type == activity_type]

        if contact_id:
            results = [a for a in results if a.contact_id == contact_id]

        if company_id:
            results = [a for a in results if a.company_id == company_id]

        if deal_id:
            results = [a for a in results if a.deal_id == deal_id]

        if owner_id:
            results = [a for a in results if a.owner_id == owner_id]

        if status:
            results = [a for a in results if a.status == status]

        if start_date:
            results = [a for a in results if a.created_at >= start_date]

        if end_date:
            results = [a for a in results if a.created_at <= end_date]

        # Sort by created_at descending
        results.sort(key=lambda a: a.created_at, reverse=True)

        # Apply pagination
        if limit:
            results = results[offset:offset + limit]
        else:
            results = results[offset:]

        return results

    def get_timeline(
        self,
        contact_id: Optional[str] = None,
        company_id: Optional[str] = None,
        deal_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get activity timeline for a contact, company, or deal."""
        activities = []

        if contact_id:
            activity_ids = self._contact_index.get(contact_id, [])
            activities = [self.activities[aid] for aid in activity_ids if aid in self.activities]

        elif company_id:
            activity_ids = self._company_index.get(company_id, [])
            activities = [self.activities[aid] for aid in activity_ids if aid in self.activities]

        elif deal_id:
            activity_ids = self._deal_index.get(deal_id, [])
            activities = [self.activities[aid] for aid in activity_ids if aid in self.activities]

        # Sort by created_at descending
        activities.sort(key=lambda a: a.created_at, reverse=True)

        # Apply limit
        activities = activities[:limit]

        return [a.to_dict() for a in activities]

    def log_call(
        self,
        subject: str,
        contact_id: Optional[str] = None,
        company_id: Optional[str] = None,
        deal_id: Optional[str] = None,
        outcome: Optional[CallOutcome] = None,
        duration_minutes: Optional[int] = None,
        notes: Optional[str] = None,
        owner_id: Optional[str] = None
    ) -> Activity:
        """Quick log a call activity."""
        activity = Activity(
            id=self._generate_id(),
            activity_type=ActivityType.CALL,
            subject=subject,
            contact_id=contact_id,
            company_id=company_id,
            deal_id=deal_id,
            call_outcome=outcome,
            duration_minutes=duration_minutes,
            notes=notes,
            owner_id=owner_id,
            status=ActivityStatus.COMPLETED,
            completed_at=datetime.now(),
        )
        return self.create_activity(activity)

    def schedule_meeting(
        self,
        subject: str,
        scheduled_at: datetime,
        duration_minutes: int,
        contact_id: Optional[str] = None,
        company_id: Optional[str] = None,
        deal_id: Optional[str] = None,
        location: Optional[str] = None,
        meeting_url: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        description: Optional[str] = None,
        owner_id: Optional[str] = None
    ) -> Activity:
        """Schedule a meeting."""
        activity = Activity(
            id=self._generate_id(),
            activity_type=ActivityType.MEETING,
            subject=subject,
            contact_id=contact_id,
            company_id=company_id,
            deal_id=deal_id,
            scheduled_at=scheduled_at,
            duration_minutes=duration_minutes,
            location=location,
            meeting_url=meeting_url,
            attendees=attendees or [],
            description=description,
            owner_id=owner_id,
            status=ActivityStatus.SCHEDULED,
        )
        return self.create_activity(activity)

    def log_email(
        self,
        subject: str,
        email_to: List[str],
        contact_id: Optional[str] = None,
        company_id: Optional[str] = None,
        deal_id: Optional[str] = None,
        email_body: Optional[str] = None,
        email_cc: Optional[List[str]] = None,
        owner_id: Optional[str] = None
    ) -> Activity:
        """Log an email activity."""
        activity = Activity(
            id=self._generate_id(),
            activity_type=ActivityType.EMAIL,
            subject=subject,
            contact_id=contact_id,
            company_id=company_id,
            deal_id=deal_id,
            email_subject=subject,
            email_body=email_body,
            email_to=email_to,
            email_cc=email_cc or [],
            owner_id=owner_id,
            status=ActivityStatus.COMPLETED,
            completed_at=datetime.now(),
        )
        return self.create_activity(activity)

    def add_note(
        self,
        subject: str,
        notes: str,
        contact_id: Optional[str] = None,
        company_id: Optional[str] = None,
        deal_id: Optional[str] = None,
        owner_id: Optional[str] = None
    ) -> Activity:
        """Add a note."""
        activity = Activity(
            id=self._generate_id(),
            activity_type=ActivityType.NOTE,
            subject=subject,
            contact_id=contact_id,
            company_id=company_id,
            deal_id=deal_id,
            notes=notes,
            owner_id=owner_id,
            status=ActivityStatus.COMPLETED,
            completed_at=datetime.now(),
        )
        return self.create_activity(activity)

    def complete_activity(self, activity_id: str, notes: Optional[str] = None) -> Optional[Activity]:
        """Mark an activity as completed."""
        updates = {
            'status': ActivityStatus.COMPLETED,
            'completed_at': datetime.now(),
        }
        if notes:
            updates['notes'] = notes
        return self.update_activity(activity_id, updates)

    def cancel_activity(self, activity_id: str, reason: Optional[str] = None) -> Optional[Activity]:
        """Cancel an activity."""
        updates = {
            'status': ActivityStatus.CANCELLED,
        }
        if reason:
            updates['notes'] = f"Cancelled: {reason}"
        return self.update_activity(activity_id, updates)

    def get_upcoming_activities(
        self,
        owner_id: Optional[str] = None,
        days_ahead: int = 7,
        limit: int = 50
    ) -> List[Activity]:
        """Get upcoming scheduled activities."""
        now = datetime.now()
        end_date = now + timedelta(days=days_ahead)

        activities = [
            a for a in self.activities.values()
            if a.status == ActivityStatus.SCHEDULED
            and a.scheduled_at
            and now <= a.scheduled_at <= end_date
        ]

        if owner_id:
            activities = [a for a in activities if a.owner_id == owner_id]

        # Sort by scheduled_at
        activities.sort(key=lambda a: a.scheduled_at or datetime.max)

        return activities[:limit]

    def get_overdue_activities(self, owner_id: Optional[str] = None) -> List[Activity]:
        """Get overdue scheduled activities."""
        now = datetime.now()

        activities = [
            a for a in self.activities.values()
            if a.status == ActivityStatus.SCHEDULED
            and a.scheduled_at
            and a.scheduled_at < now
        ]

        if owner_id:
            activities = [a for a in activities if a.owner_id == owner_id]

        # Sort by scheduled_at
        activities.sort(key=lambda a: a.scheduled_at or datetime.min)

        return activities

    def get_activity_summary(
        self,
        owner_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get activity summary statistics."""
        activities = list(self.activities.values())

        if owner_id:
            activities = [a for a in activities if a.owner_id == owner_id]

        if start_date:
            activities = [a for a in activities if a.created_at >= start_date]

        if end_date:
            activities = [a for a in activities if a.created_at <= end_date]

        # Count by type
        by_type = {}
        for activity_type in ActivityType:
            count = len([a for a in activities if a.activity_type == activity_type])
            by_type[activity_type.value] = count

        # Count by status
        by_status = {}
        for status in ActivityStatus:
            count = len([a for a in activities if a.status == status])
            by_status[status.value] = count

        # Call outcomes
        call_outcomes = {}
        calls = [a for a in activities if a.activity_type == ActivityType.CALL and a.call_outcome]
        for call in calls:
            outcome = call.call_outcome.value
            call_outcomes[outcome] = call_outcomes.get(outcome, 0) + 1

        # Email engagement
        emails = [a for a in activities if a.activity_type == ActivityType.EMAIL]
        email_stats = {
            'total_sent': len(emails),
            'opened': len([e for e in emails if e.email_opened]),
            'clicked': len([e for e in emails if e.email_clicked]),
        }

        return {
            'total_activities': len(activities),
            'by_type': by_type,
            'by_status': by_status,
            'call_outcomes': call_outcomes,
            'email_stats': email_stats,
        }

    def search_activities(self, query: str) -> List[Activity]:
        """Search activities by subject, notes, or description."""
        query_lower = query.lower()
        results = []

        for activity in self.activities.values():
            if (query_lower in activity.subject.lower() or
                (activity.notes and query_lower in activity.notes.lower()) or
                (activity.description and query_lower in activity.description.lower())):
                results.append(activity)

        return results

    def _generate_id(self) -> str:
        """Generate a unique activity ID."""
        import uuid
        return f"activity_{uuid.uuid4().hex[:12]}"

    def get_statistics(self) -> Dict[str, Any]:
        """Get activity statistics."""
        total = len(self.activities)

        by_type = {}
        for activity_type in ActivityType:
            count = len(self._type_index.get(activity_type, set()))
            by_type[activity_type.value] = count

        by_status = {}
        for status in ActivityStatus:
            count = len([a for a in self.activities.values() if a.status == status])
            by_status[status.value] = count

        return {
            'total_activities': total,
            'by_type': by_type,
            'by_status': by_status,
        }
