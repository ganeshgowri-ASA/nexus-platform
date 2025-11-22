"""Basic logging example for NEXUS platform.

This example demonstrates:
- Setting up logging
- Using different log levels
- Adding context to logs
- Error tracking
"""

from pathlib import Path

from nexus.logging import get_logger, setup_logging, LogLevel, ErrorTracker
from nexus.logging.config import LogConfig


def main() -> None:
    """Run basic logging example."""
    # Set up logging with custom configuration
    config = LogConfig(
        log_dir=Path("logs"),
        log_level=LogLevel.DEBUG,
        enable_json=True,
        enable_console=True,
    )
    setup_logging(config)

    # Get a logger instance
    logger = get_logger("example.basic")

    # Log at different levels
    logger.debug("This is a debug message", module="basic_example")
    logger.info("Application started", version="1.0.0")
    logger.warning("This is a warning", reason="demonstration")
    logger.error("This is an error", error_code="E001")

    # Log with structured data
    logger.info(
        "user_action",
        user_id="user123",
        action="login",
        ip_address="192.168.1.1",
        success=True,
    )

    # Log with nested context
    logger.info(
        "processing_complete",
        task="data_import",
        stats={
            "records_processed": 1000,
            "errors": 5,
            "duration_seconds": 45.2,
        },
    )

    # Error tracking example
    error_tracker = ErrorTracker()

    try:
        # Simulate an error
        result = 10 / 0
    except Exception as e:
        error_tracker.track_error(
            error=e,
            context={"operation": "division", "values": {"numerator": 10, "denominator": 0}},
            severity="error",
        )

    # Track HTTP error
    error_tracker.track_http_error(
        status_code=404,
        method="GET",
        url="/api/users/999",
        error_message="User not found",
        request_id="req-12345",
    )

    logger.info("Example completed successfully")


if __name__ == "__main__":
    main()
