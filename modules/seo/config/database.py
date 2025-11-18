"""
Database configuration and connection management.

Provides async database session management, connection pooling,
and utilities for database operations.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool, QueuePool

from .settings import get_settings


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class DatabaseManager:
    """
    Manages database connections and sessions.

    Provides methods for creating database engines, sessions,
    and managing database lifecycle.
    """

    def __init__(self) -> None:
        """Initialize database manager."""
        self.settings = get_settings()
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    def get_engine(self) -> AsyncEngine:
        """
        Get or create database engine.

        Returns:
            AsyncEngine: SQLAlchemy async engine
        """
        if self._engine is None:
            self._engine = create_async_engine(
                self.settings.database_url,
                echo=self.settings.log_level == "DEBUG",
                pool_size=self.settings.database_pool_size,
                max_overflow=self.settings.database_max_overflow,
                poolclass=QueuePool if "sqlite" not in self.settings.database_url else NullPool,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
        return self._engine

    def get_session_factory(self) -> async_sessionmaker[AsyncSession]:
        """
        Get or create session factory.

        Returns:
            async_sessionmaker: Session factory for creating database sessions
        """
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                self.get_engine(),
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
        return self._session_factory

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get database session context manager.

        Yields:
            AsyncSession: Database session

        Example:
            async with db_manager.get_session() as session:
                result = await session.execute(query)
        """
        session_factory = self.get_session_factory()
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def create_tables(self) -> None:
        """
        Create all database tables.

        Note:
            This should only be used in development. Use Alembic migrations in production.
        """
        engine = self.get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self) -> None:
        """
        Drop all database tables.

        Warning:
            This will delete all data. Use with caution!
        """
        engine = self.get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def close(self) -> None:
        """Close database connections."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None


# Global database manager instance
db_manager = DatabaseManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get database session.

    Yields:
        AsyncSession: Database session

    Example:
        @app.get("/items")
        async def get_items(session: AsyncSession = Depends(get_db_session)):
            result = await session.execute(select(Item))
            return result.scalars().all()
    """
    async with db_manager.get_session() as session:
        yield session
