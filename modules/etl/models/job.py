"""ETL Job model."""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from shared.database.base import Base
import uuid


class ETLJob(Base):
    """Scheduled ETL job model."""

    __tablename__ = "etl_jobs"
    __table_args__ = {"schema": "etl"}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pipeline_id = Column(String(36), ForeignKey("etl.pipelines.id"), nullable=False)

    # Schedule settings
    schedule_type = Column(String(50), nullable=False)  # cron, interval, once
    schedule_expression = Column(String(255), nullable=False)
    timezone = Column(String(50), default="UTC")

    # Job status
    is_active = Column(Boolean, default=True)
    next_run = Column(DateTime(timezone=True), nullable=True)
    last_run = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<ETLJob(pipeline_id='{self.pipeline_id}', active={self.is_active})>"
