"""Logging configuration for A/B testing module."""

import sys
from pathlib import Path

from loguru import logger

from modules.ab_testing.config import get_settings


def setup_logging() -> None:
    """
    Configure logging for the application.

    Sets up structured logging with rotation and different log levels
    for different environments.
    """
    settings = get_settings()

    # Remove default handler
    logger.remove()

    # Console logging
    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        level=settings.log_level,
        colorize=True,
    )

    # File logging (if production)
    if settings.is_production:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # General logs
        logger.add(
            log_dir / "ab_testing.log",
            rotation="500 MB",
            retention="10 days",
            compression="zip",
            level=settings.log_level,
            format=(
                "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
                "{name}:{function}:{line} | {message}"
            ),
        )

        # Error logs
        logger.add(
            log_dir / "errors.log",
            rotation="100 MB",
            retention="30 days",
            compression="zip",
            level="ERROR",
            format=(
                "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
                "{name}:{function}:{line} | {message} | {extra}"
            ),
        )

    logger.info(f"Logging configured for {settings.environment} environment")
