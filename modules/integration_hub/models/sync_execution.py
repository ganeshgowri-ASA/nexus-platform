"""Sync Execution history model."""
from sqlalchemy import Column, String, Integer, JSON, DateTime, Text, ForeignKey, Float
from sqlalchemy.sql import func
from shared.database.base import Base
import uuid


class SyncExecution(Base):
    """Sync execution history and logs."""

    __tablename__ = "sync_executions"
    __table_args__ = {"schema": "integration_hub"}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sync_config_id = Column(String(36), ForeignKey("integration_hub.sync_configs.id"), nullable=False)

    # Execution details
    status = Column(String(50), nullable=False)  # pending, running, completed, failed
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Sync metrics
    records_read = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_deleted = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)

    # Error handling
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)

    # Logs
    execution_logs = Column(JSON, nullable=True)

    # Celery task info
    celery_task_id = Column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<SyncExecution(config_id='{self.sync_config_id}', status='{self.status}')>"
