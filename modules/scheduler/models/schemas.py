"""SQLAlchemy models for scheduler"""
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text, JSON,
    ForeignKey, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from modules.scheduler.models.database import Base


class JobStatus(str, enum.Enum):
    """Job execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class JobType(str, enum.Enum):
    """Job scheduling type"""
    CRON = "cron"
    INTERVAL = "interval"
    DATE = "date"
    CALENDAR = "calendar"


class NotificationChannel(str, enum.Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


class ScheduledJob(Base):
    """Main scheduled job model"""
    __tablename__ = "scheduled_jobs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)

    # Scheduling
    job_type = Column(SQLEnum(JobType), nullable=False, default=JobType.CRON)
    cron_expression = Column(String(100))  # For cron jobs
    interval_seconds = Column(Integer)  # For interval jobs
    scheduled_time = Column(DateTime(timezone=True))  # For one-time jobs
    calendar_rule = Column(JSON)  # For calendar-based scheduling

    # Job configuration
    task_name = Column(String(255), nullable=False)  # Celery task name
    task_args = Column(JSON, default=list)
    task_kwargs = Column(JSON, default=dict)

    # Timezone
    timezone = Column(String(50), default="UTC")

    # Status and control
    is_active = Column(Boolean, default=True, index=True)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, index=True)

    # Retry configuration
    max_retries = Column(Integer, default=3)
    retry_delay = Column(Integer, default=60)  # seconds
    retry_backoff = Column(Boolean, default=True)

    # Metadata
    priority = Column(Integer, default=5)  # 1-10, higher = more priority
    tags = Column(JSON, default=list)
    metadata = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    last_run_at = Column(DateTime(timezone=True))
    next_run_at = Column(DateTime(timezone=True), index=True)

    # User tracking
    created_by = Column(String(100))

    # Relationships
    executions = relationship("JobExecution", back_populates="job", cascade="all, delete-orphan")
    notifications = relationship("JobNotification", back_populates="job", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_job_status_active', 'status', 'is_active'),
        Index('idx_job_next_run', 'next_run_at', 'is_active'),
    )

    def __repr__(self):
        return f"<ScheduledJob(id={self.id}, name='{self.name}', type={self.job_type})>"


class JobExecution(Base):
    """Job execution history"""
    __tablename__ = "job_executions"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("scheduled_jobs.id", ondelete="CASCADE"), nullable=False, index=True)

    # Execution details
    task_id = Column(String(255), unique=True, index=True)  # Celery task ID
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, index=True)

    # Timing
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)

    # Results
    result = Column(JSON)
    error_message = Column(Text)
    traceback = Column(Text)

    # Retry information
    attempt_number = Column(Integer, default=1)
    is_retry = Column(Boolean, default=False)
    parent_execution_id = Column(Integer, ForeignKey("job_executions.id"))

    # Metadata
    worker_name = Column(String(255))
    metadata = Column(JSON, default=dict)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    job = relationship("ScheduledJob", back_populates="executions")
    parent_execution = relationship("JobExecution", remote_side=[id])

    # Indexes
    __table_args__ = (
        Index('idx_execution_job_status', 'job_id', 'status'),
        Index('idx_execution_scheduled', 'scheduled_at'),
    )

    def __repr__(self):
        return f"<JobExecution(id={self.id}, job_id={self.job_id}, status={self.status})>"


class JobNotification(Base):
    """Job notification settings"""
    __tablename__ = "job_notifications"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("scheduled_jobs.id", ondelete="CASCADE"), nullable=False, index=True)

    # Notification settings
    channel = Column(SQLEnum(NotificationChannel), nullable=False)
    is_active = Column(Boolean, default=True)

    # Trigger conditions
    on_success = Column(Boolean, default=False)
    on_failure = Column(Boolean, default=True)
    on_retry = Column(Boolean, default=False)
    on_start = Column(Boolean, default=False)

    # Channel-specific config
    recipient = Column(String(255), nullable=False)  # email, telegram chat_id, etc.
    config = Column(JSON, default=dict)  # Additional channel-specific settings

    # Template
    message_template = Column(Text)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    job = relationship("ScheduledJob", back_populates="notifications")

    def __repr__(self):
        return f"<JobNotification(id={self.id}, job_id={self.job_id}, channel={self.channel})>"


class JobDependency(Base):
    """Job dependencies for workflow orchestration"""
    __tablename__ = "job_dependencies"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("scheduled_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    depends_on_job_id = Column(Integer, ForeignKey("scheduled_jobs.id", ondelete="CASCADE"), nullable=False)

    # Dependency configuration
    wait_for_completion = Column(Boolean, default=True)
    required = Column(Boolean, default=True)  # If False, job runs even if dependency fails

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Constraints
    __table_args__ = (
        UniqueConstraint('job_id', 'depends_on_job_id', name='uq_job_dependency'),
        Index('idx_dependency_job', 'job_id'),
    )

    def __repr__(self):
        return f"<JobDependency(job_id={self.job_id}, depends_on={self.depends_on_job_id})>"
