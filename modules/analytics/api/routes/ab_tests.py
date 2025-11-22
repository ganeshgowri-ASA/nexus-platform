"""
A/B Tests API Routes
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from modules.analytics.api.dependencies import get_db_session
from modules.analytics.models.ab_test import ABTestCreate, ABTestQuery
from modules.analytics.storage.repositories import ABTestRepository

router = APIRouter()
ab_test_repo = ABTestRepository()


@router.post("/")
def create_ab_test(ab_test: ABTestCreate, db: Session = Depends(get_db_session)):
    """Create a new A/B test."""
    return ab_test_repo.create(db, **ab_test.model_dump())


@router.get("/{test_id}")
def get_ab_test(test_id: str, db: Session = Depends(get_db_session)):
    """Get A/B test by ID."""
    test = ab_test_repo.get_by_id(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="A/B test not found")
    return test


@router.get("/")
def list_ab_tests(db: Session = Depends(get_db_session)):
    """List all A/B tests."""
    tests = ab_test_repo.get_all(db)
    return {"tests": tests}
