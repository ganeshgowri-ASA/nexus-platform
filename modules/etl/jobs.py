"""
Job scheduling and execution for ETL module.

This module provides job scheduling, execution, monitoring,
and history management.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from croniter import croniter

from modules.etl.models import ETLJob, JobRun, JobStatus
from modules.etl.pipeline import ETLPipeline

logger = logging.getLogger(__name__)


class JobException(Exception):
    """Base exception for job errors."""
    pass


class JobScheduler:
    """Manages scheduling of ETL jobs."""

    def __init__(self, db_url: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize job scheduler.

        Args:
            db_url: Database URL for job store
            config: Configuration options
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Initialize APScheduler
        jobstores = {
            'default': SQLAlchemyJobStore(url=db_url)
        }

        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            timezone="UTC"
        )

    def start(self) -> None:
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            self.logger.info("Job scheduler started")

    def stop(self) -> None:
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.logger.info("Job scheduler stopped")

    def schedule_job(
        self,
        job: ETLJob,
        db_session: Any,
        executor_func: Optional[Any] = None
    ) -> str:
        """
        Schedule an ETL job.

        Args:
            job: ETL job to schedule
            db_session: Database session
            executor_func: Function to execute the job

        Returns:
            Scheduled job ID
        """
        if not job.schedule_cron:
            raise JobException("Job has no schedule defined")

        # Validate cron expression
        if not croniter.is_valid(job.schedule_cron):
            raise JobException(f"Invalid cron expression: {job.schedule_cron}")

        # Create trigger
        trigger = CronTrigger.from_crontab(job.schedule_cron, timezone="UTC")

        # Schedule job
        scheduled_job = self.scheduler.add_job(
            func=executor_func or self._execute_job_wrapper,
            trigger=trigger,
            args=[job.id, db_session],
            id=f"etl_job_{job.id}",
            name=job.name,
            replace_existing=True
        )

        self.logger.info(f"Scheduled job: {job.name} with schedule: {job.schedule_cron}")
        return scheduled_job.id

    def unschedule_job(self, job_id: int) -> None:
        """
        Unschedule an ETL job.

        Args:
            job_id: Job ID to unschedule
        """
        scheduler_job_id = f"etl_job_{job_id}"
        if self.scheduler.get_job(scheduler_job_id):
            self.scheduler.remove_job(scheduler_job_id)
            self.logger.info(f"Unscheduled job: {job_id}")

    def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """
        Get list of all scheduled jobs.

        Returns:
            List of scheduled job information
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        return jobs

    def _execute_job_wrapper(self, job_id: int, db_session: Any) -> None:
        """Wrapper to execute job from scheduler."""
        try:
            job = db_session.query(ETLJob).filter(ETLJob.id == job_id).first()
            if job and job.is_active:
                executor = JobExecutor(db_session)
                executor.execute_job(job_id, triggered_by="schedule")
        except Exception as e:
            self.logger.error(f"Error executing scheduled job {job_id}: {str(e)}")


class JobExecutor:
    """Executes ETL jobs."""

    def __init__(self, db_session: Any, config: Optional[Dict[str, Any]] = None):
        """
        Initialize job executor.

        Args:
            db_session: Database session
            config: Configuration options
        """
        self.db_session = db_session
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

    def execute_job(
        self,
        job_id: int,
        triggered_by: str = "manual",
        triggered_by_user: Optional[int] = None,
        execution_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute an ETL job.

        Args:
            job_id: Job ID to execute
            triggered_by: How the job was triggered
            triggered_by_user: User who triggered the job
            execution_context: Additional execution context

        Returns:
            Execution result dictionary
        """
        try:
            # Get job
            job = self.db_session.query(ETLJob).filter(ETLJob.id == job_id).first()
            if not job:
                raise JobException(f"Job not found: {job_id}")

            if not job.is_active:
                raise JobException(f"Job is not active: {job_id}")

            self.logger.info(f"Executing job: {job.name}")

            # Create pipeline configuration
            pipeline_config = {
                "triggered_by": triggered_by,
                "triggered_by_user": triggered_by_user,
                "execution_context": execution_context or {},
                **(self.config or {})
            }

            # Execute pipeline
            pipeline = ETLPipeline(job, self.db_session, pipeline_config)
            result = pipeline.execute()

            # Update job last run time
            job.last_run_at = datetime.utcnow()
            self.db_session.commit()

            return result

        except Exception as e:
            self.logger.error(f"Job execution failed: {str(e)}")
            raise

    def execute_job_async(
        self,
        job_id: int,
        triggered_by: str = "manual",
        triggered_by_user: Optional[int] = None
    ) -> int:
        """
        Execute job asynchronously using Celery.

        Args:
            job_id: Job ID to execute
            triggered_by: How the job was triggered
            triggered_by_user: User who triggered the job

        Returns:
            Job run ID
        """
        # Import here to avoid circular dependency
        from modules.etl.tasks import execute_etl_job_task

        # Create job run record
        job = self.db_session.query(ETLJob).filter(ETLJob.id == job_id).first()
        if not job:
            raise JobException(f"Job not found: {job_id}")

        job_run = JobRun(
            job_id=job_id,
            status=JobStatus.PENDING,
            triggered_by=triggered_by,
            triggered_by_user=triggered_by_user
        )
        self.db_session.add(job_run)
        self.db_session.commit()

        # Submit to Celery
        execute_etl_job_task.delay(job_id, job_run.id, triggered_by, triggered_by_user)

        self.logger.info(f"Submitted job {job_id} for async execution, run ID: {job_run.id}")
        return job_run.id


class JobMonitor:
    """Monitors ETL job execution."""

    def __init__(self, db_session: Any):
        """
        Initialize job monitor.

        Args:
            db_session: Database session
        """
        self.db_session = db_session
        self.logger = logging.getLogger(__name__)

    def get_job_status(self, job_id: int) -> Dict[str, Any]:
        """
        Get current status of a job.

        Args:
            job_id: Job ID

        Returns:
            Job status information
        """
        job = self.db_session.query(ETLJob).filter(ETLJob.id == job_id).first()
        if not job:
            raise JobException(f"Job not found: {job_id}")

        # Get latest run
        latest_run = (
            self.db_session.query(JobRun)
            .filter(JobRun.job_id == job_id)
            .order_by(JobRun.created_at.desc())
            .first()
        )

        return {
            "job_id": job.id,
            "job_name": job.name,
            "is_active": job.is_active,
            "is_scheduled": job.is_scheduled,
            "schedule": job.schedule_cron,
            "last_run_at": job.last_run_at.isoformat() if job.last_run_at else None,
            "last_run_status": latest_run.status.value if latest_run else None,
            "last_run_duration": latest_run.duration_seconds if latest_run else None
        }

    def get_running_jobs(self) -> List[Dict[str, Any]]:
        """
        Get list of currently running jobs.

        Returns:
            List of running jobs
        """
        running_runs = (
            self.db_session.query(JobRun)
            .filter(JobRun.status == JobStatus.RUNNING)
            .all()
        )

        jobs = []
        for run in running_runs:
            jobs.append({
                "job_run_id": run.id,
                "job_id": run.job_id,
                "job_name": run.job.name if run.job else None,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "duration": (datetime.utcnow() - run.started_at).total_seconds() if run.started_at else None
            })

        return jobs

    def get_job_metrics(self, job_id: int, days: int = 7) -> Dict[str, Any]:
        """
        Get metrics for a job over a time period.

        Args:
            job_id: Job ID
            days: Number of days to include

        Returns:
            Job metrics
        """
        since = datetime.utcnow() - timedelta(days=days)

        runs = (
            self.db_session.query(JobRun)
            .filter(JobRun.job_id == job_id)
            .filter(JobRun.created_at >= since)
            .all()
        )

        if not runs:
            return {
                "job_id": job_id,
                "period_days": days,
                "total_runs": 0
            }

        total_runs = len(runs)
        successful_runs = len([r for r in runs if r.status == JobStatus.COMPLETED])
        failed_runs = len([r for r in runs if r.status == JobStatus.FAILED])

        # Calculate averages
        completed_runs = [r for r in runs if r.status == JobStatus.COMPLETED and r.duration_seconds]
        avg_duration = (
            sum(r.duration_seconds for r in completed_runs) / len(completed_runs)
            if completed_runs else 0
        )

        total_records_processed = sum(r.records_loaded or 0 for r in completed_runs)

        return {
            "job_id": job_id,
            "period_days": days,
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "success_rate": (successful_runs / total_runs * 100) if total_runs > 0 else 0,
            "avg_duration_seconds": avg_duration,
            "total_records_processed": total_records_processed,
            "avg_records_per_run": (
                total_records_processed / len(completed_runs)
                if completed_runs else 0
            )
        }


class JobHistory:
    """Manages job execution history."""

    def __init__(self, db_session: Any):
        """
        Initialize job history manager.

        Args:
            db_session: Database session
        """
        self.db_session = db_session
        self.logger = logging.getLogger(__name__)

    def get_job_runs(
        self,
        job_id: Optional[int] = None,
        status: Optional[JobStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[JobRun]:
        """
        Get job run history.

        Args:
            job_id: Filter by job ID
            status: Filter by status
            limit: Maximum number of runs to return
            offset: Number of runs to skip

        Returns:
            List of job runs
        """
        query = self.db_session.query(JobRun)

        if job_id:
            query = query.filter(JobRun.job_id == job_id)

        if status:
            query = query.filter(JobRun.status == status)

        query = query.order_by(JobRun.created_at.desc())
        query = query.limit(limit).offset(offset)

        return query.all()

    def get_job_run_details(self, run_id: int) -> Optional[JobRun]:
        """
        Get detailed information about a job run.

        Args:
            run_id: Job run ID

        Returns:
            JobRun object or None
        """
        return self.db_session.query(JobRun).filter(JobRun.id == run_id).first()

    def cleanup_old_runs(self, days: int = 30) -> int:
        """
        Clean up old job run records.

        Args:
            days: Delete runs older than this many days

        Returns:
            Number of deleted runs
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        deleted = (
            self.db_session.query(JobRun)
            .filter(JobRun.created_at < cutoff_date)
            .filter(JobRun.status.in_([JobStatus.COMPLETED, JobStatus.FAILED]))
            .delete(synchronize_session=False)
        )

        self.db_session.commit()
        self.logger.info(f"Cleaned up {deleted} old job runs")

        return deleted

    def get_execution_timeline(
        self,
        job_id: int,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get execution timeline for a job.

        Args:
            job_id: Job ID
            days: Number of days to include

        Returns:
            Timeline data
        """
        since = datetime.utcnow() - timedelta(days=days)

        runs = (
            self.db_session.query(JobRun)
            .filter(JobRun.job_id == job_id)
            .filter(JobRun.created_at >= since)
            .order_by(JobRun.created_at)
            .all()
        )

        timeline = []
        for run in runs:
            timeline.append({
                "run_id": run.id,
                "status": run.status.value,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "duration": run.duration_seconds,
                "records_loaded": run.records_loaded,
                "error_message": run.error_message
            })

        return timeline

    def compare_runs(self, run_id1: int, run_id2: int) -> Dict[str, Any]:
        """
        Compare two job runs.

        Args:
            run_id1: First run ID
            run_id2: Second run ID

        Returns:
            Comparison data
        """
        run1 = self.get_job_run_details(run_id1)
        run2 = self.get_job_run_details(run_id2)

        if not run1 or not run2:
            raise JobException("One or both runs not found")

        return {
            "run1": {
                "id": run1.id,
                "status": run1.status.value,
                "duration": run1.duration_seconds,
                "records_loaded": run1.records_loaded,
                "data_quality_score": run1.data_quality_score
            },
            "run2": {
                "id": run2.id,
                "status": run2.status.value,
                "duration": run2.duration_seconds,
                "records_loaded": run2.records_loaded,
                "data_quality_score": run2.data_quality_score
            },
            "differences": {
                "duration_diff": (run2.duration_seconds or 0) - (run1.duration_seconds or 0),
                "records_diff": (run2.records_loaded or 0) - (run1.records_loaded or 0),
                "quality_diff": (run2.data_quality_score or 0) - (run1.data_quality_score or 0)
            }
        }
