# 🤖 NEXUS Browser Automation Module

A comprehensive, production-ready browser automation system with Selenium/Playwright integration, visual workflow builder, and enterprise-grade scheduling capabilities.

## ✨ Features

### Core Capabilities
- **Dual Browser Engine Support**: Selenium & Playwright integration
- **Multi-Browser Support**: Chromium, Firefox, WebKit
- **Headless & Headed Modes**: Flexible execution options
- **Visual Workflow Builder**: Streamlit-based UI for easy workflow creation
- **Advanced Scheduling**: Cron-based workflow scheduling with Redis
- **Data Extraction**: Powerful web scraping and data collection
- **Form Automation**: Intelligent form filling and submission
- **Screenshot & PDF**: Automated capture and generation
- **Error Handling**: Robust retry logic and error recovery
- **Monitoring**: Prometheus metrics and comprehensive logging

### Workflow Step Types
- `navigate`: Navigate to URLs
- `click`: Click elements
- `type`: Type text into inputs
- `extract`: Extract data from pages
- `screenshot`: Capture screenshots
- `pdf`: Generate PDFs
- `wait`: Wait operations
- `scroll`: Scroll pages
- `select`: Select dropdown options
- `submit`: Submit forms
- `custom_js`: Execute custom JavaScript

## 🏗️ Architecture

```
modules/browser_automation/
├── api/                    # FastAPI REST endpoints
│   ├── workflows.py       # Workflow management
│   ├── schedules.py       # Schedule management
│   └── executions.py      # Execution tracking
├── models/                # Database models & schemas
│   ├── workflow.py        # Workflow models
│   ├── schedule.py        # Schedule models
│   ├── database.py        # DB configuration
│   └── schemas.py         # Pydantic schemas
├── services/              # Core automation services
│   ├── automation.py      # Base service interface
│   ├── playwright_service.py  # Playwright implementation
│   ├── selenium_service.py    # Selenium implementation
│   └── executor.py        # Workflow executor
├── tasks/                 # Celery async tasks
│   ├── celery_app.py      # Celery configuration
│   └── workflow_tasks.py  # Workflow tasks
├── utils/                 # Utility modules
│   ├── selector_helper.py # Element selector utilities
│   ├── redis_client.py    # Redis client
│   └── monitoring.py      # Metrics & monitoring
├── ui/                    # Streamlit UI
│   └── app.py            # Visual workflow builder
├── tests/                 # Test suite
├── config/               # Configuration
└── storage/              # Storage for outputs
    ├── screenshots/
    ├── pdfs/
    └── logs/
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Installation

#### Option 1: Docker (Recommended)

```bash
# Clone repository
cd modules/browser_automation

# Copy environment file
cp .env.example .env

# Edit .env with your settings
nano .env

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

Services will be available at:
- **API**: http://localhost:8000
- **Streamlit UI**: http://localhost:8501
- **Flower (Celery Monitoring)**: http://localhost:5555
- **API Docs**: http://localhost:8000/api/v1/docs

#### Option 2: Local Installation

```bash
# Install dependencies
make install

# Or manually:
pip install -r requirements.txt
playwright install chromium firefox webkit

# Set up environment
cp .env.example .env

# Start PostgreSQL and Redis
# (using your preferred method)

# Run database migrations
make migrate

# Start services in separate terminals:

# Terminal 1: API
make dev

# Terminal 2: Celery Worker
make celery

# Terminal 3: Celery Beat (Scheduler)
make beat

# Terminal 4: Streamlit UI
make streamlit
```

## 📖 Usage

### Creating a Workflow via UI

1. Open http://localhost:8501
2. Navigate to "➕ Create Workflow"
3. Fill in workflow details:
   - Name and description
   - Browser type (Chromium/Firefox/WebKit)
   - Headless mode
   - Timeout settings
4. Add workflow steps:
   - Choose step type
   - Configure selectors
   - Set wait times
5. Click "Create Workflow"

### Creating a Workflow via API

```python
import httpx

workflow_data = {
    "name": "Google Search Automation",
    "description": "Automate Google search and extract results",
    "is_active": True,
    "headless": True,
    "browser_type": "chromium",
    "timeout": 30000,
    "steps": [
        {
            "step_order": 0,
            "step_type": "navigate",
            "name": "Go to Google",
            "value": "https://www.google.com",
            "wait_after": 1000
        },
        {
            "step_order": 1,
            "step_type": "type",
            "name": "Enter search query",
            "selector": "input[name='q']",
            "selector_type": "css",
            "value": "browser automation",
            "wait_after": 500
        },
        {
            "step_order": 2,
            "step_type": "click",
            "name": "Click search button",
            "selector": "input[name='btnK']",
            "selector_type": "css",
            "wait_after": 2000
        },
        {
            "step_order": 3,
            "step_type": "extract",
            "name": "Extract search results",
            "selector": "h3",
            "selector_type": "css",
            "options": {"type": "multiple"}
        },
        {
            "step_order": 4,
            "step_type": "screenshot",
            "name": "Take screenshot",
            "options": {"full_page": True}
        }
    ]
}

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/workflows",
        json=workflow_data
    )
    workflow = response.json()
    print(f"Created workflow: {workflow['id']}")
```

### Executing a Workflow

```python
# Execute workflow
response = await client.post(
    f"http://localhost:8000/api/v1/workflows/{workflow_id}/execute"
)
execution = response.json()

print(f"Execution ID: {execution['id']}")
print(f"Status: {execution['status']}")
print(f"Extracted Data: {execution['result_data']}")
```

### Scheduling a Workflow

```python
schedule_data = {
    "workflow_id": workflow_id,
    "name": "Daily Google Search",
    "cron_expression": "0 9 * * *",  # Every day at 9 AM
    "timezone": "UTC",
    "is_active": True,
    "notify_on_failure": True,
    "notification_emails": ["admin@example.com"]
}

response = await client.post(
    "http://localhost:8000/api/v1/schedules",
    json=schedule_data
)
```

### Using Python Services Directly

```python
from modules.browser_automation.services import PlaywrightService

# Initialize service
service = PlaywrightService(headless=True, browser_type="chromium")

# Start browser
await service.start()

try:
    # Navigate
    await service.navigate("https://example.com")

    # Extract data
    title = await service.extract_text("h1", "css")
    print(f"Title: {title}")

    # Take screenshot
    await service.screenshot("example.png", full_page=True)

    # Execute custom JavaScript
    result = await service.execute_script("return document.title")

finally:
    # Always close browser
    await service.stop()
```

## 🔧 Configuration

Key environment variables in `.env`:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Browser
BROWSER_TYPE=chromium          # chromium, firefox, webkit
HEADLESS_MODE=True
BROWSER_TIMEOUT=30000
MAX_CONCURRENT_BROWSERS=5

# Storage
SCREENSHOT_PATH=./storage/screenshots
PDF_PATH=./storage/pdfs
LOG_PATH=./storage/logs
```

## 🧪 Testing

```bash
# Run all tests
make test

# Or with pytest directly
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=modules/browser_automation --cov-report=html

# Run specific test file
pytest tests/test_workflows.py -v
```

## 📊 Monitoring

### Prometheus Metrics

Access metrics at: `http://localhost:8000/metrics`

Available metrics:
- `workflow_executions_total`: Total workflow executions by status
- `workflow_execution_duration_seconds`: Execution duration histogram
- `active_workflows_total`: Number of active workflows
- `browser_sessions_active`: Active browser sessions
- `errors_total`: Total errors by type

### Flower (Celery Monitoring)

Access Flower UI at: `http://localhost:5555`

Monitor:
- Active workers
- Task queues
- Task history
- Success/failure rates

### Logs

Logs are stored in `storage/logs/` directory and include:
- Workflow execution logs
- Browser automation logs
- Error logs
- Performance metrics

## 🔒 Security Best Practices

1. **Environment Variables**: Never commit `.env` file
2. **Secret Keys**: Use strong random keys in production
3. **Database**: Use strong passwords and restrict access
4. **API**: Implement authentication (add JWT/OAuth)
5. **Rate Limiting**: Configure appropriate limits
6. **Input Validation**: All inputs are validated via Pydantic
7. **Docker**: Run containers as non-root users in production

## 🚀 Production Deployment

### Docker Deployment

```bash
# Build images
docker-compose build

# Start in production mode
docker-compose up -d

# Scale workers
docker-compose up -d --scale celery_worker=3

# View logs
docker-compose logs -f
```

### Kubernetes Deployment

See `k8s/` directory for Kubernetes manifests (TODO: add k8s configs)

### Performance Tuning

1. **Database Connection Pool**:
   ```python
   DB_POOL_SIZE=20
   DB_MAX_OVERFLOW=10
   ```

2. **Celery Workers**:
   ```bash
   celery -A tasks.celery_app worker --concurrency=4
   ```

3. **Browser Limits**:
   ```python
   MAX_CONCURRENT_BROWSERS=5
   ```

## 📚 API Documentation

Interactive API documentation available at:
- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc

### Key Endpoints

- `POST /api/v1/workflows` - Create workflow
- `GET /api/v1/workflows` - List workflows
- `GET /api/v1/workflows/{id}` - Get workflow
- `PUT /api/v1/workflows/{id}` - Update workflow
- `DELETE /api/v1/workflows/{id}` - Delete workflow
- `POST /api/v1/workflows/{id}/execute` - Execute workflow
- `POST /api/v1/schedules` - Create schedule
- `GET /api/v1/executions` - List executions
- `GET /api/v1/executions/stats/summary` - Get statistics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run test suite
6. Submit pull request

## 📄 License

This module is part of the NEXUS Platform.

## 🆘 Support

- **Documentation**: See this README
- **API Docs**: http://localhost:8000/api/v1/docs
- **Issues**: Create an issue in the repository

## 🎯 Roadmap

- [ ] Add proxy support
- [ ] Implement CAPTCHA solving integration
- [ ] Add more browser drivers
- [ ] Implement workflow versioning
- [ ] Add workflow templates library
- [ ] Implement A/B testing for workflows
- [ ] Add integration with popular APIs
- [ ] Implement workflow marketplace

## 📊 Example Use Cases

1. **Web Scraping**: Extract product data from e-commerce sites
2. **Testing**: Automated UI testing for web applications
3. **Monitoring**: Monitor website changes and availability
4. **Data Collection**: Gather market research data
5. **Form Automation**: Auto-fill and submit forms
6. **Report Generation**: Generate PDFs from web pages
7. **Social Media**: Automate social media interactions
8. **Price Monitoring**: Track competitor pricing

---

Built with ❤️ for the NEXUS Platform
