"""Pydantic schemas for batch processing module."""

from datetime import datetime
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field, ConfigDict
from database.models.batch_job import JobStatus, TaskStatus


# Base schemas
class BatchJobBase(BaseModel):
    """Base schema for batch job."""
    name: str = Field(..., min_length=1, max_length=255, description="Job name")
    description: Optional[str] = Field(None, description="Job description")
    job_type: str = Field(..., description="Type of batch job")
    config: Optional[Dict[str, Any]] = Field(None, description="Job configuration")


class BatchJobCreate(BatchJobBase):
    """Schema for creating a batch job."""
    created_by: Optional[str] = Field(None, description="User who created the job")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class BatchJobUpdate(BaseModel):
    """Schema for updating a batch job."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[JobStatus] = None
    metadata: Optional[Dict[str, Any]] = None


class BatchJobResponse(BatchJobBase):
    """Schema for batch job response."""
    id: int
    status: JobStatus
    total_items: int
    processed_items: int
    successful_items: int
    failed_items: int
    skipped_items: int
    progress_percentage: float
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    estimated_completion: Optional[datetime]
    result_summary: Optional[Dict[str, Any]]
    error_message: Optional[str]
    metadata: Optional[Dict[str, Any]]
    input_file_path: Optional[str]
    output_file_path: Optional[str]
    error_log_path: Optional[str]
    celery_task_id: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BatchJobListResponse(BaseModel):
    """Schema for paginated list of batch jobs."""
    jobs: List[BatchJobResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class BatchJobStats(BaseModel):
    """Schema for batch job statistics."""
    total_jobs: int
    pending_jobs: int
    running_jobs: int
    completed_jobs: int
    failed_jobs: int
    cancelled_jobs: int
    total_items_processed: int
    average_success_rate: float


# Task schemas
class BatchTaskBase(BaseModel):
    """Base schema for batch task."""
    task_number: int = Field(..., description="Task sequence number")
    task_name: Optional[str] = Field(None, description="Task name")
    input_data: Optional[Dict[str, Any]] = Field(None, description="Input data")


class BatchTaskCreate(BatchTaskBase):
    """Schema for creating a batch task."""
    batch_job_id: int
    max_retries: int = 3


class BatchTaskUpdate(BaseModel):
    """Schema for updating a batch task."""
    status: Optional[TaskStatus] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BatchTaskResponse(BatchTaskBase):
    """Schema for batch task response."""
    id: int
    batch_job_id: int
    status: TaskStatus
    retry_count: int
    max_retries: int
    output_data: Optional[Dict[str, Any]]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    error_message: Optional[str]
    error_traceback: Optional[str]
    metadata: Optional[Dict[str, Any]]
    celery_task_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BatchTaskListResponse(BaseModel):
    """Schema for paginated list of batch tasks."""
    tasks: List[BatchTaskResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# File upload schemas
class FileUploadResponse(BaseModel):
    """Schema for file upload response."""
    filename: str
    file_path: str
    file_size: int
    rows_detected: Optional[int] = None
    columns_detected: Optional[List[str]] = None


# Data transformation schemas
class DataTransformationConfig(BaseModel):
    """Schema for data transformation configuration."""
    source_column: str
    target_column: str
    transformation_type: str  # uppercase, lowercase, strip, etc.
    parameters: Optional[Dict[str, Any]] = None


class BatchJobWithTransformationCreate(BatchJobCreate):
    """Schema for creating a batch job with transformations."""
    transformations: List[DataTransformationConfig] = []
    chunk_size: int = Field(100, gt=0, le=1000)
    parallel_workers: int = Field(4, gt=0, le=16)


# Progress schemas
class BatchJobProgress(BaseModel):
    """Schema for batch job progress."""
    job_id: int
    status: JobStatus
    progress_percentage: float
    processed_items: int
    total_items: int
    successful_items: int
    failed_items: int
    estimated_completion: Optional[datetime]
    current_message: Optional[str] = None


# Error log schemas
class ErrorLogEntry(BaseModel):
    """Schema for error log entry."""
    task_id: int
    task_number: int
    timestamp: datetime
    error_message: str
    error_traceback: Optional[str]
    input_data: Optional[Dict[str, Any]]


class ErrorLogResponse(BaseModel):
    """Schema for error log response."""
    job_id: int
    total_errors: int
    errors: List[ErrorLogEntry]


# Retry schemas
class RetryConfig(BaseModel):
    """Schema for retry configuration."""
    max_retries: int = Field(3, ge=0, le=10)
    retry_delay_seconds: int = Field(5, ge=0, le=300)
    exponential_backoff: bool = True
    retry_on_errors: List[str] = ["*"]  # * for all errors


# CSV/Excel import schemas
class CSVImportConfig(BaseModel):
    """Schema for CSV import configuration."""
    delimiter: str = ","
    has_header: bool = True
    encoding: str = "utf-8"
    skip_rows: int = 0
    max_rows: Optional[int] = None


class ExcelImportConfig(BaseModel):
    """Schema for Excel import configuration."""
    sheet_name: Optional[str] = None
    has_header: bool = True
    skip_rows: int = 0
    max_rows: Optional[int] = None


class BatchImportJobCreate(BatchJobCreate):
    """Schema for creating a batch import job."""
    file_path: str
    import_config: Optional[Dict[str, Any]] = None
    transformations: List[DataTransformationConfig] = []
