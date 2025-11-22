"""
Custom exception classes for NEXUS platform.

This module defines all custom exceptions used throughout the application
for better error handling and meaningful error messages.
"""

from typing import Any, Dict, Optional


class NEXUSException(Exception):
    """Base exception class for all NEXUS exceptions."""

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
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details,
        }


# Authentication & Authorization Exceptions


class AuthenticationException(NEXUSException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", **kwargs: Any) -> None:
        super().__init__(message, status_code=401, **kwargs)


class AuthorizationException(NEXUSException):
    """Raised when user lacks permission for an action."""

    def __init__(
        self, message: str = "Permission denied", **kwargs: Any
    ) -> None:
        super().__init__(message, status_code=403, **kwargs)


class InvalidCredentialsException(AuthenticationException):
    """Raised when credentials are invalid."""

    def __init__(
        self, message: str = "Invalid username or password", **kwargs: Any
    ) -> None:
        super().__init__(message, **kwargs)


class TokenExpiredException(AuthenticationException):
    """Raised when JWT token has expired."""

    def __init__(self, message: str = "Token has expired", **kwargs: Any) -> None:
        super().__init__(message, **kwargs)


class InvalidTokenException(AuthenticationException):
    """Raised when JWT token is invalid."""

    def __init__(self, message: str = "Invalid token", **kwargs: Any) -> None:
        super().__init__(message, **kwargs)


# Resource Exceptions


class ResourceNotFoundException(NEXUSException):
    """Raised when a requested resource is not found."""

    def __init__(
        self, resource: str = "Resource", resource_id: Any = None, **kwargs: Any
    ) -> None:
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} with ID '{resource_id}' not found"
        super().__init__(message, status_code=404, **kwargs)


class ResourceAlreadyExistsException(NEXUSException):
    """Raised when attempting to create a resource that already exists."""

    def __init__(self, resource: str = "Resource", **kwargs: Any) -> None:
        super().__init__(f"{resource} already exists", status_code=409, **kwargs)


class ResourceConflictException(NEXUSException):
    """Raised when a resource conflict occurs."""

    def __init__(self, message: str = "Resource conflict", **kwargs: Any) -> None:
        super().__init__(message, status_code=409, **kwargs)


# Document Management Exceptions


class DocumentNotFoundException(ResourceNotFoundException):
    """Raised when a document is not found."""

    def __init__(self, document_id: Any = None, **kwargs: Any) -> None:
        super().__init__("Document", document_id, **kwargs)


class DocumentLockedException(NEXUSException):
    """Raised when attempting to modify a locked document."""

    def __init__(
        self, message: str = "Document is locked by another user", **kwargs: Any
    ) -> None:
        super().__init__(message, status_code=423, **kwargs)


class DocumentVersionNotFoundException(ResourceNotFoundException):
    """Raised when a document version is not found."""

    def __init__(self, version_id: Any = None, **kwargs: Any) -> None:
        super().__init__("Document version", version_id, **kwargs)


class FolderNotFoundException(ResourceNotFoundException):
    """Raised when a folder is not found."""

    def __init__(self, folder_id: Any = None, **kwargs: Any) -> None:
        super().__init__("Folder", folder_id, **kwargs)


class InvalidDocumentTypeException(NEXUSException):
    """Raised when document type is invalid or unsupported."""

    def __init__(
        self, message: str = "Invalid or unsupported document type", **kwargs: Any
    ) -> None:
        super().__init__(message, status_code=400, **kwargs)


class DocumentSizeLimitException(NEXUSException):
    """Raised when document size exceeds the limit."""

    def __init__(
        self, max_size: int, actual_size: int, **kwargs: Any
    ) -> None:
        message = f"Document size {actual_size} bytes exceeds limit of {max_size} bytes"
        super().__init__(message, status_code=413, **kwargs)


class StorageQuotaExceededException(NEXUSException):
    """Raised when storage quota is exceeded."""

    def __init__(
        self, message: str = "Storage quota exceeded", **kwargs: Any
    ) -> None:
        super().__init__(message, status_code=507, **kwargs)


# Storage Exceptions


class StorageException(NEXUSException):
    """Base exception for storage-related errors."""

    def __init__(self, message: str = "Storage error", **kwargs: Any) -> None:
        super().__init__(message, status_code=500, **kwargs)


class FileNotFoundException(StorageException):
    """Raised when a file is not found in storage."""

    def __init__(self, file_path: str, **kwargs: Any) -> None:
        super().__init__(f"File not found: {file_path}", status_code=404, **kwargs)


class FileUploadException(StorageException):
    """Raised when file upload fails."""

    def __init__(
        self, message: str = "File upload failed", **kwargs: Any
    ) -> None:
        super().__init__(message, **kwargs)


class FileDeleteException(StorageException):
    """Raised when file deletion fails."""

    def __init__(
        self, message: str = "File deletion failed", **kwargs: Any
    ) -> None:
        super().__init__(message, **kwargs)


# Validation Exceptions


class ValidationException(NEXUSException):
    """Raised when validation fails."""

    def __init__(
        self,
        message: str = "Validation failed",
        errors: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.get("details", {})
        if errors:
            details["validation_errors"] = errors
        super().__init__(message, status_code=422, details=details, **kwargs)


class InvalidInputException(ValidationException):
    """Raised when input data is invalid."""

    def __init__(self, field: str, reason: str, **kwargs: Any) -> None:
        message = f"Invalid input for field '{field}': {reason}"
        super().__init__(message, **kwargs)


# Search Exceptions


class SearchException(NEXUSException):
    """Raised when search operation fails."""

    def __init__(self, message: str = "Search operation failed", **kwargs: Any) -> None:
        super().__init__(message, status_code=500, **kwargs)


class InvalidSearchQueryException(SearchException):
    """Raised when search query is invalid."""

    def __init__(
        self, message: str = "Invalid search query", **kwargs: Any
    ) -> None:
        super().__init__(message, status_code=400, **kwargs)


# Workflow Exceptions


class WorkflowException(NEXUSException):
    """Base exception for workflow-related errors."""

    def __init__(self, message: str = "Workflow error", **kwargs: Any) -> None:
        super().__init__(message, status_code=500, **kwargs)


class WorkflowNotFoundException(ResourceNotFoundException):
    """Raised when a workflow is not found."""

    def __init__(self, workflow_id: Any = None, **kwargs: Any) -> None:
        super().__init__("Workflow", workflow_id, **kwargs)


class InvalidWorkflowStateException(WorkflowException):
    """Raised when workflow is in an invalid state for the operation."""

    def __init__(
        self, message: str = "Invalid workflow state", **kwargs: Any
    ) -> None:
        super().__init__(message, status_code=400, **kwargs)


class WorkflowApprovalException(WorkflowException):
    """Raised when workflow approval fails."""

    def __init__(
        self, message: str = "Workflow approval failed", **kwargs: Any
    ) -> None:
        super().__init__(message, **kwargs)


# Collaboration Exceptions


class CollaborationException(NEXUSException):
    """Base exception for collaboration-related errors."""

    def __init__(self, message: str = "Collaboration error", **kwargs: Any) -> None:
        super().__init__(message, status_code=500, **kwargs)


class ConcurrentEditException(CollaborationException):
    """Raised when concurrent edit conflict occurs."""

    def __init__(
        self, message: str = "Concurrent edit conflict detected", **kwargs: Any
    ) -> None:
        super().__init__(message, status_code=409, **kwargs)


class CommentNotFoundException(ResourceNotFoundException):
    """Raised when a comment is not found."""

    def __init__(self, comment_id: Any = None, **kwargs: Any) -> None:
        super().__init__("Comment", comment_id, **kwargs)


# Conversion Exceptions


class ConversionException(NEXUSException):
    """Raised when document conversion fails."""

    def __init__(
        self, message: str = "Document conversion failed", **kwargs: Any
    ) -> None:
        super().__init__(message, status_code=500, **kwargs)


class UnsupportedFormatException(ConversionException):
    """Raised when document format is not supported for conversion."""

    def __init__(
        self, format: str, supported_formats: Optional[list[str]] = None, **kwargs: Any
    ) -> None:
        message = f"Unsupported format: {format}"
        if supported_formats:
            message += f". Supported formats: {', '.join(supported_formats)}"
        super().__init__(message, status_code=400, **kwargs)


class OCRException(ConversionException):
    """Raised when OCR processing fails."""

    def __init__(self, message: str = "OCR processing failed", **kwargs: Any) -> None:
        super().__init__(message, **kwargs)


# AI/LLM Exceptions


class AIException(NEXUSException):
    """Base exception for AI-related errors."""

    def __init__(self, message: str = "AI processing error", **kwargs: Any) -> None:
        super().__init__(message, status_code=500, **kwargs)


class AIServiceUnavailableException(AIException):
    """Raised when AI service is unavailable."""

    def __init__(
        self, message: str = "AI service unavailable", **kwargs: Any
    ) -> None:
        super().__init__(message, status_code=503, **kwargs)


class AIQuotaExceededException(AIException):
    """Raised when AI quota is exceeded."""

    def __init__(self, message: str = "AI quota exceeded", **kwargs: Any) -> None:
        super().__init__(message, status_code=429, **kwargs)


# Rate Limiting Exceptions


class RateLimitExceededException(NEXUSException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.get("details", {})
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, status_code=429, details=details, **kwargs)


# Database Exceptions


class DatabaseException(NEXUSException):
    """Raised when database operation fails."""

    def __init__(self, message: str = "Database operation failed", **kwargs: Any) -> None:
        super().__init__(message, status_code=500, **kwargs)


class IntegrityException(DatabaseException):
    """Raised when database integrity constraint is violated."""

    def __init__(
        self, message: str = "Database integrity constraint violated", **kwargs: Any
    ) -> None:
        super().__init__(message, status_code=409, **kwargs)


# Configuration Exceptions


class ConfigurationException(NEXUSException):
    """Raised when configuration is invalid or missing."""

    def __init__(
        self, message: str = "Invalid configuration", **kwargs: Any
    ) -> None:
        super().__init__(message, status_code=500, **kwargs)


# External Service Exceptions


class ExternalServiceException(NEXUSException):
    """Raised when external service call fails."""

    def __init__(
        self, service: str, message: str = "External service error", **kwargs: Any
    ) -> None:
        super().__init__(f"{service}: {message}", status_code=502, **kwargs)


# Integration Exceptions


class IntegrationException(NEXUSException):
    """Raised when integration operation fails."""

    def __init__(
        self, message: str = "Integration operation failed", **kwargs: Any
    ) -> None:
        super().__init__(message, status_code=500, **kwargs)


# Bulk Operation Exceptions


class BulkOperationException(NEXUSException):
    """Raised when bulk operation fails."""

    def __init__(
        self, message: str = "Bulk operation failed", **kwargs: Any
    ) -> None:
        super().__init__(message, status_code=500, **kwargs)


# Report Exceptions


class ReportException(NEXUSException):
    """Raised when report generation fails."""

    def __init__(
        self, message: str = "Report generation failed", **kwargs: Any
    ) -> None:
        super().__init__(message, status_code=500, **kwargs)


# Export Exceptions


class ExportException(NEXUSException):
    """Raised when export operation fails."""

    def __init__(
        self, message: str = "Export operation failed", **kwargs: Any
    ) -> None:
        super().__init__(message, status_code=500, **kwargs)


# Permission Exceptions


class PermissionDeniedException(AuthorizationException):
    """Raised when permission is denied for a specific operation."""

    def __init__(
        self, message: str = "Permission denied for this operation", **kwargs: Any
    ) -> None:
        super().__init__(message, **kwargs)
