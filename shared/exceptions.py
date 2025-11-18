"""
Custom exceptions for NEXUS platform.

This module defines custom exception classes used throughout the application.
"""


class NexusException(Exception):
    """Base exception class for NEXUS platform."""

    def __init__(self, message: str, status_code: int = 500):
        """
        Initialize exception.

        Args:
            message: Error message.
            status_code: HTTP status code.
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(NexusException):
    """Exception raised for validation errors."""

    def __init__(self, message: str = "Validation error"):
        """Initialize validation error."""
        super().__init__(message, status_code=400)


class NotFoundError(NexusException):
    """Exception raised when resource is not found."""

    def __init__(self, message: str = "Resource not found"):
        """Initialize not found error."""
        super().__init__(message, status_code=404)


class PermissionError(NexusException):
    """Exception raised for permission errors."""

    def __init__(self, message: str = "Permission denied"):
        """Initialize permission error."""
        super().__init__(message, status_code=403)


class AuthenticationError(NexusException):
    """Exception raised for authentication errors."""

    def __init__(self, message: str = "Authentication failed"):
        """Initialize authentication error."""
        super().__init__(message, status_code=401)


class RateLimitError(NexusException):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded"):
        """Initialize rate limit error."""
        super().__init__(message, status_code=429)


class ExternalAPIError(NexusException):
    """Exception raised for external API errors."""

    def __init__(self, message: str = "External API error", service: str = ""):
        """
        Initialize external API error.

        Args:
            message: Error message.
            service: Name of external service.
        """
        self.service = service
        full_message = f"{service}: {message}" if service else message
        super().__init__(full_message, status_code=502)


class DatabaseError(NexusException):
    """Exception raised for database errors."""

    def __init__(self, message: str = "Database error"):
        """Initialize database error."""
        super().__init__(message, status_code=500)


class ConfigurationError(NexusException):
    """Exception raised for configuration errors."""

    def __init__(self, message: str = "Configuration error"):
        """Initialize configuration error."""
        super().__init__(message, status_code=500)
