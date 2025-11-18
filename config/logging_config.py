"""
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
