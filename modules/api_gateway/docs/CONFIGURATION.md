# Configuration Guide

## Environment Variables

### Application Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | NEXUS API Gateway | Application name |
| `APP_VERSION` | 1.0.0 | Application version |
| `DEBUG` | false | Enable debug mode |
| `HOST` | 0.0.0.0 | Server host |
| `PORT` | 8000 | Server port |
| `WORKERS` | 4 | Number of worker processes |

### Database Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXUS_GATEWAY_DATABASE_URL` | postgresql://nexus:nexus@localhost:5432/nexus_gateway | PostgreSQL connection URL |

Format: `postgresql://user:password@host:port/database`

### Redis Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXUS_REDIS_HOST` | localhost | Redis server host |
| `NEXUS_REDIS_PORT` | 6379 | Redis server port |
| `NEXUS_REDIS_DB` | 0 | Redis database number |
| `NEXUS_REDIS_PASSWORD` | - | Redis password (optional) |

### JWT Authentication

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET_KEY` | your-secret-key | Secret key for JWT signing (CHANGE IN PRODUCTION!) |
| `JWT_ALGORITHM` | HS256 | JWT signing algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | 60 | Access token expiration (minutes) |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Refresh token expiration (days) |

### Rate Limiting

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_RATE_LIMIT` | 100 | Default requests per minute |
| `DEFAULT_RATE_LIMIT_WINDOW` | 60 | Rate limit window in seconds |

### Caching

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_CACHE_TTL` | 300 | Default cache TTL in seconds |
| `CACHE_ENABLED` | true | Enable/disable caching |

### Timeouts

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_TIMEOUT` | 30.0 | Default request timeout (seconds) |
| `BACKEND_CONNECT_TIMEOUT` | 5.0 | Backend connection timeout |
| `BACKEND_READ_TIMEOUT` | 30.0 | Backend read timeout |

### Load Balancing

| Variable | Default | Description |
|----------|---------|-------------|
| `LOAD_BALANCE_STRATEGY` | round_robin | Strategy: round_robin, least_connections, ip_hash |

### Monitoring

| Variable | Default | Description |
|----------|---------|-------------|
| `METRICS_ENABLED` | true | Enable metrics collection |
| `METRICS_RETENTION_DAYS` | 30 | Days to retain metrics |

### CORS

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ORIGINS` | * | Allowed origins (comma-separated) |
| `CORS_CREDENTIALS` | true | Allow credentials |
| `CORS_METHODS` | * | Allowed methods |
| `CORS_HEADERS` | * | Allowed headers |

### Admin UI

| Variable | Default | Description |
|----------|---------|-------------|
| `ADMIN_UI_ENABLED` | true | Enable admin UI |
| `ADMIN_USERNAME` | admin | Admin username |
| `ADMIN_PASSWORD` | admin123 | Admin password (CHANGE IN PRODUCTION!) |

### Logging

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | INFO | Logging level: DEBUG, INFO, WARNING, ERROR |
| `LOG_FORMAT` | json | Log format: json or text |

## Route Configuration

Routes can be configured via the Admin UI or API. Each route has the following properties:

### Basic Configuration

```python
{
    "name": "route-name",          # Unique route identifier
    "path": "/api/service/*",      # Path pattern (* for wildcard)
    "method": "GET",               # HTTP method
    "target_url": "http://backend:8080",  # Backend service URL
    "enabled": true,               # Enable/disable route
    "require_auth": true,          # Require authentication
    "description": "Route description"
}
```

### Rate Limiting

```python
{
    "rate_limit": 100,             # Requests per window
    "rate_limit_window": 60        # Window size in seconds
}
```

Per-route rate limiting overrides the default.

### Load Balancing

```python
{
    "target_urls": [               # Multiple backend URLs
        "http://backend1:8080",
        "http://backend2:8080",
        "http://backend3:8080"
    ],
    "load_balance_strategy": "round_robin"  # or "least_connections", "ip_hash"
}
```

### Caching

```python
{
    "cache_enabled": true,         # Enable caching for this route
    "cache_ttl": 300              # Cache TTL in seconds
}
```

Caching only works for GET requests with 200 status codes.

### Request/Response Transformation

#### Request Transformation

```python
{
    "request_transform": {
        "rename_fields": {
            "old_name": "new_name"
        },
        "remove_fields": ["field1", "field2"],
        "add_fields": {
            "new_field": "value"
        },
        "map_values": {
            "status": {
                "active": "1",
                "inactive": "0"
            }
        }
    }
}
```

#### Response Transformation

```python
{
    "response_transform": {
        "rename_fields": {
            "data": "results"
        },
        "remove_fields": ["internal_field"],
        "extract_fields": ["meta.total"]
    }
}
```

### Headers

```python
{
    "headers_to_add": {
        "X-Custom-Header": "value",
        "X-Service-Version": "1.0"
    },
    "headers_to_remove": [
        "X-Internal-Header"
    ]
}
```

### Timeouts

```python
{
    "timeout": 30.0               # Request timeout in seconds
}
```

### Tags

```python
{
    "tags": ["users", "public", "v1"]
}
```

Tags help organize and filter routes.

## API Key Configuration

API keys can be created via the Admin UI or API:

```python
{
    "name": "Production Key",
    "user_id": "user123",
    "email": "user@example.com",
    "scopes": ["read", "write"],
    "allowed_routes": [],          # Empty = all routes
    "rate_limit": 1000,           # Requests per hour
    "rate_limit_window": 3600,
    "expires_at": "2025-12-31T23:59:59",
    "description": "Production API key",
    "metadata": {
        "department": "engineering",
        "project": "mobile-app"
    }
}
```

### Scopes

Scopes control permissions:
- `read`: Read-only access
- `write`: Write access
- `admin`: Administrative access
- Custom scopes as needed

### Rate Limiting

Per-key rate limiting overrides route and global limits.

## Nginx Configuration

### Basic Setup

```nginx
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://api-gateway:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### SSL/TLS

```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    # ... rest of config
}
```

### Rate Limiting

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;

location / {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://api-gateway:8000;
}
```

### Caching

```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m;

location / {
    proxy_cache api_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_key "$scheme$request_method$host$request_uri";
    proxy_pass http://api-gateway:8000;
}
```

## Kong Configuration

### Service and Route

```yaml
services:
  - name: nexus-api-gateway
    url: http://api-gateway:8000

routes:
  - name: api-route
    paths:
      - /api
    service: nexus-api-gateway
```

### Rate Limiting Plugin

```yaml
plugins:
  - name: rate-limiting
    config:
      minute: 100
      hour: 5000
      policy: redis
```

### Authentication Plugin

```yaml
plugins:
  - name: key-auth
    config:
      key_names:
        - apikey
```

## Database Schema

The gateway uses the following tables:

### routes
- Route configurations
- Indexes on: name, path, method, enabled

### api_keys
- API key configurations
- Indexes on: key, active, user_id

### metrics
- Request/response metrics
- Indexes on: timestamp, route_name, status_code, api_key_id

### rate_limits
- Rate limit tracking (fallback when Redis unavailable)
- Indexes on: identifier, route_name

## Redis Data Structures

### Cache Keys

```
cache:{hash}                    # Cached responses
```

### Rate Limit Keys

```
ratelimit:{identifier}          # Rate limit counters
```

### Metric Keys

```
metric:{metric_name}            # Metric counters
```

## Performance Tuning

### Database Connection Pool

```python
# In database/connection.py
engine = create_engine(
    DATABASE_URL,
    pool_size=20,              # Increase for high load
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### Redis Connection Pool

```python
# In database/redis_client.py
pool = redis.ConnectionPool(
    max_connections=50,
    socket_connect_timeout=5,
    socket_keepalive=True
)
```

### Uvicorn Workers

```bash
# Increase workers for high CPU systems
WORKERS=8

# Or use Gunicorn
gunicorn modules.api_gateway.app.main:app \
  -k uvicorn.workers.UvicornWorker \
  -w 8 \
  -b 0.0.0.0:8000
```

### Caching Strategy

1. **Cache Frequently Accessed Data**
   - Enable caching for GET endpoints
   - Set appropriate TTL

2. **Cache Invalidation**
   - Manual: DELETE /admin/cache/{pattern}
   - Automatic: Set TTL based on data volatility

3. **Cache Warming**
   - Pre-populate cache for critical endpoints

### Rate Limiting Strategy

1. **Global Limits**: Protect against DDoS
2. **Per-Route Limits**: Protect expensive operations
3. **Per-User Limits**: Fair usage

## Security Best Practices

1. **Always use HTTPS in production**
2. **Rotate JWT secret keys regularly**
3. **Use strong passwords for admin accounts**
4. **Implement IP whitelisting for admin endpoints**
5. **Enable CORS only for trusted origins**
6. **Keep dependencies updated**
7. **Regular security audits**
8. **Monitor for suspicious activity**
9. **Implement request size limits**
10. **Use prepared statements (SQLAlchemy handles this)**

## Monitoring Configuration

### Prometheus Metrics

Expose metrics endpoint:
```python
from prometheus_client import Counter, Histogram

request_count = Counter('api_requests_total', 'Total requests')
request_duration = Histogram('api_request_duration_seconds', 'Request duration')
```

### Health Checks

Configure health check intervals:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Alerting

Configure alerts for:
- High error rates (>5%)
- Slow response times (>1s)
- High memory usage (>80%)
- Database connection failures
- Redis connection failures

## Troubleshooting Configuration

### Enable Debug Logging

```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

### Database Query Logging

```python
# In database/connection.py
engine = create_engine(DATABASE_URL, echo=True)
```

### Redis Command Logging

```bash
# Connect to Redis CLI
redis-cli MONITOR
```

### Network Debugging

```bash
# Test backend connectivity
curl -v http://backend:8080/health

# Check DNS resolution
nslookup backend

# Test from gateway container
docker exec api-gateway curl http://backend:8080
```
