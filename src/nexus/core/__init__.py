<<<<<<< HEAD
"""Core infrastructure for Nexus Platform."""

from .config import settings
from .database import Base, get_db_session, init_db
from .logger import get_logger

__all__ = ["settings", "Base", "get_db_session", "init_db", "get_logger"]
=======
"""Core functionality for Nexus Platform"""

from .claude_client import ClaudeClient
from .cache import CacheManager
from .auth import AuthManager

__all__ = ["ClaudeClient", "CacheManager", "AuthManager"]
>>>>>>> origin/claude/ai-automation-platform-01KUSGzg11wJKZGW5xToQEW5
