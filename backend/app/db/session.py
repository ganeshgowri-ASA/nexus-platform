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
