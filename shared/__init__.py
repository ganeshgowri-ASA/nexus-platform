"""Shared utilities and types for NEXUS platform."""

from .types import (
    PaginationParams,
    PaginatedResponse,
    FilterParams,
    SortParams,
)
from .utils import (
    generate_uuid,
    generate_slug,
    validate_email,
    validate_phone,
    sanitize_input,
)
from .exceptions import (
    NexusException,
    ValidationError,
    NotFoundError,
    PermissionError,
    RateLimitError,
)

__all__ = [
    "PaginationParams",
    "PaginatedResponse",
    "FilterParams",
    "SortParams",
    "generate_uuid",
    "generate_slug",
    "validate_email",
    "validate_phone",
    "sanitize_input",
    "NexusException",
    "ValidationError",
    "NotFoundError",
    "PermissionError",
    "RateLimitError",
]
