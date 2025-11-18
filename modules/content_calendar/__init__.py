"""
Content Calendar Module for NEXUS Platform.

A comprehensive content calendar system with:
- Visual calendar planning
- Multi-channel content management
- AI-powered content suggestions
- Team collaboration and workflows
- Analytics and performance tracking
"""
from .calendar_types import (
    CalendarEvent,
    ContentPlan,
    ScheduleConfig,
    RecurringPattern,
    PublishingChannel,
)
from .planner import ContentPlanner
from .content import ContentManager
from .scheduling import ContentScheduler
from .workflows import WorkflowManager
from .collaboration import CollaborationManager
from .analytics import AnalyticsManager
from .integration import IntegrationManager

__version__ = "1.0.0"

__all__ = [
    "CalendarEvent",
    "ContentPlan",
    "ScheduleConfig",
    "RecurringPattern",
    "PublishingChannel",
    "ContentPlanner",
    "ContentManager",
    "ContentScheduler",
    "WorkflowManager",
    "CollaborationManager",
    "AnalyticsManager",
    "IntegrationManager",
]
