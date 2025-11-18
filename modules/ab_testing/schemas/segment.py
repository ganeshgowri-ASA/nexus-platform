"""Pydantic schemas for segment models."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from modules.ab_testing.models.segment import SegmentOperator


class SegmentConditionBase(BaseModel):
    """Base schema for segment conditions."""

    property_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Property name to evaluate",
    )
    operator: SegmentOperator = Field(..., description="Comparison operator")
    value: dict[str, Any] = Field(..., description="Value to compare against")


class SegmentConditionCreate(SegmentConditionBase):
    """Schema for creating a segment condition."""

    pass


class SegmentConditionResponse(SegmentConditionBase):
    """Schema for segment condition response."""

    id: int
    segment_id: int

    model_config = {"from_attributes": True}


class SegmentBase(BaseModel):
    """Base schema for segments."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Segment name",
    )
    description: Optional[str] = Field(None, description="Segment description")


class SegmentCreate(SegmentBase):
    """Schema for creating a new segment."""

    conditions: list[SegmentConditionCreate] = Field(
        default_factory=list,
        description="List of conditions",
    )


class SegmentResponse(SegmentBase):
    """Schema for segment response."""

    id: int
    created_at: datetime
    updated_at: datetime
    conditions: list[SegmentConditionResponse] = []

    model_config = {"from_attributes": True}
