"""
NEXUS Platform - Database Base Configuration
"""
from datetime import datetime
from typing import Any
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.ext.declarative import declared_attr, declarative_base
from sqlalchemy.orm import as_declarative


@as_declarative()
class Base:
    """Base class for all database models."""

    id: Any
    __name__: str

    # Generate __tablename__ automatically from class name
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models."""

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )


# Import all models here to ensure they are registered with Base
# This is used by Alembic for migrations
from backend.app.models.attribution import (  # noqa: E402, F401
    Touchpoint,
    Journey,
    Conversion,
    Channel,
    AttributionModel,
    AttributionResult,
)
