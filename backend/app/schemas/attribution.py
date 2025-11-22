"""
NEXUS Platform - Attribution Module Pydantic Schemas
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator

from backend.app.models.attribution import (
    ChannelType,
    TouchpointType,
    AttributionModelType,
    ConversionType,
)


# ============================================================================
# Base Schemas
# ============================================================================

class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    class Config:
        from_attributes = True


# ============================================================================
# Channel Schemas
# ============================================================================

class ChannelBase(BaseSchema):
    """Base channel schema."""
    name: str = Field(..., description="Channel name", max_length=255)
    channel_type: ChannelType = Field(..., description="Type of marketing channel")
    description: Optional[str] = Field(None, description="Channel description")
    cost_per_click: float = Field(0.0, ge=0, description="Cost per click")
    cost_per_impression: float = Field(0.0, ge=0, description="Cost per impression")
    monthly_budget: float = Field(0.0, ge=0, description="Monthly budget")
    is_active: bool = Field(True, description="Is channel active")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChannelCreate(ChannelBase):
    """Schema for creating a channel."""
    pass


class ChannelUpdate(BaseSchema):
    """Schema for updating a channel."""
    name: Optional[str] = Field(None, max_length=255)
    channel_type: Optional[ChannelType] = None
    description: Optional[str] = None
    cost_per_click: Optional[float] = Field(None, ge=0)
    cost_per_impression: Optional[float] = Field(None, ge=0)
    monthly_budget: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class ChannelResponse(ChannelBase):
    """Schema for channel response."""
    id: int
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Journey Schemas
# ============================================================================

class JourneyBase(BaseSchema):
    """Base journey schema."""
    user_id: str = Field(..., description="User identifier", max_length=255)
    session_id: Optional[str] = Field(None, max_length=255)
    start_time: datetime = Field(..., description="Journey start time")
    end_time: Optional[datetime] = Field(None, description="Journey end time")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class JourneyCreate(JourneyBase):
    """Schema for creating a journey."""
    pass


class JourneyUpdate(BaseSchema):
    """Schema for updating a journey."""
    end_time: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class JourneyResponse(JourneyBase):
    """Schema for journey response."""
    id: int
    total_touchpoints: int
    conversion_value: float
    has_conversion: bool
    journey_duration_minutes: Optional[int]
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Touchpoint Schemas
# ============================================================================

class TouchpointBase(BaseSchema):
    """Base touchpoint schema."""
    journey_id: int = Field(..., description="Journey ID")
    channel_id: int = Field(..., description="Channel ID")
    touchpoint_type: TouchpointType = Field(..., description="Type of touchpoint")
    timestamp: datetime = Field(..., description="Touchpoint timestamp")
    position_in_journey: int = Field(..., ge=1, description="Position in journey")

    # Engagement metrics
    time_spent_seconds: int = Field(0, ge=0)
    pages_viewed: int = Field(0, ge=0)
    engagement_score: float = Field(0.0, ge=0, le=1)

    # Cost data
    cost: float = Field(0.0, ge=0)

    # Context
    page_url: Optional[str] = Field(None, max_length=2048)
    referrer_url: Optional[str] = Field(None, max_length=2048)
    campaign_id: Optional[str] = Field(None, max_length=255)
    campaign_name: Optional[str] = Field(None, max_length=255)
    ad_group: Optional[str] = Field(None, max_length=255)
    keyword: Optional[str] = Field(None, max_length=255)
    device_type: Optional[str] = Field(None, max_length=50)
    browser: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=255)

    metadata: Dict[str, Any] = Field(default_factory=dict)


class TouchpointCreate(TouchpointBase):
    """Schema for creating a touchpoint."""
    pass


class TouchpointUpdate(BaseSchema):
    """Schema for updating a touchpoint."""
    touchpoint_type: Optional[TouchpointType] = None
    time_spent_seconds: Optional[int] = Field(None, ge=0)
    pages_viewed: Optional[int] = Field(None, ge=0)
    engagement_score: Optional[float] = Field(None, ge=0, le=1)
    cost: Optional[float] = Field(None, ge=0)
    metadata: Optional[Dict[str, Any]] = None


class TouchpointResponse(TouchpointBase):
    """Schema for touchpoint response."""
    id: int
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Conversion Schemas
# ============================================================================

class ConversionBase(BaseSchema):
    """Base conversion schema."""
    journey_id: int = Field(..., description="Journey ID")
    conversion_type: ConversionType = Field(..., description="Type of conversion")
    timestamp: datetime = Field(..., description="Conversion timestamp")

    # Value metrics
    revenue: float = Field(0.0, ge=0, description="Revenue generated")
    quantity: int = Field(1, ge=1, description="Quantity")

    # Conversion details
    product_id: Optional[str] = Field(None, max_length=255)
    product_name: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = Field(None, max_length=255)

    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversionCreate(ConversionBase):
    """Schema for creating a conversion."""
    pass


class ConversionUpdate(BaseSchema):
    """Schema for updating a conversion."""
    revenue: Optional[float] = Field(None, ge=0)
    quantity: Optional[int] = Field(None, ge=1)
    metadata: Optional[Dict[str, Any]] = None


class ConversionResponse(ConversionBase):
    """Schema for conversion response."""
    id: int
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Attribution Model Schemas
# ============================================================================

class AttributionModelBase(BaseSchema):
    """Base attribution model schema."""
    name: str = Field(..., description="Model name", max_length=255)
    model_type: AttributionModelType = Field(..., description="Type of attribution model")
    description: Optional[str] = Field(None, description="Model description")

    # Model parameters
    time_decay_halflife_days: Optional[float] = Field(None, gt=0)
    position_weights: Optional[Dict[str, float]] = Field(None)
    custom_rules: Optional[Dict[str, Any]] = Field(None)

    # AI/ML parameters
    ml_model_type: Optional[str] = Field(None, max_length=100)
    ml_parameters: Optional[Dict[str, Any]] = Field(None)
    training_data_window_days: int = Field(90, ge=1)

    is_active: bool = Field(True)
    is_default: bool = Field(False)

    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator("position_weights")
    def validate_position_weights(cls, v):
        """Validate position weights sum to 1."""
        if v is not None:
            total = sum(v.values())
            if not (0.99 <= total <= 1.01):  # Allow small floating point errors
                raise ValueError("Position weights must sum to 1.0")
        return v


class AttributionModelCreate(AttributionModelBase):
    """Schema for creating an attribution model."""
    pass


class AttributionModelUpdate(BaseSchema):
    """Schema for updating an attribution model."""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    time_decay_halflife_days: Optional[float] = Field(None, gt=0)
    position_weights: Optional[Dict[str, float]] = None
    custom_rules: Optional[Dict[str, Any]] = None
    ml_model_type: Optional[str] = Field(None, max_length=100)
    ml_parameters: Optional[Dict[str, Any]] = None
    training_data_window_days: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class AttributionModelResponse(AttributionModelBase):
    """Schema for attribution model response."""
    id: int
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Attribution Result Schemas
# ============================================================================

class AttributionResultBase(BaseSchema):
    """Base attribution result schema."""
    journey_id: int
    attribution_model_id: int
    channel_id: int

    # Attribution metrics
    credit: float = Field(..., description="Attribution credit")
    attributed_revenue: float = Field(0.0, ge=0)
    attributed_conversions: float = Field(0.0, ge=0)

    # ROI metrics
    channel_cost: float = Field(0.0, ge=0)
    roi: Optional[float] = None
    roas: Optional[float] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)


class AttributionResultResponse(AttributionResultBase):
    """Schema for attribution result response."""
    id: int
    calculated_at: datetime
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Analysis Request/Response Schemas
# ============================================================================

class AttributionAnalysisRequest(BaseSchema):
    """Schema for attribution analysis request."""
    journey_ids: List[int] = Field(..., description="Journey IDs to analyze")
    model_ids: List[int] = Field(..., description="Attribution model IDs to use")
    start_date: Optional[datetime] = Field(None, description="Analysis start date")
    end_date: Optional[datetime] = Field(None, description="Analysis end date")
    use_cache: bool = Field(True, description="Use cached results if available")


class ChannelAttributionSummary(BaseSchema):
    """Channel attribution summary."""
    channel_id: int
    channel_name: str
    channel_type: str
    total_credit: float
    attributed_revenue: float
    attributed_conversions: float
    total_cost: float
    roi: float
    roas: float
    touchpoint_count: int


class ModelComparisonResult(BaseSchema):
    """Model comparison result."""
    model_id: int
    model_name: str
    model_type: str
    channel_summaries: List[ChannelAttributionSummary]
    total_attributed_revenue: float
    total_attributed_conversions: float


class AttributionAnalysisResponse(BaseSchema):
    """Schema for attribution analysis response."""
    analysis_id: str
    journey_count: int
    model_comparisons: List[ModelComparisonResult]
    calculated_at: datetime


class JourneyVisualizationRequest(BaseSchema):
    """Schema for journey visualization request."""
    journey_id: int
    include_attribution: bool = Field(True, description="Include attribution data")


class TouchpointVisualization(BaseSchema):
    """Touchpoint visualization data."""
    id: int
    channel_name: str
    channel_type: str
    touchpoint_type: str
    timestamp: datetime
    position: int
    engagement_score: float
    cost: float
    attribution_credit: Optional[float] = None


class JourneyVisualizationResponse(BaseSchema):
    """Schema for journey visualization response."""
    journey_id: int
    user_id: str
    start_time: datetime
    end_time: Optional[datetime]
    total_touchpoints: int
    has_conversion: bool
    conversion_value: float
    touchpoints: List[TouchpointVisualization]
    total_cost: float
    duration_minutes: Optional[int]


class ChannelROIRequest(BaseSchema):
    """Schema for channel ROI analysis request."""
    channel_ids: Optional[List[int]] = Field(None, description="Specific channels to analyze")
    start_date: datetime = Field(..., description="Analysis start date")
    end_date: datetime = Field(..., description="Analysis end date")
    attribution_model_id: int = Field(..., description="Attribution model to use")


class ChannelROIResponse(BaseSchema):
    """Schema for channel ROI analysis response."""
    channel_id: int
    channel_name: str
    channel_type: str
    total_touchpoints: int
    total_conversions: int
    total_revenue: float
    total_cost: float
    roi: float
    roas: float
    avg_conversion_value: float
    conversion_rate: float
    cost_per_conversion: float


# ============================================================================
# Pagination Schemas
# ============================================================================

class PaginationParams(BaseSchema):
    """Pagination parameters."""
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(50, ge=1, le=1000, description="Items per page")


class PaginatedResponse(BaseSchema):
    """Paginated response wrapper."""
    total: int
    page: int
    page_size: int
    items: List[Any]
