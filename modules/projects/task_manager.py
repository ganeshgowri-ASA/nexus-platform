"""
NEXUS Task Management Module
Comprehensive task CRUD operations and management.
"""

from typing import Dict, List, Optional, Any, Set
from datetime import datetime, date, timedelta
from enum import Enum
import uuid


class TaskStatus(Enum):
    """Task status enumeration."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class RecurrencePattern(Enum):
    """Task recurrence patterns."""
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class Task:
    """
    Represents a task in a project.

    Attributes:
        id: Unique task identifier
        project_id: Associated project ID
        name: Task name
        description: Task description
        status: Current task status
        priority: Task priority
        assignee: User assigned to task
        reporter: User who created task
        start_date: Task start date
        due_date: Task due date
        estimated_hours: Estimated hours to complete
        actual_hours: Actual hours spent
        progress: Progress percentage (0-100)
        tags: Task tags
        labels: Task labels/categories
        checklist: List of checklist items
        dependencies: List of task IDs this task depends on
        parent_task: Parent task ID (for subtasks)
        subtasks: List of subtask IDs
        recurring: Whether task is recurring
        recurrence_pattern: Recurrence pattern if recurring
        metadata: Additional metadata
        created_at: Creation timestamp
        updated_at: Last update timestamp
        completed_at: Completion timestamp
    """

    def __init__(
        self,
        project_id: str,
        name: str,
        description: str = "",
        status: TaskStatus = TaskStatus.TODO,
        priority: TaskPriority = TaskPriority.MEDIUM,
        assignee: Optional[str] = None,
        reporter: Optional[str] = None,
        start_date: Optional[date] = None,
        due_date: Optional[date] = None,
        estimated_hours: float = 0.0,
        tags: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
        checklist: Optional[List[Dict[str, Any]]] = None,
        parent_task: Optional[str] = None,
        recurring: bool = False,
        recurrence_pattern: Optional[RecurrencePattern] = None,
        metadata: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None
    ):
        """Initialize a new task."""
        self.id: str = task_id or str(uuid.uuid4())
        self.project_id: str = project_id
        self.name: str = name
        self.description: str = description
        self.status: TaskStatus = status
        self.priority: TaskPriority = priority
        self.assignee: Optional[str] = assignee
        self.reporter: Optional[str] = reporter
        self.start_date: Optional[date] = start_date
        self.due_date: Optional[date] = due_date
        self.estimated_hours: float = estimated_hours
        self.actual_hours: float = 0.0
        self.progress: float = 0.0
        self.tags: List[str] = tags or []
        self.labels: List[str] = labels or []
        self.checklist: List[Dict[str, Any]] = checklist or []
        self.dependencies: List[str] = []
        self.parent_task: Optional[str] = parent_task
        self.subtasks: List[str] = []
        self.recurring: bool = recurring
        self.recurrence_pattern: Optional[RecurrencePattern] = recurrence_pattern
        self.metadata: Dict[str, Any] = metadata or {}
        self.created_at: datetime = datetime.now()
        self.updated_at: datetime = datetime.now()
        self.completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "assignee": self.assignee,
            "reporter": self.reporter,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "progress": self.progress,
            "tags": self.tags,
            "labels": self.labels,
            "checklist": self.checklist,
            "dependencies": self.dependencies,
            "parent_task": self.parent_task,
            "subtasks": self.subtasks,
            "recurring": self.recurring,
            "recurrence_pattern": self.recurrence_pattern.value if self.recurrence_pattern else None,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary."""
        task = cls(
            task_id=data.get("id"),
            project_id=data["project_id"],
            name=data["name"],
            description=data.get("description", ""),
            status=TaskStatus(data.get("status", "todo")),
            priority=TaskPriority(data.get("priority", "medium")),
            assignee=data.get("assignee"),
            reporter=data.get("reporter"),
            start_date=date.fromisoformat(data["start_date"]) if data.get("start_date") else None,
            due_date=date.fromisoformat(data["due_date"]) if data.get("due_date") else None,
            estimated_hours=data.get("estimated_hours", 0.0),
            tags=data.get("tags", []),
            labels=data.get("labels", []),
            checklist=data.get("checklist", []),
            parent_task=data.get("parent_task"),
            recurring=data.get("recurring", False),
            recurrence_pattern=RecurrencePattern(data["recurrence_pattern"]) if data.get("recurrence_pattern") else None,
            metadata=data.get("metadata", {})
        )

        task.actual_hours = data.get("actual_hours", 0.0)
        task.progress = data.get("progress", 0.0)
        task.dependencies = data.get("dependencies", [])
        task.subtasks = data.get("subtasks", [])

        return task

    def update(self, **kwargs) -> None:
        """Update task attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()

        # Set completed_at when status changes to done
        if kwargs.get("status") == TaskStatus.DONE and not self.completed_at:
            self.completed_at = datetime.now()
            self.progress = 100.0

    def add_checklist_item(self, item: str, completed: bool = False) -> None:
        """Add a checklist item."""
        self.checklist.append({
            "id": str(uuid.uuid4()),
            "item": item,
            "completed": completed
        })
        self.updated_at = datetime.now()
        self._update_progress_from_checklist()

    def update_checklist_item(self, item_id: str, completed: bool) -> None:
        """Update a checklist item."""
        for item in self.checklist:
            if item["id"] == item_id:
                item["completed"] = completed
                self.updated_at = datetime.now()
                self._update_progress_from_checklist()
                break

    def _update_progress_from_checklist(self) -> None:
        """Update task progress based on checklist completion."""
        if self.checklist:
            completed = sum(1 for item in self.checklist if item.get("completed", False))
            self.progress = (completed / len(self.checklist)) * 100

    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if self.due_date and self.status != TaskStatus.DONE:
            return date.today() > self.due_date
        return False

    def get_next_recurrence_date(self) -> Optional[date]:
        """Get the next recurrence date for recurring tasks."""
        if not self.recurring or not self.recurrence_pattern or not self.due_date:
            return None

        if self.recurrence_pattern == RecurrencePattern.DAILY:
            return self.due_date + timedelta(days=1)
        elif self.recurrence_pattern == RecurrencePattern.WEEKLY:
            return self.due_date + timedelta(weeks=1)
        elif self.recurrence_pattern == RecurrencePattern.BIWEEKLY:
            return self.due_date + timedelta(weeks=2)
        elif self.recurrence_pattern == RecurrencePattern.MONTHLY:
            return self.due_date + timedelta(days=30)
        elif self.recurrence_pattern == RecurrencePattern.QUARTERLY:
            return self.due_date + timedelta(days=90)
        elif self.recurrence_pattern == RecurrencePattern.YEARLY:
            return self.due_date + timedelta(days=365)

        return None


class TaskManager:
    """
    Task management engine.
    Handles task CRUD operations, queries, and task templates.
    """

    def __init__(self):
        """Initialize the task manager."""
        self.tasks: Dict[str, Task] = {}
        self.templates: Dict[str, Dict[str, Any]] = {}

    def create_task(
        self,
        project_id: str,
        name: str,
        description: str = "",
        **kwargs
    ) -> Task:
        """
        Create a new task.

        Args:
            project_id: Project identifier
            name: Task name
            description: Task description
            **kwargs: Additional task attributes

        Returns:
            Created task instance
        """
        task = Task(project_id=project_id, name=name, description=description, **kwargs)
        self.tasks[task.id] = task

        # Add to parent's subtasks if specified
        if task.parent_task and task.parent_task in self.tasks:
            parent = self.tasks[task.parent_task]
            if task.id not in parent.subtasks:
                parent.subtasks.append(task.id)

        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get a task by ID.

        Args:
            task_id: Task identifier

        Returns:
            Task instance or None if not found
        """
        return self.tasks.get(task_id)

    def update_task(self, task_id: str, **kwargs) -> Optional[Task]:
        """
        Update a task.

        Args:
            task_id: Task identifier
            **kwargs: Attributes to update

        Returns:
            Updated task or None if not found
        """
        task = self.get_task(task_id)
        if task:
            task.update(**kwargs)

            # Handle recurring task completion
            if task.status == TaskStatus.DONE and task.recurring:
                self._create_next_recurrence(task)

        return task

    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task.

        Args:
            task_id: Task identifier

        Returns:
            True if deleted, False if not found
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]

            # Remove from parent's subtasks
            if task.parent_task and task.parent_task in self.tasks:
                parent = self.tasks[task.parent_task]
                if task_id in parent.subtasks:
                    parent.subtasks.remove(task_id)

            # Delete all subtasks
            for subtask_id in task.subtasks[:]:
                self.delete_task(subtask_id)

            del self.tasks[task_id]
            return True
        return False

    def get_tasks_by_project(self, project_id: str) -> List[Task]:
        """
        Get all tasks for a project.

        Args:
            project_id: Project identifier

        Returns:
            List of tasks in the project
        """
        return [t for t in self.tasks.values() if t.project_id == project_id]

    def get_tasks_by_assignee(self, assignee: str) -> List[Task]:
        """
        Get all tasks assigned to a user.

        Args:
            assignee: User identifier

        Returns:
            List of assigned tasks
        """
        return [t for t in self.tasks.values() if t.assignee == assignee]

    def get_overdue_tasks(self, project_id: Optional[str] = None) -> List[Task]:
        """
        Get all overdue tasks.

        Args:
            project_id: Optional project filter

        Returns:
            List of overdue tasks
        """
        tasks = self.tasks.values()
        if project_id:
            tasks = [t for t in tasks if t.project_id == project_id]

        return [t for t in tasks if t.is_overdue()]

    def search_tasks(self, query: str, project_id: Optional[str] = None) -> List[Task]:
        """
        Search tasks by name or description.

        Args:
            query: Search query
            project_id: Optional project filter

        Returns:
            List of matching tasks
        """
        query_lower = query.lower()
        tasks = self.tasks.values()

        if project_id:
            tasks = [t for t in tasks if t.project_id == project_id]

        return [
            t for t in tasks
            if query_lower in t.name.lower() or query_lower in t.description.lower()
        ]

    def filter_tasks(
        self,
        project_id: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        assignee: Optional[str] = None,
        tags: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
        due_before: Optional[date] = None,
        due_after: Optional[date] = None
    ) -> List[Task]:
        """
        Filter tasks by multiple criteria.

        Args:
            project_id: Filter by project
            status: Filter by status
            priority: Filter by priority
            assignee: Filter by assignee
            tags: Filter by tags
            labels: Filter by labels
            due_before: Filter by due date (before)
            due_after: Filter by due date (after)

        Returns:
            List of matching tasks
        """
        tasks = list(self.tasks.values())

        if project_id:
            tasks = [t for t in tasks if t.project_id == project_id]

        if status:
            tasks = [t for t in tasks if t.status == status]

        if priority:
            tasks = [t for t in tasks if t.priority == priority]

        if assignee:
            tasks = [t for t in tasks if t.assignee == assignee]

        if tags:
            tasks = [t for t in tasks if all(tag in t.tags for tag in tags)]

        if labels:
            tasks = [t for t in tasks if all(label in t.labels for label in labels)]

        if due_before:
            tasks = [t for t in tasks if t.due_date and t.due_date <= due_before]

        if due_after:
            tasks = [t for t in tasks if t.due_date and t.due_date >= due_after]

        return tasks

    def get_subtasks(self, task_id: str) -> List[Task]:
        """
        Get all subtasks of a task.

        Args:
            task_id: Parent task identifier

        Returns:
            List of subtasks
        """
        task = self.get_task(task_id)
        if not task:
            return []

        return [self.tasks[sid] for sid in task.subtasks if sid in self.tasks]

    def create_template(self, name: str, template_data: Dict[str, Any]) -> None:
        """
        Create a task template.

        Args:
            name: Template name
            template_data: Template configuration
        """
        self.templates[name] = template_data

    def create_from_template(
        self,
        template_name: str,
        project_id: str,
        task_name: str,
        **overrides
    ) -> Optional[Task]:
        """
        Create a task from a template.

        Args:
            template_name: Name of the template
            project_id: Project identifier
            task_name: Name for the new task
            **overrides: Override template values

        Returns:
            Created task or None if template not found
        """
        if template_name not in self.templates:
            return None

        template = self.templates[template_name].copy()
        template.update(overrides)
        template["name"] = task_name
        template["project_id"] = project_id

        return self.create_task(**template)

    def _create_next_recurrence(self, task: Task) -> Optional[Task]:
        """
        Create the next occurrence of a recurring task.

        Args:
            task: The recurring task

        Returns:
            Next task instance or None
        """
        next_date = task.get_next_recurrence_date()
        if not next_date:
            return None

        # Create new task with same properties
        return self.create_task(
            project_id=task.project_id,
            name=task.name,
            description=task.description,
            priority=task.priority,
            assignee=task.assignee,
            reporter=task.reporter,
            start_date=next_date,
            due_date=next_date,
            estimated_hours=task.estimated_hours,
            tags=task.tags.copy(),
            labels=task.labels.copy(),
            recurring=task.recurring,
            recurrence_pattern=task.recurrence_pattern,
            metadata=task.metadata.copy()
        )

    def bulk_update_status(self, task_ids: List[str], status: TaskStatus) -> int:
        """
        Update status for multiple tasks.

        Args:
            task_ids: List of task identifiers
            status: New status

        Returns:
            Number of tasks updated
        """
        count = 0
        for task_id in task_ids:
            if self.update_task(task_id, status=status):
                count += 1
        return count

    def bulk_assign(self, task_ids: List[str], assignee: str) -> int:
        """
        Assign multiple tasks to a user.

        Args:
            task_ids: List of task identifiers
            assignee: User identifier

        Returns:
            Number of tasks updated
        """
        count = 0
        for task_id in task_ids:
            if self.update_task(task_id, assignee=assignee):
                count += 1
        return count

    def get_task_statistics(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get task statistics.

        Args:
            project_id: Optional project filter

        Returns:
            Dictionary of statistics
        """
        tasks = self.tasks.values()
        if project_id:
            tasks = [t for t in tasks if t.project_id == project_id]

        tasks = list(tasks)
        total = len(tasks)

        by_status = {}
        by_priority = {}
        overdue = 0

        for task in tasks:
            by_status[task.status.value] = by_status.get(task.status.value, 0) + 1
            by_priority[task.priority.value] = by_priority.get(task.priority.value, 0) + 1

            if task.is_overdue():
                overdue += 1

        return {
            "total_tasks": total,
            "by_status": by_status,
            "by_priority": by_priority,
            "overdue": overdue
        }
