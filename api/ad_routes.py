"""Advertising API routes."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from config.database import get_db
from modules.advertising.ad_types import (
    Campaign,
    CampaignCreate,
    CampaignStatus,
    Creative,
    CreativeCreate,
)
from modules.advertising.campaigns import CampaignManager
from modules.advertising.creatives import CreativeManager
from modules.advertising.analytics import AdAnalytics
from modules.advertising.reporting import AdReporting

router = APIRouter()


@router.post("/campaigns/", response_model=Campaign, status_code=status.HTTP_201_CREATED)
async def create_campaign(campaign_data: CampaignCreate, db: Session = Depends(get_db)):
    """Create a new advertising campaign."""
    try:
        manager = CampaignManager(db)
        campaign = await manager.create_campaign(campaign_data)
        return campaign
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/campaigns/{campaign_id}", response_model=Campaign)
async def get_campaign(campaign_id: str, db: Session = Depends(get_db)):
    """Get campaign by ID."""
    try:
        manager = CampaignManager(db)
        campaign = await manager.get_campaign(campaign_id)
        return campaign
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/campaigns/", response_model=List[Campaign])
async def list_campaigns(
    status: Optional[str] = None,
    platform: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """List campaigns with filters."""
    manager = CampaignManager(db)
    status_enum = CampaignStatus(status) if status else None
    campaigns = await manager.list_campaigns(
        status=status_enum,
        platform=platform,
        skip=skip,
        limit=limit
    )
    return campaigns


@router.patch("/campaigns/{campaign_id}/status")
async def update_campaign_status(
    campaign_id: str,
    status: str,
    db: Session = Depends(get_db)
):
    """Update campaign status."""
    try:
        manager = CampaignManager(db)
        campaign = await manager.update_campaign_status(campaign_id, CampaignStatus(status))
        return campaign
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/creatives/", response_model=Creative, status_code=status.HTTP_201_CREATED)
async def create_creative(creative_data: CreativeCreate, db: Session = Depends(get_db)):
    """Create a new creative."""
    try:
        manager = CreativeManager(db)
        creative = await manager.create_creative(creative_data)
        return creative
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/creatives/", response_model=List[Creative])
async def list_creatives(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """List creatives."""
    manager = CreativeManager(db)
    creatives = await manager.list_creatives(skip=skip, limit=limit)
    return creatives


@router.get("/analytics/campaign/{campaign_id}")
async def get_campaign_analytics(campaign_id: str, db: Session = Depends(get_db)):
    """Get campaign analytics."""
    from datetime import datetime, timedelta
    
    analytics = AdAnalytics(db)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    metrics = await analytics.get_campaign_metrics(campaign_id, start_date, end_date)
    return metrics


@router.get("/analytics/cross-platform")
async def get_cross_platform_analytics(db: Session = Depends(get_db)):
    """Get cross-platform analytics."""
    analytics = AdAnalytics(db)
    metrics = await analytics.get_cross_platform_metrics()
    return metrics


@router.get("/reports/roi")
async def get_roi_report(db: Session = Depends(get_db)):
    """Get ROI report."""
    reporting = AdReporting(db)
    report = await reporting.generate_roi_report()
    return report
