"""
<<<<<<< HEAD
Database configuration and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import os

# Database URL - defaults to SQLite for development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nexus.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    echo=False,
    pool_pre_ping=True
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


@contextmanager
def get_db():
    """
    Database session context manager
    Usage:
        with get_db() as db:
            db.query(...)
=======
Database configuration and session management for NEXUS platform.

This module sets up SQLAlchemy for database operations with proper
connection pooling and session management.
"""

from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

from backend.core.config import get_settings
from backend.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

# Create database engine based on configuration
if settings.TESTING:
    # Use NullPool for testing to avoid connection issues
    engine = create_engine(
        settings.TEST_DATABASE_URL,
        poolclass=NullPool,
        connect_args={"check_same_thread": False}
        if "sqlite" in settings.TEST_DATABASE_URL
        else {},
    )
else:
    # Production/development engine with connection pooling
    connect_args = {}
    if "sqlite" in settings.DATABASE_URL:
        connect_args["check_same_thread"] = False

    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DB_ECHO,
        poolclass=QueuePool,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=True,  # Enable connection health checks
        connect_args=connect_args,
    )


# Enable SQLite foreign key support
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn: Any, connection_record: Any) -> None:
    """
    Enable foreign key constraints for SQLite.

    Args:
        dbapi_conn: Database API connection
        connection_record: Connection record
    """
    if "sqlite" in settings.DATABASE_URL or (
        settings.TESTING and "sqlite" in settings.TEST_DATABASE_URL
    ):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for all models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Get database session.

    This is a dependency that can be used in FastAPI endpoints
    to get a database session.

    Yields:
        Session: SQLAlchemy database session

    Example:
        >>> from fastapi import Depends
        >>> @app.get("/users")
        >>> def get_users(db: Session = Depends(get_db)):
        ...     return db.query(User).all()
>>>>>>> origin/claude/build-dms-module-01NEqPB75CF7J7XEDr4aawai
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
<<<<<<< HEAD
    except Exception:
=======
    except Exception as e:
        logger.error("database_session_error", error=str(e))
>>>>>>> origin/claude/build-dms-module-01NEqPB75CF7J7XEDr4aawai
        db.rollback()
        raise
    finally:
        db.close()


<<<<<<< HEAD
def init_db():
    """Initialize database - create all tables"""
    from backend.models import notification, preference, template, delivery
    Base.metadata.create_all(bind=engine)


def get_db_session():
    """Get database session for dependency injection"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
=======
def create_tables() -> None:
    """
    Create all database tables.

    This should be called during application startup or in migrations.

    Example:
        >>> create_tables()
    """
    logger.info("creating_database_tables")
    Base.metadata.create_all(bind=engine)
    logger.info("database_tables_created")


def drop_tables() -> None:
    """
    Drop all database tables.

    WARNING: This will delete all data! Use only for testing or development.

    Example:
        >>> drop_tables()
    """
    logger.warning("dropping_database_tables")
    Base.metadata.drop_all(bind=engine)
    logger.warning("database_tables_dropped")


def reset_database() -> None:
    """
    Reset database by dropping and recreating all tables.

    WARNING: This will delete all data! Use only for testing or development.

    Example:
        >>> reset_database()
    """
    logger.warning("resetting_database")
    drop_tables()
    create_tables()
    logger.warning("database_reset_complete")


class DatabaseManager:
    """
    Database manager for manual session management.

    Use this when you need more control over session lifecycle,
    such as in background tasks or CLI scripts.

    Example:
        >>> with DatabaseManager() as db:
        ...     users = db.query(User).all()
    """

    def __init__(self) -> None:
        """Initialize database manager."""
        self.session: Session | None = None

    def __enter__(self) -> Session:
        """Enter context manager and create session."""
        self.session = SessionLocal()
        return self.session

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager and close session."""
        if self.session:
            if exc_type is not None:
                logger.error(
                    "database_transaction_error",
                    exc_type=exc_type.__name__ if exc_type else None,
                    exc_val=str(exc_val) if exc_val else None,
                )
                self.session.rollback()
            else:
                self.session.commit()
            self.session.close()

    def get_session(self) -> Session:
        """
        Get a new database session.

        Returns:
            Session: New database session

        Example:
            >>> manager = DatabaseManager()
            >>> db = manager.get_session()
            >>> users = db.query(User).all()
            >>> db.close()
        """
        return SessionLocal()


def get_db_session() -> Session:
    """
    Get a database session for non-FastAPI contexts.

    Note: Caller is responsible for closing the session.

    Returns:
        Session: Database session

    Example:
        >>> db = get_db_session()
        >>> try:
        ...     users = db.query(User).all()
        ...     db.commit()
        ... finally:
        ...     db.close()
    """
    return SessionLocal()


# Import models here to ensure they're registered with Base
# This should be done after Base is defined
def import_models() -> None:
    """
    Import all models to register them with SQLAlchemy.

    This ensures all models are available when creating tables.
    """
    try:
        # Import all model modules
        from backend.models import (  # noqa: F401
            user,
            document,
        )

        logger.debug("models_imported")
    except ImportError as e:
        logger.warning("model_import_failed", error=str(e))


# Type annotation imports
from typing import Any
>>>>>>> origin/claude/build-dms-module-01NEqPB75CF7J7XEDr4aawai
