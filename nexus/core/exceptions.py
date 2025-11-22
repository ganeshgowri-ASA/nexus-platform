"""
Custom Exceptions for NEXUS Platform

Defines all custom exceptions used throughout the platform.
"""

from typing import Any, Dict, Optional


class NexusException(Exception):
    """Base exception for all NEXUS errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize NEXUS exception.

        Args:
            message: Error message
            status_code: HTTP status code
            details: Additional error details
        """
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details,
        }


class AuthenticationError(NexusException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", **kwargs) -> None:
        super().__init__(message, status_code=401, **kwargs)


class AuthorizationError(NexusException):
    """Raised when user is not authorized to perform an action."""

    def __init__(
        self, message: str = "Not authorized to perform this action", **kwargs
    ) -> None:
        super().__init__(message, status_code=403, **kwargs)


class ValidationError(NexusException):
    """Raised when input validation fails."""

    def __init__(self, message: str = "Validation failed", **kwargs) -> None:
        super().__init__(message, status_code=422, **kwargs)


class NotFoundError(NexusException):
    """Raised when a resource is not found."""

    def __init__(self, message: str = "Resource not found", **kwargs) -> None:
        super().__init__(message, status_code=404, **kwargs)


class TranslationError(NexusException):
    """Raised when translation fails."""

    def __init__(self, message: str = "Translation failed", **kwargs) -> None:
        super().__init__(message, status_code=500, **kwargs)


class LanguageDetectionError(NexusException):
    """Raised when language detection fails."""

    def __init__(self, message: str = "Language detection failed", **kwargs) -> None:
        super().__init__(message, status_code=500, **kwargs)


class DocumentProcessingError(NexusException):
    """Raised when document processing fails."""

    def __init__(self, message: str = "Document processing failed", **kwargs) -> None:
        super().__init__(message, status_code=500, **kwargs)


class FileStorageError(NexusException):
    """Raised when file storage operation fails."""

    def __init__(self, message: str = "File storage operation failed", **kwargs) -> None:
        super().__init__(message, status_code=500, **kwargs)


class AIServiceError(NexusException):
    """Raised when AI service call fails."""

    def __init__(self, message: str = "AI service call failed", **kwargs) -> None:
        super().__init__(message, status_code=500, **kwargs)


class CacheError(NexusException):
    """Raised when cache operation fails."""

    def __init__(self, message: str = "Cache operation failed", **kwargs) -> None:
        super().__init__(message, status_code=500, **kwargs)


class RateLimitError(NexusException):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", **kwargs) -> None:
        super().__init__(message, status_code=429, **kwargs)


class ConfigurationError(NexusException):
    """Raised when configuration is invalid."""

    def __init__(self, message: str = "Invalid configuration", **kwargs) -> None:
        super().__init__(message, status_code=500, **kwargs)


class DatabaseError(NexusException):
    """Raised when database operation fails."""

    def __init__(self, message: str = "Database operation failed", **kwargs) -> None:
        super().__init__(message, status_code=500, **kwargs)


class ExternalAPIError(NexusException):
    """Raised when external API call fails."""

    def __init__(self, message: str = "External API call failed", **kwargs) -> None:
        super().__init__(message, status_code=502, **kwargs)
