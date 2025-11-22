"""
IMAP Protocol Handler

Handles IMAP operations for receiving and managing emails.
"""

import asyncio
import email
import imaplib
import logging
import ssl
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class IMAPHandler:
    """
    IMAP protocol handler for receiving emails.

    Supports IMAP4 with SSL/TLS and OAuth2 authentication.
    """

    def __init__(
        self,
        host: str,
        port: int = 993,
        use_ssl: bool = True,
        username: str = "",
        password: str = "",
        oauth2_token: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize IMAP handler.

        Args:
            host: IMAP server hostname
            port: IMAP server port
            use_ssl: Use SSL connection
            username: Login username
            password: Login password
            oauth2_token: OAuth2 access token
            timeout: Connection timeout in seconds
        """
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.username = username
        self.password = password
        self.oauth2_token = oauth2_token
        self.timeout = timeout

        self.connection: Optional[imaplib.IMAP4_SSL | imaplib.IMAP4] = None
        self.is_connected: bool = False
        self.current_folder: Optional[str] = None

    async def connect(self) -> bool:
        """
        Connect to IMAP server.

        Returns:
            bool: Success status
        """
        try:
            # Create connection
            if self.use_ssl:
                ssl_context = ssl.create_default_context()
                self.connection = imaplib.IMAP4_SSL(
                    self.host,
                    self.port,
                    ssl_context=ssl_context,
                    timeout=self.timeout
                )
            else:
                self.connection = imaplib.IMAP4(self.host, self.port)

            # Authenticate
            if self.oauth2_token:
                await self._oauth2_authenticate()
            else:
                await self._password_authenticate()

            self.is_connected = True
            logger.info(f"Connected to IMAP server: {self.host}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to IMAP server: {e}")
            self.is_connected = False
            return False

    async def _password_authenticate(self) -> None:
        """Authenticate using username/password."""
        if not self.connection:
            raise RuntimeError("No connection established")

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self.connection.login,
            self.username,
            self.password
        )

    async def _oauth2_authenticate(self) -> None:
        """Authenticate using OAuth2."""
        if not self.connection:
            raise RuntimeError("No connection established")

        # Build OAuth2 string
        auth_string = f"user={self.username}\x01auth=Bearer {self.oauth2_token}\x01\x01"

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self.connection.authenticate,
            "XOAUTH2",
            lambda x: auth_string
        )

    async def disconnect(self) -> None:
        """Disconnect from IMAP server."""
        if self.connection and self.is_connected:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.connection.logout)
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")
            finally:
                self.connection = None
                self.is_connected = False
                self.current_folder = None

    async def select_folder(self, folder: str = "INBOX", readonly: bool = False) -> bool:
        """
        Select a folder/mailbox.

        Args:
            folder: Folder name
            readonly: Open in readonly mode

        Returns:
            bool: Success status
        """
        if not self.connection:
            return False

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.connection.select,
                folder,
                readonly
            )

            if result[0] == "OK":
                self.current_folder = folder
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to select folder {folder}: {e}")
            return False

    async def list_folders(self) -> List[str]:
        """
        List all folders/mailboxes.

        Returns:
            List[str]: Folder names
        """
        if not self.connection:
            return []

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.connection.list
            )

            if result[0] != "OK":
                return []

            folders = []
            for item in result[1]:
                # Parse folder list response
                # Format: (flags) "delimiter" "name"
                if isinstance(item, bytes):
                    item = item.decode()

                parts = item.split('"')
                if len(parts) >= 3:
                    folder_name = parts[-2]
                    folders.append(folder_name)

            return folders

        except Exception as e:
            logger.error(f"Failed to list folders: {e}")
            return []

    async def create_folder(self, folder_name: str) -> bool:
        """
        Create a new folder.

        Args:
            folder_name: Name for new folder

        Returns:
            bool: Success status
        """
        if not self.connection:
            return False

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.connection.create,
                folder_name
            )
            return result[0] == "OK"

        except Exception as e:
            logger.error(f"Failed to create folder {folder_name}: {e}")
            return False

    async def delete_folder(self, folder_name: str) -> bool:
        """Delete a folder."""
        if not self.connection:
            return False

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.connection.delete,
                folder_name
            )
            return result[0] == "OK"

        except Exception as e:
            logger.error(f"Failed to delete folder {folder_name}: {e}")
            return False

    async def search(self, criteria: str = "ALL") -> List[str]:
        """
        Search for messages.

        Args:
            criteria: IMAP search criteria (e.g., "ALL", "UNSEEN", "FROM user@example.com")

        Returns:
            List[str]: Message IDs
        """
        if not self.connection:
            return []

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.connection.search,
                None,
                criteria
            )

            if result[0] != "OK":
                return []

            # Parse message IDs
            message_ids = result[1][0].split()
            return [mid.decode() if isinstance(mid, bytes) else mid for mid in message_ids]

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def fetch_messages(
        self,
        folder: str = "INBOX",
        limit: int = 50,
        criteria: Optional[str] = None
    ) -> List[bytes]:
        """
        Fetch messages from a folder.

        Args:
            folder: Folder to fetch from
            limit: Maximum number of messages
            criteria: Search criteria

        Returns:
            List[bytes]: Raw message data
        """
        # Select folder
        if not await self.select_folder(folder):
            return []

        # Search for messages
        search_criteria = criteria or "ALL"
        message_ids = await self.search(search_criteria)

        # Limit results
        message_ids = message_ids[-limit:] if len(message_ids) > limit else message_ids

        # Fetch messages
        messages = []
        for msg_id in message_ids:
            msg_data = await self.fetch_message(msg_id)
            if msg_data:
                messages.append(msg_data)

        return messages

    async def fetch_message(self, message_id: str) -> Optional[bytes]:
        """
        Fetch a single message by ID.

        Args:
            message_id: Message ID

        Returns:
            Optional[bytes]: Raw message data
        """
        if not self.connection:
            return None

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.connection.fetch,
                message_id,
                "(RFC822)"
            )

            if result[0] != "OK":
                return None

            # Extract message data
            msg_data = result[1][0]
            if isinstance(msg_data, tuple):
                return msg_data[1]
            return None

        except Exception as e:
            logger.error(f"Failed to fetch message {message_id}: {e}")
            return None

    async def fetch_message_headers(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch only message headers.

        Args:
            message_id: Message ID

        Returns:
            Optional[Dict]: Message headers
        """
        if not self.connection:
            return None

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.connection.fetch,
                message_id,
                "(BODY[HEADER])"
            )

            if result[0] != "OK":
                return None

            # Parse headers
            header_data = result[1][0][1]
            msg = email.message_from_bytes(header_data)

            headers = {}
            for key, value in msg.items():
                headers[key.lower()] = value

            return headers

        except Exception as e:
            logger.error(f"Failed to fetch headers for {message_id}: {e}")
            return None

    async def set_flag(self, message_id: str, flag: str, value: bool = True) -> bool:
        """
        Set/unset a flag on a message.

        Args:
            message_id: Message ID
            flag: Flag name (e.g., "\\Seen", "\\Flagged", "\\Deleted")
            value: Set (True) or unset (False)

        Returns:
            bool: Success status
        """
        if not self.connection:
            return False

        try:
            loop = asyncio.get_event_loop()

            if value:
                result = await loop.run_in_executor(
                    None,
                    self.connection.store,
                    message_id,
                    "+FLAGS",
                    flag
                )
            else:
                result = await loop.run_in_executor(
                    None,
                    self.connection.store,
                    message_id,
                    "-FLAGS",
                    flag
                )

            return result[0] == "OK"

        except Exception as e:
            logger.error(f"Failed to set flag on message {message_id}: {e}")
            return False

    async def move_message(self, message_id: str, destination_folder: str) -> bool:
        """
        Move a message to another folder.

        Args:
            message_id: Message ID
            destination_folder: Destination folder name

        Returns:
            bool: Success status
        """
        if not self.connection:
            return False

        try:
            loop = asyncio.get_event_loop()

            # Copy to destination
            result = await loop.run_in_executor(
                None,
                self.connection.copy,
                message_id,
                destination_folder
            )

            if result[0] != "OK":
                return False

            # Mark as deleted in source
            await self.set_flag(message_id, "\\Deleted", True)

            # Expunge to permanently remove
            await loop.run_in_executor(None, self.connection.expunge)

            return True

        except Exception as e:
            logger.error(f"Failed to move message {message_id}: {e}")
            return False

    async def delete_message(self, message_id: str) -> bool:
        """
        Permanently delete a message.

        Args:
            message_id: Message ID

        Returns:
            bool: Success status
        """
        if not self.connection:
            return False

        try:
            # Mark as deleted
            if not await self.set_flag(message_id, "\\Deleted", True):
                return False

            # Expunge
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.connection.expunge)

            return True

        except Exception as e:
            logger.error(f"Failed to delete message {message_id}: {e}")
            return False

    async def append_message(self, folder: str, message: Any) -> bool:
        """
        Append a message to a folder (e.g., save to Sent).

        Args:
            folder: Folder name
            message: EmailMessage object or raw message

        Returns:
            bool: Success status
        """
        if not self.connection:
            return False

        try:
            # Convert message to RFC822 format
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            if hasattr(message, 'body_html'):
                # EmailMessage object
                msg = MIMEMultipart('alternative')
                msg['Subject'] = message.subject
                msg['From'] = message.from_address
                msg['To'] = ', '.join(message.to_addresses)

                if message.body_text:
                    msg.attach(MIMEText(message.body_text, 'plain'))
                if message.body_html:
                    msg.attach(MIMEText(message.body_html, 'html'))

                message_data = msg.as_bytes()
            else:
                # Raw message
                message_data = message

            # Append to folder
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.connection.append,
                folder,
                None,
                None,
                message_data
            )

            return result[0] == "OK"

        except Exception as e:
            logger.error(f"Failed to append message to {folder}: {e}")
            return False

    async def get_folder_status(self, folder: str) -> Dict[str, int]:
        """
        Get folder status (message count, etc.).

        Args:
            folder: Folder name

        Returns:
            Dict: Status information
        """
        if not self.connection:
            return {}

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.connection.status,
                folder,
                "(MESSAGES RECENT UNSEEN)"
            )

            if result[0] != "OK":
                return {}

            # Parse status response
            status_str = result[1][0].decode() if isinstance(result[1][0], bytes) else result[1][0]

            status = {}
            parts = status_str.split()
            for i in range(1, len(parts), 2):
                if i + 1 < len(parts):
                    key = parts[i].strip('()')
                    value = int(parts[i + 1].strip('()'))
                    status[key.lower()] = value

            return status

        except Exception as e:
            logger.error(f"Failed to get folder status for {folder}: {e}")
            return {}

    async def idle(self, timeout: int = 300) -> bool:
        """
        Enter IDLE mode to wait for new messages.

        Args:
            timeout: Idle timeout in seconds

        Returns:
            bool: True if new messages arrived
        """
        if not self.connection:
            return False

        try:
            loop = asyncio.get_event_loop()

            # Start IDLE
            tag = await loop.run_in_executor(
                None,
                self.connection._simple_command,
                "IDLE"
            )

            # Wait for response or timeout
            await asyncio.sleep(timeout)

            # End IDLE
            await loop.run_in_executor(
                None,
                self.connection.send,
                b"DONE\r\n"
            )

            return True

        except Exception as e:
            logger.error(f"IDLE failed: {e}")
            return False
