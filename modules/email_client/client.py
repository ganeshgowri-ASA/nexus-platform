"""
Core Email Client Engine

Main orchestrator for email operations across multiple accounts and protocols.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union
from uuid import uuid4

from .imap_handler import IMAPHandler
from .smtp_handler import SMTPHandler
from .pop3_handler import POP3Handler
from .parser import EmailParser
from .attachment_manager import AttachmentManager
from .search import EmailSearch
from .rules import RulesEngine
from .contacts_integration import ContactsManager
from .ai_assistant import AIEmailAssistant
from .security import SecurityManager

logger = logging.getLogger(__name__)


class AccountType(Enum):
    """Email account types."""
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    YAHOO = "yahoo"
    IMAP_SMTP = "imap_smtp"
    POP3_SMTP = "pop3_smtp"
    EXCHANGE = "exchange"


class EmailProtocol(Enum):
    """Email protocols."""
    IMAP = "imap"
    POP3 = "pop3"
    SMTP = "smtp"
    EXCHANGE = "exchange"


@dataclass
class EmailAccount:
    """Email account configuration."""
    account_id: str = field(default_factory=lambda: str(uuid4()))
    email_address: str = ""
    display_name: str = ""
    account_type: AccountType = AccountType.IMAP_SMTP

    # IMAP settings
    imap_host: str = ""
    imap_port: int = 993
    imap_use_ssl: bool = True

    # SMTP settings
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_use_tls: bool = True

    # POP3 settings
    pop3_host: str = ""
    pop3_port: int = 995
    pop3_use_ssl: bool = True

    # Authentication
    username: str = ""
    password: str = ""
    oauth2_token: Optional[str] = None
    oauth2_refresh_token: Optional[str] = None

    # Settings
    signature: str = ""
    default_folder: str = "INBOX"
    sync_enabled: bool = True
    sync_interval: int = 300  # seconds

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_sync: Optional[datetime] = None
    is_default: bool = False
    is_active: bool = True


@dataclass
class EmailMessage:
    """Email message representation."""
    message_id: str = field(default_factory=lambda: str(uuid4()))
    account_id: str = ""
    thread_id: Optional[str] = None

    # Headers
    from_address: str = ""
    to_addresses: List[str] = field(default_factory=list)
    cc_addresses: List[str] = field(default_factory=list)
    bcc_addresses: List[str] = field(default_factory=list)
    reply_to: Optional[str] = None

    subject: str = ""

    # Content
    body_text: str = ""
    body_html: str = ""

    # Attachments
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    inline_images: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    date: datetime = field(default_factory=datetime.utcnow)
    received_date: Optional[datetime] = None

    # Flags
    is_read: bool = False
    is_starred: bool = False
    is_draft: bool = False
    is_sent: bool = False
    is_spam: bool = False
    is_deleted: bool = False

    # Folder/Labels
    folder: str = "INBOX"
    labels: Set[str] = field(default_factory=set)

    # Tracking
    has_attachments: bool = False
    size_bytes: int = 0

    # AI Features
    ai_priority_score: Optional[float] = None
    ai_category: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_sentiment: Optional[str] = None

    # Security
    is_encrypted: bool = False
    is_signed: bool = False
    spf_result: Optional[str] = None
    dkim_result: Optional[str] = None

    # Raw
    raw_content: Optional[bytes] = None


class EmailClient:
    """
    Main email client orchestrator.

    Manages multiple email accounts, protocols, and provides unified access
    to all email operations.
    """

    def __init__(
        self,
        db_connection: Optional[Any] = None,
        storage_path: str = "./email_storage",
        enable_ai: bool = True,
        enable_security: bool = True
    ):
        """
        Initialize the email client.

        Args:
            db_connection: Database connection for storing emails
            storage_path: Path for attachment storage
            enable_ai: Enable AI features
            enable_security: Enable security features
        """
        self.db_connection = db_connection
        self.storage_path = storage_path
        self.enable_ai = enable_ai
        self.enable_security = enable_security

        # Account management
        self.accounts: Dict[str, EmailAccount] = {}
        self.active_account_id: Optional[str] = None

        # Protocol handlers
        self.imap_handlers: Dict[str, IMAPHandler] = {}
        self.smtp_handlers: Dict[str, SMTPHandler] = {}
        self.pop3_handlers: Dict[str, POP3Handler] = {}

        # Components
        self.parser = EmailParser()
        self.attachment_manager = AttachmentManager(storage_path=storage_path)
        self.search = EmailSearch(db_connection=db_connection)
        self.rules_engine = RulesEngine()
        self.contacts_manager = ContactsManager(db_connection=db_connection)

        # Optional components
        self.ai_assistant: Optional[AIEmailAssistant] = None
        self.security_manager: Optional[SecurityManager] = None

        if enable_ai:
            self.ai_assistant = AIEmailAssistant()

        if enable_security:
            self.security_manager = SecurityManager()

        # Sync management
        self.sync_tasks: Dict[str, asyncio.Task] = {}
        self.is_syncing: bool = False

        logger.info("Email client initialized")

    async def add_account(self, account: EmailAccount) -> str:
        """
        Add an email account.

        Args:
            account: Email account configuration

        Returns:
            str: Account ID
        """
        self.accounts[account.account_id] = account

        # Initialize handlers based on account type
        await self._initialize_handlers(account)

        # Set as default if it's the first account
        if len(self.accounts) == 1 or account.is_default:
            self.active_account_id = account.account_id

        # Start sync if enabled
        if account.sync_enabled:
            await self.start_account_sync(account.account_id)

        logger.info(f"Added account: {account.email_address}")
        return account.account_id

    async def _initialize_handlers(self, account: EmailAccount) -> None:
        """Initialize protocol handlers for an account."""
        # IMAP handler
        if account.imap_host:
            imap = IMAPHandler(
                host=account.imap_host,
                port=account.imap_port,
                use_ssl=account.imap_use_ssl,
                username=account.username,
                password=account.password,
                oauth2_token=account.oauth2_token
            )
            self.imap_handlers[account.account_id] = imap

        # SMTP handler
        if account.smtp_host:
            smtp = SMTPHandler(
                host=account.smtp_host,
                port=account.smtp_port,
                use_tls=account.smtp_use_tls,
                username=account.username,
                password=account.password,
                oauth2_token=account.oauth2_token
            )
            self.smtp_handlers[account.account_id] = smtp

        # POP3 handler
        if account.pop3_host:
            pop3 = POP3Handler(
                host=account.pop3_host,
                port=account.pop3_port,
                use_ssl=account.pop3_use_ssl,
                username=account.username,
                password=account.password
            )
            self.pop3_handlers[account.account_id] = pop3

    async def remove_account(self, account_id: str) -> None:
        """Remove an email account."""
        if account_id in self.accounts:
            # Stop sync
            await self.stop_account_sync(account_id)

            # Disconnect handlers
            if account_id in self.imap_handlers:
                await self.imap_handlers[account_id].disconnect()
                del self.imap_handlers[account_id]

            if account_id in self.smtp_handlers:
                await self.smtp_handlers[account_id].disconnect()
                del self.smtp_handlers[account_id]

            if account_id in self.pop3_handlers:
                await self.pop3_handlers[account_id].disconnect()
                del self.pop3_handlers[account_id]

            # Remove account
            del self.accounts[account_id]

            # Update active account
            if self.active_account_id == account_id:
                self.active_account_id = next(iter(self.accounts.keys())) if self.accounts else None

            logger.info(f"Removed account: {account_id}")

    async def connect(self, account_id: Optional[str] = None) -> bool:
        """
        Connect to email server(s).

        Args:
            account_id: Specific account to connect, or None for all

        Returns:
            bool: Success status
        """
        accounts_to_connect = [account_id] if account_id else list(self.accounts.keys())

        success = True
        for aid in accounts_to_connect:
            try:
                # Connect IMAP
                if aid in self.imap_handlers:
                    await self.imap_handlers[aid].connect()

                # SMTP connects per-send

                # Connect POP3
                if aid in self.pop3_handlers:
                    await self.pop3_handlers[aid].connect()

                logger.info(f"Connected account: {aid}")
            except Exception as e:
                logger.error(f"Failed to connect account {aid}: {e}")
                success = False

        return success

    async def disconnect(self, account_id: Optional[str] = None) -> None:
        """Disconnect from email server(s)."""
        accounts_to_disconnect = [account_id] if account_id else list(self.accounts.keys())

        for aid in accounts_to_disconnect:
            if aid in self.imap_handlers:
                await self.imap_handlers[aid].disconnect()

            if aid in self.smtp_handlers:
                await self.smtp_handlers[aid].disconnect()

            if aid in self.pop3_handlers:
                await self.pop3_handlers[aid].disconnect()

    async def fetch_messages(
        self,
        account_id: Optional[str] = None,
        folder: str = "INBOX",
        limit: int = 50,
        criteria: Optional[str] = None
    ) -> List[EmailMessage]:
        """
        Fetch email messages.

        Args:
            account_id: Account to fetch from
            folder: Folder/mailbox name
            limit: Maximum number of messages
            criteria: IMAP search criteria

        Returns:
            List[EmailMessage]: Fetched messages
        """
        aid = account_id or self.active_account_id
        if not aid or aid not in self.imap_handlers:
            return []

        handler = self.imap_handlers[aid]
        raw_messages = await handler.fetch_messages(
            folder=folder,
            limit=limit,
            criteria=criteria
        )

        messages = []
        for raw_msg in raw_messages:
            # Parse message
            msg = self.parser.parse(raw_msg)
            msg.account_id = aid

            # Apply rules
            if self.rules_engine:
                msg = await self.rules_engine.apply_rules(msg)

            # AI processing
            if self.ai_assistant and self.enable_ai:
                msg = await self.ai_assistant.process_message(msg)

            # Security checks
            if self.security_manager and self.enable_security:
                msg = await self.security_manager.check_message(msg)

            messages.append(msg)

        return messages

    async def send_message(
        self,
        message: EmailMessage,
        account_id: Optional[str] = None,
        schedule_time: Optional[datetime] = None
    ) -> bool:
        """
        Send an email message.

        Args:
            message: Message to send
            account_id: Account to send from
            schedule_time: Optional scheduled send time

        Returns:
            bool: Success status
        """
        aid = account_id or self.active_account_id
        if not aid or aid not in self.smtp_handlers:
            logger.error("No SMTP handler available")
            return False

        # Add signature
        account = self.accounts[aid]
        if account.signature and not message.body_html.endswith(account.signature):
            message.body_html += f"<br><br>{account.signature}"

        # Process attachments
        if message.attachments:
            message.attachments = await self.attachment_manager.process_attachments(
                message.attachments
            )

        # Security: Sign/Encrypt
        if self.security_manager and self.enable_security:
            message = await self.security_manager.sign_and_encrypt(message, account)

        handler = self.smtp_handlers[aid]

        if schedule_time:
            # Schedule for later
            await self._schedule_send(message, handler, schedule_time)
            return True
        else:
            # Send immediately
            success = await handler.send_message(message)
            if success:
                message.is_sent = True
                message.date = datetime.utcnow()
                # Save to sent folder
                await self._save_to_sent(message, aid)

            return success

    async def _schedule_send(
        self,
        message: EmailMessage,
        handler: SMTPHandler,
        schedule_time: datetime
    ) -> None:
        """Schedule a message to be sent later."""
        delay = (schedule_time - datetime.utcnow()).total_seconds()
        if delay > 0:
            await asyncio.sleep(delay)
            await handler.send_message(message)

    async def _save_to_sent(self, message: EmailMessage, account_id: str) -> None:
        """Save sent message to Sent folder."""
        if account_id in self.imap_handlers:
            handler = self.imap_handlers[account_id]
            await handler.append_message("Sent", message)

    async def delete_message(
        self,
        message_id: str,
        account_id: Optional[str] = None,
        permanent: bool = False
    ) -> bool:
        """
        Delete a message.

        Args:
            message_id: Message ID
            account_id: Account ID
            permanent: Permanently delete (vs move to trash)

        Returns:
            bool: Success status
        """
        aid = account_id or self.active_account_id
        if not aid or aid not in self.imap_handlers:
            return False

        handler = self.imap_handlers[aid]

        if permanent:
            return await handler.delete_message(message_id)
        else:
            return await handler.move_message(message_id, "Trash")

    async def move_message(
        self,
        message_id: str,
        destination_folder: str,
        account_id: Optional[str] = None
    ) -> bool:
        """Move a message to another folder."""
        aid = account_id or self.active_account_id
        if not aid or aid not in self.imap_handlers:
            return False

        handler = self.imap_handlers[aid]
        return await handler.move_message(message_id, destination_folder)

    async def mark_as_read(
        self,
        message_id: str,
        read: bool = True,
        account_id: Optional[str] = None
    ) -> bool:
        """Mark message as read/unread."""
        aid = account_id or self.active_account_id
        if not aid or aid not in self.imap_handlers:
            return False

        handler = self.imap_handlers[aid]
        return await handler.set_flag(message_id, "\\Seen", read)

    async def star_message(
        self,
        message_id: str,
        starred: bool = True,
        account_id: Optional[str] = None
    ) -> bool:
        """Star/unstar a message."""
        aid = account_id or self.active_account_id
        if not aid or aid not in self.imap_handlers:
            return False

        handler = self.imap_handlers[aid]
        return await handler.set_flag(message_id, "\\Flagged", starred)

    async def search_messages(
        self,
        query: str,
        account_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[EmailMessage]:
        """
        Search for messages.

        Args:
            query: Search query
            account_id: Account to search
            filters: Additional filters

        Returns:
            List[EmailMessage]: Matching messages
        """
        return await self.search.search(
            query=query,
            account_id=account_id,
            filters=filters
        )

    async def get_folders(self, account_id: Optional[str] = None) -> List[str]:
        """Get list of folders/mailboxes."""
        aid = account_id or self.active_account_id
        if not aid or aid not in self.imap_handlers:
            return []

        handler = self.imap_handlers[aid]
        return await handler.list_folders()

    async def create_folder(
        self,
        folder_name: str,
        account_id: Optional[str] = None
    ) -> bool:
        """Create a new folder."""
        aid = account_id or self.active_account_id
        if not aid or aid not in self.imap_handlers:
            return False

        handler = self.imap_handlers[aid]
        return await handler.create_folder(folder_name)

    async def start_account_sync(self, account_id: str) -> None:
        """Start background sync for an account."""
        if account_id in self.sync_tasks:
            return

        account = self.accounts[account_id]
        task = asyncio.create_task(
            self._sync_loop(account_id, account.sync_interval)
        )
        self.sync_tasks[account_id] = task

    async def stop_account_sync(self, account_id: str) -> None:
        """Stop background sync for an account."""
        if account_id in self.sync_tasks:
            self.sync_tasks[account_id].cancel()
            try:
                await self.sync_tasks[account_id]
            except asyncio.CancelledError:
                pass
            del self.sync_tasks[account_id]

    async def _sync_loop(self, account_id: str, interval: int) -> None:
        """Background sync loop for an account."""
        while True:
            try:
                await self._sync_account(account_id)
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Sync error for account {account_id}: {e}")
                await asyncio.sleep(60)  # Wait before retry

    async def _sync_account(self, account_id: str) -> None:
        """Sync an account."""
        account = self.accounts[account_id]

        # Fetch new messages
        messages = await self.fetch_messages(account_id=account_id, limit=100)

        # Update last sync time
        account.last_sync = datetime.utcnow()

        logger.info(f"Synced {len(messages)} messages for account {account_id}")

    async def get_unified_inbox(
        self,
        limit: int = 100,
        include_accounts: Optional[List[str]] = None
    ) -> List[EmailMessage]:
        """
        Get unified inbox across all accounts.

        Args:
            limit: Maximum messages to return
            include_accounts: Specific accounts to include

        Returns:
            List[EmailMessage]: Combined messages from all accounts
        """
        accounts = include_accounts or list(self.accounts.keys())

        all_messages = []
        for account_id in accounts:
            messages = await self.fetch_messages(
                account_id=account_id,
                limit=limit // len(accounts) + 1
            )
            all_messages.extend(messages)

        # Sort by date
        all_messages.sort(key=lambda m: m.date, reverse=True)

        return all_messages[:limit]

    async def cleanup(self) -> None:
        """Cleanup resources."""
        # Stop all sync tasks
        for account_id in list(self.sync_tasks.keys()):
            await self.stop_account_sync(account_id)

        # Disconnect all accounts
        await self.disconnect()

        logger.info("Email client cleaned up")


# Preset configurations for popular providers
GMAIL_CONFIG = {
    "account_type": AccountType.GMAIL,
    "imap_host": "imap.gmail.com",
    "imap_port": 993,
    "imap_use_ssl": True,
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_use_tls": True,
}

OUTLOOK_CONFIG = {
    "account_type": AccountType.OUTLOOK,
    "imap_host": "outlook.office365.com",
    "imap_port": 993,
    "imap_use_ssl": True,
    "smtp_host": "smtp.office365.com",
    "smtp_port": 587,
    "smtp_use_tls": True,
}

YAHOO_CONFIG = {
    "account_type": AccountType.YAHOO,
    "imap_host": "imap.mail.yahoo.com",
    "imap_port": 993,
    "imap_use_ssl": True,
    "smtp_host": "smtp.mail.yahoo.com",
    "smtp_port": 587,
    "smtp_use_tls": True,
}
