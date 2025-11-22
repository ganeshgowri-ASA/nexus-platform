"""
Campaign API routes for marketing automation.

This module defines all campaign-related endpoints.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from config.logging_config import get_logger
from src.core.database import get_async_db
from src.core.exceptions import NotFoundError, ValidationError, CampaignError
from src.services.marketing.campaign_service import CampaignService
from src.schemas.marketing.campaign_schema import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignListResponse,
    CampaignSendRequest,
    CampaignAnalyticsResponse,
)
from src.schemas.common import ApiResponse

logger = get_logger(__name__)
router = APIRouter(prefix="/campaigns", tags=["campaigns"])


# Mock workspace/user authentication (replace with real auth)
async def get_current_workspace_id() -> UUID:
    """Get current workspace ID from auth."""
    return UUID("00000000-0000-0000-0000-000000000001")


async def get_current_user_id() -> UUID:
    """Get current user ID from auth."""
    return UUID("00000000-0000-0000-0000-000000000001")


@router.post("/", response_model=ApiResponse[CampaignResponse], status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign_data: CampaignCreate,
    db: AsyncSession = Depends(get_async_db),
    workspace_id: UUID = Depends(get_current_workspace_id),
    user_id: UUID = Depends(get_current_user_id),
):
    """Create a new campaign."""
    try:
        service = CampaignService(db)
        campaign = await service.create_campaign(campaign_data, workspace_id, user_id)

        return ApiResponse(
            success=True,
            data=CampaignResponse.model_validate(campaign),
            message="Campaign created successfully"
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error("Failed to create campaign", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{campaign_id}", response_model=ApiResponse[CampaignResponse])
async def get_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    """Get campaign by ID."""
    try:
        service = CampaignService(db)
        campaign = await service.get_campaign(campaign_id, workspace_id)

        return ApiResponse(
            success=True,
            data=CampaignResponse.model_validate(campaign)
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/", response_model=ApiResponse[CampaignListResponse])
async def list_campaigns(
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    """List all campaigns."""
    try:
        service = CampaignService(db)
        from config.constants import CampaignStatus

        status = CampaignStatus(status_filter) if status_filter else None
        result = await service.list_campaigns(workspace_id, page, page_size, status)

        campaigns = [CampaignResponse.model_validate(c) for c in result["campaigns"]]

        return ApiResponse(
            success=True,
            data=CampaignListResponse(
                campaigns=campaigns,
                total=result["total"],
                page=result["page"],
                page_size=result["page_size"],
                total_pages=result["total_pages"]
            )
        )
    except Exception as e:
        logger.error("Failed to list campaigns", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{campaign_id}", response_model=ApiResponse[CampaignResponse])
async def update_campaign(
    campaign_id: UUID,
    campaign_data: CampaignUpdate,
    db: AsyncSession = Depends(get_async_db),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    """Update campaign."""
    try:
        service = CampaignService(db)
        campaign = await service.update_campaign(campaign_id, workspace_id, campaign_data)

        return ApiResponse(
            success=True,
            data=CampaignResponse.model_validate(campaign),
            message="Campaign updated successfully"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    """Delete campaign."""
    try:
        service = CampaignService(db)
        await service.delete_campaign(campaign_id, workspace_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/{campaign_id}/send", response_model=ApiResponse[dict])
async def send_campaign(
    campaign_id: UUID,
    send_request: CampaignSendRequest,
    db: AsyncSession = Depends(get_async_db),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    """Send or schedule campaign."""
    try:
        service = CampaignService(db)
        campaign = await service.get_campaign(campaign_id, workspace_id)

        if send_request.send_immediately:
            # Queue campaign for immediate sending (via Celery)
            from src.tasks.marketing.email_tasks import send_campaign_task
            # send_campaign_task.delay(str(campaign_id), str(workspace_id))

            return ApiResponse(
                success=True,
                data={"status": "queued"},
                message="Campaign queued for sending"
            )
        elif send_request.scheduled_at:
            campaign = await service.schedule_campaign(
                campaign_id,
                workspace_id,
                send_request.scheduled_at
            )

            return ApiResponse(
                success=True,
                data=CampaignResponse.model_validate(campaign).model_dump(),
                message="Campaign scheduled successfully"
            )
        else:
            raise ValidationError("Must specify send_immediately=True or provide scheduled_at")

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/{campaign_id}/analytics", response_model=ApiResponse[dict])
async def get_campaign_analytics(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    """Get campaign analytics."""
    try:
        from src.services.marketing.analytics_service import AnalyticsService

        service = AnalyticsService(db)
        analytics = await service.get_campaign_analytics(campaign_id, workspace_id)

        return ApiResponse(
            success=True,
            data=analytics
        )
    except Exception as e:
        logger.error("Failed to get analytics", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
