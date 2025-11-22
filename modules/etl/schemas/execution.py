"""ETL Execution schemas."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ETLExecutionResponse(BaseModel):
    """Schema for ETL execution response."""

    id: str
    pipeline_id: str
    job_id: Optional[str] = None
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    records_extracted: int = 0
    records_transformed: int = 0
    records_loaded: int = 0
    records_failed: int = 0
    records_duplicates: int = 0
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    execution_logs: Optional[Dict[str, Any]] = None
    data_quality_report: Optional[Dict[str, Any]] = None
    celery_task_id: Optional[str] = None

    class Config:
        from_attributes = True
