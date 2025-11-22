"""
Funnels API Routes
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from modules.analytics.api.dependencies import get_db_session
from modules.analytics.models.funnel import FunnelCreate, FunnelQuery
from modules.analytics.processing.funnel import FunnelEngine
from modules.analytics.storage.database import get_database
from modules.analytics.storage.repositories import FunnelRepository

router = APIRouter()
funnel_repo = FunnelRepository()


@router.post("/")
def create_funnel(funnel: FunnelCreate, db: Session = Depends(get_db_session)):
    """Create a new funnel."""
    from shared.utils import generate_uuid

    funnel_id = generate_uuid()
    funnel_data = {"id": funnel_id, **funnel.model_dump(exclude={"steps"})}
    created_funnel = funnel_repo.create(db, **funnel_data)

    # Create steps
    from modules.analytics.storage.repositories import BaseRepository
    from modules.analytics.storage.models import FunnelStepORM

    step_repo = BaseRepository(FunnelStepORM)
    for step in funnel.steps:
        step_data = {"funnel_id": funnel_id, **step.model_dump()}
        step_repo.create(db, **step_data)

    db.commit()
    return created_funnel


@router.get("/{funnel_id}")
def get_funnel(funnel_id: str, db: Session = Depends(get_db_session)):
    """Get funnel by ID."""
    funnel = funnel_repo.get_by_id(db, funnel_id)
    if not funnel:
        raise HTTPException(status_code=404, detail="Funnel not found")
    return funnel


@router.post("/{funnel_id}/analyze")
def analyze_funnel(funnel_id: str, query: FunnelQuery, db: Session = Depends(get_db_session)):
    """Analyze funnel conversion."""
    database = get_database()
    engine = FunnelEngine(database)

    from shared.utils import get_utc_now
    from datetime import timedelta

    end_date = query.end_date or get_utc_now()
    start_date = query.start_date or (end_date - timedelta(days=30))

    analysis = engine.analyze_funnel(funnel_id, start_date, end_date)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis failed")
    return analysis
