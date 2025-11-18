# NEXUS Scheduler - Deployment Guide

## Production Deployment

### Prerequisites

- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+
- 4GB RAM minimum
- 20GB disk space

### Environment Setup

1. **Create production .env file**

```bash
cp .env.example .env
```

2. **Configure environment variables**

```bash
# Database
DATABASE_URL=postgresql+asyncpg://nexus:STRONG_PASSWORD@postgres:5432/nexus_scheduler
DATABASE_URL_SYNC=postgresql://nexus:STRONG_PASSWORD@postgres:5432/nexus_scheduler

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_HOST=redis
REDIS_PORT=6379

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# Security
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false

# Scheduler
DEFAULT_TIMEZONE=UTC
MAX_RETRY_ATTEMPTS=3
TASK_TIMEOUT=3600
ENABLE_SCHEDULER=true
```

### Deployment Steps

#### 1. Build Images

```bash
docker-compose build --no-cache
```

#### 2. Start Services

```bash
docker-compose up -d
```

#### 3. Run Migrations

```bash
docker-compose exec api alembic upgrade head
```

#### 4. Verify Deployment

```bash
# Check service health
docker-compose ps

# Check logs
docker-compose logs -f

# Test API
curl http://localhost:8000/health
```

### SSL/TLS Configuration

#### Using Nginx Reverse Proxy

1. **Install Nginx**

```bash
sudo apt-get install nginx
```

2. **Configure Nginx**

Create `/etc/nginx/sites-available/nexus-scheduler`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # API
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Streamlit UI
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

3. **Enable site**

```bash
sudo ln -s /etc/nginx/sites-available/nexus-scheduler /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Monitoring

#### Setup Health Checks

```bash
# Add to crontab
*/5 * * * * curl -f http://localhost:8000/health || systemctl restart nexus-scheduler
```

#### Log Management

```bash
# Configure log rotation
cat > /etc/logrotate.d/nexus-scheduler << EOF
/var/log/nexus-scheduler/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
}
EOF
```

### Backup

#### Database Backup

```bash
# Create backup script
cat > /usr/local/bin/backup-nexus-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=/backups/nexus-scheduler
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T postgres pg_dump -U nexus nexus_scheduler | gzip > $BACKUP_DIR/db_$DATE.sql.gz
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete
EOF

chmod +x /usr/local/bin/backup-nexus-db.sh

# Add to crontab
0 2 * * * /usr/local/bin/backup-nexus-db.sh
```

### Scaling

#### Horizontal Scaling

1. **Scale Celery Workers**

```bash
docker-compose up -d --scale celery_worker=5
```

2. **Load Balancer Configuration**

Use nginx or HAProxy to distribute requests across multiple API instances.

#### Vertical Scaling

Adjust resource limits in `docker-compose.yml`:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### Security Hardening

#### 1. Environment Variables

- Never commit .env to version control
- Use secrets management (e.g., HashiCorp Vault)

#### 2. Database Security

```bash
# Change default passwords
# Enable SSL for database connections
# Restrict network access
```

#### 3. API Security

- Add authentication middleware
- Implement rate limiting
- Enable CORS properly
- Use API keys

#### 4. Network Security

```bash
# Configure firewall
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Monitoring & Alerting

#### Prometheus + Grafana

1. **Add to docker-compose.yml**

```yaml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana-storage:/var/lib/grafana
```

2. **Configure Prometheus**

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'nexus-scheduler'
    static_configs:
      - targets: ['api:8000']
```

### Troubleshooting

#### Service Won't Start

```bash
# Check logs
docker-compose logs api

# Check database connection
docker-compose exec api python -c "from modules.scheduler.models import async_engine; print('OK')"
```

#### Performance Issues

```bash
# Monitor resource usage
docker stats

# Check database performance
docker-compose exec postgres psql -U nexus -c "SELECT * FROM pg_stat_activity;"

# Check Redis
docker-compose exec redis redis-cli info
```

#### Database Migration Issues

```bash
# Check migration status
docker-compose exec api alembic current

# Force migration
docker-compose exec api alembic upgrade head

# Rollback if needed
docker-compose exec api alembic downgrade -1
```

### Maintenance

#### Regular Tasks

- Daily database backups
- Weekly log rotation
- Monthly security updates
- Quarterly performance review

#### Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild containers
docker-compose build

# Restart services
docker-compose up -d

# Run migrations
docker-compose exec api alembic upgrade head
```

### High Availability

#### Database Replication

Configure PostgreSQL streaming replication for failover.

#### Redis Sentinel

Use Redis Sentinel for automatic failover:

```yaml
services:
  redis-sentinel:
    image: redis:7-alpine
    command: redis-sentinel /etc/redis/sentinel.conf
```

#### Load Balancing

Use multiple API instances behind a load balancer.

## Cloud Deployment

### AWS

1. Use RDS for PostgreSQL
2. Use ElastiCache for Redis
3. Use ECS/Fargate for containers
4. Use ALB for load balancing
5. Use CloudWatch for monitoring

### GCP

1. Use Cloud SQL for PostgreSQL
2. Use Memorystore for Redis
3. Use Cloud Run for containers
4. Use Cloud Load Balancing
5. Use Cloud Monitoring

### Azure

1. Use Azure Database for PostgreSQL
2. Use Azure Cache for Redis
3. Use Azure Container Instances
4. Use Azure Load Balancer
5. Use Azure Monitor

## Performance Optimization

### Database

- Add indexes on frequently queried columns
- Use connection pooling
- Enable query caching
- Regular VACUUM and ANALYZE

### Redis

- Configure max memory and eviction policy
- Use connection pooling
- Monitor memory usage

### Application

- Enable response caching
- Use async operations
- Optimize Celery concurrency
- Profile slow endpoints
