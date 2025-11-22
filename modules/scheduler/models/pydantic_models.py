"""Pydantic models for API request/response validation"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from modules.scheduler.models.schemas import JobStatus, JobType, NotificationChannel


class JobCreate(BaseModel):
    """Schema for creating a new job"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    job_type: JobType
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = Field(None, gt=0)
    scheduled_time: Optional[datetime] = None
    calendar_rule: Optional[Dict[str, Any]] = None
    task_name: str
    task_args: List[Any] = []
    task_kwargs: Dict[str, Any] = {}
    timezone: str = "UTC"
    is_active: bool = True
    max_retries: int = Field(3, ge=0, le=10)
    retry_delay: int = Field(60, ge=0)
    retry_backoff: bool = True
    priority: int = Field(5, ge=1, le=10)
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
    created_by: Optional[str] = None

    @validator('cron_expression')
    def validate_cron(cls, v, values):
        if values.get('job_type') == JobType.CRON and not v:
            raise ValueError('cron_expression is required for CRON type jobs')
        return v

    @validator('interval_seconds')
    def validate_interval(cls, v, values):
        if values.get('job_type') == JobType.INTERVAL and not v:
            raise ValueError('interval_seconds is required for INTERVAL type jobs')
        return v

    @validator('scheduled_time')
    def validate_scheduled_time(cls, v, values):
        if values.get('job_type') == JobType.DATE and not v:
            raise ValueError('scheduled_time is required for DATE type jobs')
        return v


class JobUpdate(BaseModel):
    """Schema for updating a job"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = Field(None, gt=0)
    scheduled_time: Optional[datetime] = None
    calendar_rule: Optional[Dict[str, Any]] = None
    task_args: Optional[List[Any]] = None
    task_kwargs: Optional[Dict[str, Any]] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    retry_delay: Optional[int] = Field(None, ge=0)
    retry_backoff: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class JobResponse(BaseModel):
    """Schema for job response"""
    id: int
    name: str
    description: Optional[str]
    job_type: JobType
    cron_expression: Optional[str]
    interval_seconds: Optional[int]
    scheduled_time: Optional[datetime]
    calendar_rule: Optional[Dict[str, Any]]
    task_name: str
    task_args: List[Any]
    task_kwargs: Dict[str, Any]
    timezone: str
    is_active: bool
    status: JobStatus
    max_retries: int
    retry_delay: int
    retry_backoff: bool
    priority: int
    tags: List[str]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    created_by: Optional[str]

    class Config:
        from_attributes = True


class ExecutionResponse(BaseModel):
    """Schema for execution response"""
    id: int
    job_id: int
    task_id: Optional[str]
    status: JobStatus
    scheduled_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    attempt_number: int
    is_retry: bool
    worker_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationCreate(BaseModel):
    """Schema for creating a notification"""
    job_id: int
    channel: NotificationChannel
    is_active: bool = True
    on_success: bool = False
    on_failure: bool = True
    on_retry: bool = False
    on_start: bool = False
    recipient: str
    config: Dict[str, Any] = {}
    message_template: Optional[str] = None


class NotificationResponse(BaseModel):
    """Schema for notification response"""
    id: int
    job_id: int
    channel: NotificationChannel
    is_active: bool
    on_success: bool
    on_failure: bool
    on_retry: bool
    on_start: bool
    recipient: str
    config: Dict[str, Any]
    message_template: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class JobExecuteRequest(BaseModel):
    """Schema for manual job execution"""
    task_args: Optional[List[Any]] = None
    task_kwargs: Optional[Dict[str, Any]] = None


class CronValidationRequest(BaseModel):
    """Schema for cron expression validation"""
    expression: str
    timezone: str = "UTC"


class CronValidationResponse(BaseModel):
    """Schema for cron validation response"""
    is_valid: bool
    description: Optional[str] = None
    next_runs: List[datetime] = []
    error: Optional[str] = None


class JobStatsResponse(BaseModel):
    """Schema for job statistics"""
    total_jobs: int
    active_jobs: int
    paused_jobs: int
    total_executions: int
    successful_executions: int
    failed_executions: int
    running_executions: int
    average_duration: Optional[float]
    last_24h_executions: int
