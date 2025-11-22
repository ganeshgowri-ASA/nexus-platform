"""Business logic services for workflow management."""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import (
    Workflow,
    Task,
    WorkflowExecution,
    TaskExecution,
    ScheduledWorkflow,
    WorkflowNotification,
    WorkflowStatus,
    TaskStatus,
)
from ..core.dag import DAGEngine
from .schemas import (
    WorkflowCreate,
    WorkflowUpdate,
    TaskCreate,
    NotificationCreate,
)


class WorkflowService:
    """Service for workflow operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_workflow(self, workflow_data: WorkflowCreate) -> Workflow:
        """Create a new workflow."""
        # Validate DAG
        dag = DAGEngine.from_dict(workflow_data.dag_definition)
        is_valid, error = dag.validate()
        if not is_valid:
            raise ValueError(f"Invalid DAG: {error}")

        # Create workflow
        workflow = Workflow(
            name=workflow_data.name,
            description=workflow_data.description,
            dag_definition=workflow_data.dag_definition,
            config=workflow_data.config or {},
            schedule_cron=workflow_data.schedule_cron,
            is_scheduled=workflow_data.is_scheduled,
            tags=workflow_data.tags,
            category=workflow_data.category,
            created_by=workflow_data.created_by,
            status=WorkflowStatus.CREATED,
        )

        self.session.add(workflow)
        await self.session.commit()
        await self.session.refresh(workflow)

        # Create tasks from DAG
        for task_key, task_node in dag.tasks.items():
            task = Task(
                workflow_id=workflow.id,
                task_key=task_node.task_key,
                name=task_node.name,
                task_type=task_node.task_type,
                executor="celery",
                config=task_node.config,
                depends_on=task_node.depends_on,
                max_retries=task_node.retry_config.get("max_retries", 3),
                retry_delay=task_node.retry_config.get("retry_delay", 60),
                timeout=task_node.retry_config.get("timeout", 3600),
            )
            self.session.add(task)

        await self.session.commit()

        return workflow

    async def get_workflow(self, workflow_id: int) -> Optional[Workflow]:
        """Get workflow by ID."""
        result = await self.session.execute(
            select(Workflow).where(Workflow.id == workflow_id)
        )
        return result.scalar_one_or_none()

    async def list_workflows(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[WorkflowStatus] = None,
        category: Optional[str] = None,
    ) -> List[Workflow]:
        """List workflows with filters."""
        query = select(Workflow)

        if status:
            query = query.where(Workflow.status == status)
        if category:
            query = query.where(Workflow.category == category)

        query = query.offset(skip).limit(limit).order_by(desc(Workflow.created_at))

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_workflow(
        self, workflow_id: int, workflow_data: WorkflowUpdate
    ) -> Optional[Workflow]:
        """Update workflow."""
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return None

        # Update fields
        update_data = workflow_data.model_dump(exclude_unset=True)

        # Validate DAG if provided
        if "dag_definition" in update_data:
            dag = DAGEngine.from_dict(update_data["dag_definition"])
            is_valid, error = dag.validate()
            if not is_valid:
                raise ValueError(f"Invalid DAG: {error}")

        for field, value in update_data.items():
            setattr(workflow, field, value)

        await self.session.commit()
        await self.session.refresh(workflow)

        return workflow

    async def delete_workflow(self, workflow_id: int) -> bool:
        """Delete workflow."""
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return False

        await self.session.delete(workflow)
        await self.session.commit()

        return True

    async def trigger_workflow(
        self,
        workflow_id: int,
        input_data: Optional[Dict[str, Any]] = None,
        triggered_by: str = "manual",
    ) -> WorkflowExecution:
        """Trigger workflow execution."""
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Create execution record
        run_id = str(uuid.uuid4())
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            run_id=run_id,
            status=WorkflowStatus.RUNNING,
            started_at=datetime.utcnow(),
            triggered_by=triggered_by,
            input_data=input_data or {},
            total_tasks=len(workflow.dag_definition.get("tasks", {})),
        )

        self.session.add(execution)
        await self.session.commit()
        await self.session.refresh(execution)

        # Update workflow
        workflow.status = WorkflowStatus.RUNNING
        workflow.current_run_id = run_id
        workflow.total_runs += 1
        await self.session.commit()

        # Queue workflow execution
        from ..workers.tasks import execute_workflow
        execute_workflow.delay(
            workflow_execution_id=execution.id,
            dag_definition=workflow.dag_definition,
            input_data=input_data or {},
        )

        return execution

    async def get_workflow_execution(
        self, execution_id: int
    ) -> Optional[WorkflowExecution]:
        """Get workflow execution by ID."""
        result = await self.session.execute(
            select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
        )
        return result.scalar_one_or_none()

    async def list_workflow_executions(
        self,
        workflow_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
        status: Optional[WorkflowStatus] = None,
    ) -> List[WorkflowExecution]:
        """List workflow executions."""
        query = select(WorkflowExecution)

        if workflow_id:
            query = query.where(WorkflowExecution.workflow_id == workflow_id)
        if status:
            query = query.where(WorkflowExecution.status == status)

        query = query.offset(skip).limit(limit).order_by(desc(WorkflowExecution.started_at))

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def cancel_workflow_execution(self, execution_id: int) -> bool:
        """Cancel workflow execution."""
        execution = await self.get_workflow_execution(execution_id)
        if not execution:
            return False

        if execution.status not in [WorkflowStatus.RUNNING, WorkflowStatus.SCHEDULED]:
            return False

        execution.status = WorkflowStatus.CANCELLED
        execution.completed_at = datetime.utcnow()
        execution.duration = (
            execution.completed_at - execution.started_at
        ).total_seconds()

        await self.session.commit()

        return True

    async def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get workflow statistics."""
        # Total workflows
        total_workflows = await self.session.scalar(
            select(func.count(Workflow.id))
        )

        # Active workflows
        active_workflows = await self.session.scalar(
            select(func.count(Workflow.id)).where(
                Workflow.status == WorkflowStatus.RUNNING
            )
        )

        # Total executions
        total_executions = await self.session.scalar(
            select(func.count(WorkflowExecution.id))
        )

        # Running executions
        running_executions = await self.session.scalar(
            select(func.count(WorkflowExecution.id)).where(
                WorkflowExecution.status == WorkflowStatus.RUNNING
            )
        )

        # Completed executions
        completed_executions = await self.session.scalar(
            select(func.count(WorkflowExecution.id)).where(
                WorkflowExecution.status == WorkflowStatus.COMPLETED
            )
        )

        # Failed executions
        failed_executions = await self.session.scalar(
            select(func.count(WorkflowExecution.id)).where(
                WorkflowExecution.status == WorkflowStatus.FAILED
            )
        )

        # Average duration
        avg_duration = await self.session.scalar(
            select(func.avg(WorkflowExecution.duration)).where(
                WorkflowExecution.status == WorkflowStatus.COMPLETED
            )
        )

        # Success rate
        success_rate = 0.0
        if total_executions and total_executions > 0:
            success_rate = (completed_executions or 0) / total_executions * 100

        return {
            "total_workflows": total_workflows or 0,
            "active_workflows": active_workflows or 0,
            "total_executions": total_executions or 0,
            "running_executions": running_executions or 0,
            "completed_executions": completed_executions or 0,
            "failed_executions": failed_executions or 0,
            "average_duration": float(avg_duration) if avg_duration else None,
            "success_rate": success_rate,
        }


class NotificationService:
    """Service for notification operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_notification(
        self, notification_data: NotificationCreate
    ) -> WorkflowNotification:
        """Create notification configuration."""
        notification = WorkflowNotification(
            workflow_id=notification_data.workflow_id,
            notification_type=notification_data.notification_type,
            on_success=notification_data.on_success,
            on_failure=notification_data.on_failure,
            on_start=notification_data.on_start,
            config=notification_data.config,
            is_active=notification_data.is_active,
        )

        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)

        return notification

    async def list_notifications(
        self, workflow_id: int
    ) -> List[WorkflowNotification]:
        """List notifications for a workflow."""
        result = await self.session.execute(
            select(WorkflowNotification).where(
                WorkflowNotification.workflow_id == workflow_id
            )
        )
        return list(result.scalars().all())

    async def delete_notification(self, notification_id: int) -> bool:
        """Delete notification configuration."""
        result = await self.session.execute(
            select(WorkflowNotification).where(WorkflowNotification.id == notification_id)
        )
        notification = result.scalar_one_or_none()

        if not notification:
            return False

        await self.session.delete(notification)
        await self.session.commit()

        return True
