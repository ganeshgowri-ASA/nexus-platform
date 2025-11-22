"""Pipelines API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from modules.etl.models import Pipeline
from modules.etl.schemas import PipelineCreate, PipelineUpdate, PipelineResponse
from modules.etl.core.tasks import execute_pipeline_task
from shared.database import get_db

router = APIRouter()


@router.post("/", response_model=PipelineResponse, status_code=201)
def create_pipeline(pipeline: PipelineCreate, db: Session = Depends(get_db)):
    """Create a new pipeline."""
    # Check if name already exists
    existing = db.query(Pipeline).filter(Pipeline.name == pipeline.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Pipeline with this name already exists")

    db_pipeline = Pipeline(**pipeline.model_dump())
    db.add(db_pipeline)
    db.commit()
    db.refresh(db_pipeline)
    return db_pipeline


@router.get("/", response_model=List[PipelineResponse])
def list_pipelines(
    skip: int = 0, limit: int = 100, active_only: bool = False, db: Session = Depends(get_db)
):
    """List all pipelines."""
    query = db.query(Pipeline)
    if active_only:
        query = query.filter(Pipeline.is_active == True)

    pipelines = query.offset(skip).limit(limit).all()
    return pipelines


@router.get("/{pipeline_id}", response_model=PipelineResponse)
def get_pipeline(pipeline_id: str, db: Session = Depends(get_db)):
    """Get a specific pipeline."""
    pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline


@router.put("/{pipeline_id}", response_model=PipelineResponse)
def update_pipeline(pipeline_id: str, pipeline_update: PipelineUpdate, db: Session = Depends(get_db)):
    """Update a pipeline."""
    db_pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
    if not db_pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    update_data = pipeline_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_pipeline, field, value)

    db.commit()
    db.refresh(db_pipeline)
    return db_pipeline


@router.delete("/{pipeline_id}", status_code=204)
def delete_pipeline(pipeline_id: str, db: Session = Depends(get_db)):
    """Delete a pipeline."""
    db_pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
    if not db_pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    db.delete(db_pipeline)
    db.commit()
    return None


@router.post("/{pipeline_id}/execute")
def execute_pipeline(pipeline_id: str, db: Session = Depends(get_db)):
    """Execute a pipeline."""
    pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    if not pipeline.is_active:
        raise HTTPException(status_code=400, detail="Pipeline is not active")

    # Trigger async task
    task = execute_pipeline_task.delay(pipeline_id)
    return {"task_id": task.id, "status": "queued", "pipeline_id": pipeline_id}
