"""
Logging Configuration

Centralized logging setup for the NEXUS platform using structlog.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict
import structlog
from config.settings import settings


def setup_logging() -> None:
    """
    Configure application-wide logging.

    Sets up structured logging with JSON output for production
    and pretty console output for development.
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )

    # Configure structlog
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.LOG_FORMAT == "json":
        # JSON logging for production
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Pretty console logging for development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a logger instance for the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing translation", user_id=123, language="es")
    """
    return structlog.get_logger(name)


class LoggerMixin:
    """
    Mixin class to add logging capability to any class.

    Example:
        >>> class MyService(LoggerMixin):
        ...     def process(self):
        ...         self.logger.info("Processing...")
    """

    @property
    def logger(self) -> structlog.BoundLogger:
        """Get logger instance for this class."""
        if not hasattr(self, "_logger"):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger


def log_function_call(func):
    """
    Decorator to log function calls with arguments and results.

    Args:
        func: Function to decorate

    Returns:
        Decorated function

    Example:
        >>> @log_function_call
        ... def translate(text: str, target_lang: str):
        ...     return "translated text"
    """
    logger = get_logger(func.__module__)

    def wrapper(*args, **kwargs):
        logger.debug(
            f"Calling {func.__name__}",
            args=args,
            kwargs=kwargs,
        )
        try:
            result = func(*args, **kwargs)
            logger.debug(
                f"Completed {func.__name__}",
                result=result,
            )
            return result
        except Exception as e:
            logger.error(
                f"Error in {func.__name__}",
                error=str(e),
                exc_info=True,
            )
            raise

    return wrapper


# Initialize logging when module is imported
setup_logging()
