"""
FastAPI router for Campaign Manager module.

This module defines all REST API endpoints for campaign management.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.campaign import CampaignStatus, ReportType
from app.schemas.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignListResponse,
    CampaignChannelCreate,
    CampaignChannelUpdate,
    CampaignChannelResponse,
    CampaignAssetCreate,
    CampaignAssetResponse,
    TeamMemberCreate,
    TeamMemberResponse,
    MilestoneCreate,
    MilestoneUpdate,
    MilestoneResponse,
    PerformanceMetricCreate,
    PerformanceMetricResponse,
    CampaignAnalytics,
    DashboardStats,
    OptimizationRequest,
)
from app.modules.campaign_manager.service import (
    CampaignService,
    ChannelService,
    AssetService,
    TeamService,
    MilestoneService,
    AnalyticsService,
)
from app.modules.campaign_manager.tasks import (
    generate_campaign_report,
    optimize_campaign_budget,
    calculate_campaign_performance,
)
from app.modules.campaign_manager.ai_service import AIService


router = APIRouter(prefix="/campaigns", tags=["Campaign Manager"])


# ==================== Campaign Endpoints ====================

@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
def create_campaign(
    campaign_data: CampaignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new campaign."""
    campaign = CampaignService.create_campaign(db, campaign_data, current_user.id)
    return campaign


@router.get("/", response_model=CampaignListResponse)
def list_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[CampaignStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all campaigns accessible to current user."""
    campaigns, total = CampaignService.list_campaigns(
        db, current_user, skip, limit, status
    )

    return {
        "campaigns": campaigns,
        "total": total,
        "page": skip // limit + 1,
        "page_size": limit
    }


@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get campaign by ID."""
    campaign = CampaignService.get_campaign(db, campaign_id, current_user)
    return campaign


@router.put("/{campaign_id}", response_model=CampaignResponse)
def update_campaign(
    campaign_id: int,
    campaign_data: CampaignUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update campaign."""
    campaign = CampaignService.update_campaign(
        db, campaign_id, campaign_data, current_user
    )
    return campaign


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete campaign."""
    CampaignService.delete_campaign(db, campaign_id, current_user)


@router.post("/{campaign_id}/status/{new_status}", response_model=CampaignResponse)
def update_campaign_status(
    campaign_id: int,
    new_status: CampaignStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update campaign status."""
    campaign = CampaignService.update_campaign_status(
        db, campaign_id, new_status, current_user
    )
    return campaign


# ==================== Channel Endpoints ====================

@router.post("/{campaign_id}/channels", response_model=CampaignChannelResponse)
def add_channel(
    campaign_id: int,
    channel_data: CampaignChannelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add channel to campaign."""
    channel = ChannelService.add_channel(db, campaign_id, channel_data, current_user)
    return channel


@router.get("/{campaign_id}/channels", response_model=List[CampaignChannelResponse])
def list_channels(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List campaign channels."""
    campaign = CampaignService.get_campaign(db, campaign_id, current_user)
    return campaign.channels


# ==================== Asset Endpoints ====================

@router.post("/{campaign_id}/assets", response_model=CampaignAssetResponse)
async def upload_asset(
    campaign_id: int,
    file: UploadFile = File(...),
    name: str = Query(...),
    asset_type: str = Query(...),
    description: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload campaign asset."""
    import os
    from datetime import datetime
    from app.config import settings

    # Validate file size
    file_size = 0
    file_content = await file.read()
    file_size = len(file_content)

    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds maximum allowed"
        )

    # Generate unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, "assets", filename)

    # Create directory if not exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Save file
    with open(file_path, "wb") as f:
        f.write(file_content)

    # Create asset record
    asset_data = CampaignAssetCreate(
        name=name,
        asset_type=asset_type,
        description=description,
        file_path=file_path
    )

    asset = AssetService.add_asset(db, campaign_id, asset_data, current_user)

    # Update file metadata
    asset.file_size = file_size
    asset.mime_type = file.content_type
    db.commit()
    db.refresh(asset)

    return asset


@router.get("/{campaign_id}/assets", response_model=List[CampaignAssetResponse])
def list_assets(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List campaign assets."""
    campaign = CampaignService.get_campaign(db, campaign_id, current_user)
    return campaign.assets


@router.post("/assets/{asset_id}/approve", response_model=CampaignAssetResponse)
def approve_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MANAGER))
):
    """Approve campaign asset."""
    asset = AssetService.approve_asset(db, asset_id, current_user)
    return asset


# ==================== Team Endpoints ====================

@router.post("/{campaign_id}/team", response_model=TeamMemberResponse)
def add_team_member(
    campaign_id: int,
    member_data: TeamMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add team member to campaign."""
    member = TeamService.add_team_member(db, campaign_id, member_data, current_user)
    return member


@router.get("/{campaign_id}/team", response_model=List[TeamMemberResponse])
def list_team_members(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List campaign team members."""
    campaign = CampaignService.get_campaign(db, campaign_id, current_user)
    return campaign.team_members


@router.delete("/{campaign_id}/team/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_team_member(
    campaign_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove team member from campaign."""
    TeamService.remove_team_member(db, campaign_id, user_id, current_user)


# ==================== Milestone Endpoints ====================

@router.post("/{campaign_id}/milestones", response_model=MilestoneResponse)
def create_milestone(
    campaign_id: int,
    milestone_data: MilestoneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create campaign milestone."""
    milestone = MilestoneService.create_milestone(
        db, campaign_id, milestone_data, current_user
    )
    return milestone


@router.get("/{campaign_id}/milestones", response_model=List[MilestoneResponse])
def list_milestones(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List campaign milestones."""
    campaign = CampaignService.get_campaign(db, campaign_id, current_user)
    return campaign.milestones


@router.put("/milestones/{milestone_id}", response_model=MilestoneResponse)
def update_milestone(
    milestone_id: int,
    milestone_data: MilestoneUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update milestone."""
    from app.models.campaign import Milestone

    milestone = db.query(Milestone).filter(Milestone.id == milestone_id).first()
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")

    update_data = milestone_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(milestone, field, value)

    db.commit()
    db.refresh(milestone)
    return milestone


# ==================== Analytics Endpoints ====================

@router.get("/{campaign_id}/analytics", response_model=CampaignAnalytics)
def get_campaign_analytics(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get campaign analytics."""
    campaign = CampaignService.get_campaign(db, campaign_id, current_user)
    metrics = AnalyticsService.calculate_campaign_roi(db, campaign_id)

    # Build channel performance
    channel_performance = []
    for channel in campaign.channels:
        channel_performance.append({
            "channel_name": channel.channel_name,
            "channel_type": channel.channel_type.value,
            "roi": channel.roi,
            "conversions": channel.conversions,
            "spent": channel.spent_budget,
        })

    # Get timeline data
    timeline_data = []
    for metric in campaign.performance_metrics:
        timeline_data.append({
            "date": metric.recorded_at.isoformat(),
            "impressions": metric.impressions,
            "clicks": metric.clicks,
            "conversions": metric.conversions,
            "roi": metric.roi,
        })

    return {
        "campaign_id": campaign.id,
        "campaign_name": campaign.name,
        "total_impressions": metrics["total_impressions"],
        "total_clicks": metrics["total_clicks"],
        "total_conversions": metrics["total_conversions"],
        "total_revenue": metrics["total_revenue"],
        "total_cost": metrics["total_cost"],
        "overall_roi": metrics["roi"],
        "overall_ctr": metrics["ctr"],
        "overall_conversion_rate": metrics["conversion_rate"],
        "channel_performance": channel_performance,
        "timeline_data": timeline_data,
    }


@router.get("/dashboard/stats", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dashboard statistics."""
    stats = AnalyticsService.get_dashboard_stats(db, current_user)

    # Get recent campaigns
    recent_campaigns, _ = CampaignService.list_campaigns(
        db, current_user, skip=0, limit=5
    )

    return {
        **stats,
        "total_conversions": 0,  # Would calculate from metrics
        "total_revenue": 0.0,  # Would calculate from channels
        "recent_campaigns": recent_campaigns,
    }


# ==================== AI & Optimization Endpoints ====================

@router.post("/{campaign_id}/optimize")
def optimize_campaign(
    campaign_id: int,
    request: OptimizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Request AI optimization for campaign."""
    campaign = CampaignService.get_campaign(db, campaign_id, current_user)

    # Trigger async optimization task
    task = optimize_campaign_budget.delay(campaign_id)

    return {
        "message": "Optimization in progress",
        "task_id": task.id,
        "campaign_id": campaign_id
    }


@router.post("/{campaign_id}/reports/generate")
def generate_report(
    campaign_id: int,
    report_type: ReportType = ReportType.WEEKLY,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate campaign report."""
    campaign = CampaignService.get_campaign(db, campaign_id, current_user)

    # Trigger async report generation
    from datetime import date, timedelta

    period_end = date.today()
    period_start = period_end - timedelta(days=7)

    task = generate_campaign_report.delay(
        campaign_id=campaign_id,
        report_type=report_type.value,
        period_start=period_start.isoformat(),
        period_end=period_end.isoformat(),
        user_id=current_user.id
    )

    return {
        "message": "Report generation in progress",
        "task_id": task.id,
        "campaign_id": campaign_id
    }


@router.post("/{campaign_id}/calculate-performance")
def calculate_performance(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger performance calculation."""
    campaign = CampaignService.get_campaign(db, campaign_id, current_user)

    task = calculate_campaign_performance.delay(campaign_id)

    return {
        "message": "Performance calculation in progress",
        "task_id": task.id,
        "campaign_id": campaign_id
    }
