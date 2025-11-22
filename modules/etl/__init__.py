<<<<<<< HEAD
"""
NEXUS ETL Module - Production-ready Extract-Transform-Load system.

This module provides comprehensive ETL capabilities including:
- Data extraction from multiple sources (databases, files, APIs, cloud storage)
- Data transformation and validation
- Data loading to various targets
- Job scheduling and orchestration
- Monitoring and alerting
- RESTful API and web UI

Usage:
    from modules.etl import ETLPipeline, ExtractorFactory, LoaderFactory

    # Create extractor
    extractor = ExtractorFactory.create_extractor(data_source)

    # Extract data
    with extractor:
        data = extractor.extract(query="SELECT * FROM table")

    # Transform data
    transformer = DataCleaner(config)
    cleaned_data = transformer.transform(data)

    # Load data
    loader = LoaderFactory.create_loader(data_target)
    with loader:
        loader.load(cleaned_data)
"""

__version__ = "1.0.0"
__author__ = "NEXUS Platform Team"
__email__ = "etl@nexus-platform.com"

# Core pipeline components
from modules.etl.pipeline import (
    ETLPipeline,
    PipelineContext,
    StepExecutor,
    ErrorHandler,
    RetryLogic,
    PipelineException
)

# Extractors
from modules.etl.extractors import (
    BaseExtractor,
    DatabaseExtractor,
    MongoDBExtractor,
    FileExtractor,
    APIExtractor,
    WebExtractor,
    CloudStorageExtractor,
    ExtractorFactory,
    ExtractorException,
    ConnectionException,
    ExtractionException
)

# Transformers
from modules.etl.transformers import (
    BaseTransformer,
    DataCleaner,
    DataValidator,
    DataEnricher,
    DataAggregator,
    DataMapper,
    TypeConverter,
    CustomTransformer,
    TransformationPipeline,
    TransformerFactory,
    TransformerException,
    ValidationException
)

# Loaders
from modules.etl.loaders import (
    BaseLoader,
    DatabaseLoader,
    MongoDBLoader,
    FileLoader,
    APILoader,
    CloudLoader,
    StreamLoader,
    LoaderFactory,
    LoaderException,
    LoadException
)

# Mappings
from modules.etl.mappings import (
    FieldMapper,
    TypeConverter,
    SchemaMapper,
    TransformationRules,
    MappingException
)

# Validation
from modules.etl.validation import (
    ValidationResult,
    DataQualityCheck,
    SchemaValidator,
    BusinessRuleValidator,
    DataProfiler,
    ValidationException
)

# Job management
from modules.etl.jobs import (
    JobScheduler,
    JobExecutor,
    JobMonitor,
    JobHistory,
    JobException
)

# Monitoring
from modules.etl.monitoring import (
    ETLMetrics,
    JobMetrics,
    DataMetrics,
    Alerting,
    Alert,
    PerformanceMonitor
)

# Database models
from modules.etl.models import (
    DataSource,
    DataTarget,
    Mapping,
    ETLJob,
    JobRun,
    AuditLog,
    ETLTemplate,
    DataQualityRule,
    SourceType,
    DatabaseType,
    JobStatus,
    LoadStrategy,
    create_tables,
    drop_tables
)

# Pydantic schemas
from modules.etl import schemas

# Public API
__all__ = [
    # Version
    "__version__",

    # Pipeline
    "ETLPipeline",
    "PipelineContext",
    "StepExecutor",
    "ErrorHandler",
    "RetryLogic",

    # Extractors
    "BaseExtractor",
    "DatabaseExtractor",
    "MongoDBExtractor",
    "FileExtractor",
    "APIExtractor",
    "WebExtractor",
    "CloudStorageExtractor",
    "ExtractorFactory",

    # Transformers
    "BaseTransformer",
    "DataCleaner",
    "DataValidator",
    "DataEnricher",
    "DataAggregator",
    "DataMapper",
    "TypeConverter",
    "TransformationPipeline",
    "TransformerFactory",

    # Loaders
    "BaseLoader",
    "DatabaseLoader",
    "MongoDBLoader",
    "FileLoader",
    "APILoader",
    "CloudLoader",
    "LoaderFactory",

    # Mappings
    "FieldMapper",
    "SchemaMapper",
    "TransformationRules",

    # Validation
    "ValidationResult",
    "DataQualityCheck",
    "SchemaValidator",
    "BusinessRuleValidator",
    "DataProfiler",

    # Jobs
    "JobScheduler",
    "JobExecutor",
    "JobMonitor",
    "JobHistory",

    # Monitoring
    "ETLMetrics",
    "JobMetrics",
    "DataMetrics",
    "Alerting",
    "Alert",
    "PerformanceMonitor",

    # Models
    "DataSource",
    "DataTarget",
    "Mapping",
    "ETLJob",
    "JobRun",
    "AuditLog",
    "ETLTemplate",
    "DataQualityRule",
    "SourceType",
    "DatabaseType",
    "JobStatus",
    "LoadStrategy",
    "create_tables",
    "drop_tables",

    # Schemas
    "schemas",

    # Exceptions
    "PipelineException",
    "ExtractorException",
    "TransformerException",
    "LoaderException",
    "MappingException",
    "ValidationException",
    "JobException"
]


def get_version():
    """Get ETL module version."""
    return __version__


def setup_logging(level="INFO", log_file=None):
    """
    Configure logging for ETL module.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
    """
    import logging
    import sys

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Get root logger
    logger = logging.getLogger("modules.etl")
    logger.setLevel(getattr(logging, level.upper()))
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.info(f"ETL Module v{__version__} logging initialized")


def create_engine_and_tables(database_url: str):
    """
    Create database engine and initialize tables.

    Args:
        database_url: Database connection URL

    Returns:
        SQLAlchemy engine instance
    """
    from sqlalchemy import create_engine as sa_create_engine

    engine = sa_create_engine(database_url)
    create_tables(engine)

    return engine


def quick_start_example():
    """
    Quick start example for using the ETL module.

    Returns:
        Example code as string
    """
    return '''
# Quick Start Example - NEXUS ETL Module

from modules.etl import (
    ETLPipeline,
    ExtractorFactory,
    TransformerFactory,
    LoaderFactory,
    DataSource,
    DataTarget,
    SourceType,
    DatabaseType
)

# 1. Create data source
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

# 2. Create data target
target = DataTarget(
    name="PostgreSQL Target",
    target_type=SourceType.DATABASE,
    database_type=DatabaseType.POSTGRESQL,
    host="localhost",
    port=5432,
    database_name="target_db",
    username="user",
    password="password"
)

# 3. Extract data
extractor = ExtractorFactory.create_extractor(source)
with extractor:
    data = extractor.extract(query="SELECT * FROM customers")

# 4. Transform data
transformer = TransformerFactory.create_transformer("cleaner", {
    "trim_whitespace": True,
    "remove_duplicates": True
})
transformed_data = transformer.transform(data)

# 5. Load data
loader = LoaderFactory.create_loader(target, {"table_name": "customers"})
with loader:
    records_loaded = loader.load(transformed_data)

print(f"Successfully loaded {records_loaded} records!")

# Or use ETLPipeline for full orchestration
from modules.etl.models import ETLJob

job = ETLJob(
    name="Customer Migration",
    source=source,
    target=target,
    extraction_query="SELECT * FROM customers",
    load_strategy=LoadStrategy.UPSERT
)

pipeline = ETLPipeline(job)
result = pipeline.execute()
'''


# Module initialization
def init():
    """Initialize ETL module."""
    setup_logging(level="INFO")


# Auto-initialize on import (optional)
# init()
=======
"""ETL Module - Extract, Transform, Load functionality."""
>>>>>>> origin/claude/build-etl-integration-hub-01CuRDV55w16up98jJhFz8Ts
