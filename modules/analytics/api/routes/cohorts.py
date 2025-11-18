"""
Cohorts API Routes
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from modules.analytics.api.dependencies import get_db_session
from modules.analytics.models.cohort import CohortCreate, CohortQuery
from modules.analytics.processing.cohort import CohortEngine
from modules.analytics.storage.database import get_database
from modules.analytics.storage.repositories import CohortRepository

router = APIRouter()
cohort_repo = CohortRepository()


@router.post("/")
def create_cohort(cohort: CohortCreate, db: Session = Depends(get_db_session)):
    """Create a new cohort."""
    return cohort_repo.create(db, **cohort.model_dump())


@router.get("/{cohort_id}")
def get_cohort(cohort_id: str, db: Session = Depends(get_db_session)):
    """Get cohort by ID."""
    cohort = cohort_repo.get_by_id(db, cohort_id)
    if not cohort:
        raise HTTPException(status_code=404, detail="Cohort not found")
    return cohort


@router.post("/analyze")
def analyze_cohort(query: CohortQuery):
    """Analyze cohort retention."""
    database = get_database()
    engine = CohortEngine(database)

    from shared.utils import get_utc_now
    from datetime import timedelta

    cohort_date = query.start_date or (get_utc_now() - timedelta(days=30))
    analysis = engine.analyze_retention_cohort(cohort_date, periods=query.periods)

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis failed")
    return analysis
