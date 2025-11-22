"""Error tracking and monitoring for the NEXUS platform."""

import sys
import traceback
from datetime import datetime
from typing import Any, Dict, Optional, Type
from types import TracebackType

import structlog


class ErrorTracker:
    """Centralized error tracking and monitoring."""

    def __init__(self) -> None:
        """Initialize error tracker."""
        self.logger = structlog.get_logger("nexus.errors")

    def track_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        severity: str = "error",
        **kwargs: Any,
    ) -> None:
        """Track an error with full context.

        Args:
            error: The exception that occurred
            context: Additional context about the error
            user_id: User ID if applicable
            request_id: Request ID for correlation
            severity: Error severity (warning/error/critical)
            **kwargs: Additional fields
        """
        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Add traceback
        exc_type, exc_value, exc_traceback = sys.exc_info()
        if exc_traceback:
            error_data["traceback"] = "".join(
                traceback.format_exception(exc_type, exc_value, exc_traceback)
            )
            error_data["stack_trace"] = traceback.extract_tb(exc_traceback).format()

        # Add context
        if context:
            error_data["context"] = context
        if user_id:
            error_data["user_id"] = user_id
        if request_id:
            error_data["request_id"] = request_id

        # Add any additional fields
        error_data.update(kwargs)

        # Log based on severity
        if severity == "critical":
            self.logger.critical("error_tracked", **error_data)
        elif severity == "warning":
            self.logger.warning("error_tracked", **error_data)
        else:
            self.logger.error("error_tracked", **error_data)

    def track_exception(
        self,
        exc_type: Type[BaseException],
        exc_value: BaseException,
        exc_traceback: Optional[TracebackType],
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Track an exception with type, value, and traceback.

        Args:
            exc_type: Exception type
            exc_value: Exception instance
            exc_traceback: Traceback object
            context: Additional context
            **kwargs: Additional fields
        """
        error_data = {
            "error_type": exc_type.__name__,
            "error_message": str(exc_value),
            "timestamp": datetime.utcnow().isoformat(),
        }

        if exc_traceback:
            error_data["traceback"] = "".join(
                traceback.format_exception(exc_type, exc_value, exc_traceback)
            )

        if context:
            error_data["context"] = context

        error_data.update(kwargs)

        self.logger.error("exception_tracked", **error_data)

    def track_validation_error(
        self,
        field: str,
        value: Any,
        expected: str,
        user_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Track validation errors.

        Args:
            field: Field name that failed validation
            value: Value that failed validation
            expected: Expected format/type
            user_id: User ID if applicable
            **kwargs: Additional fields
        """
        error_data = {
            "error_type": "ValidationError",
            "field": field,
            "value": str(value),
            "expected": expected,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if user_id:
            error_data["user_id"] = user_id

        error_data.update(kwargs)

        self.logger.warning("validation_error", **error_data)

    def track_http_error(
        self,
        status_code: int,
        method: str,
        url: str,
        error_message: Optional[str] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Track HTTP errors.

        Args:
            status_code: HTTP status code
            method: HTTP method
            url: Request URL
            error_message: Error message if available
            user_id: User ID if applicable
            request_id: Request ID for correlation
            **kwargs: Additional fields
        """
        error_data = {
            "error_type": "HTTPError",
            "status_code": status_code,
            "method": method,
            "url": url,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if error_message:
            error_data["error_message"] = error_message
        if user_id:
            error_data["user_id"] = user_id
        if request_id:
            error_data["request_id"] = request_id

        error_data.update(kwargs)

        # Determine severity based on status code
        if status_code >= 500:
            self.logger.error("http_error", **error_data)
        else:
            self.logger.warning("http_error", **error_data)

    def track_database_error(
        self,
        operation: str,
        table: str,
        error: Exception,
        query: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Track database errors.

        Args:
            operation: Database operation (select/insert/update/delete)
            table: Table name
            error: Exception that occurred
            query: SQL query if available
            **kwargs: Additional fields
        """
        error_data = {
            "error_type": "DatabaseError",
            "db_operation": operation,
            "table": table,
            "error_message": str(error),
            "timestamp": datetime.utcnow().isoformat(),
        }

        if query:
            error_data["query"] = query

        error_data.update(kwargs)

        self.logger.error("database_error", **error_data)


def setup_global_exception_handler(error_tracker: ErrorTracker) -> None:
    """Set up global exception handler.

    Args:
        error_tracker: ErrorTracker instance to use
    """

    def handle_exception(
        exc_type: Type[BaseException],
        exc_value: BaseException,
        exc_traceback: Optional[TracebackType],
    ) -> None:
        """Handle uncaught exceptions.

        Args:
            exc_type: Exception type
            exc_value: Exception instance
            exc_traceback: Traceback object
        """
        # Don't track KeyboardInterrupt
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        error_tracker.track_exception(
            exc_type=exc_type,
            exc_value=exc_value,
            exc_traceback=exc_traceback,
            context={"source": "global_exception_handler"},
        )

        # Call the default exception handler
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = handle_exception
