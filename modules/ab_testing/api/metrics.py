"""FastAPI endpoints for metrics tracking."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.ab_testing.models import Metric
from modules.ab_testing.models.base import get_db
from modules.ab_testing.schemas.metric import (
    MetricCreate,
    MetricEventCreate,
    MetricEventResponse,
    MetricResponse,
)
from modules.ab_testing.services.metrics import MetricsService

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.post(
    "/",
    response_model=MetricResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new metric",
    description="Create a new metric for an experiment",
)
async def create_metric(
    data: MetricCreate,
    db: AsyncSession = Depends(get_db),
) -> MetricResponse:
    """
    Create a new metric.

    Args:
        data: Metric creation data
        db: Database session

    Returns:
        MetricResponse: Created metric

    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/v1/metrics" \\
             -H "Content-Type: application/json" \\
             -d '{
                "experiment_id": 1,
                "name": "Conversion Rate",
                "type": "conversion",
                "is_primary": true
             }'
        ```
    """
    service = MetricsService(db)
    metric = await service.create_metric(data)
    return MetricResponse.model_validate(metric)


@router.get(
    "/experiment/{experiment_id}",
    response_model=List[MetricResponse],
    summary="List metrics for an experiment",
    description="Get all metrics for a specific experiment",
)
async def list_metrics(
    experiment_id: int,
    db: AsyncSession = Depends(get_db),
) -> List[MetricResponse]:
    """
    List all metrics for an experiment.

    Args:
        experiment_id: ID of the experiment
        db: Database session

    Returns:
        List[MetricResponse]: List of metrics
    """
    result = await db.execute(
        select(Metric).where(Metric.experiment_id == experiment_id)
    )
    metrics = result.scalars().all()

    return [MetricResponse.model_validate(m) for m in metrics]


@router.get(
    "/{metric_id}",
    response_model=MetricResponse,
    summary="Get metric by ID",
    description="Retrieve a specific metric by its ID",
)
async def get_metric(
    metric_id: int,
    db: AsyncSession = Depends(get_db),
) -> MetricResponse:
    """
    Get metric by ID.

    Args:
        metric_id: ID of the metric
        db: Database session

    Returns:
        MetricResponse: Metric details

    Raises:
        HTTPException: If metric not found
    """
    result = await db.execute(
        select(Metric).where(Metric.id == metric_id)
    )
    metric = result.scalar_one_or_none()

    if not metric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Metric {metric_id} not found",
        )

    return MetricResponse.model_validate(metric)


@router.post(
    "/events",
    response_model=MetricEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Track a metric event",
    description="Record a metric event for a participant",
)
async def track_event(
    data: MetricEventCreate,
    db: AsyncSession = Depends(get_db),
) -> MetricEventResponse:
    """
    Track a metric event.

    Args:
        data: Metric event data
        db: Database session

    Returns:
        MetricEventResponse: Created metric event

    Raises:
        HTTPException: If tracking fails

    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/v1/metrics/events" \\
             -H "Content-Type: application/json" \\
             -d '{
                "metric_id": 1,
                "participant_id": "user_123",
                "variant_id": 2,
                "value": 1.0,
                "properties": {"source": "email"}
             }'
        ```
    """
    service = MetricsService(db)

    try:
        event = await service.track_event(data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return MetricEventResponse.model_validate(event)


@router.get(
    "/{metric_id}/summary",
    summary="Get metric summary",
    description="Get summary statistics for a metric",
)
async def get_metric_summary(
    metric_id: int,
    variant_id: Optional[int] = Query(None, description="Filter by variant ID"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get summary statistics for a metric.

    Args:
        metric_id: ID of the metric
        variant_id: Optional variant ID filter
        db: Database session

    Returns:
        dict: Summary statistics

    Example:
        ```bash
        curl -X GET "http://localhost:8000/api/v1/metrics/1/summary?variant_id=2"
        ```
    """
    service = MetricsService(db)
    summary = await service.get_metric_summary(metric_id, variant_id)
    return summary
