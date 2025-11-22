"""Celery tasks for batch processing."""

import traceback
from typing import Any, Dict, List
from datetime import datetime
from celery import Task, group, chain
from sqlalchemy.orm import Session
from tasks.celery_app import celery_app
from database.connection import SessionLocal
from database.models.batch_job import BatchJob, BatchTask, JobStatus, TaskStatus
from .service import BatchJobService, BatchTaskService
from loguru import logger


class DatabaseTask(Task):
    """Base task with database session management."""

    _db: Session = None

    @property
    def db(self) -> Session:
        """Get database session."""
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        """Close database session after task completion."""
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="batch_processing.process_batch_job",
    max_retries=3,
    default_retry_delay=60
)
def process_batch_job(self, job_id: int) -> Dict[str, Any]:
    """
    Main task to process a batch job.

    Args:
        job_id: ID of the batch job to process

    Returns:
        Result summary dictionary
    """
    db = self.db

    try:
        logger.info(f"Starting batch job {job_id}")

        # Get job
        job = BatchJobService.get_job(db, job_id)
        if not job:
            raise ValueError(f"Batch job {job_id} not found")

        # Start job
        BatchJobService.start_job(db, job_id, celery_task_id=self.request.id)

        # Get all tasks for this job
        tasks, total = BatchTaskService.get_tasks_by_job(db, job_id, limit=100000)

        if not tasks:
            logger.warning(f"No tasks found for batch job {job_id}")
            BatchJobService.complete_job(
                db, job_id,
                result_summary={"message": "No tasks to process"}
            )
            return {"status": "completed", "message": "No tasks to process"}

        logger.info(f"Processing {len(tasks)} tasks for job {job_id}")

        # Create task group for parallel processing
        task_group = group(
            process_single_task.s(task.id)
            for task in tasks
        )

        # Execute tasks in parallel
        result = task_group.apply_async()

        # Wait for all tasks to complete
        result.get(disable_sync_subtasks=False)

        # Update job progress and status
        update_job_progress(job_id)

        # Get updated job
        job = BatchJobService.get_job(db, job_id)

        result_summary = {
            "total_items": job.total_items,
            "processed_items": job.processed_items,
            "successful_items": job.successful_items,
            "failed_items": job.failed_items,
            "duration_seconds": job.duration_seconds
        }

        # Mark job as completed
        BatchJobService.complete_job(db, job_id, result_summary=result_summary)

        logger.info(f"Completed batch job {job_id}: {result_summary}")

        return result_summary

    except Exception as e:
        logger.error(f"Error processing batch job {job_id}: {str(e)}")
        logger.error(traceback.format_exc())

        # Mark job as failed
        BatchJobService.fail_job(db, job_id, str(e))

        # Retry if retries are available
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)

        raise


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="batch_processing.process_single_task",
    max_retries=3,
    default_retry_delay=30
)
def process_single_task(self, task_id: int) -> Dict[str, Any]:
    """
    Process a single batch task.

    Args:
        task_id: ID of the task to process

    Returns:
        Task result dictionary
    """
    db = self.db

    try:
        # Get task
        task = BatchTaskService.get_task(db, task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        logger.info(f"Processing task {task_id} (job {task.batch_job_id})")

        # Start task
        BatchTaskService.start_task(db, task_id, celery_task_id=self.request.id)

        # Process the task based on input data
        output_data = process_task_data(task.input_data)

        # Mark task as completed
        BatchTaskService.complete_task(db, task_id, output_data=output_data)

        logger.info(f"Completed task {task_id}")

        return {
            "task_id": task_id,
            "status": "completed",
            "output_data": output_data
        }

    except Exception as e:
        logger.error(f"Error processing task {task_id}: {str(e)}")
        error_traceback = traceback.format_exc()

        # Get task to check retry count
        task = BatchTaskService.get_task(db, task_id)

        if task and task.can_retry:
            # Mark task for retry
            BatchTaskService.retry_task(db, task_id)
            logger.info(f"Retrying task {task_id} (attempt {task.retry_count + 1})")

            # Retry the task
            raise self.retry(exc=e, countdown=30 * (task.retry_count + 1))
        else:
            # Mark task as failed
            BatchTaskService.fail_task(db, task_id, str(e), error_traceback)

            # Don't raise exception to allow other tasks to continue
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e)
            }


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="batch_processing.update_job_progress"
)
def update_job_progress(self, job_id: int) -> Dict[str, Any]:
    """
    Update batch job progress based on task statuses.

    Args:
        job_id: ID of the batch job

    Returns:
        Progress summary
    """
    db = self.db

    try:
        # Get all tasks for the job
        tasks, total = BatchTaskService.get_tasks_by_job(db, job_id, limit=100000)

        # Count tasks by status
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in tasks if t.status == TaskStatus.FAILED)
        running = sum(1 for t in tasks if t.status == TaskStatus.RUNNING)
        pending = sum(1 for t in tasks if t.status == TaskStatus.PENDING)

        processed = completed + failed

        # Update job progress
        BatchJobService.update_progress(
            db, job_id,
            processed_items=processed,
            successful_items=completed,
            failed_items=failed
        )

        return {
            "job_id": job_id,
            "total": total,
            "processed": processed,
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": pending
        }

    except Exception as e:
        logger.error(f"Error updating job progress for {job_id}: {str(e)}")
        raise


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="batch_processing.retry_failed_tasks"
)
def retry_failed_tasks(self, job_id: int) -> Dict[str, Any]:
    """
    Retry all failed tasks for a batch job.

    Args:
        job_id: ID of the batch job

    Returns:
        Retry summary
    """
    db = self.db

    try:
        # Get all failed tasks
        failed_tasks = BatchTaskService.get_failed_tasks(db, job_id)

        retryable_tasks = [t for t in failed_tasks if t.can_retry]

        if not retryable_tasks:
            return {
                "job_id": job_id,
                "retried_count": 0,
                "message": "No tasks available for retry"
            }

        # Retry each task
        for task in retryable_tasks:
            BatchTaskService.retry_task(db, task.id)
            process_single_task.apply_async(args=[task.id])

        logger.info(f"Retrying {len(retryable_tasks)} failed tasks for job {job_id}")

        return {
            "job_id": job_id,
            "retried_count": len(retryable_tasks),
            "message": f"Retrying {len(retryable_tasks)} tasks"
        }

    except Exception as e:
        logger.error(f"Error retrying failed tasks for job {job_id}: {str(e)}")
        raise


def process_task_data(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process task data - placeholder for actual processing logic.

    This function should be customized based on the specific
    batch processing requirements.

    Args:
        input_data: Input data dictionary

    Returns:
        Processed output data
    """
    # Example processing logic
    # In a real implementation, this would be customized based on job type

    if not input_data:
        return {"status": "skipped", "reason": "No input data"}

    # Simulate processing
    output_data = {
        "processed": True,
        "timestamp": datetime.utcnow().isoformat(),
        "input_keys": list(input_data.keys()),
        "result": "success"
    }

    return output_data


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="batch_processing.cancel_job"
)
def cancel_job(self, job_id: int) -> Dict[str, Any]:
    """
    Cancel a running batch job.

    Args:
        job_id: ID of the batch job to cancel

    Returns:
        Cancellation result
    """
    db = self.db

    try:
        job = BatchJobService.cancel_job(db, job_id)

        if not job:
            return {
                "job_id": job_id,
                "status": "error",
                "message": "Job not found or already in terminal state"
            }

        # Revoke celery task if exists
        if job.celery_task_id:
            celery_app.control.revoke(job.celery_task_id, terminate=True)

        logger.info(f"Cancelled batch job {job_id}")

        return {
            "job_id": job_id,
            "status": "cancelled",
            "message": "Job cancelled successfully"
        }

    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {str(e)}")
        raise
