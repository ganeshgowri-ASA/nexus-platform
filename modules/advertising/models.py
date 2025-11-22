<<<<<<< HEAD
"""Database models for advertising module."""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON, Index
from sqlalchemy.orm import relationship

from config.database import Base
from shared.utils import generate_uuid


class Campaign(Base):
    """Campaign database model."""
    __tablename__ = "campaigns"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)
    objective = Column(String(100), nullable=False)
    platform = Column(String(50), nullable=False, index=True)
    platform_campaign_id = Column(String(255), unique=True)
    daily_budget = Column(Float, nullable=False)
    total_budget = Column(Float)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    status = Column(String(50), default="draft", index=True)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    spend = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    ad_groups = relationship("AdGroup", back_populates="campaign", cascade="all, delete-orphan")
    performance = relationship("AdPerformance", back_populates="campaign", cascade="all, delete-orphan")


class AdGroup(Base):
    """Ad Group database model."""
    __tablename__ = "ad_groups"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    campaign_id = Column(String(36), ForeignKey("campaigns.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    bid_strategy = Column(String(50), nullable=False)
    bid_amount = Column(Float)
    daily_budget = Column(Float)
    status = Column(String(50), default="active", index=True)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    ctr = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    campaign = relationship("Campaign", back_populates="ad_groups")
    ads = relationship("Ad", back_populates="ad_group", cascade="all, delete-orphan")


class Ad(Base):
    """Ad database model."""
    __tablename__ = "ads"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    ad_group_id = Column(String(36), ForeignKey("ad_groups.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    headline = Column(String(500), nullable=False)
    description = Column(Text)
    final_url = Column(String(1000), nullable=False)
    creative_id = Column(String(36), ForeignKey("creatives.id"))
    status = Column(String(50), default="active", index=True)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    ad_group = relationship("AdGroup", back_populates="ads")
    creative = relationship("Creative", back_populates="ads")


class Creative(Base):
    """Creative database model."""
    __tablename__ = "creatives"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, unique=True)
    type = Column(String(50), nullable=False)
    asset_url = Column(String(1000))
    thumbnail_url = Column(String(1000))
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    ads = relationship("Ad", back_populates="creative")


class Audience(Base):
    """Audience database model."""
    __tablename__ = "audiences"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, unique=True)
    platform = Column(String(50), nullable=False)
    targeting_criteria = Column(JSON, nullable=False)
    size_estimate = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AdPerformance(Base):
    """Ad Performance database model."""
    __tablename__ = "ad_performance"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    campaign_id = Column(String(36), ForeignKey("campaigns.id"), index=True)
    ad_group_id = Column(String(36), ForeignKey("ad_groups.id"), index=True)
    ad_id = Column(String(36), ForeignKey("ads.id"), index=True)
    date = Column(DateTime, nullable=False, index=True)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    spend = Column(Float, default=0.0)
    revenue = Column(Float)
=======
"""
Database models for advertising module.
"""
from datetime import datetime
from typing import Optional
from uuid import uuid4
import enum

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


class AdPlatform(str, enum.Enum):
    """Ad platform types."""
    GOOGLE_ADS = "google_ads"
    FACEBOOK_ADS = "facebook_ads"
    LINKEDIN_ADS = "linkedin_ads"
    TWITTER_ADS = "twitter_ads"


class CampaignStatus(str, enum.Enum):
    """Campaign status."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CampaignObjective(str, enum.Enum):
    """Campaign objective."""
    AWARENESS = "awareness"
    CONSIDERATION = "consideration"
    CONVERSION = "conversion"
    TRAFFIC = "traffic"
    ENGAGEMENT = "engagement"
    LEAD_GENERATION = "lead_generation"
    SALES = "sales"


class BidStrategy(str, enum.Enum):
    """Bid strategy."""
    MANUAL_CPC = "manual_cpc"
    MANUAL_CPM = "manual_cpm"
    AUTOMATED = "automated"
    TARGET_CPA = "target_cpa"
    TARGET_ROAS = "target_roas"
    MAXIMIZE_CLICKS = "maximize_clicks"
    MAXIMIZE_CONVERSIONS = "maximize_conversions"


class AdStatus(str, enum.Enum):
    """Ad status."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class Campaign(Base):
    """Advertising campaign model."""

    __tablename__ = "campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)

    # Platform
    platform = Column(SQLEnum(AdPlatform), nullable=False, index=True)
    platform_campaign_id = Column(String(255), index=True)

    # Objective
    objective = Column(SQLEnum(CampaignObjective), nullable=False)

    # Budget
    budget_type = Column(String(50))  # daily, lifetime
    daily_budget = Column(Float)
    lifetime_budget = Column(Float)
    spent = Column(Float, default=0.0)
    currency = Column(String(3), default="USD")

    # Bid Strategy
    bid_strategy = Column(SQLEnum(BidStrategy), nullable=False)
    bid_amount = Column(Float)
    target_cpa = Column(Float)
    target_roas = Column(Float)

    # Schedule
    start_date = Column(DateTime)
    end_date = Column(DateTime)

    # Status
    status = Column(SQLEnum(CampaignStatus), default=CampaignStatus.DRAFT, index=True)

    # Tracking
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    ctr = Column(Float, default=0.0)
    cpc = Column(Float, default=0.0)
    cpm = Column(Float, default=0.0)
    cpa = Column(Float, default=0.0)
    roas = Column(Float, default=0.0)

    # Settings
    settings = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    synced_at = Column(DateTime)

    # Relationships
    ad_sets = relationship("AdSet", back_populates="campaign", cascade="all, delete-orphan")
    performance_metrics = relationship("CampaignPerformance", back_populates="campaign")


class AdSet(Base):
    """Ad set model."""

    __tablename__ = "ad_sets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)

    # Platform
    platform_adset_id = Column(String(255), index=True)

    # Budget
    budget_type = Column(String(50))
    daily_budget = Column(Float)
    lifetime_budget = Column(Float)
    spent = Column(Float, default=0.0)

    # Bid
    bid_amount = Column(Float)

    # Schedule
    start_date = Column(DateTime)
    end_date = Column(DateTime)

    # Targeting
    targeting = Column(JSON, nullable=False)  # Demographics, interests, behaviors
    locations = Column(JSON, default=[])
    age_min = Column(Integer)
    age_max = Column(Integer)
    genders = Column(JSON, default=[])
    languages = Column(JSON, default=[])
    interests = Column(JSON, default=[])
    behaviors = Column(JSON, default=[])
    custom_audiences = Column(JSON, default=[])
    excluded_audiences = Column(JSON, default=[])

    # Status
    status = Column(String(50), default="active")

    # Tracking
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    spent = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    synced_at = Column(DateTime)

    # Relationships
    campaign = relationship("Campaign", back_populates="ad_sets")
    ads = relationship("Ad", back_populates="ad_set", cascade="all, delete-orphan")


class Ad(Base):
    """Ad model."""

    __tablename__ = "ads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    ad_set_id = Column(UUID(as_uuid=True), ForeignKey("ad_sets.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)

    # Platform
    platform_ad_id = Column(String(255), index=True)

    # Creative
    creative_id = Column(UUID(as_uuid=True), ForeignKey("ad_creatives.id"))
    headline = Column(String(500))
    description = Column(Text)
    call_to_action = Column(String(100))
    destination_url = Column(String(1000))

    # Tracking
    tracking_params = Column(JSON, default={})

    # Status
    status = Column(SQLEnum(AdStatus), default=AdStatus.DRAFT, index=True)
    review_status = Column(String(50))
    rejection_reason = Column(Text)

    # Performance
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    spent = Column(Float, default=0.0)
    ctr = Column(Float, default=0.0)
    cpc = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    synced_at = Column(DateTime)

    # Relationships
    ad_set = relationship("AdSet", back_populates="ads")
    creative = relationship("AdCreative")
    performance_metrics = relationship("AdPerformance", back_populates="ad")


class AdCreative(Base):
    """Ad creative model."""

    __tablename__ = "ad_creatives"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)  # image, video, carousel, etc.

    # Content
    title = Column(String(500))
    body = Column(Text)
    images = Column(JSON, default=[])  # Image URLs
    videos = Column(JSON, default=[])  # Video URLs
    thumbnail_url = Column(String(1000))

    # Carousel (multiple items)
    carousel_items = Column(JSON, default=[])

    # Preview
    preview_url = Column(String(1000))

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CampaignPerformance(Base):
    """Campaign performance tracking model."""

    __tablename__ = "campaign_performance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False, index=True)

    # Date
    date = Column(DateTime, nullable=False, index=True)

    # Metrics
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    spent = Column(Float, default=0.0)
    revenue = Column(Float, default=0.0)

    # Calculated metrics
    ctr = Column(Float, default=0.0)
    cpc = Column(Float, default=0.0)
    cpm = Column(Float, default=0.0)
    cpa = Column(Float, default=0.0)
    roas = Column(Float, default=0.0)
    conversion_rate = Column(Float, default=0.0)

    # Additional metrics
    video_views = Column(Integer, default=0)
    video_completion_rate = Column(Float, default=0.0)
    engagement_rate = Column(Float, default=0.0)
    reach = Column(Integer, default=0)
    frequency = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign", back_populates="performance_metrics")


class AdPerformance(Base):
    """Ad performance tracking model."""

    __tablename__ = "ad_performance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    ad_id = Column(UUID(as_uuid=True), ForeignKey("ads.id"), nullable=False, index=True)

    # Date
    date = Column(DateTime, nullable=False, index=True)

    # Metrics
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    spent = Column(Float, default=0.0)
    revenue = Column(Float, default=0.0)

    # Calculated metrics
>>>>>>> origin/claude/lead-gen-advertising-modules-013aKZjYzcLFmpKdzNMTj8Bi
    ctr = Column(Float, default=0.0)
    cpc = Column(Float, default=0.0)
    cpa = Column(Float, default=0.0)
    roas = Column(Float, default=0.0)
<<<<<<< HEAD
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    campaign = relationship("Campaign", back_populates="performance")
    
    __table_args__ = (
        Index("idx_performance_date", "date"),
        Index("idx_performance_campaign", "campaign_id", "date"),
    )


class BudgetTracking(Base):
    """Budget tracking database model."""
    __tablename__ = "budget_tracking"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    campaign_id = Column(String(36), ForeignKey("campaigns.id"), nullable=False, index=True)
    daily_budget = Column(Float, nullable=False)
    total_budget = Column(Float)
    spent_today = Column(Float, default=0.0)
    spent_total = Column(Float, default=0.0)
    remaining = Column(Float, default=0.0)
    pace_type = Column(String(50), default="standard")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
=======

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    ad = relationship("Ad", back_populates="performance_metrics")


class ABTest(Base):
    """A/B test model."""

    __tablename__ = "ab_tests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Test Configuration
    test_type = Column(String(100), nullable=False)  # ad_creative, targeting, bid, etc.
    variant_a_id = Column(String(255), nullable=False)
    variant_b_id = Column(String(255), nullable=False)
    traffic_split = Column(Integer, default=50)  # Percentage for variant A

    # Status
    status = Column(String(50), default="running")
    winner = Column(String(10))  # 'A', 'B', or 'tie'

    # Schedule
    start_date = Column(DateTime)
    end_date = Column(DateTime)

    # Results
    results = Column(JSON, default={})
    confidence_level = Column(Float)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)


class AutomatedRule(Base):
    """Automated rule model for campaign optimization."""

    __tablename__ = "automated_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Target
    target_type = Column(String(100), nullable=False)  # campaign, ad_set, ad
    target_id = Column(UUID(as_uuid=True), nullable=False)

    # Conditions
    conditions = Column(JSON, nullable=False)

    # Actions
    actions = Column(JSON, nullable=False)

    # Schedule
    schedule = Column(String(100))  # daily, hourly, etc.

    # Status
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime)
    next_run_at = Column(DateTime)

    # Execution History
    execution_count = Column(Integer, default=0)
    last_execution_result = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConversionTracking(Base):
    """Conversion tracking model."""

    __tablename__ = "conversion_tracking"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Campaign/Ad Reference
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), index=True)
    ad_id = Column(UUID(as_uuid=True), ForeignKey("ads.id"), index=True)

    # Conversion Details
    conversion_type = Column(String(100), nullable=False)
    conversion_value = Column(Float, default=0.0)
    currency = Column(String(3), default="USD")

    # Attribution
    click_id = Column(String(255))
    user_id = Column(String(255))
    session_id = Column(String(255))

    # Metadata
    metadata = Column(JSON, default={})

    # Timestamps
    click_time = Column(DateTime)
    conversion_time = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
>>>>>>> origin/claude/lead-gen-advertising-modules-013aKZjYzcLFmpKdzNMTj8Bi
