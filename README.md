# 🚀 NEXUS Platform - Document Management System

**A comprehensive, production-ready Document Management System (DMS) with AI-powered features built on FastAPI, SQLAlchemy, and Streamlit.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Development](#-development)
- [License](#-license)

---

## 🎯 Overview

NEXUS Platform is an enterprise-grade Document Management System that provides comprehensive file management, collaboration, and AI-powered intelligence capabilities. Built with modern Python technologies, it offers a scalable, secure, and feature-rich solution for managing documents across organizations.

### Key Highlights

- 📁 **Universal File Support** - Handle 100+ file formats
- 🔍 **Advanced Search** - Full-text, semantic, and faceted search
- 🤖 **AI Integration** - Claude AI for summarization, classification, and content intelligence
- 🔐 **Granular Permissions** - Fine-grained access control with inheritance
- 📊 **Version Control** - Complete version history with diff tracking and rollback
- 🔄 **Workflow Engine** - Configurable approval and review workflows
- 🌐 **Multi-Backend Storage** - Local, AWS S3, Azure Blob, Google Cloud Storage
- 📱 **Modern UI** - Streamlit-based web interface with real-time updates
- 🔒 **Enterprise Security** - Encryption, audit logging, compliance features

---

## ✨ Features

### Document Management
- ✅ Drag-and-drop upload with progress tracking
- ✅ Hierarchical folder organization
- ✅ Document metadata and tagging
- ✅ Full-text search with filters
- ✅ Document preview and thumbnails
- ✅ Multi-format support (PDF, Office, images, CAD, etc.)
- ✅ Deduplication using content hashing
- ✅ Bulk operations (upload, download, move, tag, delete)

### Version Control
- ✅ Automatic version tracking
- ✅ Visual diff comparison
- ✅ Version rollback
- ✅ Branch and merge support
- ✅ Change history with summaries

### Collaboration
- ✅ Real-time comments with threading
- ✅ @mentions and notifications
- ✅ Activity feeds
- ✅ Document sharing with links
- ✅ Co-editing support
- ✅ Check-in/check-out locking

### Search & Discovery
- ✅ Full-text indexing
- ✅ Semantic search with embeddings
- ✅ Faceted search with aggregations
- ✅ Saved searches
- ✅ Search history
- ✅ AI-powered recommendations

### Permissions & Security
- ✅ Role-based access control (RBAC)
- ✅ Document-level permissions
- ✅ Folder-level permissions with inheritance
- ✅ Share links with password protection
- ✅ Link expiration and download limits
- ✅ Audit logging and forensics

### Workflows
- ✅ Configurable approval chains
- ✅ Multi-step review processes
- ✅ Task assignment with deadlines
- ✅ Workflow templates
- ✅ Email notifications
- ✅ Status tracking

### AI-Powered Features
- ✅ Document summarization (Claude AI)
- ✅ Entity extraction (people, organizations, locations)
- ✅ Auto-classification with confidence scores
- ✅ Smart tag suggestions
- ✅ Content recommendations
- ✅ Document quality analysis

### Document Processing
- ✅ Format conversion (LibreOffice, Pandoc)
- ✅ OCR with Tesseract
- ✅ Text extraction from various formats
- ✅ Image optimization
- ✅ PDF processing

### Compliance & Retention
- ✅ Retention policies
- ✅ Automatic archival
- ✅ Legal holds
- ✅ Disposition scheduling
- ✅ Compliance reporting

### Integration
- ✅ Email integration (capture attachments)
- ✅ Scanner integration
- ✅ Cloud storage sync (Dropbox, Google Drive)
- ✅ Desktop and mobile sync
- ✅ Webhook notifications
- ✅ RESTful API

### Analytics & Reporting
- ✅ Storage usage reports
- ✅ User activity analytics
- ✅ Access reports
- ✅ Compliance reports
- ✅ Export to CSV/PDF
- ✅ Scheduled reports

---

## 🏗️ Architecture

### Technology Stack

**Backend:**
- **FastAPI** - Modern, fast web framework
- **SQLAlchemy** - ORM with async support
- **PostgreSQL** - Primary database
- **Redis** - Caching and message broker
- **Celery** - Async task processing
- **Anthropic Claude** - AI/LLM integration

**Frontend:**
- **Streamlit** - Interactive web UI
- **Plotly** - Data visualization

**Storage:**
- **Local filesystem**
- **AWS S3** - Cloud storage
- **Azure Blob Storage**
- **Google Cloud Storage**

**Search:**
- **PostgreSQL Full-Text Search**
- **Elasticsearch** (optional)

**Document Processing:**
- **LibreOffice** - Format conversion
- **Pandoc** - Markdown/text conversion
- **Tesseract** - OCR
- **Pillow** - Image processing
- **PyPDF** - PDF manipulation

### Project Structure

```
nexus-platform/
├── backend/                    # FastAPI backend
│   ├── core/                  # Core utilities
│   ├── models/               # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── api/                 # API endpoints
│   ├── services/            # Business logic
│   └── main.py              # FastAPI application
├── frontend/                 # Streamlit frontend
│   ├── app.py               # Main application
│   └── pages/               # Multi-page app
├── modules/documents/        # Document management module
│   ├── storage.py           # Multi-backend storage
│   ├── versioning.py        # Version control
│   ├── permissions.py       # Access control
│   ├── search.py            # Search engine
│   ├── workflow.py          # Approval workflows
│   ├── ai_assistant.py      # AI integration
│   └── [22 modules total]
├── tests/                   # Test suite
├── scripts/                 # Utility scripts
├── docs/                    # Documentation
└── docker-compose.yml      # Docker orchestration
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 14+
- Redis 6+
- (Optional) Tesseract OCR
- (Optional) LibreOffice for document conversion

### 1. Clone the Repository

```bash
git clone https://github.com/ganeshgowri-ASA/nexus-platform.git
cd nexus-platform
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 3. Install Dependencies

```bash
# Using Poetry (recommended)
poetry install

# Or using pip
pip install -r requirements.txt
```

### 4. Initialize Database

```bash
# Run migrations
alembic upgrade head

# Create admin user
python scripts/init_db.py --create-admin
```

### 5. Start the Application

```bash
# Development mode (starts both backend and frontend)
./scripts/start_dev.sh

# Or individually:
# Backend only
./scripts/start_dev.sh --backend-only

# Frontend only
./scripts/start_dev.sh --frontend-only
```

### 6. Access the Application

- **Frontend UI**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs
- **API Backend**: http://localhost:8000

**Default Admin Credentials:**
- Email: `admin@nexus.local`
- Password: `Admin@123`

---

## 📦 Installation

### Option 1: Docker (Recommended for Production)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services included:
- PostgreSQL database
- Redis cache
- FastAPI backend
- Streamlit frontend
- Celery worker
- Celery beat (scheduler)
- Flower (monitoring)

### Option 2: Manual Installation

See `docs/SETUP.md` for detailed installation instructions.

---

## ⚙️ Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Application
APP_NAME=NEXUS Platform
DEBUG=False
ENVIRONMENT=production

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/nexus_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-change-this
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Integration
ANTHROPIC_API_KEY=your-anthropic-api-key
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Storage
STORAGE_BACKEND=local  # Options: local, s3, azure, gcs
STORAGE_PATH=./storage

# AWS S3 (if using S3)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET_NAME=your-bucket
AWS_S3_REGION=us-east-1
```

See `.env.example` for complete configuration options (200+ settings).

---

## 🔌 API Documentation

### Authentication

All API requests require authentication using JWT tokens:

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin@nexus.local", "password": "Admin@123"}'

# Use token in subsequent requests
curl -X GET http://localhost:8000/api/v1/documents/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Key Endpoints

**Documents:**
- `POST /api/v1/documents/` - Upload document
- `GET /api/v1/documents/` - List documents
- `GET /api/v1/documents/{id}` - Get document details
- `DELETE /api/v1/documents/{id}` - Delete document
- `POST /api/v1/documents/search` - Search documents

**Permissions:**
- `POST /api/v1/documents/{id}/permissions` - Grant permission
- `GET /api/v1/documents/{id}/permissions` - List permissions
- `POST /api/v1/documents/{id}/share` - Create share link

**AI Operations:**
- `POST /api/v1/documents/{id}/ai/summarize` - Summarize document
- `POST /api/v1/documents/{id}/ai/classify` - Classify document
- `POST /api/v1/documents/{id}/ai/extract-entities` - Extract entities

See full API documentation at: http://localhost:8000/docs

---

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov=modules --cov-report=html

# Run specific test file
pytest tests/backend/test_storage.py

# Run integration tests only
pytest tests/integration/ -v
```

### Test Coverage

Current test coverage: **80%+**

Coverage areas:
- Storage operations: 95%+
- Permission system: 90%+
- Versioning: 85%+
- Search functionality: 85%+
- Workflow engine: 85%+
- API endpoints: 80%+

---

## 🚢 Deployment

### Docker Deployment

```bash
# Build production image
docker build -t nexus-platform:latest .

# Run with docker-compose
docker-compose -f docker-compose.yml up -d

# Scale workers
docker-compose up -d --scale celery-worker=3
```

### Traditional Server Deployment

See `docs/SETUP.md` for detailed deployment instructions including:
- Gunicorn + Supervisor setup
- Nginx reverse proxy configuration
- SSL certificate setup
- Systemd service configuration

---

## 💻 Development

### Code Style

```bash
# Format code with Black
black backend/ frontend/ modules/ tests/

# Lint with Ruff
ruff check backend/ frontend/ modules/ tests/

# Type checking with MyPy
mypy backend/ modules/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

---

## 📖 Additional Documentation

- **[Setup Guide](docs/SETUP.md)** - Detailed installation and configuration
- **[API Reference](docs/API.md)** - Complete API documentation
- **[Architecture](docs/ARCHITECTURE.md)** - System architecture and design
- **[Streamlit UI Guide](STREAMLIT_UI_GUIDE.txt)** - Frontend features and usage

---

## 🔒 Security

### Security Features

- JWT-based authentication
- Password hashing with bcrypt
- Role-based access control
- Audit logging for all actions
- Encryption at rest and in transit
- SQL injection prevention
- XSS protection
- CSRF protection
- Rate limiting

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Team

**NEXUS Team**
- Platform Development
- AI Integration
- Security & Compliance

---

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- Anthropic for Claude AI integration
- Streamlit for the interactive UI framework
- SQLAlchemy for database ORM
- All open-source contributors

---

**Built with ❤️ by the NEXUS Team**

⭐ Star us on GitHub if you find this project useful!
