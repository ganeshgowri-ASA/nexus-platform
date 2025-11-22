"""FastAPI endpoints for experiment management."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from modules.ab_testing.models import Experiment
from modules.ab_testing.models.base import get_db
from modules.ab_testing.schemas.experiment import (
    ExperimentCreate,
    ExperimentResponse,
    ExperimentStats,
    ExperimentUpdate,
)
from modules.ab_testing.services.allocation import TrafficAllocator
from modules.ab_testing.services.experiment import ExperimentService

router = APIRouter(prefix="/experiments", tags=["Experiments"])


@router.post(
    "/",
    response_model=ExperimentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new experiment",
    description="Create a new A/B test or multivariate experiment",
)
async def create_experiment(
    data: ExperimentCreate,
    db: AsyncSession = Depends(get_db),
) -> ExperimentResponse:
    """
    Create a new experiment.

    Args:
        data: Experiment creation data
        db: Database session

    Returns:
        ExperimentResponse: Created experiment

    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/v1/experiments" \\
             -H "Content-Type: application/json" \\
             -d '{
                "name": "Homepage CTA Test",
                "description": "Testing different CTA button colors",
                "hypothesis": "Red button will increase conversions by 10%",
                "type": "ab",
                "target_sample_size": 1000,
                "confidence_level": 0.95
             }'
        ```
    """
    service = ExperimentService(db)
    experiment = await service.create_experiment(data)
    return ExperimentResponse.model_validate(experiment)


@router.get(
    "/",
    response_model=List[ExperimentResponse],
    summary="List all experiments",
    description="Get a list of all experiments with optional filtering",
)
async def list_experiments(
    status: Optional[str] = Query(None, description="Filter by experiment status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    db: AsyncSession = Depends(get_db),
) -> List[ExperimentResponse]:
    """
    List all experiments with optional filtering.

    Args:
        status: Optional status filter
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List[ExperimentResponse]: List of experiments
    """
    query = select(Experiment).offset(skip).limit(limit)

    if status:
        query = query.where(Experiment.status == status)

    result = await db.execute(query)
    experiments = result.scalars().all()

    return [ExperimentResponse.model_validate(exp) for exp in experiments]


@router.get(
    "/{experiment_id}",
    response_model=ExperimentResponse,
    summary="Get experiment by ID",
    description="Retrieve a specific experiment by its ID",
)
async def get_experiment(
    experiment_id: int,
    db: AsyncSession = Depends(get_db),
) -> ExperimentResponse:
    """
    Get experiment by ID.

    Args:
        experiment_id: ID of the experiment
        db: Database session

    Returns:
        ExperimentResponse: Experiment details

    Raises:
        HTTPException: If experiment not found
    """
    result = await db.execute(
        select(Experiment).where(Experiment.id == experiment_id)
    )
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found",
        )

    return ExperimentResponse.model_validate(experiment)


@router.patch(
    "/{experiment_id}",
    response_model=ExperimentResponse,
    summary="Update experiment",
    description="Update an existing experiment",
)
async def update_experiment(
    experiment_id: int,
    data: ExperimentUpdate,
    db: AsyncSession = Depends(get_db),
) -> ExperimentResponse:
    """
    Update an existing experiment.

    Args:
        experiment_id: ID of the experiment
        data: Update data
        db: Database session

    Returns:
        ExperimentResponse: Updated experiment

    Raises:
        HTTPException: If experiment not found
    """
    service = ExperimentService(db)
    experiment = await service.update_experiment(experiment_id, data)

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found",
        )

    return ExperimentResponse.model_validate(experiment)


@router.post(
    "/{experiment_id}/start",
    response_model=ExperimentResponse,
    summary="Start experiment",
    description="Start a draft experiment",
)
async def start_experiment(
    experiment_id: int,
    db: AsyncSession = Depends(get_db),
) -> ExperimentResponse:
    """
    Start an experiment.

    Args:
        experiment_id: ID of the experiment
        db: Database session

    Returns:
        ExperimentResponse: Started experiment

    Raises:
        HTTPException: If experiment cannot be started
    """
    service = ExperimentService(db)

    try:
        experiment = await service.start_experiment(experiment_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found",
        )

    return ExperimentResponse.model_validate(experiment)


@router.post(
    "/{experiment_id}/pause",
    response_model=ExperimentResponse,
    summary="Pause experiment",
    description="Pause a running experiment",
)
async def pause_experiment(
    experiment_id: int,
    db: AsyncSession = Depends(get_db),
) -> ExperimentResponse:
    """
    Pause a running experiment.

    Args:
        experiment_id: ID of the experiment
        db: Database session

    Returns:
        ExperimentResponse: Paused experiment

    Raises:
        HTTPException: If experiment cannot be paused
    """
    service = ExperimentService(db)

    try:
        experiment = await service.pause_experiment(experiment_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found",
        )

    return ExperimentResponse.model_validate(experiment)


@router.post(
    "/{experiment_id}/complete",
    response_model=ExperimentResponse,
    summary="Complete experiment",
    description="Mark an experiment as completed",
)
async def complete_experiment(
    experiment_id: int,
    db: AsyncSession = Depends(get_db),
) -> ExperimentResponse:
    """
    Complete an experiment.

    Args:
        experiment_id: ID of the experiment
        db: Database session

    Returns:
        ExperimentResponse: Completed experiment

    Raises:
        HTTPException: If experiment not found
    """
    service = ExperimentService(db)
    experiment = await service.complete_experiment(experiment_id)

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found",
        )

    return ExperimentResponse.model_validate(experiment)


@router.get(
    "/{experiment_id}/stats",
    response_model=ExperimentStats,
    summary="Get experiment statistics",
    description="Get statistical analysis and results for an experiment",
)
async def get_experiment_stats(
    experiment_id: int,
    db: AsyncSession = Depends(get_db),
) -> ExperimentStats:
    """
    Get statistical analysis for an experiment.

    Args:
        experiment_id: ID of the experiment
        db: Database session

    Returns:
        ExperimentStats: Statistical analysis results

    Raises:
        HTTPException: If experiment not found

    Example:
        ```bash
        curl -X GET "http://localhost:8000/api/v1/experiments/1/stats"
        ```
    """
    service = ExperimentService(db)
    stats = await service.get_experiment_stats(experiment_id)

    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found",
        )

    return stats


@router.post(
    "/{experiment_id}/check-winner",
    summary="Check for automatic winner",
    description="Check if a winner can be automatically determined",
)
async def check_auto_winner(
    experiment_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Check if a winner can be automatically determined.

    Args:
        experiment_id: ID of the experiment
        db: Database session

    Returns:
        dict: Winner information or status

    Raises:
        HTTPException: If experiment not found
    """
    service = ExperimentService(db)
    winner = await service.check_auto_winner(experiment_id)

    if winner:
        return {
            "has_winner": True,
            "winner_variant_id": winner.id,
            "winner_variant_name": winner.name,
        }
    else:
        return {
            "has_winner": False,
            "message": "No statistically significant winner yet",
        }


@router.post(
    "/{experiment_id}/assign",
    summary="Assign participant to variant",
    description="Assign a participant to a variant in the experiment",
)
async def assign_participant(
    experiment_id: int,
    participant_id: str = Query(..., description="Unique participant identifier"),
    properties: Optional[dict] = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Assign a participant to a variant.

    Args:
        experiment_id: ID of the experiment
        participant_id: Unique participant identifier
        properties: Optional participant properties for targeting
        db: Database session

    Returns:
        dict: Assignment information

    Raises:
        HTTPException: If assignment fails

    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/v1/experiments/1/assign?participant_id=user_123" \\
             -H "Content-Type: application/json" \\
             -d '{"properties": {"country": "US", "age": 25}}'
        ```
    """
    allocator = TrafficAllocator(db)

    try:
        variant = await allocator.assign_variant(
            experiment_id=experiment_id,
            participant_id=participant_id,
            properties=properties,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if not variant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Participant not eligible for experiment",
        )

    return {
        "experiment_id": experiment_id,
        "participant_id": participant_id,
        "variant_id": variant.id,
        "variant_name": variant.name,
        "config": variant.config,
    }
