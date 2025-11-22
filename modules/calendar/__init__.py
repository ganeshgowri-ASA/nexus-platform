"""
NEXUS Calendar & Scheduling Module

A world-class calendar system with comprehensive features including:
- Multiple calendar views (month, week, day, agenda, year)
- Event management with CRUD operations
- Recurring events with complex patterns
- Meeting invitations and RSVP
- Reminders and notifications
- Calendar synchronization (Google, Outlook, iCal)
- Availability and free/busy time
- Time zone support
- Conflict detection
- AI-powered scheduling

Author: NEXUS Platform
Version: 1.0.0
"""

from typing import Dict, Any

__version__ = "1.0.0"
__author__ = "NEXUS Platform"

# Import main components
from .calendar_engine import CalendarEngine
from .event_manager import EventManager
from .scheduling import Scheduler
from .recurrence import RecurrenceEngine
from .reminders import ReminderManager
from .invites import InviteManager
from .availability import AvailabilityManager
from .sync import SyncManager
from .timezones import TimezoneManager
from .conflicts import ConflictDetector
from .ai_scheduler import AIScheduler

__all__ = [
    "CalendarEngine",
    "EventManager",
    "Scheduler",
    "RecurrenceEngine",
    "ReminderManager",
    "InviteManager",
    "AvailabilityManager",
    "SyncManager",
    "TimezoneManager",
    "ConflictDetector",
    "AIScheduler",
]


def get_module_info() -> Dict[str, Any]:
    """
    Get information about the calendar module.

    Returns:
        Dict containing module metadata
    """
    return {
        "name": "Calendar & Scheduling Module",
        "version": __version__,
        "author": __author__,
        "description": "Full-featured calendar system for NEXUS platform",
        "features": [
            "Multiple calendar views",
            "Event management",
            "Recurring events",
            "Meeting invitations",
            "Reminders & notifications",
            "Calendar sync",
            "Availability tracking",
            "Conflict detection",
            "AI scheduling",
        ],
    }
