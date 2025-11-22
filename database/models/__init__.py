"""Database models for NEXUS Platform."""

from database import Base

# DO NOT import any models here - prevents circular dependencies
# Models should be imported directly where needed

__all__ = ["Base"]
