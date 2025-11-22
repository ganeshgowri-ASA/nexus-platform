"""
Database connection and session management for NEXUS Platform.

This module provides database connection utilities, session management,
and base CRUD operations using SQLAlchemy 2.0.
"""

from typing import Any, Dict, Generator, List, Optional, Type, TypeVar
from contextlib import contextmanager
from datetime import datetime
import os

from sqlalchemy import create_engine, event, inspect
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase
from sqlalchemy.pool import StaticPool, QueuePool
from sqlalchemy.engine import Engine


# Type variable for generic model operations
T = TypeVar('T', bound='Base')


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./data/nexus.db"
)

# Create engine with appropriate pool settings based on database type
if DATABASE_URL.startswith("sqlite"):
    # SQLite specific configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    )
else:
    # PostgreSQL/MySQL configuration
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    )


# SQLite foreign key support
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign key support for SQLite."""
    if 'sqlite' in DATABASE_URL:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)


def get_db() -> Generator[Session, None, None]:
    """
    Get database session as a generator (for FastAPI/Streamlit dependency injection).

    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for database sessions.

    Usage:
        with get_db_context() as db:
            user = db.query(User).filter(User.id == 1).first()

    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_session() -> Session:
    """
    Get a new database session.

    Note: Caller is responsible for closing the session.

    Returns:
        Session: SQLAlchemy database session
    """
    return SessionLocal()


class CRUDBase:
    """
    Base class providing CRUD operations for database models.

    This class provides generic create, read, update, and delete operations
    that can be used with any SQLAlchemy model.
    """

    @staticmethod
    def create(db: Session, model: Type[T], **kwargs) -> T:
        """Create a new record in the database."""
        if hasattr(model, 'created_at') and 'created_at' not in kwargs:
            kwargs['created_at'] = datetime.utcnow()
        if hasattr(model, 'updated_at') and 'updated_at' not in kwargs:
            kwargs['updated_at'] = datetime.utcnow()

        instance = model(**kwargs)
        db.add(instance)
        db.commit()
        db.refresh(instance)
        return instance

    @staticmethod
    def get_by_id(db: Session, model: Type[T], id: int) -> Optional[T]:
        """Get a record by its primary key."""
        return db.query(model).filter(model.id == id).first()

    @staticmethod
    def get_multi(
        db: Session,
        model: Type[T],
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """Get multiple records with optional filtering."""
        query = db.query(model)

        if filters:
            for field, value in filters.items():
                if hasattr(model, field):
                    query = query.filter(getattr(model, field) == value)

        if hasattr(model, 'deleted_at'):
            query = query.filter(model.deleted_at.is_(None))

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, model: Type[T], id: int, **kwargs) -> Optional[T]:
        """Update a record by its primary key."""
        instance = db.query(model).filter(model.id == id).first()
        if not instance:
            return None

        if hasattr(model, 'updated_at'):
            kwargs['updated_at'] = datetime.utcnow()

        for field, value in kwargs.items():
            if hasattr(instance, field):
                setattr(instance, field, value)

        db.commit()
        db.refresh(instance)
        return instance

    @staticmethod
    def delete(db: Session, model: Type[T], id: int, soft: bool = True) -> bool:
        """Delete a record by its primary key."""
        instance = db.query(model).filter(model.id == id).first()
        if not instance:
            return False

        if soft and hasattr(model, 'deleted_at'):
            instance.deleted_at = datetime.utcnow()
            if hasattr(model, 'updated_at'):
                instance.updated_at = datetime.utcnow()
            db.commit()
        else:
            db.delete(instance)
            db.commit()

        return True

    @staticmethod
    def count(db: Session, model: Type[T], filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filtering."""
        query = db.query(model)

        if filters:
            for field, value in filters.items():
                if hasattr(model, field):
                    query = query.filter(getattr(model, field) == value)

        if hasattr(model, 'deleted_at'):
            query = query.filter(model.deleted_at.is_(None))

        return query.count()

    @staticmethod
    def exists(db: Session, model: Type[T], filters: Dict[str, Any]) -> bool:
        """Check if a record exists with the given filters."""
        query = db.query(model)

        for field, value in filters.items():
            if hasattr(model, field):
                query = query.filter(getattr(model, field) == value)

        if hasattr(model, 'deleted_at'):
            query = query.filter(model.deleted_at.is_(None))

        return query.first() is not None


# Convenience instance for CRUD operations
crud = CRUDBase()


def init_db():
    """
    Initialize the database by creating all tables.

    This function should be called when setting up a new database.
    For production, use Alembic migrations instead.
    """
    Base.metadata.create_all(bind=engine)


def init_database():
    """Alias for init_db for backwards compatibility."""
    init_db()


def drop_database():
    """
    Drop all tables from the database.

    WARNING: This will delete all data. Use with caution!
    """
    Base.metadata.drop_all(bind=engine)


def get_table_names() -> List[str]:
    """Get list of all table names in the database."""
    inspector = inspect(engine)
    return inspector.get_table_names()
