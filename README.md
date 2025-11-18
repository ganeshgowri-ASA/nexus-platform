# NEXUS Platform

NEXUS: Unified AI-powered productivity platform with 24 integrated modules - Word, Excel, PPT, Projects, Email, Chat, Flowcharts, Analytics, Meetings & more. Built with Streamlit & Claude AI.

## Features

### Centralized Logging System

A comprehensive enterprise-grade logging system with:

- **Structured Logging** with `structlog` - JSON-formatted logs for easy parsing
- **Log Rotation** - Automatic rotation to manage disk space
- **Multiple Log Levels** - DEBUG, INFO, WARNING, ERROR, CRITICAL
- **ELK Stack Ready** - JSON format compatible with Elasticsearch, Logstash, Kibana
- **Request Logging** - Middleware for tracking HTTP requests in FastAPI and Streamlit
- **Error Tracking** - Comprehensive error tracking and monitoring
- **Audit Logging** - Security and compliance audit trails
- **Log Search API** - RESTful API for searching and analyzing logs

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd nexus-platform

# Install dependencies
pip install -r requirements.txt

# Or install with development dependencies
pip install -e ".[dev]"
```

### Basic Usage

```python
from pathlib import Path
from nexus.logging import setup_logging, get_logger, LogLevel
from nexus.logging.config import LogConfig

# Configure logging
config = LogConfig(
    log_dir=Path("logs"),
    log_level=LogLevel.INFO,
)
setup_logging(config)

# Get a logger
logger = get_logger(__name__)

# Log messages
logger.info("Application started", version="1.0.0")
logger.error("Something went wrong", error_code="E001")
```

### Run Log Search API

```bash
# Start the log search API
uvicorn examples.log_search_api_example:app --reload --port 8000

# Access the API
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

## Documentation

- **[Logging System Documentation](docs/LOGGING.md)** - Comprehensive guide to the logging system
- **[Log Search API Documentation](docs/API.md)** - API reference and examples

## Examples

The `examples/` directory contains working examples:

- `basic_logging_example.py` - Basic logging usage
- `audit_logging_example.py` - Audit logging examples
- `fastapi_logging_example.py` - FastAPI integration with request logging
- `log_search_api_example.py` - Log search API server

Run an example:

```bash
python examples/basic_logging_example.py
python examples/audit_logging_example.py
```

## Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

## Project Structure

```
nexus-platform/
├── src/nexus/              # Main source code
│   ├── logging/            # Logging system
│   │   ├── config.py       # Logging configuration
│   │   ├── audit.py        # Audit logging
│   │   └── error_tracker.py # Error tracking
│   ├── middleware/         # Middleware components
│   │   └── request_logging.py # Request logging
│   ├── api/                # API endpoints
│   │   └── log_search.py   # Log search API
│   └── models/             # Data models
│       └── log_models.py   # Log models
├── tests/                  # Test suite
│   └── logging/            # Logging tests
├── examples/               # Example applications
├── docs/                   # Documentation
├── logs/                   # Log files (created automatically)
├── requirements.txt        # Dependencies
└── pyproject.toml          # Project configuration
```

## Features in Detail

### Structured Logging

```python
logger.info(
    "user_login",
    user_id="user123",
    email="user@example.com",
    ip_address="192.168.1.1",
)
```

### Error Tracking

```python
from nexus.logging import ErrorTracker

error_tracker = ErrorTracker()
error_tracker.track_error(
    error=exception,
    context={"operation": "payment_processing"},
    user_id="user123",
    severity="error",
)
```

### Audit Logging

```python
from nexus.logging import AuditLogger

audit = AuditLogger()
audit.log_user_login(
    user_id="user123",
    user_email="user@example.com",
    ip_address="192.168.1.1",
)
```

### Request Logging

```python
from fastapi import FastAPI
from nexus.middleware import RequestLoggingMiddleware

app = FastAPI()
app.add_middleware(RequestLoggingMiddleware)
```

### Log Search API

```bash
# Search for errors
curl "http://localhost:8000/search?level=ERROR&limit=50"

# Get statistics
curl "http://localhost:8000/stats?hours=24"
```

## ELK Stack Integration

The logging system produces JSON-formatted logs ready for ELK stack integration:

```json
{
  "timestamp": "2025-01-18T10:30:45.123456",
  "level": "ERROR",
  "logger_name": "nexus.api",
  "event": "database_error",
  "app": "nexus",
  "request_id": "req-123",
  "user_id": "user456"
}
```

See [LOGGING.md](docs/LOGGING.md) for ELK stack configuration examples.

## Log Files

The system creates the following log files:

- `logs/nexus.json.log` - Main application logs (JSON format, ELK ready)
- `logs/nexus.error.log` - Error-level logs only
- `logs/nexus.audit.log` - Audit trail logs

All files support automatic rotation.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues and questions, please use the GitHub issue tracker.
