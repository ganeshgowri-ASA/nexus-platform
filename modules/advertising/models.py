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
    ctr = Column(Float, default=0.0)
    cpc = Column(Float, default=0.0)
    cpa = Column(Float, default=0.0)
    roas = Column(Float, default=0.0)
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
