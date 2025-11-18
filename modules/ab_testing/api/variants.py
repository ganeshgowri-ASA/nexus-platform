"""FastAPI endpoints for variant management."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.ab_testing.models import Variant
from modules.ab_testing.models.base import get_db
from modules.ab_testing.schemas.variant import (
    VariantCreate,
    VariantResponse,
    VariantUpdate,
)

router = APIRouter(prefix="/variants", tags=["Variants"])


@router.post(
    "/",
    response_model=VariantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new variant",
    description="Create a new variant for an experiment",
)
async def create_variant(
    data: VariantCreate,
    db: AsyncSession = Depends(get_db),
) -> VariantResponse:
    """
    Create a new variant.

    Args:
        data: Variant creation data
        db: Database session

    Returns:
        VariantResponse: Created variant

    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/v1/variants" \\
             -H "Content-Type: application/json" \\
             -d '{
                "experiment_id": 1,
                "name": "Control",
                "description": "Original homepage",
                "is_control": true,
                "traffic_weight": 1.0,
                "config": {"button_color": "blue"}
             }'
        ```
    """
    variant = Variant(
        experiment_id=data.experiment_id,
        name=data.name,
        description=data.description,
        is_control=data.is_control,
        traffic_weight=data.traffic_weight,
        config=data.config,
    )

    db.add(variant)
    await db.commit()
    await db.refresh(variant)

    return VariantResponse.model_validate(variant)


@router.get(
    "/experiment/{experiment_id}",
    response_model=List[VariantResponse],
    summary="List variants for an experiment",
    description="Get all variants for a specific experiment",
)
async def list_variants(
    experiment_id: int,
    db: AsyncSession = Depends(get_db),
) -> List[VariantResponse]:
    """
    List all variants for an experiment.

    Args:
        experiment_id: ID of the experiment
        db: Database session

    Returns:
        List[VariantResponse]: List of variants
    """
    result = await db.execute(
        select(Variant).where(Variant.experiment_id == experiment_id)
    )
    variants = result.scalars().all()

    return [VariantResponse.model_validate(v) for v in variants]


@router.get(
    "/{variant_id}",
    response_model=VariantResponse,
    summary="Get variant by ID",
    description="Retrieve a specific variant by its ID",
)
async def get_variant(
    variant_id: int,
    db: AsyncSession = Depends(get_db),
) -> VariantResponse:
    """
    Get variant by ID.

    Args:
        variant_id: ID of the variant
        db: Database session

    Returns:
        VariantResponse: Variant details

    Raises:
        HTTPException: If variant not found
    """
    result = await db.execute(
        select(Variant).where(Variant.id == variant_id)
    )
    variant = result.scalar_one_or_none()

    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Variant {variant_id} not found",
        )

    return VariantResponse.model_validate(variant)


@router.patch(
    "/{variant_id}",
    response_model=VariantResponse,
    summary="Update variant",
    description="Update an existing variant",
)
async def update_variant(
    variant_id: int,
    data: VariantUpdate,
    db: AsyncSession = Depends(get_db),
) -> VariantResponse:
    """
    Update an existing variant.

    Args:
        variant_id: ID of the variant
        data: Update data
        db: Database session

    Returns:
        VariantResponse: Updated variant

    Raises:
        HTTPException: If variant not found
    """
    result = await db.execute(
        select(Variant).where(Variant.id == variant_id)
    )
    variant = result.scalar_one_or_none()

    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Variant {variant_id} not found",
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(variant, field, value)

    await db.commit()
    await db.refresh(variant)

    return VariantResponse.model_validate(variant)


@router.delete(
    "/{variant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete variant",
    description="Delete a variant",
)
async def delete_variant(
    variant_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a variant.

    Args:
        variant_id: ID of the variant
        db: Database session

    Raises:
        HTTPException: If variant not found
    """
    result = await db.execute(
        select(Variant).where(Variant.id == variant_id)
    )
    variant = result.scalar_one_or_none()

    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Variant {variant_id} not found",
        )

    await db.delete(variant)
    await db.commit()
