"""
NEXUS Platform Database Package.

Provides lazy-loaded database connection to avoid circular imports
and initialization issues in Streamlit deployment.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

# Base class for all models - can be imported without triggering DB init
Base = declarative_base()

# Private module-level variables for lazy initialization
_engine = None
_SessionLocal = None


def get_database_url():
    """Get database URL from Streamlit secrets or environment."""
    # Try Streamlit secrets first
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'database' in st.secrets:
            return st.secrets["database"]["url"]
    except Exception:
        pass

    # Fall back to environment variable
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        return db_url

    # Default to SQLite in data directory
    os.makedirs("data", exist_ok=True)
    return "sqlite:///./data/nexus.db"


def init_database():
    """Initialize database and create all tables (lazy initialization)."""
    global _engine, _SessionLocal

    if _engine is None:
        db_url = get_database_url()

        if db_url.startswith("sqlite"):
            _engine = create_engine(
                db_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        else:
            _engine = create_engine(
                db_url,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
            )

        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_engine
        )

        # Create all tables
        Base.metadata.create_all(bind=_engine)

    return _SessionLocal


# Alias for backwards compatibility
init_db = init_database


def get_db():
    """Get database session generator for dependency injection."""
    SessionLocal = init_database()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session():
    """Get a new database session directly."""
    SessionLocal = init_database()
    return SessionLocal()


def get_engine():
    """Get database engine (initializes if needed)."""
    init_database()
    return _engine


def get_session_local():
    """Get SessionLocal factory (initializes if needed)."""
    return init_database()


# For backwards compatibility - these are now functions
SessionLocal = property(lambda self: init_database())


__all__ = [
    "Base",
    "get_database_url",
    "init_database",
    "init_db",
    "get_db",
    "get_session",
    "get_engine",
    "get_session_local",
]

__version__ = "1.0.0"
