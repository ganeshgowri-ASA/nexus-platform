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
