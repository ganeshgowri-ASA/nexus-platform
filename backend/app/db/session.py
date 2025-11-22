<<<<<<< HEAD
"""
NEXUS Platform - Database Session Management
"""
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import Pool

from backend.app.core.config import settings


# Create database engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.SQL_ECHO,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=20,  # Maximum number of connections to keep in the pool
    max_overflow=0,  # Maximum overflow connections beyond pool_size
    pool_recycle=3600,  # Recycle connections after 1 hour
)


# Set up connection pool event listeners
@event.listens_for(Pool, "connect")
def set_search_path(dbapi_conn, connection_record):
    """Set search path for new connections."""
    cursor = dbapi_conn.cursor()
    cursor.execute("SET search_path TO public")
    cursor.close()


# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.

    Yields:
        Session: SQLAlchemy database session

    Example:
        @router.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database - create all tables."""
    from backend.app.db.base import Base
    Base.metadata.create_all(bind=engine)
=======
"""Database session management"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import Session
from typing import AsyncGenerator
from app.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables"""
    from app.db.base import Base

    async with engine.begin() as conn:
        # Import all models here to ensure they are registered
        from app.modules.ocr import models as ocr_models
        from app.modules.translation import models as translation_models

        await conn.run_sync(Base.metadata.create_all)
>>>>>>> origin/claude/ocr-translation-modules-01Kv1eeHRaW9ea224g8V59NS
