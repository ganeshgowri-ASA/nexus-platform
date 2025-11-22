"""Celery tasks for workflow execution"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
from celery import Task
from sqlalchemy import select
from modules.browser_automation.tasks.celery_app import celery_app
from modules.browser_automation.models import (
    Workflow,
    WorkflowExecution,
    Schedule,
    WorkflowStatus,
)
from modules.browser_automation.models.database import AsyncSessionLocal
from modules.browser_automation.services.executor import WorkflowExecutor


class DatabaseTask(Task):
    """Base task with database session"""
    _db = None

    @property
    def db(self):
        if self._db is None:
            self._db = AsyncSessionLocal()
        return self._db


@celery_app.task(name="execute_workflow_task", bind=True, base=DatabaseTask)
def execute_workflow_task(self, workflow_id: int, execution_id: int) -> Dict[str, Any]:
    """Execute a workflow asynchronously"""
    async def _execute():
        async with AsyncSessionLocal() as db:
            # Get workflow
            result = await db.execute(
                select(Workflow).where(Workflow.id == workflow_id)
            )
            workflow = result.scalar_one_or_none()

            if not workflow:
                return {"status": "failed", "error": "Workflow not found"}

            # Get execution
            result = await db.execute(
                select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
            )
            execution = result.scalar_one_or_none()

            if not execution:
                return {"status": "failed", "error": "Execution not found"}

            # Execute workflow
            executor = WorkflowExecutor(workflow, use_playwright=True, execution=execution)
            result = await executor.execute()

            # Commit changes
            await db.commit()

            return result

    # Run async function in event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_execute())
    finally:
        loop.close()


@celery_app.task(name="scheduled_workflow_task")
def scheduled_workflow_task(schedule_id: int) -> Dict[str, Any]:
    """Execute a scheduled workflow"""
    async def _execute():
        async with AsyncSessionLocal() as db:
            # Get schedule
            result = await db.execute(
                select(Schedule).where(Schedule.id == schedule_id)
            )
            schedule = result.scalar_one_or_none()

            if not schedule or not schedule.is_active:
                return {"status": "skipped", "reason": "Schedule not active"}

            # Get workflow
            result = await db.execute(
                select(Workflow).where(Workflow.id == schedule.workflow_id)
            )
            workflow = result.scalar_one_or_none()

            if not workflow or not workflow.is_active:
                return {"status": "skipped", "reason": "Workflow not active"}

            # Create execution
            execution = WorkflowExecution(
                workflow_id=workflow.id,
                status=WorkflowStatus.PENDING,
                triggered_by="scheduled"
            )
            db.add(execution)
            await db.flush()

            # Execute workflow
            executor = WorkflowExecutor(workflow, use_playwright=True, execution=execution)
            result = await executor.execute()

            # Update schedule stats
            schedule.last_run_at = datetime.utcnow()
            schedule.run_count += 1

            if result.get("status") == "failed":
                schedule.failure_count += 1

            await db.commit()

            return result

    # Run async function in event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_execute())
    finally:
        loop.close()


@celery_app.task(name="check_scheduled_workflows")
def check_scheduled_workflows() -> Dict[str, Any]:
    """Check and trigger scheduled workflows"""
    async def _check():
        from croniter import croniter
        async with AsyncSessionLocal() as db:
            # Get active schedules
            result = await db.execute(
                select(Schedule).where(Schedule.is_active == True)
            )
            schedules = result.scalars().all()

            triggered = 0
            now = datetime.utcnow()

            for schedule in schedules:
                try:
                    # Check if schedule should run
                    cron = croniter(schedule.cron_expression, now)
                    next_run = cron.get_prev(datetime)

                    # If next_run is within the last minute and hasn't run yet
                    if schedule.last_run_at is None or next_run > schedule.last_run_at:
                        # Trigger workflow
                        scheduled_workflow_task.delay(schedule.id)
                        triggered += 1

                        # Update next run time
                        schedule.next_run_at = cron.get_next(datetime)

                except Exception as e:
                    print(f"Error checking schedule {schedule.id}: {e}")
                    continue

            await db.commit()

            return {
                "status": "success",
                "schedules_checked": len(schedules),
                "workflows_triggered": triggered
            }

    # Run async function in event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_check())
    finally:
        loop.close()
