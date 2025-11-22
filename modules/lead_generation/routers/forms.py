"""
Form management API router.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from modules.lead_generation.schemas import FormCreate, FormUpdate, FormResponse
from modules.lead_generation.services.form_service import FormService

router = APIRouter()


@router.post("/", response_model=FormResponse, status_code=201)
async def create_form(
    form_data: FormCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new form."""
    form = await FormService.create_form(db, form_data)
    return form


@router.get("/", response_model=List[FormResponse])
async def list_forms(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """List forms with optional filtering."""
    forms = await FormService.list_forms(db, skip, limit, is_active)
    return forms


@router.get("/{form_id}", response_model=FormResponse)
async def get_form(
    form_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a form by ID."""
    form = await FormService.get_form(db, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    # Increment views
    await FormService.increment_views(db, form_id)

    return form


@router.patch("/{form_id}", response_model=FormResponse)
async def update_form(
    form_id: UUID,
    form_data: FormUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a form."""
    form = await FormService.update_form(db, form_id, form_data)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    return form


@router.delete("/{form_id}", status_code=204)
async def delete_form(
    form_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a form."""
    deleted = await FormService.delete_form(db, form_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Form not found")
