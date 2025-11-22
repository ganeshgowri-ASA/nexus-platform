"""
<<<<<<< HEAD
NEXUS Platform - Custom Exceptions
"""
from typing import Any, Optional, Dict
from fastapi import HTTPException, status


class NEXUSException(Exception):
    """Base exception for NEXUS platform."""
=======
Custom exceptions for NEXUS Platform.

This module defines application-specific exceptions for better error handling.
"""

from typing import Any, Optional, Dict


class NexusException(Exception):
    """Base exception for NEXUS Platform."""
>>>>>>> origin/claude/build-campaign-manager-01KFpVYVNSuz2bfrpAMAZpwp

    def __init__(
        self,
        message: str,
<<<<<<< HEAD
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
=======
        status_code: int = 500,
>>>>>>> origin/claude/build-campaign-manager-01KFpVYVNSuz2bfrpAMAZpwp
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


<<<<<<< HEAD
class DatabaseException(NEXUSException):
    """Database operation exception."""

    def __init__(self, message: str = "Database operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class NotFoundException(NEXUSException):
    """Resource not found exception."""

    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )


class ValidationException(NEXUSException):
    """Validation error exception."""

    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class AuthenticationException(NEXUSException):
    """Authentication failed exception."""

    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class AuthorizationException(NEXUSException):
    """Authorization failed exception."""

    def __init__(self, message: str = "Not authorized", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class AttributionException(NEXUSException):
    """Attribution module specific exception."""

    def __init__(self, message: str = "Attribution operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class CacheException(NEXUSException):
    """Cache operation exception."""

    def __init__(self, message: str = "Cache operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )
=======
class AuthenticationError(NexusException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class AuthorizationError(NexusException):
    """Raised when user lacks required permissions."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status_code=403)


class ResourceNotFoundError(NexusException):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str, resource_id: Any):
        message = f"{resource} with id {resource_id} not found"
        super().__init__(message, status_code=404)


class ValidationError(NexusException):
    """Raised when input validation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=422, details=details)


class CampaignError(NexusException):
    """Raised for campaign-specific errors."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message, status_code=status_code)


class BudgetExceededError(CampaignError):
    """Raised when budget allocation exceeds available budget."""

    def __init__(self, available: float, requested: float):
        message = f"Budget exceeded: Available ${available:.2f}, Requested ${requested:.2f}"
        super().__init__(message, status_code=400)


class InvalidStatusTransitionError(CampaignError):
    """Raised when attempting an invalid campaign status transition."""

    def __init__(self, current_status: str, new_status: str):
        message = f"Invalid status transition from '{current_status}' to '{new_status}'"
        super().__init__(message, status_code=400)


class AssetNotFoundError(ResourceNotFoundError):
    """Raised when a campaign asset is not found."""

    def __init__(self, asset_id: int):
        super().__init__("Asset", asset_id)


class ChannelNotFoundError(ResourceNotFoundError):
    """Raised when a campaign channel is not found."""

    def __init__(self, channel_id: int):
        super().__init__("Channel", channel_id)


class FileUploadError(NexusException):
    """Raised when file upload fails."""

    def __init__(self, message: str):
        super().__init__(message, status_code=400)
>>>>>>> origin/claude/build-campaign-manager-01KFpVYVNSuz2bfrpAMAZpwp
