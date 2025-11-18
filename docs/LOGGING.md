# NEXUS Logging System Documentation

## Overview

The NEXUS platform includes a comprehensive centralized logging system built on `structlog` with the following features:

- **Structured Logging**: JSON-formatted logs for easy parsing and analysis
- **Log Rotation**: Automatic log file rotation to manage disk space
- **Multiple Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **ELK Stack Ready**: JSON format compatible with Elasticsearch, Logstash, Kibana
- **Request Logging**: Middleware for tracking HTTP requests
- **Error Tracking**: Comprehensive error tracking and monitoring
- **Audit Logging**: Security and compliance audit trails
- **Log Search API**: RESTful API for searching and analyzing logs

## Quick Start

### Basic Setup

```python
from pathlib import Path
from nexus.logging import setup_logging, get_logger, LogLevel
from nexus.logging.config import LogConfig

# Configure logging
config = LogConfig(
    log_dir=Path("logs"),
    log_level=LogLevel.INFO,
    enable_json=True,
    enable_console=True,
)
setup_logging(config)

# Get a logger
logger = get_logger(__name__)

# Log messages
logger.info("Application started", version="1.0.0")
logger.error("Something went wrong", error_code="E001")
```

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or with pip
pip install structlog python-json-logger fastapi uvicorn
```

## Configuration

### LogConfig Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `log_dir` | Path | `Path("logs")` | Directory for log files |
| `log_level` | LogLevel | `LogLevel.INFO` | Minimum log level |
| `enable_json` | bool | `True` | Enable JSON formatted logs |
| `enable_console` | bool | `True` | Enable console output |
| `max_bytes` | int | `10485760` (10MB) | Max bytes per log file |
| `backup_count` | int | `10` | Number of backup files |
| `app_name` | str | `"nexus"` | Application name |

### Example Configuration

```python
from nexus.logging.config import LogConfig, LogLevel

# Production configuration
prod_config = LogConfig(
    log_dir=Path("/var/log/nexus"),
    log_level=LogLevel.WARNING,
    enable_json=True,
    enable_console=False,
    max_bytes=50 * 1024 * 1024,  # 50MB
    backup_count=20,
)

# Development configuration
dev_config = LogConfig(
    log_dir=Path("./logs"),
    log_level=LogLevel.DEBUG,
    enable_json=True,
    enable_console=True,
)
```

## Log Files

The logging system creates several log files:

- `nexus.json.log` - Main application logs in JSON format (ELK ready)
- `nexus.error.log` - Error-level and above logs only
- `nexus.audit.log` - Audit trail for security and compliance

All log files support automatic rotation based on size.

## Structured Logging

### Basic Usage

```python
logger = get_logger("myapp")

# Simple log message
logger.info("User logged in")

# Structured log with context
logger.info(
    "user_login",
    user_id="user123",
    email="user@example.com",
    ip_address="192.168.1.1",
    timestamp=datetime.utcnow().isoformat(),
)
```

### Log Levels

```python
logger.debug("Detailed information", var=value)
logger.info("General information", status="ok")
logger.warning("Warning message", reason="high_load")
logger.error("Error occurred", error_code="E001")
logger.critical("Critical failure", component="database")
```

## Error Tracking

### Basic Error Tracking

```python
from nexus.logging import ErrorTracker

error_tracker = ErrorTracker()

try:
    result = risky_operation()
except Exception as e:
    error_tracker.track_error(
        error=e,
        context={"operation": "risky_operation", "params": params},
        user_id="user123",
        request_id="req-456",
        severity="error",
    )
```

### HTTP Error Tracking

```python
error_tracker.track_http_error(
    status_code=404,
    method="GET",
    url="/api/users/999",
    error_message="User not found",
    user_id="user123",
    request_id="req-789",
)
```

### Validation Error Tracking

```python
error_tracker.track_validation_error(
    field="email",
    value="invalid-email",
    expected="valid email format",
    user_id="user123",
)
```

### Database Error Tracking

```python
error_tracker.track_database_error(
    operation="insert",
    table="users",
    error=db_error,
    query="INSERT INTO users (name, email) VALUES (?, ?)",
)
```

## Audit Logging

### User Actions

```python
from nexus.logging import AuditLogger

audit = AuditLogger()

# User login
audit.log_user_login(
    user_id="user123",
    user_email="user@example.com",
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0...",
    status="success",
)

# User logout
audit.log_user_logout(
    user_id="user123",
    user_email="user@example.com",
)
```

### Data Access and Modification

```python
# Data access
audit.log_data_access(
    user_id="user123",
    resource_type="document",
    resource_id="doc456",
    action="read",
)

# Data modification
audit.log_data_modification(
    user_id="user123",
    resource_type="document",
    resource_id="doc456",
    action="update",
    changes={"title": "New Title", "status": "published"},
)
```

### Security Events

```python
audit.log_security_event(
    event_description="Multiple failed login attempts",
    severity="high",
    user_id="user123",
    ip_address="192.168.1.1",
    details={"attempt_count": 5},
)
```

### Configuration Changes

```python
audit.log_config_change(
    user_id="admin001",
    config_key="max_file_size",
    old_value=10,
    new_value=20,
)
```

## Request Logging Middleware

### FastAPI Integration

```python
from fastapi import FastAPI
from nexus.middleware import RequestLoggingMiddleware

app = FastAPI()

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Skip certain paths
app.add_middleware(
    RequestLoggingMiddleware,
    skip_paths=["/health", "/metrics", "/favicon.ico"],
)
```

### Streamlit Integration

```python
from nexus.middleware.request_logging import StreamlitRequestLogger

streamlit_logger = StreamlitRequestLogger()

# Log page view
streamlit_logger.log_page_view(
    page_name="dashboard",
    user_id="user123",
    session_id="session-456",
)

# Log user interaction
streamlit_logger.log_interaction(
    interaction_type="button_click",
    component="export_button",
    user_id="user123",
    session_id="session-456",
)
```

## Log Search API

### Starting the API

```python
from pathlib import Path
from nexus.api import create_log_search_api

# Create the API
app = create_log_search_api(log_dir=Path("logs"))

# Run with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Or from command line:

```bash
uvicorn examples.log_search_api_example:app --reload --port 8000
```

### API Endpoints

#### GET /search

Search logs with query parameters.

**Query Parameters:**
- `start_time` (datetime): Start of time range
- `end_time` (datetime): End of time range
- `level` (string): Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `logger_name` (string): Filter by logger name
- `request_id` (string): Filter by request ID
- `user_id` (string): Filter by user ID
- `search_text` (string): Search in log messages
- `error_type` (string): Filter by error type
- `limit` (int): Maximum results (1-1000, default: 100)
- `offset` (int): Offset for pagination (default: 0)
- `sort_order` (string): Sort order - 'asc' or 'desc' (default: 'desc')

**Example:**

```bash
# Get all errors
curl "http://localhost:8000/search?level=ERROR&limit=50"

# Search for specific user
curl "http://localhost:8000/search?user_id=user123"

# Search text in logs
curl "http://localhost:8000/search?search_text=login&limit=20"

# Time range search
curl "http://localhost:8000/search?start_time=2025-01-01T00:00:00&end_time=2025-01-02T00:00:00"
```

#### POST /search

Search logs with JSON body.

**Request Body:**

```json
{
  "level": "ERROR",
  "user_id": "user123",
  "limit": 50,
  "offset": 0,
  "sort_order": "desc"
}
```

**Example:**

```bash
curl -X POST http://localhost:8000/search \
     -H "Content-Type: application/json" \
     -d '{
       "level": "ERROR",
       "search_text": "database",
       "limit": 100
     }'
```

#### GET /stats

Get log statistics.

**Query Parameters:**
- `hours` (int): Number of hours to analyze (1-168, default: 24)

**Example:**

```bash
# Get stats for last 24 hours
curl "http://localhost:8000/stats"

# Get stats for last week
curl "http://localhost:8000/stats?hours=168"
```

**Response:**

```json
{
  "total_logs": 1523,
  "error_count": 45,
  "warning_count": 123,
  "info_count": 1345,
  "debug_count": 10,
  "critical_count": 0,
  "time_range": {
    "start": "2025-01-17T00:00:00",
    "end": "2025-01-18T00:00:00"
  },
  "top_errors": [
    {"error_type": "ValueError", "count": 15},
    {"error_type": "ConnectionError", "count": 8}
  ],
  "logs_per_hour": [
    {"hour": "2025-01-17 00:00", "count": 45},
    {"hour": "2025-01-17 01:00", "count": 38}
  ]
}
```

## ELK Stack Integration

### JSON Log Format

Logs are automatically formatted as JSON for ELK stack compatibility:

```json
{
  "timestamp": "2025-01-18T10:30:45.123456",
  "level": "INFO",
  "logger_name": "nexus.api",
  "event": "user_login",
  "app": "nexus",
  "user_id": "user123",
  "ip_address": "192.168.1.1",
  "request_id": "req-abc-123"
}
```

### Logstash Configuration

Example Logstash configuration:

```ruby
input {
  file {
    path => "/var/log/nexus/nexus.json.log"
    codec => json
    type => "nexus"
  }
}

filter {
  if [type] == "nexus" {
    date {
      match => ["timestamp", "ISO8601"]
      target => "@timestamp"
    }
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "nexus-logs-%{+YYYY.MM.dd}"
  }
}
```

### Elasticsearch Index Template

```json
{
  "index_patterns": ["nexus-logs-*"],
  "mappings": {
    "properties": {
      "timestamp": {"type": "date"},
      "level": {"type": "keyword"},
      "logger_name": {"type": "keyword"},
      "event": {"type": "text"},
      "app": {"type": "keyword"},
      "user_id": {"type": "keyword"},
      "request_id": {"type": "keyword"},
      "error_type": {"type": "keyword"}
    }
  }
}
```

## Best Practices

### 1. Use Structured Logging

Always include structured data:

```python
# Good
logger.info("order_created", order_id=order.id, user_id=user.id, amount=100.50)

# Bad
logger.info(f"Order {order.id} created by user {user.id} for ${100.50}")
```

### 2. Include Request Context

Use request IDs for correlation:

```python
logger.info("processing_request", request_id=request_id, user_id=user_id)
```

### 3. Choose Appropriate Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages for potentially harmful situations
- **ERROR**: Error events that might still allow the application to continue
- **CRITICAL**: Very severe error events that might cause the application to abort

### 4. Audit Sensitive Operations

Always log security-relevant events:

```python
audit.log_user_login(user_id, user_email, ip_address)
audit.log_data_access(user_id, resource_type, resource_id)
audit.log_security_event("unauthorized_access_attempt", severity="high")
```

### 5. Track Errors with Context

Include relevant context when tracking errors:

```python
error_tracker.track_error(
    error=e,
    context={
        "operation": "process_payment",
        "order_id": order_id,
        "amount": amount,
    },
    user_id=user_id,
    request_id=request_id,
)
```

## Testing

Run the test suite:

```bash
# Install dev dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/logging/test_config.py
```

## Examples

See the `examples/` directory for complete working examples:

- `basic_logging_example.py` - Basic logging usage
- `audit_logging_example.py` - Audit logging examples
- `fastapi_logging_example.py` - FastAPI integration
- `log_search_api_example.py` - Log search API

Run an example:

```bash
python examples/basic_logging_example.py
python examples/audit_logging_example.py
```

## Troubleshooting

### Logs not appearing

1. Check log directory permissions
2. Verify logging is configured: `setup_logging(config)`
3. Check log level is appropriate for the messages

### Log files growing too large

Adjust rotation settings:

```python
config = LogConfig(
    max_bytes=5 * 1024 * 1024,  # 5MB
    backup_count=20,
)
```

### JSON parsing errors in ELK

Ensure all log entries are valid JSON. The system handles this automatically.

## License

MIT License - See LICENSE file for details
