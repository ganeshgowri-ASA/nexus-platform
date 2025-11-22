"""
Campaign Manager models for NEXUS Platform.

This module defines all database models for the campaign management system.
"""

from enum import Enum as PyEnum
from datetime import datetime, date
from typing import List, Optional

from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, Date, DateTime,
    Enum, ForeignKey, JSON, CheckConstraint, Index
)
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


# ==================== Enums ====================

class CampaignStatus(str, PyEnum):
    """Campaign lifecycle status."""
    DRAFT = "draft"
    PLANNED = "planned"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CampaignType(str, PyEnum):
    """Type of campaign."""
    PRODUCT_LAUNCH = "product_launch"
    BRAND_AWARENESS = "brand_awareness"
    LEAD_GENERATION = "lead_generation"
    SALES = "sales"
    EVENT = "event"
    CONTENT = "content"
    SOCIAL = "social"
    EMAIL = "email"
    CUSTOM = "custom"


class ChannelType(str, PyEnum):
    """Marketing channels."""
    EMAIL = "email"
    SOCIAL_MEDIA = "social_media"
    PAID_ADS = "paid_ads"
    CONTENT = "content"
    SEO = "seo"
    INFLUENCER = "influencer"
    EVENTS = "events"
    PR = "pr"
    DIRECT_MAIL = "direct_mail"
    OTHER = "other"


class AssetType(str, PyEnum):
    """Types of creative assets."""
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    DESIGN = "design"
    OTHER = "other"


class MilestoneStatus(str, PyEnum):
    """Milestone completion status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"
    CANCELLED = "cancelled"


class TeamMemberRole(str, PyEnum):
    """Team member roles in campaign."""
    OWNER = "owner"
    MANAGER = "manager"
    CONTRIBUTOR = "contributor"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


class ReportType(str, PyEnum):
    """Types of campaign reports."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"
    FINAL = "final"


# ==================== Models ====================

class Campaign(BaseModel):
    """
    Main campaign model.

    Represents a marketing campaign with all associated metadata.
    """

    __tablename__ = "campaigns"

    # Basic Information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    campaign_type = Column(Enum(CampaignType), nullable=False, index=True)
    status = Column(
        Enum(CampaignStatus),
        default=CampaignStatus.DRAFT,
        nullable=False,
        index=True
    )

    # Timeline
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    # Ownership
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Budget
    total_budget = Column(Float, default=0.0, nullable=False)
    spent_budget = Column(Float, default=0.0, nullable=False)

    # Goals and Metrics
    goals = Column(JSON, nullable=True)  # {"reach": 100000, "conversions": 1000}
    target_audience = Column(JSON, nullable=True)  # {"age": "25-45", "location": "US"}

    # AI-generated insights
    ai_insights = Column(JSON, nullable=True)
    optimization_suggestions = Column(JSON, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="campaigns", foreign_keys=[owner_id])
    channels = relationship(
        "CampaignChannel",
        back_populates="campaign",
        cascade="all, delete-orphan"
    )
    assets = relationship(
        "CampaignAsset",
        back_populates="campaign",
        cascade="all, delete-orphan"
    )
    team_members = relationship(
        "TeamMember",
        back_populates="campaign",
        cascade="all, delete-orphan"
    )
    milestones = relationship(
        "Milestone",
        back_populates="campaign",
        cascade="all, delete-orphan"
    )
    performance_metrics = relationship(
        "PerformanceMetric",
        back_populates="campaign",
        cascade="all, delete-orphan"
    )
    reports = relationship(
        "CampaignReport",
        back_populates="campaign",
        cascade="all, delete-orphan"
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint("total_budget >= 0", name="check_total_budget_positive"),
        CheckConstraint("spent_budget >= 0", name="check_spent_budget_positive"),
        CheckConstraint("spent_budget <= total_budget", name="check_budget_not_exceeded"),
        Index("idx_campaign_status_dates", "status", "start_date", "end_date"),
    )

    def __repr__(self) -> str:
        return f"<Campaign {self.name} ({self.status.value})>"

    @property
    def remaining_budget(self) -> float:
        """Calculate remaining budget."""
        return self.total_budget - self.spent_budget

    @property
    def budget_utilization(self) -> float:
        """Calculate budget utilization percentage."""
        if self.total_budget == 0:
            return 0.0
        return (self.spent_budget / self.total_budget) * 100

    @property
    def is_active(self) -> bool:
        """Check if campaign is currently active."""
        return self.status == CampaignStatus.ACTIVE

    @property
    def duration_days(self) -> Optional[int]:
        """Calculate campaign duration in days."""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return None


class CampaignChannel(BaseModel):
    """
    Marketing channels for a campaign.

    Represents different channels through which campaign is executed.
    """

    __tablename__ = "campaign_channels"

    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False, index=True)
    channel_type = Column(Enum(ChannelType), nullable=False)
    channel_name = Column(String(255), nullable=False)

    # Budget allocation for this channel
    allocated_budget = Column(Float, default=0.0, nullable=False)
    spent_budget = Column(Float, default=0.0, nullable=False)

    # Channel-specific configuration
    config = Column(JSON, nullable=True)  # Platform-specific settings

    # Performance data
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    revenue = Column(Float, default=0.0)

    # Status
    is_active = Column(Boolean, default=True)

    # Relationships
    campaign = relationship("Campaign", back_populates="channels")

    __table_args__ = (
        CheckConstraint("allocated_budget >= 0", name="check_channel_budget_positive"),
        CheckConstraint("spent_budget >= 0", name="check_channel_spent_positive"),
        Index("idx_channel_campaign_type", "campaign_id", "channel_type"),
    )

    def __repr__(self) -> str:
        return f"<CampaignChannel {self.channel_name} ({self.channel_type.value})>"

    @property
    def ctr(self) -> float:
        """Calculate Click-Through Rate."""
        if self.impressions == 0:
            return 0.0
        return (self.clicks / self.impressions) * 100

    @property
    def conversion_rate(self) -> float:
        """Calculate conversion rate."""
        if self.clicks == 0:
            return 0.0
        return (self.conversions / self.clicks) * 100

    @property
    def roi(self) -> float:
        """Calculate Return on Investment."""
        if self.spent_budget == 0:
            return 0.0
        return ((self.revenue - self.spent_budget) / self.spent_budget) * 100


class CampaignAsset(BaseModel):
    """
    Creative assets for campaigns.

    Stores all creative materials used in campaigns.
    """

    __tablename__ = "campaign_assets"

    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False, index=True)

    # Asset details
    name = Column(String(255), nullable=False)
    asset_type = Column(Enum(AssetType), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    mime_type = Column(String(100), nullable=True)

    # Metadata
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # ["social", "banner", "holiday"]

    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)

    # Approval workflow
    is_approved = Column(Boolean, default=False)
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    # Relationships
    campaign = relationship("Campaign", back_populates="assets")
    approved_by = relationship("User", foreign_keys=[approved_by_id])

    __table_args__ = (
        Index("idx_asset_campaign_type", "campaign_id", "asset_type"),
    )

    def __repr__(self) -> str:
        return f"<CampaignAsset {self.name} ({self.asset_type.value})>"


class TeamMember(BaseModel):
    """
    Team members assigned to campaigns.

    Manages team collaboration and permissions.
    """

    __tablename__ = "team_members"

    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Role and permissions
    role = Column(Enum(TeamMemberRole), nullable=False)

    # Assignment details
    assigned_tasks = Column(JSON, nullable=True)  # List of task IDs or descriptions
    notes = Column(Text, nullable=True)

    # Relationships
    campaign = relationship("Campaign", back_populates="team_members")
    user = relationship("User", back_populates="team_members")

    __table_args__ = (
        Index("idx_team_campaign_user", "campaign_id", "user_id", unique=True),
    )

    def __repr__(self) -> str:
        return f"<TeamMember campaign={self.campaign_id} user={self.user_id}>"


class Milestone(BaseModel):
    """
    Campaign milestones and timeline management.

    Represents key milestones in campaign execution.
    """

    __tablename__ = "milestones"

    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False, index=True)

    # Milestone details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        Enum(MilestoneStatus),
        default=MilestoneStatus.PENDING,
        nullable=False
    )

    # Timeline
    due_date = Column(Date, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Assignment
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Dependencies (for Gantt chart)
    dependencies = Column(JSON, nullable=True)  # [milestone_id1, milestone_id2]

    # Progress tracking
    progress_percentage = Column(Integer, default=0)

    # Relationships
    campaign = relationship("Campaign", back_populates="milestones")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])

    __table_args__ = (
        CheckConstraint(
            "progress_percentage >= 0 AND progress_percentage <= 100",
            name="check_progress_range"
        ),
        Index("idx_milestone_campaign_status", "campaign_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Milestone {self.title} ({self.status.value})>"

    @property
    def is_overdue(self) -> bool:
        """Check if milestone is overdue."""
        if self.status in [MilestoneStatus.COMPLETED, MilestoneStatus.CANCELLED]:
            return False
        return date.today() > self.due_date


class PerformanceMetric(BaseModel):
    """
    Performance metrics for campaigns.

    Stores time-series performance data for analytics.
    """

    __tablename__ = "performance_metrics"

    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False, index=True)
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Engagement metrics
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)

    # Financial metrics
    cost = Column(Float, default=0.0)
    revenue = Column(Float, default=0.0)
    roi = Column(Float, default=0.0)

    # Channel-specific metrics
    channel_breakdown = Column(JSON, nullable=True)

    # Custom metrics
    custom_metrics = Column(JSON, nullable=True)

    # Relationships
    campaign = relationship("Campaign", back_populates="performance_metrics")

    __table_args__ = (
        Index("idx_perf_campaign_date", "campaign_id", "recorded_at"),
    )

    def __repr__(self) -> str:
        return f"<PerformanceMetric campaign={self.campaign_id} at {self.recorded_at}>"


class CampaignReport(BaseModel):
    """
    Generated campaign reports.

    Stores both automated and manual campaign reports.
    """

    __tablename__ = "campaign_reports"

    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False, index=True)

    # Report details
    title = Column(String(255), nullable=False)
    report_type = Column(Enum(ReportType), nullable=False)

    # Report period
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # Report content
    summary = Column(Text, nullable=True)
    metrics = Column(JSON, nullable=False)  # All calculated metrics
    insights = Column(JSON, nullable=True)  # AI-generated insights
    recommendations = Column(JSON, nullable=True)  # AI recommendations

    # Report file (if generated as PDF/Excel)
    file_path = Column(String(500), nullable=True)

    # Generation details
    generated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_automated = Column(Boolean, default=False)

    # Relationships
    campaign = relationship("Campaign", back_populates="reports")
    generated_by = relationship("User", foreign_keys=[generated_by_id])

    __table_args__ = (
        Index("idx_report_campaign_type", "campaign_id", "report_type"),
        Index("idx_report_period", "period_start", "period_end"),
    )

    def __repr__(self) -> str:
        return f"<CampaignReport {self.title} ({self.report_type.value})>"
