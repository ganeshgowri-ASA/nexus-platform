"""
NEXUS Platform Database Package.

This package provides database models, connection management, and utilities
for the NEXUS Platform using SQLAlchemy 2.0.

Modules:
    - models: SQLAlchemy ORM models for all core entities
    - connection: Database connection and session management
    - init_db: Database initialization and sample data utilities

Usage:
    from database import get_db, User, Document
    from database.connection import crud

    # Using context manager
    with get_db() as db:
        user = crud.get_by_id(db, User, 1)

    # Using CRUD operations
    with get_db() as db:
        new_user = crud.create(db, User, email="user@example.com", ...)
"""

# Core database components
from database.connection import (
    Base,
    engine,
    SessionLocal,
    get_db,
    get_session,
    crud,
    CRUDBase,
    init_database,
    drop_database,
    get_table_names,
)

# All models
from database.models import (
    User,
    Document,
    Email,
    Chat,
    Project,
    Task,
    File,
    AIInteraction,
)


__all__ = [
    # Connection
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "get_session",
    "crud",
    "CRUDBase",
    "init_database",
    "drop_database",
    "get_table_names",
    # Models
    "User",
    "Document",
    "Email",
    "Chat",
    "Project",
    "Task",
    "File",
    "AIInteraction",
]

__version__ = "1.0.0"
