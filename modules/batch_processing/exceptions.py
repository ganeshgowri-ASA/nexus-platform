"""Custom exceptions for batch processing module."""


class BatchProcessingException(Exception):
    """Base exception for batch processing errors."""
    pass


class JobNotFoundException(BatchProcessingException):
    """Raised when a batch job is not found."""
    pass


class TaskNotFoundException(BatchProcessingException):
    """Raised when a batch task is not found."""
    pass


class InvalidJobStateException(BatchProcessingException):
    """Raised when attempting an invalid operation on a job in a specific state."""
    pass


class FileImportException(BatchProcessingException):
    """Raised when file import fails."""
    pass


class DataTransformationException(BatchProcessingException):
    """Raised when data transformation fails."""
    pass


class ValidationException(BatchProcessingException):
    """Raised when validation fails."""
    pass


class MaxRetriesExceededException(BatchProcessingException):
    """Raised when maximum retry attempts are exceeded."""
    pass


class CancelledException(BatchProcessingException):
    """Raised when a job is cancelled."""
    pass
