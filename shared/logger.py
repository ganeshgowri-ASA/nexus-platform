"""
NEXUS Platform - Logging Configuration

Centralized logging setup with structured logging support,
contextual information, and multiple output handlers.
"""

import logging
import sys
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

import orjson


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.

    Converts log records to JSON format with additional context
    and metadata for better log analysis and monitoring.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            str: JSON-formatted log string
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception information if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Add custom attributes
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
                "extra_fields",
            ]:
                log_data[key] = value

        return orjson.dumps(log_data).decode("utf-8")


class ColoredFormatter(logging.Formatter):
    """
    Colored console formatter for better readability.

    Adds colors to log levels and formats messages with
    timestamps and contextual information.
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with colors.

        Args:
            record: Log record to format

        Returns:
            str: Colored log string
        """
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        record.timestamp = f"\033[90m{timestamp}{self.RESET}"

        return super().format(record)


class ContextualLogger(logging.LoggerAdapter):
    """
    Logger adapter that adds contextual information to log records.

    Allows adding user_id, request_id, session_id, and other
    contextual data to all log messages.
    """

    def process(
        self, msg: str, kwargs: Dict[str, Any]
    ) -> tuple[str, Dict[str, Any]]:
        """
        Process log message with context.

        Args:
            msg: Log message
            kwargs: Additional keyword arguments

        Returns:
            tuple: Processed message and kwargs
        """
        # Add context to extra fields
        extra = kwargs.get("extra", {})
        extra.update(self.extra)
        kwargs["extra"] = extra

        return msg, kwargs


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    json_format: bool = False,
    enable_colors: bool = True,
) -> None:
    """
    Setup application logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for file logging
        json_format: Use JSON format for logs (useful for production)
        enable_colors: Enable colored output for console logs

    Example:
        >>> setup_logging(log_level="DEBUG", json_format=True)
    """
    # Create logs directory if needed
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))

    if json_format:
        console_formatter = JSONFormatter()
    elif enable_colors:
        console_formatter = ColoredFormatter(
            fmt="%(timestamp)s | %(levelname)s | %(name)s | %(message)s"
        )
    else:
        console_formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file

        # Always use JSON format for file logs
        file_formatter = JSONFormatter()
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


@lru_cache()
def get_logger(
    name: str,
    context: Optional[Dict[str, Any]] = None,
) -> logging.Logger | ContextualLogger:
    """
    Get a logger instance with optional context.

    Args:
        name: Logger name (typically __name__)
        context: Optional context dictionary to include in all log messages

    Returns:
        logging.Logger | ContextualLogger: Logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing event", extra={"event_id": "123"})

        >>> # With context
        >>> logger = get_logger(__name__, context={"user_id": "user123"})
        >>> logger.info("User action")  # Will include user_id in logs
    """
    logger = logging.getLogger(name)

    if context:
        return ContextualLogger(logger, context)

    return logger


def log_execution_time(logger: logging.Logger) -> Any:
    """
    Decorator to log function execution time.

    Args:
        logger: Logger instance to use

    Returns:
        Decorator function

    Example:
        >>> logger = get_logger(__name__)
        >>> @log_execution_time(logger)
        ... def slow_function():
        ...     time.sleep(2)
    """
    from functools import wraps
    from time import perf_counter

    def decorator(func: Any) -> Any:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = perf_counter()
            try:
                result = func(*args, **kwargs)
                end_time = perf_counter()
                execution_time = end_time - start_time

                logger.info(
                    f"{func.__name__} executed successfully",
                    extra={
                        "function": func.__name__,
                        "execution_time": f"{execution_time:.4f}s",
                    },
                )

                return result
            except Exception as e:
                end_time = perf_counter()
                execution_time = end_time - start_time

                logger.error(
                    f"{func.__name__} failed",
                    extra={
                        "function": func.__name__,
                        "execution_time": f"{execution_time:.4f}s",
                        "error": str(e),
                    },
                    exc_info=True,
                )
                raise

        return wrapper

    return decorator


class LogContext:
    """
    Context manager for adding temporary context to logs.

    Example:
        >>> logger = get_logger(__name__)
        >>> with LogContext(logger, user_id="user123", request_id="req456"):
        ...     logger.info("Processing request")  # Will include context
    """

    def __init__(self, logger: logging.Logger, **context: Any):
        """
        Initialize log context.

        Args:
            logger: Logger instance
            **context: Context key-value pairs
        """
        self.logger = logger
        self.context = context
        self.original_logger: Optional[logging.Logger] = None

    def __enter__(self) -> ContextualLogger:
        """Enter context and return contextual logger."""
        if isinstance(self.logger, ContextualLogger):
            # Merge with existing context
            merged_context = {**self.logger.extra, **self.context}
            return ContextualLogger(self.logger.logger, merged_context)
        else:
            return ContextualLogger(self.logger, self.context)

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context."""
        pass
