"""Email scheduler for scheduling email delivery."""

from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.memory import MemoryJobStore
import logging

from sqlalchemy.orm import Session

from src.modules.email.models import Email, EmailStatus

logger = logging.getLogger(__name__)


class EmailScheduler:
    """Scheduler for email delivery."""

    def __init__(self, db: Optional[Session] = None):
        """Initialize email scheduler.

        Args:
            db: Database session
        """
        self.db = db
        self._scheduler = BackgroundScheduler(
            jobstores={'default': MemoryJobStore()},
            timezone='UTC'
        )
        self._is_running = False

    def start(self):
        """Start the scheduler."""
        if not self._is_running:
            self._scheduler.start()
            self._is_running = True
            logger.info("Email scheduler started")

    def stop(self):
        """Stop the scheduler."""
        if self._is_running:
            self._scheduler.shutdown()
            self._is_running = False
            logger.info("Email scheduler stopped")

    def schedule_email(
        self,
        send_function: Callable,
        send_at: datetime,
        email_id: Optional[int] = None,
        **kwargs
    ) -> str:
        """Schedule an email to be sent at a specific time.

        Args:
            send_function: Function to call to send email
            send_at: When to send the email
            email_id: Email ID (for database tracking)
            **kwargs: Arguments to pass to send_function

        Returns:
            Job ID
        """
        if send_at <= datetime.utcnow():
            raise ValueError("Scheduled time must be in the future")

        # Ensure scheduler is running
        if not self._is_running:
            self.start()

        # Create wrapper function for tracking
        def wrapped_send():
            logger.info(f"Sending scheduled email (ID: {email_id})")
            try:
                result = send_function(**kwargs)

                # Update email status in database
                if self.db and email_id:
                    email = self.db.query(Email).filter_by(id=email_id).first()
                    if email:
                        email.status = EmailStatus.SENT.value
                        email.sent_at = datetime.utcnow()
                        self.db.commit()

                logger.info(f"Scheduled email sent successfully (ID: {email_id})")
                return result

            except Exception as e:
                logger.error(f"Failed to send scheduled email: {e}")

                # Update email status to failed
                if self.db and email_id:
                    email = self.db.query(Email).filter_by(id=email_id).first()
                    if email:
                        email.status = EmailStatus.FAILED.value
                        self.db.commit()

                raise

        # Schedule the job
        job = self._scheduler.add_job(
            wrapped_send,
            trigger=DateTrigger(run_date=send_at),
            id=f"email_{email_id}_{send_at.timestamp()}" if email_id else None,
            replace_existing=True
        )

        # Update email status in database
        if self.db and email_id:
            email = self.db.query(Email).filter_by(id=email_id).first()
            if email:
                email.status = EmailStatus.SCHEDULED.value
                email.scheduled_at = send_at
                self.db.commit()

        logger.info(f"Scheduled email for {send_at} (Job ID: {job.id})")
        return job.id

    def schedule_recurring(
        self,
        send_function: Callable,
        interval: Optional[timedelta] = None,
        cron: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        **kwargs
    ) -> str:
        """Schedule a recurring email.

        Args:
            send_function: Function to call to send email
            interval: Interval between sends (e.g., timedelta(hours=24))
            cron: Cron expression (e.g., '0 9 * * *' for 9 AM daily)
            start_date: When to start sending
            end_date: When to stop sending
            **kwargs: Arguments to pass to send_function

        Returns:
            Job ID
        """
        if not interval and not cron:
            raise ValueError("Either interval or cron must be provided")

        # Ensure scheduler is running
        if not self._is_running:
            self.start()

        # Determine trigger
        if cron:
            trigger = CronTrigger.from_crontab(
                cron,
                timezone='UTC'
            )
        else:
            trigger = IntervalTrigger(
                seconds=interval.total_seconds(),
                start_date=start_date or datetime.utcnow(),
                end_date=end_date,
                timezone='UTC'
            )

        # Schedule the job
        job = self._scheduler.add_job(
            send_function,
            trigger=trigger,
            kwargs=kwargs,
            replace_existing=False
        )

        logger.info(f"Scheduled recurring email (Job ID: {job.id})")
        return job.id

    def cancel_scheduled_email(self, job_id: str) -> bool:
        """Cancel a scheduled email.

        Args:
            job_id: Job ID to cancel

        Returns:
            True if cancelled successfully
        """
        try:
            self._scheduler.remove_job(job_id)
            logger.info(f"Cancelled scheduled email: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel scheduled email: {e}")
            return False

    def reschedule_email(
        self,
        job_id: str,
        new_send_at: datetime
    ) -> bool:
        """Reschedule an email.

        Args:
            job_id: Job ID to reschedule
            new_send_at: New send time

        Returns:
            True if rescheduled successfully
        """
        try:
            self._scheduler.reschedule_job(
                job_id,
                trigger=DateTrigger(run_date=new_send_at)
            )
            logger.info(f"Rescheduled email {job_id} to {new_send_at}")
            return True
        except Exception as e:
            logger.error(f"Failed to reschedule email: {e}")
            return False

    def get_scheduled_jobs(self) -> list:
        """Get all scheduled jobs.

        Returns:
            List of job info dicts
        """
        jobs = []
        for job in self._scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time,
                'trigger': str(job.trigger)
            })
        return jobs

    def pause_job(self, job_id: str) -> bool:
        """Pause a scheduled job.

        Args:
            job_id: Job ID to pause

        Returns:
            True if paused successfully
        """
        try:
            self._scheduler.pause_job(job_id)
            logger.info(f"Paused job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to pause job: {e}")
            return False

    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job.

        Args:
            job_id: Job ID to resume

        Returns:
            True if resumed successfully
        """
        try:
            self._scheduler.resume_job(job_id)
            logger.info(f"Resumed job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to resume job: {e}")
            return False

    def schedule_batch(
        self,
        send_function: Callable,
        emails: list,
        send_at: datetime,
        batch_size: int = 50,
        interval_seconds: int = 5
    ) -> list:
        """Schedule a batch of emails with staggered sending.

        Args:
            send_function: Function to call to send email
            emails: List of email data dicts
            send_at: When to start sending
            batch_size: Emails per batch
            interval_seconds: Seconds between batches

        Returns:
            List of job IDs
        """
        job_ids = []
        current_time = send_at

        for i in range(0, len(emails), batch_size):
            batch = emails[i:i + batch_size]

            # Create batch send function
            def send_batch(batch_data=batch):
                for email_data in batch_data:
                    try:
                        send_function(**email_data)
                    except Exception as e:
                        logger.error(f"Failed to send email in batch: {e}")

            # Schedule batch
            job = self._scheduler.add_job(
                send_batch,
                trigger=DateTrigger(run_date=current_time),
                replace_existing=False
            )

            job_ids.append(job.id)
            logger.info(f"Scheduled batch of {len(batch)} emails for {current_time}")

            # Increment time for next batch
            current_time += timedelta(seconds=interval_seconds)

        return job_ids

    def load_pending_schedules(self):
        """Load pending scheduled emails from database."""
        if not self.db:
            logger.warning("Database session not provided")
            return

        # Get all scheduled emails
        scheduled_emails = self.db.query(Email).filter(
            Email.status == EmailStatus.SCHEDULED.value,
            Email.scheduled_at > datetime.utcnow()
        ).all()

        logger.info(f"Loading {len(scheduled_emails)} pending scheduled emails")

        for email in scheduled_emails:
            # Note: This would need the actual send function to be passed in
            # For now, just log
            logger.info(
                f"Pending scheduled email: ID={email.id}, "
                f"scheduled_at={email.scheduled_at}"
            )

    def clear_all_jobs(self):
        """Clear all scheduled jobs."""
        self._scheduler.remove_all_jobs()
        logger.info("Cleared all scheduled jobs")

    def get_job_info(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a scheduled job.

        Args:
            job_id: Job ID

        Returns:
            Job info dict or None
        """
        try:
            job = self._scheduler.get_job(job_id)
            if job:
                return {
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time,
                    'trigger': str(job.trigger),
                    'pending': job.pending
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get job info: {e}")
            return None

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
