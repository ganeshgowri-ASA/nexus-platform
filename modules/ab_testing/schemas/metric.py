"""Pydantic schemas for metric models."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from modules.ab_testing.models.metric import MetricType


class MetricBase(BaseModel):
    """Base schema for metrics."""

    name: str = Field(..., min_length=1, max_length=255, description="Metric name")
    description: Optional[str] = Field(None, description="Metric description")
    type: MetricType = Field(
        default=MetricType.CONVERSION,
        description="Type of metric",
    )
    is_primary: bool = Field(
        default=True,
        description="Is this the primary metric",
    )
    goal_value: Optional[float] = Field(
        None,
        description="Target/goal value for this metric",
    )
    metadata: Optional[dict[str, Any]] = Field(None, description="Additional metadata")


class MetricCreate(MetricBase):
    """Schema for creating a new metric."""

    experiment_id: int = Field(..., gt=0, description="Parent experiment ID")


class MetricResponse(MetricBase):
    """Schema for metric response."""

    id: int
    experiment_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MetricEventCreate(BaseModel):
    """Schema for creating a metric event."""

    metric_id: int = Field(..., gt=0, description="Parent metric ID")
    participant_id: str = Field(..., min_length=1, description="Participant identifier")
    variant_id: int = Field(..., gt=0, description="Variant ID")
    value: float = Field(..., description="Metric value")
    properties: Optional[dict[str, Any]] = Field(
        None,
        description="Additional event properties",
    )


class MetricEventResponse(BaseModel):
    """Schema for metric event response."""

    id: int
    metric_id: int
    participant_id: str
    variant_id: int
    value: float
    timestamp: datetime
    properties: Optional[dict[str, Any]] = None

    model_config = {"from_attributes": True}
