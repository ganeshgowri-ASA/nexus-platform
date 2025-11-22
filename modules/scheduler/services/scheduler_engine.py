"""Core scheduler engine using APScheduler"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.redis import RedisJobStore
from datetime import datetime
from typing import Optional
import pytz
from modules.scheduler.config import settings
from modules.scheduler.models.schemas import ScheduledJob, JobType


class SchedulerEngine:
    """Singleton scheduler engine"""

    _instance = None
    _scheduler = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_scheduler()
        return cls._instance

    def _initialize_scheduler(self):
        """Initialize APScheduler"""
        if self._scheduler is None:
            jobstores = {
                'default': RedisJobStore(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB
                )
            }

            job_defaults = {
                'coalesce': True,
                'max_instances': 3,
                'misfire_grace_time': 300
            }

            self._scheduler = AsyncIOScheduler(
                jobstores=jobstores,
                job_defaults=job_defaults,
                timezone=pytz.timezone(settings.DEFAULT_TIMEZONE)
            )

    def start(self):
        """Start the scheduler"""
        if self._scheduler and not self._scheduler.running:
            self._scheduler.start()

    def shutdown(self, wait: bool = True):
        """Shutdown the scheduler"""
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown(wait=wait)

    async def register_job(self, job: ScheduledJob) -> str:
        """Register a job with the scheduler"""
        if not job.is_active:
            return None

        # Create trigger based on job type
        trigger = self._create_trigger(job)
        if not trigger:
            return None

        # Add job to scheduler
        job_id = f"job_{job.id}"

        try:
            self._scheduler.add_job(
                func=self._execute_job_callback,
                trigger=trigger,
                id=job_id,
                args=[job.id],
                replace_existing=True,
                name=job.name
            )
            return job_id

        except Exception as e:
            print(f"Error registering job {job.id}: {e}")
            return None

    async def update_job(self, job: ScheduledJob) -> bool:
        """Update a job in the scheduler"""
        job_id = f"job_{job.id}"

        try:
            # Remove old job
            if self._scheduler.get_job(job_id):
                self._scheduler.remove_job(job_id)

            # Re-register if active
            if job.is_active:
                await self.register_job(job)

            return True

        except Exception as e:
            print(f"Error updating job {job.id}: {e}")
            return False

    async def remove_job(self, job_id: int) -> bool:
        """Remove a job from the scheduler"""
        scheduler_job_id = f"job_{job_id}"

        try:
            if self._scheduler.get_job(scheduler_job_id):
                self._scheduler.remove_job(scheduler_job_id)
            return True

        except Exception as e:
            print(f"Error removing job {job_id}: {e}")
            return False

    async def pause_job(self, job_id: int) -> bool:
        """Pause a job"""
        scheduler_job_id = f"job_{job_id}"

        try:
            if self._scheduler.get_job(scheduler_job_id):
                self._scheduler.pause_job(scheduler_job_id)
            return True

        except Exception as e:
            print(f"Error pausing job {job_id}: {e}")
            return False

    async def resume_job(self, job: ScheduledJob) -> bool:
        """Resume a paused job"""
        scheduler_job_id = f"job_{job.id}"

        try:
            if self._scheduler.get_job(scheduler_job_id):
                self._scheduler.resume_job(scheduler_job_id)
            else:
                # Re-register if not exists
                await self.register_job(job)
            return True

        except Exception as e:
            print(f"Error resuming job {job.id}: {e}")
            return False

    async def execute_job_now(
        self,
        job: ScheduledJob,
        task_args: Optional[list] = None,
        task_kwargs: Optional[dict] = None
    ) -> str:
        """Execute a job immediately"""
        from modules.scheduler.tasks.job_tasks import execute_scheduled_job
        from modules.scheduler.models import get_sync_db, JobExecution

        # Create execution record
        db = next(get_sync_db())
        try:
            execution = JobExecution(
                job_id=job.id,
                scheduled_at=datetime.utcnow(),
                attempt_number=1
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)

            # Execute task
            task = execute_scheduled_job.apply_async(
                kwargs={
                    'job_id': job.id,
                    'execution_id': execution.id,
                    'task_args': task_args,
                    'task_kwargs': task_kwargs
                }
            )

            return task.id

        finally:
            db.close()

    def _create_trigger(self, job: ScheduledJob):
        """Create appropriate trigger for job type"""
        try:
            tz = pytz.timezone(job.timezone)

            if job.job_type == JobType.CRON and job.cron_expression:
                # Parse cron expression
                parts = job.cron_expression.split()
                if len(parts) == 5:
                    minute, hour, day, month, day_of_week = parts
                    return CronTrigger(
                        minute=minute,
                        hour=hour,
                        day=day,
                        month=month,
                        day_of_week=day_of_week,
                        timezone=tz
                    )

            elif job.job_type == JobType.INTERVAL and job.interval_seconds:
                return IntervalTrigger(
                    seconds=job.interval_seconds,
                    timezone=tz
                )

            elif job.job_type == JobType.DATE and job.scheduled_time:
                return DateTrigger(
                    run_date=job.scheduled_time,
                    timezone=tz
                )

            return None

        except Exception as e:
            print(f"Error creating trigger for job {job.id}: {e}")
            return None

    def _execute_job_callback(self, job_id: int):
        """Callback function executed by APScheduler"""
        from modules.scheduler.tasks.job_tasks import execute_scheduled_job
        from modules.scheduler.models import get_sync_db, ScheduledJob, JobExecution

        db = next(get_sync_db())
        try:
            # Get job
            job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
            if not job:
                return

            # Create execution record
            execution = JobExecution(
                job_id=job_id,
                scheduled_at=datetime.utcnow(),
                attempt_number=1
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)

            # Queue task in Celery
            execute_scheduled_job.apply_async(
                kwargs={
                    'job_id': job_id,
                    'execution_id': execution.id
                },
                priority=job.priority
            )

        finally:
            db.close()

    def get_job_info(self, job_id: int) -> Optional[dict]:
        """Get job information from scheduler"""
        scheduler_job_id = f"job_{job_id}"
        job = self._scheduler.get_job(scheduler_job_id)

        if job:
            return {
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time,
                'trigger': str(job.trigger)
            }

        return None

    def get_all_jobs(self) -> list:
        """Get all jobs from scheduler"""
        jobs = self._scheduler.get_jobs()
        return [
            {
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time,
                'trigger': str(job.trigger)
            }
            for job in jobs
        ]
