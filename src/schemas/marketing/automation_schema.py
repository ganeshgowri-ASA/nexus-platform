"""
Pydantic schemas for automation-related API operations.

This module defines request and response schemas for automation endpoints.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field

from config.constants import AutomationStatus, TriggerType, ActionType


class ActionConfig(BaseModel):
    """Schema for automation action configuration."""
    action_type: ActionType = Field(..., description="Action type")
    config: Dict[str, Any] = Field(..., description="Action-specific configuration")
    delay_minutes: Optional[int] = Field(None, ge=0, description="Delay before execution (minutes)")


class TriggerConfig(BaseModel):
    """Schema for automation trigger configuration."""
    trigger_type: TriggerType = Field(..., description="Trigger type")
    config: Dict[str, Any] = Field(..., description="Trigger-specific configuration")


class AutomationBase(BaseModel):
    """Base automation schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Automation name")
    description: Optional[str] = Field(None, description="Automation description")


class AutomationCreate(AutomationBase):
    """Schema for creating automation."""
    trigger_type: TriggerType = Field(..., description="Trigger type")
    trigger_config: Dict[str, Any] = Field(..., description="Trigger configuration")
    actions: List[ActionConfig] = Field(..., min_length=1, description="List of actions")
    conditions: Optional[Dict[str, Any]] = Field(default={}, description="Execution conditions")


class AutomationUpdate(BaseModel):
    """Schema for updating automation."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[AutomationStatus] = None
    trigger_config: Optional[Dict[str, Any]] = None
    actions: Optional[List[ActionConfig]] = None
    conditions: Optional[Dict[str, Any]] = None


class AutomationResponse(AutomationBase):
    """Schema for automation response."""
    id: UUID
    workspace_id: UUID
    status: AutomationStatus
    trigger_type: TriggerType
    trigger_config: Dict[str, Any]
    actions: List[Dict[str, Any]]
    conditions: Dict[str, Any]
    execution_count: int
    last_executed_at: Optional[datetime] = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AutomationListResponse(BaseModel):
    """Schema for automation list response."""
    automations: List[AutomationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AutomationExecutionResponse(BaseModel):
    """Schema for automation execution response."""
    id: UUID
    automation_id: UUID
    contact_id: Optional[UUID] = None
    status: str
    trigger_data: Dict[str, Any]
    actions_executed: List[Dict[str, Any]]
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AutomationTriggerRequest(BaseModel):
    """Schema for manually triggering automation."""
    contact_id: Optional[UUID] = Field(None, description="Contact ID to trigger for")
    trigger_data: Optional[Dict[str, Any]] = Field(default={}, description="Trigger data")


class DripCampaignStep(BaseModel):
    """Schema for drip campaign step."""
    name: str = Field(..., min_length=1, description="Step name")
    delay_minutes: int = Field(..., ge=0, description="Delay from previous step (minutes)")
    action_type: ActionType = Field(..., description="Action type")
    action_config: Dict[str, Any] = Field(..., description="Action configuration")


class DripCampaignCreate(BaseModel):
    """Schema for creating drip campaign."""
    name: str = Field(..., min_length=1, max_length=255, description="Drip campaign name")
    description: Optional[str] = Field(None, description="Description")
    entry_trigger: Dict[str, Any] = Field(..., description="Entry trigger configuration")
    steps: List[DripCampaignStep] = Field(..., min_length=1, description="Campaign steps")


class DripCampaignUpdate(BaseModel):
    """Schema for updating drip campaign."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = None
    entry_trigger: Optional[Dict[str, Any]] = None
    steps: Optional[List[DripCampaignStep]] = None


class DripCampaignResponse(BaseModel):
    """Schema for drip campaign response."""
    id: UUID
    workspace_id: UUID
    name: str
    description: Optional[str] = None
    status: str
    entry_trigger: Dict[str, Any]
    steps: List[Dict[str, Any]]
    total_enrolled: int
    total_completed: int
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DripEnrollmentCreate(BaseModel):
    """Schema for enrolling contact in drip campaign."""
    contact_id: UUID = Field(..., description="Contact ID to enroll")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Enrollment metadata")


class DripEnrollmentResponse(BaseModel):
    """Schema for drip enrollment response."""
    id: UUID
    drip_campaign_id: UUID
    contact_id: UUID
    status: str
    current_step: int
    enrolled_at: datetime
    completed_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkflowNodeCreate(BaseModel):
    """Schema for creating workflow node."""
    automation_id: UUID = Field(..., description="Automation ID")
    node_type: str = Field(..., description="Node type")
    node_config: Dict[str, Any] = Field(..., description="Node configuration")
    position_x: int = Field(default=0, description="X position")
    position_y: int = Field(default=0, description="Y position")
    next_node_id: Optional[UUID] = Field(None, description="Next node ID")


class WorkflowNodeResponse(BaseModel):
    """Schema for workflow node response."""
    id: UUID
    automation_id: UUID
    node_type: str
    node_config: Dict[str, Any]
    position_x: int
    position_y: int
    next_node_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkflowVisualization(BaseModel):
    """Schema for workflow visualization data."""
    nodes: List[WorkflowNodeResponse]
    edges: List[Dict[str, str]]  # List of {from: node_id, to: node_id}
