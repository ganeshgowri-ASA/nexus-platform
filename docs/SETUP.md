# NEXUS DMS Setup Guide

Complete guide for setting up and deploying the NEXUS Document Management System.

## Table of Contents

- [System Requirements](#system-requirements)
- [Local Development Setup](#local-development-setup)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [Running Tests](#running-tests)
- [Production Deployment](#production-deployment)
- [Docker Deployment](#docker-deployment)
- [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements

- Python 3.11 or higher
- PostgreSQL 14+ or SQLite (development only)
- Redis 6+ (for caching and task queue)
- 2GB RAM
- 10GB disk space

### Recommended Requirements

- Python 3.12
- PostgreSQL 16+
- Redis 7+
- 4GB+ RAM
- 50GB+ disk space (for document storage)
- Linux/Unix-based OS

### Optional Requirements

- Elasticsearch 8+ (for advanced search)
- AWS S3 / Azure Blob / GCS (for cloud storage)
- Tesseract OCR (for document OCR)
- Docker & Docker Compose (for containerized deployment)

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/nexus-platform.git
cd nexus-platform
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install Poetry (if not already installed)
pip install poetry

# Install project dependencies
poetry install

# Or using pip
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# Application
APP_NAME=NEXUS Platform
DEBUG=true
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql://nexus_user:nexus_password@localhost:5432/nexus_db

# Security
SECRET_KEY=your-secret-key-here-minimum-32-characters

# Storage
STORAGE_BACKEND=local
STORAGE_PATH=./storage

# Redis
REDIS_URL=redis://localhost:6379/0

# Optional: AI Features
ANTHROPIC_API_KEY=your-anthropic-api-key
```

### 5. Install System Dependencies

#### Ubuntu/Debian

```bash
# PostgreSQL
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Redis
sudo apt-get install redis-server

# Tesseract OCR (optional)
sudo apt-get install tesseract-ocr tesseract-ocr-eng

# Image processing
sudo apt-get install libmagic1
```

#### macOS

```bash
# Using Homebrew
brew install postgresql@16
brew install redis
brew install tesseract  # optional
brew install libmagic
```

### 6. Set Up PostgreSQL Database

```bash
# Create database and user
sudo -u postgres psql

CREATE USER nexus_user WITH PASSWORD 'nexus_password';
CREATE DATABASE nexus_db OWNER nexus_user;
GRANT ALL PRIVILEGES ON DATABASE nexus_db TO nexus_user;
\q
```

### 7. Run Database Migrations

```bash
# Create tables
alembic upgrade head

# Or using the setup script
python scripts/setup_db.py
```

### 8. Create Admin User

```bash
python scripts/create_admin.py --email admin@example.com --password AdminPass123!
```

## Configuration

### Environment Variables

Key configuration options in `.env`:

#### Application Settings

```bash
APP_NAME=NEXUS Platform
APP_VERSION=0.1.0
DEBUG=false
ENVIRONMENT=production
API_V1_PREFIX=/api/v1
```

#### Database

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
DB_ECHO=false  # Set to true for SQL query logging
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

#### Security

```bash
SECRET_KEY=your-very-secure-secret-key-at-least-32-chars-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Password requirements
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_NUMBERS=true
PASSWORD_REQUIRE_SPECIAL=true
```

#### Storage

```bash
# Local storage
STORAGE_BACKEND=local
STORAGE_PATH=./storage
MAX_UPLOAD_SIZE=104857600  # 100MB in bytes

# AWS S3
STORAGE_BACKEND=s3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET_NAME=nexus-documents
AWS_S3_REGION=us-east-1
```

#### Redis

```bash
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=optional-password
REDIS_CACHE_TTL=3600
```

#### AI Features

```bash
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
AI_SUMMARIZATION_ENABLED=true
AI_CLASSIFICATION_ENABLED=true
```

#### Search

```bash
SEARCH_BACKEND=postgresql  # or elasticsearch
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
```

#### Email (SMTP)

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@nexus-platform.com
SMTP_USE_TLS=true
```

## Database Setup

### Using Alembic Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

### Database Backup and Restore

```bash
# Backup
pg_dump nexus_db > backup_$(date +%Y%m%d).sql

# Restore
psql nexus_db < backup_20250115.sql
```

## Running the Application

### Development Server

```bash
# Start backend API
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Start Celery worker (in separate terminal)
celery -A backend.celery_app worker --loglevel=info

# Start Celery beat (scheduler)
celery -A backend.celery_app beat --loglevel=info

# Start frontend (Streamlit)
streamlit run frontend/app.py --server.port 8501
```

### Using the Makefile

```bash
# Start all services
make dev

# Start backend only
make run-backend

# Start frontend only
make run-frontend

# Start workers
make run-workers
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test Types

```bash
# Unit tests only
pytest tests/backend/ -m unit

# Integration tests only
pytest tests/integration/ -m integration

# With coverage
pytest --cov=backend --cov-report=html

# Verbose output
pytest -v

# Run specific test file
pytest tests/backend/test_storage.py

# Run specific test
pytest tests/backend/test_storage.py::TestLocalStorageBackend::test_upload_file_success
```

### Test Configuration

Configure pytest in `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
```

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=backend --cov-report=html

# View report
open htmlcov/index.html

# Generate coverage badge
coverage-badge -o coverage.svg
```

## Production Deployment

### 1. Server Setup

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install system dependencies
sudo apt-get install -y \
    python3.11 python3.11-venv \
    postgresql-16 redis-server \
    nginx supervisor \
    git build-essential
```

### 2. Application Deployment

```bash
# Create application user
sudo useradd -m -s /bin/bash nexus
sudo su - nexus

# Clone repository
git clone https://github.com/your-org/nexus-platform.git
cd nexus-platform

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with production settings

# Run migrations
alembic upgrade head

# Collect static files (if applicable)
python scripts/collect_static.py
```

### 3. Configure Gunicorn

Create `/home/nexus/nexus-platform/gunicorn_config.py`:

```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
max_requests = 1000
max_requests_jitter = 50
timeout = 120
keepalive = 5
```

### 4. Configure Supervisor

Create `/etc/supervisor/conf.d/nexus.conf`:

```ini
[program:nexus-api]
command=/home/nexus/nexus-platform/venv/bin/gunicorn backend.main:app -c /home/nexus/nexus-platform/gunicorn_config.py
directory=/home/nexus/nexus-platform
user=nexus
autostart=true
autorestart=true
stderr_logfile=/var/log/nexus/api.err.log
stdout_logfile=/var/log/nexus/api.out.log

[program:nexus-celery]
command=/home/nexus/nexus-platform/venv/bin/celery -A backend.celery_app worker --loglevel=info
directory=/home/nexus/nexus-platform
user=nexus
autostart=true
autorestart=true
stderr_logfile=/var/log/nexus/celery.err.log
stdout_logfile=/var/log/nexus/celery.out.log
```

Start services:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start nexus-api
sudo supervisorctl start nexus-celery
```

### 5. Configure Nginx

Create `/etc/nginx/sites-available/nexus`:

```nginx
server {
    listen 80;
    server_name nexus.example.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /home/nexus/nexus-platform/static;
        expires 30d;
    }

    location /media {
        internal;
        alias /home/nexus/nexus-platform/storage;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/nexus /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. SSL Certificate (Let's Encrypt)

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d nexus.example.com
```

## Docker Deployment

### Using Docker Compose

1. **Create docker-compose.yml:**

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: nexus_db
      POSTGRES_USER: nexus_user
      POSTGRES_PASSWORD: nexus_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: .
    command: uvicorn backend.main:app --host 0.0.0.0 --port 8000
    volumes:
      - ./storage:/app/storage
      - ./logs:/app/logs
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://nexus_user:nexus_password@postgres:5432/nexus_db
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  celery:
    build: .
    command: celery -A backend.celery_app worker --loglevel=info
    volumes:
      - ./storage:/app/storage
    environment:
      DATABASE_URL: postgresql://nexus_user:nexus_password@postgres:5432/nexus_db
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
```

2. **Build and run:**

```bash
docker-compose up -d
```

3. **Run migrations:**

```bash
docker-compose exec backend alembic upgrade head
```

4. **View logs:**

```bash
docker-compose logs -f backend
```

## Troubleshooting

### Common Issues

#### Database Connection Errors

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection
psql -U nexus_user -d nexus_db -h localhost

# Reset password
sudo -u postgres psql
ALTER USER nexus_user WITH PASSWORD 'new_password';
```

#### Redis Connection Errors

```bash
# Check Redis is running
sudo systemctl status redis

# Test connection
redis-cli ping

# Check Redis logs
sudo tail -f /var/log/redis/redis-server.log
```

#### Storage Permission Errors

```bash
# Fix storage permissions
sudo chown -R nexus:nexus /path/to/storage
sudo chmod -R 755 /path/to/storage
```

#### Port Already in Use

```bash
# Find process using port 8000
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>
```

### Logs

```bash
# Application logs
tail -f logs/nexus.log

# Nginx logs
sudo tail -f /var/log/nginx/error.log

# Supervisor logs
sudo tail -f /var/log/supervisor/supervisord.log

# PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-16-main.log
```

### Performance Tuning

#### PostgreSQL

Edit `/etc/postgresql/16/main/postgresql.conf`:

```
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
work_mem = 4MB
max_connections = 100
```

#### Redis

Edit `/etc/redis/redis.conf`:

```
maxmemory 512mb
maxmemory-policy allkeys-lru
```

### Health Checks

```bash
# Check API health
curl http://localhost:8000/health

# Check database connection
python -c "from backend.database import engine; engine.connect()"

# Check Redis
redis-cli ping
```

## Next Steps

- Review the [API Documentation](API.md)
- Understand the [Architecture](ARCHITECTURE.md)
- Configure [monitoring and alerting](#monitoring)
- Set up [automated backups](#backups)
- Review [security best practices](#security)

## Support

For setup assistance:

- Email: support@nexus-platform.com
- Documentation: https://docs.nexus-platform.com
- Community: https://community.nexus-platform.com
