"""Pydantic schemas for experiment models."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from modules.ab_testing.models.experiment import ExperimentStatus, ExperimentType


class ExperimentBase(BaseModel):
    """Base schema for experiments."""

    name: str = Field(..., min_length=1, max_length=255, description="Experiment name")
    description: Optional[str] = Field(None, description="Detailed description")
    hypothesis: Optional[str] = Field(None, description="Hypothesis being tested")
    type: ExperimentType = Field(
        default=ExperimentType.AB,
        description="Type of experiment",
    )
    target_sample_size: int = Field(
        default=1000,
        ge=10,
        description="Target sample size per variant",
    )
    confidence_level: float = Field(
        default=0.95,
        ge=0.8,
        le=0.99,
        description="Required confidence level",
    )
    traffic_allocation: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Overall traffic allocation (0.0-1.0)",
    )
    auto_winner_enabled: bool = Field(
        default=True,
        description="Enable automatic winner detection",
    )
    metadata: Optional[dict[str, Any]] = Field(None, description="Additional metadata")


class ExperimentCreate(ExperimentBase):
    """Schema for creating a new experiment."""

    pass


class ExperimentUpdate(BaseModel):
    """Schema for updating an experiment."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    hypothesis: Optional[str] = None
    status: Optional[ExperimentStatus] = None
    target_sample_size: Optional[int] = Field(None, ge=10)
    confidence_level: Optional[float] = Field(None, ge=0.8, le=0.99)
    traffic_allocation: Optional[float] = Field(None, ge=0.0, le=1.0)
    auto_winner_enabled: Optional[bool] = None
    metadata: Optional[dict[str, Any]] = None


class ExperimentResponse(ExperimentBase):
    """Schema for experiment response."""

    id: int
    status: ExperimentStatus
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    winner_variant_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExperimentStats(BaseModel):
    """Schema for experiment statistics."""

    experiment_id: int
    total_participants: int
    variant_stats: dict[str, Any]
    primary_metric_results: Optional[dict[str, Any]] = None
    statistical_significance: Optional[float] = None
    confidence_interval: Optional[dict[str, Any]] = None
    recommended_action: Optional[str] = None
