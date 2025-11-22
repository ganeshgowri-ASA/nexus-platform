"""
A/B Testing Models

Data models for A/B test experiments.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from shared.constants import ABTestStatus, ABTestVariant
from shared.utils import generate_uuid, get_utc_now


class ABTestBase(BaseModel):
    """Base A/B test model."""

    name: str = Field(..., min_length=1, max_length=255, description="Test name")
    description: Optional[str] = Field(None, max_length=1000, description="Description")
    hypothesis: Optional[str] = Field(None, max_length=1000, description="Hypothesis")
    goal_metric: str = Field(..., description="Primary metric to optimize")
    variants: List[ABTestVariant] = Field(..., min_length=2, description="Test variants")
    traffic_split: Dict[str, float] = Field(..., description="Traffic allocation")
    start_date: Optional[datetime] = Field(None, description="Test start date")
    end_date: Optional[datetime] = Field(None, description="Test end date")
    min_sample_size: int = Field(default=1000, ge=100, description="Minimum sample size")


class ABTestCreate(ABTestBase):
    """Model for creating an A/B test."""

    pass


class ABTestUpdate(BaseModel):
    """Model for updating an A/B test."""

    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ABTestStatus] = None
    end_date: Optional[datetime] = None


class ABTest(ABTestBase):
    """Complete A/B test model."""

    id: str = Field(default_factory=generate_uuid, description="Test ID")
    status: ABTestStatus = Field(
        default=ABTestStatus.DRAFT, description="Test status"
    )
    total_participants: int = Field(default=0, description="Total participants")
    winner: Optional[ABTestVariant] = Field(None, description="Winning variant")
    confidence_level: Optional[float] = Field(None, description="Statistical confidence")
    created_at: datetime = Field(
        default_factory=get_utc_now, description="Creation time"
    )
    updated_at: datetime = Field(
        default_factory=get_utc_now, description="Update time"
    )

    model_config = {"from_attributes": True}


class ABTestAssignment(BaseModel):
    """User assignment to A/B test variant."""

    id: str = Field(default_factory=generate_uuid, description="Assignment ID")
    test_id: str = Field(..., description="Test ID")
    user_id: str = Field(..., description="User ID")
    variant: ABTestVariant = Field(..., description="Assigned variant")
    assigned_at: datetime = Field(
        default_factory=get_utc_now, description="Assignment time"
    )

    model_config = {"from_attributes": True}


class ABTestVariantStats(BaseModel):
    """Statistics for an A/B test variant."""

    variant: ABTestVariant
    participants: int
    conversions: int
    conversion_rate: float
    avg_metric_value: float
    total_metric_value: float
    confidence_interval: tuple[float, float]


class ABTestResults(BaseModel):
    """Complete A/B test results."""

    test_id: str
    test_name: str
    status: ABTestStatus
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    total_participants: int
    variant_stats: List[ABTestVariantStats]
    winner: Optional[ABTestVariant]
    confidence_level: Optional[float]
    p_value: Optional[float]
    statistical_significance: bool
    recommendation: str


class ABTestQuery(BaseModel):
    """Model for querying A/B tests."""

    test_id: Optional[str] = None
    status: Optional[ABTestStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
