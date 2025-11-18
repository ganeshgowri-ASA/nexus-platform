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
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.

    Yields:
        SQLAlchemy session

    Example:
        >>> from fastapi import Depends
        >>> def my_endpoint(db: Session = Depends(get_db)):
        ...     users = db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()


def init_db() -> None:
    """
    Initialize database tables.

    Creates all tables defined in SQLAlchemy models.
    Should only be used in development or testing.
    In production, use Alembic migrations.
    """
    from nexus.models.base import Base

    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def drop_db() -> None:
    """
    Drop all database tables.

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
