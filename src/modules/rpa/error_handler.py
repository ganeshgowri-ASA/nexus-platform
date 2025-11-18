"""
Error handling for RPA module
"""
from typing import Dict, Any, Optional, Callable
from functools import wraps
import traceback
from enum import Enum

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ErrorSeverity(str, Enum):
    """Error severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RPAError(Exception):
    """Base exception for RPA module"""

    def __init__(
        self,
        message: str,
        error_code: str = "RPA_ERROR",
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.severity = severity
        self.details = details or {}
        super().__init__(self.message)


class AutomationNotFoundError(RPAError):
    """Raised when automation is not found"""

    def __init__(self, automation_id: str):
        super().__init__(
            message=f"Automation not found: {automation_id}",
            error_code="AUTOMATION_NOT_FOUND",
            severity=ErrorSeverity.MEDIUM,
            details={"automation_id": automation_id},
        )


class ExecutionError(RPAError):
    """Raised when execution fails"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="EXECUTION_ERROR",
            severity=ErrorSeverity.HIGH,
            details=details,
        )


class ValidationError(RPAError):
    """Raised when validation fails"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            severity=ErrorSeverity.LOW,
            details=details,
        )


class TimeoutError(RPAError):
    """Raised when execution times out"""

    def __init__(self, timeout: int):
        super().__init__(
            message=f"Execution timed out after {timeout} seconds",
            error_code="EXECUTION_TIMEOUT",
            severity=ErrorSeverity.HIGH,
            details={"timeout": timeout},
        )


class ElementNotFoundError(RPAError):
    """Raised when UI element is not found"""

    def __init__(self, element_selector: str):
        super().__init__(
            message=f"UI element not found: {element_selector}",
            error_code="ELEMENT_NOT_FOUND",
            severity=ErrorSeverity.MEDIUM,
            details={"selector": element_selector},
        )


class ErrorHandler:
    """Handles errors and implements retry logic"""

    @staticmethod
    def handle_error(
        error: Exception, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Handle an error and return error details

        Args:
            error: Exception that occurred
            context: Additional context about the error

        Returns:
            Dictionary with error details
        """
        error_type = type(error).__name__
        error_message = str(error)

        # Get traceback
        tb = traceback.format_exc()

        # Build error details
        error_details = {
            "type": error_type,
            "message": error_message,
            "traceback": tb,
        }

        # Add RPA-specific error details
        if isinstance(error, RPAError):
            error_details["code"] = error.error_code
            error_details["severity"] = error.severity.value
            error_details["details"] = error.details

        # Add context
        if context:
            error_details["context"] = context

        # Log error
        logger.error(
            f"Error occurred: {error_type}: {error_message}", exc_info=True
        )

        return error_details

    @staticmethod
    def should_retry(
        error: Exception, retry_config: Dict[str, Any]
    ) -> bool:
        """
        Determine if an error should trigger a retry

        Args:
            error: Exception that occurred
            retry_config: Retry configuration

        Returns:
            True if should retry, False otherwise
        """
        # Check if retries are enabled
        if not retry_config.get("enabled", True):
            return False

        # Get error types that should trigger retry
        retryable_errors = retry_config.get(
            "retryable_errors",
            [
                "TimeoutError",
                "ElementNotFoundError",
                "ConnectionError",
                "HTTPError",
            ],
        )

        error_type = type(error).__name__

        return error_type in retryable_errors

    @staticmethod
    def get_retry_delay(
        attempt: int, retry_config: Dict[str, Any]
    ) -> int:
        """
        Calculate retry delay based on attempt number

        Args:
            attempt: Current retry attempt number
            retry_config: Retry configuration

        Returns:
            Delay in seconds
        """
        strategy = retry_config.get("strategy", "fixed")
        base_delay = retry_config.get("base_delay", 5)

        if strategy == "exponential":
            return base_delay * (2 ** (attempt - 1))
        elif strategy == "linear":
            return base_delay * attempt
        else:  # fixed
            return base_delay


def handle_rpa_errors(func: Callable) -> Callable:
    """
    Decorator to handle RPA errors

    Usage:
        @handle_rpa_errors
        def my_function():
            ...
    """

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except RPAError as e:
            logger.error(f"RPA Error in {func.__name__}: {e.message}")
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error in {func.__name__}: {str(e)}",
                exc_info=True,
            )
            raise RPAError(
                message=f"Unexpected error: {str(e)}",
                error_code="UNEXPECTED_ERROR",
                severity=ErrorSeverity.HIGH,
            )

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except RPAError as e:
            logger.error(f"RPA Error in {func.__name__}: {e.message}")
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error in {func.__name__}: {str(e)}",
                exc_info=True,
            )
            raise RPAError(
                message=f"Unexpected error: {str(e)}",
                error_code="UNEXPECTED_ERROR",
                severity=ErrorSeverity.HIGH,
            )

    # Return appropriate wrapper based on function type
    import asyncio

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
