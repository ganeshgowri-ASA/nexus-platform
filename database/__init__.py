"""
NEXUS Platform Database Package.

This package provides database models, connection management, and utilities
for the NEXUS Platform using SQLAlchemy 2.0.

Usage:
    from database import get_db, SessionLocal, Base
    from database.connection import crud

    # Using generator for FastAPI/Streamlit
    db = next(get_db())
    try:
        # do work
    finally:
        db.close()
"""

# Core database components
from database.connection import (
    Base,
    engine,
    SessionLocal,
    get_db,
    get_session,
    get_db_context,
    crud,
    CRUDBase,
    init_db,
    init_database,
    drop_database,
    get_table_names,
)

# Import models - wrapped in try/except to handle circular imports
try:
    from database.models import (
        Presentation,
        Slide,
        EmailMessage,
        EmailDraft,
        ChatRoom,
        ChatMessage,
        Project,
        Task,
        Milestone,
        CalendarEvent,
        VideoConference,
        ConferenceRecording,
        Note,
        CRMContact,
        CRMDeal,
        CRMActivity,
    )

    __all__ = [
        # Connection
        "Base",
        "engine",
        "SessionLocal",
        "get_db",
        "get_session",
        "get_db_context",
        "crud",
        "CRUDBase",
        "init_db",
        "init_database",
        "drop_database",
        "get_table_names",
        # Models
        "Presentation",
        "Slide",
        "EmailMessage",
        "EmailDraft",
        "ChatRoom",
        "ChatMessage",
        "Project",
        "Task",
        "Milestone",
        "CalendarEvent",
        "VideoConference",
        "ConferenceRecording",
        "Note",
        "CRMContact",
        "CRMDeal",
        "CRMActivity",
    ]
except ImportError:
    # Models may not be available during initial setup
    __all__ = [
        "Base",
        "engine",
        "SessionLocal",
        "get_db",
        "get_session",
        "get_db_context",
        "crud",
        "CRUDBase",
        "init_db",
        "init_database",
        "drop_database",
        "get_table_names",
    ]

__version__ = "1.0.0"
