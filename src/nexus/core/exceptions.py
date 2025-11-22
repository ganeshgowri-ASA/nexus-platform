"""Custom exceptions for Nexus Platform."""


class NexusException(Exception):
    """Base exception for Nexus Platform."""

    pass


class DatabaseException(NexusException):
    """Database-related exceptions."""

    pass


class ValidationException(NexusException):
    """Validation-related exceptions."""

    pass


class NotFoundException(NexusException):
    """Resource not found exceptions."""

    pass


class PermissionDeniedException(NexusException):
    """Permission/authorization exceptions."""

    pass


class StorageException(NexusException):
    """File storage exceptions."""

    pass


class ExportException(NexusException):
    """Export/conversion exceptions."""

    pass


class AIException(NexusException):
    """AI service exceptions."""

    pass
