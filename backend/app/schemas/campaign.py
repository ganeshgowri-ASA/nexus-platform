"""
Campaign schemas for request/response validation.

This module defines Pydantic schemas for campaign-related operations.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field, validator

from app.models.campaign import (
    CampaignStatus,
    CampaignType,
    ChannelType,
    AssetType,
    MilestoneStatus,
    TeamMemberRole,
    ReportType,
)


# ==================== Campaign Schemas ====================

class CampaignBase(BaseModel):
    """Base campaign schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    campaign_type: CampaignType
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_budget: float = Field(default=0.0, ge=0)
    goals: Optional[Dict[str, Any]] = None
    target_audience: Optional[Dict[str, Any]] = None

    @validator("end_date")
    def validate_end_date(cls, v, values):
        """Validate end date is after start date."""
        if v and "start_date" in values and values["start_date"]:
            if v < values["start_date"]:
                raise ValueError("End date must be after start date")
        return v


class CampaignCreate(CampaignBase):
    """Schema for creating a new campaign."""
    pass


class CampaignUpdate(BaseModel):
    """Schema for updating a campaign."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    campaign_type: Optional[CampaignType] = None
    status: Optional[CampaignStatus] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_budget: Optional[float] = Field(None, ge=0)
    goals: Optional[Dict[str, Any]] = None
    target_audience: Optional[Dict[str, Any]] = None


class CampaignResponse(CampaignBase):
    """Schema for campaign response."""
    id: int
    status: CampaignStatus
    owner_id: int
    spent_budget: float
    remaining_budget: float
    budget_utilization: float
    ai_insights: Optional[Dict[str, Any]] = None
    optimization_suggestions: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CampaignListResponse(BaseModel):
    """Schema for campaign list response."""
    campaigns: List[CampaignResponse]
    total: int
    page: int
    page_size: int


# ==================== Channel Schemas ====================

class CampaignChannelBase(BaseModel):
    """Base channel schema."""
    channel_type: ChannelType
    channel_name: str = Field(..., min_length=1, max_length=255)
    allocated_budget: float = Field(default=0.0, ge=0)
    config: Optional[Dict[str, Any]] = None
    is_active: bool = True


class CampaignChannelCreate(CampaignChannelBase):
    """Schema for creating a campaign channel."""
    pass


class CampaignChannelUpdate(BaseModel):
    """Schema for updating a campaign channel."""
    channel_name: Optional[str] = Field(None, min_length=1, max_length=255)
    allocated_budget: Optional[float] = Field(None, ge=0)
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class CampaignChannelResponse(CampaignChannelBase):
    """Schema for channel response."""
    id: int
    campaign_id: int
    spent_budget: float
    impressions: int
    clicks: int
    conversions: int
    revenue: float
    ctr: float
    conversion_rate: float
    roi: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Asset Schemas ====================

class CampaignAssetBase(BaseModel):
    """Base asset schema."""
    name: str = Field(..., min_length=1, max_length=255)
    asset_type: AssetType
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class CampaignAssetCreate(CampaignAssetBase):
    """Schema for creating a campaign asset."""
    file_path: str


class CampaignAssetUpdate(BaseModel):
    """Schema for updating a campaign asset."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_approved: Optional[bool] = None


class CampaignAssetResponse(CampaignAssetBase):
    """Schema for asset response."""
    id: int
    campaign_id: int
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    usage_count: int
    last_used_at: Optional[datetime] = None
    is_approved: bool
    approved_by_id: Optional[int] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Team Member Schemas ====================

class TeamMemberBase(BaseModel):
    """Base team member schema."""
    user_id: int
    role: TeamMemberRole
    assigned_tasks: Optional[List[str]] = None
    notes: Optional[str] = None


class TeamMemberCreate(TeamMemberBase):
    """Schema for adding a team member."""
    pass


class TeamMemberUpdate(BaseModel):
    """Schema for updating a team member."""
    role: Optional[TeamMemberRole] = None
    assigned_tasks: Optional[List[str]] = None
    notes: Optional[str] = None


class TeamMemberResponse(TeamMemberBase):
    """Schema for team member response."""
    id: int
    campaign_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Milestone Schemas ====================

class MilestoneBase(BaseModel):
    """Base milestone schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    due_date: date
    assigned_to_id: Optional[int] = None
    dependencies: Optional[List[int]] = None


class MilestoneCreate(MilestoneBase):
    """Schema for creating a milestone."""
    pass


class MilestoneUpdate(BaseModel):
    """Schema for updating a milestone."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[MilestoneStatus] = None
    due_date: Optional[date] = None
    assigned_to_id: Optional[int] = None
    dependencies: Optional[List[int]] = None
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)


class MilestoneResponse(MilestoneBase):
    """Schema for milestone response."""
    id: int
    campaign_id: int
    status: MilestoneStatus
    progress_percentage: int
    completed_at: Optional[datetime] = None
    is_overdue: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Performance Metric Schemas ====================

class PerformanceMetricBase(BaseModel):
    """Base performance metric schema."""
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    engagement_rate: float = 0.0
    cost: float = 0.0
    revenue: float = 0.0
    roi: float = 0.0
    channel_breakdown: Optional[Dict[str, Any]] = None
    custom_metrics: Optional[Dict[str, Any]] = None


class PerformanceMetricCreate(PerformanceMetricBase):
    """Schema for creating a performance metric."""
    pass


class PerformanceMetricResponse(PerformanceMetricBase):
    """Schema for performance metric response."""
    id: int
    campaign_id: int
    recorded_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Report Schemas ====================

class CampaignReportBase(BaseModel):
    """Base report schema."""
    title: str = Field(..., min_length=1, max_length=255)
    report_type: ReportType
    period_start: date
    period_end: date
    summary: Optional[str] = None


class CampaignReportCreate(CampaignReportBase):
    """Schema for creating a campaign report."""
    metrics: Dict[str, Any]


class CampaignReportResponse(CampaignReportBase):
    """Schema for report response."""
    id: int
    campaign_id: int
    metrics: Dict[str, Any]
    insights: Optional[Dict[str, Any]] = None
    recommendations: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None
    generated_by_id: Optional[int] = None
    is_automated: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Analytics & Dashboard Schemas ====================

class CampaignAnalytics(BaseModel):
    """Schema for campaign analytics summary."""
    campaign_id: int
    campaign_name: str
    total_impressions: int
    total_clicks: int
    total_conversions: int
    total_revenue: float
    total_cost: float
    overall_roi: float
    overall_ctr: float
    overall_conversion_rate: float
    channel_performance: List[Dict[str, Any]]
    timeline_data: List[Dict[str, Any]]


class DashboardStats(BaseModel):
    """Schema for dashboard statistics."""
    total_campaigns: int
    active_campaigns: int
    total_budget: float
    spent_budget: float
    total_conversions: int
    total_revenue: float
    average_roi: float
    recent_campaigns: List[CampaignResponse]


class BudgetAllocation(BaseModel):
    """Schema for budget allocation request."""
    channel_id: int
    amount: float = Field(..., gt=0)


class OptimizationRequest(BaseModel):
    """Schema for requesting AI optimization."""
    campaign_id: int
    focus_areas: Optional[List[str]] = None  # ["budget", "channels", "timing"]
