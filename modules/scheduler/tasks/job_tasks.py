"""Celery tasks for job execution"""
from celery import Task
from datetime import datetime, timedelta
from typing import Any, Dict, List
import traceback
from modules.scheduler.tasks.celery_app import celery_app
from modules.scheduler.models import get_sync_db, ScheduledJob, JobExecution, JobStatus
from modules.scheduler.services.notification_service import NotificationService
from modules.scheduler.utils.cron_utils import calculate_next_run
from sqlalchemy import select, and_


class CallbackTask(Task):
    """Base task with callbacks"""

    def on_success(self, retval, task_id, args, kwargs):
        """Success callback"""
        pass

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Failure callback"""
        pass

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Retry callback"""
        pass


@celery_app.task(base=CallbackTask, bind=True, max_retries=3)
def execute_scheduled_job(
    self,
    job_id: int,
    execution_id: int,
    task_args: List[Any] = None,
    task_kwargs: Dict[str, Any] = None
):
    """Execute a scheduled job"""
    db = next(get_sync_db())
    start_time = datetime.utcnow()

    try:
        # Get execution record
        execution = db.query(JobExecution).filter(JobExecution.id == execution_id).first()
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        # Update status to running
        execution.status = JobStatus.RUNNING
        execution.started_at = start_time
        execution.task_id = self.request.id
        execution.worker_name = self.request.hostname
        db.commit()

        # Get job
        job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Send start notification
        NotificationService.send_notification(
            job=job,
            execution=execution,
            event="start",
            db=db
        )

        # Execute the actual task
        # This is a placeholder - in production, you'd dynamically import and execute the task
        result = execute_task_function(
            job.task_name,
            task_args or job.task_args,
            task_kwargs or job.task_kwargs
        )

        # Update execution as completed
        end_time = datetime.utcnow()
        execution.status = JobStatus.COMPLETED
        execution.completed_at = end_time
        execution.duration_seconds = int((end_time - start_time).total_seconds())
        execution.result = result
        db.commit()

        # Update job last run time
        job.last_run_at = end_time
        job.status = JobStatus.COMPLETED

        # Calculate next run
        if job.is_active:
            next_run = calculate_next_run(
                job_type=job.job_type,
                cron_expression=job.cron_expression,
                interval_seconds=job.interval_seconds,
                scheduled_time=job.scheduled_time,
                timezone=job.timezone
            )
            job.next_run_at = next_run

        db.commit()

        # Send success notification
        NotificationService.send_notification(
            job=job,
            execution=execution,
            event="success",
            db=db
        )

        return result

    except Exception as exc:
        # Update execution as failed
        end_time = datetime.utcnow()
        execution.status = JobStatus.FAILED
        execution.completed_at = end_time
        execution.duration_seconds = int((end_time - start_time).total_seconds())
        execution.error_message = str(exc)
        execution.traceback = traceback.format_exc()
        db.commit()

        # Update job status
        job.status = JobStatus.FAILED
        db.commit()

        # Check if we should retry
        if execution.attempt_number < job.max_retries:
            # Send retry notification
            NotificationService.send_notification(
                job=job,
                execution=execution,
                event="retry",
                db=db
            )

            # Calculate retry delay
            retry_delay = job.retry_delay
            if job.retry_backoff:
                retry_delay = retry_delay * (2 ** (execution.attempt_number - 1))

            # Create new execution for retry
            retry_execution = JobExecution(
                job_id=job_id,
                scheduled_at=datetime.utcnow() + timedelta(seconds=retry_delay),
                attempt_number=execution.attempt_number + 1,
                is_retry=True,
                parent_execution_id=execution_id
            )
            db.add(retry_execution)
            db.commit()

            # Schedule retry
            self.retry(
                exc=exc,
                countdown=retry_delay,
                kwargs={
                    'job_id': job_id,
                    'execution_id': retry_execution.id,
                    'task_args': task_args,
                    'task_kwargs': task_kwargs
                }
            )
        else:
            # Send failure notification
            NotificationService.send_notification(
                job=job,
                execution=execution,
                event="failure",
                db=db
            )

        raise

    finally:
        db.close()


def execute_task_function(task_name: str, args: List[Any], kwargs: Dict[str, Any]) -> Any:
    """
    Execute the actual task function
    This is a placeholder - implement your task registry here
    """
    # Example task registry
    task_registry = {
        'example.hello_world': lambda *args, **kwargs: {'message': 'Hello World!'},
        'example.add_numbers': lambda a, b: {'result': a + b},
        'example.send_email': lambda to, subject, body: {'status': 'sent'},
    }

    task_func = task_registry.get(task_name)
    if not task_func:
        raise ValueError(f"Task '{task_name}' not found in registry")

    return task_func(*args, **kwargs)


@celery_app.task
def check_scheduled_jobs():
    """Check for jobs that need to be executed"""
    db = next(get_sync_db())

    try:
        now = datetime.utcnow()

        # Find jobs that are due
        jobs = db.query(ScheduledJob).filter(
            and_(
                ScheduledJob.is_active == True,
                ScheduledJob.next_run_at <= now
            )
        ).all()

        for job in jobs:
            # Create execution record
            execution = JobExecution(
                job_id=job.id,
                scheduled_at=now,
                attempt_number=1
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)

            # Queue the task
            execute_scheduled_job.apply_async(
                kwargs={
                    'job_id': job.id,
                    'execution_id': execution.id
                },
                priority=job.priority
            )

    except Exception as e:
        print(f"Error checking scheduled jobs: {e}")
        traceback.print_exc()

    finally:
        db.close()


@celery_app.task
def cleanup_old_executions(days: int = 30):
    """Clean up old execution records"""
    db = next(get_sync_db())

    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        deleted = db.query(JobExecution).filter(
            JobExecution.created_at < cutoff_date
        ).delete()

        db.commit()

        return {'deleted': deleted}

    except Exception as e:
        db.rollback()
        raise e

    finally:
        db.close()
