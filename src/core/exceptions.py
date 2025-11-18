"""
Custom exceptions for NEXUS Platform.

This module defines all custom exceptions used throughout the application,
providing clear error types for different failure scenarios.
"""
from typing import Any, Dict, Optional


class NexusException(Exception):
    """Base exception for all NEXUS platform errors."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ) -> None:
        """
        Initialize exception.

        Args:
            message: Error message
            details: Additional error details
            status_code: HTTP status code
        """
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(NexusException):
    """Exception raised for validation errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize validation error.

        Args:
            message: Validation error message
            details: Validation error details
        """
        super().__init__(message=message, details=details, status_code=422)


class NotFoundError(NexusException):
    """Exception raised when a resource is not found."""

    def __init__(self, resource: str, resource_id: str) -> None:
        """
        Initialize not found error.

        Args:
            resource: Resource type (e.g., 'Campaign', 'Contact')
            resource_id: Resource identifier
        """
        message = f"{resource} with id '{resource_id}' not found"
        super().__init__(message=message, status_code=404)


class AuthenticationError(NexusException):
    """Exception raised for authentication failures."""

    def __init__(self, message: str = "Authentication failed") -> None:
        """
        Initialize authentication error.

        Args:
            message: Authentication error message
        """
        super().__init__(message=message, status_code=401)


class AuthorizationError(NexusException):
    """Exception raised for authorization failures."""

    def __init__(self, message: str = "Insufficient permissions") -> None:
        """
        Initialize authorization error.

        Args:
            message: Authorization error message
        """
        super().__init__(message=message, status_code=403)


class DatabaseError(NexusException):
    """Exception raised for database operation errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize database error.

        Args:
            message: Database error message
            details: Error details
        """
        super().__init__(message=message, details=details, status_code=500)


class ExternalServiceError(NexusException):
    """Exception raised for external service failures."""

    def __init__(
        self,
        service: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize external service error.

        Args:
            service: Service name (e.g., 'SendGrid', 'Twilio')
            message: Error message
            details: Error details
        """
        full_message = f"{service} error: {message}"
        super().__init__(message=full_message, details=details, status_code=502)


class RateLimitError(NexusException):
    """Exception raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None
    ) -> None:
        """
        Initialize rate limit error.

        Args:
            message: Rate limit error message
            retry_after: Seconds to wait before retrying
        """
        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(message=message, details=details, status_code=429)


class CampaignError(NexusException):
    """Exception raised for campaign-related errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize campaign error.

        Args:
            message: Campaign error message
            details: Error details
        """
        super().__init__(message=message, details=details, status_code=400)


class AutomationError(NexusException):
    """Exception raised for automation workflow errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize automation error.

        Args:
            message: Automation error message
            details: Error details
        """
        super().__init__(message=message, details=details, status_code=400)


class EmailSendError(ExternalServiceError):
    """Exception raised for email sending failures."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize email send error.

        Args:
            message: Email error message
            details: Error details
        """
        super().__init__(service="Email Service", message=message, details=details)


class SMSSendError(ExternalServiceError):
    """Exception raised for SMS sending failures."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize SMS send error.

        Args:
            message: SMS error message
            details: Error details
        """
        super().__init__(service="SMS Service", message=message, details=details)


class LLMError(ExternalServiceError):
    """Exception raised for LLM/AI service errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize LLM error.

        Args:
            message: LLM error message
            details: Error details
        """
        super().__init__(service="LLM Service", message=message, details=details)
