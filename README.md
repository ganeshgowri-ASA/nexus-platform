# NEXUS Platform

NEXUS: Unified AI-powered productivity platform with 24 integrated modules - Word, Excel, PPT, Projects, Email, Chat, Flowcharts, Analytics, Meetings & more. Built with Streamlit & Claude AI.

## 🔄 Workflow Orchestration Module

Production-ready workflow orchestration system for complex multi-step workflows.

### Features

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

### Quick Start

```bash
# Setup (first time only)
./scripts/setup.sh

# Start all services
./scripts/start.sh

# Or using Docker Compose directly
docker-compose up -d

# Access services
# - API Documentation: http://localhost:8000/docs
# - Streamlit UI: http://localhost:8501
# - Flower (Celery): http://localhost:5555
# - Temporal UI: http://localhost:8088

# Run example workflows
python examples/simple_workflow.py
python examples/parallel_workflow.py
python examples/http_workflow.py
```

### Documentation

- **Full Documentation**: [docs/ORCHESTRATION_README.md](docs/ORCHESTRATION_README.md)
- **Examples**: [examples/](examples/)
- **API Reference**: http://localhost:8000/docs (when running)

### Architecture

```
modules/orchestration/
├── api/              # FastAPI REST API
│   ├── endpoints.py  # API endpoints
│   ├── schemas.py    # Pydantic models
│   ├── services.py   # Business logic
│   └── main.py       # FastAPI app
├── core/             # Core orchestration engine
│   ├── dag.py        # DAG engine
│   ├── executor.py   # Task execution
│   └── temporal_integration.py
├── db/               # Database layer
│   ├── models.py     # SQLAlchemy models
│   └── session.py    # Database session
├── workers/          # Celery workers
│   ├── celery_app.py # Celery configuration
│   └── tasks.py      # Celery tasks
├── ui/               # Streamlit UI
│   └── app.py        # Workflow designer
├── utils/            # Utilities
│   ├── redis_client.py
│   ├── monitoring.py
│   └── notifications.py
├── config/           # Configuration
│   └── settings.py   # Settings management
└── tests/            # Test suite
    ├── test_dag.py
    └── conftest.py
```

### Technology Stack

- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Reliable database
- **Redis** - Fast caching & message broker
- **Celery** - Distributed task queue
- **Streamlit** - Interactive UI
- **Temporal** - Advanced orchestration (optional)
- **NetworkX** - Graph algorithms for DAG
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation
- **Docker** - Containerization

### Available Commands

```bash
make help            # Show all available commands
make install         # Install dependencies
make test            # Run tests
make docker-up       # Start Docker services
make run-api         # Run FastAPI server
make run-ui          # Run Streamlit UI
make example-simple  # Run simple workflow example
```

### Module Features

#### 1. DAG Engine
- Directed Acyclic Graph workflow definition
- Cycle detection
- Topological sorting
- Parallel execution group identification
- Critical path analysis
- DAG validation

#### 2. Task Execution
- Multiple task types (Python, HTTP, Bash, SQL)
- Automatic retry with exponential backoff
- Task timeout handling
- Error recovery
- Input/output data passing
- Celery distributed execution

#### 3. REST API
- Workflow CRUD operations
- Execution management
- Real-time status tracking
- DAG validation
- Statistics and metrics
- Notification configuration

#### 4. Visual Designer
- Interactive workflow creation
- Task configuration
- Dependency management
- Real-time DAG visualization
- Workflow templates
- Export/Import workflows

#### 5. Monitoring
- Real-time execution tracking
- Task status monitoring
- Performance metrics
- Flower dashboard
- Prometheus metrics
- Custom dashboards

#### 6. Notifications
- Email notifications
- Slack integration
- Webhook support
- Configurable triggers
- Event-based notifications

### Example Workflow

```python
{
  "name": "Data Processing Pipeline",
  "dag_definition": {
    "tasks": {
      "extract": {
        "task_key": "extract",
        "name": "Extract Data",
        "task_type": "http",
        "config": {
          "method": "GET",
          "url": "https://api.example.com/data"
        },
        "depends_on": []
      },
      "transform": {
        "task_key": "transform",
        "name": "Transform Data",
        "task_type": "python",
        "config": {
          "code": "output['result'] = process(input['extract'])"
        },
        "depends_on": ["extract"]
      },
      "load": {
        "task_key": "load",
        "name": "Load Data",
        "task_type": "sql",
        "config": {
          "query": "INSERT INTO results VALUES (...)"
        },
        "depends_on": ["transform"]
      }
    }
  }
}
```

---

## 📜 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please read the contributing guidelines before submitting PRs.

## 📞 Support

For questions and support, please open an issue on GitHub.

---

**Built with ❤️ for the NEXUS Platform**
