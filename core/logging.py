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
