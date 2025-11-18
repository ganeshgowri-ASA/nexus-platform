"""Contact API routes for marketing automation."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_db
from src.core.exceptions import NotFoundError, ValidationError
from src.services.marketing.contact_service import ContactService
from src.schemas.marketing.contact_schema import (
    ContactCreate, ContactUpdate, ContactResponse, ContactListResponse
)
from src.schemas.common import ApiResponse

router = APIRouter(prefix="/contacts", tags=["contacts"])

async def get_current_workspace_id() -> UUID:
    return UUID("00000000-0000-0000-0000-000000000001")

@router.post("/", response_model=ApiResponse[ContactResponse], status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact_data: ContactCreate,
    db: AsyncSession = Depends(get_async_db),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    """Create a new contact."""
    try:
        service = ContactService(db)
        contact = await service.create_contact(contact_data, workspace_id)
        return ApiResponse(success=True, data=ContactResponse.model_validate(contact))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

@router.get("/{contact_id}", response_model=ApiResponse[ContactResponse])
async def get_contact(
    contact_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    """Get contact by ID."""
    try:
        service = ContactService(db)
        contact = await service.get_contact(contact_id, workspace_id)
        return ApiResponse(success=True, data=ContactResponse.model_validate(contact))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.put("/{contact_id}", response_model=ApiResponse[ContactResponse])
async def update_contact(
    contact_id: UUID,
    contact_data: ContactUpdate,
    db: AsyncSession = Depends(get_async_db),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    """Update contact."""
    try:
        service = ContactService(db)
        contact = await service.update_contact(contact_id, workspace_id, contact_data)
        return ApiResponse(success=True, data=ContactResponse.model_validate(contact))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
