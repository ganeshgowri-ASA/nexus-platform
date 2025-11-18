"""Pydantic schemas for API request/response models."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


# Enums
class WorkflowStatusEnum(str, Enum):
    CREATED = "created"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatusEnum(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class TaskTypeEnum(str, Enum):
    PYTHON = "python"
    HTTP = "http"
    BASH = "bash"
    SQL = "sql"
    DOCKER = "docker"
    CUSTOM = "custom"


# Task schemas
class TaskNodeSchema(BaseModel):
    task_key: str = Field(..., description="Unique task identifier within workflow")
    name: str = Field(..., description="Task display name")
    task_type: TaskTypeEnum = Field(..., description="Type of task")
    config: Dict[str, Any] = Field(..., description="Task configuration")
    depends_on: List[str] = Field(default=[], description="List of dependent task keys")
    retry_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Retry configuration (max_retries, retry_delay, timeout)"
    )


class TaskCreate(BaseModel):
    workflow_id: int
    task_key: str
    name: str
    description: Optional[str] = None
    task_type: TaskTypeEnum
    executor: str = "celery"
    config: Dict[str, Any]
    parameters: Optional[Dict[str, Any]] = None
    depends_on: List[str] = []
    max_retries: int = 3
    retry_delay: int = 60
    timeout: int = 3600
    run_condition: Optional[str] = None


class TaskResponse(BaseModel):
    id: int
    workflow_id: int
    task_key: str
    name: str
    description: Optional[str]
    task_type: str
    executor: str
    config: Dict[str, Any]
    depends_on: List[str]
    max_retries: int
    retry_delay: int
    timeout: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Workflow schemas
class WorkflowCreate(BaseModel):
    name: str = Field(..., description="Workflow name")
    description: Optional[str] = Field(None, description="Workflow description")
    dag_definition: Dict[str, Any] = Field(..., description="DAG definition with tasks")
    config: Optional[Dict[str, Any]] = Field(default={}, description="Workflow configuration")
    schedule_cron: Optional[str] = Field(None, description="Cron expression for scheduling")
    is_scheduled: bool = Field(default=False, description="Enable scheduled execution")
    tags: List[str] = Field(default=[], description="Workflow tags")
    category: Optional[str] = Field(None, description="Workflow category")
    created_by: Optional[str] = Field(None, description="Creator username")


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    dag_definition: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None
    schedule_cron: Optional[str] = None
    is_scheduled: Optional[bool] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None


class WorkflowResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    dag_definition: Dict[str, Any]
    config: Dict[str, Any]
    schedule_cron: Optional[str]
    is_scheduled: bool
    status: WorkflowStatusEnum
    current_run_id: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    total_runs: int
    successful_runs: int
    failed_runs: int
    tags: List[str]
    category: Optional[str]

    class Config:
        from_attributes = True


# Workflow execution schemas
class WorkflowExecutionTrigger(BaseModel):
    workflow_id: int = Field(..., description="Workflow ID to execute")
    input_data: Optional[Dict[str, Any]] = Field(default={}, description="Input data for workflow")
    triggered_by: Optional[str] = Field(None, description="Trigger source")


class WorkflowExecutionResponse(BaseModel):
    id: int
    workflow_id: int
    run_id: str
    status: WorkflowStatusEnum
    started_at: datetime
    completed_at: Optional[datetime]
    duration: Optional[float]
    triggered_by: Optional[str]
    trigger_metadata: Dict[str, Any]
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    total_tasks: int
    completed_tasks: int
    failed_tasks: int

    class Config:
        from_attributes = True


class TaskExecutionResponse(BaseModel):
    id: int
    workflow_execution_id: int
    task_id: Optional[int]
    execution_id: str
    status: TaskStatusEnum
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration: Optional[float]
    retry_count: int
    worker_id: Optional[str]
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    logs: Optional[str]

    class Config:
        from_attributes = True


# DAG schemas
class DAGValidationRequest(BaseModel):
    dag_definition: Dict[str, Any] = Field(..., description="DAG definition to validate")


class DAGValidationResponse(BaseModel):
    is_valid: bool
    error_message: Optional[str] = None
    execution_order: Optional[List[str]] = None
    parallel_groups: Optional[List[List[str]]] = None
    visualization: Optional[Dict[str, Any]] = None


# Notification schemas
class NotificationCreate(BaseModel):
    workflow_id: int
    notification_type: str = Field(..., description="email, slack, or webhook")
    on_success: bool = False
    on_failure: bool = True
    on_start: bool = False
    config: Dict[str, Any] = Field(..., description="Notification configuration")
    is_active: bool = True


class NotificationResponse(BaseModel):
    id: int
    workflow_id: int
    notification_type: str
    on_success: bool
    on_failure: bool
    on_start: bool
    config: Dict[str, Any]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Statistics schemas
class WorkflowStatistics(BaseModel):
    total_workflows: int
    active_workflows: int
    total_executions: int
    running_executions: int
    completed_executions: int
    failed_executions: int
    average_duration: Optional[float]
    success_rate: float


class TaskStatistics(BaseModel):
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    average_duration: Optional[float]
    success_rate: float
