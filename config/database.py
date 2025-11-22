<<<<<<< HEAD
"""Database configuration and session management."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

from .settings import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.SQLALCHEMY_ECHO,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Get database session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """Get database session as context manager."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
=======
"""
Database configuration and session management.

This module provides SQLAlchemy database configuration, session management,
and connection pooling for the NEXUS platform.
"""

from typing import Generator
from contextlib import contextmanager
from sqlalchemy import create_engine, event, Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool

from .settings import settings
from .logging_config import get_logger

logger = get_logger(__name__)

# Create SQLAlchemy engine
engine = create_engine(
    settings.database_url,
    echo=settings.db_echo,
    poolclass=QueuePool,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Create SessionLocal class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Create Base class for declarative models
Base = declarative_base()


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Set SQLite pragmas for better performance (if using SQLite)."""
    if "sqlite" in settings.database_url:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.

    Yields:
        Session: SQLAlchemy database session.

    Example:
        ```python
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
        ```
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
>>>>>>> origin/claude/build-advertising-lead-generation-01Skr8pwxfdGAtz4wHoobrUL
        db.rollback()
        raise
    finally:
        db.close()


<<<<<<< HEAD
def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def drop_db():
    """Drop all database tables (use with caution!)."""
    Base.metadata.drop_all(bind=engine)
=======
@contextmanager
def get_db_context():
    """
    Context manager for database sessions.

    Yields:
        Session: SQLAlchemy database session.

    Example:
        ```python
        with get_db_context() as db:
            user = db.query(User).first()
        ```
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database transaction error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database by creating all tables.

    This should be called on application startup.
    """
    try:
        # Import all models here to ensure they're registered
        from modules.lead_generation.models import (
            Lead,
            LeadSource,
            LeadActivity,
            Form,
            LandingPage,
            Popup,
        )
        from modules.advertising.models import (
            Campaign,
            AdGroup,
            Ad,
            Creative,
            AdPerformance,
        )

        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def drop_db() -> None:
    """
    Drop all database tables.

    WARNING: This will delete all data. Use with caution.
    """
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise


def reset_db() -> None:
    """
    Reset database by dropping and recreating all tables.

    WARNING: This will delete all data. Use with caution.
    """
    try:
        drop_db()
        init_db()
        logger.warning("Database reset complete")
    except Exception as e:
        logger.error(f"Failed to reset database: {e}")
        raise
>>>>>>> origin/claude/build-advertising-lead-generation-01Skr8pwxfdGAtz4wHoobrUL
