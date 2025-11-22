"""
Goal Models

Data models for goal tracking and conversions.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from shared.constants import EventType
from shared.utils import generate_uuid, get_utc_now


class GoalBase(BaseModel):
    """Base goal model."""

    name: str = Field(..., min_length=1, max_length=255, description="Goal name")
    description: Optional[str] = Field(None, max_length=1000, description="Description")
    event_type: EventType = Field(..., description="Event that triggers goal")
    conditions: Dict[str, Any] = Field(
        default_factory=dict, description="Goal conditions"
    )
    value: Optional[float] = Field(None, description="Goal value")
    enabled: bool = Field(default=True, description="Goal enabled status")


class GoalCreate(GoalBase):
    """Model for creating a goal."""

    pass


class GoalUpdate(BaseModel):
    """Model for updating a goal."""

    name: Optional[str] = None
    description: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    value: Optional[float] = None
    enabled: Optional[bool] = None


class Goal(GoalBase):
    """Complete goal model."""

    id: str = Field(default_factory=generate_uuid, description="Goal ID")
    total_conversions: int = Field(default=0, description="Total conversions")
    total_value: float = Field(default=0.0, description="Total conversion value")
    created_at: datetime = Field(
        default_factory=get_utc_now, description="Creation time"
    )
    updated_at: datetime = Field(
        default_factory=get_utc_now, description="Update time"
    )

    model_config = {"from_attributes": True}


class GoalConversion(BaseModel):
    """Goal conversion record."""

    id: str = Field(default_factory=generate_uuid, description="Conversion ID")
    goal_id: str = Field(..., description="Goal ID")
    user_id: str = Field(..., description="User ID")
    session_id: Optional[str] = Field(None, description="Session ID")
    event_id: str = Field(..., description="Triggering event ID")
    value: Optional[float] = Field(None, description="Conversion value")
    properties: Dict[str, Any] = Field(
        default_factory=dict, description="Conversion properties"
    )
    converted_at: datetime = Field(
        default_factory=get_utc_now, description="Conversion time"
    )

    model_config = {"from_attributes": True}


class GoalAnalytics(BaseModel):
    """Goal analytics and metrics."""

    goal_id: str
    goal_name: str
    total_conversions: int
    unique_users: int
    conversion_rate: float
    total_value: float
    avg_value_per_conversion: float
    avg_time_to_conversion: Optional[float] = None
    start_date: datetime
    end_date: datetime


class GoalQuery(BaseModel):
    """Model for querying goals."""

    goal_id: Optional[str] = None
    enabled: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
