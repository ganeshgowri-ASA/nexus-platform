"""ETL Executions API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from modules.etl.models import ETLExecution
from modules.etl.schemas import ETLExecutionResponse
from shared.database import get_db
from datetime import datetime, timedelta

router = APIRouter()


@router.get("/", response_model=List[ETLExecutionResponse])
def list_executions(
    skip: int = 0,
    limit: int = 100,
    pipeline_id: Optional[str] = None,
    status: Optional[str] = None,
    days: int = Query(7, description="Number of days to look back"),
    db: Session = Depends(get_db),
):
    """List execution history."""
    query = db.query(ETLExecution)

    # Filter by pipeline
    if pipeline_id:
        query = query.filter(ETLExecution.pipeline_id == pipeline_id)

    # Filter by status
    if status:
        query = query.filter(ETLExecution.status == status)

    # Filter by date
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    query = query.filter(ETLExecution.started_at >= cutoff_date)

    # Order by most recent first
    query = query.order_by(ETLExecution.started_at.desc())

    executions = query.offset(skip).limit(limit).all()
    return executions


@router.get("/{execution_id}", response_model=ETLExecutionResponse)
def get_execution(execution_id: str, db: Session = Depends(get_db)):
    """Get a specific execution."""
    execution = db.query(ETLExecution).filter(ETLExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution


@router.get("/pipeline/{pipeline_id}/latest", response_model=ETLExecutionResponse)
def get_latest_execution(pipeline_id: str, db: Session = Depends(get_db)):
    """Get the latest execution for a pipeline."""
    execution = (
        db.query(ETLExecution)
        .filter(ETLExecution.pipeline_id == pipeline_id)
        .order_by(ETLExecution.started_at.desc())
        .first()
    )
    if not execution:
        raise HTTPException(status_code=404, detail="No executions found for this pipeline")
    return execution


@router.get("/stats/summary")
def get_execution_stats(days: int = Query(7, description="Number of days to analyze"), db: Session = Depends(get_db)):
    """Get execution statistics."""
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    executions = db.query(ETLExecution).filter(ETLExecution.started_at >= cutoff_date).all()

    stats = {
        "total_executions": len(executions),
        "successful": len([e for e in executions if e.status == "completed"]),
        "failed": len([e for e in executions if e.status == "failed"]),
        "running": len([e for e in executions if e.status == "running"]),
        "total_records_processed": sum(e.records_loaded for e in executions if e.records_loaded),
        "avg_duration_seconds": (
            sum(e.duration_seconds for e in executions if e.duration_seconds) / len(executions)
            if executions
            else 0
        ),
    }

    return stats
