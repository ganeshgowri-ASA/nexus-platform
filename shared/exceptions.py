"""Custom exceptions for NEXUS platform.

This module defines all custom exceptions used throughout the platform,
providing consistent error handling and messaging.
"""

from typing import Any, Dict, Optional


class NexusException(Exception):
    """Base exception for all NEXUS platform errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize exception.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error context
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}


# Contract-specific exceptions
class ContractException(NexusException):
    """Base exception for contract-related errors."""
    pass


class ContractNotFoundError(ContractException):
    """Raised when a contract cannot be found."""
    pass


class ContractValidationError(ContractException):
    """Raised when contract validation fails."""
    pass


class ContractStateError(ContractException):
    """Raised when an invalid state transition is attempted."""
    pass


class ContractPermissionError(ContractException):
    """Raised when user lacks permission for contract operation."""
    pass


class TemplateNotFoundError(ContractException):
    """Raised when a contract template cannot be found."""
    pass


class ClauseNotFoundError(ContractException):
    """Raised when a clause cannot be found."""
    pass


class ApprovalWorkflowError(ContractException):
    """Raised when approval workflow encounters an error."""
    pass


class SignatureError(ContractException):
    """Raised when e-signature operation fails."""
    pass


class ObligationError(ContractException):
    """Raised when obligation management encounters an error."""
    pass


class ComplianceError(ContractException):
    """Raised when compliance check fails."""
    pass


class IntegrationError(ContractException):
    """Raised when external integration fails."""
    pass


class ExportError(ContractException):
    """Raised when document export fails."""
    pass


class ImportError(ContractException):
    """Raised when document import fails."""
    pass


# Database exceptions
class DatabaseException(NexusException):
    """Base exception for database errors."""
    pass


class RecordNotFoundError(DatabaseException):
    """Raised when a database record cannot be found."""
    pass


class DuplicateRecordError(DatabaseException):
    """Raised when attempting to create a duplicate record."""
    pass


# Authentication exceptions
class AuthenticationException(NexusException):
    """Base exception for authentication errors."""
    pass


class AuthorizationException(NexusException):
    """Base exception for authorization errors."""
    pass


# AI/LLM exceptions
class AIException(NexusException):
    """Base exception for AI/LLM errors."""
    pass


class AIProviderError(AIException):
    """Raised when AI provider API fails."""
    pass


class AIProcessingError(AIException):
    """Raised when AI processing encounters an error."""
    pass


# Validation exceptions
class ValidationException(NexusException):
    """Base exception for validation errors."""
    pass


class InvalidInputError(ValidationException):
    """Raised when input validation fails."""
    pass


class InvalidConfigurationError(ValidationException):
    """Raised when configuration is invalid."""
    pass
