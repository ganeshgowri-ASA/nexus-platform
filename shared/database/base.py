"""Database base class and session utilities."""
from sqlalchemy.ext.declarative import declarative_base
from typing import Generator

Base = declarative_base()


def get_db() -> Generator:
    """Get database session."""
    from .session import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
