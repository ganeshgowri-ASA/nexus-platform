"""
<<<<<<< HEAD
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
=======
NEXUS Platform Database Package
SQLAlchemy-based database models and utilities
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator
from app.config import settings
from app.utils import get_logger

logger = get_logger(__name__)

# Create declarative base
Base = declarative_base()

# Create database engine
engine = create_engine(
    settings.get_database_url(),
    echo=settings.database.echo,
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    pool_pre_ping=True,  # Verify connections before using
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator:
    """
    Get database session
    Yields database session and ensures proper cleanup
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database
    Creates all tables defined in models
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)
        raise


def drop_db() -> None:
    """
    Drop all database tables
    WARNING: This will delete all data!
    """
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("Database tables dropped")
    except Exception as e:
        logger.error(f"Failed to drop database: {str(e)}", exc_info=True)
        raise


__all__ = [
>>>>>>> origin/claude/nexus-platform-setup-01GgK8vgMUpRwMXvUmBp8eNW
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
<<<<<<< HEAD
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
=======
    "init_db",
    "drop_db",
]
>>>>>>> origin/claude/nexus-platform-setup-01GgK8vgMUpRwMXvUmBp8eNW
