"""
Exports API Routes
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from modules.analytics.api.dependencies import get_db_session
from modules.analytics.export.exporters import DataExporter
from modules.analytics.storage.repositories import ExportJobRepository
from shared.constants import ExportFormat

router = APIRouter()
export_job_repo = ExportJobRepository()
exporter = DataExporter()


@router.post("/")
def create_export(export_data: dict, db: Session = Depends(get_db_session)):
    """Create a new export job."""
    # Create export job record
    job = export_job_repo.create(db, **export_data)
    db.commit()

    # TODO: Trigger async export task
    return {"job_id": job.id, "status": "pending"}


@router.get("/{job_id}")
def get_export_status(job_id: str, db: Session = Depends(get_db_session)):
    """Get export job status."""
    job = export_job_repo.get_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")
    return job
