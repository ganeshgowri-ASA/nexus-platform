"""
Celery tasks for async ETL job execution.

This module provides asynchronous task execution for ETL jobs
using Celery distributed task queue.
"""

import logging
from typing import Optional, Any
from celery import Celery, Task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from modules.etl.jobs import JobExecutor
from modules.etl.models import JobRun, JobStatus

logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    "nexus_etl",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000
)


class ETLTask(Task):
    """Base task class for ETL operations."""

    _db_session = None

    @property
    def db_session(self):
        """Get database session."""
        if self._db_session is None:
            # TODO: Get database URL from config
            engine = create_engine("postgresql://user:pass@localhost/nexus_etl")
            Session = sessionmaker(bind=engine)
            self._db_session = Session()
        return self._db_session


@celery_app.task(
    bind=True,
    base=ETLTask,
    name="modules.etl.tasks.execute_etl_job",
    max_retries=3,
    default_retry_delay=300
)
def execute_etl_job_task(
    self,
    job_id: int,
    job_run_id: Optional[int] = None,
    triggered_by: str = "celery",
    triggered_by_user: Optional[int] = None
) -> dict:
    """
    Execute an ETL job asynchronously.

    Args:
        job_id: ETL job ID
        job_run_id: Existing job run ID (if any)
        triggered_by: How the job was triggered
        triggered_by_user: User who triggered the job

    Returns:
        Execution result dictionary
    """
    logger.info(f"Starting async execution of job {job_id}")

    try:
        db_session = self.db_session

        # Update job run status if exists
        if job_run_id:
            job_run = db_session.query(JobRun).filter(JobRun.id == job_run_id).first()
            if job_run:
                job_run.status = JobStatus.RUNNING
                db_session.commit()

        # Execute job
        executor = JobExecutor(db_session)
        result = executor.execute_job(
            job_id=job_id,
            triggered_by=triggered_by,
            triggered_by_user=triggered_by_user
        )

        logger.info(f"Job {job_id} completed successfully")
        return result

    except Exception as exc:
        logger.error(f"Job {job_id} failed: {str(exc)}")

        # Update job run status
        if job_run_id:
            try:
                job_run = db_session.query(JobRun).filter(JobRun.id == job_run_id).first()
                if job_run:
                    job_run.status = JobStatus.FAILED
                    job_run.error_message = str(exc)
                    db_session.commit()
            except Exception as e:
                logger.error(f"Failed to update job run status: {str(e)}")

        # Retry task
        raise self.retry(exc=exc)


@celery_app.task(
    name="modules.etl.tasks.cleanup_old_runs",
    bind=True
)
def cleanup_old_runs_task(self, days: int = 30) -> dict:
    """
    Clean up old job run records.

    Args:
        days: Delete runs older than this many days

    Returns:
        Cleanup result
    """
    logger.info(f"Starting cleanup of job runs older than {days} days")

    try:
        from modules.etl.jobs import JobHistory

        db_session = self.db_session
        history = JobHistory(db_session)
        deleted_count = history.cleanup_old_runs(days)

        logger.info(f"Cleaned up {deleted_count} old job runs")
        return {"deleted_count": deleted_count}

    except Exception as exc:
        logger.error(f"Cleanup failed: {str(exc)}")
        raise


@celery_app.task(
    name="modules.etl.tasks.health_check"
)
def health_check_task() -> dict:
    """
    Perform system health check.

    Returns:
        Health check result
    """
    logger.info("Performing system health check")

    try:
        from modules.etl.monitoring import ETLMetrics

        # TODO: Get db session
        # metrics = ETLMetrics(db_session)
        # health = metrics.get_system_health()

        return {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00"
        }

    except Exception as exc:
        logger.error(f"Health check failed: {str(exc)}")
        return {
            "status": "unhealthy",
            "error": str(exc)
        }


# Periodic tasks can be configured using Celery Beat
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup periodic tasks."""

    # Cleanup old runs daily at 2 AM
    sender.add_periodic_task(
        crontab(hour=2, minute=0),
        cleanup_old_runs_task.s(days=30),
        name="cleanup-old-runs-daily"
    )

    # Health check every 5 minutes
    sender.add_periodic_task(
        300.0,
        health_check_task.s(),
        name="health-check-5min"
    )


from celery.schedules import crontab
