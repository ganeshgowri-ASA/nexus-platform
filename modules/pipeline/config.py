"""Configuration for Pipeline module."""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class PipelineConfig:
    """Pipeline module configuration."""

    # Pipeline limits
    MAX_PIPELINE_STEPS: int = 100
    MAX_CONCURRENT_EXECUTIONS: int = 10
    MAX_RETRY_ATTEMPTS: int = 3

    # Timeouts (in seconds)
    STEP_TIMEOUT: int = 3600  # 1 hour
    PIPELINE_TIMEOUT: int = 86400  # 24 hours

    # Scheduling
    MIN_SCHEDULE_INTERVAL: int = 60  # 1 minute
    SUPPORTED_TRIGGERS: List[str] = field(default_factory=lambda: [
        "manual",
        "schedule",
        "webhook",
        "event"
    ])

    # Retry policy
    RETRY_POLICY: Dict[str, Any] = field(default_factory=lambda: {
        "max_retries": 3,
        "retry_delay": 60,  # seconds
        "exponential_backoff": True,
        "backoff_multiplier": 2
    })

    # Monitoring
    ENABLE_METRICS: bool = True
    ENABLE_LOGGING: bool = True
    METRICS_RETENTION_DAYS: int = 30

    # Connectors
    SUPPORTED_SOURCE_TYPES: List[str] = field(default_factory=lambda: [
        "database",
        "api",
        "file",
        "s3",
        "gcs",
        "azure_blob",
        "kafka",
        "redis",
        "http",
        "ftp",
        "sftp"
    ])

    SUPPORTED_DESTINATION_TYPES: List[str] = field(default_factory=lambda: [
        "database",
        "api",
        "file",
        "s3",
        "gcs",
        "azure_blob",
        "kafka",
        "redis",
        "email",
        "webhook"
    ])

    # Transformations
    SUPPORTED_TRANSFORMATIONS: List[str] = field(default_factory=lambda: [
        "filter",
        "map",
        "aggregate",
        "join",
        "sort",
        "deduplicate",
        "validation",
        "enrichment",
        "custom_python",
        "custom_sql"
    ])

    # Airflow integration
    AIRFLOW_ENABLED: bool = True
    AIRFLOW_DAG_FOLDER: str = "./airflow/dags"
    AIRFLOW_SYNC_INTERVAL: int = 300  # 5 minutes

    # Celery configuration
    CELERY_TASK_TIME_LIMIT: int = 7200  # 2 hours
    CELERY_TASK_SOFT_TIME_LIMIT: int = 3600  # 1 hour


pipeline_config = PipelineConfig()
