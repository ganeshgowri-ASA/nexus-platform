"""Schedule database models"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base


class Schedule(Base):
    """Schedule model for workflow automation"""
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)

    # Schedule configuration
    cron_expression = Column(String(100), nullable=False)  # Cron format
    timezone = Column(String(50), default="UTC")

    # Execution settings
    max_concurrent_runs = Column(Integer, default=1)
    retry_on_failure = Column(Boolean, default=True)
    max_retries = Column(Integer, default=3)

    # Notifications
    notify_on_success = Column(Boolean, default=False)
    notify_on_failure = Column(Boolean, default=True)
    notification_emails = Column(JSON, nullable=True)  # List of emails

    # Metadata
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    run_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = Column(String(255), nullable=True)

    # Relationships
    workflow = relationship("Workflow", back_populates="schedules")
