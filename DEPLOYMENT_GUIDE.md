# NEXUS Platform - Deployment Guide

## Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL 14+ (or SQLite for development)
- Redis 7+
- Node.js 18+ (optional, for frontend builds)
- Docker & Docker Compose (recommended)

### Local Development

1. **Clone the repository:**
```bash
git clone https://github.com/ganeshgowri-ASA/nexus-platform.git
cd nexus-platform
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Initialize database:**
```bash
alembic upgrade head
python database/init_db.py
```

6. **Run Streamlit app:**
```bash
streamlit run streamlit_app.py
```

Access the app at: http://localhost:8501

---

## Docker Deployment

### Using Docker Compose

1. **Build and run:**
```bash
docker-compose up -d --build
```

2. **View logs:**
```bash
docker-compose logs -f
```

3. **Stop services:**
```bash
docker-compose down
```

### Services
- **Streamlit App:** http://localhost:8501
- **FastAPI:** http://localhost:8000
- **Redis:** localhost:6379
- **PostgreSQL:** localhost:5432

---

## Streamlit Cloud Deployment

### Step 1: Prepare Repository
Ensure the following files are in your repository root:
- `streamlit_app.py` (main entry point)
- `requirements.txt` (dependencies)
- `.streamlit/config.toml` (optional configuration)

### Step 2: Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select repository: `ganeshgowri-ASA/nexus-platform`
5. Branch: `main`
6. Main file path: `streamlit_app.py`
7. Click "Deploy"

### Step 3: Configure Secrets
In Streamlit Cloud dashboard, add secrets:
```toml
[database]
DATABASE_URL = "postgresql://..."

[redis]
REDIS_URL = "redis://..."

[api_keys]
OPENAI_API_KEY = "sk-..."
ANTHROPIC_API_KEY = "..."
```

---

## Environment Variables

### Required Variables
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/nexus_db

# Security
SECRET_KEY=your-secret-key-minimum-32-characters

# Redis
REDIS_URL=redis://localhost:6379/0
```

### Optional Variables
```env
# AI Services
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=...

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# OAuth
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
MICROSOFT_CLIENT_ID=...
MICROSOFT_CLIENT_SECRET=...

# Monitoring
SENTRY_DSN=https://...
```

---

## Production Checklist

### Security
- [ ] Change all default passwords
- [ ] Generate strong SECRET_KEY
- [ ] Enable HTTPS
- [ ] Configure CORS properly
- [ ] Enable rate limiting
- [ ] Set up firewall rules

### Performance
- [ ] Enable Redis caching
- [ ] Configure connection pooling
- [ ] Set up CDN for static assets
- [ ] Enable gzip compression
- [ ] Configure proper resource limits

### Monitoring
- [ ] Set up Sentry error tracking
- [ ] Configure log aggregation
- [ ] Set up health checks
- [ ] Configure alerting

### Backup
- [ ] Database backup schedule
- [ ] File storage backup
- [ ] Configuration backup

---

## Scaling

### Horizontal Scaling
```yaml
# docker-compose.yml
services:
  streamlit:
    deploy:
      replicas: 3
```

### Load Balancing
Use nginx or cloud load balancer for distributing traffic.

### Database Scaling
- Read replicas for heavy read workloads
- Connection pooling with PgBouncer
- Consider managed database services

---

## Troubleshooting

### Common Issues

**Database Connection Error**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql
# Test connection
psql -h localhost -U user -d nexus_db
```

**Redis Connection Error**
```bash
# Check Redis is running
sudo systemctl status redis
# Test connection
redis-cli ping
```

**Module Import Error**
```bash
# Ensure all dependencies installed
pip install -r requirements.txt
# Check Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/nexus-platform"
```

---

## Support
- Documentation: [docs/](./docs/)
- Issues: [GitHub Issues](https://github.com/ganeshgowri-ASA/nexus-platform/issues)
- Wiki: [GitHub Wiki](https://github.com/ganeshgowri-ASA/nexus-platform/wiki)
