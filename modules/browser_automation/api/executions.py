"""Execution API endpoints"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from modules.browser_automation.models import (
    get_db,
    WorkflowExecution,
    WorkflowExecutionResponse,
    WorkflowStatus,
)

router = APIRouter(prefix="/executions", tags=["executions"])


@router.get("/", response_model=List[WorkflowExecutionResponse])
async def list_executions(
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[WorkflowStatus] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db)
):
    """List all executions"""
    query = select(WorkflowExecution)

    if status_filter:
        query = query.where(WorkflowExecution.status == status_filter)

    query = query.offset(skip).limit(limit).order_by(WorkflowExecution.started_at.desc())
    result = await db.execute(query)
    executions = result.scalars().all()

    return executions


@router.get("/{execution_id}", response_model=WorkflowExecutionResponse)
async def get_execution(
    execution_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get execution by ID"""
    result = await db.execute(
        select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
    )
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution {execution_id} not found"
        )

    return execution


@router.delete("/{execution_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_execution(
    execution_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete execution record"""
    result = await db.execute(
        select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
    )
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution {execution_id} not found"
        )

    await db.delete(execution)
    await db.commit()


@router.get("/stats/summary")
async def get_execution_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get execution statistics"""
    # Total executions
    total_result = await db.execute(
        select(func.count(WorkflowExecution.id))
    )
    total = total_result.scalar()

    # Count by status
    status_result = await db.execute(
        select(
            WorkflowExecution.status,
            func.count(WorkflowExecution.id)
        ).group_by(WorkflowExecution.status)
    )
    status_counts = {status: count for status, count in status_result.all()}

    # Average duration for completed executions
    duration_result = await db.execute(
        select(func.avg(WorkflowExecution.duration_seconds))
        .where(WorkflowExecution.status == WorkflowStatus.COMPLETED)
    )
    avg_duration = duration_result.scalar() or 0

    return {
        "total_executions": total,
        "by_status": status_counts,
        "average_duration_seconds": round(avg_duration, 2),
    }
