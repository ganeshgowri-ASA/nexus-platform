<<<<<<< HEAD
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
=======
"""
Database Configuration

SQLAlchemy database engine and session management.
"""

from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


# Create database engine
def create_db_engine(is_test: bool = False):
    """
    Create SQLAlchemy database engine.

    Args:
        is_test: Whether to create a test database engine

    Returns:
        SQLAlchemy engine instance
    """
    database_url = settings.TEST_DATABASE_URL if is_test else settings.DATABASE_URL

    engine_kwargs = {
        "echo": settings.DATABASE_ECHO,
        "future": True,
    }

    if is_test:
        # Use NullPool for testing to avoid connection issues
        engine_kwargs["poolclass"] = NullPool
    else:
        # Use QueuePool for production
        engine_kwargs.update({
            "poolclass": QueuePool,
            "pool_size": settings.DATABASE_POOL_SIZE,
            "max_overflow": settings.DATABASE_MAX_OVERFLOW,
            "pool_pre_ping": True,  # Verify connections before using
            "pool_recycle": 3600,  # Recycle connections after 1 hour
        })

    engine = create_engine(database_url, **engine_kwargs)

    # Add event listeners
    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """Event listener for new database connections."""
        logger.debug("Database connection established")

    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_conn, connection_record, connection_proxy):
        """Event listener for connection checkout from pool."""
        logger.debug("Database connection checked out from pool")

    return engine


# Create session factory
engine = create_db_engine()
>>>>>>> origin/claude/nexus-translation-module-011pENKCpeToEVPri4dLYT7D
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
<<<<<<< HEAD
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

=======
    expire_on_commit=False,
)

>>>>>>> origin/claude/nexus-translation-module-011pENKCpeToEVPri4dLYT7D

def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.

    Yields:
<<<<<<< HEAD
        Session: SQLAlchemy database session.

    Example:
        ```python
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
        ```
=======
        SQLAlchemy session

    Example:
        >>> from fastapi import Depends
        >>> def my_endpoint(db: Session = Depends(get_db)):
        ...     users = db.query(User).all()
>>>>>>> origin/claude/nexus-translation-module-011pENKCpeToEVPri4dLYT7D
    """
    db = SessionLocal()
    try:
        yield db
<<<<<<< HEAD
    except Exception as e:
        logger.error(f"Database session error: {e}")
>>>>>>> origin/claude/build-advertising-lead-generation-01Skr8pwxfdGAtz4wHoobrUL
        db.rollback()
        raise
=======
>>>>>>> origin/claude/nexus-translation-module-011pENKCpeToEVPri4dLYT7D
    finally:
        db.close()


<<<<<<< HEAD
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
=======
def get_db_session() -> Session:
    """
    Get a new database session.

    Returns:
        SQLAlchemy session

    Note:
        Caller is responsible for closing the session.

    Example:
        >>> db = get_db_session()
        >>> try:
        ...     users = db.query(User).all()
        ... finally:
        ...     db.close()
    """
    return SessionLocal()


async def get_async_db() -> Generator:
    """
    Async dependency function to get database session.

    Yields:
        SQLAlchemy session
>>>>>>> origin/claude/nexus-translation-module-011pENKCpeToEVPri4dLYT7D
    """
    db = SessionLocal()
    try:
        yield db
<<<<<<< HEAD
        db.commit()
    except Exception as e:
        logger.error(f"Database transaction error: {e}")
        db.rollback()
        raise
    finally:
        db.close()
=======
    finally:
        await db.close()
>>>>>>> origin/claude/nexus-translation-module-011pENKCpeToEVPri4dLYT7D


def init_db() -> None:
    """
<<<<<<< HEAD
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
=======
    Initialize database tables.

    Creates all tables defined in SQLAlchemy models.
    Should only be used in development or testing.
    In production, use Alembic migrations.
    """
    from nexus.models.base import Base

    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
>>>>>>> origin/claude/nexus-translation-module-011pENKCpeToEVPri4dLYT7D


def drop_db() -> None:
    """
    Drop all database tables.

<<<<<<< HEAD
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
=======
    Warning:
        This will delete all data! Only use in development/testing.
    """
    from nexus.models.base import Base

    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped")


def check_db_connection() -> bool:
    """
    Check if database connection is working.

    Returns:
        True if connection is successful, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
>>>>>>> origin/claude/nexus-translation-module-011pENKCpeToEVPri4dLYT7D
