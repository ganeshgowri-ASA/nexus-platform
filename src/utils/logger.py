"""
Logging configuration using loguru
"""
import sys
from loguru import logger
from src.config.settings import settings
from pathlib import Path

# Remove default logger
logger.remove()

# Add console handler
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL,
    colorize=True,
)

# Add file handler
log_file = Path(settings.LOG_FILE)
log_file.parent.mkdir(parents=True, exist_ok=True)

logger.add(
    settings.LOG_FILE,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level=settings.LOG_LEVEL,
    rotation="500 MB",
    retention="10 days",
    compression="zip",
)


def get_logger(name: str = __name__):
    """Get a logger instance"""
    return logger.bind(name=name)
