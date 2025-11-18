"""
NEXUS Platform - Attribution Module Database Models
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, JSON, Index, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
import enum

from backend.app.db.base import Base, TimestampMixin


class ChannelType(str, enum.Enum):
    """Marketing channel types."""
    DIRECT = "direct"
    ORGANIC_SEARCH = "organic_search"
    PAID_SEARCH = "paid_search"
    SOCIAL_ORGANIC = "social_organic"
    SOCIAL_PAID = "social_paid"
    EMAIL = "email"
    REFERRAL = "referral"
    DISPLAY = "display"
    AFFILIATE = "affiliate"
    VIDEO = "video"
    OTHER = "other"


class TouchpointType(str, enum.Enum):
    """Touchpoint interaction types."""
    IMPRESSION = "impression"
    CLICK = "click"
    VIEW = "view"
    ENGAGEMENT = "engagement"
    CONVERSION = "conversion"


class AttributionModelType(str, enum.Enum):
    """Attribution model types."""
    FIRST_TOUCH = "first_touch"
    LAST_TOUCH = "last_touch"
    LINEAR = "linear"
    TIME_DECAY = "time_decay"
    POSITION_BASED = "position_based"
    DATA_DRIVEN = "data_driven"
    CUSTOM = "custom"


class ConversionType(str, enum.Enum):
    """Conversion types."""
    PURCHASE = "purchase"
    SIGNUP = "signup"
    LEAD = "lead"
    DOWNLOAD = "download"
    SUBSCRIPTION = "subscription"
    TRIAL = "trial"
    CUSTOM = "custom"


class Channel(Base, TimestampMixin):
    """Marketing channel model."""

    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    channel_type = Column(SQLEnum(ChannelType), nullable=False)
    description = Column(Text)
    cost_per_click = Column(Float, default=0.0)
    cost_per_impression = Column(Float, default=0.0)
    monthly_budget = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    metadata = Column(JSON, default=dict)

    # Relationships
    touchpoints = relationship("Touchpoint", back_populates="channel", cascade="all, delete-orphan")
    attribution_results = relationship("AttributionResult", back_populates="channel")

    # Indexes
    __table_args__ = (
        Index("idx_channel_type", "channel_type"),
        Index("idx_channel_active", "is_active"),
    )


class Journey(Base, TimestampMixin):
    """Customer journey model."""

    __tablename__ = "journeys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False)
    session_id = Column(String(255))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    total_touchpoints = Column(Integer, default=0)
    conversion_value = Column(Float, default=0.0)
    has_conversion = Column(Boolean, default=False)
    journey_duration_minutes = Column(Integer)
    metadata = Column(JSON, default=dict)

    # Relationships
    touchpoints = relationship("Touchpoint", back_populates="journey", cascade="all, delete-orphan")
    conversions = relationship("Conversion", back_populates="journey", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_journey_user", "user_id"),
        Index("idx_journey_session", "session_id"),
        Index("idx_journey_conversion", "has_conversion"),
        Index("idx_journey_start_time", "start_time"),
    )


class Touchpoint(Base, TimestampMixin):
    """Customer touchpoint model."""

    __tablename__ = "touchpoints"

    id = Column(Integer, primary_key=True, index=True)
    journey_id = Column(Integer, ForeignKey("journeys.id"), nullable=False)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)
    touchpoint_type = Column(SQLEnum(TouchpointType), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    position_in_journey = Column(Integer, nullable=False)

    # Engagement metrics
    time_spent_seconds = Column(Integer, default=0)
    pages_viewed = Column(Integer, default=0)
    engagement_score = Column(Float, default=0.0)

    # Cost data
    cost = Column(Float, default=0.0)

    # Context
    page_url = Column(String(2048))
    referrer_url = Column(String(2048))
    campaign_id = Column(String(255))
    campaign_name = Column(String(255))
    ad_group = Column(String(255))
    keyword = Column(String(255))
    device_type = Column(String(50))
    browser = Column(String(100))
    location = Column(String(255))

    metadata = Column(JSON, default=dict)

    # Relationships
    journey = relationship("Journey", back_populates="touchpoints")
    channel = relationship("Channel", back_populates="touchpoints")

    # Indexes
    __table_args__ = (
        Index("idx_touchpoint_journey", "journey_id"),
        Index("idx_touchpoint_channel", "channel_id"),
        Index("idx_touchpoint_timestamp", "timestamp"),
        Index("idx_touchpoint_type", "touchpoint_type"),
        Index("idx_touchpoint_campaign", "campaign_id"),
    )


class Conversion(Base, TimestampMixin):
    """Conversion event model."""

    __tablename__ = "conversions"

    id = Column(Integer, primary_key=True, index=True)
    journey_id = Column(Integer, ForeignKey("journeys.id"), nullable=False)
    conversion_type = Column(SQLEnum(ConversionType), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Value metrics
    revenue = Column(Float, default=0.0)
    quantity = Column(Integer, default=1)

    # Conversion details
    product_id = Column(String(255))
    product_name = Column(String(255))
    category = Column(String(255))

    metadata = Column(JSON, default=dict)

    # Relationships
    journey = relationship("Journey", back_populates="conversions")

    # Indexes
    __table_args__ = (
        Index("idx_conversion_journey", "journey_id"),
        Index("idx_conversion_type", "conversion_type"),
        Index("idx_conversion_timestamp", "timestamp"),
    )


class AttributionModel(Base, TimestampMixin):
    """Attribution model configuration."""

    __tablename__ = "attribution_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    model_type = Column(SQLEnum(AttributionModelType), nullable=False)
    description = Column(Text)

    # Model parameters
    time_decay_halflife_days = Column(Float)  # For time-decay model
    position_weights = Column(JSON)  # For position-based model: {"first": 0.4, "middle": 0.2, "last": 0.4}
    custom_rules = Column(JSON)  # For custom model

    # AI/ML parameters for data-driven model
    ml_model_type = Column(String(100))
    ml_parameters = Column(JSON)
    training_data_window_days = Column(Integer, default=90)

    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)

    metadata = Column(JSON, default=dict)

    # Relationships
    attribution_results = relationship("AttributionResult", back_populates="attribution_model")

    # Indexes
    __table_args__ = (
        Index("idx_attribution_model_type", "model_type"),
        Index("idx_attribution_model_active", "is_active"),
    )


class AttributionResult(Base, TimestampMixin):
    """Attribution analysis result."""

    __tablename__ = "attribution_results"

    id = Column(Integer, primary_key=True, index=True)
    journey_id = Column(Integer, ForeignKey("journeys.id"), nullable=False)
    attribution_model_id = Column(Integer, ForeignKey("attribution_models.id"), nullable=False)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)

    # Attribution metrics
    credit = Column(Float, nullable=False)  # Attribution credit (0-1 or actual value)
    attributed_revenue = Column(Float, default=0.0)
    attributed_conversions = Column(Float, default=0.0)

    # ROI metrics
    channel_cost = Column(Float, default=0.0)
    roi = Column(Float)  # Return on investment
    roas = Column(Float)  # Return on ad spend

    # Calculated at
    calculated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    metadata = Column(JSON, default=dict)

    # Relationships
    attribution_model = relationship("AttributionModel", back_populates="attribution_results")
    channel = relationship("Channel", back_populates="attribution_results")

    # Indexes
    __table_args__ = (
        Index("idx_attribution_result_journey", "journey_id"),
        Index("idx_attribution_result_model", "attribution_model_id"),
        Index("idx_attribution_result_channel", "channel_id"),
        Index("idx_attribution_result_calculated", "calculated_at"),
    )
