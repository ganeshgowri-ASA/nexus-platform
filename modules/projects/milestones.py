"""
NEXUS Milestones Module
Milestone tracking and goal management.
"""

from typing import Dict, List, Optional, Any
from datetime import date, datetime
from enum import Enum
import uuid


class MilestoneStatus(Enum):
    """Milestone status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    MISSED = "missed"


class Milestone:
    """
    Represents a project milestone.

    Attributes:
        id: Unique milestone identifier
        project_id: Associated project ID
        name: Milestone name
        description: Milestone description
        due_date: Milestone due date
        status: Milestone status
        progress: Progress percentage (0-100)
        dependencies: List of milestone IDs this depends on
        linked_tasks: List of task IDs linked to this milestone
        is_completed: Whether milestone is completed
        completed_at: Completion timestamp
        metadata: Additional metadata
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    def __init__(
        self,
        project_id: str,
        name: str,
        description: str = "",
        due_date: Optional[date] = None,
        status: MilestoneStatus = MilestoneStatus.PENDING,
        dependencies: Optional[List[str]] = None,
        linked_tasks: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        milestone_id: Optional[str] = None
    ):
        """Initialize a milestone."""
        self.id: str = milestone_id or str(uuid.uuid4())
        self.project_id: str = project_id
        self.name: str = name
        self.description: str = description
        self.due_date: Optional[date] = due_date
        self.status: MilestoneStatus = status
        self.progress: float = 0.0
        self.dependencies: List[str] = dependencies or []
        self.linked_tasks: List[str] = linked_tasks or []
        self.is_completed: bool = False
        self.completed_at: Optional[datetime] = None
        self.metadata: Dict[str, Any] = metadata or {}
        self.created_at: datetime = datetime.now()
        self.updated_at: datetime = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert milestone to dictionary."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "status": self.status.value,
            "progress": self.progress,
            "dependencies": self.dependencies,
            "linked_tasks": self.linked_tasks,
            "is_completed": self.is_completed,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Milestone':
        """Create milestone from dictionary."""
        milestone = cls(
            milestone_id=data.get("id"),
            project_id=data["project_id"],
            name=data["name"],
            description=data.get("description", ""),
            due_date=date.fromisoformat(data["due_date"]) if data.get("due_date") else None,
            status=MilestoneStatus(data.get("status", "pending")),
            dependencies=data.get("dependencies", []),
            linked_tasks=data.get("linked_tasks", []),
            metadata=data.get("metadata", {})
        )

        milestone.progress = data.get("progress", 0.0)
        milestone.is_completed = data.get("is_completed", False)

        return milestone

    def update(self, **kwargs) -> None:
        """Update milestone attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()

    def mark_completed(self) -> None:
        """Mark milestone as completed."""
        self.is_completed = True
        self.status = MilestoneStatus.COMPLETED
        self.progress = 100.0
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()

    def is_overdue(self) -> bool:
        """Check if milestone is overdue."""
        if self.due_date and not self.is_completed:
            return date.today() > self.due_date
        return False


class MilestoneManager:
    """
    Milestone management engine.
    Handles milestone creation, tracking, and progress calculation.
    """

    def __init__(self, task_manager):
        """
        Initialize the milestone manager.

        Args:
            task_manager: Task manager instance
        """
        self.task_manager = task_manager
        self.milestones: Dict[str, Milestone] = {}

    def create_milestone(
        self,
        project_id: str,
        name: str,
        description: str = "",
        due_date: Optional[date] = None,
        **kwargs
    ) -> Milestone:
        """
        Create a new milestone.

        Args:
            project_id: Project identifier
            name: Milestone name
            description: Milestone description
            due_date: Milestone due date
            **kwargs: Additional milestone attributes

        Returns:
            Created milestone
        """
        milestone = Milestone(
            project_id=project_id,
            name=name,
            description=description,
            due_date=due_date,
            **kwargs
        )

        self.milestones[milestone.id] = milestone
        return milestone

    def get_milestone(self, milestone_id: str) -> Optional[Milestone]:
        """Get a milestone by ID."""
        return self.milestones.get(milestone_id)

    def update_milestone(self, milestone_id: str, **kwargs) -> Optional[Milestone]:
        """
        Update a milestone.

        Args:
            milestone_id: Milestone identifier
            **kwargs: Attributes to update

        Returns:
            Updated milestone or None if not found
        """
        milestone = self.get_milestone(milestone_id)
        if milestone:
            milestone.update(**kwargs)
        return milestone

    def delete_milestone(self, milestone_id: str) -> bool:
        """Delete a milestone."""
        if milestone_id in self.milestones:
            del self.milestones[milestone_id]
            return True
        return False

    def get_milestones_by_project(self, project_id: str) -> List[Milestone]:
        """Get all milestones for a project."""
        return [m for m in self.milestones.values() if m.project_id == project_id]

    def link_task_to_milestone(self, milestone_id: str, task_id: str) -> bool:
        """
        Link a task to a milestone.

        Args:
            milestone_id: Milestone identifier
            task_id: Task identifier

        Returns:
            True if linked successfully
        """
        milestone = self.get_milestone(milestone_id)
        task = self.task_manager.get_task(task_id)

        if not milestone or not task:
            return False

        if task_id not in milestone.linked_tasks:
            milestone.linked_tasks.append(task_id)
            milestone.updated_at = datetime.now()

        return True

    def unlink_task_from_milestone(self, milestone_id: str, task_id: str) -> bool:
        """Unlink a task from a milestone."""
        milestone = self.get_milestone(milestone_id)

        if not milestone:
            return False

        if task_id in milestone.linked_tasks:
            milestone.linked_tasks.remove(task_id)
            milestone.updated_at = datetime.now()
            return True

        return False

    def calculate_milestone_progress(self, milestone_id: str) -> float:
        """
        Calculate milestone progress based on linked tasks.

        Args:
            milestone_id: Milestone identifier

        Returns:
            Progress percentage (0-100)
        """
        milestone = self.get_milestone(milestone_id)
        if not milestone:
            return 0.0

        if not milestone.linked_tasks:
            return milestone.progress

        # Calculate based on linked tasks
        total_tasks = len(milestone.linked_tasks)
        completed_tasks = 0

        for task_id in milestone.linked_tasks:
            task = self.task_manager.get_task(task_id)
            if task and task.status.value == "done":
                completed_tasks += 1

        progress = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0.0
        milestone.progress = progress

        # Auto-complete if all tasks done
        if progress >= 100.0 and not milestone.is_completed:
            milestone.mark_completed()

        return progress

    def get_upcoming_milestones(
        self,
        project_id: str,
        days: int = 30
    ) -> List[Milestone]:
        """
        Get upcoming milestones.

        Args:
            project_id: Project identifier
            days: Number of days to look ahead

        Returns:
            List of upcoming milestones
        """
        milestones = self.get_milestones_by_project(project_id)
        today = date.today()

        from datetime import timedelta
        future_date = today + timedelta(days=days)

        upcoming = [
            m for m in milestones
            if m.due_date and today <= m.due_date <= future_date
            and not m.is_completed
        ]

        return sorted(upcoming, key=lambda m: m.due_date)

    def get_overdue_milestones(self, project_id: str) -> List[Milestone]:
        """Get overdue milestones for a project."""
        milestones = self.get_milestones_by_project(project_id)
        return [m for m in milestones if m.is_overdue()]

    def get_milestone_statistics(self, project_id: str) -> Dict[str, Any]:
        """
        Get milestone statistics for a project.

        Args:
            project_id: Project identifier

        Returns:
            Dictionary of statistics
        """
        milestones = self.get_milestones_by_project(project_id)

        total = len(milestones)
        completed = sum(1 for m in milestones if m.is_completed)
        overdue = sum(1 for m in milestones if m.is_overdue())

        avg_progress = sum(m.progress for m in milestones) / total if total > 0 else 0.0

        return {
            "total_milestones": total,
            "completed": completed,
            "in_progress": total - completed,
            "overdue": overdue,
            "average_progress": avg_progress,
            "completion_rate": (completed / total * 100) if total > 0 else 0.0
        }

    def create_milestone_template(
        self,
        name: str,
        template_data: Dict[str, Any]
    ) -> None:
        """
        Create a milestone template.

        Args:
            name: Template name
            template_data: Template configuration
        """
        if not hasattr(self, 'templates'):
            self.templates = {}
        self.templates[name] = template_data

    def auto_update_milestone_status(self, milestone_id: str) -> None:
        """
        Automatically update milestone status based on progress and dates.

        Args:
            milestone_id: Milestone identifier
        """
        milestone = self.get_milestone(milestone_id)
        if not milestone:
            return

        # Calculate progress
        progress = self.calculate_milestone_progress(milestone_id)

        # Update status
        if milestone.is_completed:
            milestone.status = MilestoneStatus.COMPLETED
        elif milestone.is_overdue():
            milestone.status = MilestoneStatus.MISSED
        elif progress > 0:
            milestone.status = MilestoneStatus.IN_PROGRESS
        else:
            milestone.status = MilestoneStatus.PENDING

        milestone.updated_at = datetime.now()
