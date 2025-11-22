"""Database configuration and session management."""

import logging
from contextlib import contextmanager
from typing import Generator

import streamlit as st
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from .config import settings

logger = logging.getLogger(__name__)

# Base class for all SQLAlchemy models
Base = declarative_base()


def get_engine() -> Engine:
    """Create and configure SQLAlchemy engine.

    Returns:
        Engine: Configured SQLAlchemy engine
    """
    if "sqlite" in settings.DATABASE_URL:
        engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=settings.DATABASE_ECHO,
        )

        # Enable foreign key support for SQLite
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return engine
    else:
        return create_engine(
            settings.DATABASE_URL,
            echo=settings.DATABASE_ECHO,
            pool_pre_ping=True,
        )


def get_session_factory():
    """Get session factory for database sessions.

    Returns:
        sessionmaker: Session factory
    """
    engine = get_engine()
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


@st.cache_resource
def get_db_session() -> Session:
    """Get cached database session for Streamlit.

    Returns:
        Session: SQLAlchemy session
    """
    SessionLocal = get_session_factory()
    return SessionLocal()


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Context manager for database sessions.

    Yields:
        Session: SQLAlchemy session

    Example:
        >>> with get_db() as db:
        >>>     user = db.query(User).first()
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()


def init_db() -> None:
    """Initialize database by creating all tables.

    This should be called once at application startup.
    """
    engine = get_engine()
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def drop_db() -> None:
    """Drop all database tables.

    WARNING: This will delete all data! Use only for testing/development.
    """
    engine = get_engine()
    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped")
