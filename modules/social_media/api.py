"""
Social Media Module - FastAPI Endpoints.

This module provides REST API endpoints for all social media management features.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel

from .composer import PostComposer
from .scheduling import PostScheduler
from .analytics import AnalyticsManager
from .engagement import EngagementManager
from .campaigns import CampaignManager
from .hashtags import HashtagManager
from .ai_assistant import AIContentAssistant
from .links import LinkManager
from .approvals import ApprovalWorkflow
from .social_types import PlatformType, PostStatus, CampaignStatus

router = APIRouter(prefix="/api/social", tags=["social_media"])

# Initialize managers (in production, use dependency injection)
composer = PostComposer()
scheduler = PostScheduler()
analytics_manager = AnalyticsManager()
engagement_manager = EngagementManager()
campaign_manager = CampaignManager()
hashtag_manager = HashtagManager()
ai_assistant = AIContentAssistant()
link_manager = LinkManager()
approval_workflow = ApprovalWorkflow()


# Pydantic models for API requests/responses
class PostCreateRequest(BaseModel):
    title: str
    platforms: List[str]
    base_content: str
    campaign_id: Optional[str] = None


class PostResponse(BaseModel):
    post_id: str
    title: str
    status: str
    platforms: List[str]
    created_at: str


@router.post("/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(request: PostCreateRequest):
    """Create a new social media post."""
    try:
        platforms = [PlatformType(p) for p in request.platforms]
        post = composer.create_post(
            title=request.title,
            platforms=platforms,
            author_id=UUID("00000000-0000-0000-0000-000000000000"),  # Replace with auth
            base_content=request.base_content,
            campaign_id=UUID(request.campaign_id) if request.campaign_id else None,
        )

        return PostResponse(
            post_id=str(post.id),
            title=post.title,
            status=post.status.value,
            platforms=[p.value for p in post.platforms],
            created_at=post.created_at.isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/posts/{post_id}")
async def get_post(post_id: str):
    """Get post by ID."""
    try:
        post = composer.get_post(UUID(post_id))
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        return post.to_dict()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid post ID")


@router.get("/posts")
async def list_posts(status: Optional[str] = None, limit: int = 50):
    """List all posts."""
    posts = composer.list_drafts()
    if status:
        posts = [p for p in posts if p.status.value == status]
    return {"posts": [p.to_dict() for p in posts[:limit]]}


@router.post("/posts/{post_id}/schedule")
async def schedule_post(post_id: str, scheduled_time: str, timezone: str = "UTC"):
    """Schedule a post for publishing."""
    try:
        post = composer.get_post(UUID(post_id))
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        scheduled_dt = datetime.fromisoformat(scheduled_time)
        scheduled_post = scheduler.schedule_post(post, scheduled_dt, timezone)

        return {
            "post_id": str(scheduled_post.id),
            "scheduled_time": scheduled_post.scheduled_time.isoformat(),
            "status": scheduled_post.status.value,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analytics/posts/{post_id}")
async def get_post_analytics(post_id: str, platform: str):
    """Get analytics for a post."""
    try:
        # Implementation would fetch from analytics manager
        return {
            "post_id": post_id,
            "platform": platform,
            "impressions": 1000,
            "engagement": 120,
            "reach": 850,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/campaigns")
async def list_campaigns(status: Optional[str] = None):
    """List all campaigns."""
    try:
        status_filter = CampaignStatus(status) if status else None
        campaigns = campaign_manager.list_campaigns(status=status_filter)
        return {"campaigns": [c.to_dict() for c in campaigns]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/hashtags/trending")
async def get_trending_hashtags(platform: str, limit: int = 20):
    """Get trending hashtags for a platform."""
    try:
        platform_type = PlatformType(platform)
        trending = hashtag_manager.get_trending_hashtags(platform_type, limit=limit)
        return {"hashtags": [h.to_dict() for h in trending]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/ai/generate-caption")
async def generate_caption(
    topic: str,
    platform: str,
    tone: str = "professional",
    include_hashtags: bool = True,
):
    """Generate AI caption for a post."""
    try:
        platform_type = PlatformType(platform)
        caption = ai_assistant.generate_caption(
            topic=topic,
            platform=platform_type,
            tone=tone,
            include_hashtags=include_hashtags,
        )
        return {"caption": caption}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/engagement/inbox")
async def get_inbox(
    platform: Optional[str] = None,
    unread: Optional[bool] = None,
    limit: int = 50,
):
    """Get engagement inbox."""
    try:
        platform_filter = PlatformType(platform) if platform else None
        engagements = engagement_manager.get_engagements(
            platform=platform_filter,
            is_read=not unread if unread is not None else None,
            limit=limit,
        )
        return {"engagements": [e.to_dict() for e in engagements]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "social_media_manager"}
