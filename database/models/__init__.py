"""
Database models package for NEXUS Platform.

Models are imported lazily to avoid circular dependencies.
Import specific models directly from database.models module when needed:

    from database.models import Presentation, Slide
    from database import Base, init_database
"""

# Import Base from parent package
from database import Base

# DO NOT import any models here to avoid circular dependencies
# Models should be imported directly where needed

__all__ = ["Base"]
