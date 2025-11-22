"""Type definitions for advertising module."""

from typing import Optional, Any, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

from shared.types import TimestampMixin


class CampaignStatus(str, Enum):
    """Campaign status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class AdPlatform(str, Enum):
    """Advertising platform enumeration."""
    GOOGLE_ADS = "google_ads"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    TIKTOK = "tiktok"


class BidStrategy(str, Enum):
    """Bid strategy enumeration."""
    MANUAL_CPC = "manual_cpc"
    AUTO_CPC = "auto_cpc"
    TARGET_CPA = "target_cpa"
    TARGET_ROAS = "target_roas"
    MAXIMIZE_CONVERSIONS = "maximize_conversions"
    MAXIMIZE_CLICKS = "maximize_clicks"


class AdType(str, Enum):
    """Ad type enumeration."""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    CAROUSEL = "carousel"
    SHOPPING = "shopping"
    DYNAMIC = "dynamic"


# Campaign Models

class CampaignBase(BaseModel):
    """Base campaign model."""
    name: str = Field(description="Campaign name")
    objective: str = Field(description="Campaign objective")
    platform: AdPlatform = Field(description="Advertising platform")
    daily_budget: float = Field(description="Daily budget")
    total_budget: Optional[float] = Field(default=None, description="Total budget")
    start_date: datetime = Field(description="Campaign start date")
    end_date: Optional[datetime] = Field(default=None, description="Campaign end date")
    status: CampaignStatus = Field(default=CampaignStatus.DRAFT)
    
    model_config = ConfigDict(from_attributes=True)


class CampaignCreate(CampaignBase):
    """Model for creating a campaign."""
    pass


class Campaign(CampaignBase, TimestampMixin):
    """Complete campaign model."""
    id: str = Field(description="Campaign ID")
    platform_campaign_id: Optional[str] = Field(default=None, description="Platform-specific campaign ID")
    impressions: int = Field(default=0)
    clicks: int = Field(default=0)
    conversions: int = Field(default=0)
    spend: float = Field(default=0.0)
    
    model_config = ConfigDict(from_attributes=True)


# Ad Group Models

class AdGroupBase(BaseModel):
    """Base ad group model."""
    campaign_id: str = Field(description="Campaign ID")
    name: str = Field(description="Ad group name")
    bid_strategy: BidStrategy = Field(description="Bid strategy")
    bid_amount: Optional[float] = Field(default=None, description="Bid amount")
    daily_budget: Optional[float] = Field(default=None, description="Daily budget")
    
    model_config = ConfigDict(from_attributes=True)


class AdGroupCreate(AdGroupBase):
    """Model for creating an ad group."""
    pass


class AdGroup(AdGroupBase, TimestampMixin):
    """Complete ad group model."""
    id: str = Field(description="Ad group ID")
    status: str = Field(default="active")
    impressions: int = Field(default=0)
    clicks: int = Field(default=0)
    ctr: float = Field(default=0.0, description="Click-through rate")
    
    model_config = ConfigDict(from_attributes=True)


# Ad Models

class AdBase(BaseModel):
    """Base ad model."""
    ad_group_id: str = Field(description="Ad group ID")
    name: str = Field(description="Ad name")
    type: AdType = Field(description="Ad type")
    headline: str = Field(description="Ad headline")
    description: Optional[str] = Field(default=None, description="Ad description")
    final_url: str = Field(description="Final URL")
    
    model_config = ConfigDict(from_attributes=True)


class AdCreate(AdBase):
    """Model for creating an ad."""
    creative_id: Optional[str] = None


class Ad(AdBase, TimestampMixin):
    """Complete ad model."""
    id: str = Field(description="Ad ID")
    creative_id: Optional[str] = None
    status: str = Field(default="active")
    impressions: int = Field(default=0)
    clicks: int = Field(default=0)
    conversions: int = Field(default=0)
    
    model_config = ConfigDict(from_attributes=True)


# Creative Models

class CreativeBase(BaseModel):
    """Base creative model."""
    name: str = Field(description="Creative name")
    type: AdType = Field(description="Creative type")
    asset_url: Optional[str] = Field(default=None, description="Asset URL")
    thumbnail_url: Optional[str] = Field(default=None, description="Thumbnail URL")
    metadata: Optional[dict[str, Any]] = Field(default=None)
    
    model_config = ConfigDict(from_attributes=True)


class CreativeCreate(CreativeBase):
    """Model for creating a creative."""
    pass


class Creative(CreativeBase, TimestampMixin):
    """Complete creative model."""
    id: str = Field(description="Creative ID")
    
    model_config = ConfigDict(from_attributes=True)


# Audience Models

class AudienceBase(BaseModel):
    """Base audience model."""
    name: str = Field(description="Audience name")
    platform: AdPlatform = Field(description="Platform")
    targeting_criteria: dict[str, Any] = Field(description="Targeting criteria")
    size_estimate: Optional[int] = Field(default=None)
    
    model_config = ConfigDict(from_attributes=True)


class AudienceCreate(AudienceBase):
    """Model for creating an audience."""
    pass


class Audience(AudienceBase, TimestampMixin):
    """Complete audience model."""
    id: str = Field(description="Audience ID")
    
    model_config = ConfigDict(from_attributes=True)


# Performance Models

class PerformanceBase(BaseModel):
    """Base performance model."""
    campaign_id: Optional[str] = None
    ad_group_id: Optional[str] = None
    ad_id: Optional[str] = None
    date: datetime = Field(description="Performance date")
    impressions: int = Field(default=0)
    clicks: int = Field(default=0)
    conversions: int = Field(default=0)
    spend: float = Field(default=0.0)
    revenue: Optional[float] = Field(default=None)
    
    model_config = ConfigDict(from_attributes=True)


class PerformanceCreate(PerformanceBase):
    """Model for creating performance record."""
    pass


class Performance(PerformanceBase, TimestampMixin):
    """Complete performance model."""
    id: str = Field(description="Performance ID")
    ctr: float = Field(default=0.0, description="CTR")
    cpc: float = Field(default=0.0, description="CPC")
    cpa: float = Field(default=0.0, description="CPA")
    roas: float = Field(default=0.0, description="ROAS")
    
    model_config = ConfigDict(from_attributes=True)


# Budget Models

class BudgetBase(BaseModel):
    """Base budget model."""
    campaign_id: str = Field(description="Campaign ID")
    daily_budget: float = Field(description="Daily budget")
    total_budget: Optional[float] = Field(default=None)
    pace_type: str = Field(default="standard", description="Budget pacing type")
    
    model_config = ConfigDict(from_attributes=True)


class Budget(BudgetBase, TimestampMixin):
    """Complete budget model."""
    id: str = Field(description="Budget ID")
    spent_today: float = Field(default=0.0)
    spent_total: float = Field(default=0.0)
    remaining: float = Field(default=0.0)
    
    model_config = ConfigDict(from_attributes=True)


# Bid Models

class BidBase(BaseModel):
    """Base bid model."""
    ad_group_id: str = Field(description="Ad group ID")
    strategy: BidStrategy = Field(description="Bid strategy")
    amount: Optional[float] = Field(default=None)
    target_cpa: Optional[float] = Field(default=None)
    target_roas: Optional[float] = Field(default=None)
    
    model_config = ConfigDict(from_attributes=True)


class Bid(BidBase, TimestampMixin):
    """Complete bid model."""
    id: str = Field(description="Bid ID")
    
    model_config = ConfigDict(from_attributes=True)
