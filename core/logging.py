<<<<<<< HEAD
"""Logging configuration for NEXUS Platform."""

import sys
from pathlib import Path
from loguru import logger
from core.config import settings


def setup_logging():
    """Configure logging for the application."""

    # Remove default handler
    logger.remove()

    # Console handler with custom format
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True
    )

    # File handler for all logs
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logger.add(
        log_dir / "nexus_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="DEBUG",
        rotation="00:00",  # Rotate at midnight
        retention="30 days",  # Keep logs for 30 days
        compression="zip",  # Compress old logs
        enqueue=True  # Thread-safe
    )

    # Separate file handler for errors
    logger.add(
        log_dir / "nexus_errors_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="ERROR",
        rotation="00:00",
        retention="90 days",  # Keep error logs longer
        compression="zip",
        enqueue=True
    )

    # Batch processing specific logs
    logger.add(
        log_dir / "batch_processing_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="DEBUG",
        rotation="00:00",
        retention="60 days",
        compression="zip",
        filter=lambda record: "batch_processing" in record["name"],
        enqueue=True
    )

    logger.info("Logging configured successfully")


# Initialize logging when module is imported
setup_logging()
=======
"""
Logging configuration for the NEXUS platform.
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class Logger:
    """Custom logger for NEXUS platform."""

    def __init__(
        self,
        name: str,
        log_file: Optional[Path] = None,
        level: int = logging.INFO,
    ):
        """
        Initialize logger.

        Args:
            name: Logger name
            log_file: Optional log file path
            level: Logging level
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Prevent duplicate handlers
        if self.logger.handlers:
            return

        # Create formatters
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File handler (optional)
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)

    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)

    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)

    def error(self, message: str):
        """Log error message."""
        self.logger.error(message)

    def critical(self, message: str):
        """Log critical message."""
        self.logger.critical(message)

    def exception(self, message: str):
        """Log exception with traceback."""
        self.logger.exception(message)


def get_logger(name: str, log_file: Optional[str] = None) -> Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name
        log_file: Optional log file name

    Returns:
        Logger instance
    """
    if log_file:
        log_path = Path("logs") / log_file
    else:
        log_path = None

    return Logger(name, log_path)


# Default application logger
app_logger = get_logger("nexus", "app.log")
>>>>>>> origin/claude/word-editor-module-01PPyUEeNUgZmU4swtfxgoCB
