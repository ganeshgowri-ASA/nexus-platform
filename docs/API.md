# NEXUS Log Search API Documentation

## Overview

The NEXUS Log Search API provides RESTful endpoints for searching, filtering, and analyzing application logs. It's built with FastAPI and provides comprehensive log querying capabilities.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. In production, implement appropriate authentication mechanisms (API keys, OAuth, etc.).

## Endpoints

### 1. Root Endpoint

Get API information.

**Endpoint:** `GET /`

**Response:**

```json
{
  "service": "NEXUS Log Search API",
  "version": "1.0.0",
  "status": "running"
}
```

### 2. Health Check

Check API health status.

**Endpoint:** `GET /health`

**Response:**

```json
{
  "status": "healthy"
}
```

### 3. Search Logs (GET)

Search logs using query parameters.

**Endpoint:** `GET /search`

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start_time | datetime | No | - | Start of time range (ISO 8601) |
| end_time | datetime | No | - | End of time range (ISO 8601) |
| level | string | No | - | Log level filter |
| logger_name | string | No | - | Logger name filter |
| request_id | string | No | - | Request ID filter |
| user_id | string | No | - | User ID filter |
| search_text | string | No | - | Text search in messages |
| error_type | string | No | - | Error type filter |
| limit | int | No | 100 | Max results (1-1000) |
| offset | int | No | 0 | Pagination offset |
| sort_order | string | No | desc | Sort order (asc/desc) |

**Examples:**

```bash
# Get all logs
curl "http://localhost:8000/search"

# Get errors only
curl "http://localhost:8000/search?level=ERROR"

# Search for specific user
curl "http://localhost:8000/search?user_id=user123&limit=50"

# Time range search
curl "http://localhost:8000/search?start_time=2025-01-18T00:00:00&end_time=2025-01-18T23:59:59"

# Combined filters
curl "http://localhost:8000/search?level=ERROR&search_text=database&limit=20"
```

**Response:**

```json
{
  "logs": [
    {
      "timestamp": "2025-01-18T10:30:45.123456",
      "level": "ERROR",
      "logger_name": "nexus.database",
      "message": "database_connection_failed",
      "app": "nexus",
      "request_id": "req-123",
      "user_id": "user456",
      "error_type": "ConnectionError",
      "error_message": "Failed to connect to database",
      "context": {
        "host": "db.example.com",
        "port": 5432
      }
    }
  ],
  "total_count": 1,
  "offset": 0,
  "limit": 100,
  "has_more": false
}
```

### 4. Search Logs (POST)

Search logs using JSON request body.

**Endpoint:** `POST /search`

**Request Body:**

```json
{
  "start_time": "2025-01-18T00:00:00",
  "end_time": "2025-01-18T23:59:59",
  "level": "ERROR",
  "logger_name": "nexus.api",
  "request_id": "req-123",
  "user_id": "user456",
  "search_text": "failed",
  "error_type": "ValueError",
  "limit": 50,
  "offset": 0,
  "sort_order": "desc"
}
```

All fields are optional.

**Examples:**

```bash
# Search for errors
curl -X POST http://localhost:8000/search \
     -H "Content-Type: application/json" \
     -d '{"level": "ERROR", "limit": 100}'

# Search with multiple filters
curl -X POST http://localhost:8000/search \
     -H "Content-Type: application/json" \
     -d '{
       "level": "ERROR",
       "search_text": "database",
       "user_id": "user123",
       "limit": 50
     }'

# Time range search
curl -X POST http://localhost:8000/search \
     -H "Content-Type: application/json" \
     -d '{
       "start_time": "2025-01-18T00:00:00",
       "end_time": "2025-01-18T12:00:00",
       "limit": 100
     }'
```

**Response:** Same as GET /search

### 5. Log Statistics

Get aggregated log statistics.

**Endpoint:** `GET /stats`

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| hours | int | No | 24 | Hours to analyze (1-168) |

**Examples:**

```bash
# Get stats for last 24 hours
curl "http://localhost:8000/stats"

# Get stats for last 7 days
curl "http://localhost:8000/stats?hours=168"

# Get stats for last hour
curl "http://localhost:8000/stats?hours=1"
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
    "start": "2025-01-17T10:00:00",
    "end": "2025-01-18T10:00:00"
  },
  "top_errors": [
    {
      "error_type": "ValueError",
      "count": 15
    },
    {
      "error_type": "ConnectionError",
      "count": 8
    },
    {
      "error_type": "TimeoutError",
      "count": 5
    }
  ],
  "logs_per_hour": [
    {
      "hour": "2025-01-17 10:00",
      "count": 45
    },
    {
      "hour": "2025-01-17 11:00",
      "count": 52
    }
  ]
}
```

## Data Models

### LogEntry

```python
{
  "timestamp": "datetime",           # Log timestamp (ISO 8601)
  "level": "string",                 # Log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)
  "logger_name": "string",           # Logger name
  "message": "string",               # Log message
  "app": "string",                   # Application name (default: "nexus")
  "request_id": "string | null",     # Request ID for correlation
  "user_id": "string | null",        # User identifier
  "error_type": "string | null",     # Error type if applicable
  "error_message": "string | null",  # Error message
  "traceback": "string | null",      # Stack trace for errors
  "context": "object | null",        # Additional context data
  "extra": "object | null"           # Extra fields
}
```

### LogSearchQuery

```python
{
  "start_time": "datetime | null",   # Start of time range
  "end_time": "datetime | null",     # End of time range
  "level": "string | null",          # Log level filter
  "logger_name": "string | null",    # Logger name filter
  "request_id": "string | null",     # Request ID filter
  "user_id": "string | null",        # User ID filter
  "search_text": "string | null",    # Text search
  "error_type": "string | null",     # Error type filter
  "limit": "int",                    # Max results (1-1000, default: 100)
  "offset": "int",                   # Pagination offset (default: 0)
  "sort_order": "string"             # Sort order (asc/desc, default: desc)
}
```

### LogSearchResponse

```python
{
  "logs": [LogEntry],                # Array of log entries
  "total_count": "int",              # Total matching logs
  "offset": "int",                   # Current offset
  "limit": "int",                    # Results per page
  "has_more": "bool"                 # More results available
}
```

### LogStats

```python
{
  "total_logs": "int",               # Total log count
  "error_count": "int",              # ERROR level count
  "warning_count": "int",            # WARNING level count
  "info_count": "int",               # INFO level count
  "debug_count": "int",              # DEBUG level count
  "critical_count": "int",           # CRITICAL level count
  "time_range": {
    "start": "datetime",             # Analysis start time
    "end": "datetime"                # Analysis end time
  },
  "top_errors": [
    {
      "error_type": "string",        # Error type
      "count": "int"                 # Occurrence count
    }
  ],
  "logs_per_hour": [
    {
      "hour": "string",              # Hour timestamp
      "count": "int"                 # Log count for hour
    }
  ]
}
```

## Error Responses

All endpoints may return these error responses:

### 400 Bad Request

Invalid request parameters.

```json
{
  "detail": "Invalid parameter value"
}
```

### 404 Not Found

Endpoint not found.

```json
{
  "detail": "Not Found"
}
```

### 422 Validation Error

Request validation failed.

```json
{
  "detail": [
    {
      "loc": ["query", "limit"],
      "msg": "ensure this value is less than or equal to 1000",
      "type": "value_error"
    }
  ]
}
```

### 500 Internal Server Error

Server error occurred.

```json
{
  "detail": "Internal server error message"
}
```

## Pagination

Use `limit` and `offset` for pagination:

```bash
# First page (items 0-99)
curl "http://localhost:8000/search?limit=100&offset=0"

# Second page (items 100-199)
curl "http://localhost:8000/search?limit=100&offset=100"

# Third page (items 200-299)
curl "http://localhost:8000/search?limit=100&offset=200"
```

Check `has_more` in the response to determine if more results are available.

## Rate Limiting

Currently, no rate limiting is implemented. In production, implement appropriate rate limiting based on your requirements.

## CORS

Configure CORS for cross-origin requests if needed:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Interactive API Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Client Examples

### Python

```python
import requests

# Search for errors
response = requests.post(
    "http://localhost:8000/search",
    json={
        "level": "ERROR",
        "limit": 50,
    }
)
logs = response.json()

# Get statistics
response = requests.get("http://localhost:8000/stats?hours=24")
stats = response.json()
print(f"Total errors: {stats['error_count']}")
```

### JavaScript

```javascript
// Search for errors
fetch('http://localhost:8000/search', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    level: 'ERROR',
    limit: 50,
  }),
})
  .then(response => response.json())
  .then(data => console.log(data.logs));

// Get statistics
fetch('http://localhost:8000/stats?hours=24')
  .then(response => response.json())
  .then(stats => console.log(`Total errors: ${stats.error_count}`));
```

### cURL

```bash
# Search for errors
curl -X POST http://localhost:8000/search \
     -H "Content-Type: application/json" \
     -d '{"level": "ERROR", "limit": 50}'

# Get statistics
curl "http://localhost:8000/stats?hours=24"
```

## Performance Considerations

- The API reads log files directly for simplicity
- For large log files (>100MB), consider using a database backend
- Implement caching for frequently accessed queries
- Use appropriate indexes if using database storage
- Consider log archival for old logs

## Future Enhancements

- [ ] Database backend for better performance
- [ ] Real-time log streaming via WebSocket
- [ ] Advanced filtering with regex support
- [ ] Log aggregation and grouping
- [ ] Export logs to various formats (CSV, Excel)
- [ ] Authentication and authorization
- [ ] Rate limiting
- [ ] Metrics and monitoring integration
