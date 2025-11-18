# Deployment Guide

## Production Deployment

### System Requirements

- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 50GB+ SSD
- **OS**: Ubuntu 20.04 LTS or similar

### Pre-deployment Checklist

- [ ] Database credentials configured
- [ ] Redis instance set up
- [ ] API keys obtained (Anthropic, SEMrush, etc.)
- [ ] SSL certificates ready
- [ ] Domain/subdomain configured
- [ ] Monitoring tools set up
- [ ] Backup strategy defined

### Environment Setup

1. **Install System Dependencies**

```bash
sudo apt update
sudo apt install python3.10 python3-pip postgresql redis-server nginx
```

2. **Create Application User**

```bash
sudo useradd -m -s /bin/bash nexus-seo
sudo su - nexus-seo
```

3. **Clone and Install**

```bash
git clone <repository-url> /home/nexus-seo/app
cd /home/nexus-seo/app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Database Setup

```bash
# Create database
sudo -u postgres createdb nexus_seo_prod

# Create user
sudo -u postgres psql -c "CREATE USER nexus_seo WITH PASSWORD 'strong_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE nexus_seo_prod TO nexus_seo;"

# Run migrations
cd /home/nexus-seo/app
source venv/bin/activate
alembic upgrade head
```

### Systemd Services

Create `/etc/systemd/system/nexus-seo-api.service`:

```ini
[Unit]
Description=NEXUS SEO Tools API
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=nexus-seo
Group=nexus-seo
WorkingDirectory=/home/nexus-seo/app
Environment="PATH=/home/nexus-seo/app/venv/bin"
ExecStart=/home/nexus-seo/app/venv/bin/uvicorn modules.seo.api.app:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/nexus-seo-worker.service`:

```ini
[Unit]
Description=NEXUS SEO Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=nexus-seo
Group=nexus-seo
WorkingDirectory=/home/nexus-seo/app
Environment="PATH=/home/nexus-seo/app/venv/bin"
ExecStart=/home/nexus-seo/app/venv/bin/celery -A modules.seo.config.celery_config worker --loglevel=info --concurrency=4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/nexus-seo-beat.service`:

```ini
[Unit]
Description=NEXUS SEO Celery Beat
After=network.target redis.service

[Service]
Type=simple
User=nexus-seo
Group=nexus-seo
WorkingDirectory=/home/nexus-seo/app
Environment="PATH=/home/nexus-seo/app/venv/bin"
ExecStart=/home/nexus-seo/app/venv/bin/celery -A modules.seo.config.celery_config beat --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start services:

```bash
sudo systemctl daemon-reload
sudo systemctl enable nexus-seo-api nexus-seo-worker nexus-seo-beat
sudo systemctl start nexus-seo-api nexus-seo-worker nexus-seo-beat
```

### Nginx Configuration

Create `/etc/nginx/sites-available/nexus-seo`:

```nginx
upstream nexus_seo_api {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name seo.yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name seo.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/seo.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seo.yourdomain.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    client_max_body_size 10M;

    location / {
        proxy_pass http://nexus_seo_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_buffering off;
    }

    location /static {
        alias /home/nexus-seo/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/nexus-seo /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d seo.yourdomain.com
```

### Monitoring Setup

Install Prometheus exporters:

```bash
pip install prometheus-fastapi-instrumentator
pip install celery-prometheus-exporter
```

### Logging

Configure log rotation in `/etc/logrotate.d/nexus-seo`:

```
/home/nexus-seo/app/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 nexus-seo nexus-seo
    sharedscripts
    postrotate
        systemctl reload nexus-seo-api
    endscript
}
```

### Backup Strategy

Create backup script `/home/nexus-seo/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups/nexus-seo"
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
pg_dump -U nexus_seo nexus_seo_prod | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Application backup
tar -czf "$BACKUP_DIR/app_$DATE.tar.gz" /home/nexus-seo/app

# Keep only last 30 days
find $BACKUP_DIR -type f -mtime +30 -delete
```

Add to crontab:

```bash
0 2 * * * /home/nexus-seo/backup.sh
```

### Health Checks

Set up health monitoring:

```bash
# Add to crontab
*/5 * * * * curl -f https://seo.yourdomain.com/health || echo "API Down" | mail -s "NEXUS SEO Alert" admin@yourdomain.com
```

### Scaling

For high-traffic deployments:

1. **Database**: Use PostgreSQL replication
2. **Redis**: Use Redis Cluster
3. **Workers**: Scale Celery workers horizontally
4. **API**: Use load balancer with multiple API instances
5. **CDN**: Use Cloudflare or similar for static assets

### Maintenance

Regular maintenance tasks:

```bash
# Update application
cd /home/nexus-seo/app
git pull
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart nexus-seo-api nexus-seo-worker nexus-seo-beat

# Clean old logs
find /home/nexus-seo/app/logs -name "*.log.*" -mtime +30 -delete

# Vacuum database
sudo -u postgres vacuumdb --analyze nexus_seo_prod
```

### Troubleshooting

Check service status:
```bash
sudo systemctl status nexus-seo-api
sudo systemctl status nexus-seo-worker
sudo journalctl -u nexus-seo-api -n 100
```

Check logs:
```bash
tail -f /home/nexus-seo/app/logs/seo.log
```

Test API:
```bash
curl https://seo.yourdomain.com/health
```
