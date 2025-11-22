"""Celery tasks for workflow execution."""

import asyncio
from typing import Dict, Any
from celery import Task
import logging

from .celery_app import celery_app
from ..core.executor import TaskExecutionEngine, WorkflowExecutionEngine

logger = logging.getLogger(__name__)


class AsyncTask(Task):
    """Base task class for async operations."""

    def __call__(self, *args, **kwargs):
        """Call the async run method in a new event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.run_async(*args, **kwargs))
        finally:
            loop.close()

    async def run_async(self, *args, **kwargs):
        """Async run method to be implemented by subclasses."""
        raise NotImplementedError()


@celery_app.task(base=AsyncTask, bind=True, max_retries=3, default_retry_delay=60)
async def execute_task(
    self,
    task_execution_id: int,
    task_type: str,
    task_config: Dict[str, Any],
    input_data: Dict[str, Any],
    max_retries: int = 3,
    retry_delay: int = 60,
    timeout: int = 3600,
) -> Dict[str, Any]:
    """
    Execute a single task.

    Args:
        task_execution_id: Task execution database ID
        task_type: Type of task to execute
        task_config: Task configuration
        input_data: Input data for the task
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries
        timeout: Task timeout

    Returns:
        Task output data
    """
    try:
        engine = TaskExecutionEngine()
        result = await engine.execute_task(
            task_execution_id=task_execution_id,
            task_type=task_type,
            task_config=task_config,
            input_data=input_data,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
        )
        return result
    except Exception as exc:
        logger.error(f"Task execution {task_execution_id} failed: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(base=AsyncTask, bind=True, max_retries=1)
async def execute_workflow(
    self,
    workflow_execution_id: int,
    dag_definition: Dict[str, Any],
    input_data: Dict[str, Any] = None,
    max_parallel_tasks: int = 10,
) -> Dict[str, Any]:
    """
    Execute a complete workflow.

    Args:
        workflow_execution_id: Workflow execution database ID
        dag_definition: DAG definition
        input_data: Input data for the workflow
        max_parallel_tasks: Maximum number of parallel tasks

    Returns:
        Workflow output data
    """
    try:
        engine = WorkflowExecutionEngine()
        result = await engine.execute_workflow(
            workflow_execution_id=workflow_execution_id,
            dag_definition=dag_definition,
            input_data=input_data or {},
            max_parallel_tasks=max_parallel_tasks,
        )
        return result
    except Exception as exc:
        logger.error(f"Workflow execution {workflow_execution_id} failed: {exc}")
        raise


@celery_app.task
def scheduled_workflow_trigger(workflow_id: int):
    """
    Trigger a scheduled workflow execution.

    Args:
        workflow_id: Workflow database ID
    """
    from ..api.services import WorkflowService
    import asyncio

    async def run():
        async with AsyncSessionLocal() as session:
            service = WorkflowService(session)
            await service.trigger_workflow(workflow_id)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run())
    finally:
        loop.close()


@celery_app.task
def cleanup_old_executions(days: int = 30):
    """
    Clean up old workflow executions.

    Args:
        days: Number of days to keep executions
    """
    from datetime import datetime, timedelta
    from ..db.session import AsyncSessionLocal
    from ..db.models import WorkflowExecution
    from sqlalchemy import delete
    import asyncio

    async def run():
        async with AsyncSessionLocal() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            stmt = delete(WorkflowExecution).where(
                WorkflowExecution.completed_at < cutoff_date
            )
            result = await session.execute(stmt)
            await session.commit()
            logger.info(f"Cleaned up {result.rowcount} old workflow executions")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run())
    finally:
        loop.close()
