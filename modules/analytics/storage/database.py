"""
Database Module

SQLAlchemy database setup with connection pooling and async support.
"""

import logging
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator, Optional

from sqlalchemy import create_engine, event, pool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

from shared.constants import (
    DB_POOL_SIZE,
    DB_MAX_OVERFLOW,
    DB_POOL_TIMEOUT,
    DB_POOL_RECYCLE,
)

logger = logging.getLogger(__name__)

# Base class for ORM models
Base = declarative_base()


class DatabaseConfig:
    """Database configuration."""

    def __init__(
        self,
        database_url: str,
        async_database_url: Optional[str] = None,
        pool_size: int = DB_POOL_SIZE,
        max_overflow: int = DB_MAX_OVERFLOW,
        pool_timeout: int = DB_POOL_TIMEOUT,
        pool_recycle: int = DB_POOL_RECYCLE,
        echo: bool = False,
        echo_pool: bool = False,
    ):
        """
        Initialize database configuration.

        Args:
            database_url: Synchronous database URL
            async_database_url: Asynchronous database URL
            pool_size: Number of connections in pool
            max_overflow: Maximum overflow connections
            pool_timeout: Connection timeout in seconds
            pool_recycle: Connection recycle time in seconds
            echo: Echo SQL statements
            echo_pool: Echo connection pool events
        """
        self.database_url = database_url
        self.async_database_url = async_database_url or database_url.replace(
            "postgresql://", "postgresql+asyncpg://"
        ).replace("mysql://", "mysql+aiomysql://")
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.echo = echo
        self.echo_pool = echo_pool


class Database:
    """Database manager with connection pooling."""

    def __init__(self, config: DatabaseConfig):
        """
        Initialize database manager.

        Args:
            config: Database configuration
        """
        self.config = config
        self._engine: Optional[create_engine] = None
        self._async_engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._async_session_factory: Optional[async_sessionmaker] = None

        logger.info("Database manager initialized")

    def get_engine(self) -> create_engine:
        """
        Get or create synchronous database engine.

        Returns:
            SQLAlchemy engine
        """
        if self._engine is None:
            self._engine = create_engine(
                self.config.database_url,
                poolclass=QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                echo=self.config.echo,
                echo_pool=self.config.echo_pool,
                pool_pre_ping=True,  # Enable connection health checks
            )

            # Set up event listeners
            self._setup_engine_events(self._engine)

            logger.info(
                f"Created database engine: pool_size={self.config.pool_size}, "
                f"max_overflow={self.config.max_overflow}"
            )

        return self._engine

    def get_async_engine(self) -> AsyncEngine:
        """
        Get or create asynchronous database engine.

        Returns:
            Async SQLAlchemy engine
        """
        if self._async_engine is None:
            self._async_engine = create_async_engine(
                self.config.async_database_url,
                poolclass=QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                echo=self.config.echo,
                echo_pool=self.config.echo_pool,
                pool_pre_ping=True,
            )

            logger.info(
                f"Created async database engine: pool_size={self.config.pool_size}, "
                f"max_overflow={self.config.max_overflow}"
            )

        return self._async_engine

    def get_session_factory(self) -> sessionmaker:
        """
        Get or create session factory.

        Returns:
            Session factory
        """
        if self._session_factory is None:
            engine = self.get_engine()
            self._session_factory = sessionmaker(
                bind=engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False,
            )

            logger.debug("Created session factory")

        return self._session_factory

    def get_async_session_factory(self) -> async_sessionmaker:
        """
        Get or create async session factory.

        Returns:
            Async session factory
        """
        if self._async_session_factory is None:
            engine = self.get_async_engine()
            self._async_session_factory = async_sessionmaker(
                bind=engine,
                class_=AsyncSession,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False,
            )

            logger.debug("Created async session factory")

        return self._async_session_factory

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """
        Create a database session context manager.

        Yields:
            Database session

        Example:
            >>> with db.session() as session:
            ...     user = session.query(User).first()
        """
        session_factory = self.get_session_factory()
        session = session_factory()

        try:
            logger.debug("Database session started")
            yield session
            session.commit()
            logger.debug("Database session committed")
        except Exception as e:
            logger.error(f"Database session error: {e}", exc_info=True)
            session.rollback()
            raise
        finally:
            session.close()
            logger.debug("Database session closed")

    @asynccontextmanager
    async def async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Create an async database session context manager.

        Yields:
            Async database session

        Example:
            >>> async with db.async_session() as session:
            ...     result = await session.execute(select(User))
        """
        session_factory = self.get_async_session_factory()
        session = session_factory()

        try:
            logger.debug("Async database session started")
            yield session
            await session.commit()
            logger.debug("Async database session committed")
        except Exception as e:
            logger.error(f"Async database session error: {e}", exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()
            logger.debug("Async database session closed")

    def create_tables(self) -> None:
        """
        Create all database tables.

        Example:
            >>> db.create_tables()
        """
        try:
            engine = self.get_engine()
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}", exc_info=True)
            raise

    def drop_tables(self) -> None:
        """
        Drop all database tables.

        Warning:
            This will delete all data. Use with caution.

        Example:
            >>> db.drop_tables()
        """
        try:
            engine = self.get_engine()
            Base.metadata.drop_all(bind=engine)
            logger.warning("Database tables dropped")
        except Exception as e:
            logger.error(f"Error dropping database tables: {e}", exc_info=True)
            raise

    def dispose(self) -> None:
        """
        Dispose of all database connections.

        Example:
            >>> db.dispose()
        """
        if self._engine:
            self._engine.dispose()
            logger.info("Database engine disposed")

        if self._async_engine:
            # Async engine disposal is handled differently
            logger.info("Async database engine will be disposed on event loop close")

    async def async_dispose(self) -> None:
        """
        Dispose of async database connections.

        Example:
            >>> await db.async_dispose()
        """
        if self._async_engine:
            await self._async_engine.dispose()
            logger.info("Async database engine disposed")

    def _setup_engine_events(self, engine: create_engine) -> None:
        """
        Set up database engine event listeners.

        Args:
            engine: SQLAlchemy engine
        """

        @event.listens_for(engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Handle new database connections."""
            logger.debug("New database connection established")

        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """Handle connection checkout from pool."""
            logger.debug("Connection checked out from pool")

        @event.listens_for(engine, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            """Handle connection checkin to pool."""
            logger.debug("Connection checked in to pool")

    def get_pool_status(self) -> dict:
        """
        Get connection pool status.

        Returns:
            Dictionary with pool statistics

        Example:
            >>> status = db.get_pool_status()
            >>> print(status['size'])
        """
        if self._engine is None:
            return {"status": "not_initialized"}

        pool = self._engine.pool
        return {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "timeout": self.config.pool_timeout,
        }

    def health_check(self) -> bool:
        """
        Perform database health check.

        Returns:
            True if database is healthy, False otherwise

        Example:
            >>> if db.health_check():
            ...     print("Database is healthy")
        """
        try:
            with self.session() as session:
                session.execute("SELECT 1")
            logger.info("Database health check passed")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}", exc_info=True)
            return False

    async def async_health_check(self) -> bool:
        """
        Perform async database health check.

        Returns:
            True if database is healthy, False otherwise

        Example:
            >>> if await db.async_health_check():
            ...     print("Database is healthy")
        """
        try:
            async with self.async_session() as session:
                await session.execute("SELECT 1")
            logger.info("Async database health check passed")
            return True
        except Exception as e:
            logger.error(f"Async database health check failed: {e}", exc_info=True)
            return False


# Global database instance
_db_instance: Optional[Database] = None


def init_database(config: DatabaseConfig) -> Database:
    """
    Initialize global database instance.

    Args:
        config: Database configuration

    Returns:
        Database instance

    Example:
        >>> config = DatabaseConfig("postgresql://localhost/nexus")
        >>> db = init_database(config)
    """
    global _db_instance
    _db_instance = Database(config)
    logger.info("Global database instance initialized")
    return _db_instance


def get_database() -> Database:
    """
    Get global database instance.

    Returns:
        Database instance

    Raises:
        RuntimeError: If database not initialized

    Example:
        >>> db = get_database()
        >>> with db.session() as session:
        ...     pass
    """
    if _db_instance is None:
        raise RuntimeError(
            "Database not initialized. Call init_database() first."
        )
    return _db_instance
