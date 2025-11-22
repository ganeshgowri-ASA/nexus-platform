"""Main email service orchestrator."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import logging

from sqlalchemy.orm import Session

from src.modules.email.smtp_client import SMTPClient
from src.modules.email.imap_client import IMAPClient
from src.modules.email.parser import EmailParser
from src.modules.email.attachment_handler import AttachmentHandler
from src.modules.email.template_manager import TemplateManager
from src.modules.email.scheduler import EmailScheduler
from src.modules.email.tracking import EmailTracker
from src.modules.email.spam_filter import SpamFilter
from src.modules.email.sync_service import InboxSyncService
from src.modules.email.models import (
    Email, EmailAccount, EmailTemplate, EmailStatus,
    EmailPriority, EmailCreate
)
from src.core.config import settings
from src.core.database import SessionLocal

logger = logging.getLogger(__name__)


class EmailService:
    """Main email service orchestrator."""

    def __init__(
        self,
        db: Optional[Session] = None,
        account_id: Optional[int] = None
    ):
        """Initialize email service.

        Args:
            db: Database session
            account_id: Default email account ID
        """
        self.db = db or SessionLocal()
        self.account_id = account_id

        # Initialize components
        self.smtp_client: Optional[SMTPClient] = None
        self.imap_client: Optional[IMAPClient] = None
        self.attachment_handler = AttachmentHandler()
        self.template_manager = TemplateManager(db=self.db)
        self.scheduler = EmailScheduler(db=self.db)
        self.tracker = EmailTracker(db=self.db)
        self.spam_filter = SpamFilter()
        self.sync_service = InboxSyncService(
            db=self.db,
            attachment_handler=self.attachment_handler,
            spam_filter=self.spam_filter
        )

        # Load account if provided
        if account_id:
            self._load_account(account_id)

    def _load_account(self, account_id: int):
        """Load email account configuration.

        Args:
            account_id: Email account ID
        """
        account = self.db.query(EmailAccount).filter_by(id=account_id).first()
        if not account:
            raise ValueError(f"Account not found: {account_id}")

        self.account_id = account_id

        # Initialize SMTP client
        if account.smtp_host:
            self.smtp_client = SMTPClient(
                host=account.smtp_host,
                port=account.smtp_port,
                username=account.smtp_username,
                password=account.smtp_password,
                use_tls=account.smtp_use_tls
            )

        # Initialize IMAP client
        if account.imap_host:
            self.imap_client = IMAPClient(
                host=account.imap_host,
                port=account.imap_port,
                username=account.imap_username,
                password=account.imap_password,
                use_ssl=account.imap_use_ssl
            )

        logger.info(f"Loaded account: {account.email}")

    # Email sending methods

    def send_email(
        self,
        to: List[str],
        subject: str,
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        priority: EmailPriority = EmailPriority.NORMAL,
        track_opens: bool = False,
        track_clicks: bool = False,
        account_id: Optional[int] = None
    ) -> Email:
        """Send an email.

        Args:
            to: List of recipient email addresses
            subject: Email subject
            body_text: Plain text body
            body_html: HTML body
            cc: List of CC recipients
            bcc: List of BCC recipients
            attachments: List of attachment file paths
            priority: Email priority
            track_opens: Enable open tracking
            track_clicks: Enable click tracking
            account_id: Email account ID (uses default if not provided)

        Returns:
            Created Email object
        """
        # Use specified account or default
        acc_id = account_id or self.account_id
        if not acc_id:
            raise ValueError("No email account specified")

        # Load account if different
        if acc_id != self.account_id:
            self._load_account(acc_id)

        if not self.smtp_client:
            raise ValueError("SMTP client not configured")

        # Get account
        account = self.db.query(EmailAccount).filter_by(id=acc_id).first()

        # Create email record
        email = Email(
            account_id=acc_id,
            from_address=account.email,
            from_name=account.name,
            to_addresses=to,
            cc_addresses=cc or [],
            bcc_addresses=bcc or [],
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            status=EmailStatus.SENDING.value,
            priority=priority.value
        )

        self.db.add(email)
        self.db.flush()  # Get email ID

        # Add tracking
        if track_opens and body_html:
            body_html = self.tracker.add_tracking_pixel(email.id, body_html)
            email.body_html = body_html

        if track_clicks and body_html:
            body_html = self.tracker.add_link_tracking(email.id, body_html)
            email.body_html = body_html

        # Prepare attachments
        attachment_list = None
        if attachments:
            attachment_list = [{'path': path} for path in attachments]

        try:
            # Send email
            message_id = self.smtp_client.send_email(
                to=to,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                from_address=account.email,
                from_name=account.name,
                cc=cc,
                bcc=bcc,
                attachments=attachment_list,
                priority=priority
            )

            # Update email record
            email.message_id = message_id
            email.status = EmailStatus.SENT.value
            email.sent_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(email)

            logger.info(f"Email sent: {subject} to {to}")
            return email

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            email.status = EmailStatus.FAILED.value
            self.db.commit()
            raise

    def send_template_email(
        self,
        to: List[str],
        template_name: str,
        context: Dict[str, Any],
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        priority: EmailPriority = EmailPriority.NORMAL
    ) -> Email:
        """Send email using template.

        Args:
            to: List of recipient email addresses
            template_name: Template name
            context: Template context variables
            cc: List of CC recipients
            bcc: List of BCC recipients
            attachments: List of attachment file paths
            priority: Email priority

        Returns:
            Created Email object
        """
        # Render template
        rendered = self.template_manager.render_from_db(template_name, context)

        # Send email
        return self.send_email(
            to=to,
            subject=rendered['subject'],
            body_text=rendered.get('text'),
            body_html=rendered.get('html'),
            cc=cc,
            bcc=bcc,
            attachments=attachments,
            priority=priority
        )

    def schedule_email(
        self,
        to: List[str],
        subject: str,
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
        send_at: Optional[datetime] = None,
        **kwargs
    ) -> Email:
        """Schedule an email to be sent later.

        Args:
            to: List of recipient email addresses
            subject: Email subject
            body_text: Plain text body
            body_html: HTML body
            send_at: When to send the email
            **kwargs: Additional arguments for send_email

        Returns:
            Created Email object
        """
        if not send_at:
            raise ValueError("send_at is required for scheduled emails")

        # Create email record
        email = Email(
            account_id=self.account_id,
            to_addresses=to,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            status=EmailStatus.SCHEDULED.value,
            scheduled_at=send_at
        )

        self.db.add(email)
        self.db.commit()
        self.db.refresh(email)

        # Schedule sending
        self.scheduler.schedule_email(
            send_function=self.send_email,
            send_at=send_at,
            email_id=email.id,
            to=to,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            **kwargs
        )

        logger.info(f"Email scheduled for {send_at}: {subject}")
        return email

    # Email receiving methods

    def fetch_emails(
        self,
        folder: str = "INBOX",
        limit: Optional[int] = None,
        unread_only: bool = False
    ) -> List[Email]:
        """Fetch emails from inbox.

        Args:
            folder: Folder to fetch from
            limit: Maximum number of emails
            unread_only: Only fetch unread emails

        Returns:
            List of Email objects
        """
        if unread_only:
            return self.db.query(Email).filter_by(
                account_id=self.account_id,
                folder=folder,
                is_read=False
            ).limit(limit).all()
        else:
            return self.db.query(Email).filter_by(
                account_id=self.account_id,
                folder=folder
            ).limit(limit).all()

    def sync_inbox(
        self,
        folders: Optional[List[str]] = None,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Sync inbox from IMAP.

        Args:
            folders: List of folders to sync
            since: Only sync emails since this date

        Returns:
            Dict with sync statistics
        """
        if not self.account_id:
            raise ValueError("No email account specified")

        return self.sync_service.sync_account(
            self.account_id,
            folders=folders,
            since=since
        )

    def get_email(self, email_id: int) -> Optional[Email]:
        """Get email by ID.

        Args:
            email_id: Email ID

        Returns:
            Email object or None
        """
        return self.db.query(Email).filter_by(id=email_id).first()

    def mark_as_read(self, email_id: int):
        """Mark email as read.

        Args:
            email_id: Email ID
        """
        email = self.get_email(email_id)
        if email:
            email.is_read = True
            self.db.commit()

    def mark_as_unread(self, email_id: int):
        """Mark email as unread.

        Args:
            email_id: Email ID
        """
        email = self.get_email(email_id)
        if email:
            email.is_read = False
            self.db.commit()

    def delete_email(self, email_id: int):
        """Delete email.

        Args:
            email_id: Email ID
        """
        email = self.get_email(email_id)
        if email:
            # Delete attachments
            for attachment in email.attachments:
                self.attachment_handler.delete_attachment(attachment.file_path)

            # Delete email
            self.db.delete(email)
            self.db.commit()

    # Template methods

    def create_template(
        self,
        name: str,
        subject: str,
        body_html: Optional[str] = None,
        body_text: Optional[str] = None,
        **kwargs
    ) -> EmailTemplate:
        """Create email template.

        Args:
            name: Template name
            subject: Subject template
            body_html: HTML body template
            body_text: Text body template
            **kwargs: Additional template arguments

        Returns:
            Created EmailTemplate object
        """
        return self.template_manager.create_template(
            name=name,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            **kwargs
        )

    def get_template(self, name: str) -> Optional[EmailTemplate]:
        """Get template by name.

        Args:
            name: Template name

        Returns:
            EmailTemplate object or None
        """
        return self.template_manager.get_template(name)

    # Account management

    def create_account(
        self,
        email: str,
        name: Optional[str] = None,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        imap_host: Optional[str] = None,
        imap_port: Optional[int] = None,
        imap_username: Optional[str] = None,
        imap_password: Optional[str] = None,
        is_default: bool = False
    ) -> EmailAccount:
        """Create email account.

        Args:
            email: Email address
            name: Account name
            smtp_host: SMTP server host
            smtp_port: SMTP server port
            smtp_username: SMTP username
            smtp_password: SMTP password
            imap_host: IMAP server host
            imap_port: IMAP server port
            imap_username: IMAP username
            imap_password: IMAP password
            is_default: Whether this is the default account

        Returns:
            Created EmailAccount object
        """
        account = EmailAccount(
            email=email,
            name=name,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
            imap_host=imap_host,
            imap_port=imap_port,
            imap_username=imap_username,
            imap_password=imap_password,
            is_default=is_default
        )

        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)

        logger.info(f"Created email account: {email}")
        return account

    def get_account(self, account_id: int) -> Optional[EmailAccount]:
        """Get email account by ID.

        Args:
            account_id: Account ID

        Returns:
            EmailAccount object or None
        """
        return self.db.query(EmailAccount).filter_by(id=account_id).first()

    # Statistics and tracking

    def get_email_stats(self, email_id: int) -> Optional[Dict[str, Any]]:
        """Get tracking statistics for email.

        Args:
            email_id: Email ID

        Returns:
            Dict with tracking statistics
        """
        return self.tracker.get_email_stats(email_id)

    def get_inbox_stats(self) -> Dict[str, Any]:
        """Get inbox statistics.

        Returns:
            Dict with inbox statistics
        """
        if not self.account_id:
            raise ValueError("No email account specified")

        total = self.db.query(Email).filter_by(
            account_id=self.account_id
        ).count()

        unread = self.db.query(Email).filter_by(
            account_id=self.account_id,
            is_read=False
        ).count()

        spam = self.db.query(Email).filter_by(
            account_id=self.account_id,
            is_spam=True
        ).count()

        sent = self.db.query(Email).filter_by(
            account_id=self.account_id,
            status=EmailStatus.SENT.value
        ).count()

        return {
            'total': total,
            'unread': unread,
            'spam': spam,
            'sent': sent,
            'read': total - unread
        }

    def start_scheduler(self):
        """Start email scheduler."""
        self.scheduler.start()
        logger.info("Email scheduler started")

    def stop_scheduler(self):
        """Stop email scheduler."""
        self.scheduler.stop()
        logger.info("Email scheduler stopped")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.smtp_client:
            self.smtp_client.disconnect()
        if self.imap_client:
            self.imap_client.disconnect()
        self.scheduler.stop()
