# NEXUS Workflow Orchestration Module

## 🚀 Overview

The NEXUS Workflow Orchestration Module is a production-ready, enterprise-grade workflow management system designed for complex multi-step workflows, task dependencies, parallel execution, and comprehensive monitoring.

### Key Features

✅ **DAG-based Workflows** - Directed Acyclic Graph workflow definition
✅ **Task Scheduling** - Cron-based scheduling with automatic execution
✅ **Dependency Management** - Complex task dependencies with automatic resolution
✅ **Parallel Processing** - Execute independent tasks concurrently
✅ **Error Recovery** - Automatic retries with exponential backoff
✅ **Monitoring Dashboard** - Real-time workflow and task monitoring
✅ **Visual Designer** - Streamlit-based UI for workflow creation
✅ **Notifications** - Email, Slack, and webhook notifications
✅ **REST API** - Comprehensive FastAPI REST endpoints
✅ **Temporal Integration** - Advanced orchestration with Temporal
✅ **Production Ready** - Docker, PostgreSQL, Redis, Celery

---

## 📋 Table of Contents

1. [Architecture](#architecture)
2. [Quick Start](#quick-start)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [API Reference](#api-reference)
6. [Workflow Designer](#workflow-designer)
7. [Task Types](#task-types)
8. [Monitoring](#monitoring)
9. [Deployment](#deployment)
10. [Examples](#examples)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      NEXUS Orchestration                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │ Streamlit   │───▶│   FastAPI    │───▶│  PostgreSQL  │ │
│  │     UI      │    │     API      │    │   Database   │ │
│  └─────────────┘    └──────────────┘    └──────────────┘ │
│                            │                               │
│                            │                               │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   Celery    │◀───│    Redis     │◀───│  DAG Engine  │ │
│  │   Workers   │    │   Broker     │    │              │ │
│  └─────────────┘    └──────────────┘    └──────────────┘ │
│                                                            │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │  Temporal   │    │   Flower     │    │  Prometheus  │ │
│  │  (Optional) │    │  Monitoring  │    │   Metrics    │ │
│  └─────────────┘    └──────────────┘    └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Components

- **FastAPI**: REST API for workflow management
- **PostgreSQL**: Persistent storage for workflows and executions
- **Redis**: Message broker and caching layer
- **Celery**: Distributed task execution
- **Streamlit**: Visual workflow designer UI
- **Temporal**: Advanced workflow orchestration (optional)
- **Flower**: Celery monitoring dashboard
- **Prometheus**: Metrics collection

---

## ⚡ Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Start Services

```bash
# Clone repository
cd nexus-platform

# Start all services
docker-compose up -d

# Check service status
docker-compose ps
```

### Access Services

- **API Documentation**: http://localhost:8000/docs
- **Streamlit UI**: http://localhost:8501
- **Flower (Celery)**: http://localhost:5555
- **Temporal UI**: http://localhost:8088

### Create Your First Workflow

```python
import httpx
import asyncio

async def create_workflow():
    workflow_data = {
        "name": "My First Workflow",
        "description": "Hello World workflow",
        "category": "Example",
        "dag_definition": {
            "tasks": {
                "hello": {
                    "task_key": "hello",
                    "name": "Say Hello",
                    "task_type": "python",
                    "config": {
                        "code": "output['message'] = 'Hello, NEXUS!'"
                    },
                    "depends_on": [],
                    "retry_config": {
                        "max_retries": 3,
                        "retry_delay": 60,
                        "timeout": 300
                    }
                }
            }
        },
        "tags": ["example"],
        "is_scheduled": False
    }

    async with httpx.AsyncClient() as client:
        # Create workflow
        response = await client.post(
            "http://localhost:8000/api/v1/workflows/",
            json=workflow_data
        )
        workflow = response.json()

        # Trigger execution
        exec_response = await client.post(
            f"http://localhost:8000/api/v1/workflows/{workflow['id']}/trigger"
        )
        execution = exec_response.json()

        print(f"✅ Workflow created: {workflow['id']}")
        print(f"✅ Execution started: {execution['run_id']}")

asyncio.run(create_workflow())
```

---

## 📦 Installation

### Docker (Recommended)

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python -c "
from modules.orchestration.db.session import init_db
import asyncio
asyncio.run(init_db())
"

# Start API server
uvicorn modules.orchestration.api.main:app --host 0.0.0.0 --port 8000

# Start Celery worker (in another terminal)
celery -A modules.orchestration.workers.celery_app worker --loglevel=info

# Start Celery beat scheduler (in another terminal)
celery -A modules.orchestration.workers.celery_app beat --loglevel=info

# Start Streamlit UI (in another terminal)
streamlit run modules/orchestration/ui/app.py
```

---

## ⚙️ Configuration

Edit `.env` file or set environment variables:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/nexus_orchestration

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Task Execution
MAX_RETRY_ATTEMPTS=3
RETRY_DELAY=60
TASK_TIMEOUT=3600
MAX_PARALLEL_TASKS=10

# Notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-password
SMTP_FROM=nexus@example.com

SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

---

## 📚 API Reference

### Workflows

**Create Workflow**
```http
POST /api/v1/workflows/
Content-Type: application/json

{
  "name": "My Workflow",
  "description": "Description",
  "category": "ETL",
  "dag_definition": {...},
  "tags": ["tag1", "tag2"],
  "is_scheduled": false
}
```

**List Workflows**
```http
GET /api/v1/workflows/?skip=0&limit=100&status=running&category=ETL
```

**Get Workflow**
```http
GET /api/v1/workflows/{workflow_id}
```

**Update Workflow**
```http
PUT /api/v1/workflows/{workflow_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "description": "Updated description"
}
```

**Delete Workflow**
```http
DELETE /api/v1/workflows/{workflow_id}
```

**Trigger Workflow**
```http
POST /api/v1/workflows/{workflow_id}/trigger
Content-Type: application/json

{
  "input_data": {"key": "value"},
  "triggered_by": "api"
}
```

### Executions

**List Executions**
```http
GET /api/v1/executions/?workflow_id=1&skip=0&limit=100
```

**Get Execution**
```http
GET /api/v1/executions/{execution_id}
```

**Cancel Execution**
```http
POST /api/v1/executions/{execution_id}/cancel
```

### DAG Validation

**Validate DAG**
```http
POST /api/v1/dag/validate
Content-Type: application/json

{
  "dag_definition": {...}
}
```

### Statistics

**Get Statistics**
```http
GET /api/v1/statistics/workflows
```

---

## 🎨 Workflow Designer

Access the visual workflow designer at http://localhost:8501

### Features

- **Drag-and-Drop Interface**: Build workflows visually
- **Task Configuration**: Configure task types, dependencies, and retry policies
- **DAG Visualization**: See workflow structure in real-time
- **Validation**: Validate workflows before creation
- **Templates**: Use pre-built workflow templates

### Using the Designer

1. Navigate to "Workflow Designer" in the sidebar
2. Enter workflow name and description
3. Add tasks using the "Add New Task" form
4. Configure task type and settings
5. Set dependencies on other tasks
6. Click "Add Task" to add to workflow
7. Review DAG visualization
8. Click "Create Workflow" to save

---

## 🔧 Task Types

### Python Tasks

Execute Python code with access to input/output variables:

```python
{
  "task_type": "python",
  "config": {
    "code": """
# Access input from previous tasks
previous_result = input.get('previous_task', {})

# Perform computation
result = previous_result.get('value', 0) * 2

# Set output for next tasks
output['result'] = result
output['status'] = 'success'
"""
  }
}
```

### HTTP Tasks

Make HTTP API calls:

```python
{
  "task_type": "http",
  "config": {
    "method": "POST",
    "url": "https://api.example.com/data",
    "headers": {
      "Authorization": "Bearer token",
      "Content-Type": "application/json"
    },
    "json": {"key": "value"},
    "timeout": 30
  }
}
```

### Bash Tasks

Execute shell commands:

```python
{
  "task_type": "bash",
  "config": {
    "command": "python script.py --arg value"
  }
}
```

### SQL Tasks

Run SQL queries:

```python
{
  "task_type": "sql",
  "config": {
    "query": "SELECT * FROM users WHERE active = true LIMIT 100"
  }
}
```

---

## 📊 Monitoring

### Metrics Dashboard

Access at http://localhost:8501 → "Dashboard"

**Metrics Include:**
- Total workflows
- Active workflows
- Execution statistics
- Success rate
- Average duration
- Task statistics

### Flower (Celery Monitoring)

Access at http://localhost:5555

**Features:**
- Worker status
- Task queue length
- Active tasks
- Task history
- Worker utilization

### Prometheus Metrics

Metrics exposed at `/metrics` endpoint:

- `workflow_executions_total`
- `workflow_execution_duration_seconds`
- `active_workflows`
- `task_executions_total`
- `task_execution_duration_seconds`
- `task_retries_total`

---

## 🚀 Deployment

### Production Checklist

- [ ] Set strong `SECRET_KEY` in `.env`
- [ ] Configure PostgreSQL with persistent storage
- [ ] Set up Redis with persistence
- [ ] Configure SMTP for email notifications
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Set up log aggregation
- [ ] Configure backup strategy
- [ ] Set up monitoring alerts
- [ ] Review resource limits

### Docker Deployment

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Scale workers
docker-compose up -d --scale celery_worker=4

# View logs
docker-compose logs -f

# Backup database
docker-compose exec postgres pg_dump -U postgres nexus_orchestration > backup.sql
```

### Kubernetes Deployment

```yaml
# See docs/kubernetes/ for complete manifests
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nexus-orchestration-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nexus-api
  template:
    metadata:
      labels:
        app: nexus-api
    spec:
      containers:
      - name: api
        image: nexus-orchestration:latest
        ports:
        - containerPort: 8000
```

---

## 📖 Examples

See the `examples/` directory for complete examples:

- **simple_workflow.py**: Sequential task execution
- **parallel_workflow.py**: Parallel task processing
- **http_workflow.py**: HTTP API integration

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Ensure all tests pass
5. Submit a pull request

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🆘 Support

- **Documentation**: See `/docs` directory
- **API Docs**: http://localhost:8000/docs
- **Examples**: See `/examples` directory
- **Issues**: Create an issue on GitHub

---

## 🎯 Roadmap

- [ ] GraphQL API
- [ ] Workflow versioning
- [ ] Workflow templates marketplace
- [ ] Advanced scheduling (date ranges, holidays)
- [ ] Workflow analytics and insights
- [ ] Integration with more services (AWS, GCP, Azure)
- [ ] Workflow debugging tools
- [ ] Mobile app for monitoring

---

**Built with ❤️ for the NEXUS Platform**
