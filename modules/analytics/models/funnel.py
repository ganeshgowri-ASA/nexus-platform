"""
Funnel Models

Data models for funnel analysis.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from shared.constants import EventType, FunnelStepStatus
from shared.utils import generate_uuid, get_utc_now


class FunnelStepBase(BaseModel):
    """Base funnel step model."""

    name: str = Field(..., min_length=1, max_length=255, description="Step name")
    event_type: EventType = Field(..., description="Event type for this step")
    order: int = Field(..., ge=0, description="Step order in funnel")
    description: Optional[str] = Field(None, max_length=1000, description="Description")


class FunnelStepCreate(FunnelStepBase):
    """Model for creating a funnel step."""

    pass


class FunnelStep(FunnelStepBase):
    """Complete funnel step model."""

    id: str = Field(default_factory=generate_uuid, description="Step ID")
    funnel_id: str = Field(..., description="Parent funnel ID")
    created_at: datetime = Field(
        default_factory=get_utc_now, description="Creation time"
    )

    model_config = {"from_attributes": True}


class FunnelBase(BaseModel):
    """Base funnel model."""

    name: str = Field(..., min_length=1, max_length=255, description="Funnel name")
    description: Optional[str] = Field(None, max_length=1000, description="Description")
    enabled: bool = Field(default=True, description="Funnel enabled status")


class FunnelCreate(FunnelBase):
    """Model for creating a funnel."""

    steps: List[FunnelStepCreate] = Field(
        ..., min_length=2, description="Funnel steps"
    )


class Funnel(FunnelBase):
    """Complete funnel model."""

    id: str = Field(default_factory=generate_uuid, description="Funnel ID")
    steps: List[FunnelStep] = Field(default_factory=list, description="Funnel steps")
    created_at: datetime = Field(
        default_factory=get_utc_now, description="Creation time"
    )
    updated_at: datetime = Field(
        default_factory=get_utc_now, description="Update time"
    )

    model_config = {"from_attributes": True}


class FunnelStepStats(BaseModel):
    """Statistics for a funnel step."""

    step_id: str
    step_name: str
    order: int
    entered: int
    completed: int
    dropped: int
    completion_rate: float
    drop_off_rate: float
    avg_time_to_complete: Optional[float] = None


class FunnelAnalysis(BaseModel):
    """Complete funnel analysis results."""

    funnel_id: str
    funnel_name: str
    start_date: datetime
    end_date: datetime
    total_entered: int
    total_completed: int
    overall_conversion_rate: float
    steps: List[FunnelStepStats]
    avg_completion_time: Optional[float] = None


class FunnelQuery(BaseModel):
    """Model for querying funnels."""

    funnel_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user_segment: Optional[str] = None
