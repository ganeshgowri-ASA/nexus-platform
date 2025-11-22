"""
Email Tasks for Nexus Platform
Handles all email-related background tasks
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging

from celery import Task
from config.celery_config import celery_app
from config.settings import settings

logger = logging.getLogger(__name__)


class EmailTask(Task):
    """Base class for email tasks with retry logic"""
    autoretry_for = (smtplib.SMTPException, ConnectionError)
    retry_kwargs = {'max_retries': 3, 'countdown': 60}
    retry_backoff = True


@celery_app.task(base=EmailTask, bind=True, name='app.tasks.email_tasks.send_email')
def send_email(
    self,
    to_email: str | List[str],
    subject: str,
    body: str,
    html_body: Optional[str] = None,
    attachments: Optional[List[str]] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Send email with optional HTML content and attachments

    Args:
        to_email: Recipient email(s)
        subject: Email subject
        body: Plain text body
        html_body: Optional HTML body
        attachments: List of file paths to attach
        cc: CC recipients
        bcc: BCC recipients

    Returns:
        Dict with status and message
    """
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = settings.SMTP_FROM
        msg['Subject'] = subject

        # Handle recipient lists
        if isinstance(to_email, str):
            to_email = [to_email]
        msg['To'] = ', '.join(to_email)

        if cc:
            msg['Cc'] = ', '.join(cc)
            to_email.extend(cc)

        if bcc:
            to_email.extend(bcc)

        # Attach text body
        msg.attach(MIMEText(body, 'plain'))

        # Attach HTML body if provided
        if html_body:
            msg.attach(MIMEText(html_body, 'html'))

        # Attach files if provided
        if attachments:
            for file_path in attachments:
                if Path(file_path).exists():
                    with open(file_path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename={Path(file_path).name}'
                        )
                        msg.attach(part)

        # Send email
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()

            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

            server.send_message(msg)

        logger.info(f"Email sent successfully to {to_email}")
        return {
            'status': 'success',
            'message': f'Email sent to {len(to_email)} recipient(s)',
            'recipients': to_email
        }

    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise self.retry(exc=e)


@celery_app.task(name='app.tasks.email_tasks.send_bulk_emails')
def send_bulk_emails(email_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Send bulk emails using a list of email configurations

    Args:
        email_list: List of dicts with email parameters

    Returns:
        Dict with results summary
    """
    results = {
        'total': len(email_list),
        'success': 0,
        'failed': 0,
        'task_ids': []
    }

    for email_data in email_list:
        try:
            task = send_email.delay(**email_data)
            results['task_ids'].append(task.id)
            results['success'] += 1
        except Exception as e:
            logger.error(f"Failed to queue email: {str(e)}")
            results['failed'] += 1

    return results


@celery_app.task(name='app.tasks.email_tasks.send_notification')
def send_notification(
    user_email: str,
    notification_type: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Send templated notification email

    Args:
        user_email: Recipient email
        notification_type: Type of notification (task_complete, error, report_ready, etc.)
        context: Context data for email template

    Returns:
        Result dict
    """
    # Email templates
    templates = {
        'task_complete': {
            'subject': 'Task Completed - {task_name}',
            'body': 'Your task "{task_name}" has been completed successfully.\n\nDetails:\n{details}'
        },
        'task_failed': {
            'subject': 'Task Failed - {task_name}',
            'body': 'Your task "{task_name}" has failed.\n\nError: {error}\n\nPlease try again or contact support.'
        },
        'report_ready': {
            'subject': 'Report Ready - {report_name}',
            'body': 'Your report "{report_name}" is ready for download.\n\nGenerated at: {timestamp}'
        },
        'file_processed': {
            'subject': 'File Processing Complete - {file_name}',
            'body': 'Your file "{file_name}" has been processed successfully.\n\nResults: {results}'
        }
    }

    template = templates.get(notification_type)
    if not template:
        raise ValueError(f"Unknown notification type: {notification_type}")

    subject = template['subject'].format(**context)
    body = template['body'].format(**context)

    return send_email(
        to_email=user_email,
        subject=subject,
        body=body
    )


@celery_app.task(name='app.tasks.email_tasks.send_scheduled_email')
def send_scheduled_email(
    to_email: str,
    subject: str,
    body: str,
    schedule_time: str
) -> Dict[str, Any]:
    """
    Send email at scheduled time (using ETA)

    Args:
        to_email: Recipient email
        subject: Email subject
        body: Email body
        schedule_time: ISO format timestamp

    Returns:
        Task info
    """
    from datetime import datetime

    eta = datetime.fromisoformat(schedule_time)
    task = send_email.apply_async(
        args=[to_email, subject, body],
        eta=eta
    )

    return {
        'status': 'scheduled',
        'task_id': task.id,
        'scheduled_for': schedule_time
    }
