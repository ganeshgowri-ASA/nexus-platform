"""Schedule API endpoints"""
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from modules.browser_automation.models import (
    get_db,
    Schedule,
    Workflow,
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse,
)

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.post("/", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_data: ScheduleCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new schedule"""
    # Verify workflow exists
    result = await db.execute(
        select(Workflow).where(Workflow.id == schedule_data.workflow_id)
    )
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {schedule_data.workflow_id} not found"
        )

    # Create schedule
    schedule = Schedule(**schedule_data.model_dump())
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)

    return schedule


@router.get("/", response_model=List[ScheduleResponse])
async def list_schedules(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """List all schedules"""
    query = select(Schedule)

    if active_only:
        query = query.where(Schedule.is_active == True)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    schedules = result.scalars().all()

    return schedules


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get schedule by ID"""
    result = await db.execute(
        select(Schedule).where(Schedule.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule {schedule_id} not found"
        )

    return schedule


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    schedule_data: ScheduleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update schedule"""
    result = await db.execute(
        select(Schedule).where(Schedule.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule {schedule_id} not found"
        )

    # Update fields
    update_data = schedule_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(schedule, field, value)

    await db.commit()
    await db.refresh(schedule)

    return schedule


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete schedule"""
    result = await db.execute(
        select(Schedule).where(Schedule.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule {schedule_id} not found"
        )

    await db.delete(schedule)
    await db.commit()


@router.post("/{schedule_id}/toggle", response_model=ScheduleResponse)
async def toggle_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Toggle schedule active status"""
    result = await db.execute(
        select(Schedule).where(Schedule.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule {schedule_id} not found"
        )

    schedule.is_active = not schedule.is_active
    await db.commit()
    await db.refresh(schedule)

    return schedule
