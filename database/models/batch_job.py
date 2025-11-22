"""Batch processing database models."""

import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey,
    JSON, Text, Enum, Float
)
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class JobStatus(str, enum.Enum):
    """Batch job status enum."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class TaskStatus(str, enum.Enum):
    """Batch task status enum."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"


class BatchJob(Base, TimestampMixin):
    """Batch job model."""

    __tablename__ = "batch_jobs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(
        Enum(JobStatus),
        default=JobStatus.PENDING,
        nullable=False,
        index=True
    )

    # Job configuration
    job_type = Column(String(100), nullable=False)  # csv_import, data_transform, etc.
    config = Column(JSON, nullable=True)  # Job-specific configuration

    # Progress tracking
    total_items = Column(Integer, default=0, nullable=False)
    processed_items = Column(Integer, default=0, nullable=False)
    successful_items = Column(Integer, default=0, nullable=False)
    failed_items = Column(Integer, default=0, nullable=False)
    skipped_items = Column(Integer, default=0, nullable=False)

    # Progress percentage (0-100)
    progress_percentage = Column(Float, default=0.0, nullable=False)

    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    estimated_completion = Column(DateTime, nullable=True)

    # Results and metadata
    result_summary = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)

    # File references
    input_file_path = Column(String(500), nullable=True)
    output_file_path = Column(String(500), nullable=True)
    error_log_path = Column(String(500), nullable=True)

    # Celery task ID
    celery_task_id = Column(String(255), nullable=True, index=True)

    # User information (placeholder for future auth)
    created_by = Column(String(255), nullable=True)

    # Relationships
    tasks = relationship(
        "BatchTask",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    def __repr__(self):
        return f"<BatchJob(id={self.id}, name='{self.name}', status={self.status})>"

    @property
    def duration_seconds(self) -> float:
        """Calculate job duration in seconds."""
        if not self.started_at:
            return 0.0
        end_time = self.completed_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()

    @property
    def is_terminal_state(self) -> bool:
        """Check if job is in a terminal state."""
        return self.status in [
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED
        ]


class BatchTask(Base, TimestampMixin):
    """Individual task within a batch job."""

    __tablename__ = "batch_tasks"

    id = Column(Integer, primary_key=True, index=True)
    batch_job_id = Column(
        Integer,
        ForeignKey("batch_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Task identification
    task_number = Column(Integer, nullable=False)  # Sequential number within job
    task_name = Column(String(255), nullable=True)

    # Status and retry
    status = Column(
        Enum(TaskStatus),
        default=TaskStatus.PENDING,
        nullable=False,
        index=True
    )
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)

    # Data
    input_data = Column(JSON, nullable=True)  # Input data for this task
    output_data = Column(JSON, nullable=True)  # Result data

    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)

    # Metadata
    metadata = Column(JSON, nullable=True)

    # Celery task ID
    celery_task_id = Column(String(255), nullable=True, index=True)

    # Relationships
    job = relationship("BatchJob", back_populates="tasks")

    def __repr__(self):
        return (
            f"<BatchTask(id={self.id}, job_id={self.batch_job_id}, "
            f"task_number={self.task_number}, status={self.status})>"
        )

    @property
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return (
            self.status == TaskStatus.FAILED and
            self.retry_count < self.max_retries
        )
