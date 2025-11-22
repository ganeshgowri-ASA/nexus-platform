"""
Lead management API router.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from modules.lead_generation.models import LeadStatus
from modules.lead_generation.schemas import (
    LeadCreate, LeadUpdate, LeadResponse, LeadActivityResponse,
    LeadEnrichRequest, LeadScoreRequest
)
from modules.lead_generation.services.lead_service import LeadService
from modules.lead_generation.services.enrichment_service import EnrichmentService
from modules.lead_generation.services.scoring_service import ScoringService

router = APIRouter()


@router.post("/", response_model=LeadResponse, status_code=201)
async def create_lead(
    lead_data: LeadCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new lead.

    Args:
        lead_data: Lead creation data
        db: Database session

    Returns:
        Created lead
    """
    lead = await LeadService.create_lead(db, lead_data)

    # Trigger async validation
    await LeadService.validate_email(db, lead.id)
    if lead.phone:
        await LeadService.validate_phone(db, lead.id)

    # Increment form submissions if from a form
    if lead.form_id:
        from modules.lead_generation.services.form_service import FormService
        await FormService.increment_submissions(db, lead.form_id)

    return lead


@router.get("/", response_model=List[LeadResponse])
async def list_leads(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[LeadStatus] = None,
    is_qualified: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List leads with optional filtering.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Filter by status
        is_qualified: Filter by qualification status
        db: Database session

    Returns:
        List of leads
    """
    leads = await LeadService.list_leads(db, skip, limit, status, is_qualified)
    return leads


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a lead by ID.

    Args:
        lead_id: Lead ID
        db: Database session

    Returns:
        Lead details
    """
    lead = await LeadService.get_lead(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: UUID,
    lead_data: LeadUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a lead.

    Args:
        lead_id: Lead ID
        lead_data: Lead update data
        db: Database session

    Returns:
        Updated lead
    """
    lead = await LeadService.update_lead(db, lead_id, lead_data)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Add activity for update
    await LeadService.add_activity(
        db, lead_id, "lead_updated", "Lead information updated"
    )

    return lead


@router.get("/{lead_id}/activities", response_model=List[LeadActivityResponse])
async def get_lead_activities(
    lead_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """
    Get lead activities.

    Args:
        lead_id: Lead ID
        limit: Maximum number of activities
        db: Database session

    Returns:
        List of activities
    """
    # Verify lead exists
    lead = await LeadService.get_lead(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    activities = await LeadService.get_lead_activities(db, lead_id, limit)
    return activities


@router.post("/{lead_id}/enrich", response_model=LeadResponse)
async def enrich_lead(
    lead_id: UUID,
    request: LeadEnrichRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Enrich lead data using external APIs.

    Args:
        lead_id: Lead ID
        request: Enrichment request
        db: Database session

    Returns:
        Enriched lead
    """
    lead = await EnrichmentService.enrich_lead(
        db,
        request.lead_id,
        request.provider
    )
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Add activity
    await LeadService.add_activity(
        db, lead_id, "lead_enriched",
        f"Lead enriched using {request.provider}"
    )

    return lead


@router.post("/{lead_id}/score", response_model=LeadResponse)
async def score_lead(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate lead score.

    Args:
        lead_id: Lead ID
        db: Database session

    Returns:
        Lead with updated score
    """
    score = await ScoringService.calculate_lead_score(db, lead_id)

    lead = await LeadService.get_lead(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Add activity
    await LeadService.add_activity(
        db, lead_id, "lead_scored",
        f"Lead scored: {score} ({lead.grade})"
    )

    return lead
