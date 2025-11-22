"""
Social Media Module - Database Models.

SQLAlchemy models for PostgreSQL database integration.
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, JSON, Text,
    ForeignKey, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

from .social_types import (
    PostStatus, PlatformType, CampaignStatus,
    ApprovalStatus, MediaType, SentimentType
)

Base = declarative_base()


class PostModel(Base):
    """Database model for social media posts."""

    __tablename__ = "social_posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    status = Column(SQLEnum(PostStatus), default=PostStatus.DRAFT)
    platforms = Column(ARRAY(String), nullable=False)
    scheduled_time = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("social_campaigns.id"), nullable=True)
    author_id = Column(UUID(as_uuid=True), nullable=False)
    approver_id = Column(UUID(as_uuid=True), nullable=True)
    approval_status = Column(SQLEnum(ApprovalStatus), default=ApprovalStatus.PENDING)
    content_by_platform = Column(JSON, default={})
    platform_post_ids = Column(JSON, default={})
    performance_metrics = Column(JSON, default={})
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(String(500), nullable=True)
    parent_post_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON, default={})

    # Relationships
    campaign = relationship("CampaignModel", back_populates="posts")


class CampaignModel(Base):
    """Database model for campaigns."""

    __tablename__ = "social_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(CampaignStatus), default=CampaignStatus.DRAFT)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    platforms = Column(ARRAY(String), nullable=False)
    budget = Column(Float, default=0.0)
    spent = Column(Float, default=0.0)
    goals = Column(JSON, default={})
    target_audience = Column(JSON, default={})
    color_code = Column(String(20), default="#3B82F6")
    owner_id = Column(UUID(as_uuid=True), nullable=False)
    team_members = Column(ARRAY(UUID(as_uuid=True)), default=[])
    performance_metrics = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON, default={})

    # Relationships
    posts = relationship("PostModel", back_populates="campaign")


class AnalyticsModel(Base):
    """Database model for analytics."""

    __tablename__ = "social_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    entity_type = Column(String(50), nullable=False)
    platform = Column(SQLEnum(PlatformType), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    impressions = Column(Integer, default=0)
    reach = Column(Integer, default=0)
    engagement_count = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)
    metadata = Column(JSON, default={})


class EngagementModel(Base):
    """Database model for engagements."""

    __tablename__ = "social_engagements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = Column(UUID(as_uuid=True), nullable=False)
    platform = Column(SQLEnum(PlatformType), nullable=False)
    platform_engagement_id = Column(String(255), nullable=False)
    engagement_type = Column(String(50), nullable=False)
    user_id = Column(String(255), nullable=False)
    username = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    sentiment = Column(SQLEnum(SentimentType), default=SentimentType.NEUTRAL)
    sentiment_score = Column(Float, default=0.0)
    is_read = Column(Boolean, default=False)
    is_replied = Column(Boolean, default=False)
    reply_content = Column(Text, nullable=True)
    replied_at = Column(DateTime, nullable=True)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, default={})
