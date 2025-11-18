# NEXUS Scheduler Module

Advanced task scheduling system with cron, calendar-based scheduling, timezone support, and comprehensive job management.

## 🌟 Features

### Core Scheduling
- **Cron Scheduling**: Traditional cron expressions with visual builder
- **Interval Scheduling**: Run jobs at fixed intervals
- **Date Scheduling**: One-time job execution at specific dates
- **Calendar-Based Scheduling**: Advanced calendar rules

### Management & Monitoring
- **Visual Cron Builder**: User-friendly interface for creating cron expressions
- **Calendar Picker**: Visual calendar view of scheduled jobs
- **Task Queue**: Real-time job queue monitoring
- **Execution History**: Complete audit trail of all job executions
- **Retry Logic**: Automatic retry with exponential backoff
- **Notifications**: Multi-channel notifications (Email, Telegram, Webhook)

### Advanced Features
- **Timezone Support**: Full timezone conversion and scheduling
- **Job Dependencies**: Define job workflows and dependencies
- **Priority Queue**: Job prioritization (1-10)
- **Metadata & Tags**: Organize jobs with tags and metadata
- **Real-time Monitoring**: Dashboard with statistics and metrics

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit UI                          │
│  Dashboard │ Jobs │ Calendar │ History │ Notifications  │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Backend                        │
│         Jobs API │ Cron API │ Stats API                 │
└──────────┬──────────────────────────────┬───────────────┘
           │                              │
           ▼                              ▼
┌──────────────────────┐       ┌──────────────────────┐
│  APScheduler Engine  │       │   Celery Workers     │
│  - Job Registration  │       │   - Task Execution   │
│  - Trigger Management│       │   - Retry Logic      │
└──────────┬───────────┘       └──────────┬───────────┘
           │                              │
           ▼                              ▼
┌─────────────────────────────────────────────────────────┐
│                      Redis                               │
│         Job Store │ Message Queue │ Result Backend      │
└─────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────┐
│                    PostgreSQL                            │
│      Jobs │ Executions │ Notifications │ Dependencies   │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL 15+
- Redis 7+

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd nexus-platform
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start with Docker**
```bash
# Using provided script
./scripts/start.sh

# Or using Make
make up

# Or using Docker Compose directly
docker-compose up -d
```

4. **Access the application**
- **API Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Streamlit UI**: http://localhost:8501

## 📖 Usage

### Creating a Job via UI

1. Navigate to **Create Job** in the sidebar
2. Fill in basic information:
   - Job name
   - Description
   - Task name
3. Choose schedule type:
   - **Cron**: Use visual builder or presets
   - **Interval**: Set interval value and unit
   - **Date**: Pick specific date and time
   - **Calendar**: Define custom calendar rules
4. Configure retry settings and priority
5. Click **Create Job**

### Creating a Job via API

```python
import httpx

job_data = {
    "name": "Daily Report",
    "description": "Generate daily analytics report",
    "job_type": "cron",
    "cron_expression": "0 9 * * 1-5",  # Weekdays at 9 AM
    "task_name": "tasks.generate_report",
    "timezone": "US/Eastern",
    "is_active": True,
    "max_retries": 3,
    "retry_delay": 60,
    "priority": 7,
    "tags": ["report", "analytics"],
    "task_args": [],
    "task_kwargs": {"format": "pdf"}
}

response = httpx.post("http://localhost:8000/api/v1/jobs/", json=job_data)
print(response.json())
```

### Cron Expression Examples

```bash
# Every minute
* * * * *

# Every 5 minutes
*/5 * * * *

# Every hour
0 * * * *

# Daily at midnight
0 0 * * *

# Weekdays at 9 AM
0 9 * * 1-5

# First day of month
0 0 1 * *

# Every Monday at 8:30 AM
30 8 * * 1
```

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/nexus_scheduler
DATABASE_URL_SYNC=postgresql://user:pass@localhost:5432/nexus_scheduler

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Scheduler
DEFAULT_TIMEZONE=UTC
MAX_RETRY_ATTEMPTS=3
TASK_TIMEOUT=3600
ENABLE_SCHEDULER=true

# Notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-password
TELEGRAM_BOT_TOKEN=your-bot-token
```

## 📊 API Reference

### Jobs API

#### Create Job
```http
POST /api/v1/jobs/
Content-Type: application/json

{
  "name": "string",
  "job_type": "cron|interval|date|calendar",
  "cron_expression": "string",
  "task_name": "string",
  ...
}
```

#### List Jobs
```http
GET /api/v1/jobs/?is_active=true&job_type=cron&skip=0&limit=100
```

#### Get Job
```http
GET /api/v1/jobs/{job_id}
```

#### Update Job
```http
PUT /api/v1/jobs/{job_id}
```

#### Delete Job
```http
DELETE /api/v1/jobs/{job_id}
```

#### Execute Job Now
```http
POST /api/v1/jobs/{job_id}/execute
```

#### Pause/Resume Job
```http
POST /api/v1/jobs/{job_id}/pause
POST /api/v1/jobs/{job_id}/resume
```

### Cron API

#### Validate Cron Expression
```http
POST /api/v1/cron/validate
Content-Type: application/json

{
  "expression": "*/5 * * * *",
  "timezone": "UTC"
}
```

#### Get Cron Presets
```http
GET /api/v1/cron/presets
```

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific test file
pytest modules/scheduler/tests/test_cron_utils.py -v

# Run with coverage
pytest --cov=modules/scheduler --cov-report=html
```

## 🔍 Monitoring

### Dashboard Metrics

- Total Jobs
- Active Jobs
- Total Executions
- Success Rate
- Execution Status Distribution
- Last 24h Activity

### Logs

```bash
# All services
make logs

# Specific service
make logs-api
make logs-worker
make logs-beat
make logs-ui
```

## 🔔 Notifications

### Email Notifications

Configure SMTP settings in `.env`:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Telegram Notifications

1. Create a bot via @BotFather
2. Get your bot token
3. Configure in `.env`:
```bash
TELEGRAM_BOT_TOKEN=your-bot-token
```

### Webhook Notifications

Send job events to any HTTP endpoint:
```json
{
  "channel": "webhook",
  "recipient": "https://your-endpoint.com/webhook",
  "on_success": true,
  "on_failure": true
}
```

## 🐳 Docker Commands

```bash
# Build containers
docker-compose build

# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart service
docker-compose restart api

# Execute command in container
docker-compose exec api alembic upgrade head
```

## 🗄️ Database Migrations

```bash
# Create migration
make migrate-create message="Add new field"

# Apply migrations
make migrate

# Rollback migration
make migrate-downgrade
```

## 🛠️ Development

### Project Structure

```
modules/scheduler/
├── api/                    # FastAPI endpoints
│   ├── jobs.py            # Job management API
│   └── cron.py            # Cron validation API
├── models/                 # Database models
│   ├── schemas.py         # SQLAlchemy models
│   └── pydantic_models.py # Pydantic schemas
├── services/               # Business logic
│   ├── scheduler_engine.py # APScheduler integration
│   └── notification_service.py # Notifications
├── tasks/                  # Celery tasks
│   ├── celery_app.py      # Celery configuration
│   └── job_tasks.py       # Task definitions
├── ui/                     # Streamlit interface
│   ├── app.py             # Main UI app
│   └── pages/             # UI pages
├── utils/                  # Utilities
│   ├── cron_utils.py      # Cron helpers
│   └── timezone_utils.py  # Timezone helpers
├── config/                 # Configuration
└── tests/                  # Test suite
```

## 📝 License

[Your License Here]

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines first.

## 📞 Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Documentation: [docs-url]

## 🎯 Roadmap

- [ ] Advanced calendar rules engine
- [ ] Job templates
- [ ] Multi-tenancy support
- [ ] GraphQL API
- [ ] Mobile app
- [ ] Advanced analytics
- [ ] SLA monitoring
- [ ] Job versioning
