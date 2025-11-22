"""
Dashboards API Routes
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from modules.analytics.api.dependencies import get_db_session
from modules.analytics.storage.repositories import DashboardRepository

router = APIRouter()
dashboard_repo = DashboardRepository()


@router.post("/")
def create_dashboard(dashboard_data: dict, db: Session = Depends(get_db_session)):
    """Create a new dashboard."""
    return dashboard_repo.create(db, **dashboard_data)


@router.get("/{dashboard_id}")
def get_dashboard(dashboard_id: str, db: Session = Depends(get_db_session)):
    """Get dashboard by ID."""
    dashboard = dashboard_repo.get_by_id(db, dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


@router.get("/")
def list_dashboards(db: Session = Depends(get_db_session)):
    """List all dashboards."""
    dashboards = dashboard_repo.get_all(db)
    return {"dashboards": dashboards}
