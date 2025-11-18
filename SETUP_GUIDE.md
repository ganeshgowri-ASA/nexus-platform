# NEXUS Platform Setup Guide

This guide will walk you through setting up the NEXUS Platform for development and production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Setup](#development-setup)
3. [Database Setup](#database-setup)
4. [API Keys Configuration](#api-keys-configuration)
5. [Running Services](#running-services)
6. [Production Deployment](#production-deployment)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System**: Linux, macOS, or Windows with WSL
- **Python**: 3.11 or higher
- **PostgreSQL**: 14 or higher
- **Redis**: 6 or higher
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: Minimum 10GB free space

### Install Required Software

#### On Ubuntu/Debian

```bash
# Update package list
sudo apt update

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Install Redis
sudo apt install redis-server

# Install build tools
sudo apt install build-essential libpq-dev
```

#### On macOS

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.11

# Install PostgreSQL
brew install postgresql@14

# Install Redis
brew install redis

# Start services
brew services start postgresql@14
brew services start redis
```

## Development Setup

### 1. Clone and Setup Project

```bash
# Clone repository
git clone https://github.com/ganeshgowri-ASA/nexus-platform.git
cd nexus-platform

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your configuration
nano .env  # or use your preferred editor
```

## Database Setup

### 1. Create Database

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# In PostgreSQL shell:
CREATE DATABASE nexus;
CREATE USER nexus_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE nexus TO nexus_user;
\q
```

### 2. Update Database URL

Edit `.env` file:

```env
DATABASE_URL=postgresql+asyncpg://nexus_user:your_secure_password@localhost:5432/nexus
DATABASE_SYNC_URL=postgresql://nexus_user:your_secure_password@localhost:5432/nexus
```

### 3. Run Migrations

```bash
# Initialize Alembic (if not already done)
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

## API Keys Configuration

### Lead Enrichment APIs

#### Clearbit

1. Sign up at https://clearbit.com
2. Get your API key from dashboard
3. Add to `.env`:
   ```env
   CLEARBIT_API_KEY=sk_your_clearbit_key
   ```

#### Hunter

1. Sign up at https://hunter.io
2. Get your API key
3. Add to `.env`:
   ```env
   HUNTER_API_KEY=your_hunter_key
   ```

### AI/LLM APIs

#### Anthropic Claude

1. Sign up at https://console.anthropic.com
2. Create an API key
3. Add to `.env`:
   ```env
   ANTHROPIC_API_KEY=sk-ant-your_key
   ```

#### OpenAI (Optional)

1. Sign up at https://platform.openai.com
2. Create an API key
3. Add to `.env`:
   ```env
   OPENAI_API_KEY=sk-your_openai_key
   ```

### Ad Platform APIs

#### Google Ads

1. Create a Google Ads account
2. Apply for API access at https://ads.google.com/home/tools/api/
3. Set up OAuth 2.0 credentials
4. Get developer token
5. Add to `.env`:
   ```env
   GOOGLE_ADS_DEVELOPER_TOKEN=your_token
   GOOGLE_ADS_CLIENT_ID=your_client_id
   GOOGLE_ADS_CLIENT_SECRET=your_secret
   GOOGLE_ADS_REFRESH_TOKEN=your_refresh_token
   GOOGLE_ADS_LOGIN_CUSTOMER_ID=your_customer_id
   ```

#### Facebook Ads

1. Create a Facebook Developer account
2. Create an app
3. Get your app credentials
4. Generate a long-lived access token
5. Add to `.env`:
   ```env
   FACEBOOK_APP_ID=your_app_id
   FACEBOOK_APP_SECRET=your_app_secret
   FACEBOOK_ACCESS_TOKEN=your_token
   ```

#### LinkedIn Ads

1. Create a LinkedIn Developer account
2. Create an app
3. Set up OAuth 2.0
4. Add to `.env`:
   ```env
   LINKEDIN_CLIENT_ID=your_client_id
   LINKEDIN_CLIENT_SECRET=your_client_secret
   LINKEDIN_ACCESS_TOKEN=your_access_token
   ```

## Running Services

### Terminal 1: FastAPI Backend

```bash
# Activate virtual environment
source venv/bin/activate

# Run FastAPI
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Access:
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Terminal 2: Celery Worker

```bash
# Activate virtual environment
source venv/bin/activate

# Run Celery worker
celery -A celery_app worker --loglevel=info
```

### Terminal 3: Celery Beat (Scheduler)

```bash
# Activate virtual environment
source venv/bin/activate

# Run Celery beat
celery -A celery_app beat --loglevel=info
```

### Terminal 4: Streamlit UI

```bash
# Activate virtual environment
source venv/bin/activate

# Run Streamlit
streamlit run streamlit_app.py
```

Access: http://localhost:8501

### Optional: Flower (Celery Monitoring)

```bash
# Activate virtual environment
source venv/bin/activate

# Run Flower
celery -A celery_app flower
```

Access: http://localhost:5555

## Production Deployment

### Using Docker

1. **Create Dockerfile**:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. **Create docker-compose.yml**:

```yaml
version: '3.8'

services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: nexus
      POSTGRES_USER: nexus_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6
    volumes:
      - redis_data:/data

  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    env_file:
      - .env

  celery_worker:
    build: .
    command: celery -A celery_app worker --loglevel=info
    depends_on:
      - db
      - redis
    env_file:
      - .env

  celery_beat:
    build: .
    command: celery -A celery_app beat --loglevel=info
    depends_on:
      - db
      - redis
    env_file:
      - .env

  streamlit:
    build: .
    command: streamlit run streamlit_app.py
    ports:
      - "8501:8501"
    depends_on:
      - api
    env_file:
      - .env

volumes:
  postgres_data:
  redis_data:
```

3. **Deploy**:

```bash
docker-compose up -d
```

### Using Systemd (Linux)

Create service files for each component:

**FastAPI Service** (`/etc/systemd/system/nexus-api.service`):

```ini
[Unit]
Description=NEXUS API
After=network.target

[Service]
User=nexus
WorkingDirectory=/opt/nexus-platform
Environment="PATH=/opt/nexus-platform/venv/bin"
ExecStart=/opt/nexus-platform/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

**Celery Worker Service** (`/etc/systemd/system/nexus-celery.service`):

```ini
[Unit]
Description=NEXUS Celery Worker
After=network.target

[Service]
User=nexus
WorkingDirectory=/opt/nexus-platform
Environment="PATH=/opt/nexus-platform/venv/bin"
ExecStart=/opt/nexus-platform/venv/bin/celery -A celery_app worker --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start services:

```bash
sudo systemctl enable nexus-api nexus-celery
sudo systemctl start nexus-api nexus-celery
```

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Check database exists
psql -U postgres -l

# Test connection
psql -U nexus_user -d nexus -h localhost
```

### Redis Connection Issues

```bash
# Check if Redis is running
sudo systemctl status redis

# Test Redis connection
redis-cli ping
```

### Migration Issues

```bash
# Reset database (CAUTION: destroys data)
alembic downgrade base
alembic upgrade head

# Or drop and recreate
sudo -u postgres psql
DROP DATABASE nexus;
CREATE DATABASE nexus;
\q

alembic upgrade head
```

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

## Next Steps

1. **Configure API Keys**: Add all required API keys to `.env`
2. **Run Tests**: `pytest` to ensure everything works
3. **Create Admin User**: Set up initial user accounts
4. **Import Sample Data**: Test with sample leads and campaigns
5. **Configure Monitoring**: Set up Sentry for error tracking
6. **Set up Backups**: Configure database backup strategy

## Support

For help and questions:
- Documentation: Check README.md
- Issues: GitHub Issues
- Email: support@nexus-platform.com
