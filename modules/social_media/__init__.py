"""
NEXUS Platform - Social Media Manager Module.

A comprehensive social media management system with multi-platform publishing,
scheduling, analytics, engagement tracking, and AI-powered content assistance.

Supported Platforms:
- Facebook
- Twitter/X
- Instagram
- LinkedIn
- TikTok
- YouTube
- Pinterest

Key Features:
- Multi-platform post composer with platform-specific customization
- Smart scheduling with optimal time suggestions
- Visual calendar with drag-and-drop scheduling
- Media library with asset management
- Unified inbox for all engagements
- Social listening and brand monitoring
- Cross-platform analytics and reporting
- Hashtag intelligence
- AI-powered content suggestions
- Campaign management
- Influencer discovery and tracking
- Social advertising management
- Link tracking and UTM management
"""

__version__ = "1.0.0"
__author__ = "NEXUS Platform Team"

from .ai_assistant import AIContentAssistant
from .analytics import AnalyticsManager
from .approvals import ApprovalWorkflow
from .campaigns import CampaignManager
from .composer import PostComposer
from .engagement import EngagementManager
from .hashtags import HashtagManager
from .influencer import InfluencerManager
from .links import LinkManager
from .monitoring import SocialMonitor
from .platforms import (
    BasePlatform,
    FacebookPlatform,
    InstagramPlatform,
    LinkedInPlatform,
    PinterestPlatform,
    PlatformFactory,
    TikTokPlatform,
    TwitterPlatform,
    YouTubePlatform,
)
from .reporting import ReportGenerator
from .scheduling import PostScheduler
from .social_types import (
    Advertisement,
    AdStatus,
    Analytics,
    ApprovalStatus,
    Campaign,
    CampaignStatus,
    Engagement,
    EngagementType,
    Hashtag,
    Influencer,
    Media,
    MediaType,
    PlatformCredentials,
    PlatformType,
    Post,
    PostContent,
    PostStatus,
    Profile,
    Schedule,
    SentimentType,
    ShortLink,
)

__all__ = [
    # Version
    "__version__",
    "__author__",
    # Types
    "Advertisement",
    "AdStatus",
    "Analytics",
    "ApprovalStatus",
    "Campaign",
    "CampaignStatus",
    "Engagement",
    "EngagementType",
    "Hashtag",
    "Influencer",
    "Media",
    "MediaType",
    "PlatformCredentials",
    "PlatformType",
    "Post",
    "PostContent",
    "PostStatus",
    "Profile",
    "Schedule",
    "SentimentType",
    "ShortLink",
    # Platforms
    "BasePlatform",
    "FacebookPlatform",
    "InstagramPlatform",
    "LinkedInPlatform",
    "PinterestPlatform",
    "PlatformFactory",
    "TikTokPlatform",
    "TwitterPlatform",
    "YouTubePlatform",
    # Core Managers
    "AIContentAssistant",
    "AnalyticsManager",
    "ApprovalWorkflow",
    "CampaignManager",
    "PostComposer",
    "EngagementManager",
    "HashtagManager",
    "InfluencerManager",
    "LinkManager",
    "ReportGenerator",
    "SocialMonitor",
    "PostScheduler",
]
