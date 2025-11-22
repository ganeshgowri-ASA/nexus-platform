"""Logging configuration."""
import sys
from loguru import logger
from shared.config import get_settings

settings = get_settings()


def setup_logger() -> None:
    """Configure logger."""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True,
    )
    logger.add(
        "logs/nexus_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        level=settings.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )


def get_logger(name: str):
    """Get a logger instance."""
    return logger.bind(name=name)
