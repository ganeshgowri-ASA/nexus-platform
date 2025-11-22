"""Workflow API endpoints"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from modules.browser_automation.models import (
    get_db,
    Workflow,
    WorkflowStep,
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    WorkflowExecuteRequest,
    WorkflowExecution,
    WorkflowExecutionResponse,
    WorkflowStatus,
)
from modules.browser_automation.services.executor import WorkflowExecutor

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("/", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow_data: WorkflowCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new workflow"""
    # Create workflow
    workflow = Workflow(
        name=workflow_data.name,
        description=workflow_data.description,
        is_active=workflow_data.is_active,
        headless=workflow_data.headless,
        browser_type=workflow_data.browser_type,
        timeout=workflow_data.timeout,
    )

    db.add(workflow)
    await db.flush()

    # Create steps
    for step_data in workflow_data.steps:
        step = WorkflowStep(
            workflow_id=workflow.id,
            **step_data.model_dump()
        )
        db.add(step)

    await db.commit()
    await db.refresh(workflow)

    # Fetch with relationships
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow.id)
    )
    workflow = result.scalar_one()

    return workflow


@router.get("/", response_model=List[WorkflowResponse])
async def list_workflows(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all workflows"""
    result = await db.execute(
        select(Workflow).offset(skip).limit(limit)
    )
    workflows = result.scalars().all()
    return workflows


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get workflow by ID"""
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )

    return workflow


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: int,
    workflow_data: WorkflowUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update workflow"""
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )

    # Update fields
    update_data = workflow_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workflow, field, value)

    await db.commit()
    await db.refresh(workflow)

    return workflow


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete workflow"""
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )

    await db.delete(workflow)
    await db.commit()


@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    workflow_id: int,
    execute_request: WorkflowExecuteRequest = WorkflowExecuteRequest(),
    db: AsyncSession = Depends(get_db)
):
    """Execute a workflow"""
    # Get workflow
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )

    if not workflow.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow is not active"
        )

    # Create execution record
    execution = WorkflowExecution(
        workflow_id=workflow.id,
        status=WorkflowStatus.PENDING,
        triggered_by="manual"
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)

    # Override workflow settings if provided
    if execute_request.headless is not None:
        workflow.headless = execute_request.headless
    if execute_request.browser_type is not None:
        workflow.browser_type = execute_request.browser_type

    # Execute workflow
    executor = WorkflowExecutor(workflow, use_playwright=True, execution=execution)
    result = await executor.execute()

    # Update execution record
    await db.commit()
    await db.refresh(execution)

    return execution


@router.get("/{workflow_id}/executions", response_model=List[WorkflowExecutionResponse])
async def list_workflow_executions(
    workflow_id: int,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """List workflow executions"""
    result = await db.execute(
        select(WorkflowExecution)
        .where(WorkflowExecution.workflow_id == workflow_id)
        .offset(skip)
        .limit(limit)
        .order_by(WorkflowExecution.started_at.desc())
    )
    executions = result.scalars().all()
    return executions


@router.post("/{workflow_id}/duplicate", response_model=WorkflowResponse)
async def duplicate_workflow(
    workflow_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Duplicate an existing workflow"""
    # Get original workflow
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )

    # Create duplicate
    new_workflow = Workflow(
        name=f"{workflow.name} (Copy)",
        description=workflow.description,
        is_active=False,
        headless=workflow.headless,
        browser_type=workflow.browser_type,
        timeout=workflow.timeout,
    )
    db.add(new_workflow)
    await db.flush()

    # Duplicate steps
    for step in workflow.steps:
        new_step = WorkflowStep(
            workflow_id=new_workflow.id,
            step_order=step.step_order,
            step_type=step.step_type,
            name=step.name,
            description=step.description,
            selector=step.selector,
            selector_type=step.selector_type,
            value=step.value,
            wait_before=step.wait_before,
            wait_after=step.wait_after,
            options=step.options,
            error_handling=step.error_handling,
            max_retries=step.max_retries,
        )
        db.add(new_step)

    await db.commit()
    await db.refresh(new_workflow)

    return new_workflow
