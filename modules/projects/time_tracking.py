"""
NEXUS Time Tracking Module
Time logging, timesheets, and time reporting.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, date, time, timedelta
from enum import Enum
import uuid


class TimeEntryStatus(Enum):
    """Time entry status."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class TimeEntry:
    """
    Represents a time log entry.

    Attributes:
        id: Unique entry identifier
        task_id: Associated task ID
        user_id: User who logged time
        start_time: Start timestamp
        end_time: End timestamp
        duration_hours: Duration in hours
        description: Entry description
        is_billable: Whether time is billable
        status: Entry status
        approved_by: User who approved entry
        metadata: Additional metadata
        created_at: Creation timestamp
    """

    def __init__(
        self,
        task_id: str,
        user_id: str,
        duration_hours: float,
        description: str = "",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        is_billable: bool = True,
        status: TimeEntryStatus = TimeEntryStatus.DRAFT,
        metadata: Optional[Dict[str, Any]] = None,
        entry_id: Optional[str] = None
    ):
        """Initialize a time entry."""
        self.id: str = entry_id or str(uuid.uuid4())
        self.task_id: str = task_id
        self.user_id: str = user_id
        self.start_time: Optional[datetime] = start_time
        self.end_time: Optional[datetime] = end_time
        self.duration_hours: float = duration_hours
        self.description: str = description
        self.is_billable: bool = is_billable
        self.status: TimeEntryStatus = status
        self.approved_by: Optional[str] = None
        self.metadata: Dict[str, Any] = metadata or {}
        self.created_at: datetime = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary."""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "user_id": self.user_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_hours": self.duration_hours,
            "description": self.description,
            "is_billable": self.is_billable,
            "status": self.status.value,
            "approved_by": self.approved_by,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimeEntry':
        """Create entry from dictionary."""
        entry = cls(
            entry_id=data.get("id"),
            task_id=data["task_id"],
            user_id=data["user_id"],
            duration_hours=data["duration_hours"],
            description=data.get("description", ""),
            start_time=datetime.fromisoformat(data["start_time"]) if data.get("start_time") else None,
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            is_billable=data.get("is_billable", True),
            status=TimeEntryStatus(data.get("status", "draft")),
            metadata=data.get("metadata", {})
        )

        entry.approved_by = data.get("approved_by")
        return entry


class Timer:
    """
    Active timer for tracking time.

    Attributes:
        id: Timer identifier
        task_id: Associated task ID
        user_id: User ID
        start_time: Timer start time
        description: Timer description
    """

    def __init__(
        self,
        task_id: str,
        user_id: str,
        description: str = "",
        timer_id: Optional[str] = None
    ):
        """Initialize a timer."""
        self.id: str = timer_id or str(uuid.uuid4())
        self.task_id: str = task_id
        self.user_id: str = user_id
        self.start_time: datetime = datetime.now()
        self.description: str = description

    def get_elapsed_hours(self) -> float:
        """Get elapsed time in hours."""
        elapsed = datetime.now() - self.start_time
        return elapsed.total_seconds() / 3600.0

    def stop(self) -> TimeEntry:
        """
        Stop the timer and create a time entry.

        Returns:
            Created time entry
        """
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds() / 3600.0

        return TimeEntry(
            task_id=self.task_id,
            user_id=self.user_id,
            start_time=self.start_time,
            end_time=end_time,
            duration_hours=duration,
            description=self.description
        )


class TimeTrackingManager:
    """
    Time tracking and timesheet management.
    Handles time entries, timers, and time reporting.
    """

    def __init__(self, task_manager):
        """
        Initialize the time tracking manager.

        Args:
            task_manager: Task manager instance
        """
        self.task_manager = task_manager
        self.time_entries: Dict[str, TimeEntry] = {}
        self.active_timers: Dict[str, Timer] = {}

    def log_time(
        self,
        task_id: str,
        user_id: str,
        duration_hours: float,
        description: str = "",
        start_time: Optional[datetime] = None,
        is_billable: bool = True,
        **kwargs
    ) -> Optional[TimeEntry]:
        """
        Log time for a task.

        Args:
            task_id: Task identifier
            user_id: User identifier
            duration_hours: Duration in hours
            description: Entry description
            start_time: Start time (None = now)
            is_billable: Whether time is billable
            **kwargs: Additional entry attributes

        Returns:
            Created time entry or None if invalid
        """
        task = self.task_manager.get_task(task_id)
        if not task:
            return None

        entry = TimeEntry(
            task_id=task_id,
            user_id=user_id,
            duration_hours=duration_hours,
            description=description,
            start_time=start_time or datetime.now(),
            is_billable=is_billable,
            **kwargs
        )

        self.time_entries[entry.id] = entry

        # Update task actual hours
        task.actual_hours += duration_hours
        task.updated_at = datetime.now()

        return entry

    def get_time_entry(self, entry_id: str) -> Optional[TimeEntry]:
        """Get a time entry by ID."""
        return self.time_entries.get(entry_id)

    def update_time_entry(self, entry_id: str, **kwargs) -> Optional[TimeEntry]:
        """Update a time entry."""
        entry = self.get_time_entry(entry_id)
        if not entry:
            return None

        # Track old duration for task update
        old_duration = entry.duration_hours

        for key, value in kwargs.items():
            if hasattr(entry, key):
                setattr(entry, key, value)

        # Update task actual hours if duration changed
        if "duration_hours" in kwargs:
            task = self.task_manager.get_task(entry.task_id)
            if task:
                task.actual_hours = task.actual_hours - old_duration + entry.duration_hours

        return entry

    def delete_time_entry(self, entry_id: str) -> bool:
        """Delete a time entry."""
        entry = self.get_time_entry(entry_id)
        if not entry:
            return False

        # Update task actual hours
        task = self.task_manager.get_task(entry.task_id)
        if task:
            task.actual_hours = max(0, task.actual_hours - entry.duration_hours)

        del self.time_entries[entry_id]
        return True

    def start_timer(
        self,
        task_id: str,
        user_id: str,
        description: str = ""
    ) -> Optional[Timer]:
        """
        Start a timer for a task.

        Args:
            task_id: Task identifier
            user_id: User identifier
            description: Timer description

        Returns:
            Started timer or None if invalid
        """
        task = self.task_manager.get_task(task_id)
        if not task:
            return None

        # Stop any existing timer for this user
        existing_key = f"{user_id}"
        if existing_key in self.active_timers:
            self.stop_timer(user_id)

        timer = Timer(task_id=task_id, user_id=user_id, description=description)
        self.active_timers[user_id] = timer

        return timer

    def stop_timer(self, user_id: str) -> Optional[TimeEntry]:
        """
        Stop the active timer for a user.

        Args:
            user_id: User identifier

        Returns:
            Created time entry or None if no active timer
        """
        if user_id not in self.active_timers:
            return None

        timer = self.active_timers[user_id]
        entry = timer.stop()

        # Save the time entry
        self.time_entries[entry.id] = entry

        # Update task actual hours
        task = self.task_manager.get_task(entry.task_id)
        if task:
            task.actual_hours += entry.duration_hours

        # Remove timer
        del self.active_timers[user_id]

        return entry

    def get_active_timer(self, user_id: str) -> Optional[Timer]:
        """Get the active timer for a user."""
        return self.active_timers.get(user_id)

    def get_time_entries_by_task(self, task_id: str) -> List[TimeEntry]:
        """Get all time entries for a task."""
        return [e for e in self.time_entries.values() if e.task_id == task_id]

    def get_time_entries_by_user(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[TimeEntry]:
        """
        Get time entries for a user.

        Args:
            user_id: User identifier
            start_date: Filter start date
            end_date: Filter end date

        Returns:
            List of time entries
        """
        entries = [e for e in self.time_entries.values() if e.user_id == user_id]

        if start_date or end_date:
            filtered = []
            for entry in entries:
                entry_date = entry.start_time.date() if entry.start_time else entry.created_at.date()

                if start_date and entry_date < start_date:
                    continue
                if end_date and entry_date > end_date:
                    continue

                filtered.append(entry)

            entries = filtered

        return entries

    def get_time_entries_by_project(
        self,
        project_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[TimeEntry]:
        """Get all time entries for a project."""
        tasks = self.task_manager.get_tasks_by_project(project_id)
        task_ids = {t.id for t in tasks}

        entries = [e for e in self.time_entries.values() if e.task_id in task_ids]

        if start_date or end_date:
            filtered = []
            for entry in entries:
                entry_date = entry.start_time.date() if entry.start_time else entry.created_at.date()

                if start_date and entry_date < start_date:
                    continue
                if end_date and entry_date > end_date:
                    continue

                filtered.append(entry)

            entries = filtered

        return entries

    def approve_time_entry(self, entry_id: str, approver_id: str) -> bool:
        """Approve a time entry."""
        entry = self.get_time_entry(entry_id)
        if not entry:
            return False

        entry.status = TimeEntryStatus.APPROVED
        entry.approved_by = approver_id
        return True

    def reject_time_entry(self, entry_id: str) -> bool:
        """Reject a time entry."""
        entry = self.get_time_entry(entry_id)
        if not entry:
            return False

        entry.status = TimeEntryStatus.REJECTED
        return True

    def generate_timesheet(
        self,
        user_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Generate a timesheet for a user.

        Args:
            user_id: User identifier
            start_date: Timesheet start date
            end_date: Timesheet end date

        Returns:
            Timesheet dictionary
        """
        entries = self.get_time_entries_by_user(user_id, start_date, end_date)

        total_hours = sum(e.duration_hours for e in entries)
        billable_hours = sum(e.duration_hours for e in entries if e.is_billable)
        non_billable_hours = total_hours - billable_hours

        # Group by task
        by_task: Dict[str, List[TimeEntry]] = {}
        for entry in entries:
            if entry.task_id not in by_task:
                by_task[entry.task_id] = []
            by_task[entry.task_id].append(entry)

        task_summaries = []
        for task_id, task_entries in by_task.items():
            task = self.task_manager.get_task(task_id)
            task_summaries.append({
                "task_id": task_id,
                "task_name": task.name if task else "Unknown",
                "total_hours": sum(e.duration_hours for e in task_entries),
                "entry_count": len(task_entries)
            })

        return {
            "user_id": user_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_hours": total_hours,
            "billable_hours": billable_hours,
            "non_billable_hours": non_billable_hours,
            "entry_count": len(entries),
            "by_task": task_summaries,
            "entries": [e.to_dict() for e in entries]
        }

    def get_project_time_summary(
        self,
        project_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get time summary for a project.

        Args:
            project_id: Project identifier
            start_date: Filter start date
            end_date: Filter end date

        Returns:
            Time summary dictionary
        """
        entries = self.get_time_entries_by_project(project_id, start_date, end_date)

        total_hours = sum(e.duration_hours for e in entries)
        billable_hours = sum(e.duration_hours for e in entries if e.is_billable)

        # Group by user
        by_user: Dict[str, float] = {}
        for entry in entries:
            if entry.user_id not in by_user:
                by_user[entry.user_id] = 0.0
            by_user[entry.user_id] += entry.duration_hours

        return {
            "project_id": project_id,
            "total_hours": total_hours,
            "billable_hours": billable_hours,
            "non_billable_hours": total_hours - billable_hours,
            "entry_count": len(entries),
            "by_user": by_user
        }
