# API Reference

## Authentication

### Login

**POST** `/auth/login`

Get JWT access and refresh tokens.

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Refresh Token

**POST** `/auth/refresh`

Refresh an expired access token.

**Parameters:**
- `refresh_token` (string): The refresh token

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## Routes Management

### List Routes

**GET** `/admin/routes/`

Get all configured routes.

**Parameters:**
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Maximum records to return (default: 100)

**Response:**
```json
[
  {
    "id": 1,
    "name": "user-service",
    "path": "/api/users/*",
    "method": "GET",
    "target_url": "http://backend:8080",
    "enabled": true,
    "require_auth": true,
    "rate_limit": 100,
    "cache_enabled": false,
    "description": "User service API",
    "created_at": "2024-01-01T00:00:00"
  }
]
```

### Get Route

**GET** `/admin/routes/{route_id}`

Get details of a specific route.

**Response:**
```json
{
  "id": 1,
  "name": "user-service",
  "path": "/api/users/*",
  "method": "GET",
  "target_url": "http://backend:8080",
  "enabled": true,
  "require_auth": true,
  "rate_limit": 100,
  "rate_limit_window": 60,
  "load_balance_strategy": "round_robin",
  "target_urls": ["http://backend1:8080", "http://backend2:8080"],
  "cache_enabled": false,
  "cache_ttl": 300,
  "request_transform": null,
  "response_transform": null,
  "headers_to_add": {},
  "headers_to_remove": [],
  "timeout": 30.0,
  "description": "User service API",
  "tags": ["users", "api"],
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

### Create Route

**POST** `/admin/routes/`

Create a new route configuration.

**Request:**
```json
{
  "name": "user-service",
  "path": "/api/users/*",
  "method": "GET",
  "target_url": "http://backend:8080",
  "enabled": true,
  "require_auth": true,
  "rate_limit": 100,
  "rate_limit_window": 60,
  "load_balance_strategy": "round_robin",
  "target_urls": [],
  "cache_enabled": false,
  "cache_ttl": 300,
  "request_transform": null,
  "response_transform": null,
  "headers_to_add": {},
  "headers_to_remove": [],
  "timeout": 30.0,
  "description": "User service API",
  "tags": ["users", "api"]
}
```

**Response:**
```json
{
  "id": 1,
  "name": "user-service",
  "message": "Route created successfully"
}
```

### Update Route

**PUT** `/admin/routes/{route_id}`

Update an existing route.

**Request:**
```json
{
  "enabled": false,
  "rate_limit": 200,
  "cache_enabled": true
}
```

**Response:**
```json
{
  "id": 1,
  "name": "user-service",
  "message": "Route updated successfully"
}
```

### Delete Route

**DELETE** `/admin/routes/{route_id}`

Delete a route configuration.

**Response:**
```json
{
  "message": "Route deleted successfully"
}
```

## API Keys Management

### List API Keys

**GET** `/admin/api-keys/`

Get all API keys.

**Parameters:**
- `skip` (int): Number to skip (default: 0)
- `limit` (int): Max records (default: 100)
- `active_only` (bool): Only active keys (default: false)

**Response:**
```json
[
  {
    "id": 1,
    "key": "nxs_abc123...",
    "name": "Production API Key",
    "user_id": "user123",
    "email": "user@example.com",
    "active": true,
    "scopes": ["read", "write"],
    "rate_limit": 1000,
    "total_requests": 5420,
    "last_used_at": "2024-01-01T12:00:00",
    "expires_at": null,
    "created_at": "2024-01-01T00:00:00"
  }
]
```

### Get API Key

**GET** `/admin/api-keys/{key_id}`

Get details of a specific API key.

### Create API Key

**POST** `/admin/api-keys/`

Generate a new API key.

**Request:**
```json
{
  "name": "Production API Key",
  "user_id": "user123",
  "email": "user@example.com",
  "scopes": ["read", "write"],
  "allowed_routes": [],
  "rate_limit": 1000,
  "rate_limit_window": 3600,
  "expires_at": null,
  "description": "Key for production use",
  "metadata": {}
}
```

**Response:**
```json
{
  "id": 1,
  "key": "nxs_abc123def456...",
  "name": "Production API Key",
  "message": "API key created successfully. Save this key - it won't be shown again!"
}
```

### Update API Key

**PUT** `/admin/api-keys/{key_id}`

Update an API key.

### Delete API Key

**DELETE** `/admin/api-keys/{key_id}`

Delete an API key.

### Rotate API Key

**POST** `/admin/api-keys/{key_id}/rotate`

Generate a new key value for an existing API key.

**Response:**
```json
{
  "id": 1,
  "key": "nxs_new789xyz...",
  "name": "Production API Key",
  "message": "API key rotated successfully. Save this new key!"
}
```

## Metrics

### Metrics Summary

**GET** `/admin/metrics/summary`

Get aggregated metrics for a time period.

**Parameters:**
- `hours` (int): Time window in hours (default: 24)

**Response:**
```json
{
  "period_hours": 24,
  "total_requests": 15420,
  "error_count": 54,
  "error_rate": 0.35,
  "avg_response_time_ms": 125.5,
  "cache_hit_rate": 45.2,
  "status_codes": {
    "200": 14800,
    "404": 320,
    "500": 54
  },
  "top_routes": [
    {
      "route": "user-service",
      "requests": 5420,
      "avg_response_time_ms": 98.2
    }
  ]
}
```

### Request Metrics

**GET** `/admin/metrics/requests`

Get detailed request metrics.

**Parameters:**
- `skip` (int): Records to skip
- `limit` (int): Max records (default: 100)
- `route_name` (string): Filter by route
- `status_code` (int): Filter by status code
- `error_only` (bool): Only errors
- `hours` (int): Time window (default: 24)

**Response:**
```json
[
  {
    "id": 1,
    "timestamp": "2024-01-01T12:00:00",
    "method": "GET",
    "path": "/api/users/123",
    "route_name": "user-service",
    "status_code": 200,
    "response_time_ms": 125.5,
    "client_ip": "192.168.1.100",
    "error": false,
    "error_message": null,
    "cache_hit": false
  }
]
```

### Time Series Metrics

**GET** `/admin/metrics/timeseries`

Get metrics aggregated by time intervals.

**Parameters:**
- `interval_minutes` (int): Interval size (default: 60)
- `hours` (int): Time window (default: 24)

**Response:**
```json
[
  {
    "timestamp": "2024-01-01T12:00:00",
    "requests": 540,
    "avg_response_time_ms": 125.5,
    "errors": 5
  }
]
```

### Cleanup Old Metrics

**DELETE** `/admin/metrics/cleanup`

Delete metrics older than specified days.

**Parameters:**
- `days` (int): Delete metrics older than this (default: 30)

**Response:**
```json
{
  "message": "Deleted 15420 metrics older than 30 days"
}
```

## Health Check

**GET** `/health`

Check gateway health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "redis_connected": true
}
```

## Gateway Proxy

**ANY** `/{path:path}`

Proxy requests to backend services based on configured routes.

This endpoint handles all HTTP methods (GET, POST, PUT, DELETE, PATCH, etc.) and routes them to the appropriate backend service based on the route configuration.

**Headers:**
- `X-API-Key`: API key for authentication
- `Authorization`: JWT bearer token for authentication

**Response Headers:**
- `X-RateLimit-Limit`: Rate limit maximum
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Rate limit reset time
- `X-Response-Time`: Response time in milliseconds
