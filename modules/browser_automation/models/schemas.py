"""Pydantic schemas for API validation"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from .workflow import WorkflowStatus, StepType


# ============= Workflow Schemas =============

class WorkflowStepCreate(BaseModel):
    """Schema for creating workflow step"""
    step_order: int = Field(..., ge=0)
    step_type: StepType
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    selector: Optional[str] = None
    selector_type: str = "css"
    value: Optional[str] = None
    wait_before: int = Field(default=0, ge=0)
    wait_after: int = Field(default=0, ge=0)
    options: Optional[Dict[str, Any]] = None
    error_handling: str = Field(default="stop", pattern="^(stop|continue|retry)$")
    max_retries: int = Field(default=3, ge=0, le=10)


class WorkflowStepResponse(WorkflowStepCreate):
    """Schema for workflow step response"""
    id: int
    workflow_id: int

    class Config:
        from_attributes = True


class WorkflowCreate(BaseModel):
    """Schema for creating workflow"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: bool = True
    headless: bool = True
    browser_type: str = Field(default="chromium", pattern="^(chromium|firefox|webkit)$")
    timeout: int = Field(default=30000, ge=1000, le=300000)
    steps: List[WorkflowStepCreate] = []


class WorkflowUpdate(BaseModel):
    """Schema for updating workflow"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    headless: Optional[bool] = None
    browser_type: Optional[str] = Field(None, pattern="^(chromium|firefox|webkit)$")
    timeout: Optional[int] = Field(None, ge=1000, le=300000)


class WorkflowResponse(BaseModel):
    """Schema for workflow response"""
    id: int
    name: str
    description: Optional[str]
    is_active: bool
    headless: bool
    browser_type: str
    timeout: int
    user_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    steps: List[WorkflowStepResponse] = []

    class Config:
        from_attributes = True


# ============= Workflow Execution Schemas =============

class WorkflowExecutionResponse(BaseModel):
    """Schema for workflow execution response"""
    id: int
    workflow_id: int
    status: WorkflowStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    result_data: Optional[Dict[str, Any]]
    screenshots: Optional[List[str]]
    pdfs: Optional[List[str]]
    error_message: Optional[str]
    error_step: Optional[int]
    triggered_by: str
    user_id: Optional[str]

    class Config:
        from_attributes = True


class WorkflowExecuteRequest(BaseModel):
    """Schema for workflow execution request"""
    headless: Optional[bool] = None
    browser_type: Optional[str] = Field(None, pattern="^(chromium|firefox|webkit)$")
    variables: Optional[Dict[str, Any]] = None


# ============= Schedule Schemas =============

class ScheduleCreate(BaseModel):
    """Schema for creating schedule"""
    workflow_id: int
    name: str = Field(..., min_length=1, max_length=255)
    is_active: bool = True
    cron_expression: str = Field(..., min_length=1, max_length=100)
    timezone: str = "UTC"
    max_concurrent_runs: int = Field(default=1, ge=1, le=10)
    retry_on_failure: bool = True
    max_retries: int = Field(default=3, ge=0, le=10)
    notify_on_success: bool = False
    notify_on_failure: bool = True
    notification_emails: Optional[List[str]] = None

    @field_validator("cron_expression")
    @classmethod
    def validate_cron(cls, v: str) -> str:
        """Basic cron expression validation"""
        parts = v.split()
        if len(parts) not in [5, 6]:
            raise ValueError("Cron expression must have 5 or 6 parts")
        return v


class ScheduleUpdate(BaseModel):
    """Schema for updating schedule"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None
    cron_expression: Optional[str] = None
    timezone: Optional[str] = None
    max_concurrent_runs: Optional[int] = Field(None, ge=1, le=10)
    retry_on_failure: Optional[bool] = None
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    notify_on_success: Optional[bool] = None
    notify_on_failure: Optional[bool] = None
    notification_emails: Optional[List[str]] = None


class ScheduleResponse(BaseModel):
    """Schema for schedule response"""
    id: int
    workflow_id: int
    name: str
    is_active: bool
    cron_expression: str
    timezone: str
    max_concurrent_runs: int
    retry_on_failure: bool
    max_retries: int
    notify_on_success: bool
    notify_on_failure: bool
    notification_emails: Optional[List[str]]
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    run_count: int
    failure_count: int
    created_at: datetime
    updated_at: datetime
    user_id: Optional[str]

    class Config:
        from_attributes = True


# ============= Data Extraction Schemas =============

class ExtractedData(BaseModel):
    """Schema for extracted data"""
    selector: str
    data: Any
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ScrapingResult(BaseModel):
    """Schema for scraping results"""
    url: str
    title: Optional[str]
    extracted_data: List[ExtractedData]
    screenshots: List[str] = []
    execution_time: float
    success: bool
    error: Optional[str] = None
