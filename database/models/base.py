"""Base models and mixins for database models."""

from datetime import datetime
from sqlalchemy import Column, DateTime

# Import Base from parent package
from database import Base


class TimestampMixin:
    """Mixin for adding timestamp columns."""

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )


__all__ = ["Base", "TimestampMixin"]
