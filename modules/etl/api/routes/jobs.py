"""ETL Jobs API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from modules.etl.models import ETLJob
from modules.etl.schemas import ETLJobCreate, ETLJobUpdate, ETLJobResponse
from modules.etl.core.tasks import calculate_next_run
from shared.database import get_db

router = APIRouter()


@router.post("/", response_model=ETLJobResponse, status_code=201)
def create_job(job: ETLJobCreate, db: Session = Depends(get_db)):
    """Create a new scheduled job."""
    db_job = ETLJob(**job.model_dump())

    # Calculate initial next_run
    db_job.next_run = calculate_next_run(db_job.schedule_expression, db_job.schedule_type)

    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


@router.get("/", response_model=List[ETLJobResponse])
def list_jobs(skip: int = 0, limit: int = 100, active_only: bool = False, db: Session = Depends(get_db)):
    """List all scheduled jobs."""
    query = db.query(ETLJob)
    if active_only:
        query = query.filter(ETLJob.is_active == True)

    jobs = query.offset(skip).limit(limit).all()
    return jobs


@router.get("/{job_id}", response_model=ETLJobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    """Get a specific job."""
    job = db.query(ETLJob).filter(ETLJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.put("/{job_id}", response_model=ETLJobResponse)
def update_job(job_id: str, job_update: ETLJobUpdate, db: Session = Depends(get_db)):
    """Update a job."""
    db_job = db.query(ETLJob).filter(ETLJob.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")

    update_data = job_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_job, field, value)

    # Recalculate next_run if schedule changed
    if "schedule_expression" in update_data or "schedule_type" in update_data:
        db_job.next_run = calculate_next_run(db_job.schedule_expression, db_job.schedule_type)

    db.commit()
    db.refresh(db_job)
    return db_job


@router.delete("/{job_id}", status_code=204)
def delete_job(job_id: str, db: Session = Depends(get_db)):
    """Delete a job."""
    db_job = db.query(ETLJob).filter(ETLJob.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")

    db.delete(db_job)
    db.commit()
    return None


@router.post("/{job_id}/pause")
def pause_job(job_id: str, db: Session = Depends(get_db)):
    """Pause a job."""
    db_job = db.query(ETLJob).filter(ETLJob.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")

    db_job.is_active = False
    db.commit()
    return {"message": "Job paused", "job_id": job_id}


@router.post("/{job_id}/resume")
def resume_job(job_id: str, db: Session = Depends(get_db)):
    """Resume a paused job."""
    db_job = db.query(ETLJob).filter(ETLJob.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")

    db_job.is_active = True
    db.commit()
    return {"message": "Job resumed", "job_id": job_id}
