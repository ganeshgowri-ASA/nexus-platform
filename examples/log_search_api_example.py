"""Log search API example for NEXUS platform.

This example demonstrates:
- Running the log search API
- Searching logs via API endpoints
- Getting log statistics
"""

from pathlib import Path

from nexus.api import create_log_search_api
from nexus.logging import setup_logging, get_logger, LogLevel
from nexus.logging.config import LogConfig


def main() -> None:
    """Run log search API example."""
    # Set up logging
    config = LogConfig(
        log_dir=Path("logs"),
        log_level=LogLevel.INFO,
    )
    setup_logging(config)

    # Generate some sample logs
    logger = get_logger("example.search")

    logger.info("API server starting")
    logger.info("user_action", user_id="user1", action="login")
    logger.warning("high_memory_usage", memory_percent=85)
    logger.error("database_connection_failed", host="db.example.com")
    logger.info("user_action", user_id="user2", action="create_document")

    # Create and run the log search API
    app = create_log_search_api(log_dir=Path("logs"))

    print("""
Log Search API is ready to start!

To run the API server:
    uvicorn examples.log_search_api_example:app --reload

Available endpoints:
    - GET  /              - API info
    - GET  /health        - Health check
    - GET  /search        - Search logs (GET)
    - POST /search        - Search logs (POST)
    - GET  /stats         - Log statistics

Example queries:
    # Get all logs
    curl http://localhost:8000/search

    # Search for errors
    curl "http://localhost:8000/search?level=ERROR"

    # Search by user ID
    curl "http://localhost:8000/search?user_id=user1"

    # Search with text
    curl "http://localhost:8000/search?search_text=login"

    # Get statistics
    curl http://localhost:8000/stats

    # Search with POST
    curl -X POST http://localhost:8000/search \\
         -H "Content-Type: application/json" \\
         -d '{"level": "ERROR", "limit": 10}'
""")


# Export app for uvicorn
if __name__ != "__main__":
    # Set up logging when imported by uvicorn
    config = LogConfig(
        log_dir=Path("logs"),
        log_level=LogLevel.INFO,
    )
    setup_logging(config)

app = create_log_search_api(log_dir=Path("logs"))


if __name__ == "__main__":
    main()
