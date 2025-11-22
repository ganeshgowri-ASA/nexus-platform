"""
Logging configuration for NEXUS platform.

This module sets up structured logging with support for both console and file outputs,
with JSON formatting for production environments.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict

import structlog
from structlog.types import EventDict, Processor

from backend.core.config import get_settings

settings = get_settings()


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Add application context to log events.

    Args:
        logger: Logger instance
        method_name: Method name
        event_dict: Event dictionary

    Returns:
        EventDict: Updated event dictionary
    """
    event_dict["app"] = settings.APP_NAME
    event_dict["version"] = settings.APP_VERSION
    event_dict["environment"] = settings.ENVIRONMENT
    return event_dict


def setup_logging() -> None:
    """
    Configure structured logging for the application.

    Sets up both structlog and standard logging with appropriate
    processors, formatters, and handlers based on configuration.
    """
    # Create logs directory if it doesn't exist
    log_file_path = Path(settings.LOG_FILE_PATH)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure standard logging
    timestamper = structlog.processors.TimeStamper(fmt="iso")

    # Shared processors for both development and production
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        add_app_context,
    ]

    if settings.LOG_FORMAT == "json" or settings.is_production:
        # JSON formatting for production
        processors = shared_processors + [
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Pretty formatting for development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    if settings.LOG_FORMAT == "json" or settings.is_production:
        # Use structlog processor for console
        console_handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                processor=structlog.processors.JSONRenderer(),
            )
        )
    else:
        # Use colored output for development
        console_handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                processor=structlog.dev.ConsoleRenderer(colors=True),
            )
        )

    root_logger.addHandler(console_handler)

    # File handler with rotation
    from logging.handlers import RotatingFileHandler

    file_handler = RotatingFileHandler(
        settings.LOG_FILE_PATH,
        maxBytes=settings.LOG_FILE_MAX_SIZE,
        backupCount=settings.LOG_FILE_BACKUP_COUNT,
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
        )
    )
    root_logger.addHandler(file_handler)

    # Configure third-party loggers
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        BoundLogger: Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("message", key="value")
    """
    return structlog.get_logger(name)


class LoggerMixin:
    """
    Mixin class to add logging capability to any class.

    Provides a logger property that can be used throughout the class.

    Example:
        >>> class MyService(LoggerMixin):
        ...     def process(self):
        ...         self.logger.info("processing started")
    """

    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """Get logger for this class."""
        return get_logger(self.__class__.__name__)


def log_function_call(func_name: str, **kwargs: Any) -> None:
    """
    Log a function call with parameters.

    Args:
        func_name: Name of the function
        **kwargs: Function parameters to log
    """
    logger = get_logger(func_name)
    logger.debug("function_call", function=func_name, parameters=kwargs)


def log_exception(
    exc: Exception, context: Dict[str, Any] | None = None, logger_name: str | None = None
) -> None:
    """
    Log an exception with context.

    Args:
        exc: Exception to log
        context: Additional context information
        logger_name: Logger name (defaults to exception type)
    """
    logger = get_logger(logger_name or exc.__class__.__name__)
    log_context = context or {}
    logger.exception(
        "exception_occurred",
        exc_type=exc.__class__.__name__,
        exc_message=str(exc),
        **log_context,
    )
