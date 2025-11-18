"""Database session management."""
from contextlib import contextmanager
from typing import Generator
from sqlalchemy.orm import Session
from .base import SessionLocal, Base, engine


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Provide a transactional scope for database operations.

    Yields:
        Session: Database session

    Example:
        >>> with get_db_session() as db:
        ...     user = db.query(User).first()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """
    Initialize database tables.

    Creates all tables defined in models if they don't exist.
    """
    # Import all models to ensure they're registered
    from core.auth.models import User  # noqa
    from modules.excel.models import Spreadsheet, SpreadsheetVersion, SpreadsheetShare  # noqa

    # Create all tables
    Base.metadata.create_all(bind=engine)
