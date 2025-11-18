# 🚀 NEXUS Platform

> **Unified AI-powered productivity platform with 24 integrated modules** - Word, Excel, PPT, Projects, Email, Chat, Flowcharts, Analytics, Meetings & more. Built with Streamlit & Claude AI.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28.1-FF4B4B.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
- [Batch Processing Module](#-batch-processing-module)
- [API Documentation](#-api-documentation)
- [Configuration](#-configuration)
- [Development](#-development)
- [Deployment](#-deployment)
- [Contributing](#-contributing)

---

## 🎯 Overview

NEXUS Platform is a comprehensive productivity suite that combines 24 powerful modules into a single, unified interface. The platform leverages Claude AI for intelligent assistance and provides enterprise-grade features for data processing, analytics, collaboration, and more.

### Current Modules

- ⚙️ **Batch Processing** - Large-scale data processing with parallel execution
- 📊 **Analytics** - Data visualization and insights (Coming Soon)
- 📧 **Email** - Email management and automation (Coming Soon)
- 💬 **Chat** - AI-powered conversations (Coming Soon)
- ...and 20+ more modules in development

---

## ✨ Features

### Platform Features

- 🔐 **Enterprise Security** - Production-ready authentication and authorization
- 🚀 **High Performance** - Async processing with FastAPI and Celery
- 📊 **Real-time Monitoring** - Live progress tracking and notifications
- 🐳 **Docker Support** - Complete containerization for easy deployment
- 📝 **Comprehensive Logging** - Structured logging with Loguru
- 🎨 **Modern UI** - Beautiful Streamlit interface
- 🔄 **Auto-scaling** - Distributed task processing with Celery
- 💾 **PostgreSQL + Redis** - Robust data persistence and caching

---

## 🏗️ Architecture

```
NEXUS Platform
├── FastAPI Backend (Port 8000)
│   ├── RESTful API
│   ├── Database Models
│   └── Business Logic
│
├── Celery Workers
│   ├── Task Processing
│   ├── Job Scheduling
│   └── Retry Logic
│
├── Streamlit UI (Port 8501)
│   ├── Job Management
│   ├── Real-time Monitoring
│   └── Data Visualization
│
├── PostgreSQL Database
│   ├── Job Storage
│   ├── Task Tracking
│   └── Results Cache
│
└── Redis
    ├── Message Broker
    ├── Result Backend
    └── Session Cache
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (recommended)
- PostgreSQL 15+ (if not using Docker)
- Redis 7+ (if not using Docker)

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/nexus-platform.git
cd nexus-platform

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
nano .env

# Start all services
docker-compose up -d

# Initialize database
docker-compose exec api python scripts/init_db.py

# (Optional) Seed sample data
docker-compose exec api python scripts/seed_data.py
```

Access the services:
- 🎨 Streamlit UI: http://localhost:8501
- 📚 API Documentation: http://localhost:8000/docs
- 🌺 Flower (Celery Monitor): http://localhost:5555

### Option 2: Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your settings

# Start PostgreSQL and Redis
# (Use your preferred method)

# Initialize database
python scripts/init_db.py

# Start API server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start Celery worker
celery -A tasks.celery_app worker --loglevel=info

# In another terminal, start Streamlit
streamlit run ui/main.py
```

---

## 📦 Installation

### System Requirements

- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 10GB minimum
- **OS**: Linux, macOS, or Windows (with WSL2)

### Python Dependencies

All dependencies are listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

Key dependencies:
- FastAPI 0.104.1 - Web framework
- SQLAlchemy 2.0.23 - ORM
- Celery 5.3.4 - Distributed task queue
- Streamlit 1.28.1 - UI framework
- Pandas 2.1.3 - Data processing
- Redis 5.0.1 - Message broker
- PostgreSQL (psycopg2-binary) - Database

---

## 💼 Usage

### Using Makefile Commands

```bash
# Show all available commands
make help

# Install dependencies
make install

# Initialize database
make init-db

# Seed sample data
make seed-data

# Start development server
make dev

# Start Celery worker
make worker

# Start Streamlit UI
make streamlit

# Start Flower monitoring
make flower

# Build Docker images
make docker-build

# Start all Docker services
make docker-up

# Stop Docker services
make docker-down

# Run tests
make test

# Clean temporary files
make clean
```

---

## ⚙️ Batch Processing Module

The Batch Processing module is a production-ready system for processing large-scale data with parallel execution, automatic retry logic, and comprehensive monitoring.

### Features

- ✅ **Batch Job Builder** - Create jobs with custom configurations
- 📊 **CSV/Excel Import** - Import data from various file formats
- 🔄 **Data Transformation** - Apply transformations to data
- ⚡ **Parallel Execution** - Process tasks in parallel for speed
- 📈 **Progress Monitoring** - Real-time progress tracking
- 📝 **Error Logging** - Comprehensive error tracking and logs
- 🔁 **Retry Policies** - Configurable retry logic with exponential backoff
- 🔔 **Notifications** - Completion notifications (email support)

### Creating a Batch Job

#### Via API

```python
import requests

# Create a batch job
job_data = {
    "name": "My Batch Job",
    "description": "Process customer data",
    "job_type": "csv_import",
    "config": {
        "chunk_size": 100,
        "parallel_workers": 4,
        "max_retries": 3
    }
}

response = requests.post(
    "http://localhost:8000/api/v1/batch/jobs",
    json=job_data
)

job = response.json()
print(f"Created job: {job['id']}")

# Start the job
requests.post(f"http://localhost:8000/api/v1/batch/jobs/{job['id']}/start")

# Monitor progress
progress = requests.get(f"http://localhost:8000/api/v1/batch/jobs/{job['id']}/progress")
print(f"Progress: {progress.json()['progress_percentage']}%")
```

#### Via Streamlit UI

1. Navigate to **Batch Processing** page
2. Click **Create Job** tab
3. Fill in job details
4. Upload data file (CSV/Excel)
5. Configure advanced options
6. Click **Create Job**
7. Monitor progress in real-time

### Data Import & Transformation

```python
from modules.batch_processing.utils import FileImporter, DataTransformer

# Import CSV file
df = FileImporter.import_csv(
    "data/customers.csv",
    delimiter=",",
    has_header=True
)

# Apply transformations
transformations = [
    {
        "source_column": "name",
        "target_column": "name_upper",
        "transformation_type": "uppercase"
    },
    {
        "source_column": "email",
        "target_column": "email_lower",
        "transformation_type": "lowercase"
    }
]

df_transformed = DataTransformer.apply_transformations(df, transformations)

# Export results
from modules.batch_processing.utils import DataExporter
DataExporter.export_to_excel(df_transformed, "output/results.xlsx")
```

### Monitoring & Management

#### Real-time Progress

```python
# Get job progress
GET /api/v1/batch/jobs/{job_id}/progress

# Response
{
    "job_id": 123,
    "status": "running",
    "progress_percentage": 45.5,
    "processed_items": 455,
    "total_items": 1000,
    "successful_items": 450,
    "failed_items": 5,
    "estimated_completion": "2024-01-15T10:30:00Z"
}
```

#### Error Handling

```python
# Get error logs
GET /api/v1/batch/jobs/{job_id}/errors

# Retry failed tasks
POST /api/v1/batch/jobs/{job_id}/retry

# Cancel running job
POST /api/v1/batch/jobs/{job_id}/cancel
```

---

## 📚 API Documentation

### Batch Processing Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/batch/jobs` | Create a new batch job |
| `GET` | `/api/v1/batch/jobs` | List all batch jobs |
| `GET` | `/api/v1/batch/jobs/{id}` | Get specific job details |
| `PATCH` | `/api/v1/batch/jobs/{id}` | Update a batch job |
| `DELETE` | `/api/v1/batch/jobs/{id}` | Delete a batch job |
| `POST` | `/api/v1/batch/jobs/{id}/start` | Start job processing |
| `POST` | `/api/v1/batch/jobs/{id}/cancel` | Cancel a running job |
| `POST` | `/api/v1/batch/jobs/{id}/retry` | Retry failed tasks |
| `GET` | `/api/v1/batch/jobs/{id}/progress` | Get real-time progress |
| `GET` | `/api/v1/batch/jobs/{id}/tasks` | List job tasks |
| `GET` | `/api/v1/batch/jobs/{id}/errors` | Get error logs |
| `GET` | `/api/v1/batch/stats` | Get statistics |

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Application
APP_NAME=NEXUS Platform
DEBUG=False
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://nexus_user:nexus_password@localhost:5432/nexus_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Claude AI
CLAUDE_API_KEY=your-claude-api-key-here
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Batch Processing
MAX_BATCH_SIZE=10000
MAX_RETRY_ATTEMPTS=3
BATCH_CHUNK_SIZE=100
PARALLEL_WORKERS=4

# File Upload
MAX_FILE_SIZE_MB=100
ALLOWED_EXTENSIONS=csv,xlsx,xls,json
```

---

## 🛠️ Development

### Project Structure

```
nexus-platform/
├── api/                    # FastAPI application
│   ├── main.py            # Application entry point
│   └── middleware/        # Custom middleware
├── core/                  # Core utilities
│   ├── config.py         # Configuration
│   └── logging.py        # Logging setup
├── database/             # Database layer
│   ├── connection.py    # DB connection
│   └── models/          # SQLAlchemy models
├── modules/             # Feature modules
│   └── batch_processing/
│       ├── routes.py    # API endpoints
│       ├── service.py   # Business logic
│       ├── tasks.py     # Celery tasks
│       ├── schemas.py   # Pydantic models
│       ├── utils.py     # Utilities
│       └── exceptions.py # Custom exceptions
├── tasks/               # Celery configuration
│   └── celery_app.py   # Celery app
├── ui/                  # Streamlit UI
│   ├── main.py         # Main UI app
│   └── pages/          # UI pages
├── scripts/            # Utility scripts
│   ├── init_db.py     # Database init
│   └── seed_data.py   # Sample data
├── tests/             # Test suite
├── docker-compose.yml # Docker composition
├── Dockerfile        # Docker image
├── requirements.txt  # Dependencies
├── Makefile         # Common commands
└── README.md        # This file
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
pytest tests/ -v --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_batch_processing.py -v
```

### Code Quality

```bash
# Format code
make format

# Run linters
make lint

# Type checking
mypy .
```

---

## 🚀 Deployment

### Production Deployment with Docker

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Start production services
docker-compose -f docker-compose.prod.yml up -d

# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale celery-worker=4
```

### Environment-specific Configuration

- Development: `.env.dev`
- Staging: `.env.staging`
- Production: `.env.prod`

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Worker health (via Flower)
curl http://localhost:5555/api/workers
```

---

## 📊 Monitoring

### Flower (Celery Monitoring)

Access Flower dashboard at http://localhost:5555

Features:
- Real-time worker monitoring
- Task progress tracking
- Task history and statistics
- Worker management

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api
docker-compose logs -f celery-worker

# Application logs (local)
tail -f logs/nexus_*.log
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Write unit tests for new features
- Update documentation
- Keep commits atomic and descriptive

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Streamlit](https://streamlit.io/) - Beautiful UI framework
- [Celery](https://docs.celeryq.dev/) - Distributed task queue
- [Claude AI](https://www.anthropic.com/) - AI assistance
- [PostgreSQL](https://www.postgresql.org/) - Robust database
- [Redis](https://redis.io/) - In-memory data store

---

## 📞 Support

For issues, questions, or contributions:

- 📧 Email: support@nexus-platform.com
- 💬 Discord: [Join our community](https://discord.gg/nexus)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/nexus-platform/issues)

---

## 🗺️ Roadmap

### Q1 2024
- ✅ Batch Processing Module
- 🔄 Analytics Dashboard
- 🔄 Email Integration

### Q2 2024
- 📅 Calendar & Meetings
- 📊 Advanced Analytics
- 🔐 Enhanced Security

### Future
- 🤖 AI-powered automation
- 📱 Mobile app
- 🌐 Multi-language support
- 🔌 Plugin system

---

<div align="center">

**Built with ❤️ by the NEXUS Team**

[Website](https://nexus-platform.com) • [Documentation](https://docs.nexus-platform.com) • [Blog](https://blog.nexus-platform.com)

</div>
