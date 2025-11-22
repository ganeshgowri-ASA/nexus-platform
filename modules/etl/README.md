# NEXUS ETL Module

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)

Production-ready Extract-Transform-Load (ETL) module for the NEXUS platform with comprehensive data integration capabilities.

## 🚀 Features

### Data Extraction
- **Multiple Sources**: Databases (PostgreSQL, MySQL, MongoDB, SQL Server, Oracle, SQLite), Files (CSV, JSON, Excel, Parquet), REST APIs, Web Scraping, Cloud Storage (AWS S3, Azure Blob, Google Cloud Storage)
- **Incremental Extraction**: Delta/change data capture with watermark tracking
- **Connection Management**: Robust connection pooling and retry logic

### Data Transformation
- **Data Cleaning**: Null handling, whitespace trimming, duplicate removal
- **Validation**: Schema validation, business rules, data quality checks
- **Enrichment**: Computed fields, lookups, aggregations
- **Mapping**: Field mapping, type conversion, schema transformation

### Data Loading
- **Multiple Targets**: Same variety as extraction sources
- **Load Strategies**: Full, Incremental, Upsert, Append, Replace
- **Batch Processing**: Configurable batch sizes for optimal performance

### Pipeline Orchestration
- **Multi-Step Pipelines**: Chain extraction, transformation, and loading
- **Error Handling**: Comprehensive error recovery and retry logic
- **Parallel Processing**: Multi-threaded execution for improved performance

### Job Scheduling
- **Cron Scheduling**: Standard cron expressions for job scheduling
- **Event-Triggered**: Execute jobs based on events
- **Dependencies**: Define job dependencies and execution order

### Monitoring & Alerting
- **Real-Time Metrics**: Job status, execution time, records processed
- **Data Quality Metrics**: Completeness, accuracy, validity scores
- **Alerts**: Email and Slack notifications for failures and anomalies
- **Audit Trail**: Complete lineage tracking and change history

### User Interfaces
- **REST API**: FastAPI-based RESTful API for programmatic access
- **Web Dashboard**: Streamlit-based interactive dashboard
- **WebSocket**: Real-time job status updates

## 📦 Installation

```bash
# Clone repository
git clone https://github.com/nexus-platform/nexus.git
cd nexus-platform/modules/etl

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from modules.etl import create_engine_and_tables; create_engine_and_tables('postgresql://user:pass@localhost/nexus_etl')"
```

## 🔧 Quick Start

### Basic ETL Pipeline

```python
from modules.etl import (
    ETLPipeline,
    ExtractorFactory,
    TransformerFactory,
    LoaderFactory,
    DataSource,
    DataTarget,
    SourceType,
    DatabaseType,
    LoadStrategy
)

# 1. Define data source
source = DataSource(
    name="MySQL Source",
    source_type=SourceType.DATABASE,
    database_type=DatabaseType.MYSQL,
    host="localhost",
    port=3306,
    database_name="source_db",
    username="user",
    password="password"
)

# 2. Define data target
target = DataTarget(
    name="PostgreSQL Target",
    target_type=SourceType.DATABASE,
    database_type=DatabaseType.POSTGRESQL,
    host="localhost",
    port=5432,
    database_name="target_db",
    username="user",
    password="password",
    load_strategy=LoadStrategy.UPSERT
)

# 3. Extract data
extractor = ExtractorFactory.create_extractor(source)
with extractor:
    data = extractor.extract(query="SELECT * FROM customers")

# 4. Transform data
cleaner = TransformerFactory.create_transformer("cleaner", {
    "trim_whitespace": True,
    "remove_duplicates": True
})
cleaned_data = cleaner.transform(data)

# 5. Load data
loader = LoaderFactory.create_loader(target, {"table_name": "customers"})
with loader:
    records_loaded = loader.load(cleaned_data)

print(f"Successfully loaded {records_loaded} records!")
```

### Using ETL Jobs

```python
from modules.etl import ETLJob, ETLPipeline
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create database session
engine = create_engine("postgresql://user:pass@localhost/nexus_etl")
Session = sessionmaker(bind=engine)
db_session = Session()

# Create ETL job
job = ETLJob(
    name="Customer Data Sync",
    source_id=1,  # Source ID from database
    target_id=2,  # Target ID from database
    extraction_query="SELECT * FROM customers WHERE updated_at > :last_watermark",
    is_incremental=True,
    watermark_column="updated_at",
    load_strategy=LoadStrategy.UPSERT,
    schedule_cron="0 2 * * *",  # Daily at 2 AM
    is_scheduled=True
)

db_session.add(job)
db_session.commit()

# Execute job
pipeline = ETLPipeline(job, db_session)
result = pipeline.execute()

print(f"Job status: {result['status']}")
print(f"Records processed: {result['metrics']['records_loaded']}")
```

### REST API Usage

```bash
# Start API server
uvicorn modules.etl.api:router --host 0.0.0.0 --port 8000

# Create data source
curl -X POST http://localhost:8000/api/v1/etl/sources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MySQL Source",
    "source_type": "database",
    "database_type": "mysql",
    "host": "localhost",
    "port": 3306,
    "database_name": "mydb"
  }'

# List all jobs
curl http://localhost:8000/api/v1/etl/jobs

# Execute job
curl -X POST http://localhost:8000/api/v1/etl/jobs/1/execute

# Get job metrics
curl http://localhost:8000/api/v1/etl/jobs/1/metrics?days=7
```

### Streamlit Dashboard

```bash
# Start dashboard
streamlit run modules/etl/ui.py

# Access at http://localhost:8501
```

## 📊 Architecture

```
modules/etl/
├── __init__.py          # Module initialization and public API
├── models.py            # SQLAlchemy database models
├── schemas.py           # Pydantic validation schemas
├── extractors.py        # Data extraction from sources
├── transformers.py      # Data transformation logic
├── loaders.py           # Data loading to targets
├── mappings.py          # Field and schema mapping
├── validation.py        # Data quality validation
├── pipeline.py          # Pipeline orchestration
├── jobs.py              # Job scheduling and execution
├── monitoring.py        # Metrics and alerting
├── tasks.py             # Celery async tasks
├── api.py               # FastAPI REST endpoints
├── ui.py                # Streamlit dashboard
└── tests/               # Pytest test suite
    ├── conftest.py      # Test fixtures
    ├── test_transformers.py
    └── test_validation.py
```

## 🧪 Testing

```bash
# Run all tests
pytest modules/etl/tests/

# Run with coverage
pytest modules/etl/tests/ --cov=modules.etl --cov-report=html

# Run specific test file
pytest modules/etl/tests/test_transformers.py -v
```

## 📖 Documentation

### Data Sources

Supported data sources:
- **Relational Databases**: PostgreSQL, MySQL, SQL Server, Oracle, SQLite
- **NoSQL Databases**: MongoDB, Redis
- **Files**: CSV, JSON, Excel (XLSX/XLS), Parquet
- **APIs**: REST APIs with custom authentication
- **Web**: HTML scraping with BeautifulSoup
- **Cloud Storage**: AWS S3, Azure Blob Storage, Google Cloud Storage

### Transformations

Available transformers:
- `DataCleaner`: Remove nulls, trim whitespace, handle outliers
- `DataValidator`: Schema validation, type checking, business rules
- `DataEnricher`: Add computed fields, lookups, timestamps
- `DataAggregator`: Group by and aggregate data
- `DataMapper`: Map fields between schemas
- `TypeConverter`: Convert data types

### Load Strategies

- `FULL`: Truncate target and load all data
- `INCREMENTAL`: Load only new/changed records
- `UPSERT`: Insert new records, update existing
- `APPEND`: Append all records to target
- `REPLACE`: Drop and recreate target table

### Monitoring

Key metrics:
- Job execution statistics (success rate, duration, throughput)
- Data quality scores (completeness, accuracy, validity)
- System health (running jobs, failures, bottlenecks)
- Performance trends (execution time, records processed)

## 🔐 Security

- **Credential Encryption**: Sensitive data encrypted at rest
- **RBAC**: Role-based access control (integration ready)
- **Audit Logs**: Complete audit trail of all operations
- **Secure Connections**: SSL/TLS support for database connections

## ⚙️ Configuration

### Environment Variables

```bash
# Database
NEXUS_ETL_DB_URL=postgresql://user:pass@localhost/nexus_etl

# Redis (for Celery)
NEXUS_ETL_REDIS_URL=redis://localhost:6379/0

# Email notifications
NEXUS_ETL_SMTP_HOST=smtp.gmail.com
NEXUS_ETL_SMTP_PORT=587
NEXUS_ETL_SMTP_USERNAME=your_email@gmail.com
NEXUS_ETL_SMTP_PASSWORD=your_password

# Slack notifications
NEXUS_ETL_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Logging
NEXUS_ETL_LOG_LEVEL=INFO
NEXUS_ETL_LOG_FILE=/var/log/nexus-etl.log
```

## 🚀 Production Deployment

### Using Docker

```bash
# Build image
docker build -t nexus-etl:latest .

# Run container
docker run -d \
  --name nexus-etl \
  -e NEXUS_ETL_DB_URL=postgresql://user:pass@db:5432/nexus_etl \
  -p 8000:8000 \
  nexus-etl:latest
```

### Using Docker Compose

```yaml
version: '3.8'

services:
  api:
    image: nexus-etl:latest
    ports:
      - "8000:8000"
    environment:
      - NEXUS_ETL_DB_URL=postgresql://user:pass@postgres:5432/nexus_etl
      - NEXUS_ETL_REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  celery_worker:
    image: nexus-etl:latest
    command: celery -A modules.etl.tasks worker --loglevel=info
    environment:
      - NEXUS_ETL_DB_URL=postgresql://user:pass@postgres:5432/nexus_etl
      - NEXUS_ETL_REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  celery_beat:
    image: nexus-etl:latest
    command: celery -A modules.etl.tasks beat --loglevel=info
    environment:
      - NEXUS_ETL_DB_URL=postgresql://user:pass@postgres:5432/nexus_etl
      - NEXUS_ETL_REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:14
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=nexus_etl
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 💬 Support

- Documentation: https://docs.nexus-platform.com/etl
- Issues: https://github.com/nexus-platform/nexus/issues
- Email: support@nexus-platform.com
- Slack: https://nexus-platform.slack.com

## 🙏 Acknowledgments

- Built with FastAPI, SQLAlchemy, Pandas, and Streamlit
- Inspired by Apache Airflow, dbt, and Prefect
- Part of the NEXUS AI-powered productivity platform

---

**NEXUS ETL** - Production-ready data integration for modern enterprises
