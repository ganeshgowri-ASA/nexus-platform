"""
Notification scheduler
Handles scheduled and delayed notifications
"""
from datetime import datetime, timedelta
from typing import Optional, List
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.models.notification import Notification, NotificationStatus


class NotificationScheduler:
    """
    Notification scheduler
    Processes scheduled notifications and sends them at the appropriate time
    """

    def __init__(self, check_interval_seconds: int = 60):
        """
        Initialize scheduler

        Args:
            check_interval_seconds: How often to check for pending notifications (default: 60s)
        """
        self.check_interval = check_interval_seconds
        self.running = False
        self.task = None

    async def start(self, db: Session, notification_service):
        """
        Start the scheduler

        Args:
            db: Database session
            notification_service: NotificationService instance for sending notifications
        """
        if self.running:
            return

        self.running = True
        self.task = asyncio.create_task(self._run_scheduler(db, notification_service))

    async def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

    async def _run_scheduler(self, db: Session, notification_service):
        """
        Main scheduler loop
        Continuously checks for and processes scheduled notifications
        """
        while self.running:
            try:
                await self.process_scheduled_notifications(db, notification_service)
            except Exception as e:
                print(f"Scheduler error: {str(e)}")

            # Wait before next check
            await asyncio.sleep(self.check_interval)

    async def process_scheduled_notifications(self, db: Session, notification_service):
        """
        Process all notifications scheduled for sending

        Args:
            db: Database session
            notification_service: NotificationService instance
        """
        # Get notifications that are scheduled and due
        now = datetime.utcnow()
        due_notifications = db.query(Notification).filter(
            and_(
                Notification.status == NotificationStatus.SCHEDULED,
                Notification.scheduled_at <= now
            )
        ).all()

        # Send each notification
        for notification in due_notifications:
            try:
                # Update status to processing
                notification.status = NotificationStatus.PROCESSING
                db.commit()

                # Send the notification
                await notification_service.send_notification(
                    notification_id=notification.id,
                    db=db
                )

            except Exception as e:
                # Mark as failed if there's an error
                notification.status = NotificationStatus.FAILED
                notification.last_error = str(e)
                db.commit()
                print(f"Failed to send scheduled notification {notification.id}: {str(e)}")

    def schedule_notification(
        self,
        db: Session,
        notification_id: str,
        scheduled_time: datetime
    ) -> bool:
        """
        Schedule a notification for later delivery

        Args:
            db: Database session
            notification_id: Notification ID to schedule
            scheduled_time: When to send the notification

        Returns:
            True if scheduled successfully
        """
        try:
            notification = db.query(Notification).filter(
                Notification.id == notification_id
            ).first()

            if not notification:
                return False

            notification.scheduled_at = scheduled_time
            notification.status = NotificationStatus.SCHEDULED
            db.commit()

            return True

        except Exception as e:
            db.rollback()
            print(f"Failed to schedule notification: {str(e)}")
            return False

    def reschedule_notification(
        self,
        db: Session,
        notification_id: str,
        new_scheduled_time: datetime
    ) -> bool:
        """
        Reschedule a notification

        Args:
            db: Database session
            notification_id: Notification ID
            new_scheduled_time: New scheduled time

        Returns:
            True if rescheduled successfully
        """
        return self.schedule_notification(db, notification_id, new_scheduled_time)

    def cancel_scheduled_notification(
        self,
        db: Session,
        notification_id: str
    ) -> bool:
        """
        Cancel a scheduled notification

        Args:
            db: Database session
            notification_id: Notification ID to cancel

        Returns:
            True if cancelled successfully
        """
        try:
            notification = db.query(Notification).filter(
                Notification.id == notification_id,
                Notification.status == NotificationStatus.SCHEDULED
            ).first()

            if not notification:
                return False

            notification.status = NotificationStatus.CANCELLED
            db.commit()

            return True

        except Exception as e:
            db.rollback()
            print(f"Failed to cancel notification: {str(e)}")
            return False

    def get_scheduled_notifications(
        self,
        db: Session,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Notification]:
        """
        Get scheduled notifications

        Args:
            db: Database session
            user_id: Optional user ID to filter by
            limit: Maximum number to return

        Returns:
            List of scheduled notifications
        """
        query = db.query(Notification).filter(
            Notification.status == NotificationStatus.SCHEDULED
        )

        if user_id:
            query = query.filter(Notification.user_id == user_id)

        return query.order_by(Notification.scheduled_at).limit(limit).all()

    def schedule_bulk_notifications(
        self,
        db: Session,
        notification_ids: List[str],
        scheduled_time: datetime
    ) -> Dict[str, bool]:
        """
        Schedule multiple notifications at once

        Args:
            db: Database session
            notification_ids: List of notification IDs
            scheduled_time: When to send

        Returns:
            Dictionary mapping notification_id to success status
        """
        results = {}

        for notification_id in notification_ids:
            results[notification_id] = self.schedule_notification(
                db, notification_id, scheduled_time
            )

        return results

    def schedule_recurring_notification(
        self,
        db: Session,
        template_id: str,
        user_id: str,
        recipient: str,
        channel: str,
        interval_hours: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> str:
        """
        Schedule a recurring notification
        (This is a placeholder - full implementation would require a job scheduler)

        Args:
            db: Database session
            template_id: Template to use
            user_id: User ID
            recipient: Recipient identifier
            channel: Notification channel
            interval_hours: Hours between notifications
            start_time: When to start (default: now)
            end_time: When to stop (optional)

        Returns:
            Job ID for the recurring notification
        """
        # This would typically use a job scheduler like APScheduler or Celery
        # For now, return a placeholder
        return f"recurring_{datetime.utcnow().timestamp()}"
