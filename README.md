# NEXUS Platform

> **Unified AI-powered productivity platform with 24 integrated modules including advanced Analytics**

NEXUS is a production-ready platform built with **Python**, **FastAPI**, **Streamlit**, **PostgreSQL**, **Redis**, **Celery**, and **Claude AI** integration. The platform features a comprehensive analytics module with real-time tracking, predictive insights, and intelligent automation.

[![CI/CD Pipeline](https://github.com/ganeshgowri-ASA/nexus-platform/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/ganeshgowri-ASA/nexus-platform/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Analytics Module](#analytics-module)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)

---

## Features

### Platform Modules (24 Integrated Modules)

- **Word Processing** - Document creation and editing
- **Excel** - Spreadsheet analysis and manipulation
- **PowerPoint** - Presentation creation
- **Projects** - Project management and tracking
- **Email** - Email management and automation
- **Chat** - Real-time messaging with AI assistance
- **Flowcharts** - Diagram and flowchart creation
- **Analytics** - **Comprehensive analytics and insights** ⭐
- **Meetings** - Meeting scheduling and management
- **Calendar** - Event and schedule management
- **Tasks** - Task tracking and automation
- **Notes** - Note-taking and organization
- **Files** - Document storage and management
- **Contacts** - Contact management
- **Reports** - Custom report generation
- And more...

### Analytics Module Features ⭐

#### Core Analytics
- **Real-time Event Tracking** - Track all user interactions instantly
- **User Behavior Analysis** - Deep insights into user patterns
- **Session Management** - Complete session lifecycle tracking
- **Funnel Analysis** - Multi-step conversion tracking with drop-off analysis
- **Cohort Analysis** - User retention and engagement over time
- **Goal Tracking** - Monitor conversion goals and KPIs
- **A/B Testing** - Statistical testing framework with confidence intervals

#### Advanced Features
- **Multi-channel Attribution** - 5 attribution models (first-touch, last-touch, linear, time-decay, position-based)
- **Predictive Analytics** - ML-powered churn prediction, LTV forecasting, engagement scoring
- **AI-Powered Insights** - Claude AI integration for anomaly detection and recommendations
- **Custom Dashboards** - Build personalized analytics dashboards
- **Data Visualization** - Interactive charts (Plotly), heatmaps, funnels
- **Session Replay** - Record and replay user sessions
- **Real-time Processing** - Celery-based async processing pipeline
- **Data Export** - CSV, JSON, Excel, PDF export with custom reports

#### Technical Capabilities
- **Time-series Database** - TimescaleDB for high-performance analytics
- **Caching Layer** - Redis for real-time data access
- **REST API** - Comprehensive FastAPI endpoints
- **Streamlit Dashboard** - Interactive UI for data exploration
- **Production-Ready** - Full logging, error handling, monitoring

---

## Architecture

```
NEXUS Platform Architecture
│
├── Frontend Layer
│   ├── Streamlit Dashboard (Port 8501)
│   └── Custom UI Components
│
├── API Layer
│   ├── FastAPI REST API (Port 8000)
│   ├── Authentication & Authorization
│   ├── Rate Limiting
│   └── API Documentation (Swagger/OpenAPI)
│
├── Processing Layer
│   ├── Celery Workers (Async Tasks)
│   ├── Celery Beat (Scheduled Jobs)
│   └── Flower Monitoring (Port 5555)
│
├── Storage Layer
│   ├── PostgreSQL + TimescaleDB (Port 5432)
│   ├── Redis Cache (Port 6379)
│   └── InfluxDB Time-series (Port 8086)
│
└── AI Layer
    ├── Claude AI Integration
    └── Predictive ML Models
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend Framework** | FastAPI | High-performance REST API |
| **UI Framework** | Streamlit | Interactive dashboards |
| **Database** | PostgreSQL + TimescaleDB | Analytics data storage |
| **Cache** | Redis | Real-time data & task queue |
| **Task Queue** | Celery | Async processing |
| **Time Series** | InfluxDB | High-frequency metrics |
| **AI** | Claude (Anthropic) | Intelligent insights |
| **ML** | scikit-learn, Prophet | Predictive analytics |
| **Visualization** | Plotly, Altair | Interactive charts |
| **ORM** | SQLAlchemy | Database abstraction |
| **Validation** | Pydantic | Data validation |
| **Testing** | pytest, pytest-asyncio | Test suite |
| **Containerization** | Docker, Docker Compose | Deployment |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/ganeshgowri-ASA/nexus-platform.git
cd nexus-platform

# Run setup script
./scripts/setup.sh

# Or manual setup
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your configuration
```

### Running with Docker (Recommended)

```bash
# Start all services
make docker-up

# Or using docker-compose directly
docker-compose up -d

# Initialize database
make init-db

# View logs
make docker-logs

# Check service health
make health
```

### Running Locally

```bash
# Terminal 1: Start API server
make api

# Terminal 2: Start Streamlit dashboard
make dashboard

# Terminal 3: Start Celery worker
make celery

# Terminal 4: Start Celery beat scheduler
python app.py celery-beat

# Terminal 5: Start Flower monitoring
make flower
```

### Access Points

- **Streamlit Dashboard**: http://localhost:8501
- **FastAPI Docs**: http://localhost:8000/docs
- **Flower Monitoring**: http://localhost:5555
- **InfluxDB UI**: http://localhost:8086

---

## Analytics Module

### Quick Start

```python
from modules.analytics.core.tracker import EventTracker
from modules.analytics.models.event import EventCreate
from shared.constants import EventType

# Initialize tracker
tracker = EventTracker()

# Track an event
event = EventCreate(
    name="page_view",
    event_type=EventType.PAGE_VIEW,
    properties={
        "page": "/home",
        "title": "Home Page"
    },
    user_id="user_123",
    session_id="session_456"
)

tracker.track(event)
```

### Funnel Analysis

```python
from modules.analytics.processing.funnel import FunnelEngine
from modules.analytics.models.funnel import FunnelCreate, FunnelStepCreate
from shared.constants import EventType

# Create funnel
funnel = FunnelCreate(
    name="Signup Funnel",
    steps=[
        FunnelStepCreate(name="Landing", event_type=EventType.PAGE_VIEW, order=0),
        FunnelStepCreate(name="Form Start", event_type=EventType.FORM_START, order=1),
        FunnelStepCreate(name="Form Submit", event_type=EventType.FORM_SUBMIT, order=2),
        FunnelStepCreate(name="Conversion", event_type=EventType.CONVERSION, order=3),
    ]
)

# Analyze funnel
engine = FunnelEngine(db)
analysis = await engine.analyze_funnel(
    funnel_id="funnel_id",
    start_date=start_date,
    end_date=end_date
)

print(f"Conversion Rate: {analysis.overall_conversion_rate:.2%}")
```

### AI-Powered Insights

```python
from modules.analytics.processing.ai_insights import get_ai_insights_engine

# Get insights engine
ai_engine = get_ai_insights_engine()

# Detect anomalies
anomalies = await ai_engine.detect_anomalies(
    metric_data=data,
    metric_name="daily_active_users",
    context={"product": "nexus"}
)

# Get optimization recommendations
recommendations = await ai_engine.recommend_optimizations(
    funnel_data=funnel_performance,
    goal_data=goal_conversions
)
```

### Dashboard Integration

The Streamlit dashboard provides:

1. **Overview Dashboard** - Key metrics, trends, real-time stats
2. **Funnels** - Conversion funnel visualization and analysis
3. **Cohorts** - Retention heatmaps and cohort analysis
4. **A/B Tests** - Experiment tracking and statistical analysis
5. **Reports** - Custom report builder and export
6. **Insights** - AI-powered recommendations and anomaly alerts

---

## API Documentation

### Authentication

```bash
# Get API token (if auth enabled)
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'
```

### Event Tracking

```bash
# Track single event
curl -X POST http://localhost:8000/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "name": "button_click",
    "event_type": "button_click",
    "user_id": "user_123",
    "properties": {"button": "signup"}
  }'

# Track batch events
curl -X POST http://localhost:8000/api/v1/events/batch \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {"name": "page_view", "event_type": "page_view"},
      {"name": "button_click", "event_type": "button_click"}
    ]
  }'
```

### Analytics Queries

```bash
# Get funnel analysis
curl http://localhost:8000/api/v1/analytics/funnels/{funnel_id}/analysis

# Get cohort retention
curl http://localhost:8000/api/v1/analytics/cohorts/{cohort_id}/retention

# Get dashboard overview
curl http://localhost:8000/api/v1/dashboards/overview?period=last_30_days

# Export data
curl http://localhost:8000/api/v1/exports/events?format=csv
```

Full API documentation available at: http://localhost:8000/docs

---

## Development

### Project Structure

```
nexus-platform/
├── modules/
│   └── analytics/          # Analytics module
│       ├── api/           # FastAPI routes
│       ├── core/          # Core logic (tracker, aggregator, processor)
│       ├── models/        # Pydantic models
│       ├── storage/       # Database & cache
│       ├── processing/    # Celery tasks & engines
│       ├── export/        # Data export
│       ├── ui/            # Streamlit dashboard
│       ├── config/        # Configuration
│       └── tests/         # Test suite (305+ tests)
├── shared/                # Shared utilities
│   ├── config.py         # Configuration management
│   ├── logger.py         # Logging setup
│   ├── constants.py      # Global constants
│   └── utils.py          # Utility functions
├── scripts/              # Setup & deployment scripts
├── alembic/              # Database migrations
├── .github/              # CI/CD workflows
├── app.py               # Main entry point
├── docker-compose.yml   # Docker orchestration
├── Makefile             # Common commands
└── pyproject.toml       # Project configuration
```

### Makefile Commands

```bash
# Development
make install           # Install dependencies
make dev              # Install dev dependencies
make init-db          # Initialize database
make api              # Run API server
make dashboard        # Run Streamlit dashboard
make celery           # Run Celery worker

# Testing & Quality
make test             # Run test suite
make test-cov         # Run with coverage
make lint             # Run linters
make format           # Format code

# Docker
make docker-build     # Build images
make docker-up        # Start services
make docker-down      # Stop services
make docker-logs      # View logs

# Database
make migrate          # Run migrations
make migration        # Create new migration

# Utilities
make health           # Health check
make version          # Show version
make clean            # Clean generated files
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
pytest modules/analytics/tests/unit/test_tracker.py -v

# Run integration tests
make test-integration

# Run in parallel
pytest modules/analytics/tests/ -n auto
```

**Test Coverage**: 305+ tests with 80%+ coverage

---

## Deployment

### Production Deployment

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy to production
make deploy-prod

# Or step by step
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head
```

### Environment Variables

Key environment variables (see `.env.example` for full list):

```bash
# Application
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Redis
REDIS_URL=redis://host:6379/0

# AI
CLAUDE_API_KEY=sk-ant-your-key
AI_MODEL=claude-3-5-sonnet-20241022

# Features
FEATURE_PREDICTIVE_ANALYTICS=true
FEATURE_AB_TESTING=true
ANALYTICS_ENABLED=true
```

### Monitoring

- **Flower**: Celery task monitoring at port 5555
- **Prometheus**: Metrics at `/metrics` endpoint
- **Logging**: Structured JSON logs in production
- **Health Checks**: `/health` endpoint

---

## Performance

### Benchmarks

- **Event Ingestion**: 10,000+ events/minute
- **API Response Time**: <100ms (p95)
- **Dashboard Load Time**: <2s
- **Batch Processing**: 1M+ events/hour

### Optimization

- Connection pooling (20 connections)
- Redis caching (TTL-based)
- Database indexing on key columns
- Async processing with Celery
- Query optimization with SQLAlchemy
- TimescaleDB for time-series data

---

## Contributing

We welcome contributions! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Write comprehensive docstrings
- Add unit tests for new features
- Update documentation
- Run linters before committing (`make lint`)

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Support

- **Documentation**: See `/docs` folder
- **Issues**: [GitHub Issues](https://github.com/ganeshgowri-ASA/nexus-platform/issues)
- **Email**: support@nexus-platform.com

---

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- UI powered by [Streamlit](https://streamlit.io/)
- AI by [Anthropic Claude](https://www.anthropic.com/)
- Analytics inspired by best practices from Mixpanel, Amplitude, and Google Analytics

---

**Made with ❤️ by the NEXUS Team**
