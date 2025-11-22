"""Automation API routes for marketing automation."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_db
from src.core.exceptions import NotFoundError, ValidationError, AutomationError
from src.services.marketing.automation_service import AutomationService
from src.schemas.marketing.automation_schema import (
    AutomationCreate, AutomationUpdate, AutomationResponse, AutomationTriggerRequest
)
from src.schemas.common import ApiResponse

router = APIRouter(prefix="/automations", tags=["automations"])

async def get_current_workspace_id() -> UUID:
    return UUID("00000000-0000-0000-0000-000000000001")

async def get_current_user_id() -> UUID:
    return UUID("00000000-0000-0000-0000-000000000001")

@router.post("/", response_model=ApiResponse[AutomationResponse], status_code=status.HTTP_201_CREATED)
async def create_automation(
    automation_data: AutomationCreate,
    db: AsyncSession = Depends(get_async_db),
    workspace_id: UUID = Depends(get_current_workspace_id),
    user_id: UUID = Depends(get_current_user_id),
):
    """Create a new automation workflow."""
    try:
        service = AutomationService(db)
        automation = await service.create_automation(automation_data, workspace_id, user_id)
        return ApiResponse(success=True, data=AutomationResponse.model_validate(automation))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

@router.get("/{automation_id}", response_model=ApiResponse[AutomationResponse])
async def get_automation(
    automation_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    """Get automation by ID."""
    try:
        service = AutomationService(db)
        automation = await service.get_automation(automation_id, workspace_id)
        return ApiResponse(success=True, data=AutomationResponse.model_validate(automation))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/{automation_id}/activate", response_model=ApiResponse[AutomationResponse])
async def activate_automation(
    automation_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    """Activate automation."""
    try:
        service = AutomationService(db)
        automation = await service.activate_automation(automation_id, workspace_id)
        return ApiResponse(success=True, data=AutomationResponse.model_validate(automation))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/{automation_id}/pause", response_model=ApiResponse[AutomationResponse])
async def pause_automation(
    automation_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    """Pause automation."""
    try:
        service = AutomationService(db)
        automation = await service.pause_automation(automation_id, workspace_id)
        return ApiResponse(success=True, data=AutomationResponse.model_validate(automation))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
