"""Base module class for all NEXUS modules."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session


class BaseModule(ABC):
    """Base class for all NEXUS modules."""

    MODULE_NAME: str = "base"
    MODULE_ICON: str = "📦"
    MODULE_DESCRIPTION: str = "Base module"
    MODULE_VERSION: str = "1.0.0"

    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize module.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session

    @abstractmethod
    def render_ui(self):
        """Render Streamlit UI for this module."""
        pass

    @abstractmethod
    def get_routes(self):
        """Return FastAPI router for this module."""
        pass

    @abstractmethod
    def get_models(self) -> List:
        """Return list of SQLAlchemy models for this module."""
        pass

    def get_info(self) -> Dict[str, Any]:
        """Return module information."""
        return {
            "name": self.MODULE_NAME,
            "icon": self.MODULE_ICON,
            "description": self.MODULE_DESCRIPTION,
            "version": self.MODULE_VERSION
        }

    def initialize(self):
        """Initialize module (called on startup)."""
        pass

    def cleanup(self):
        """Cleanup module resources."""
        pass
