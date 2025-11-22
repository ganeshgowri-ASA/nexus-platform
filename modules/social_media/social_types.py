"""
Social Media Module - Type Definitions and Data Models.

This module provides comprehensive type definitions for social media management,
including posts, profiles, campaigns, schedules, media, engagement, and analytics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4


class PlatformType(str, Enum):
    """Supported social media platforms."""

    FACEBOOK = "facebook"
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    PINTEREST = "pinterest"


class PostStatus(str, Enum):
    """Status of a social media post."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    DELETED = "deleted"


class MediaType(str, Enum):
    """Type of media content."""

    IMAGE = "image"
    VIDEO = "video"
    GIF = "gif"
    DOCUMENT = "document"
    AUDIO = "audio"


class CampaignStatus(str, Enum):
    """Status of a marketing campaign."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class SentimentType(str, Enum):
    """Sentiment analysis results."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class EngagementType(str, Enum):
    """Type of user engagement."""

    LIKE = "like"
    COMMENT = "comment"
    SHARE = "share"
    RETWEET = "retweet"
    REPLY = "reply"
    MENTION = "mention"
    DIRECT_MESSAGE = "direct_message"
    REACTION = "reaction"


class ApprovalStatus(str, Enum):
    """Approval workflow status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"


class AdStatus(str, Enum):
    """Social media advertisement status."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    REJECTED = "rejected"


@dataclass
class Media:
    """Media asset for social media posts."""

    id: UUID = field(default_factory=uuid4)
    media_type: MediaType = MediaType.IMAGE
    url: str = ""
    thumbnail_url: Optional[str] = None
    file_path: Optional[str] = None
    file_size: int = 0  # bytes
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None  # seconds for video/audio
    alt_text: Optional[str] = None
    caption: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert media to dictionary."""
        return {
            "id": str(self.id),
            "media_type": self.media_type.value,
            "url": self.url,
            "thumbnail_url": self.thumbnail_url,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "width": self.width,
            "height": self.height,
            "duration": self.duration,
            "alt_text": self.alt_text,
            "caption": self.caption,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class PlatformCredentials:
    """Credentials for a social media platform."""

    platform: PlatformType
    access_token: str
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    account_id: Optional[str] = None
    page_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Profile:
    """Social media profile/account."""

    id: UUID = field(default_factory=uuid4)
    platform: PlatformType = PlatformType.FACEBOOK
    platform_user_id: str = ""
    username: str = ""
    display_name: str = ""
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0
    verified: bool = False
    credentials: Optional[PlatformCredentials] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_synced_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            "id": str(self.id),
            "platform": self.platform.value,
            "platform_user_id": self.platform_user_id,
            "username": self.username,
            "display_name": self.display_name,
            "bio": self.bio,
            "profile_image_url": self.profile_image_url,
            "followers_count": self.followers_count,
            "following_count": self.following_count,
            "posts_count": self.posts_count,
            "verified": self.verified,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_synced_at": self.last_synced_at.isoformat() if self.last_synced_at else None,
            "metadata": self.metadata,
        }


@dataclass
class PostContent:
    """Content for a social media post (platform-specific)."""

    platform: PlatformType
    text: str = ""
    media: List[Media] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    location: Optional[str] = None
    link: Optional[str] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)  # Platform-specific fields

    def to_dict(self) -> Dict[str, Any]:
        """Convert post content to dictionary."""
        return {
            "platform": self.platform.value,
            "text": self.text,
            "media": [m.to_dict() for m in self.media],
            "hashtags": self.hashtags,
            "mentions": self.mentions,
            "location": self.location,
            "link": self.link,
            "custom_fields": self.custom_fields,
        }


@dataclass
class Post:
    """Social media post."""

    id: UUID = field(default_factory=uuid4)
    title: str = ""
    content_by_platform: Dict[PlatformType, PostContent] = field(default_factory=dict)
    platforms: List[PlatformType] = field(default_factory=list)
    status: PostStatus = PostStatus.DRAFT
    scheduled_time: Optional[datetime] = None
    published_at: Optional[datetime] = None
    campaign_id: Optional[UUID] = None
    author_id: UUID = field(default_factory=uuid4)
    approver_id: Optional[UUID] = None
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    approval_notes: Optional[str] = None
    platform_post_ids: Dict[str, str] = field(default_factory=dict)  # platform -> post_id
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None  # RRULE format
    parent_post_id: Optional[UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert post to dictionary."""
        return {
            "id": str(self.id),
            "title": self.title,
            "content_by_platform": {
                p.value: c.to_dict() for p, c in self.content_by_platform.items()
            },
            "platforms": [p.value for p in self.platforms],
            "status": self.status.value,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "campaign_id": str(self.campaign_id) if self.campaign_id else None,
            "author_id": str(self.author_id),
            "approver_id": str(self.approver_id) if self.approver_id else None,
            "approval_status": self.approval_status.value,
            "approval_notes": self.approval_notes,
            "platform_post_ids": self.platform_post_ids,
            "performance_metrics": self.performance_metrics,
            "is_recurring": self.is_recurring,
            "recurrence_rule": self.recurrence_rule,
            "parent_post_id": str(self.parent_post_id) if self.parent_post_id else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class Schedule:
    """Posting schedule configuration."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: Optional[str] = None
    timezone: str = "UTC"
    slots: List[Dict[str, Any]] = field(default_factory=list)  # Time slots for posting
    platforms: List[PlatformType] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert schedule to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "timezone": self.timezone,
            "slots": self.slots,
            "platforms": [p.value for p in self.platforms],
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class Campaign:
    """Marketing campaign."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: Optional[str] = None
    status: CampaignStatus = CampaignStatus.DRAFT
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    platforms: List[PlatformType] = field(default_factory=list)
    budget: float = 0.0
    spent: float = 0.0
    goals: Dict[str, Any] = field(default_factory=dict)
    target_audience: Dict[str, Any] = field(default_factory=dict)
    hashtags: List[str] = field(default_factory=list)
    color_code: str = "#3B82F6"  # For calendar visualization
    owner_id: UUID = field(default_factory=uuid4)
    team_members: List[UUID] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert campaign to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "platforms": [p.value for p in self.platforms],
            "budget": self.budget,
            "spent": self.spent,
            "goals": self.goals,
            "target_audience": self.target_audience,
            "hashtags": self.hashtags,
            "color_code": self.color_code,
            "owner_id": str(self.owner_id),
            "team_members": [str(m) for m in self.team_members],
            "performance_metrics": self.performance_metrics,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class Engagement:
    """User engagement with posts."""

    id: UUID = field(default_factory=uuid4)
    post_id: UUID = field(default_factory=uuid4)
    platform: PlatformType = PlatformType.FACEBOOK
    platform_engagement_id: str = ""
    engagement_type: EngagementType = EngagementType.LIKE
    user_id: str = ""
    username: str = ""
    user_profile_url: Optional[str] = None
    content: Optional[str] = None  # For comments, messages
    sentiment: SentimentType = SentimentType.NEUTRAL
    sentiment_score: float = 0.0  # -1.0 to 1.0
    is_read: bool = False
    is_replied: bool = False
    reply_content: Optional[str] = None
    replied_at: Optional[datetime] = None
    priority: int = 0  # Higher = more important
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert engagement to dictionary."""
        return {
            "id": str(self.id),
            "post_id": str(self.post_id),
            "platform": self.platform.value,
            "platform_engagement_id": self.platform_engagement_id,
            "engagement_type": self.engagement_type.value,
            "user_id": self.user_id,
            "username": self.username,
            "user_profile_url": self.user_profile_url,
            "content": self.content,
            "sentiment": self.sentiment.value,
            "sentiment_score": self.sentiment_score,
            "is_read": self.is_read,
            "is_replied": self.is_replied,
            "reply_content": self.reply_content,
            "replied_at": self.replied_at.isoformat() if self.replied_at else None,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class Analytics:
    """Analytics data for posts/campaigns."""

    id: UUID = field(default_factory=uuid4)
    entity_id: UUID = field(default_factory=uuid4)  # Post or Campaign ID
    entity_type: str = "post"  # post, campaign, profile
    platform: PlatformType = PlatformType.FACEBOOK
    date: datetime = field(default_factory=datetime.utcnow)
    impressions: int = 0
    reach: int = 0
    engagement_count: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    clicks: int = 0
    video_views: int = 0
    saves: int = 0
    engagement_rate: float = 0.0
    click_through_rate: float = 0.0
    conversion_count: int = 0
    conversion_rate: float = 0.0
    revenue: float = 0.0
    cost: float = 0.0
    roi: float = 0.0
    followers_gained: int = 0
    followers_lost: int = 0
    audience_demographics: Dict[str, Any] = field(default_factory=dict)
    top_performing_content: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert analytics to dictionary."""
        return {
            "id": str(self.id),
            "entity_id": str(self.entity_id),
            "entity_type": self.entity_type,
            "platform": self.platform.value,
            "date": self.date.isoformat(),
            "impressions": self.impressions,
            "reach": self.reach,
            "engagement_count": self.engagement_count,
            "likes": self.likes,
            "comments": self.comments,
            "shares": self.shares,
            "clicks": self.clicks,
            "video_views": self.video_views,
            "saves": self.saves,
            "engagement_rate": self.engagement_rate,
            "click_through_rate": self.click_through_rate,
            "conversion_count": self.conversion_count,
            "conversion_rate": self.conversion_rate,
            "revenue": self.revenue,
            "cost": self.cost,
            "roi": self.roi,
            "followers_gained": self.followers_gained,
            "followers_lost": self.followers_lost,
            "audience_demographics": self.audience_demographics,
            "top_performing_content": self.top_performing_content,
            "metadata": self.metadata,
        }


@dataclass
class Hashtag:
    """Hashtag tracking and performance."""

    id: UUID = field(default_factory=uuid4)
    tag: str = ""
    platform: PlatformType = PlatformType.FACEBOOK
    category: Optional[str] = None
    usage_count: int = 0
    reach: int = 0
    engagement: int = 0
    trend_score: float = 0.0  # 0-100
    is_trending: bool = False
    related_hashtags: List[str] = field(default_factory=list)
    saved_sets: List[str] = field(default_factory=list)
    performance_history: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert hashtag to dictionary."""
        return {
            "id": str(self.id),
            "tag": self.tag,
            "platform": self.platform.value,
            "category": self.category,
            "usage_count": self.usage_count,
            "reach": self.reach,
            "engagement": self.engagement,
            "trend_score": self.trend_score,
            "is_trending": self.is_trending,
            "related_hashtags": self.related_hashtags,
            "saved_sets": self.saved_sets,
            "performance_history": self.performance_history,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class Influencer:
    """Influencer profile and collaboration tracking."""

    id: UUID = field(default_factory=uuid4)
    platform: PlatformType = PlatformType.INSTAGRAM
    platform_user_id: str = ""
    username: str = ""
    display_name: str = ""
    category: Optional[str] = None
    followers_count: int = 0
    engagement_rate: float = 0.0
    average_likes: int = 0
    average_comments: int = 0
    verified: bool = False
    contact_email: Optional[str] = None
    collaboration_status: str = "prospect"  # prospect, contacted, negotiating, active, completed
    collaboration_notes: str = ""
    collaboration_cost: float = 0.0
    collaboration_roi: float = 0.0
    posts: List[UUID] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert influencer to dictionary."""
        return {
            "id": str(self.id),
            "platform": self.platform.value,
            "platform_user_id": self.platform_user_id,
            "username": self.username,
            "display_name": self.display_name,
            "category": self.category,
            "followers_count": self.followers_count,
            "engagement_rate": self.engagement_rate,
            "average_likes": self.average_likes,
            "average_comments": self.average_comments,
            "verified": self.verified,
            "contact_email": self.contact_email,
            "collaboration_status": self.collaboration_status,
            "collaboration_notes": self.collaboration_notes,
            "collaboration_cost": self.collaboration_cost,
            "collaboration_roi": self.collaboration_roi,
            "posts": [str(p) for p in self.posts],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class Advertisement:
    """Social media advertisement."""

    id: UUID = field(default_factory=uuid4)
    campaign_id: UUID = field(default_factory=uuid4)
    platform: PlatformType = PlatformType.FACEBOOK
    name: str = ""
    ad_type: str = "image"  # image, video, carousel, story
    status: AdStatus = AdStatus.DRAFT
    content: Dict[str, Any] = field(default_factory=dict)
    targeting: Dict[str, Any] = field(default_factory=dict)
    budget_daily: float = 0.0
    budget_total: float = 0.0
    spent: float = 0.0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    platform_ad_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert advertisement to dictionary."""
        return {
            "id": str(self.id),
            "campaign_id": str(self.campaign_id),
            "platform": self.platform.value,
            "name": self.name,
            "ad_type": self.ad_type,
            "status": self.status.value,
            "content": self.content,
            "targeting": self.targeting,
            "budget_daily": self.budget_daily,
            "budget_total": self.budget_total,
            "spent": self.spent,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "performance_metrics": self.performance_metrics,
            "platform_ad_id": self.platform_ad_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class ShortLink:
    """Shortened URL with tracking."""

    id: UUID = field(default_factory=uuid4)
    original_url: str = ""
    short_code: str = ""
    short_url: str = ""
    post_id: Optional[UUID] = None
    campaign_id: Optional[UUID] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None
    clicks: int = 0
    unique_clicks: int = 0
    click_details: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    is_active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert short link to dictionary."""
        return {
            "id": str(self.id),
            "original_url": self.original_url,
            "short_code": self.short_code,
            "short_url": self.short_url,
            "post_id": str(self.post_id) if self.post_id else None,
            "campaign_id": str(self.campaign_id) if self.campaign_id else None,
            "utm_source": self.utm_source,
            "utm_medium": self.utm_medium,
            "utm_campaign": self.utm_campaign,
            "utm_term": self.utm_term,
            "utm_content": self.utm_content,
            "clicks": self.clicks,
            "unique_clicks": self.unique_clicks,
            "click_details": self.click_details,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
        }
