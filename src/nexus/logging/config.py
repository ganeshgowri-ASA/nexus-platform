"""Core logging configuration using structlog.

This module sets up centralized logging with:
- Structured JSON logs for ELK stack
- Console logs with color coding
- Log rotation
- Multiple log levels
- Context binding
"""

import logging
import logging.handlers
import sys
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import structlog
from structlog.types import EventDict, Processor


class LogLevel(str, Enum):
    """Log level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogConfig:
    """Logging configuration."""

    def __init__(
        self,
        log_dir: Path = Path("logs"),
        log_level: LogLevel = LogLevel.INFO,
        enable_json: bool = True,
        enable_console: bool = True,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 10,
        app_name: str = "nexus",
    ):
        """Initialize logging configuration.

        Args:
            log_dir: Directory for log files
            log_level: Minimum log level
            enable_json: Enable JSON formatted logs for ELK
            enable_console: Enable console output
            max_bytes: Max bytes per log file before rotation
            backup_count: Number of backup files to keep
            app_name: Application name for log context
        """
        self.log_dir = log_dir
        self.log_level = log_level
        self.enable_json = enable_json
        self.enable_console = enable_console
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.app_name = app_name

        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add application context to log entries.

    Args:
        logger: The logger instance
        method_name: The name of the method being called
        event_dict: The event dictionary

    Returns:
        Modified event dictionary with app context
    """
    event_dict["app"] = "nexus"
    event_dict["logger_name"] = logger.name
    return event_dict


def add_log_level(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add log level to event dictionary.

    Args:
        logger: The logger instance
        method_name: The name of the method being called
        event_dict: The event dictionary

    Returns:
        Modified event dictionary with log level
    """
    if method_name == "warn":
        method_name = "warning"
    event_dict["level"] = method_name.upper()
    return event_dict


def setup_logging(config: Optional[LogConfig] = None) -> None:
    """Set up centralized logging system.

    Args:
        config: Logging configuration (uses defaults if not provided)
    """
    if config is None:
        config = LogConfig()

    # Clear any existing handlers
    logging.root.handlers.clear()

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, config.log_level.value),
        stream=sys.stdout,
    )

    # Set up processors for structlog
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        add_log_level,
        add_app_context,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Configure JSON logs for ELK stack
    if config.enable_json:
        json_handler = logging.handlers.RotatingFileHandler(
            filename=config.log_dir / f"{config.app_name}.json.log",
            maxBytes=config.max_bytes,
            backupCount=config.backup_count,
            encoding="utf-8",
        )
        json_handler.setLevel(getattr(logging, config.log_level.value))

        # JSON formatter for ELK
        json_formatter = logging.Formatter(
            "%(message)s"
        )  # structlog will handle JSON formatting
        json_handler.setFormatter(json_formatter)
        logging.root.addHandler(json_handler)

    # Configure console logs with color
    if config.enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, config.log_level.value))
        logging.root.addHandler(console_handler)

    # Configure separate error log file
    error_handler = logging.handlers.RotatingFileHandler(
        filename=config.log_dir / f"{config.app_name}.error.log",
        maxBytes=config.max_bytes,
        backupCount=config.backup_count,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    logging.root.addHandler(error_handler)

    # Configure audit log file
    audit_handler = logging.handlers.RotatingFileHandler(
        filename=config.log_dir / f"{config.app_name}.audit.log",
        maxBytes=config.max_bytes,
        backupCount=config.backup_count,
        encoding="utf-8",
    )
    audit_handler.setLevel(logging.INFO)
    audit_logger = logging.getLogger("nexus.audit")
    audit_logger.addHandler(audit_handler)
    audit_logger.propagate = False

    # Configure structlog
    if config.enable_json:
        processors.append(structlog.processors.JSONRenderer())
    else:
        if config.enable_console:
            processors.append(structlog.dev.ConsoleRenderer(colors=True))
        else:
            processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """Get a logger instance.

    Args:
        name: Logger name (uses calling module if not provided)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)
