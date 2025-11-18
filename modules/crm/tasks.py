"""
CRM Tasks Module - Task management with follow-ups, reminders, and assignments.
"""

from typing import Dict, List, Optional, Any, Set
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
from enum import Enum


class TaskType(Enum):
    """Task types."""
    FOLLOW_UP = "follow_up"
    TODO = "todo"
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    SEND_QUOTE = "send_quote"
    SEND_CONTRACT = "send_contract"
    DEMO = "demo"
    OTHER = "other"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(Enum):
    """Task status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ReminderType(Enum):
    """Reminder types."""
    NONE = "none"
    AT_TIME = "at_time"
    BEFORE_15MIN = "15_minutes_before"
    BEFORE_30MIN = "30_minutes_before"
    BEFORE_1HOUR = "1_hour_before"
    BEFORE_1DAY = "1_day_before"


@dataclass
class Task:
    """Task entity for CRM activities."""
    id: str
    title: str
    task_type: TaskType = TaskType.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.NOT_STARTED

    # Task details
    description: Optional[str] = None
    notes: Optional[str] = None

    # Related entities
    contact_id: Optional[str] = None
    contact_name: Optional[str] = None
    company_id: Optional[str] = None
    company_name: Optional[str] = None
    deal_id: Optional[str] = None
    deal_name: Optional[str] = None

    # Scheduling
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None

    # Reminders
    reminder_type: ReminderType = ReminderType.NONE
    reminder_sent: bool = False
    reminder_sent_at: Optional[datetime] = None

    # Assignment
    assigned_to: Optional[str] = None
    assigned_by: Optional[str] = None
    owner_id: Optional[str] = None

    # Progress
    progress: int = 0  # 0-100 percentage

    # Metadata
    tags: Set[str] = field(default_factory=set)
    custom_fields: Dict[str, Any] = field(default_factory=dict)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if self.due_date and self.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
            return datetime.now() > self.due_date
        return False

    @property
    def days_until_due(self) -> Optional[int]:
        """Calculate days until due date."""
        if self.due_date:
            delta = self.due_date - datetime.now()
            return delta.days
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'task_type': self.task_type.value,
            'priority': self.priority.value,
            'status': self.status.value,
            'description': self.description,
            'notes': self.notes,
            'contact_id': self.contact_id,
            'contact_name': self.contact_name,
            'company_id': self.company_id,
            'company_name': self.company_name,
            'deal_id': self.deal_id,
            'deal_name': self.deal_name,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'completed_date': self.completed_date.isoformat() if self.completed_date else None,
            'reminder_type': self.reminder_type.value,
            'reminder_sent': self.reminder_sent,
            'reminder_sent_at': self.reminder_sent_at.isoformat() if self.reminder_sent_at else None,
            'assigned_to': self.assigned_to,
            'assigned_by': self.assigned_by,
            'owner_id': self.owner_id,
            'progress': self.progress,
            'tags': list(self.tags),
            'custom_fields': self.custom_fields,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_overdue': self.is_overdue,
            'days_until_due': self.days_until_due,
        }


class TaskManager:
    """Manage tasks, follow-ups, and reminders."""

    def __init__(self):
        """Initialize task manager."""
        self.tasks: Dict[str, Task] = {}
        self._contact_index: Dict[str, List[str]] = {}  # contact_id -> [task_ids]
        self._company_index: Dict[str, List[str]] = {}  # company_id -> [task_ids]
        self._deal_index: Dict[str, List[str]] = {}  # deal_id -> [task_ids]
        self._assigned_index: Dict[str, List[str]] = {}  # user_id -> [task_ids]
        self._status_index: Dict[TaskStatus, Set[str]] = {}  # status -> {task_ids}
        self._priority_index: Dict[TaskPriority, Set[str]] = {}  # priority -> {task_ids}
        self._tag_index: Dict[str, Set[str]] = {}  # tag -> {task_ids}

    def create_task(self, task: Task) -> Task:
        """Create a new task."""
        self.tasks[task.id] = task

        # Update indexes
        if task.contact_id:
            if task.contact_id not in self._contact_index:
                self._contact_index[task.contact_id] = []
            self._contact_index[task.contact_id].append(task.id)

        if task.company_id:
            if task.company_id not in self._company_index:
                self._company_index[task.company_id] = []
            self._company_index[task.company_id].append(task.id)

        if task.deal_id:
            if task.deal_id not in self._deal_index:
                self._deal_index[task.deal_id] = []
            self._deal_index[task.deal_id].append(task.id)

        if task.assigned_to:
            if task.assigned_to not in self._assigned_index:
                self._assigned_index[task.assigned_to] = []
            self._assigned_index[task.assigned_to].append(task.id)

        if task.status not in self._status_index:
            self._status_index[task.status] = set()
        self._status_index[task.status].add(task.id)

        if task.priority not in self._priority_index:
            self._priority_index[task.priority] = set()
        self._priority_index[task.priority].add(task.id)

        for tag in task.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = set()
            self._tag_index[tag].add(task.id)

        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    def update_task(self, task_id: str, updates: Dict[str, Any]) -> Optional[Task]:
        """Update a task."""
        task = self.tasks.get(task_id)
        if not task:
            return None

        # Handle status change
        if 'status' in updates:
            old_status = task.status
            new_status = updates['status'] if isinstance(updates['status'], TaskStatus) else TaskStatus(updates['status'])
            if new_status != old_status:
                # Update status index
                self._status_index[old_status].discard(task_id)
                if new_status not in self._status_index:
                    self._status_index[new_status] = set()
                self._status_index[new_status].add(task_id)

                # Mark completed
                if new_status == TaskStatus.COMPLETED:
                    task.completed_date = datetime.now()
                    task.progress = 100

        # Handle priority change
        if 'priority' in updates:
            old_priority = task.priority
            new_priority = updates['priority'] if isinstance(updates['priority'], TaskPriority) else TaskPriority(updates['priority'])
            if new_priority != old_priority:
                self._priority_index[old_priority].discard(task_id)
                if new_priority not in self._priority_index:
                    self._priority_index[new_priority] = set()
                self._priority_index[new_priority].add(task_id)

        # Update fields
        for key, value in updates.items():
            if hasattr(task, key):
                # Handle enum conversions
                if key == 'task_type' and isinstance(value, str):
                    value = TaskType(value)
                elif key == 'priority' and isinstance(value, str):
                    value = TaskPriority(value)
                elif key == 'status' and isinstance(value, str):
                    value = TaskStatus(value)
                elif key == 'reminder_type' and isinstance(value, str):
                    value = ReminderType(value)
                setattr(task, key, value)

        task.updated_at = datetime.now()
        return task

    def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        task = self.tasks.get(task_id)
        if not task:
            return False

        # Remove from indexes
        if task.contact_id and task.contact_id in self._contact_index:
            self._contact_index[task.contact_id].remove(task_id)

        if task.company_id and task.company_id in self._company_index:
            self._company_index[task.company_id].remove(task_id)

        if task.deal_id and task.deal_id in self._deal_index:
            self._deal_index[task.deal_id].remove(task_id)

        if task.assigned_to and task.assigned_to in self._assigned_index:
            self._assigned_index[task.assigned_to].remove(task_id)

        if task.status in self._status_index:
            self._status_index[task.status].discard(task_id)

        if task.priority in self._priority_index:
            self._priority_index[task.priority].discard(task_id)

        for tag in task.tags:
            if tag in self._tag_index:
                self._tag_index[tag].discard(task_id)

        del self.tasks[task_id]
        return True

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        task_type: Optional[TaskType] = None,
        assigned_to: Optional[str] = None,
        contact_id: Optional[str] = None,
        company_id: Optional[str] = None,
        deal_id: Optional[str] = None,
        overdue_only: bool = False,
        tags: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Task]:
        """List tasks with filtering."""
        results = list(self.tasks.values())

        # Apply filters
        if status:
            results = [t for t in results if t.status == status]

        if priority:
            results = [t for t in results if t.priority == priority]

        if task_type:
            results = [t for t in results if t.task_type == task_type]

        if assigned_to:
            results = [t for t in results if t.assigned_to == assigned_to]

        if contact_id:
            results = [t for t in results if t.contact_id == contact_id]

        if company_id:
            results = [t for t in results if t.company_id == company_id]

        if deal_id:
            results = [t for t in results if t.deal_id == deal_id]

        if overdue_only:
            results = [t for t in results if t.is_overdue]

        if tags:
            results = [t for t in results if any(tag in t.tags for tag in tags)]

        # Sort by priority and due date
        def sort_key(task: Task):
            # Priority order: urgent, high, medium, low
            priority_order = {
                TaskPriority.URGENT: 0,
                TaskPriority.HIGH: 1,
                TaskPriority.MEDIUM: 2,
                TaskPriority.LOW: 3,
            }
            return (
                priority_order.get(task.priority, 4),
                task.due_date or datetime.max,
                task.created_at
            )

        results.sort(key=sort_key)

        # Apply pagination
        if limit:
            results = results[offset:offset + limit]
        else:
            results = results[offset:]

        return results

    def get_my_tasks(
        self,
        user_id: str,
        status: Optional[TaskStatus] = None,
        include_overdue: bool = True
    ) -> Dict[str, List[Task]]:
        """Get tasks organized by category for a user."""
        all_tasks = self.list_tasks(assigned_to=user_id)

        if status:
            all_tasks = [t for t in all_tasks if t.status == status]

        categorized = {
            'overdue': [],
            'today': [],
            'this_week': [],
            'later': [],
            'no_due_date': [],
        }

        today = date.today()
        week_end = today + timedelta(days=7)

        for task in all_tasks:
            if task.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
                continue

            if task.is_overdue and include_overdue:
                categorized['overdue'].append(task)
            elif task.due_date:
                due_date = task.due_date.date() if isinstance(task.due_date, datetime) else task.due_date
                if due_date == today:
                    categorized['today'].append(task)
                elif due_date <= week_end:
                    categorized['this_week'].append(task)
                else:
                    categorized['later'].append(task)
            else:
                categorized['no_due_date'].append(task)

        return categorized

    def complete_task(
        self,
        task_id: str,
        completion_notes: Optional[str] = None
    ) -> Optional[Task]:
        """Mark a task as completed."""
        updates = {
            'status': TaskStatus.COMPLETED,
            'completed_date': datetime.now(),
            'progress': 100,
        }
        if completion_notes:
            updates['notes'] = completion_notes
        return self.update_task(task_id, updates)

    def assign_task(
        self,
        task_id: str,
        assigned_to: str,
        assigned_by: Optional[str] = None
    ) -> Optional[Task]:
        """Assign a task to a user."""
        task = self.tasks.get(task_id)
        if not task:
            return None

        # Update assignment index
        if task.assigned_to and task.assigned_to in self._assigned_index:
            self._assigned_index[task.assigned_to].remove(task_id)

        if assigned_to not in self._assigned_index:
            self._assigned_index[assigned_to] = []
        self._assigned_index[assigned_to].append(task_id)

        updates = {
            'assigned_to': assigned_to,
            'assigned_by': assigned_by,
        }
        return self.update_task(task_id, updates)

    def set_reminder(
        self,
        task_id: str,
        reminder_type: ReminderType
    ) -> Optional[Task]:
        """Set a reminder for a task."""
        return self.update_task(task_id, {'reminder_type': reminder_type})

    def get_tasks_needing_reminders(self) -> List[Task]:
        """Get tasks that need reminders sent."""
        now = datetime.now()
        tasks_to_remind = []

        for task in self.tasks.values():
            if (task.reminder_type != ReminderType.NONE and
                not task.reminder_sent and
                task.due_date and
                task.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]):

                # Calculate when to send reminder
                send_reminder = False

                if task.reminder_type == ReminderType.AT_TIME:
                    send_reminder = now >= task.due_date
                elif task.reminder_type == ReminderType.BEFORE_15MIN:
                    reminder_time = task.due_date - timedelta(minutes=15)
                    send_reminder = now >= reminder_time
                elif task.reminder_type == ReminderType.BEFORE_30MIN:
                    reminder_time = task.due_date - timedelta(minutes=30)
                    send_reminder = now >= reminder_time
                elif task.reminder_type == ReminderType.BEFORE_1HOUR:
                    reminder_time = task.due_date - timedelta(hours=1)
                    send_reminder = now >= reminder_time
                elif task.reminder_type == ReminderType.BEFORE_1DAY:
                    reminder_time = task.due_date - timedelta(days=1)
                    send_reminder = now >= reminder_time

                if send_reminder:
                    tasks_to_remind.append(task)

        return tasks_to_remind

    def mark_reminder_sent(self, task_id: str) -> Optional[Task]:
        """Mark reminder as sent for a task."""
        return self.update_task(task_id, {
            'reminder_sent': True,
            'reminder_sent_at': datetime.now(),
        })

    def get_overdue_tasks(self, assigned_to: Optional[str] = None) -> List[Task]:
        """Get all overdue tasks."""
        tasks = [t for t in self.tasks.values() if t.is_overdue]

        if assigned_to:
            tasks = [t for t in tasks if t.assigned_to == assigned_to]

        # Sort by due date (oldest first)
        tasks.sort(key=lambda t: t.due_date or datetime.min)

        return tasks

    def get_tasks_due_soon(
        self,
        days: int = 3,
        assigned_to: Optional[str] = None
    ) -> List[Task]:
        """Get tasks due within a certain number of days."""
        now = datetime.now()
        due_date_threshold = now + timedelta(days=days)

        tasks = [
            t for t in self.tasks.values()
            if t.due_date
            and now <= t.due_date <= due_date_threshold
            and t.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]
        ]

        if assigned_to:
            tasks = [t for t in tasks if t.assigned_to == assigned_to]

        # Sort by due date
        tasks.sort(key=lambda t: t.due_date or datetime.max)

        return tasks

    def update_progress(self, task_id: str, progress: int) -> Optional[Task]:
        """Update task progress (0-100)."""
        if not 0 <= progress <= 100:
            raise ValueError("Progress must be between 0 and 100")

        updates = {'progress': progress}

        # Auto-update status based on progress
        if progress == 0:
            updates['status'] = TaskStatus.NOT_STARTED
        elif progress == 100:
            updates['status'] = TaskStatus.COMPLETED
            updates['completed_date'] = datetime.now()
        elif progress > 0:
            updates['status'] = TaskStatus.IN_PROGRESS

        return self.update_task(task_id, updates)

    def create_follow_up(
        self,
        title: str,
        due_date: datetime,
        contact_id: Optional[str] = None,
        company_id: Optional[str] = None,
        deal_id: Optional[str] = None,
        assigned_to: Optional[str] = None,
        description: Optional[str] = None,
        priority: TaskPriority = TaskPriority.MEDIUM
    ) -> Task:
        """Quick create a follow-up task."""
        task = Task(
            id=self._generate_id(),
            title=title,
            task_type=TaskType.FOLLOW_UP,
            priority=priority,
            due_date=due_date,
            contact_id=contact_id,
            company_id=company_id,
            deal_id=deal_id,
            assigned_to=assigned_to,
            description=description,
        )
        return self.create_task(task)

    def search_tasks(self, query: str) -> List[Task]:
        """Search tasks by title, description, or notes."""
        query_lower = query.lower()
        results = []

        for task in self.tasks.values():
            if (query_lower in task.title.lower() or
                (task.description and query_lower in task.description.lower()) or
                (task.notes and query_lower in task.notes.lower())):
                results.append(task)

        return results

    def get_statistics(
        self,
        assigned_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get task statistics."""
        tasks = list(self.tasks.values())

        if assigned_to:
            tasks = [t for t in tasks if t.assigned_to == assigned_to]

        total = len(tasks)

        # By status
        by_status = {}
        for status in TaskStatus:
            count = len([t for t in tasks if t.status == status])
            by_status[status.value] = count

        # By priority
        by_priority = {}
        for priority in TaskPriority:
            count = len([t for t in tasks if t.priority == priority])
            by_priority[priority.value] = count

        # By type
        by_type = {}
        for task_type in TaskType:
            count = len([t for t in tasks if t.task_type == task_type])
            by_type[task_type.value] = count

        # Completion metrics
        completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED]
        overdue_tasks = [t for t in tasks if t.is_overdue]

        completion_rate = (len(completed_tasks) / total * 100) if total > 0 else 0

        return {
            'total_tasks': total,
            'by_status': by_status,
            'by_priority': by_priority,
            'by_type': by_type,
            'completed_count': len(completed_tasks),
            'overdue_count': len(overdue_tasks),
            'completion_rate': round(completion_rate, 2),
        }

    def _generate_id(self) -> str:
        """Generate a unique task ID."""
        import uuid
        return f"task_{uuid.uuid4().hex[:12]}"
