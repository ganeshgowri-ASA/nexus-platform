"""
<<<<<<< HEAD
API routers for all NEXUS modules
"""

from .auth import router as auth_router
from .users import router as users_router
from .documents import router as documents_router
from .emails import router as emails_router
from .chat import router as chat_router
from .projects import router as projects_router
from .tasks import router as tasks_router
from .files import router as files_router
from .ai import router as ai_router

__all__ = [
    "auth_router",
    "users_router",
    "documents_router",
    "emails_router",
    "chat_router",
    "projects_router",
    "tasks_router",
    "files_router",
    "ai_router",
]
=======
NEXUS Platform API Routers

FastAPI routers for all platform modules.

Author: NEXUS Platform Team
"""

from . import wiki

__all__ = ["wiki"]
>>>>>>> origin/claude/nexus-wiki-system-014QYW66NHVN69yKZhJKr3Uq
