"""
Campaign management API router.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from modules.advertising.models import CampaignStatus
from modules.advertising.schemas import CampaignCreate, CampaignUpdate, CampaignResponse
from modules.advertising.services.campaign_service import CampaignService
from modules.advertising.services.google_ads_service import GoogleAdsService

router = APIRouter()


@router.post("/", response_model=CampaignResponse, status_code=201)
async def create_campaign(
    campaign_data: CampaignCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new campaign."""
    campaign = await CampaignService.create_campaign(db, campaign_data)

    # Sync to ad platform if applicable
    if campaign.platform.value == "google_ads":
        google_ads_service = GoogleAdsService()
        await google_ads_service.create_campaign(db, campaign)

    return campaign


@router.get("/", response_model=List[CampaignResponse])
async def list_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[CampaignStatus] = None,
    platform: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List campaigns with optional filtering."""
    campaigns = await CampaignService.list_campaigns(
        db, skip, limit, status, platform
    )
    return campaigns


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a campaign by ID."""
    campaign = await CampaignService.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: UUID,
    campaign_data: CampaignUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a campaign."""
    campaign = await CampaignService.update_campaign(db, campaign_id, campaign_data)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.post("/{campaign_id}/pause", response_model=CampaignResponse)
async def pause_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Pause a campaign."""
    campaign = await CampaignService.pause_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Sync to ad platform
    if campaign.platform.value == "google_ads" and campaign.platform_campaign_id:
        google_ads_service = GoogleAdsService()
        await google_ads_service.pause_campaign(campaign.platform_campaign_id)

    return campaign


@router.post("/{campaign_id}/activate", response_model=CampaignResponse)
async def activate_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Activate a campaign."""
    campaign = await CampaignService.activate_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Sync to ad platform
    if campaign.platform.value == "google_ads" and campaign.platform_campaign_id:
        google_ads_service = GoogleAdsService()
        await google_ads_service.activate_campaign(campaign.platform_campaign_id)

    return campaign


@router.post("/{campaign_id}/sync")
async def sync_campaign_metrics(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Sync campaign metrics from ad platform."""
    campaign = await CampaignService.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.platform.value == "google_ads":
        google_ads_service = GoogleAdsService()
        success = await google_ads_service.sync_campaign_metrics(db, campaign)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to sync metrics")

    return {"status": "success", "message": "Metrics synced successfully"}
