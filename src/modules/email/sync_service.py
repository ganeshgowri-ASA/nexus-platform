"""Inbox synchronization service for syncing emails from IMAP."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from sqlalchemy.orm import Session

from src.modules.email.imap_client import IMAPClient
from src.modules.email.parser import EmailParser
from src.modules.email.attachment_handler import AttachmentHandler
from src.modules.email.spam_filter import SpamFilter
from src.modules.email.models import Email, EmailAccount, EmailStatus
from src.core.config import settings

logger = logging.getLogger(__name__)


class InboxSyncService:
    """Service for synchronizing inbox from IMAP."""

    def __init__(
        self,
        db: Session,
        attachment_handler: Optional[AttachmentHandler] = None,
        spam_filter: Optional[SpamFilter] = None
    ):
        """Initialize inbox sync service.

        Args:
            db: Database session
            attachment_handler: Attachment handler instance
            spam_filter: Spam filter instance
        """
        self.db = db
        self.attachment_handler = attachment_handler or AttachmentHandler()
        self.spam_filter = spam_filter or SpamFilter()

    def sync_account(
        self,
        account_id: int,
        folders: Optional[List[str]] = None,
        since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Sync emails for an account.

        Args:
            account_id: Email account ID
            folders: List of folders to sync (default: ["INBOX"])
            since: Only sync emails since this date
            limit: Maximum number of emails to sync per folder

        Returns:
            Dict with sync statistics
        """
        # Get account from database
        account = self.db.query(EmailAccount).filter_by(id=account_id).first()
        if not account:
            raise ValueError(f"Account not found: {account_id}")

        if not account.is_active:
            raise ValueError(f"Account is inactive: {account_id}")

        logger.info(f"Starting sync for account: {account.email}")

        # Default folders
        if not folders:
            folders = ["INBOX"]

        # Default since time
        if not since:
            if account.last_sync:
                since = account.last_sync
            else:
                # First sync: get emails from last 30 days
                since = datetime.utcnow() - timedelta(days=30)

        # Initialize IMAP client
        imap = IMAPClient(
            host=account.imap_host,
            port=account.imap_port,
            username=account.imap_username,
            password=account.imap_password,
            use_ssl=account.imap_use_ssl
        )

        stats = {
            'account_id': account_id,
            'folders': {},
            'total_synced': 0,
            'total_new': 0,
            'total_spam': 0,
            'errors': []
        }

        try:
            # Connect to IMAP
            imap.connect()

            # Sync each folder
            for folder in folders:
                logger.info(f"Syncing folder: {folder}")

                try:
                    folder_stats = self._sync_folder(
                        imap,
                        account,
                        folder,
                        since,
                        limit
                    )

                    stats['folders'][folder] = folder_stats
                    stats['total_synced'] += folder_stats['synced']
                    stats['total_new'] += folder_stats['new']
                    stats['total_spam'] += folder_stats['spam']

                except Exception as e:
                    logger.error(f"Failed to sync folder {folder}: {e}")
                    stats['errors'].append({
                        'folder': folder,
                        'error': str(e)
                    })

            # Update last sync time
            account.last_sync = datetime.utcnow()
            self.db.commit()

            logger.info(
                f"Sync completed: {stats['total_synced']} emails synced, "
                f"{stats['total_new']} new, {stats['total_spam']} spam"
            )

        finally:
            imap.disconnect()

        return stats

    def _sync_folder(
        self,
        imap: IMAPClient,
        account: EmailAccount,
        folder: str,
        since: datetime,
        limit: Optional[int]
    ) -> Dict[str, Any]:
        """Sync a specific folder.

        Args:
            imap: IMAP client
            account: Email account
            folder: Folder name
            since: Sync emails since this date
            limit: Maximum number of emails

        Returns:
            Dict with folder sync statistics
        """
        stats = {
            'folder': folder,
            'synced': 0,
            'new': 0,
            'spam': 0,
            'updated': 0
        }

        try:
            # Fetch emails since date
            messages = imap.fetch_emails_since(since, folder, limit)

            for msg in messages:
                try:
                    # Parse email
                    parsed = EmailParser.parse_message(msg)

                    # Check if email already exists
                    message_id = parsed.get('message_id')
                    existing = None

                    if message_id:
                        existing = self.db.query(Email).filter_by(
                            message_id=message_id
                        ).first()

                    if existing:
                        # Update existing email
                        self._update_email(existing, parsed, folder)
                        stats['updated'] += 1
                    else:
                        # Create new email
                        self._create_email(account, parsed, folder, msg)
                        stats['new'] += 1

                    stats['synced'] += 1

                except Exception as e:
                    logger.error(f"Failed to process email: {e}")

        except Exception as e:
            logger.error(f"Failed to sync folder {folder}: {e}")
            raise

        return stats

    def _create_email(
        self,
        account: EmailAccount,
        parsed: Dict[str, Any],
        folder: str,
        msg: Any
    ):
        """Create new email in database.

        Args:
            account: Email account
            parsed: Parsed email data
            folder: Folder name
            msg: Original email message object
        """
        # Check for spam
        spam_analysis = self.spam_filter.analyze_email(msg)

        # Create email record
        email = Email(
            account_id=account.id,
            message_id=parsed.get('message_id'),
            in_reply_to=parsed.get('in_reply_to'),
            references=parsed.get('references'),
            from_address=parsed.get('from_email'),
            from_name=parsed.get('from_name'),
            to_addresses=[addr['email'] for addr in parsed.get('to_addresses', [])],
            cc_addresses=[addr['email'] for addr in parsed.get('cc_addresses', [])],
            reply_to=parsed.get('reply_to'),
            subject=parsed.get('subject'),
            body_text=parsed.get('body_text'),
            body_html=parsed.get('body_html'),
            status=EmailStatus.RECEIVED.value,
            priority=parsed.get('priority', 'normal'),
            folder=folder,
            received_at=parsed.get('date') or datetime.utcnow(),
            is_spam=spam_analysis['is_spam'],
            spam_score=spam_analysis['spam_score']
        )

        self.db.add(email)
        self.db.flush()  # Get email ID

        # Save attachments
        if parsed.get('attachments'):
            try:
                saved_attachments = self.attachment_handler.save_attachments(
                    msg,
                    subfolder=str(account.id)
                )

                # Create attachment records
                from src.modules.email.models import EmailAttachment

                for att_info in saved_attachments:
                    attachment = EmailAttachment(
                        email_id=email.id,
                        filename=att_info['filename'],
                        content_type=att_info['content_type'],
                        content_id=att_info.get('content_id'),
                        size=att_info['size'],
                        file_path=att_info['file_path'],
                        is_inline=att_info.get('is_inline', False)
                    )
                    self.db.add(attachment)

            except Exception as e:
                logger.error(f"Failed to save attachments: {e}")

        self.db.commit()

        if spam_analysis['is_spam']:
            logger.info(
                f"Spam email saved: {parsed.get('subject')} "
                f"(score: {spam_analysis['spam_score']:.2f})"
            )
        else:
            logger.debug(f"Email saved: {parsed.get('subject')}")

    def _update_email(
        self,
        email: Email,
        parsed: Dict[str, Any],
        folder: str
    ):
        """Update existing email in database.

        Args:
            email: Email record
            parsed: Parsed email data
            folder: Folder name
        """
        # Update folder if moved
        if email.folder != folder:
            email.folder = folder

        # Update other fields that might change
        email.is_read = False  # Reset read status

        self.db.commit()
        logger.debug(f"Updated email: {email.subject}")

    def sync_all_accounts(
        self,
        folders: Optional[List[str]] = None,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Sync all active email accounts.

        Args:
            folders: List of folders to sync
            since: Only sync emails since this date

        Returns:
            Dict with overall sync statistics
        """
        # Get all active accounts
        accounts = self.db.query(EmailAccount).filter_by(is_active=True).all()

        logger.info(f"Syncing {len(accounts)} accounts")

        overall_stats = {
            'accounts': {},
            'total_synced': 0,
            'total_new': 0,
            'total_spam': 0,
            'total_errors': 0
        }

        for account in accounts:
            try:
                stats = self.sync_account(
                    account.id,
                    folders=folders,
                    since=since
                )

                overall_stats['accounts'][account.email] = stats
                overall_stats['total_synced'] += stats['total_synced']
                overall_stats['total_new'] += stats['total_new']
                overall_stats['total_spam'] += stats['total_spam']
                overall_stats['total_errors'] += len(stats.get('errors', []))

            except Exception as e:
                logger.error(f"Failed to sync account {account.email}: {e}")
                overall_stats['accounts'][account.email] = {
                    'error': str(e)
                }
                overall_stats['total_errors'] += 1

        logger.info(
            f"All accounts synced: {overall_stats['total_synced']} emails, "
            f"{overall_stats['total_new']} new, {overall_stats['total_spam']} spam"
        )

        return overall_stats

    def sync_unread_only(
        self,
        account_id: int,
        folder: str = "INBOX"
    ) -> Dict[str, Any]:
        """Sync only unread emails for an account.

        Args:
            account_id: Email account ID
            folder: Folder to sync

        Returns:
            Dict with sync statistics
        """
        # Get account
        account = self.db.query(EmailAccount).filter_by(id=account_id).first()
        if not account:
            raise ValueError(f"Account not found: {account_id}")

        logger.info(f"Syncing unread emails for: {account.email}")

        # Initialize IMAP client
        imap = IMAPClient(
            host=account.imap_host,
            port=account.imap_port,
            username=account.imap_username,
            password=account.imap_password,
            use_ssl=account.imap_use_ssl
        )

        stats = {
            'account_id': account_id,
            'folder': folder,
            'synced': 0,
            'new': 0,
            'spam': 0
        }

        try:
            imap.connect()

            # Fetch unread emails
            messages = imap.fetch_unread_emails(folder)

            for msg in messages:
                try:
                    parsed = EmailParser.parse_message(msg)

                    # Check if already exists
                    message_id = parsed.get('message_id')
                    if message_id:
                        existing = self.db.query(Email).filter_by(
                            message_id=message_id
                        ).first()

                        if not existing:
                            self._create_email(account, parsed, folder, msg)
                            stats['new'] += 1

                    stats['synced'] += 1

                except Exception as e:
                    logger.error(f"Failed to process unread email: {e}")

        finally:
            imap.disconnect()

        logger.info(f"Unread sync completed: {stats['synced']} emails")
        return stats

    def get_sync_status(self, account_id: int) -> Dict[str, Any]:
        """Get sync status for an account.

        Args:
            account_id: Email account ID

        Returns:
            Dict with sync status
        """
        account = self.db.query(EmailAccount).filter_by(id=account_id).first()
        if not account:
            raise ValueError(f"Account not found: {account_id}")

        # Count emails
        total_emails = self.db.query(Email).filter_by(
            account_id=account_id
        ).count()

        unread_emails = self.db.query(Email).filter_by(
            account_id=account_id,
            is_read=False
        ).count()

        spam_emails = self.db.query(Email).filter_by(
            account_id=account_id,
            is_spam=True
        ).count()

        return {
            'account_id': account_id,
            'email': account.email,
            'last_sync': account.last_sync,
            'is_active': account.is_active,
            'total_emails': total_emails,
            'unread_emails': unread_emails,
            'spam_emails': spam_emails,
            'sync_interval_minutes': settings.email_sync_interval_minutes
        }
