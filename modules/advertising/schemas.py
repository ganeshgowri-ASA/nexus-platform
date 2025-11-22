"""
Pydantic schemas for advertising module.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator

from modules.advertising.models import (
    AdPlatform, CampaignStatus, CampaignObjective, BidStrategy, AdStatus
)


# Campaign Schemas
class CampaignCreate(BaseModel):
    """Schema for creating a campaign."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    platform: AdPlatform
    objective: CampaignObjective
    budget_type: str = "daily"  # daily or lifetime
    daily_budget: Optional[float] = Field(None, gt=0)
    lifetime_budget: Optional[float] = Field(None, gt=0)
    currency: str = "USD"
    bid_strategy: BidStrategy
    bid_amount: Optional[float] = Field(None, gt=0)
    target_cpa: Optional[float] = Field(None, gt=0)
    target_roas: Optional[float] = Field(None, gt=0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    settings: Dict[str, Any] = {}

    @validator("daily_budget")
    def validate_daily_budget(cls, v, values):
        if values.get("budget_type") == "daily" and not v:
            raise ValueError("daily_budget required when budget_type is daily")
        return v

    @validator("lifetime_budget")
    def validate_lifetime_budget(cls, v, values):
        if values.get("budget_type") == "lifetime" and not v:
            raise ValueError("lifetime_budget required when budget_type is lifetime")
        return v


class CampaignUpdate(BaseModel):
    """Schema for updating a campaign."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    budget_type: Optional[str] = None
    daily_budget: Optional[float] = Field(None, gt=0)
    lifetime_budget: Optional[float] = Field(None, gt=0)
    bid_strategy: Optional[BidStrategy] = None
    bid_amount: Optional[float] = Field(None, gt=0)
    target_cpa: Optional[float] = Field(None, gt=0)
    target_roas: Optional[float] = Field(None, gt=0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[CampaignStatus] = None
    settings: Optional[Dict[str, Any]] = None


class CampaignResponse(BaseModel):
    """Schema for campaign response."""
    id: UUID
    name: str
    description: Optional[str]
    platform: AdPlatform
    platform_campaign_id: Optional[str]
    objective: CampaignObjective
    budget_type: str
    daily_budget: Optional[float]
    lifetime_budget: Optional[float]
    spent: float
    currency: str
    bid_strategy: BidStrategy
    status: CampaignStatus
    impressions: int
    clicks: int
    conversions: int
    ctr: float
    cpc: float
    cpm: float
    cpa: float
    roas: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Ad Set Schemas
class AdSetCreate(BaseModel):
    """Schema for creating an ad set."""
    campaign_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    budget_type: Optional[str] = "daily"
    daily_budget: Optional[float] = Field(None, gt=0)
    lifetime_budget: Optional[float] = Field(None, gt=0)
    bid_amount: Optional[float] = Field(None, gt=0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    targeting: Dict[str, Any]
    locations: List[str] = []
    age_min: Optional[int] = Field(None, ge=13, le=65)
    age_max: Optional[int] = Field(None, ge=13, le=65)
    genders: List[str] = []
    languages: List[str] = []
    interests: List[str] = []
    behaviors: List[str] = []
    custom_audiences: List[str] = []
    excluded_audiences: List[str] = []


class AdSetUpdate(BaseModel):
    """Schema for updating an ad set."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    budget_type: Optional[str] = None
    daily_budget: Optional[float] = Field(None, gt=0)
    lifetime_budget: Optional[float] = Field(None, gt=0)
    bid_amount: Optional[float] = Field(None, gt=0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    targeting: Optional[Dict[str, Any]] = None
    locations: Optional[List[str]] = None
    age_min: Optional[int] = Field(None, ge=13, le=65)
    age_max: Optional[int] = Field(None, ge=13, le=65)
    genders: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    behaviors: Optional[List[str]] = None
    status: Optional[str] = None


class AdSetResponse(BaseModel):
    """Schema for ad set response."""
    id: UUID
    campaign_id: UUID
    name: str
    platform_adset_id: Optional[str]
    budget_type: str
    daily_budget: Optional[float]
    lifetime_budget: Optional[float]
    spent: float
    bid_amount: Optional[float]
    targeting: Dict[str, Any]
    locations: List[str]
    age_min: Optional[int]
    age_max: Optional[int]
    status: str
    impressions: int
    clicks: int
    conversions: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Ad Schemas
class AdCreate(BaseModel):
    """Schema for creating an ad."""
    ad_set_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    creative_id: Optional[UUID] = None
    headline: str = Field(..., max_length=500)
    description: str
    call_to_action: str
    destination_url: str = Field(..., max_length=1000)
    tracking_params: Dict[str, Any] = {}


class AdUpdate(BaseModel):
    """Schema for updating an ad."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    creative_id: Optional[UUID] = None
    headline: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    call_to_action: Optional[str] = None
    destination_url: Optional[str] = Field(None, max_length=1000)
    tracking_params: Optional[Dict[str, Any]] = None
    status: Optional[AdStatus] = None


class AdResponse(BaseModel):
    """Schema for ad response."""
    id: UUID
    ad_set_id: UUID
    name: str
    platform_ad_id: Optional[str]
    headline: str
    description: str
    call_to_action: str
    destination_url: str
    status: AdStatus
    review_status: Optional[str]
    impressions: int
    clicks: int
    conversions: int
    spent: float
    ctr: float
    cpc: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Ad Creative Schemas
class AdCreativeCreate(BaseModel):
    """Schema for creating an ad creative."""
    name: str = Field(..., min_length=1, max_length=255)
    type: str
    title: Optional[str] = Field(None, max_length=500)
    body: Optional[str] = None
    images: List[str] = []
    videos: List[str] = []
    thumbnail_url: Optional[str] = None
    carousel_items: List[Dict[str, Any]] = []


class AdCreativeUpdate(BaseModel):
    """Schema for updating an ad creative."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[str] = None
    title: Optional[str] = Field(None, max_length=500)
    body: Optional[str] = None
    images: Optional[List[str]] = None
    videos: Optional[List[str]] = None
    thumbnail_url: Optional[str] = None
    carousel_items: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None


class AdCreativeResponse(BaseModel):
    """Schema for ad creative response."""
    id: UUID
    name: str
    type: str
    title: Optional[str]
    body: Optional[str]
    images: List[str]
    videos: List[str]
    thumbnail_url: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Performance Schemas
class PerformanceMetrics(BaseModel):
    """Schema for performance metrics."""
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    spent: float = 0.0
    revenue: float = 0.0
    ctr: float = 0.0
    cpc: float = 0.0
    cpm: float = 0.0
    cpa: float = 0.0
    roas: float = 0.0
    conversion_rate: float = 0.0


class CampaignPerformanceResponse(BaseModel):
    """Schema for campaign performance response."""
    id: UUID
    campaign_id: UUID
    date: datetime
    impressions: int
    clicks: int
    conversions: int
    spent: float
    revenue: float
    ctr: float
    cpc: float
    cpm: float
    cpa: float
    roas: float
    conversion_rate: float
    created_at: datetime

    class Config:
        from_attributes = True


# A/B Test Schemas
class ABTestCreate(BaseModel):
    """Schema for creating an A/B test."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    test_type: str
    variant_a_id: str
    variant_b_id: str
    traffic_split: int = Field(50, ge=10, le=90)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ABTestUpdate(BaseModel):
    """Schema for updating an A/B test."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    traffic_split: Optional[int] = Field(None, ge=10, le=90)
    end_date: Optional[datetime] = None
    status: Optional[str] = None


class ABTestResponse(BaseModel):
    """Schema for A/B test response."""
    id: UUID
    name: str
    description: Optional[str]
    test_type: str
    variant_a_id: str
    variant_b_id: str
    traffic_split: int
    status: str
    winner: Optional[str]
    results: Dict[str, Any]
    confidence_level: Optional[float]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Automated Rule Schemas
class AutomatedRuleCreate(BaseModel):
    """Schema for creating an automated rule."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    target_type: str
    target_id: UUID
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    schedule: str = "daily"


class AutomatedRuleUpdate(BaseModel):
    """Schema for updating an automated rule."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    actions: Optional[Dict[str, Any]] = None
    schedule: Optional[str] = None
    is_active: Optional[bool] = None


class AutomatedRuleResponse(BaseModel):
    """Schema for automated rule response."""
    id: UUID
    name: str
    description: Optional[str]
    target_type: str
    target_id: UUID
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    schedule: str
    is_active: bool
    execution_count: int
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Conversion Tracking Schemas
class ConversionTrackingCreate(BaseModel):
    """Schema for creating a conversion tracking record."""
    campaign_id: Optional[UUID] = None
    ad_id: Optional[UUID] = None
    conversion_type: str
    conversion_value: float = 0.0
    currency: str = "USD"
    click_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = {}
    click_time: Optional[datetime] = None
    conversion_time: datetime


class ConversionTrackingResponse(BaseModel):
    """Schema for conversion tracking response."""
    id: UUID
    campaign_id: Optional[UUID]
    ad_id: Optional[UUID]
    conversion_type: str
    conversion_value: float
    currency: str
    metadata: Dict[str, Any]
    conversion_time: datetime
    created_at: datetime

    class Config:
        from_attributes = True
