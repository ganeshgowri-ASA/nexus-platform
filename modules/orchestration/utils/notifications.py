"""Notification system for workflow events."""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx
from slack_sdk.webhook.async_client import AsyncWebhookClient

from ..config.settings import settings
from ..db.models import WorkflowExecution, WorkflowStatus

logger = logging.getLogger(__name__)


class BaseNotifier(ABC):
    """Base class for notifiers."""

    @abstractmethod
    async def send(self, message: Dict[str, Any]) -> bool:
        """Send notification."""
        pass


class EmailNotifier(BaseNotifier):
    """Email notifier using SMTP."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.to_addresses = config.get("to", [])
        self.subject_prefix = config.get("subject_prefix", "[NEXUS Workflow]")

    async def send(self, message: Dict[str, Any]) -> bool:
        """Send email notification."""
        if not settings.SMTP_HOST:
            logger.warning("SMTP not configured, skipping email notification")
            return False

        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = settings.SMTP_FROM
            msg["To"] = ", ".join(self.to_addresses)
            msg["Subject"] = f"{self.subject_prefix} {message.get('subject', 'Notification')}"

            # Create email body
            body = self._format_message(message)
            msg.attach(MIMEText(body, "html"))

            # Send email
            async with aiosmtplib.SMTP(
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                use_tls=True,
            ) as smtp:
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    await smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

                await smtp.send_message(msg)

            logger.info(f"Email notification sent to {self.to_addresses}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False

    def _format_message(self, message: Dict[str, Any]) -> str:
        """Format message as HTML."""
        status = message.get("status", "unknown")
        workflow_name = message.get("workflow_name", "Unknown")
        run_id = message.get("run_id", "")
        duration = message.get("duration", 0)
        error = message.get("error", "")

        status_color = {
            "completed": "#28a745",
            "failed": "#dc3545",
            "running": "#007bff",
        }.get(status, "#6c757d")

        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: {status_color};">Workflow {status.upper()}</h2>
                <table style="border-collapse: collapse; width: 100%;">
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Workflow:</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{workflow_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Run ID:</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{run_id}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Status:</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd; color: {status_color};">{status.upper()}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Duration:</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{duration:.2f} seconds</td>
                    </tr>
        """

        if error:
            html += f"""
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Error:</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd; color: #dc3545;">{error}</td>
                    </tr>
            """

        html += """
                </table>
            </body>
        </html>
        """

        return html


class SlackNotifier(BaseNotifier):
    """Slack notifier using webhooks."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.webhook_url = config.get("webhook_url") or settings.SLACK_WEBHOOK_URL

    async def send(self, message: Dict[str, Any]) -> bool:
        """Send Slack notification."""
        if not self.webhook_url:
            logger.warning("Slack webhook not configured, skipping notification")
            return False

        try:
            client = AsyncWebhookClient(self.webhook_url)

            status = message.get("status", "unknown")
            workflow_name = message.get("workflow_name", "Unknown")
            run_id = message.get("run_id", "")
            duration = message.get("duration", 0)
            error = message.get("error", "")

            # Status emoji
            status_emoji = {
                "completed": ":white_check_mark:",
                "failed": ":x:",
                "running": ":arrow_forward:",
            }.get(status, ":question:")

            # Create Slack message
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{status_emoji} Workflow {status.upper()}",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Workflow:*\n{workflow_name}"},
                        {"type": "mrkdwn", "text": f"*Run ID:*\n{run_id}"},
                        {"type": "mrkdwn", "text": f"*Status:*\n{status.upper()}"},
                        {
                            "type": "mrkdwn",
                            "text": f"*Duration:*\n{duration:.2f}s",
                        },
                    ],
                },
            ]

            if error:
                blocks.append(
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*Error:*\n```{error}```"},
                    }
                )

            response = await client.send(blocks=blocks)

            logger.info("Slack notification sent successfully")
            return response.status_code == 200

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False


class WebhookNotifier(BaseNotifier):
    """Generic webhook notifier."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.url = config.get("url")
        self.headers = config.get("headers", {})
        self.method = config.get("method", "POST").upper()

    async def send(self, message: Dict[str, Any]) -> bool:
        """Send webhook notification."""
        if not self.url:
            logger.warning("Webhook URL not configured, skipping notification")
            return False

        try:
            async with httpx.AsyncClient() as client:
                if self.method == "POST":
                    response = await client.post(
                        self.url, json=message, headers=self.headers
                    )
                elif self.method == "PUT":
                    response = await client.put(
                        self.url, json=message, headers=self.headers
                    )
                else:
                    response = await client.get(self.url, headers=self.headers)

                response.raise_for_status()

                logger.info(f"Webhook notification sent to {self.url}")
                return True

        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
            return False


class NotificationManager:
    """Manager for sending notifications."""

    NOTIFIER_TYPES = {
        "email": EmailNotifier,
        "slack": SlackNotifier,
        "webhook": WebhookNotifier,
    }

    @classmethod
    async def send_workflow_notification(
        cls,
        workflow_execution: WorkflowExecution,
        notification_configs: List[Dict[str, Any]],
        event: str,  # "start", "success", "failure"
    ):
        """
        Send workflow notifications.

        Args:
            workflow_execution: Workflow execution instance
            notification_configs: List of notification configurations
            event: Event type (start, success, failure)
        """
        # Prepare message
        message = {
            "workflow_name": workflow_execution.workflow.name
            if hasattr(workflow_execution, "workflow")
            else "Unknown",
            "workflow_id": workflow_execution.workflow_id,
            "run_id": workflow_execution.run_id,
            "status": workflow_execution.status.value,
            "duration": workflow_execution.duration or 0,
            "error": workflow_execution.error_message or "",
            "event": event,
        }

        # Filter relevant notifications
        tasks = []
        for config in notification_configs:
            should_send = False

            if event == "start" and config.get("on_start"):
                should_send = True
            elif (
                event == "success"
                and config.get("on_success")
                and workflow_execution.status == WorkflowStatus.COMPLETED
            ):
                should_send = True
            elif (
                event == "failure"
                and config.get("on_failure")
                and workflow_execution.status == WorkflowStatus.FAILED
            ):
                should_send = True

            if should_send and config.get("is_active"):
                notifier_class = cls.NOTIFIER_TYPES.get(config["notification_type"])
                if notifier_class:
                    notifier = notifier_class(config.get("config", {}))
                    tasks.append(notifier.send(message))

        # Send all notifications in parallel
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for r in results if r is True)
            logger.info(
                f"Sent {success_count}/{len(tasks)} notifications for workflow {workflow_execution.run_id}"
            )


# Notification manager instance
notification_manager = NotificationManager()
