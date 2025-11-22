"""
NEXUS Project Management Module
A comprehensive project management system for the NEXUS platform.

This module provides world-class project management capabilities including:
- Project and task management
- Kanban boards and Gantt charts
- Resource allocation and time tracking
- Budget management
- Milestone tracking
- Team collaboration
- AI-powered insights and recommendations
- Comprehensive reporting and analytics
"""

# Project Management
from .project_manager import (
    ProjectManager,
    Project,
    ProjectStatus,
    ProjectPriority
)

# Task Management
from .task_manager import (
    TaskManager,
    Task,
    TaskStatus,
    TaskPriority,
    RecurrencePattern
)

# Dependencies
from .dependencies import (
    DependencyManager,
    Dependency,
    DependencyType
)

# Kanban
from .kanban import (
    KanbanManager,
    KanbanBoard,
    KanbanColumn,
    KanbanCard,
    Swimlane
)

# Gantt Charts
from .gantt import (
    GanttChart,
    GanttTask
)

# Timeline
from .timeline import (
    TimelineManager,
    TimelineEvent,
    TimelineViewType
)

# Resource Management
from .resource_manager import (
    ResourceManager,
    Resource,
    ResourceAllocation
)

# Milestones
from .milestones import (
    MilestoneManager,
    Milestone,
    MilestoneStatus
)

# Time Tracking
from .time_tracking import (
    TimeTrackingManager,
    TimeEntry,
    Timer,
    TimeEntryStatus
)

# Budget Management
from .budget import (
    BudgetManager,
    Budget,
    Expense,
    ExpenseCategory,
    ExpenseStatus
)

# Collaboration
from .collaboration import (
    CollaborationManager,
    Comment,
    Activity,
    ActivityType,
    Attachment
)

# Reporting
from .reporting import (
    ReportingManager,
    ReportType
)

# AI Assistant
from .ai_assistant import (
    AIProjectAssistant,
    AIInsight
)

# Streamlit UI
from .streamlit_ui import (
    ProjectManagementUI,
    main as run_ui
)


__version__ = "1.0.0"

__all__ = [
    # Project Management
    "ProjectManager",
    "Project",
    "ProjectStatus",
    "ProjectPriority",

    # Task Management
    "TaskManager",
    "Task",
    "TaskStatus",
    "TaskPriority",
    "RecurrencePattern",

    # Dependencies
    "DependencyManager",
    "Dependency",
    "DependencyType",

    # Kanban
    "KanbanManager",
    "KanbanBoard",
    "KanbanColumn",
    "KanbanCard",
    "Swimlane",

    # Gantt
    "GanttChart",
    "GanttTask",

    # Timeline
    "TimelineManager",
    "TimelineEvent",
    "TimelineViewType",

    # Resources
    "ResourceManager",
    "Resource",
    "ResourceAllocation",

    # Milestones
    "MilestoneManager",
    "Milestone",
    "MilestoneStatus",

    # Time Tracking
    "TimeTrackingManager",
    "TimeEntry",
    "Timer",
    "TimeEntryStatus",

    # Budget
    "BudgetManager",
    "Budget",
    "Expense",
    "ExpenseCategory",
    "ExpenseStatus",

    # Collaboration
    "CollaborationManager",
    "Comment",
    "Activity",
    "ActivityType",
    "Attachment",

    # Reporting
    "ReportingManager",
    "ReportType",

    # AI
    "AIProjectAssistant",
    "AIInsight",

    # UI
    "ProjectManagementUI",
    "run_ui"
]


def get_version():
    """Get the current version of the projects module."""
    return __version__


def create_project_management_system():
    """
    Create and return a fully configured project management system.

    Returns:
        Dictionary containing all initialized managers
    """
    # Initialize core managers
    project_manager = ProjectManager()
    task_manager = TaskManager()

    # Initialize supporting managers
    dependency_manager = DependencyManager(task_manager)
    kanban_manager = KanbanManager(task_manager)
    resource_manager = ResourceManager(task_manager)
    milestone_manager = MilestoneManager(task_manager)
    time_tracking_manager = TimeTrackingManager(task_manager)
    budget_manager = BudgetManager(resource_manager)
    collaboration_manager = CollaborationManager()

    # Initialize analytics managers
    reporting_manager = ReportingManager(
        project_manager,
        task_manager,
        resource_manager,
        time_tracking_manager,
        budget_manager,
        milestone_manager
    )

    ai_assistant = AIProjectAssistant(
        project_manager,
        task_manager,
        dependency_manager,
        resource_manager,
        time_tracking_manager,
        budget_manager
    )

    return {
        "project_manager": project_manager,
        "task_manager": task_manager,
        "dependency_manager": dependency_manager,
        "kanban_manager": kanban_manager,
        "resource_manager": resource_manager,
        "milestone_manager": milestone_manager,
        "time_tracking_manager": time_tracking_manager,
        "budget_manager": budget_manager,
        "collaboration_manager": collaboration_manager,
        "reporting_manager": reporting_manager,
        "ai_assistant": ai_assistant
    }


# Module metadata
__author__ = "NEXUS Development Team"
__description__ = "Comprehensive project management system for NEXUS platform"
__license__ = "MIT"
