"""
Cohort Models

Data models for cohort analysis.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from shared.constants import CohortType, AggregationPeriod
from shared.utils import generate_uuid, get_utc_now


class CohortBase(BaseModel):
    """Base cohort model."""

    name: str = Field(..., min_length=1, max_length=255, description="Cohort name")
    cohort_type: CohortType = Field(..., description="Type of cohort")
    description: Optional[str] = Field(None, max_length=1000, description="Description")
    criteria: Dict[str, Any] = Field(..., description="Cohort criteria")
    period: AggregationPeriod = Field(
        default=AggregationPeriod.DAY, description="Analysis period"
    )


class CohortCreate(CohortBase):
    """Model for creating a cohort."""

    pass


class CohortUpdate(BaseModel):
    """Model for updating a cohort."""

    name: Optional[str] = None
    description: Optional[str] = None
    criteria: Optional[Dict[str, Any]] = None


class Cohort(CohortBase):
    """Complete cohort model."""

    id: str = Field(default_factory=generate_uuid, description="Cohort ID")
    user_count: int = Field(default=0, description="Number of users in cohort")
    created_at: datetime = Field(
        default_factory=get_utc_now, description="Creation time"
    )
    updated_at: datetime = Field(
        default_factory=get_utc_now, description="Update time"
    )

    model_config = {"from_attributes": True}


class CohortRetention(BaseModel):
    """Retention data for a cohort period."""

    period: int = Field(..., description="Period number (0 = acquisition period)")
    users_active: int = Field(..., description="Active users in period")
    retention_rate: float = Field(..., description="Retention rate")
    cumulative_retention: float = Field(..., description="Cumulative retention rate")


class CohortAnalysis(BaseModel):
    """Complete cohort analysis results."""

    cohort_id: str
    cohort_name: str
    cohort_date: datetime
    initial_users: int
    retention_data: List[CohortRetention]
    avg_retention_rate: float
    churn_rate: float


class CohortComparisonMetric(BaseModel):
    """Metric comparison across cohorts."""

    metric_name: str
    cohort_values: Dict[str, float]
    best_cohort: str
    worst_cohort: str


class CohortQuery(BaseModel):
    """Model for querying cohorts."""

    cohort_id: Optional[str] = None
    cohort_type: Optional[CohortType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    periods: int = Field(default=12, ge=1, le=52, description="Number of periods")
