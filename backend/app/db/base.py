<<<<<<< HEAD
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
=======
"""Base database models and session configuration"""
from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class BaseModel(Base):
    """Base model with common fields"""
    __abstract__ = True

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def dict(self):
        """Convert model to dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
>>>>>>> origin/claude/ocr-translation-modules-01Kv1eeHRaW9ea224g8V59NS
