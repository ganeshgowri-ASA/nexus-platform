"""
Email service for marketing automation.

This module handles email sending, template management, and personalization.
"""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from config.logging_config import get_logger
from src.core.exceptions import EmailSendError
from src.core.llm_client import llm_client
from src.core.utils import replace_template_variables, parse_template_variables
from src.models.contact import Contact
from src.models.campaign import Campaign

logger = get_logger(__name__)


class EmailService:
    """
    Service for sending and managing emails.

    Provides methods for sending emails, personalizing content, and tracking.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize email service."""
        self.db = db
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_from_email
        self.from_name = settings.smtp_from_name

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Send an email.

        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML email content
            from_email: Sender email (defaults to settings)
            from_name: Sender name (defaults to settings)
            reply_to: Reply-to email
            text_content: Plain text content (optional)

        Returns:
            True if sent successfully

        Raises:
            EmailSendError: If sending fails
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = f"{from_name or self.from_name} <{from_email or self.from_email}>"
            message["To"] = to_email
            message["Subject"] = subject

            if reply_to:
                message["Reply-To"] = reply_to

            # Add text and HTML parts
            if text_content:
                part1 = MIMEText(text_content, "plain")
                message.attach(part1)

            part2 = MIMEText(html_content, "html")
            message.attach(part2)

            # Send email
            async with aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                use_tls=True,
            ) as smtp:
                await smtp.login(self.smtp_user, self.smtp_password)
                await smtp.send_message(message)

            logger.info("Email sent successfully", to_email=to_email, subject=subject)

            return True

        except Exception as e:
            logger.error("Failed to send email", error=str(e), to_email=to_email)
            raise EmailSendError(f"Failed to send email: {str(e)}")

    async def send_campaign_email(
        self,
        contact: Contact,
        campaign: Campaign,
        personalize: bool = True,
    ) -> bool:
        """
        Send campaign email to a contact.

        Args:
            contact: Contact to send to
            campaign: Campaign
            personalize: Whether to personalize content with AI

        Returns:
            True if sent successfully
        """
        try:
            # Prepare contact data for personalization
            contact_data = {
                "first_name": contact.first_name or "there",
                "last_name": contact.last_name or "",
                "email": contact.email,
                "company": contact.company or "",
                "job_title": contact.job_title or "",
                **contact.custom_attributes,
            }

            # Personalize content
            subject = replace_template_variables(campaign.subject or "", contact_data)
            content = replace_template_variables(campaign.content, contact_data)

            # Use AI for deeper personalization if enabled
            if personalize:
                try:
                    content = await llm_client.personalize_content(
                        template=content,
                        contact_data=contact_data,
                        personalization_level="medium",
                    )
                except Exception as e:
                    logger.warning(
                        "AI personalization failed, using template",
                        error=str(e)
                    )

            # Send email
            return await self.send_email(
                to_email=contact.email,
                subject=subject,
                html_content=content,
                from_email=campaign.from_email,
                from_name=campaign.from_name,
                reply_to=campaign.reply_to,
            )

        except Exception as e:
            logger.error(
                "Failed to send campaign email",
                error=str(e),
                contact_id=str(contact.id),
                campaign_id=str(campaign.id)
            )
            raise EmailSendError(f"Failed to send campaign email: {str(e)}")

    async def send_test_email(
        self,
        campaign: Campaign,
        test_emails: List[str],
    ) -> Dict[str, bool]:
        """
        Send test emails for a campaign.

        Args:
            campaign: Campaign
            test_emails: List of test email addresses

        Returns:
            Dictionary of email -> success status
        """
        results = {}

        for email in test_emails:
            try:
                await self.send_email(
                    to_email=email,
                    subject=f"[TEST] {campaign.subject}",
                    html_content=campaign.content,
                    from_email=campaign.from_email,
                    from_name=campaign.from_name,
                    reply_to=campaign.reply_to,
                )
                results[email] = True
            except Exception as e:
                logger.error("Test email failed", error=str(e), email=email)
                results[email] = False

        return results

    async def generate_unsubscribe_link(
        self,
        contact_id: UUID,
        campaign_id: UUID,
    ) -> str:
        """Generate unsubscribe link."""
        from src.core.utils import generate_unsubscribe_token

        token = generate_unsubscribe_token(str(contact_id), str(campaign_id))
        return f"{settings.app_name}/unsubscribe?token={token}&contact={contact_id}&campaign={campaign_id}"

    async def add_tracking_pixels(
        self,
        html_content: str,
        message_id: UUID,
    ) -> str:
        """
        Add tracking pixels to email content.

        Args:
            html_content: HTML email content
            message_id: Campaign message ID

        Returns:
            HTML with tracking pixels added
        """
        # Add open tracking pixel
        tracking_pixel = f'<img src="{settings.app_name}/track/open/{message_id}" width="1" height="1" alt="" />'

        # Insert before closing body tag
        if "</body>" in html_content:
            html_content = html_content.replace("</body>", f"{tracking_pixel}</body>")
        else:
            html_content += tracking_pixel

        return html_content
