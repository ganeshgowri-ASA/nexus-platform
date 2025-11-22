"""
NEXUS Platform Database Package.

This package provides database models, connection management, and utilities
for the NEXUS Platform using SQLAlchemy 2.0.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import StaticPool, QueuePool

_engine = None
_SessionLocal = None


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


def get_database_url():
    """Get database URL from Railway or environment or default to SQLite"""
    # Railway provides DATABASE_URL environment variable
    if os.getenv('DATABASE_URL'):
        url = os.getenv('DATABASE_URL')
        # Railway uses postgres:// but SQLAlchemy needs postgresql://
        return url.replace('postgres://', 'postgresql://')

    # Try Streamlit secrets
    try:
        import streamlit as st
        return st.secrets["database"]["url"]
    except:
        pass

    # Default to SQLite for local development
    os.makedirs("data", exist_ok=True)
    return "sqlite:///./data/nexus.db"


def init_database():
    """Initialize database with proper connection pooling"""
    global _engine, _SessionLocal

    if _engine is None:
        db_url = get_database_url()

        # Configure based on database type
        if 'sqlite' in db_url:
            _engine = create_engine(
                db_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool
            )
        else:
            # PostgreSQL with connection pooling for Railway
            _engine = create_engine(
                db_url,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True
            )

        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
        Base.metadata.create_all(bind=_engine)

    return _SessionLocal


def get_engine():
    """Get the database engine, initializing if needed."""
    global _engine
    if _engine is None:
        init_database()
    return _engine


def get_db():
    """Get database session"""
    SessionLocal = init_database()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session():
    """Get a new database session (caller responsible for closing)."""
    SessionLocal = init_database()
    return SessionLocal()


# Backwards compatibility aliases
engine = property(lambda self: get_engine())
SessionLocal = property(lambda self: init_database())


def init_db():
    """Alias for init_database for backwards compatibility."""
    init_database()


__all__ = [
    "Base",
    "get_database_url",
    "init_database",
    "init_db",
    "get_db",
    "get_session",
    "get_engine",
]

__version__ = "1.0.0"
