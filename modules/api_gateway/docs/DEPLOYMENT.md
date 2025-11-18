# Deployment Guide

## Production Deployment Checklist

### Pre-Deployment

- [ ] Update `.env` with production values
- [ ] Set strong `JWT_SECRET_KEY`
- [ ] Configure SSL/TLS certificates
- [ ] Set up database backups
- [ ] Configure Redis persistence
- [ ] Set up monitoring and alerts
- [ ] Review security settings
- [ ] Load testing completed
- [ ] Documentation updated

### Security Configuration

1. **Change Default Credentials**
```bash
# In .env
ADMIN_USERNAME=<strong-username>
ADMIN_PASSWORD=<strong-password>
JWT_SECRET_KEY=<generate-random-256-bit-key>
```

2. **Generate Strong JWT Secret**
```python
import secrets
print(secrets.token_urlsafe(32))
```

3. **Configure Database Passwords**
```bash
POSTGRES_PASSWORD=<strong-db-password>
REDIS_PASSWORD=<strong-redis-password>
```

## Docker Deployment

### Basic Deployment

```bash
# Clone repository
git clone <repo-url>
cd nexus-platform/modules/api_gateway

# Configure environment
cp .env.example .env
# Edit .env with production values

# Build and start
docker-compose -f nginx/docker-compose.yml up -d

# Check logs
docker-compose -f nginx/docker-compose.yml logs -f

# Check status
docker-compose -f nginx/docker-compose.yml ps
```

### Production Configuration

Edit `nginx/docker-compose.yml` for production:

```yaml
# Increase workers
api-gateway:
  environment:
    WORKERS: 8  # Based on CPU cores

# Enable Redis persistence
redis:
  command: redis-server --appendonly yes

# Add PostgreSQL backup
postgres:
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./backups:/backups
```

### SSL/TLS Configuration

1. **Generate SSL Certificates**
```bash
# Using Let's Encrypt
certbot certonly --standalone -d api.yourdomain.com

# Or self-signed for testing
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem
```

2. **Update Nginx Configuration**
```nginx
# Uncomment SSL sections in nginx.conf
listen 443 ssl http2;
ssl_certificate /etc/nginx/ssl/cert.pem;
ssl_certificate_key /etc/nginx/ssl/key.pem;
```

3. **Update docker-compose.yml**
```yaml
nginx:
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - ./nginx/ssl:/etc/nginx/ssl:ro
```

## Kubernetes Deployment

### Deploy to Kubernetes

1. **Create ConfigMap**
```bash
kubectl create configmap api-gateway-config \
  --from-env-file=.env
```

2. **Deploy PostgreSQL**
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: nexus_gateway
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: db-secrets
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-secrets
              key: password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
```

3. **Deploy API Gateway**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
      - name: api-gateway
        image: nexus/api-gateway:latest
        envFrom:
        - configMapRef:
            name: api-gateway-config
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

4. **Create Service**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: api-gateway
spec:
  selector:
    app: api-gateway
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

5. **Deploy Ingress**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-gateway-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: api-gateway-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-gateway
            port:
              number: 80
```

## Cloud Deployment

### AWS ECS

```bash
# Build and push image
docker build -t nexus-api-gateway .
docker tag nexus-api-gateway:latest <ecr-url>/nexus-api-gateway:latest
docker push <ecr-url>/nexus-api-gateway:latest

# Create task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service
aws ecs create-service \
  --cluster nexus-cluster \
  --service-name api-gateway \
  --task-definition nexus-api-gateway \
  --desired-count 3 \
  --load-balancers targetGroupArn=<tg-arn>,containerName=api-gateway,containerPort=8000
```

### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/<project-id>/api-gateway

# Deploy
gcloud run deploy api-gateway \
  --image gcr.io/<project-id>/api-gateway \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=<url>,REDIS_HOST=<host>
```

### Azure Container Instances

```bash
# Create container
az container create \
  --resource-group nexus-rg \
  --name api-gateway \
  --image <acr-url>/api-gateway:latest \
  --dns-name-label nexus-api \
  --ports 8000 \
  --environment-variables \
    DATABASE_URL=<url> \
    REDIS_HOST=<host>
```

## Monitoring Setup

### Prometheus

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'api-gateway'
    static_configs:
      - targets: ['api-gateway:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboard

Import dashboard from `monitoring/grafana-dashboard.json`

### Logging

Configure centralized logging:

```yaml
# docker-compose.yml
api-gateway:
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
```

Or use ELK stack:
```bash
# Send logs to Logstash
LOG_OUTPUT=logstash://logstash:5000
```

## Backup and Recovery

### Database Backup

```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR=/backups
DATE=$(date +%Y%m%d_%H%M%S)

docker exec postgres pg_dump -U nexus nexus_gateway | \
  gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
```

### Redis Backup

```bash
# Backup Redis
docker exec redis redis-cli BGSAVE

# Copy RDB file
docker cp redis:/data/dump.rdb ./backups/redis_backup.rdb
```

## Scaling

### Horizontal Scaling

```bash
# Docker Swarm
docker service scale api-gateway=5

# Kubernetes
kubectl scale deployment api-gateway --replicas=5

# Docker Compose
docker-compose -f nginx/docker-compose.yml up -d --scale api-gateway=5
```

### Vertical Scaling

Update resource limits in docker-compose.yml:
```yaml
api-gateway:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 2G
      reservations:
        cpus: '1.0'
        memory: 1G
```

## Health Checks

### Application Health

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed metrics
curl http://localhost:8000/admin/metrics/summary
```

### Database Health

```bash
# PostgreSQL
docker exec postgres pg_isready -U nexus

# Redis
docker exec redis redis-cli ping
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
```bash
# Check database is running
docker-compose ps postgres

# Check connection string
docker-compose exec api-gateway env | grep DATABASE_URL

# Test connection
docker-compose exec postgres psql -U nexus -d nexus_gateway
```

2. **Redis Connection Failed**
```bash
# Check Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping
```

3. **High Memory Usage**
```bash
# Check container stats
docker stats

# Reduce workers
WORKERS=2

# Enable connection pooling
DATABASE_POOL_SIZE=20
```

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f api-gateway

# Last 100 lines
docker-compose logs --tail=100 api-gateway
```

## Maintenance

### Update Deployment

```bash
# Pull latest code
git pull

# Rebuild
docker-compose build

# Rolling update
docker-compose up -d --no-deps api-gateway
```

### Database Migrations

```bash
# Run migrations
docker-compose exec api-gateway alembic upgrade head

# Rollback
docker-compose exec api-gateway alembic downgrade -1
```

### Cleanup

```bash
# Remove old metrics
curl -X DELETE "http://localhost:8000/admin/metrics/cleanup?days=30"

# Clean Docker
docker system prune -a
```
