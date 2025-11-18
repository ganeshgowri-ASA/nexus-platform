"""
Email notification provider
Supports multiple email backends (SMTP, SendGrid, AWS SES, etc.)
"""
import re
import os
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from backend.services.notifications.providers.base import (
    BaseNotificationProvider,
    NotificationResult,
)


class EmailProvider(BaseNotificationProvider):
    """
    Email notification provider
    Supports SMTP, SendGrid, AWS SES, and other email services
    """

    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize email provider

        Config options:
            - backend: 'smtp', 'sendgrid', 'ses' (default: smtp)
            - smtp_host: SMTP server host
            - smtp_port: SMTP server port
            - smtp_user: SMTP username
            - smtp_password: SMTP password
            - smtp_use_tls: Use TLS (default: True)
            - from_email: Sender email address
            - from_name: Sender name
            - sendgrid_api_key: SendGrid API key (if using SendGrid)
            - aws_region: AWS region (if using SES)
        """
        super().__init__(config)
        self.backend = config.get("backend", "smtp") if config else "smtp"
        self.from_email = config.get("from_email", os.getenv("EMAIL_FROM", "noreply@nexus.com")) if config else "noreply@nexus.com"
        self.from_name = config.get("from_name", "NEXUS Platform") if config else "NEXUS Platform"

        # SMTP configuration
        if self.backend == "smtp":
            self.smtp_host = config.get("smtp_host", os.getenv("SMTP_HOST", "localhost"))
            self.smtp_port = int(config.get("smtp_port", os.getenv("SMTP_PORT", "587")))
            self.smtp_user = config.get("smtp_user", os.getenv("SMTP_USER", ""))
            self.smtp_password = config.get("smtp_password", os.getenv("SMTP_PASSWORD", ""))
            self.smtp_use_tls = config.get("smtp_use_tls", os.getenv("SMTP_USE_TLS", "true").lower() == "true")

    async def send(
        self,
        recipient: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> NotificationResult:
        """
        Send email notification

        Args:
            recipient: Email address
            title: Email subject
            message: Email body (plain text)
            data: Additional data (html_body, cc, bcc, attachments, etc.)
            **kwargs: Additional parameters

        Returns:
            NotificationResult
        """
        start_time = datetime.utcnow()

        try:
            # Validate recipient
            if not self.validate_recipient(recipient):
                return NotificationResult(
                    success=False,
                    error_message=f"Invalid email address: {recipient}",
                    error_code="INVALID_EMAIL",
                )

            # Extract additional parameters
            html_body = kwargs.get("html_body") or (data.get("html_body") if data else None)
            cc = kwargs.get("cc", [])
            bcc = kwargs.get("bcc", [])
            reply_to = kwargs.get("reply_to")

            # Send based on backend
            if self.backend == "smtp":
                result = await self._send_smtp(
                    recipient, title, message, html_body, cc, bcc, reply_to
                )
            elif self.backend == "sendgrid":
                result = await self._send_sendgrid(
                    recipient, title, message, html_body, cc, bcc, reply_to
                )
            elif self.backend == "ses":
                result = await self._send_ses(
                    recipient, title, message, html_body, cc, bcc, reply_to
                )
            else:
                return NotificationResult(
                    success=False,
                    error_message=f"Unknown email backend: {self.backend}",
                    error_code="UNKNOWN_BACKEND",
                )

            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.processing_time_ms = processing_time

            return result

        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return NotificationResult(
                success=False,
                error_message=str(e),
                error_code="SEND_FAILED",
                processing_time_ms=processing_time,
            )

    async def _send_smtp(
        self,
        recipient: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        cc: List[str] = None,
        bcc: List[str] = None,
        reply_to: Optional[str] = None,
    ) -> NotificationResult:
        """Send email via SMTP"""
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = recipient

            if cc:
                msg["Cc"] = ", ".join(cc)
            if reply_to:
                msg["Reply-To"] = reply_to

            # Attach text and HTML parts
            text_part = MIMEText(body, "plain", "utf-8")
            msg.attach(text_part)

            if html_body:
                html_part = MIMEText(html_body, "html", "utf-8")
                msg.attach(html_part)

            # Send email
            def send_sync():
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    if self.smtp_use_tls:
                        server.starttls()
                    if self.smtp_user and self.smtp_password:
                        server.login(self.smtp_user, self.smtp_password)

                    recipients = [recipient]
                    if cc:
                        recipients.extend(cc)
                    if bcc:
                        recipients.extend(bcc)

                    server.send_message(msg, self.from_email, recipients)
                    return True

            # Run sync operation in thread pool
            await asyncio.get_event_loop().run_in_executor(None, send_sync)

            return NotificationResult(
                success=True,
                provider_message_id=f"smtp_{datetime.utcnow().timestamp()}",
                provider_response={"backend": "smtp", "recipient": recipient},
            )

        except Exception as e:
            return NotificationResult(
                success=False,
                error_message=str(e),
                error_code="SMTP_ERROR",
            )

    async def _send_sendgrid(
        self,
        recipient: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        cc: List[str] = None,
        bcc: List[str] = None,
        reply_to: Optional[str] = None,
    ) -> NotificationResult:
        """Send email via SendGrid API"""
        # Placeholder for SendGrid implementation
        # Requires: pip install sendgrid
        return NotificationResult(
            success=False,
            error_message="SendGrid backend not implemented. Install 'sendgrid' package and implement.",
            error_code="NOT_IMPLEMENTED",
        )

    async def _send_ses(
        self,
        recipient: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        cc: List[str] = None,
        bcc: List[str] = None,
        reply_to: Optional[str] = None,
    ) -> NotificationResult:
        """Send email via AWS SES"""
        # Placeholder for AWS SES implementation
        # Requires: pip install boto3
        return NotificationResult(
            success=False,
            error_message="AWS SES backend not implemented. Install 'boto3' package and implement.",
            error_code="NOT_IMPLEMENTED",
        )

    def validate_recipient(self, recipient: str) -> bool:
        """Validate email address format"""
        return bool(self.EMAIL_REGEX.match(recipient))

    def is_configured(self) -> bool:
        """Check if email provider is configured"""
        if self.backend == "smtp":
            return bool(self.smtp_host and self.from_email)
        return super().is_configured()
