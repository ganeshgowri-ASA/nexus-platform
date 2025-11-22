"""
<<<<<<< HEAD
Logging configuration for NEXUS Platform.

This module sets up structured logging using structlog for better log management
and debugging capabilities.
"""
import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from config.settings import settings


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Add application context to log entries.

    Args:
        logger: Logger instance
        method_name: Method name
        event_dict: Event dictionary

    Returns:
        Updated event dictionary with application context
    """
    event_dict["app"] = settings.app_name
    event_dict["environment"] = settings.environment
    return event_dict


def configure_logging() -> None:
    """
    Configure structured logging for the application.

    Sets up structlog with appropriate processors and formatters based on
    the environment (JSON for production, console-friendly for development).
    """
    # Determine log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Silence noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # Configure structlog processors
    processors: list[Processor] = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        add_app_context,
    ]

    # Use JSON formatting in production, console-friendly in development
    if settings.environment == "production":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Campaign created", campaign_id="123", user_id="456")
    """
    return structlog.get_logger(name)


# Initialize logging on module import
configure_logging()
=======
Logging configuration for NEXUS platform.

This module provides centralized logging configuration with support for
file logging, console logging, and structured log formatting.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

from .settings import settings

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)


def setup_logging(
    name: Optional[str] = None,
    level: Optional[str] = None,
) -> logging.Logger:
    """
    Set up logging configuration.

    Args:
        name: Logger name (default: root logger).
        level: Log level (default: from settings).

    Returns:
        Configured logger instance.
    """
    level = level or settings.log_level
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_formatter = logging.Formatter(
        fmt=settings.log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (rotating)
    if name:
        log_file = LOGS_DIR / f"{name}.log"
    else:
        log_file = LOGS_DIR / "nexus.log"

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10485760,  # 10MB
        backupCount=5,
    )
    file_handler.setLevel(getattr(logging, level.upper()))
    file_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with the given name.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Logger instance.

    Example:
        ```python
        from config.logging_config import get_logger
        logger = get_logger(__name__)
        logger.info("Application started")
        ```
    """
    return setup_logging(name)


# Set up root logger
root_logger = setup_logging()
root_logger.info("Logging configured successfully")
>>>>>>> origin/claude/build-advertising-lead-generation-01Skr8pwxfdGAtz4wHoobrUL
