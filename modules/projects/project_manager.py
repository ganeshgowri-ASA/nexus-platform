"""
NEXUS Project Management Engine
Main project manager for creating, editing, and managing projects.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, date
from enum import Enum
import uuid
import json


class ProjectStatus(Enum):
    """Project status enumeration."""
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ProjectPriority(Enum):
    """Project priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Project:
    """
    Represents a project in the NEXUS platform.

    Attributes:
        id: Unique project identifier
        name: Project name
        description: Project description
        status: Current project status
        priority: Project priority level
        category: Project category
        portfolio: Portfolio this project belongs to
        start_date: Project start date
        end_date: Project end date
        budget: Project budget
        owner: Project owner/manager
        team_members: List of team member IDs
        tags: Project tags
        metadata: Additional metadata
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        status: ProjectStatus = ProjectStatus.PLANNING,
        priority: ProjectPriority = ProjectPriority.MEDIUM,
        category: str = "",
        portfolio: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        budget: float = 0.0,
        owner: Optional[str] = None,
        team_members: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        project_id: Optional[str] = None
    ):
        """Initialize a new project."""
        self.id: str = project_id or str(uuid.uuid4())
        self.name: str = name
        self.description: str = description
        self.status: ProjectStatus = status
        self.priority: ProjectPriority = priority
        self.category: str = category
        self.portfolio: Optional[str] = portfolio
        self.start_date: Optional[date] = start_date
        self.end_date: Optional[date] = end_date
        self.budget: float = budget
        self.owner: Optional[str] = owner
        self.team_members: List[str] = team_members or []
        self.tags: List[str] = tags or []
        self.metadata: Dict[str, Any] = metadata or {}
        self.created_at: datetime = datetime.now()
        self.updated_at: datetime = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert project to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "category": self.category,
            "portfolio": self.portfolio,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "budget": self.budget,
            "owner": self.owner,
            "team_members": self.team_members,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Create project from dictionary."""
        return cls(
            project_id=data.get("id"),
            name=data["name"],
            description=data.get("description", ""),
            status=ProjectStatus(data.get("status", "planning")),
            priority=ProjectPriority(data.get("priority", "medium")),
            category=data.get("category", ""),
            portfolio=data.get("portfolio"),
            start_date=date.fromisoformat(data["start_date"]) if data.get("start_date") else None,
            end_date=date.fromisoformat(data["end_date"]) if data.get("end_date") else None,
            budget=data.get("budget", 0.0),
            owner=data.get("owner"),
            team_members=data.get("team_members", []),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {})
        )

    def update(self, **kwargs) -> None:
        """Update project attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()

    def add_team_member(self, member_id: str) -> None:
        """Add a team member to the project."""
        if member_id not in self.team_members:
            self.team_members.append(member_id)
            self.updated_at = datetime.now()

    def remove_team_member(self, member_id: str) -> None:
        """Remove a team member from the project."""
        if member_id in self.team_members:
            self.team_members.remove(member_id)
            self.updated_at = datetime.now()

    def add_tag(self, tag: str) -> None:
        """Add a tag to the project."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the project."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now()

    def get_progress(self, task_manager: Any) -> float:
        """
        Calculate project progress based on completed tasks.

        Args:
            task_manager: Task manager instance to get tasks

        Returns:
            Progress percentage (0-100)
        """
        tasks = task_manager.get_tasks_by_project(self.id)
        if not tasks:
            return 0.0

        completed = sum(1 for task in tasks if task.status.value == "done")
        return (completed / len(tasks)) * 100


class ProjectManager:
    """
    Main project management engine.
    Handles project creation, editing, deletion, and queries.
    """

    def __init__(self):
        """Initialize the project manager."""
        self.projects: Dict[str, Project] = {}
        self.portfolios: Dict[str, List[str]] = {}  # portfolio_name -> [project_ids]
        self.templates: Dict[str, Dict[str, Any]] = {}

    def create_project(
        self,
        name: str,
        description: str = "",
        **kwargs
    ) -> Project:
        """
        Create a new project.

        Args:
            name: Project name
            description: Project description
            **kwargs: Additional project attributes

        Returns:
            Created project instance
        """
        project = Project(name=name, description=description, **kwargs)
        self.projects[project.id] = project

        # Add to portfolio if specified
        if project.portfolio:
            if project.portfolio not in self.portfolios:
                self.portfolios[project.portfolio] = []
            self.portfolios[project.portfolio].append(project.id)

        return project

    def get_project(self, project_id: str) -> Optional[Project]:
        """
        Get a project by ID.

        Args:
            project_id: Project identifier

        Returns:
            Project instance or None if not found
        """
        return self.projects.get(project_id)

    def update_project(self, project_id: str, **kwargs) -> Optional[Project]:
        """
        Update a project.

        Args:
            project_id: Project identifier
            **kwargs: Attributes to update

        Returns:
            Updated project or None if not found
        """
        project = self.get_project(project_id)
        if project:
            project.update(**kwargs)
        return project

    def delete_project(self, project_id: str) -> bool:
        """
        Delete a project.

        Args:
            project_id: Project identifier

        Returns:
            True if deleted, False if not found
        """
        if project_id in self.projects:
            project = self.projects[project_id]

            # Remove from portfolio
            if project.portfolio and project.portfolio in self.portfolios:
                if project_id in self.portfolios[project.portfolio]:
                    self.portfolios[project.portfolio].remove(project_id)

            del self.projects[project_id]
            return True
        return False

    def list_projects(
        self,
        status: Optional[ProjectStatus] = None,
        category: Optional[str] = None,
        portfolio: Optional[str] = None,
        owner: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Project]:
        """
        List projects with optional filters.

        Args:
            status: Filter by status
            category: Filter by category
            portfolio: Filter by portfolio
            owner: Filter by owner
            tags: Filter by tags (must have all specified tags)

        Returns:
            List of matching projects
        """
        projects = list(self.projects.values())

        if status:
            projects = [p for p in projects if p.status == status]

        if category:
            projects = [p for p in projects if p.category == category]

        if portfolio:
            projects = [p for p in projects if p.portfolio == portfolio]

        if owner:
            projects = [p for p in projects if p.owner == owner]

        if tags:
            projects = [p for p in projects if all(tag in p.tags for tag in tags)]

        return projects

    def search_projects(self, query: str) -> List[Project]:
        """
        Search projects by name or description.

        Args:
            query: Search query

        Returns:
            List of matching projects
        """
        query_lower = query.lower()
        return [
            p for p in self.projects.values()
            if query_lower in p.name.lower() or query_lower in p.description.lower()
        ]

    def create_portfolio(self, name: str, project_ids: Optional[List[str]] = None) -> None:
        """
        Create a project portfolio.

        Args:
            name: Portfolio name
            project_ids: List of project IDs to add
        """
        self.portfolios[name] = project_ids or []

        # Update projects
        for project_id in self.portfolios[name]:
            if project_id in self.projects:
                self.projects[project_id].portfolio = name

    def get_portfolio_projects(self, portfolio: str) -> List[Project]:
        """
        Get all projects in a portfolio.

        Args:
            portfolio: Portfolio name

        Returns:
            List of projects in the portfolio
        """
        project_ids = self.portfolios.get(portfolio, [])
        return [self.projects[pid] for pid in project_ids if pid in self.projects]

    def create_template(self, name: str, template_data: Dict[str, Any]) -> None:
        """
        Create a project template.

        Args:
            name: Template name
            template_data: Template configuration
        """
        self.templates[name] = template_data

    def create_from_template(self, template_name: str, project_name: str, **overrides) -> Optional[Project]:
        """
        Create a project from a template.

        Args:
            template_name: Name of the template
            project_name: Name for the new project
            **overrides: Override template values

        Returns:
            Created project or None if template not found
        """
        if template_name not in self.templates:
            return None

        template = self.templates[template_name].copy()
        template.update(overrides)
        template["name"] = project_name

        return self.create_project(**template)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get project statistics.

        Returns:
            Dictionary of statistics
        """
        total = len(self.projects)
        by_status = {}
        by_priority = {}

        for project in self.projects.values():
            status_key = project.status.value
            priority_key = project.priority.value

            by_status[status_key] = by_status.get(status_key, 0) + 1
            by_priority[priority_key] = by_priority.get(priority_key, 0) + 1

        return {
            "total_projects": total,
            "by_status": by_status,
            "by_priority": by_priority,
            "portfolios": len(self.portfolios),
            "templates": len(self.templates)
        }

    def export_to_json(self, filepath: str) -> None:
        """
        Export all projects to JSON file.

        Args:
            filepath: Path to save JSON file
        """
        data = {
            "projects": [p.to_dict() for p in self.projects.values()],
            "portfolios": self.portfolios,
            "templates": self.templates
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def import_from_json(self, filepath: str) -> None:
        """
        Import projects from JSON file.

        Args:
            filepath: Path to JSON file
        """
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Import projects
        for project_data in data.get("projects", []):
            project = Project.from_dict(project_data)
            self.projects[project.id] = project

        # Import portfolios
        self.portfolios.update(data.get("portfolios", {}))

        # Import templates
        self.templates.update(data.get("templates", {}))
