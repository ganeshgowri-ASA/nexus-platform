"""Database models for Pipeline module."""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, JSON,
    ForeignKey, Enum, Float, Index
)
from sqlalchemy.orm import relationship
from config.database import Base
import enum


class PipelineStatus(str, enum.Enum):
    """Pipeline status enum."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class ExecutionStatus(str, enum.Enum):
    """Execution status enum."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TriggerType(str, enum.Enum):
    """Trigger type enum."""
    MANUAL = "manual"
    SCHEDULE = "schedule"
    WEBHOOK = "webhook"
    EVENT = "event"


class Pipeline(Base):
    """Pipeline model."""

    __tablename__ = "pipelines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    status = Column(Enum(PipelineStatus), default=PipelineStatus.DRAFT, nullable=False)

    # Pipeline configuration
    config = Column(JSON, default={})
    tags = Column(JSON, default=[])

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(255))

    # Airflow integration
    airflow_dag_id = Column(String(255), unique=True, index=True)

    # Relationships
    steps = relationship("PipelineStep", back_populates="pipeline", cascade="all, delete-orphan")
    executions = relationship("PipelineExecution", back_populates="pipeline", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="pipeline", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Pipeline(id={self.id}, name='{self.name}', status='{self.status}')>"


class PipelineStep(Base):
    """Pipeline step model."""

    __tablename__ = "pipeline_steps"
    __table_args__ = (
        Index("idx_pipeline_order", "pipeline_id", "order"),
    )

    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, ForeignKey("pipelines.id"), nullable=False)

    name = Column(String(255), nullable=False)
    description = Column(Text)
    step_type = Column(String(50), nullable=False)  # extract, transform, load, custom
    order = Column(Integer, nullable=False)

    # Step configuration
    config = Column(JSON, default={})

    # Connector references
    source_connector_id = Column(Integer, ForeignKey("connectors.id"))
    destination_connector_id = Column(Integer, ForeignKey("connectors.id"))

    # Dependencies
    depends_on = Column(JSON, default=[])  # List of step IDs this step depends on

    # Retry configuration
    max_retries = Column(Integer, default=3)
    retry_delay = Column(Integer, default=60)  # seconds

    # Timeout
    timeout = Column(Integer, default=3600)  # seconds

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    pipeline = relationship("Pipeline", back_populates="steps")
    source_connector = relationship("Connector", foreign_keys=[source_connector_id])
    destination_connector = relationship("Connector", foreign_keys=[destination_connector_id])
    step_executions = relationship("StepExecution", back_populates="step", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PipelineStep(id={self.id}, name='{self.name}', type='{self.step_type}')>"


class PipelineExecution(Base):
    """Pipeline execution model."""

    __tablename__ = "pipeline_executions"
    __table_args__ = (
        Index("idx_pipeline_status", "pipeline_id", "status"),
        Index("idx_execution_time", "started_at", "completed_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, ForeignKey("pipelines.id"), nullable=False)

    status = Column(Enum(ExecutionStatus), default=ExecutionStatus.PENDING, nullable=False)
    trigger_type = Column(Enum(TriggerType), nullable=False)

    # Execution details
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration = Column(Float)  # seconds

    # Results
    records_processed = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    error_message = Column(Text)

    # Metadata
    execution_config = Column(JSON, default={})
    metrics = Column(JSON, default={})
    logs_path = Column(String(500))

    # Airflow execution ID
    airflow_run_id = Column(String(255), index=True)

    # Backfill info
    is_backfill = Column(Boolean, default=False)
    backfill_start_date = Column(DateTime)
    backfill_end_date = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    pipeline = relationship("Pipeline", back_populates="executions")
    step_executions = relationship("StepExecution", back_populates="pipeline_execution", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PipelineExecution(id={self.id}, pipeline_id={self.pipeline_id}, status='{self.status}')>"


class StepExecution(Base):
    """Step execution model."""

    __tablename__ = "step_executions"
    __table_args__ = (
        Index("idx_pipeline_execution_step", "pipeline_execution_id", "step_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    pipeline_execution_id = Column(Integer, ForeignKey("pipeline_executions.id"), nullable=False)
    step_id = Column(Integer, ForeignKey("pipeline_steps.id"), nullable=False)

    status = Column(Enum(ExecutionStatus), default=ExecutionStatus.PENDING, nullable=False)

    # Execution details
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration = Column(Float)  # seconds

    # Results
    records_processed = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    error_message = Column(Text)

    # Retry tracking
    retry_count = Column(Integer, default=0)

    # Metrics
    metrics = Column(JSON, default={})

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    pipeline_execution = relationship("PipelineExecution", back_populates="step_executions")
    step = relationship("PipelineStep", back_populates="step_executions")

    def __repr__(self):
        return f"<StepExecution(id={self.id}, step_id={self.step_id}, status='{self.status}')>"


class Connector(Base):
    """Data connector model."""

    __tablename__ = "connectors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    connector_type = Column(String(50), nullable=False)  # database, api, file, s3, etc.

    # Connection configuration (encrypted in production)
    config = Column(JSON, default={})

    # Credentials reference (should be stored securely)
    credentials = Column(JSON, default={})

    # Status
    is_active = Column(Boolean, default=True)
    last_tested_at = Column(DateTime)
    last_test_status = Column(String(50))

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(255))

    def __repr__(self):
        return f"<Connector(id={self.id}, name='{self.name}', type='{self.connector_type}')>"


class Schedule(Base):
    """Pipeline schedule model."""

    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, ForeignKey("pipelines.id"), nullable=False)

    # Schedule configuration
    cron_expression = Column(String(100), nullable=False)
    timezone = Column(String(50), default="UTC")

    # Status
    is_active = Column(Boolean, default=True)

    # Execution window
    start_date = Column(DateTime)
    end_date = Column(DateTime)

    # Next/Last execution
    next_execution_at = Column(DateTime)
    last_execution_at = Column(DateTime)

    # Backfill configuration
    allow_backfill = Column(Boolean, default=False)
    max_backfill_window = Column(Integer)  # days

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    pipeline = relationship("Pipeline", back_populates="schedules")

    def __repr__(self):
        return f"<Schedule(id={self.id}, pipeline_id={self.pipeline_id}, cron='{self.cron_expression}')>"
