"""Notification service for job events"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import httpx
from modules.scheduler.config import settings
from modules.scheduler.models.schemas import (
    ScheduledJob, JobExecution, JobNotification, NotificationChannel
)


class NotificationService:
    """Service for sending job notifications"""

    @staticmethod
    def send_notification(
        job: ScheduledJob,
        execution: JobExecution,
        event: str,
        db
    ):
        """Send notifications for job event"""
        # Get active notifications for this job and event
        notifications = db.query(JobNotification).filter(
            JobNotification.job_id == job.id,
            JobNotification.is_active == True
        ).all()

        for notification in notifications:
            # Check if notification should be sent for this event
            should_send = False
            if event == "start" and notification.on_start:
                should_send = True
            elif event == "success" and notification.on_success:
                should_send = True
            elif event == "failure" and notification.on_failure:
                should_send = True
            elif event == "retry" and notification.on_retry:
                should_send = True

            if not should_send:
                continue

            # Send notification based on channel
            try:
                if notification.channel == NotificationChannel.EMAIL:
                    NotificationService._send_email(
                        notification, job, execution, event
                    )
                elif notification.channel == NotificationChannel.TELEGRAM:
                    NotificationService._send_telegram(
                        notification, job, execution, event
                    )
                elif notification.channel == NotificationChannel.WEBHOOK:
                    NotificationService._send_webhook(
                        notification, job, execution, event
                    )

            except Exception as e:
                print(f"Error sending notification: {e}")

    @staticmethod
    def _send_email(
        notification: JobNotification,
        job: ScheduledJob,
        execution: JobExecution,
        event: str
    ):
        """Send email notification"""
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            return

        # Create message
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_USER
        msg['To'] = notification.recipient
        msg['Subject'] = f"Job {event.upper()}: {job.name}"

        # Create body
        if notification.message_template:
            body = notification.message_template.format(
                job_name=job.name,
                event=event,
                status=execution.status,
                started_at=execution.started_at,
                completed_at=execution.completed_at,
                error_message=execution.error_message or ""
            )
        else:
            body = f"""
Job: {job.name}
Event: {event.upper()}
Status: {execution.status}
Started: {execution.started_at}
Completed: {execution.completed_at}
Error: {execution.error_message or "None"}
            """

        msg.attach(MIMEText(body, 'plain'))

        # Send email
        try:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
        except Exception as e:
            print(f"Error sending email: {e}")

    @staticmethod
    def _send_telegram(
        notification: JobNotification,
        job: ScheduledJob,
        execution: JobExecution,
        event: str
    ):
        """Send Telegram notification"""
        if not settings.TELEGRAM_BOT_TOKEN:
            return

        # Create message
        if notification.message_template:
            message = notification.message_template.format(
                job_name=job.name,
                event=event,
                status=execution.status,
                started_at=execution.started_at,
                completed_at=execution.completed_at,
                error_message=execution.error_message or ""
            )
        else:
            message = f"""
🤖 Job {event.upper()}

📋 Job: {job.name}
📊 Status: {execution.status}
⏰ Started: {execution.started_at}
✅ Completed: {execution.completed_at}
❌ Error: {execution.error_message or "None"}
            """

        # Send via Telegram API
        try:
            url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
            data = {
                "chat_id": notification.recipient,
                "text": message,
                "parse_mode": "Markdown"
            }
            httpx.post(url, json=data)
        except Exception as e:
            print(f"Error sending Telegram message: {e}")

    @staticmethod
    def _send_webhook(
        notification: JobNotification,
        job: ScheduledJob,
        execution: JobExecution,
        event: str
    ):
        """Send webhook notification"""
        # Prepare payload
        payload = {
            "event": event,
            "job": {
                "id": job.id,
                "name": job.name,
                "type": job.job_type,
                "status": job.status
            },
            "execution": {
                "id": execution.id,
                "status": execution.status,
                "started_at": str(execution.started_at),
                "completed_at": str(execution.completed_at),
                "duration_seconds": execution.duration_seconds,
                "error_message": execution.error_message
            }
        }

        # Send webhook
        try:
            headers = notification.config.get("headers", {})
            httpx.post(
                notification.recipient,
                json=payload,
                headers=headers,
                timeout=10
            )
        except Exception as e:
            print(f"Error sending webhook: {e}")
