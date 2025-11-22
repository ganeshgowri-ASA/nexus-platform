"""
Base Model Classes

Provides base classes and mixins for all database models.
"""

from datetime import datetime
from typing import Any, Dict
from sqlalchemy import Column, Integer, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import Session

Base = declarative_base()


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps."""

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class SoftDeleteMixin:
    """Mixin to add soft delete functionality."""

    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    def soft_delete(self, db: Session) -> None:
        """Soft delete the record."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        db.commit()

    def restore(self, db: Session) -> None:
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
        db.commit()


class BaseModel(Base, TimestampMixin):
    """
    Base model for all database tables.

    Provides:
    - Primary key (id)
    - Timestamps (created_at, updated_at)
    - Common utility methods
    """

    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        return cls.__name__.lower() + "s"

    def to_dict(self, exclude: list = None) -> Dict[str, Any]:
        """
        Convert model instance to dictionary.

        Args:
            exclude: List of fields to exclude

        Returns:
            Dictionary representation of the model
        """
        exclude = exclude or []
        result = {}

        for column in self.__table__.columns:
            if column.name not in exclude:
                value = getattr(self, column.name)
                # Convert datetime to ISO format
                if isinstance(value, datetime):
                    value = value.isoformat()
                result[column.name] = value

        return result

    def update(self, db: Session, **kwargs) -> None:
        """
        Update model instance with provided kwargs.

        Args:
            db: Database session
            **kwargs: Fields to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        db.commit()
        db.refresh(self)

    def save(self, db: Session) -> None:
        """
        Save model instance to database.

        Args:
            db: Database session
        """
        db.add(self)
        db.commit()
        db.refresh(self)

    def delete(self, db: Session) -> None:
        """
        Delete model instance from database.

        Args:
            db: Database session
        """
        db.delete(self)
        db.commit()

    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"
