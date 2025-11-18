"""
Metrics API Routes
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from modules.analytics.api.dependencies import get_db_session
from modules.analytics.models.metric import MetricCreate, MetricQuery, Metric
from modules.analytics.storage.repositories import MetricRepository

router = APIRouter()
metric_repo = MetricRepository()


@router.post("/")
def create_metric(metric: MetricCreate, db: Session = Depends(get_db_session)):
    """Create a new metric."""
    return metric_repo.create(db, **metric.model_dump())


@router.get("/{metric_id}", response_model=Metric)
def get_metric(metric_id: str, db: Session = Depends(get_db_session)):
    """Get metric by ID."""
    metric = metric_repo.get_by_id(db, metric_id)
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")
    return metric


@router.post("/query")
def query_metrics(query: MetricQuery, db: Session = Depends(get_db_session)):
    """Query metrics with filters."""
    metrics = metric_repo.get_by_filters(
        db,
        names=query.names,
        metric_types=[mt.value for mt in query.metric_types] if query.metric_types else None,
        module=query.module,
        period=query.period.value if query.period else None,
        start_date=query.start_date,
        end_date=query.end_date,
        skip=(query.page - 1) * query.page_size,
        limit=query.page_size
    )
    return {"metrics": metrics}
