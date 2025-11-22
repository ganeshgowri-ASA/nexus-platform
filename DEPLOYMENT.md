# Nexus Search - Deployment Guide

This guide covers deploying the Nexus Search system in production.

## Prerequisites

- Python 3.8+
- Elasticsearch 8.x
- Redis 5.x+ (for async indexing)
- Docker & Docker Compose (recommended)

## Quick Start with Docker

### 1. Clone and Configure

```bash
git clone <repository-url>
cd nexus-platform
cp .env.example .env
```

Edit `.env` with your configuration.

### 2. Start Services

```bash
docker-compose up -d
```

### 3. Initialize Indices

```bash
python scripts/init_search.py
```

### 4. Verify Installation

```bash
python -c "
import asyncio
from search.monitoring import health_monitor

async def check():
    health = await health_monitor.check_health()
    print(f\"Status: {health['status']}\")

asyncio.run(check())
"
```

## Production Deployment

### Docker Compose Setup

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.12.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
      - xpack.security.enabled=true
      - ELASTIC_PASSWORD=${ELASTICSEARCH_PASSWORD}
    volumes:
      - es_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
    networks:
      - nexus
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    networks:
      - nexus
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 5

  nexus-search-api:
    build: .
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
      - ELASTICSEARCH_USERNAME=elastic
      - ELASTICSEARCH_PASSWORD=${ELASTICSEARCH_PASSWORD}
      - REDIS_HOST=redis
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - APP_ENV=production
    depends_on:
      elasticsearch:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - nexus
    restart: unless-stopped

volumes:
  es_data:
  redis_data:

networks:
  nexus:
    driver: bridge
```

### Environment Configuration

Production `.env`:

```bash
# Elasticsearch
ELASTICSEARCH_HOSTS=http://elasticsearch:9200
ELASTICSEARCH_USERNAME=elastic
ELASTICSEARCH_PASSWORD=<strong-password>
ELASTICSEARCH_USE_SSL=true
ELASTICSEARCH_VERIFY_CERTS=true

# Index Settings
ELASTICSEARCH_INDEX_PREFIX=nexus_prod
ELASTICSEARCH_SHARDS=3
ELASTICSEARCH_REPLICAS=2

# Performance
ELASTICSEARCH_BULK_SIZE=1000
ELASTICSEARCH_QUEUE_SIZE=5000
ELASTICSEARCH_REQUEST_TIMEOUT=60
ELASTICSEARCH_MAX_RETRIES=3

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=<strong-password>

# Application
APP_ENV=production
LOG_LEVEL=WARNING
```

### Elasticsearch Configuration

Recommended `elasticsearch.yml` for production:

```yaml
cluster.name: nexus-cluster
node.name: nexus-node-1

# Network
network.host: 0.0.0.0
http.port: 9200

# Memory
bootstrap.memory_lock: true

# Discovery
discovery.type: single-node

# Paths
path.data: /usr/share/elasticsearch/data
path.logs: /usr/share/elasticsearch/logs

# Security
xpack.security.enabled: true
xpack.security.transport.ssl.enabled: true
```

### Performance Tuning

#### Elasticsearch JVM Settings

For production with large datasets:

```bash
# 8GB RAM
-Xms4g
-Xmx4g

# 16GB RAM
-Xms8g
-Xmx8g

# 32GB RAM (recommended for production)
-Xms16g
-Xmx16g
```

#### Index Settings

Optimize for your use case:

```python
# High write throughput
settings = {
    "number_of_shards": 5,
    "number_of_replicas": 1,
    "refresh_interval": "30s",
    "index.translog.durability": "async",
}

# High read performance
settings = {
    "number_of_shards": 3,
    "number_of_replicas": 2,
    "refresh_interval": "1s",
}
```

## Monitoring

### Health Checks

Set up automated health checks:

```bash
# Health check script
#!/bin/bash
curl -f http://localhost:9200/_cluster/health || exit 1
```

### Prometheus Metrics

Export metrics for monitoring:

```python
from prometheus_client import Counter, Histogram

search_requests = Counter('search_requests_total', 'Total search requests')
search_duration = Histogram('search_duration_seconds', 'Search duration')
```

### Logging

Configure centralized logging:

```python
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'nexus_search.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)

logging.basicConfig(
    handlers=[handler],
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Backup and Recovery

### Snapshot Configuration

```bash
# Create snapshot repository
curl -X PUT "localhost:9200/_snapshot/nexus_backup" -H 'Content-Type: application/json' -d'
{
  "type": "fs",
  "settings": {
    "location": "/mnt/backups/elasticsearch"
  }
}
'

# Create snapshot
curl -X PUT "localhost:9200/_snapshot/nexus_backup/snapshot_1?wait_for_completion=true"

# Restore snapshot
curl -X POST "localhost:9200/_snapshot/nexus_backup/snapshot_1/_restore"
```

### Automated Backups

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
curl -X PUT "localhost:9200/_snapshot/nexus_backup/snapshot_${DATE}?wait_for_completion=true"

# Keep only last 7 days
find /mnt/backups/elasticsearch -name "snapshot_*" -mtime +7 -delete
```

## Scaling

### Horizontal Scaling

1. **Add more Elasticsearch nodes**:
   ```yaml
   elasticsearch-2:
     image: docker.elastic.co/elasticsearch/elasticsearch:8.12.0
     environment:
       - cluster.name=nexus-cluster
       - discovery.seed_hosts=elasticsearch-1
   ```

2. **Load balancing**:
   ```nginx
   upstream elasticsearch {
       server es-node-1:9200;
       server es-node-2:9200;
       server es-node-3:9200;
   }
   ```

### Vertical Scaling

Increase resources for Elasticsearch:
- CPU: 8+ cores
- RAM: 32GB+ (50% for ES heap)
- Disk: SSD recommended, 500GB+

## Security

### Enable Authentication

```python
# In .env
ELASTICSEARCH_USERNAME=nexus_user
ELASTICSEARCH_PASSWORD=<strong-password>
ELASTICSEARCH_USE_SSL=true
```

### Network Security

1. **Firewall rules**: Restrict Elasticsearch to application servers only
2. **VPC**: Deploy in private network
3. **SSL/TLS**: Enable encryption in transit

### API Security

Implement rate limiting and authentication:

```python
from functools import wraps
from flask import request, abort

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.headers.get('X-API-Key') != API_KEY:
            abort(401)
        return f(*args, **kwargs)
    return decorated
```

## Maintenance

### Index Optimization

Run weekly:

```bash
python -c "
import asyncio
from search.monitoring import analytics

async def optimize():
    await analytics.optimize_indices()

asyncio.run(optimize())
"
```

### Clear Old Data

```python
from datetime import datetime, timedelta

async def cleanup_old_data():
    # Delete documents older than 1 year
    cutoff = datetime.utcnow() - timedelta(days=365)

    query = {
        "query": {
            "range": {
                "created_at": {"lt": cutoff.isoformat()}
            }
        }
    }

    await client.delete_by_query(index="nexus_*", body=query)
```

## Troubleshooting

### Common Issues

1. **Out of Memory**:
   - Increase heap size
   - Add more nodes
   - Reduce shard count

2. **Slow Searches**:
   - Optimize indices
   - Reduce replica count
   - Use filters instead of queries

3. **Index Issues**:
   - Check cluster health
   - Verify mappings
   - Review logs

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Support

For issues and questions:
- Check logs: `docker-compose logs elasticsearch`
- Health check: `python scripts/health_check.py`
- Documentation: `/search/README.md`
