"""
Database models package for NEXUS Platform.

Models are imported lazily to avoid circular dependencies.
Import specific models directly from their modules when needed.
"""

# Import directly from connection to avoid circular imports
from database.connection import Base
from .base import TimestampMixin

__all__ = ["Base", "TimestampMixin"]
