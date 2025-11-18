"""
Type definitions for the Content Calendar module.

This module contains all data types, enums, and schemas used throughout
the content calendar system.
"""
from datetime import datetime, time
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
import pytz


class Priority(str, Enum):
    """Content priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class RecurrenceType(str, Enum):
    """Recurrence pattern types."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class DayOfWeek(str, Enum):
    """Days of the week."""

    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class ContentFormat(str, Enum):
    """Content format types."""

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    CAROUSEL = "carousel"
    STORY = "story"
    REEL = "reel"
    ARTICLE = "article"
    LINK = "link"


class ApprovalStatus(str, Enum):
    """Approval workflow statuses."""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    IN_REVIEW = "in_review"
    CHANGES_REQUESTED = "changes_requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class NotificationType(str, Enum):
    """Notification types."""

    ASSIGNMENT = "assignment"
    REVIEW_REQUEST = "review_request"
    APPROVAL = "approval"
    REJECTION = "rejection"
    COMMENT = "comment"
    MENTION = "mention"
    DEADLINE = "deadline"
    PUBLISH_SUCCESS = "publish_success"
    PUBLISH_FAILURE = "publish_failure"


# Pydantic Models
class RecurringPattern(BaseModel):
    """Recurring content pattern configuration."""

    model_config = ConfigDict(use_enum_values=True)

    type: RecurrenceType = Field(description="Type of recurrence")
    interval: int = Field(default=1, ge=1, description="Interval between occurrences")
    days_of_week: Optional[list[DayOfWeek]] = Field(
        default=None, description="Days of week (for weekly recurrence)"
    )
    day_of_month: Optional[int] = Field(
        default=None, ge=1, le=31, description="Day of month (for monthly recurrence)"
    )
    end_date: Optional[datetime] = Field(default=None, description="End date for recurrence")
    occurrences: Optional[int] = Field(
        default=None, ge=1, description="Number of occurrences"
    )

    @field_validator("days_of_week")
    @classmethod
    def validate_days_of_week(
        cls, v: Optional[list[DayOfWeek]]
    ) -> Optional[list[DayOfWeek]]:
        """Validate days of week."""
        if v is not None and len(v) == 0:
            raise ValueError("days_of_week must not be empty if provided")
        return v


class PublishingChannel(BaseModel):
    """Publishing channel configuration."""

    model_config = ConfigDict(use_enum_values=True)

    name: str = Field(description="Channel name (e.g., twitter, facebook)")
    platform: str = Field(description="Platform identifier")
    account_id: Optional[str] = Field(default=None, description="Account or page ID")
    account_name: Optional[str] = Field(default=None, description="Account display name")
    is_active: bool = Field(default=True, description="Whether channel is active")
    config: dict[str, Any] = Field(
        default_factory=dict, description="Channel-specific configuration"
    )


class MediaAsset(BaseModel):
    """Media asset metadata."""

    model_config = ConfigDict(use_enum_values=True)

    url: str = Field(description="Media URL")
    type: str = Field(description="Media type (image, video, etc.)")
    filename: str = Field(description="Original filename")
    size: int = Field(description="File size in bytes")
    width: Optional[int] = Field(default=None, description="Width in pixels")
    height: Optional[int] = Field(default=None, description="Height in pixels")
    duration: Optional[float] = Field(default=None, description="Duration in seconds (for video)")
    thumbnail_url: Optional[str] = Field(default=None, description="Thumbnail URL")
    alt_text: Optional[str] = Field(default=None, description="Alt text for accessibility")


class ContentMetadata(BaseModel):
    """Content metadata."""

    model_config = ConfigDict(use_enum_values=True)

    tags: list[str] = Field(default_factory=list, description="Content tags")
    categories: list[str] = Field(default_factory=list, description="Content categories")
    keywords: list[str] = Field(default_factory=list, description="SEO keywords")
    target_audience: Optional[str] = Field(default=None, description="Target audience")
    language: str = Field(default="en", description="Content language")
    location: Optional[str] = Field(default=None, description="Geographic location")
    custom_fields: dict[str, Any] = Field(
        default_factory=dict, description="Custom metadata fields"
    )


class ScheduleConfig(BaseModel):
    """Schedule configuration."""

    model_config = ConfigDict(use_enum_values=True)

    scheduled_time: datetime = Field(description="Scheduled publication time")
    timezone: str = Field(default="UTC", description="Timezone for scheduling")
    auto_schedule: bool = Field(
        default=False, description="Whether to auto-schedule at optimal time"
    )
    send_notification: bool = Field(
        default=True, description="Send notification when published"
    )
    retry_on_failure: bool = Field(
        default=True, description="Retry publication on failure"
    )
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        """Validate timezone."""
        if v not in pytz.all_timezones:
            raise ValueError(f"Invalid timezone: {v}")
        return v


class CalendarEvent(BaseModel):
    """Calendar event for content planning."""

    model_config = ConfigDict(use_enum_values=True)

    id: Optional[int] = Field(default=None, description="Event ID")
    title: str = Field(description="Event title")
    description: Optional[str] = Field(default=None, description="Event description")
    content: str = Field(description="Content text")
    content_type: ContentFormat = Field(description="Content format")
    status: ApprovalStatus = Field(
        default=ApprovalStatus.DRAFT, description="Current status"
    )
    priority: Priority = Field(default=Priority.MEDIUM, description="Priority level")

    # Scheduling
    schedule: ScheduleConfig = Field(description="Schedule configuration")
    recurring: Optional[RecurringPattern] = Field(
        default=None, description="Recurring pattern"
    )

    # Channels
    channels: list[PublishingChannel] = Field(
        default_factory=list, description="Publishing channels"
    )

    # Media
    media: list[MediaAsset] = Field(default_factory=list, description="Media assets")

    # Metadata
    metadata: ContentMetadata = Field(
        default_factory=ContentMetadata, description="Content metadata"
    )

    # Campaign
    campaign_id: Optional[int] = Field(default=None, description="Associated campaign ID")
    campaign_name: Optional[str] = Field(default=None, description="Campaign name")

    # Team
    creator_id: int = Field(description="Creator user ID")
    assignees: list[int] = Field(default_factory=list, description="Assigned user IDs")

    # Analytics
    views: int = Field(default=0, ge=0, description="View count")
    likes: int = Field(default=0, ge=0, description="Like count")
    shares: int = Field(default=0, ge=0, description="Share count")
    comments: int = Field(default=0, ge=0, description="Comment count")
    engagement_rate: float = Field(default=0.0, ge=0.0, description="Engagement rate")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ContentPlan(BaseModel):
    """Content plan for a specific time period."""

    model_config = ConfigDict(use_enum_values=True)

    id: Optional[int] = Field(default=None, description="Plan ID")
    name: str = Field(description="Plan name")
    description: Optional[str] = Field(default=None, description="Plan description")
    start_date: datetime = Field(description="Plan start date")
    end_date: datetime = Field(description="Plan end date")
    events: list[CalendarEvent] = Field(default_factory=list, description="Calendar events")
    goals: dict[str, Any] = Field(default_factory=dict, description="Plan goals and KPIs")
    budget: Optional[float] = Field(default=None, ge=0, description="Budget allocated")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WorkflowStep(BaseModel):
    """Workflow step definition."""

    model_config = ConfigDict(use_enum_values=True)

    id: Optional[int] = Field(default=None, description="Step ID")
    name: str = Field(description="Step name")
    description: Optional[str] = Field(default=None, description="Step description")
    order: int = Field(ge=0, description="Step order")
    assignee_id: Optional[int] = Field(default=None, description="Assigned user ID")
    role: Optional[str] = Field(default=None, description="Required role")
    status: ApprovalStatus = Field(
        default=ApprovalStatus.PENDING_REVIEW, description="Step status"
    )
    deadline: Optional[datetime] = Field(default=None, description="Deadline")
    completed_at: Optional[datetime] = Field(default=None, description="Completion time")


class Workflow(BaseModel):
    """Content approval workflow."""

    model_config = ConfigDict(use_enum_values=True)

    id: Optional[int] = Field(default=None, description="Workflow ID")
    name: str = Field(description="Workflow name")
    description: Optional[str] = Field(default=None, description="Workflow description")
    content_id: int = Field(description="Associated content ID")
    steps: list[WorkflowStep] = Field(description="Workflow steps")
    current_step: int = Field(default=0, ge=0, description="Current step index")
    status: ApprovalStatus = Field(
        default=ApprovalStatus.PENDING_REVIEW, description="Overall workflow status"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Comment(BaseModel):
    """Comment or feedback."""

    model_config = ConfigDict(use_enum_values=True)

    id: Optional[int] = Field(default=None, description="Comment ID")
    content_id: int = Field(description="Associated content ID")
    author_id: int = Field(description="Author user ID")
    author_name: Optional[str] = Field(default=None, description="Author name")
    text: str = Field(description="Comment text")
    parent_id: Optional[int] = Field(default=None, description="Parent comment ID")
    is_resolved: bool = Field(default=False, description="Whether comment is resolved")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Notification(BaseModel):
    """User notification."""

    model_config = ConfigDict(use_enum_values=True)

    id: Optional[int] = Field(default=None, description="Notification ID")
    user_id: int = Field(description="Target user ID")
    type: NotificationType = Field(description="Notification type")
    title: str = Field(description="Notification title")
    message: str = Field(description="Notification message")
    link: Optional[str] = Field(default=None, description="Related link")
    is_read: bool = Field(default=False, description="Whether notification is read")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AnalyticsMetric(BaseModel):
    """Analytics metric."""

    model_config = ConfigDict(use_enum_values=True)

    metric_name: str = Field(description="Metric name")
    metric_value: float = Field(description="Metric value")
    channel: Optional[str] = Field(default=None, description="Channel name")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PerformanceReport(BaseModel):
    """Performance report for content."""

    model_config = ConfigDict(use_enum_values=True)

    content_id: int = Field(description="Content ID")
    period_start: datetime = Field(description="Report period start")
    period_end: datetime = Field(description="Report period end")
    metrics: list[AnalyticsMetric] = Field(description="Collected metrics")
    total_views: int = Field(default=0, ge=0)
    total_likes: int = Field(default=0, ge=0)
    total_shares: int = Field(default=0, ge=0)
    total_comments: int = Field(default=0, ge=0)
    engagement_rate: float = Field(default=0.0, ge=0.0)
    roi: Optional[float] = Field(default=None, description="Return on investment")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class OptimalTime(BaseModel):
    """Optimal posting time recommendation."""

    model_config = ConfigDict(use_enum_values=True)

    channel: str = Field(description="Channel name")
    day_of_week: DayOfWeek = Field(description="Recommended day")
    time: time = Field(description="Recommended time")
    expected_engagement: float = Field(ge=0.0, description="Expected engagement rate")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")
