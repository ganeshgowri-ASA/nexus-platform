<<<<<<< HEAD
"""Database configuration and utilities."""

from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from src.core.config import settings

# Create base class for declarative models
Base = declarative_base()

# Synchronous engine for SQLite
sync_engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=settings.app_debug
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


def get_db() -> AsyncGenerator[Session, None]:
    """Get database session."""
=======
"""
Database connection and session management for NEXUS Platform.

This module provides database connectivity, session management, and base
model class for SQLAlchemy ORM.
"""
import uuid
from datetime import datetime
from typing import AsyncGenerator, Any

from sqlalchemy import create_engine, MetaData, Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from config.settings import settings
from config.logging_config import get_logger

logger = get_logger(__name__)

# SQLAlchemy metadata and base
metadata = MetaData()
Base = declarative_base(metadata=metadata)


class BaseModel:
    """
    Base model class with common fields and methods.

    Provides id, created_at, and updated_at fields for all models,
    along with utility methods for common operations.
    """

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert model instance to dictionary.

        Returns:
            Dictionary representation of the model
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def __repr__(self) -> str:
        """String representation of model instance."""
        return f"<{self.__class__.__name__}(id={self.id})>"


# Create sync engine for migrations and admin tasks
engine = create_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    echo=settings.debug,
)

# Create sync session maker
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Create async engine for application use
async_database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
async_engine = create_async_engine(
    async_database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    echo=settings.debug,
)

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def get_db() -> Session:
    """
    Get synchronous database session.

    Yields:
        Database session

    Example:
        >>> db = next(get_db())
        >>> try:
        >>>     # Use db session
        >>>     db.commit()
        >>> except Exception:
        >>>     db.rollback()
        >>>     raise
        >>> finally:
        >>>     db.close()
    """
>>>>>>> origin/claude/marketing-automation-module-01QZjZLNDEejmtRGTMvcovNS
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


<<<<<<< HEAD
def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=sync_engine)
=======
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get asynchronous database session.

    Yields:
        Async database session

    Example:
        >>> async for db in get_async_db():
        >>>     result = await db.execute(select(User))
        >>>     users = result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("Database error", error=str(e))
            raise
        finally:
            await session.close()


def init_db() -> None:
    """
    Initialize database by creating all tables.

    This should be called during application startup or via migration scripts.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise


async def close_db() -> None:
    """
    Close database connections.

    This should be called during application shutdown.
    """
    try:
        await async_engine.dispose()
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error("Error closing database connections", error=str(e))
        raise


class DatabaseHealthCheck:
    """Database health check utility."""

    @staticmethod
    async def check() -> bool:
        """
        Check database connectivity.

        Returns:
            True if database is accessible, False otherwise
        """
        try:
            async with AsyncSessionLocal() as session:
                await session.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return False
>>>>>>> origin/claude/marketing-automation-module-01QZjZLNDEejmtRGTMvcovNS
