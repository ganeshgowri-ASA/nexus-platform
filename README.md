# 🚀 NEXUS Platform - Pipeline Module

NEXUS: Unified AI-powered productivity platform with 24 integrated modules - Word, Excel, PPT, Projects, Email, Chat, Flowcharts, Analytics, Meetings & more. Built with Streamlit & Claude AI.

## 📦 Pipeline Module

The **Pipeline Module** is a comprehensive data pipeline orchestration system with visual workflow building, ETL capabilities, stream processing, and production-ready monitoring.

### ✨ Features

- **Visual Pipeline Builder**: Drag-and-drop interface for creating data workflows
- **Source/Destination Connectors**: 10+ built-in connectors (PostgreSQL, CSV, JSON, REST API, etc.)
- **Data Transformations**: Filter, map, aggregate, join, sort, deduplicate, validate
- **Scheduling**: Cron-based scheduling with timezone support
- **Monitoring**: Real-time execution monitoring with metrics and logging
- **Error Handling**: Automatic retries, error recovery, and detailed error tracking
- **Backfill Support**: Historical data processing with date range backfills
- **Apache Airflow Integration**: Sync pipelines to Airflow DAGs
- **Celery Backend**: Asynchronous task execution with distributed workers
- **Production-Ready**: Docker support, health checks, monitoring, and logging

---

## 🏗️ Architecture

```
nexus-platform/
├── config/                      # Configuration
│   ├── settings.py             # Global settings
│   └── database.py             # Database configuration
├── core/                       # Core infrastructure
│   ├── base_module.py          # Base module class
│   └── utils.py                # Utilities
├── modules/                    # Application modules
│   └── pipeline/               # Pipeline module
│       ├── models.py           # Database models
│       ├── services.py         # Business logic
│       ├── api.py              # FastAPI endpoints
│       ├── ui.py               # Streamlit UI
│       ├── connectors.py       # Data connectors
│       ├── transformations.py  # Transformation engine
│       ├── tasks.py            # Celery tasks
│       └── airflow_integration.py  # Airflow integration
├── scripts/                    # Utility scripts
│   └── init_db.py             # Database initialization
├── main.py                     # Streamlit entry point
├── api_server.py              # FastAPI entry point
├── requirements.txt           # Python dependencies
├── docker-compose.yml         # Docker orchestration
└── Dockerfile                 # Container definition
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Installation

#### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd nexus-platform

# Copy environment configuration
cp .env.example .env

# Edit .env with your configuration
nano .env

# Start all services
docker-compose up -d

# Initialize database
docker-compose exec api python scripts/init_db.py

# Access the application
# Streamlit UI: http://localhost:8501
# FastAPI: http://localhost:8000
# Flower (Celery): http://localhost:5555
```

#### Option 2: Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
nano .env

# Start PostgreSQL and Redis
# (Use your preferred method)

# Initialize database
python scripts/init_db.py

# Start Celery worker (in separate terminal)
celery -A modules.pipeline.tasks worker --loglevel=info

# Start Celery beat scheduler (in separate terminal)
celery -A modules.pipeline.tasks beat --loglevel=info

# Start FastAPI server (in separate terminal)
uvicorn api_server:app --reload --port 8000

# Start Streamlit UI
streamlit run main.py
```

---

## 📖 Usage Guide

### Creating a Pipeline

#### 1. Via Streamlit UI

1. Navigate to **Create Pipeline** page
2. Enter pipeline name and description
3. Add pipeline steps:
   - **Extract**: Configure source connector
   - **Transform**: Add transformations
   - **Load**: Configure destination connector
4. Click **Create Pipeline**

#### 2. Via REST API

```bash
# Create a pipeline
curl -X POST http://localhost:8000/api/v1/pipelines \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My ETL Pipeline",
    "description": "Extract data from PostgreSQL, transform, and load to S3",
    "tags": ["etl", "daily"]
  }'

# Add a step
curl -X POST http://localhost:8000/api/v1/pipelines/1/steps \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Extract from DB",
    "step_type": "extract",
    "source_connector_id": 1,
    "config": {
      "source_params": {
        "query": "SELECT * FROM users WHERE created_at >= NOW() - INTERVAL '\''1 day'\''"
      }
    }
  }'

# Execute pipeline
curl -X POST http://localhost:8000/api/v1/pipelines/1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "trigger_type": "manual"
  }'
```

### Creating Connectors

#### PostgreSQL Connector

```python
from modules.pipeline.connectors import ConnectorFactory

# Create PostgreSQL connector
connector = ConnectorFactory.create("postgresql", {
    "host": "localhost",
    "port": 5432,
    "database": "mydb",
    "user": "postgres",
    "password": "password"
})

# Test connection
with connector:
    result = connector.test_connection()
    print(result)  # {'status': 'success', 'message': 'Connection successful', ...}

    # Read data
    for record in connector.read(query="SELECT * FROM users LIMIT 100"):
        print(record)
```

#### CSV Connector

```python
# Create CSV connector
connector = ConnectorFactory.create("csv", {
    "file_path": "/path/to/data.csv",
    "delimiter": ",",
    "encoding": "utf-8"
})

# Read data
with connector:
    for record in connector.read():
        print(record)
```

### Transformations

```python
from modules.pipeline.transformations import TransformationFactory, TransformationPipeline

# Create transformations
filter_transform = TransformationFactory.create("filter", {
    "conditions": [
        {"field": "age", "operator": "greater_than", "value": 18}
    ]
})

map_transform = TransformationFactory.create("map", {
    "mappings": {
        "full_name": {"field": "name", "transform": "uppercase"},
        "age_years": "age"
    }
})

# Create pipeline
pipeline = TransformationPipeline([filter_transform, map_transform])

# Execute
data = [{"name": "john", "age": 25}, {"name": "jane", "age": 15}]
result = pipeline.execute(data)
print(result)  # [{'full_name': 'JOHN', 'age_years': 25}]
```

### Scheduling

```python
from modules.pipeline.services import PipelineService
from config.database import get_db_context

with get_db_context() as db:
    service = PipelineService(db)

    # Create schedule (runs daily at midnight)
    schedule = service.create_schedule(
        pipeline_id=1,
        cron_expression="0 0 * * *",
        timezone="UTC"
    )

    # Activate schedule
    service.activate_schedule(schedule.id)
```

### Backfilling

```python
from datetime import datetime

with get_db_context() as db:
    service = PipelineService(db)

    # Backfill pipeline for date range
    result = service.backfill_pipeline(
        pipeline_id=1,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31)
    )

    print(f"Backfill started: {result['task_id']}")
```

---

## 🔌 Available Connectors

### Source & Destination Connectors

| Connector | Type | Read | Write | Description |
|-----------|------|------|-------|-------------|
| PostgreSQL | Database | ✅ | ✅ | PostgreSQL database |
| CSV | File | ✅ | ✅ | CSV files |
| JSON | File | ✅ | ✅ | JSON files |
| REST API | API | ✅ | ✅ | RESTful APIs |

### Extensibility

Add custom connectors by extending the `BaseConnector` class:

```python
from modules.pipeline.connectors import BaseConnector, ConnectorFactory

class MyCustomConnector(BaseConnector):
    def connect(self):
        # Implementation
        pass

    def disconnect(self):
        # Implementation
        pass

    def test_connection(self):
        # Implementation
        pass

# Register connector
ConnectorFactory.register("my_custom", MyCustomConnector)
```

---

## 🔄 Available Transformations

- **Filter**: Filter records based on conditions
- **Map**: Transform and rename fields
- **Aggregate**: Group and aggregate data
- **Sort**: Sort records
- **Deduplicate**: Remove duplicate records
- **Join**: Join two datasets
- **Validation**: Validate data against rules
- **Custom Python**: Execute custom Python code

---

## 📊 Monitoring & Observability

### Metrics

- Total executions
- Success rate
- Average duration
- Records processed
- Failed records

### Logging

All pipeline executions are logged with:
- Execution start/end times
- Step-by-step logs
- Error messages and stack traces
- Performance metrics

### Celery Flower

Monitor Celery tasks at: `http://localhost:5555`

### Health Checks

```bash
# Check API health
curl http://localhost:8000/health

# Response
{
  "status": "healthy",
  "database": "healthy",
  "timestamp": 1234567890
}
```

---

## 🔐 Security

### Environment Variables

Store sensitive data in `.env`:
- Database credentials
- API keys
- Secret keys

### Production Recommendations

1. Use environment-specific `.env` files
2. Enable HTTPS/TLS
3. Implement authentication middleware
4. Encrypt connector credentials
5. Enable audit logging
6. Regular security updates

---

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=modules/pipeline --cov-report=html

# Run specific test
pytest tests/test_pipeline.py::test_create_pipeline
```

---

## 📚 API Documentation

### Interactive API Docs

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key Endpoints

#### Pipelines

- `POST /api/v1/pipelines` - Create pipeline
- `GET /api/v1/pipelines` - List pipelines
- `GET /api/v1/pipelines/{id}` - Get pipeline
- `PUT /api/v1/pipelines/{id}` - Update pipeline
- `DELETE /api/v1/pipelines/{id}` - Delete pipeline
- `POST /api/v1/pipelines/{id}/execute` - Execute pipeline

#### Connectors

- `POST /api/v1/pipelines/connectors` - Create connector
- `GET /api/v1/pipelines/connectors` - List connectors
- `POST /api/v1/pipelines/connectors/{id}/test` - Test connector

#### Executions

- `GET /api/v1/pipelines/executions/{id}` - Get execution
- `GET /api/v1/pipelines/{id}/executions` - List executions
- `POST /api/v1/pipelines/executions/{id}/cancel` - Cancel execution

---

## 🛠️ Development

### Project Structure

Follow the modular architecture:
- `models.py`: Database models
- `services.py`: Business logic
- `api.py`: REST endpoints
- `ui.py`: Streamlit UI
- `tasks.py`: Async tasks

### Adding a New Transformation

```python
# In modules/pipeline/transformations.py

class MyCustomTransformation(BaseTransformation):
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Your transformation logic
        return transformed_data

# Register transformation
TransformationFactory.register("my_custom", MyCustomTransformation)
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -am 'Add my feature'`
4. Push to branch: `git push origin feature/my-feature`
5. Submit a pull request

---

## 📝 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- Built with Streamlit, FastAPI, Celery, and Apache Airflow
- Powered by PostgreSQL and Redis
- AI capabilities by Anthropic Claude

---

## 📞 Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Version:** 1.0.0
**Last Updated:** 2024
