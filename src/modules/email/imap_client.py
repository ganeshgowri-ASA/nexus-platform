"""IMAP client for receiving emails."""

import imaplib
import email
from email.message import Message
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import logging

from src.core.config import settings

logger = logging.getLogger(__name__)


class IMAPClient:
    """IMAP client for receiving and managing emails."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_ssl: bool = True
    ):
        """Initialize IMAP client.

        Args:
            host: IMAP server host
            port: IMAP server port
            username: IMAP username
            password: IMAP password
            use_ssl: Whether to use SSL
        """
        self.host = host or settings.email_imap_host
        self.port = port or settings.email_imap_port
        self.username = username or settings.email_imap_username
        self.password = password or settings.email_imap_password
        self.use_ssl = use_ssl
        self._connection: Optional[imaplib.IMAP4_SSL | imaplib.IMAP4] = None

    def connect(self) -> imaplib.IMAP4_SSL | imaplib.IMAP4:
        """Establish IMAP connection.

        Returns:
            IMAP connection object

        Raises:
            ConnectionError: If connection fails
        """
        try:
            logger.info(f"Connecting to IMAP server {self.host}:{self.port}")

            # Create IMAP connection
            if self.use_ssl:
                imap = imaplib.IMAP4_SSL(self.host, self.port)
            else:
                imap = imaplib.IMAP4(self.host, self.port)

            # Login
            if self.username and self.password:
                imap.login(self.username, self.password)

            logger.info("IMAP connection established successfully")
            self._connection = imap
            return imap

        except Exception as e:
            logger.error(f"Failed to connect to IMAP server: {e}")
            raise ConnectionError(f"IMAP connection failed: {e}")

    def disconnect(self):
        """Disconnect from IMAP server."""
        if self._connection:
            try:
                self._connection.close()
                self._connection.logout()
                logger.info("IMAP connection closed")
            except Exception as e:
                logger.warning(f"Error closing IMAP connection: {e}")
            finally:
                self._connection = None

    def list_folders(self) -> List[str]:
        """List all email folders.

        Returns:
            List of folder names
        """
        if not self._connection:
            self.connect()

        try:
            status, folders = self._connection.list()
            if status != 'OK':
                raise Exception(f"Failed to list folders: {status}")

            folder_names = []
            for folder in folders:
                # Parse folder name from IMAP response
                parts = folder.decode().split('"')
                if len(parts) >= 3:
                    folder_names.append(parts[-2])

            return folder_names

        except Exception as e:
            logger.error(f"Failed to list folders: {e}")
            raise

    def select_folder(self, folder: str = "INBOX") -> Tuple[str, int]:
        """Select a folder.

        Args:
            folder: Folder name to select

        Returns:
            Tuple of (status, message count)
        """
        if not self._connection:
            self.connect()

        try:
            status, data = self._connection.select(folder)
            if status != 'OK':
                raise Exception(f"Failed to select folder {folder}: {status}")

            message_count = int(data[0])
            logger.info(f"Selected folder '{folder}' with {message_count} messages")
            return status, message_count

        except Exception as e:
            logger.error(f"Failed to select folder: {e}")
            raise

    def search_emails(
        self,
        criteria: str = "ALL",
        folder: str = "INBOX"
    ) -> List[int]:
        """Search for emails matching criteria.

        Args:
            criteria: IMAP search criteria (e.g., "ALL", "UNSEEN", "SINCE 01-Jan-2024")
            folder: Folder to search in

        Returns:
            List of email IDs
        """
        self.select_folder(folder)

        try:
            status, data = self._connection.search(None, criteria)
            if status != 'OK':
                raise Exception(f"Search failed: {status}")

            # Parse email IDs
            email_ids = data[0].split()
            email_ids = [int(id) for id in email_ids]

            logger.info(f"Found {len(email_ids)} emails matching criteria: {criteria}")
            return email_ids

        except Exception as e:
            logger.error(f"Failed to search emails: {e}")
            raise

    def fetch_email(
        self,
        email_id: int,
        parts: str = "(RFC822)"
    ) -> Message:
        """Fetch an email by ID.

        Args:
            email_id: Email ID
            parts: Email parts to fetch (default: full message)

        Returns:
            Email message object
        """
        if not self._connection:
            raise Exception("Not connected to IMAP server")

        try:
            status, data = self._connection.fetch(str(email_id).encode(), parts)
            if status != 'OK':
                raise Exception(f"Failed to fetch email {email_id}: {status}")

            # Parse email
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            logger.debug(f"Fetched email {email_id}: {msg.get('Subject', 'No subject')}")
            return msg

        except Exception as e:
            logger.error(f"Failed to fetch email {email_id}: {e}")
            raise

    def fetch_emails(
        self,
        criteria: str = "ALL",
        folder: str = "INBOX",
        limit: Optional[int] = None
    ) -> List[Message]:
        """Fetch multiple emails.

        Args:
            criteria: IMAP search criteria
            folder: Folder to search in
            limit: Maximum number of emails to fetch

        Returns:
            List of email message objects
        """
        email_ids = self.search_emails(criteria, folder)

        # Apply limit
        if limit:
            email_ids = email_ids[-limit:]  # Get most recent

        # Fetch emails
        emails = []
        for email_id in email_ids:
            try:
                msg = self.fetch_email(email_id)
                emails.append(msg)
            except Exception as e:
                logger.error(f"Failed to fetch email {email_id}: {e}")

        logger.info(f"Fetched {len(emails)} emails")
        return emails

    def fetch_unread_emails(
        self,
        folder: str = "INBOX",
        limit: Optional[int] = None
    ) -> List[Message]:
        """Fetch unread emails.

        Args:
            folder: Folder to search in
            limit: Maximum number of emails to fetch

        Returns:
            List of unread email messages
        """
        return self.fetch_emails("UNSEEN", folder, limit)

    def fetch_emails_since(
        self,
        since: datetime,
        folder: str = "INBOX",
        limit: Optional[int] = None
    ) -> List[Message]:
        """Fetch emails since a specific date.

        Args:
            since: Date to fetch emails from
            folder: Folder to search in
            limit: Maximum number of emails to fetch

        Returns:
            List of email messages
        """
        # Format date for IMAP
        date_str = since.strftime("%d-%b-%Y")
        criteria = f'SINCE {date_str}'

        return self.fetch_emails(criteria, folder, limit)

    def mark_as_read(self, email_id: int):
        """Mark an email as read.

        Args:
            email_id: Email ID to mark as read
        """
        if not self._connection:
            raise Exception("Not connected to IMAP server")

        try:
            self._connection.store(str(email_id).encode(), '+FLAGS', '\\Seen')
            logger.debug(f"Marked email {email_id} as read")
        except Exception as e:
            logger.error(f"Failed to mark email as read: {e}")
            raise

    def mark_as_unread(self, email_id: int):
        """Mark an email as unread.

        Args:
            email_id: Email ID to mark as unread
        """
        if not self._connection:
            raise Exception("Not connected to IMAP server")

        try:
            self._connection.store(str(email_id).encode(), '-FLAGS', '\\Seen')
            logger.debug(f"Marked email {email_id} as unread")
        except Exception as e:
            logger.error(f"Failed to mark email as unread: {e}")
            raise

    def delete_email(self, email_id: int):
        """Delete an email.

        Args:
            email_id: Email ID to delete
        """
        if not self._connection:
            raise Exception("Not connected to IMAP server")

        try:
            self._connection.store(str(email_id).encode(), '+FLAGS', '\\Deleted')
            self._connection.expunge()
            logger.debug(f"Deleted email {email_id}")
        except Exception as e:
            logger.error(f"Failed to delete email: {e}")
            raise

    def move_email(self, email_id: int, destination_folder: str):
        """Move an email to another folder.

        Args:
            email_id: Email ID to move
            destination_folder: Destination folder name
        """
        if not self._connection:
            raise Exception("Not connected to IMAP server")

        try:
            # Copy to destination
            self._connection.copy(str(email_id).encode(), destination_folder)

            # Delete from current folder
            self._connection.store(str(email_id).encode(), '+FLAGS', '\\Deleted')
            self._connection.expunge()

            logger.debug(f"Moved email {email_id} to {destination_folder}")
        except Exception as e:
            logger.error(f"Failed to move email: {e}")
            raise

    def get_folder_status(self, folder: str = "INBOX") -> Dict[str, Any]:
        """Get folder status information.

        Args:
            folder: Folder name

        Returns:
            Dict with folder statistics
        """
        if not self._connection:
            self.connect()

        try:
            status, count = self._connection.select(folder)
            total = int(count[0]) if status == 'OK' else 0

            # Get unread count
            status, data = self._connection.search(None, 'UNSEEN')
            unread = len(data[0].split()) if status == 'OK' else 0

            return {
                'folder': folder,
                'total': total,
                'unread': unread,
                'read': total - unread
            }

        except Exception as e:
            logger.error(f"Failed to get folder status: {e}")
            raise

    def verify_connection(self) -> bool:
        """Verify IMAP connection.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.connect()
            self.list_folders()
            self.disconnect()
            return True
        except Exception as e:
            logger.error(f"IMAP connection verification failed: {e}")
            return False

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
