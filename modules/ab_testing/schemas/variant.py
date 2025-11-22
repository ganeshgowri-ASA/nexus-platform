"""Pydantic schemas for variant models."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class VariantBase(BaseModel):
    """Base schema for variants."""

    name: str = Field(..., min_length=1, max_length=255, description="Variant name")
    description: Optional[str] = Field(None, description="Variant description")
    is_control: bool = Field(default=False, description="Is this the control variant")
    traffic_weight: float = Field(
        default=1.0,
        gt=0.0,
        description="Traffic weight for allocation",
    )
    config: Optional[dict[str, Any]] = Field(
        None,
        description="Variant configuration",
    )


class VariantCreate(VariantBase):
    """Schema for creating a new variant."""

    experiment_id: int = Field(..., gt=0, description="Parent experiment ID")


class VariantUpdate(BaseModel):
    """Schema for updating a variant."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_control: Optional[bool] = None
    traffic_weight: Optional[float] = Field(None, gt=0.0)
    config: Optional[dict[str, Any]] = None


class VariantResponse(VariantBase):
    """Schema for variant response."""

    id: int
    experiment_id: int

    model_config = {"from_attributes": True}


class VariantAssignment(BaseModel):
    """Schema for variant assignment response."""

    experiment_id: int
    variant_id: int
    variant_name: str
    participant_id: str
    assigned_at: str
    config: Optional[dict[str, Any]] = None
