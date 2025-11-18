"""
Metric Models

Data models for analytics metrics and KPIs.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from shared.constants import MetricType, AggregationPeriod
from shared.utils import generate_uuid, get_utc_now


class MetricBase(BaseModel):
    """Base metric model."""

    name: str = Field(..., min_length=1, max_length=255, description="Metric name")
    metric_type: MetricType = Field(..., description="Type of metric")
    value: float = Field(..., description="Metric value")
    unit: Optional[str] = Field(None, max_length=50, description="Metric unit")
    dimensions: Dict[str, Any] = Field(
        default_factory=dict, description="Metric dimensions"
    )
    period: Optional[AggregationPeriod] = Field(None, description="Aggregation period")
    module: Optional[str] = Field(None, max_length=100, description="Module name")


class MetricCreate(MetricBase):
    """Model for creating a new metric."""

    pass


class MetricUpdate(BaseModel):
    """Model for updating a metric."""

    value: Optional[float] = None
    dimensions: Optional[Dict[str, Any]] = None


class Metric(MetricBase):
    """Complete metric model with database fields."""

    id: str = Field(default_factory=generate_uuid, description="Metric ID")
    timestamp: datetime = Field(
        default_factory=get_utc_now, description="Metric timestamp"
    )
    created_at: datetime = Field(
        default_factory=get_utc_now, description="Creation time"
    )

    model_config = {"from_attributes": True}


class MetricQuery(BaseModel):
    """Model for querying metrics."""

    names: Optional[list[str]] = None
    metric_types: Optional[list[MetricType]] = None
    module: Optional[str] = None
    period: Optional[AggregationPeriod] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=100, ge=1, le=1000)


class MetricSeries(BaseModel):
    """Time series data for a metric."""

    name: str
    metric_type: MetricType
    data_points: list[tuple[datetime, float]]
    period: AggregationPeriod
    start_date: datetime
    end_date: datetime
    total: float
    average: float
    min_value: float
    max_value: float


class MetricComparison(BaseModel):
    """Comparison of metrics across periods."""

    name: str
    current_value: float
    previous_value: float
    change: float
    change_percentage: float
    is_improvement: bool
