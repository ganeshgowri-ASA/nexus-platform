"""
Logging configuration and utilities.

Provides structured logging with JSON support, log rotation,
and integration with various logging frameworks.
"""

import sys
from pathlib import Path
from typing import Any, Dict

from loguru import logger

from .settings import get_settings


def setup_logging() -> None:
    """
    Configure application logging.

    Sets up loguru with appropriate handlers, formatters,
    and log levels based on application settings.
    """
    settings = get_settings()

    # Remove default handler
    logger.remove()

    # Create logs directory if it doesn't exist
    log_file_path = Path(settings.log_file)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Console handler
    if settings.log_format == "json":
        console_format = (
            "{{\"time\": \"{time:YYYY-MM-DD HH:mm:ss}\", "
            "\"level\": \"{level}\", "
            "\"module\": \"{name}\", "
            "\"function\": \"{function}\", "
            "\"line\": {line}, "
            "\"message\": \"{message}\"}}\n"
        )
    else:
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>\n"
        )

    logger.add(
        sys.stdout,
        format=console_format,
        level=settings.log_level,
        colorize=settings.log_format != "json",
    )

    # File handler with rotation
    if settings.log_format == "json":
        file_format = (
            "{{\"time\": \"{time:YYYY-MM-DD HH:mm:ss}\", "
            "\"level\": \"{level}\", "
            "\"module\": \"{name}\", "
            "\"function\": \"{function}\", "
            "\"line\": {line}, "
            "\"message\": \"{message}\"}}\n"
        )
    else:
        file_format = (
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{name}:{function}:{line} - "
            "{message}\n"
        )

    logger.add(
        settings.log_file,
        format=file_format,
        level=settings.log_level,
        rotation="100 MB",
        retention="30 days",
        compression="gz",
        enqueue=True,
    )

    # Log startup message
    logger.info(
        f"Logging initialized - Level: {settings.log_level}, Format: {settings.log_format}"
    )


def log_function_call(func_name: str, **kwargs: Any) -> None:
    """
    Log function call with parameters.

    Args:
        func_name: Name of the function
        **kwargs: Function parameters to log
    """
    logger.debug(f"Calling {func_name} with params: {kwargs}")


def log_error(error: Exception, context: Dict[str, Any]) -> None:
    """
    Log error with context.

    Args:
        error: Exception that occurred
        context: Additional context information
    """
    logger.error(
        f"Error occurred: {type(error).__name__}: {str(error)} | Context: {context}"
    )


def log_performance(operation: str, duration: float, **metadata: Any) -> None:
    """
    Log performance metrics.

    Args:
        operation: Name of the operation
        duration: Duration in seconds
        **metadata: Additional metadata
    """
    logger.info(
        f"Performance - {operation}: {duration:.3f}s | Metadata: {metadata}"
    )
