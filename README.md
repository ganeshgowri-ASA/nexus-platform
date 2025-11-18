# NEXUS Platform

NEXUS: Unified AI-powered productivity platform with integrated ETL and Integration Hub modules. Built with FastAPI, PostgreSQL, Redis, Celery, and Streamlit.

## 🚀 Overview

NEXUS provides two powerful modules:

1. **ETL Module**: Extract, Transform, Load data from multiple sources with validation and scheduling
2. **Integration Hub**: Third-party integrations with OAuth, webhooks, and data synchronization

## 📦 Modules

### 1. ETL Module (`modules/etl/`)

Extract, transform, and load data from various sources with comprehensive data quality features.

#### Features:
- **Source Connectors**: CSV, JSON, SQL, PostgreSQL, MySQL, REST APIs
- **Transformations**: 20+ transformation types (filter, map, aggregate, join, etc.)
- **Data Validation**: NOT_NULL, UNIQUE, RANGE, REGEX, TYPE_CHECK, etc.
- **Deduplication**: Exact, fuzzy, and hash-based deduplication
- **Scheduling**: Cron-based and interval-based pipeline execution
- **Monitoring**: Execution history, metrics, and logs

#### API Endpoints:
- `/api/v1/sources` - Data source management
- `/api/v1/pipelines` - ETL pipeline configuration
- `/api/v1/transformations` - Transformation templates
- `/api/v1/jobs` - Scheduled jobs
- `/api/v1/executions` - Execution history

#### Streamlit UI:
Access at `http://localhost:8501`

### 2. Integration Hub (`modules/integration_hub/`)

Manage third-party integrations with OAuth 2.0, API keys, webhooks, and data sync.

#### Features:
- **OAuth 2.0 Flows**: Complete OAuth implementation with token refresh
- **API Key Management**: Encrypted storage and rotation
- **Webhook Handling**: Event-driven webhooks with retry logic
- **Data Synchronization**: Bi-directional sync with field mapping
- **Rate Limiting**: Redis-based rate limiting per integration
- **Integration Marketplace**: Pre-built connectors (coming soon)

#### API Endpoints:
- `/api/v1/integrations` - Available integrations
- `/api/v1/api-keys` - API key management
- `/api/v1/oauth` - OAuth flows
- `/api/v1/webhooks` - Webhook configuration
- `/api/v1/sync` - Data sync configuration

#### Streamlit UI:
Access at `http://localhost:8502`

## 🛠️ Technology Stack

- **Backend**: FastAPI 0.109.0
- **Database**: PostgreSQL 16
- **Cache/Queue**: Redis 7
- **Task Queue**: Celery 5.3.6
- **Data Processing**: pandas 2.2.0, numpy 1.26.3
- **UI**: Streamlit 1.30.0
- **Authentication**: OAuth 2.0 (authlib), JWT
- **Security**: Encryption (cryptography), password hashing (passlib)

## 📋 Prerequisites

- Docker and Docker Compose
- Python 3.11+
- PostgreSQL 16
- Redis 7

## 🚀 Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd nexus-platform
```

2. Create environment file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start all services:
```bash
docker-compose up -d
```

4. Run database migrations:
```bash
docker-compose exec etl-api alembic upgrade head
```

5. Access the services:
- ETL API: http://localhost:8001/docs
- Integration Hub API: http://localhost:8002/docs
- ETL UI: http://localhost:8501
- Integration Hub UI: http://localhost:8502
- Flower (Celery monitoring): http://localhost:5555

## 🏗️ Architecture

```
nexus-platform/
├── modules/
│   ├── etl/                      # ETL Module
│   │   ├── api/                  # FastAPI routes
│   │   ├── connectors/           # Data source connectors
│   │   ├── core/                 # Celery tasks, constants
│   │   ├── models/               # SQLAlchemy models
│   │   ├── schemas/              # Pydantic schemas
│   │   ├── services/             # Business logic
│   │   └── ui/                   # Streamlit UI
│   └── integration_hub/          # Integration Hub Module
│       ├── api/                  # FastAPI routes
│       ├── core/                 # Celery tasks
│       ├── integrations/         # Pre-built connectors
│       ├── models/               # SQLAlchemy models
│       ├── schemas/              # Pydantic schemas
│       ├── services/             # OAuth, webhooks, sync
│       └── ui/                   # Streamlit UI
├── shared/                       # Shared utilities
│   ├── database/                 # Database configuration
│   ├── security/                 # Auth & encryption
│   └── utils/                    # Logger, Redis client
├── alembic/                      # Database migrations
├── scripts/                      # Utility scripts
├── docker-compose.yml            # Docker orchestration
├── Dockerfile                    # Container image
└── requirements.txt              # Python dependencies
```

## 🔒 Security

- **Encryption**: All sensitive data (OAuth tokens, API keys) is encrypted using Fernet
- **Password Hashing**: Bcrypt for password storage
- **JWT**: Secure API authentication
- **Rate Limiting**: Redis-based rate limiting
- **Webhook Signatures**: HMAC-SHA256 verification

## 📝 License

This project is licensed under the MIT License.

---

**Version**: 0.1.0
**Built with**: FastAPI, PostgreSQL, Redis, Celery, pandas, Streamlit
