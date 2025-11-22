"""
Pydantic schemas for RPA module
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum


class AutomationStatus(str, Enum):
    """Automation status"""

    ACTIVE = "active"
    PAUSED = "paused"
    DRAFT = "draft"
    ARCHIVED = "archived"


class ExecutionStatus(str, Enum):
    """Execution status"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TriggerType(str, Enum):
    """Trigger type"""

    MANUAL = "manual"
    SCHEDULED = "scheduled"
    WEBHOOK = "webhook"
    EVENT = "event"


# Bot Schemas
class BotBase(BaseModel):
    """Base bot schema"""

    name: str
    description: Optional[str] = None
    bot_type: str = "standard"
    capabilities: List[str] = Field(default_factory=list)
    configuration: Dict[str, Any] = Field(default_factory=dict)


class BotCreate(BotBase):
    """Bot creation schema"""

    created_by: str


class BotUpdate(BaseModel):
    """Bot update schema"""

    name: Optional[str] = None
    description: Optional[str] = None
    bot_type: Optional[str] = None
    capabilities: Optional[List[str]] = None
    configuration: Optional[Dict[str, Any]] = None
    status: Optional[AutomationStatus] = None


class BotResponse(BotBase):
    """Bot response schema"""

    id: str
    status: AutomationStatus
    created_at: datetime
    updated_at: datetime
    created_by: str

    class Config:
        from_attributes = True


# Automation Schemas
class AutomationBase(BaseModel):
    """Base automation schema"""

    name: str
    description: Optional[str] = None
    bot_id: Optional[str] = None
    trigger_type: TriggerType = TriggerType.MANUAL
    workflow: Dict[str, Any]
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    variables: Dict[str, Any] = Field(default_factory=dict)
    error_handling: Dict[str, Any] = Field(default_factory=dict)
    retry_config: Dict[str, Any] = Field(default_factory=dict)
    timeout: int = 3600
    tags: List[str] = Field(default_factory=list)


class AutomationCreate(AutomationBase):
    """Automation creation schema"""

    created_by: str


class AutomationUpdate(BaseModel):
    """Automation update schema"""

    name: Optional[str] = None
    description: Optional[str] = None
    bot_id: Optional[str] = None
    trigger_type: Optional[TriggerType] = None
    workflow: Optional[Dict[str, Any]] = None
    inputs: Optional[Dict[str, Any]] = None
    outputs: Optional[Dict[str, Any]] = None
    variables: Optional[Dict[str, Any]] = None
    error_handling: Optional[Dict[str, Any]] = None
    retry_config: Optional[Dict[str, Any]] = None
    timeout: Optional[int] = None
    status: Optional[AutomationStatus] = None
    tags: Optional[List[str]] = None


class AutomationResponse(AutomationBase):
    """Automation response schema"""

    id: str
    status: AutomationStatus
    version: int
    is_template: bool
    created_at: datetime
    updated_at: datetime
    created_by: str
    last_executed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Execution Schemas
class ExecutionCreate(BaseModel):
    """Execution creation schema"""

    automation_id: str
    trigger_type: TriggerType = TriggerType.MANUAL
    input_data: Dict[str, Any] = Field(default_factory=dict)
    triggered_by: str


class ExecutionResponse(BaseModel):
    """Execution response schema"""

    id: str
    automation_id: str
    trigger_type: TriggerType
    status: ExecutionStatus
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    variables: Dict[str, Any]
    logs: List[Dict[str, Any]]
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[int] = None
    retry_count: int
    triggered_by: str
    created_at: datetime

    class Config:
        from_attributes = True


# Schedule Schemas
class ScheduleBase(BaseModel):
    """Base schedule schema"""

    name: str
    cron_expression: str
    timezone: str = "UTC"
    input_data: Dict[str, Any] = Field(default_factory=dict)


class ScheduleCreate(ScheduleBase):
    """Schedule creation schema"""

    automation_id: str
    created_by: str


class ScheduleUpdate(BaseModel):
    """Schedule update schema"""

    name: Optional[str] = None
    cron_expression: Optional[str] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None
    input_data: Optional[Dict[str, Any]] = None


class ScheduleResponse(ScheduleBase):
    """Schedule response schema"""

    id: str
    automation_id: str
    is_active: bool
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    run_count: int
    created_at: datetime
    updated_at: datetime
    created_by: str

    class Config:
        from_attributes = True


# UI Element Schemas
class UIElementBase(BaseModel):
    """Base UI element schema"""

    name: str
    element_type: str
    selector: Dict[str, Any]
    properties: Dict[str, Any] = Field(default_factory=dict)


class UIElementCreate(UIElementBase):
    """UI element creation schema"""

    automation_id: Optional[str] = None
    screenshot_path: Optional[str] = None


class UIElementResponse(UIElementBase):
    """UI element response schema"""

    id: str
    automation_id: Optional[str] = None
    screenshot_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Workflow Node Schema
class WorkflowNode(BaseModel):
    """Workflow node schema"""

    id: str
    type: str  # click, type, wait, condition, loop, etc.
    name: str
    config: Dict[str, Any] = Field(default_factory=dict)
    position: Dict[str, float] = Field(default_factory=dict)


class WorkflowEdge(BaseModel):
    """Workflow edge schema"""

    id: str
    source: str
    target: str
    condition: Optional[str] = None


class WorkflowDefinition(BaseModel):
    """Complete workflow definition"""

    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]
    variables: Dict[str, Any] = Field(default_factory=dict)


# Response Models
class PaginatedResponse(BaseModel):
    """Paginated response"""

    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


class MessageResponse(BaseModel):
    """Simple message response"""

    message: str
    success: bool = True
