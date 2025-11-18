# NEXUS Platform - RPA Module

## 🤖 Robotic Process Automation Platform

NEXUS: Unified AI-powered productivity platform with 24 integrated modules - Word, Excel, PPT, Projects, Email, Chat, Flowcharts, Analytics, Meetings & more. Built with Streamlit & Claude AI.

This repository contains the **RPA (Robotic Process Automation) module** - a comprehensive, production-ready automation platform built with FastAPI, PostgreSQL, Redis, Celery, and Streamlit.

---

## 🚀 Features

### Core RPA Capabilities
- ✅ **Visual Bot Builder** - Intuitive workflow editor for creating automations
- ✅ **Process Recorder** - Record user actions to create automations automatically
- ✅ **UI Element Detection** - Advanced element detection with OCR and image recognition
- ✅ **Desktop Automation** - Mouse, keyboard, and screen automation
- ✅ **Application Integration** - HTTP requests, API calls, webhooks
- ✅ **Data Manipulation** - Transform, parse, and process data
- ✅ **Conditional Logic** - If/else conditions and decision trees
- ✅ **Loops & Iterations** - Process collections and repeat actions
- ✅ **Error Handling** - Retry logic, error recovery, fallback actions
- ✅ **Bot Orchestration** - Manage multiple bots and workflows
- ✅ **Scheduling** - Cron-based automation scheduling with timezone support
- ✅ **Audit Logs** - Complete audit trail of all actions

### Technology Stack
- **Backend**: FastAPI (async Python web framework)
- **Database**: PostgreSQL (primary data store)
- **Cache/Queue**: Redis (Celery broker and caching)
- **Task Queue**: Celery (async task execution and scheduling)
- **UI**: Streamlit (interactive web interface)
- **RPA Libraries**: PyAutoGUI, OpenCV, Playwright, Selenium, pytesseract
- **ORM**: SQLAlchemy with Alembic migrations

---

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 16+
- Redis 7+
- Docker & Docker Compose (optional but recommended)

---

## 🛠️ Installation

### Option 1: Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd nexus-platform
```

2. Copy environment variables:
```bash
cp .env.example .env
# Edit .env with your configurations
```

3. Start all services:
```bash
docker-compose up -d
```

4. Initialize database:
```bash
docker-compose exec api python scripts/init_db.py
docker-compose exec api python scripts/seed_data.py
```

5. Access the applications:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Streamlit UI**: http://localhost:8501
- **Flower (Celery monitoring)**: http://localhost:5555

### Option 2: Manual Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install chromium
```

3. Set up PostgreSQL and Redis locally

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your database and Redis URLs
```

5. Initialize database:
```bash
python scripts/init_db.py
python scripts/seed_data.py
```

6. Start services in separate terminals:

```bash
# Terminal 1 - API
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Streamlit
streamlit run src/ui/streamlit_app.py

# Terminal 3 - Celery Worker
celery -A src.services.task_queue.celery_app worker --loglevel=info

# Terminal 4 - Celery Beat (Scheduler)
celery -A src.services.task_queue.celery_app beat --loglevel=info
```

---

## 📖 Quick Start

### Creating Your First Automation

1. **Access Streamlit UI**: Open http://localhost:8501

2. **Navigate to Bot Builder**: Click "Bot Builder" in the sidebar

3. **Create Automation**:
   - Fill in automation name and description
   - Select trigger type (manual, scheduled, webhook)
   - Click "Create Automation"

4. **Build Workflow**:
   - Switch to "Workflow Editor" tab
   - Add action nodes (Click, Type, Wait, HTTP Request, etc.)
   - Configure each action with required parameters
   - Save workflow

5. **Test & Deploy**:
   - Switch to "Test & Deploy" tab
   - Provide test input data
   - Run a test execution
   - Activate the automation

### Available Action Types

- **Click** - Simulate mouse clicks at specific coordinates
- **Type** - Simulate keyboard typing
- **Wait** - Pause execution for specified duration
- **Condition** - Evaluate conditions and branch logic
- **Loop** - Iterate over collections
- **Set Variable** - Store values in variables
- **HTTP Request** - Make API calls
- **Data Manipulation** - Transform data (parse JSON, split, join, etc.)
- **Screenshot** - Capture screen
- **Log Message** - Add log entries

---

## 🏗️ Architecture

### Project Structure
```
nexus-platform/
├── src/
│   ├── api/                    # FastAPI application
│   │   └── main.py            # API entry point
│   ├── config/                 # Configuration
│   │   ├── settings.py        # Application settings
│   │   └── database.py        # Database configuration
│   ├── database/               # Database layer
│   │   ├── models.py          # SQLAlchemy models
│   │   └── migrations/        # Alembic migrations
│   ├── modules/rpa/            # RPA module
│   │   ├── engine.py          # Automation execution engine
│   │   ├── execution_manager.py   # Execution management
│   │   ├── scheduler.py       # Scheduling service
│   │   ├── actions.py         # Action executors
│   │   ├── recorder.py        # Process recorder
│   │   ├── ui_detector.py     # UI element detection
│   │   ├── audit.py           # Audit logging
│   │   ├── error_handler.py   # Error handling
│   │   ├── routes.py          # API routes
│   │   └── schemas.py         # Pydantic schemas
│   ├── services/               # Background services
│   │   └── task_queue.py      # Celery tasks
│   ├── ui/                     # Streamlit UI
│   │   ├── streamlit_app.py   # Main app
│   │   └── pages/             # UI pages
│   └── utils/                  # Utilities
├── scripts/                    # Utility scripts
│   ├── init_db.py             # Database initialization
│   └── seed_data.py           # Seed sample data
├── docker-compose.yml          # Docker orchestration
├── Dockerfile                  # Container image
└── requirements.txt            # Python dependencies
```

### Database Schema

- **bots** - Bot/agent configurations and capabilities
- **automations** - Automation workflow definitions
- **automation_executions** - Execution history, logs, and results
- **schedules** - Scheduled automation configurations
- **audit_logs** - Complete audit trail of all actions
- **ui_elements** - UI element definitions for automation

---

## 📊 Monitoring & Observability

### Celery Flower
Monitor Celery workers and tasks at http://localhost:5555

### Logs
- Application logs: `./logs/nexus.log`
- Rotation enabled (500MB per file, 10 days retention)
- Compression enabled (ZIP)

### Metrics & Statistics
- Execution statistics: `GET /api/v1/rpa/statistics/executions`
- Audit statistics: `GET /api/v1/rpa/statistics/audit`

---

## 📚 API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Bots
- `POST /api/v1/rpa/bots` - Create bot
- `GET /api/v1/rpa/bots` - List bots
- `GET /api/v1/rpa/bots/{bot_id}` - Get bot details
- `PUT /api/v1/rpa/bots/{bot_id}` - Update bot
- `DELETE /api/v1/rpa/bots/{bot_id}` - Delete bot

#### Automations
- `POST /api/v1/rpa/automations` - Create automation
- `GET /api/v1/rpa/automations` - List automations
- `GET /api/v1/rpa/automations/{id}` - Get automation
- `PUT /api/v1/rpa/automations/{id}` - Update automation
- `DELETE /api/v1/rpa/automations/{id}` - Delete automation
- `POST /api/v1/rpa/automations/{id}/execute` - Execute automation

#### Executions
- `GET /api/v1/rpa/executions` - List executions
- `GET /api/v1/rpa/executions/{id}` - Get execution details
- `POST /api/v1/rpa/executions/{id}/cancel` - Cancel execution
- `GET /api/v1/rpa/executions/{id}/logs` - Get execution logs

#### Schedules
- `POST /api/v1/rpa/schedules` - Create schedule
- `GET /api/v1/rpa/schedules` - List schedules
- `PUT /api/v1/rpa/schedules/{id}` - Update schedule
- `DELETE /api/v1/rpa/schedules/{id}` - Delete schedule

---

## 🔧 Configuration

Key environment variables (see `.env.example`):

```bash
# Environment
ENVIRONMENT=development
DEBUG=True

# Database
DATABASE_URL=postgresql://nexus:password@localhost:5432/nexus_platform

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here

# RPA Settings
RPA_SCREENSHOT_DIR=./data/screenshots
RPA_RECORDING_DIR=./data/recordings
RPA_MAX_EXECUTION_TIME=3600
RPA_RETRY_ATTEMPTS=3
```

---

## 🧪 Testing

Run tests:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest --cov=src tests/
```

---

## 🚢 Production Deployment

### Checklist

1. ✅ Set strong secrets in `.env`
2. ✅ Configure production database with SSL
3. ✅ Set `ENVIRONMENT=production` and `DEBUG=False`
4. ✅ Use production WSGI server (Gunicorn + Uvicorn)
5. ✅ Configure SSL/TLS certificates
6. ✅ Set up firewall rules
7. ✅ Configure monitoring and alerting
8. ✅ Set up regular database backups
9. ✅ Configure log aggregation
10. ✅ Set up auto-scaling for Celery workers

---

## 🛡️ Security Features

- JWT-based authentication
- SQL injection protection via SQLAlchemy ORM
- CORS configuration
- Input validation with Pydantic
- Comprehensive audit logging
- Secure password hashing (bcrypt)
- Rate limiting (configurable)

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📝 License

[Add your license here]

---

## 💬 Support

- Documentation: `./docs/`
- Issues: GitHub Issues
- Discussions: GitHub Discussions

---

## 🎯 Roadmap

- [ ] Enhanced visual workflow designer with drag-and-drop
- [ ] Machine learning-based element detection
- [ ] Multi-tenant support
- [ ] Workflow templates marketplace
- [ ] Advanced analytics dashboard
- [ ] Integration with more external services
- [ ] Mobile app for monitoring
- [ ] Enterprise SSO integration
- [ ] AI-powered workflow optimization

---

## ⭐ Acknowledgments

Built with amazing open-source technologies:
- FastAPI, SQLAlchemy, Celery, Streamlit
- PyAutoGUI, OpenCV, Playwright, Selenium
- And many other fantastic projects

---

**Happy Automating! 🤖**
