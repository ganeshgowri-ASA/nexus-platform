"""Lead generation API routes."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from config.database import get_db
from modules.lead_generation.lead_types import (
    Lead,
    LeadCreate,
    LeadUpdate,
    Form,
    FormCreate,
    LandingPage,
    LandingPageCreate,
)
from modules.lead_generation.capture import LeadCapture
from modules.lead_generation.forms import FormBuilder
from modules.lead_generation.landing_pages import LandingPageManager
from modules.lead_generation.scoring import LeadScoring
from modules.lead_generation.qualification import LeadQualification
from modules.lead_generation.analytics import LeadAnalytics
from shared.types import PaginatedResponse

router = APIRouter()


@router.post("/", response_model=Lead, status_code=status.HTTP_201_CREATED)
async def create_lead(lead_data: LeadCreate, db: Session = Depends(get_db)):
    """Create a new lead."""
    try:
        capture = LeadCapture(db)
        lead = await capture.capture_lead(lead_data)
        return lead
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{lead_id}", response_model=Lead)
async def get_lead(lead_id: str, db: Session = Depends(get_db)):
    """Get lead by ID."""
    from modules.lead_generation.models import Lead as LeadModel
    
    lead = db.query(LeadModel).filter(LeadModel.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return Lead.model_validate(lead)


@router.get("/", response_model=List[Lead])
async def list_leads(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List leads with pagination."""
    from modules.lead_generation.models import Lead as LeadModel
    
    query = db.query(LeadModel)
    if status:
        query = query.filter(LeadModel.status == status)
    
    leads = query.offset(skip).limit(limit).all()
    return [Lead.model_validate(lead) for lead in leads]


@router.post("/{lead_id}/score")
async def calculate_lead_score(lead_id: str, db: Session = Depends(get_db)):
    """Calculate lead score."""
    try:
        scorer = LeadScoring(db)
        score = await scorer.calculate_score(lead_id)
        return {"lead_id": lead_id, "score": score}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{lead_id}/qualify")
async def qualify_lead(lead_id: str, db: Session = Depends(get_db)):
    """Qualify lead."""
    try:
        qualifier = LeadQualification(db)
        result = await qualifier.qualify_lead(lead_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/forms/", response_model=Form, status_code=status.HTTP_201_CREATED)
async def create_form(form_data: FormCreate, db: Session = Depends(get_db)):
    """Create a new form."""
    try:
        builder = FormBuilder(db)
        form = await builder.create_form(form_data)
        return form
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/forms/", response_model=List[Form])
async def list_forms(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """List forms."""
    builder = FormBuilder(db)
    forms = await builder.list_forms(skip=skip, limit=limit)
    return forms


@router.post("/landing-pages/", response_model=LandingPage, status_code=status.HTTP_201_CREATED)
async def create_landing_page(page_data: LandingPageCreate, db: Session = Depends(get_db)):
    """Create a new landing page."""
    try:
        manager = LandingPageManager(db)
        page = await manager.create_landing_page(page_data)
        return page
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analytics/conversion-metrics")
async def get_conversion_metrics(db: Session = Depends(get_db)):
    """Get conversion metrics."""
    from datetime import datetime, timedelta
    
    analytics = LeadAnalytics(db)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    metrics = await analytics.get_conversion_metrics(start_date, end_date)
    return metrics
