"""
Base model for all database models.

This module provides the base model with common fields for all entities.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, Boolean
from sqlalchemy.ext.declarative import declared_attr

from app.database import Base


class BaseModel(Base):
    """
    Base model with common fields for all entities.

    Provides:
    - id: Primary key
    - created_at: Timestamp when record was created
    - updated_at: Timestamp when record was last updated
    - is_deleted: Soft delete flag (for soft delete functionality)
    """

    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        return cls.__name__.lower() + "s"

    def soft_delete(self) -> None:
        """Mark record as deleted without removing from database."""
        self.is_deleted = True

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.is_deleted = False

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
