"""FastAPI REST API endpoints for workflow orchestration."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import get_db
from ..db.models import WorkflowStatus
from .schemas import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    WorkflowExecutionTrigger,
    WorkflowExecutionResponse,
    TaskExecutionResponse,
    DAGValidationRequest,
    DAGValidationResponse,
    NotificationCreate,
    NotificationResponse,
    WorkflowStatistics,
)
from .services import WorkflowService, NotificationService
from ..core.dag import DAGEngine

# Create routers
workflow_router = APIRouter(prefix="/workflows", tags=["Workflows"])
execution_router = APIRouter(prefix="/executions", tags=["Executions"])
dag_router = APIRouter(prefix="/dag", tags=["DAG"])
notification_router = APIRouter(prefix="/notifications", tags=["Notifications"])
stats_router = APIRouter(prefix="/statistics", tags=["Statistics"])


# Workflow endpoints
@workflow_router.post("/", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow_data: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new workflow.

    - **name**: Workflow name
    - **description**: Workflow description
    - **dag_definition**: DAG definition with tasks
    - **config**: Workflow configuration
    - **schedule_cron**: Cron expression for scheduling
    - **is_scheduled**: Enable scheduled execution
    """
    try:
        async with db as session:
            service = WorkflowService(session)
            workflow = await service.create_workflow(workflow_data)
            return workflow
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workflow: {str(e)}",
        )


@workflow_router.get("/", response_model=List[WorkflowResponse])
async def list_workflows(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[WorkflowStatus] = None,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    List workflows with optional filters.

    - **skip**: Number of workflows to skip
    - **limit**: Maximum number of workflows to return
    - **status**: Filter by workflow status
    - **category**: Filter by category
    """
    async with db as session:
        service = WorkflowService(session)
        workflows = await service.list_workflows(
            skip=skip, limit=limit, status=status, category=category
        )
        return workflows


@workflow_router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get workflow by ID."""
    async with db as session:
        service = WorkflowService(session)
        workflow = await service.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found",
            )
        return workflow


@workflow_router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: int,
    workflow_data: WorkflowUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update workflow."""
    try:
        async with db as session:
            service = WorkflowService(session)
            workflow = await service.update_workflow(workflow_id, workflow_data)
            if not workflow:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Workflow {workflow_id} not found",
                )
            return workflow
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@workflow_router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete workflow."""
    async with db as session:
        service = WorkflowService(session)
        deleted = await service.delete_workflow(workflow_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found",
            )


@workflow_router.post("/{workflow_id}/trigger", response_model=WorkflowExecutionResponse)
async def trigger_workflow(
    workflow_id: int,
    trigger_data: Optional[WorkflowExecutionTrigger] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger workflow execution.

    - **workflow_id**: Workflow ID to execute
    - **input_data**: Input data for workflow
    - **triggered_by**: Trigger source (manual, api, scheduled)
    """
    try:
        async with db as session:
            service = WorkflowService(session)
            execution = await service.trigger_workflow(
                workflow_id=workflow_id,
                input_data=trigger_data.input_data if trigger_data else {},
                triggered_by=trigger_data.triggered_by if trigger_data else "api",
            )
            return execution
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Execution endpoints
@execution_router.get("/", response_model=List[WorkflowExecutionResponse])
async def list_executions(
    workflow_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[WorkflowStatus] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    List workflow executions.

    - **workflow_id**: Filter by workflow ID
    - **skip**: Number of executions to skip
    - **limit**: Maximum number of executions to return
    - **status**: Filter by execution status
    """
    async with db as session:
        service = WorkflowService(session)
        executions = await service.list_workflow_executions(
            workflow_id=workflow_id, skip=skip, limit=limit, status=status
        )
        return executions


@execution_router.get("/{execution_id}", response_model=WorkflowExecutionResponse)
async def get_execution(
    execution_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get workflow execution by ID."""
    async with db as session:
        service = WorkflowService(session)
        execution = await service.get_workflow_execution(execution_id)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution {execution_id} not found",
            )
        return execution


@execution_router.post("/{execution_id}/cancel", response_model=WorkflowExecutionResponse)
async def cancel_execution(
    execution_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Cancel workflow execution."""
    async with db as session:
        service = WorkflowService(session)
        cancelled = await service.cancel_workflow_execution(execution_id)
        if not cancelled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel execution (not found or not running)",
            )
        execution = await service.get_workflow_execution(execution_id)
        return execution


# DAG endpoints
@dag_router.post("/validate", response_model=DAGValidationResponse)
async def validate_dag(request: DAGValidationRequest):
    """
    Validate a DAG definition.

    Returns validation status, execution order, parallel groups, and visualization data.
    """
    try:
        dag = DAGEngine.from_dict(request.dag_definition)
        is_valid, error_message = dag.validate()

        response = {
            "is_valid": is_valid,
            "error_message": error_message,
        }

        if is_valid:
            response.update({
                "execution_order": dag.get_execution_order(),
                "parallel_groups": [list(group) for group in dag.get_parallel_groups()],
                "visualization": dag.visualize(),
            })

        return response
    except Exception as e:
        return {
            "is_valid": False,
            "error_message": str(e),
        }


# Notification endpoints
@notification_router.post("/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(
    notification_data: NotificationCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create notification configuration for a workflow.

    - **workflow_id**: Workflow ID
    - **notification_type**: Type of notification (email, slack, webhook)
    - **on_success**: Notify on success
    - **on_failure**: Notify on failure
    - **on_start**: Notify on start
    - **config**: Notification configuration
    """
    async with db as session:
        service = NotificationService(session)
        notification = await service.create_notification(notification_data)
        return notification


@notification_router.get("/{workflow_id}", response_model=List[NotificationResponse])
async def list_notifications(
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
):
    """List notifications for a workflow."""
    async with db as session:
        service = NotificationService(session)
        notifications = await service.list_notifications(workflow_id)
        return notifications


@notification_router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete notification configuration."""
    async with db as session:
        service = NotificationService(session)
        deleted = await service.delete_notification(notification_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification {notification_id} not found",
            )


# Statistics endpoints
@stats_router.get("/workflows", response_model=WorkflowStatistics)
async def get_workflow_statistics(
    db: AsyncSession = Depends(get_db),
):
    """Get workflow statistics (counts, success rate, average duration)."""
    async with db as session:
        service = WorkflowService(session)
        stats = await service.get_workflow_statistics()
        return stats
