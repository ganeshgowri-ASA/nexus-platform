"""ETL Execution history model."""
from sqlalchemy import Column, String, Integer, JSON, DateTime, Text, ForeignKey, Float
from sqlalchemy.sql import func
from shared.database.base import Base
import uuid


class ETLExecution(Base):
    """ETL execution history and logs model."""

    __tablename__ = "etl_executions"
    __table_args__ = {"schema": "etl"}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pipeline_id = Column(String(36), ForeignKey("etl.pipelines.id"), nullable=False)
    job_id = Column(String(36), ForeignKey("etl.etl_jobs.id"), nullable=True)

    # Execution details
    status = Column(
        String(50), nullable=False
    )  # pending, running, completed, failed, cancelled
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Data metrics
    records_extracted = Column(Integer, default=0)
    records_transformed = Column(Integer, default=0)
    records_loaded = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    records_duplicates = Column(Integer, default=0)

    # Error handling
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)

    # Logs and metadata
    execution_logs = Column(JSON, nullable=True)  # Detailed step-by-step logs
    data_quality_report = Column(JSON, nullable=True)

    # Celery task info
    celery_task_id = Column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<ETLExecution(pipeline_id='{self.pipeline_id}', status='{self.status}')>"
