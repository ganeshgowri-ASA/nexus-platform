"""
SQLAlchemy models for ETL module.

This module defines database models for managing ETL jobs, data sources,
targets, mappings, job runs, and audit trails.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text, JSON,
    ForeignKey, Enum, Float, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class SourceType(str, PyEnum):
    """Enumeration of supported data source types."""
    DATABASE = "database"
    FILE = "file"
    API = "api"
    WEB = "web"
    CLOUD_STORAGE = "cloud_storage"
    STREAM = "stream"


class DatabaseType(str, PyEnum):
    """Enumeration of supported database types."""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    SQLITE = "sqlite"
    MSSQL = "mssql"
    ORACLE = "oracle"
    REDIS = "redis"


class JobStatus(str, PyEnum):
    """Enumeration of job execution statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class LoadStrategy(str, PyEnum):
    """Enumeration of data loading strategies."""
    FULL = "full"
    INCREMENTAL = "incremental"
    UPSERT = "upsert"
    APPEND = "append"
    REPLACE = "replace"


class DataSource(Base):
    """Model for data sources configuration."""

    __tablename__ = "etl_data_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    source_type = Column(Enum(SourceType), nullable=False, index=True)
    database_type = Column(Enum(DatabaseType), nullable=True)

    # Connection details (encrypted)
    connection_string = Column(Text, nullable=True)  # Encrypted
    host = Column(String(255), nullable=True)
    port = Column(Integer, nullable=True)
    database_name = Column(String(255), nullable=True)
    username = Column(String(255), nullable=True)
    password = Column(Text, nullable=True)  # Encrypted

    # Additional configuration
    config = Column(JSON, nullable=True, default={})

    # File/Cloud storage specific
    file_path = Column(String(500), nullable=True)
    bucket_name = Column(String(255), nullable=True)
    region = Column(String(100), nullable=True)

    # API specific
    api_url = Column(String(500), nullable=True)
    api_key = Column(Text, nullable=True)  # Encrypted
    headers = Column(JSON, nullable=True, default={})

    # Metadata
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_by = Column(Integer, nullable=True)  # Foreign key to user
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    jobs_as_source = relationship("ETLJob", back_populates="source", foreign_keys="ETLJob.source_id")

    __table_args__ = (
        Index('idx_source_type_active', 'source_type', 'is_active'),
    )


class DataTarget(Base):
    """Model for data targets configuration."""

    __tablename__ = "etl_data_targets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    target_type = Column(Enum(SourceType), nullable=False, index=True)
    database_type = Column(Enum(DatabaseType), nullable=True)

    # Connection details (encrypted)
    connection_string = Column(Text, nullable=True)
    host = Column(String(255), nullable=True)
    port = Column(Integer, nullable=True)
    database_name = Column(String(255), nullable=True)
    username = Column(String(255), nullable=True)
    password = Column(Text, nullable=True)  # Encrypted

    # Additional configuration
    config = Column(JSON, nullable=True, default={})

    # File/Cloud storage specific
    file_path = Column(String(500), nullable=True)
    bucket_name = Column(String(255), nullable=True)
    region = Column(String(100), nullable=True)

    # API specific
    api_url = Column(String(500), nullable=True)
    api_key = Column(Text, nullable=True)  # Encrypted
    headers = Column(JSON, nullable=True, default={})

    # Load strategy
    load_strategy = Column(Enum(LoadStrategy), default=LoadStrategy.APPEND)

    # Metadata
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    jobs_as_target = relationship("ETLJob", back_populates="target", foreign_keys="ETLJob.target_id")


class Mapping(Base):
    """Model for field and schema mappings."""

    __tablename__ = "etl_mappings"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)

    # Source and target schemas
    source_schema = Column(JSON, nullable=True, default={})
    target_schema = Column(JSON, nullable=True, default={})

    # Field mappings: {"source_field": "target_field", ...}
    field_mappings = Column(JSON, nullable=False, default={})

    # Type conversions: {"field": "target_type", ...}
    type_conversions = Column(JSON, nullable=True, default={})

    # Transformation rules: {"field": "transformation_function", ...}
    transformation_rules = Column(JSON, nullable=True, default={})

    # Default values: {"field": "default_value", ...}
    default_values = Column(JSON, nullable=True, default={})

    # Metadata
    is_active = Column(Boolean, default=True, index=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    jobs = relationship("ETLJob", back_populates="mapping")


class ETLJob(Base):
    """Model for ETL job definitions."""

    __tablename__ = "etl_jobs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)

    # Source and target references
    source_id = Column(Integer, ForeignKey("etl_data_sources.id"), nullable=False, index=True)
    target_id = Column(Integer, ForeignKey("etl_data_targets.id"), nullable=False, index=True)
    mapping_id = Column(Integer, ForeignKey("etl_mappings.id"), nullable=True, index=True)

    # Extraction configuration
    extraction_query = Column(Text, nullable=True)  # SQL query or filter
    extraction_config = Column(JSON, nullable=True, default={})

    # Transformation configuration
    transformation_steps = Column(JSON, nullable=True, default=[])

    # Loading configuration
    load_strategy = Column(Enum(LoadStrategy), default=LoadStrategy.APPEND)
    batch_size = Column(Integer, default=1000)

    # Incremental load configuration
    is_incremental = Column(Boolean, default=False)
    watermark_column = Column(String(255), nullable=True)
    last_watermark_value = Column(String(255), nullable=True)

    # Scheduling
    schedule_cron = Column(String(100), nullable=True)
    is_scheduled = Column(Boolean, default=False, index=True)

    # Retry configuration
    max_retries = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=300)

    # Notification configuration
    notify_on_success = Column(Boolean, default=False)
    notify_on_failure = Column(Boolean, default=True)
    notification_emails = Column(JSON, nullable=True, default=[])
    notification_slack_webhook = Column(String(500), nullable=True)

    # Performance settings
    parallel_workers = Column(Integer, default=1)
    timeout_seconds = Column(Integer, default=3600)

    # Metadata
    is_active = Column(Boolean, default=True, index=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_run_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    source = relationship("DataSource", back_populates="jobs_as_source", foreign_keys=[source_id])
    target = relationship("DataTarget", back_populates="jobs_as_target", foreign_keys=[target_id])
    mapping = relationship("Mapping", back_populates="jobs")
    runs = relationship("JobRun", back_populates="job", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_job_active_scheduled', 'is_active', 'is_scheduled'),
    )


class JobRun(Base):
    """Model for ETL job execution history."""

    __tablename__ = "etl_job_runs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("etl_jobs.id"), nullable=False, index=True)

    # Execution details
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Statistics
    records_extracted = Column(Integer, default=0)
    records_transformed = Column(Integer, default=0)
    records_loaded = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)

    # Error tracking
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)
    error_count = Column(Integer, default=0)

    # Retry tracking
    retry_count = Column(Integer, default=0)
    parent_run_id = Column(Integer, ForeignKey("etl_job_runs.id"), nullable=True)

    # Data quality metrics
    data_quality_score = Column(Float, nullable=True)
    validation_errors = Column(JSON, nullable=True, default=[])

    # Watermark tracking
    watermark_value = Column(String(255), nullable=True)

    # Execution metadata
    execution_context = Column(JSON, nullable=True, default={})
    triggered_by = Column(String(100), nullable=True)  # 'schedule', 'manual', 'api', 'event'
    triggered_by_user = Column(Integer, nullable=True)

    # Performance metrics
    extraction_time_seconds = Column(Float, nullable=True)
    transformation_time_seconds = Column(Float, nullable=True)
    loading_time_seconds = Column(Float, nullable=True)

    # Logs and artifacts
    log_file_path = Column(String(500), nullable=True)
    artifacts = Column(JSON, nullable=True, default={})

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job = relationship("ETLJob", back_populates="runs")
    retries = relationship("JobRun", remote_side=[id], backref="parent_run")
    audit_logs = relationship("AuditLog", back_populates="job_run", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_run_job_status', 'job_id', 'status'),
        Index('idx_run_created', 'created_at'),
    )


class AuditLog(Base):
    """Model for audit trail and data lineage."""

    __tablename__ = "etl_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    job_run_id = Column(Integer, ForeignKey("etl_job_runs.id"), nullable=False, index=True)

    # Event details
    event_type = Column(String(100), nullable=False, index=True)  # 'extraction', 'transformation', 'loading', 'error'
    event_timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Event data
    event_data = Column(JSON, nullable=True, default={})
    message = Column(Text, nullable=True)

    # Data lineage
    source_records = Column(JSON, nullable=True, default=[])
    target_records = Column(JSON, nullable=True, default=[])

    # Severity level
    severity = Column(String(20), default="info")  # 'debug', 'info', 'warning', 'error', 'critical'

    # User tracking
    user_id = Column(Integer, nullable=True)
    user_action = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job_run = relationship("JobRun", back_populates="audit_logs")

    __table_args__ = (
        Index('idx_audit_event_timestamp', 'event_type', 'event_timestamp'),
    )


class ETLTemplate(Base):
    """Model for ETL job templates."""

    __tablename__ = "etl_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)

    # Template configuration
    template_config = Column(JSON, nullable=False, default={})

    # Source/target type hints
    source_type = Column(Enum(SourceType), nullable=True)
    target_type = Column(Enum(SourceType), nullable=True)

    # Tags for searchability
    tags = Column(JSON, nullable=True, default=[])

    # Usage statistics
    usage_count = Column(Integer, default=0)

    # Metadata
    is_builtin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True, index=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index('idx_template_category_active', 'category', 'is_active'),
    )


class DataQualityRule(Base):
    """Model for data quality validation rules."""

    __tablename__ = "etl_data_quality_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)

    # Rule configuration
    rule_type = Column(String(100), nullable=False)  # 'null_check', 'range_check', 'pattern_check', 'uniqueness', 'custom'
    field_name = Column(String(255), nullable=True)
    rule_config = Column(JSON, nullable=False, default={})

    # Severity
    severity = Column(String(20), default="warning")  # 'info', 'warning', 'error', 'critical'

    # Action on failure
    fail_job_on_error = Column(Boolean, default=False)

    # Metadata
    is_active = Column(Boolean, default=True, index=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# Create all tables function
def create_tables(engine):
    """Create all ETL tables in the database."""
    Base.metadata.create_all(bind=engine)


def drop_tables(engine):
    """Drop all ETL tables from the database."""
    Base.metadata.drop_all(bind=engine)
