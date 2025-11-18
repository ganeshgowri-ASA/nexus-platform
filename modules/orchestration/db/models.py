"""SQLAlchemy database models for workflow orchestration."""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, Integer, String, DateTime, JSON, Text,
    ForeignKey, Boolean, Float, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    CREATED = "created"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """Task type definitions."""
    PYTHON = "python"
    HTTP = "http"
    BASH = "bash"
    SQL = "sql"
    DOCKER = "docker"
    CUSTOM = "custom"


class Workflow(Base):
    """Workflow definition and execution."""
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # DAG definition (stores the workflow structure)
    dag_definition = Column(JSON, nullable=False)

    # Workflow configuration
    config = Column(JSON, nullable=True, default={})

    # Scheduling
    schedule_cron = Column(String(100), nullable=True)
    is_scheduled = Column(Boolean, default=False)

    # Status and execution
    status = Column(SQLEnum(WorkflowStatus), default=WorkflowStatus.CREATED, index=True)
    current_run_id = Column(String(255), nullable=True)

    # Metadata
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Statistics
    total_runs = Column(Integer, default=0)
    successful_runs = Column(Integer, default=0)
    failed_runs = Column(Integer, default=0)

    # Tags and categorization
    tags = Column(JSON, default=[])
    category = Column(String(100), nullable=True)

    # Relationships
    tasks = relationship("Task", back_populates="workflow", cascade="all, delete-orphan")
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")


class Task(Base):
    """Task definition within a workflow."""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False, index=True)

    # Task identification
    task_key = Column(String(255), nullable=False)  # Unique within workflow
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Task type and execution
    task_type = Column(SQLEnum(TaskType), nullable=False)
    executor = Column(String(100), nullable=False)  # celery, temporal, etc.

    # Task configuration
    config = Column(JSON, nullable=False, default={})
    parameters = Column(JSON, nullable=True, default={})

    # Dependencies (list of task_keys this task depends on)
    depends_on = Column(JSON, default=[])

    # Retry configuration
    max_retries = Column(Integer, default=3)
    retry_delay = Column(Integer, default=60)  # seconds
    timeout = Column(Integer, default=3600)  # seconds

    # Conditions
    run_condition = Column(Text, nullable=True)  # Python expression

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    workflow = relationship("Workflow", back_populates="tasks")
    executions = relationship("TaskExecution", back_populates="task", cascade="all, delete-orphan")


class WorkflowExecution(Base):
    """Workflow execution instance."""
    __tablename__ = "workflow_executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False, index=True)

    # Execution identification
    run_id = Column(String(255), unique=True, nullable=False, index=True)

    # Status and timing
    status = Column(SQLEnum(WorkflowStatus), default=WorkflowStatus.RUNNING, index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration = Column(Float, nullable=True)  # seconds

    # Execution context
    triggered_by = Column(String(255), nullable=True)  # manual, scheduled, api
    trigger_metadata = Column(JSON, nullable=True, default={})

    # Input/Output
    input_data = Column(JSON, nullable=True, default={})
    output_data = Column(JSON, nullable=True, default={})

    # Error handling
    error_message = Column(Text, nullable=True)
    error_stack_trace = Column(Text, nullable=True)

    # Statistics
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)

    # Relationships
    workflow = relationship("Workflow", back_populates="executions")
    task_executions = relationship("TaskExecution", back_populates="workflow_execution", cascade="all, delete-orphan")


class TaskExecution(Base):
    """Task execution instance."""
    __tablename__ = "task_executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_execution_id = Column(Integer, ForeignKey("workflow_executions.id"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)

    # Execution identification
    execution_id = Column(String(255), unique=True, nullable=False, index=True)

    # Status and timing
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration = Column(Float, nullable=True)  # seconds

    # Retry tracking
    retry_count = Column(Integer, default=0)

    # Execution details
    worker_id = Column(String(255), nullable=True)
    celery_task_id = Column(String(255), nullable=True, index=True)

    # Input/Output
    input_data = Column(JSON, nullable=True, default={})
    output_data = Column(JSON, nullable=True, default={})

    # Error handling
    error_message = Column(Text, nullable=True)
    error_stack_trace = Column(Text, nullable=True)

    # Logs
    logs = Column(Text, nullable=True)

    # Relationships
    workflow_execution = relationship("WorkflowExecution", back_populates="task_executions")
    task = relationship("Task", back_populates="executions")


class ScheduledWorkflow(Base):
    """Scheduled workflow executions."""
    __tablename__ = "scheduled_workflows"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False, index=True)

    # Schedule configuration
    cron_expression = Column(String(100), nullable=False)
    timezone = Column(String(50), default="UTC")

    # Status
    is_active = Column(Boolean, default=True)

    # Execution tracking
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class WorkflowNotification(Base):
    """Notification configuration for workflows."""
    __tablename__ = "workflow_notifications"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False, index=True)

    # Notification type
    notification_type = Column(String(50), nullable=False)  # email, slack, webhook

    # Trigger conditions
    on_success = Column(Boolean, default=False)
    on_failure = Column(Boolean, default=True)
    on_start = Column(Boolean, default=False)

    # Configuration
    config = Column(JSON, nullable=False, default={})

    # Status
    is_active = Column(Boolean, default=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
