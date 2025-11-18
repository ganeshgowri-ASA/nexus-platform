"""
Pydantic schemas for API request/response validation
"""

from .user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserInDB,
    Token,
    TokenData,
)
from .document import (
    DocumentBase,
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
)
from .email import (
    EmailBase,
    EmailCreate,
    EmailSend,
    EmailResponse,
)
from .chat import (
    MessageBase,
    MessageCreate,
    MessageResponse,
    ChatRoomBase,
    ChatRoomCreate,
    ChatRoomResponse,
)
from .project import (
    ProjectBase,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
)
from .task import (
    TaskBase,
    TaskCreate,
    TaskUpdate,
    TaskResponse,
)
from .file import (
    FileBase,
    FileCreate,
    FileResponse,
    FileUploadResponse,
)
from .ai import (
    AICompletionRequest,
    AICompletionResponse,
    AIModelInfo,
)
from .common import (
    PaginatedResponse,
    MessageResponse as GenericMessageResponse,
)

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserInDB",
    "Token",
    "TokenData",
    # Document schemas
    "DocumentBase",
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentResponse",
    # Email schemas
    "EmailBase",
    "EmailCreate",
    "EmailSend",
    "EmailResponse",
    # Chat schemas
    "MessageBase",
    "MessageCreate",
    "MessageResponse",
    "ChatRoomBase",
    "ChatRoomCreate",
    "ChatRoomResponse",
    # Project schemas
    "ProjectBase",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    # Task schemas
    "TaskBase",
    "TaskCreate",
    "TaskUpdate",
    "TaskResponse",
    # File schemas
    "FileBase",
    "FileCreate",
    "FileResponse",
    "FileUploadResponse",
    # AI schemas
    "AICompletionRequest",
    "AICompletionResponse",
    "AIModelInfo",
    # Common schemas
    "PaginatedResponse",
    "GenericMessageResponse",
]
