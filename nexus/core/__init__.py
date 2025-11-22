"""
NEXUS Core Package

Core functionality for the NEXUS platform including database, security, and utilities.
"""

from .database import get_db, get_db_session, init_db
from .exceptions import (
    NexusException,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    NotFoundError,
    TranslationError,
)
from .security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
)

__all__ = [
    "get_db",
    "get_db_session",
    "init_db",
    "NexusException",
    "AuthenticationError",
    "AuthorizationError",
    "ValidationError",
    "NotFoundError",
    "TranslationError",
    "get_password_hash",
    "verify_password",
    "create_access_token",
    "decode_access_token",
]
