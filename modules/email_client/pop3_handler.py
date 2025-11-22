"""
POP3 Protocol Handler

Handles POP3 operations for receiving emails.
"""

import asyncio
import logging
import poplib
import ssl
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class POP3Handler:
    """
    POP3 protocol handler for receiving emails.

    Supports POP3 with SSL.
    """

    def __init__(
        self,
        host: str,
        port: int = 995,
        use_ssl: bool = True,
        username: str = "",
        password: str = "",
        timeout: int = 30
    ):
        """
        Initialize POP3 handler.

        Args:
            host: POP3 server hostname
            port: POP3 server port
            use_ssl: Use SSL connection
            username: Login username
            password: Login password
            timeout: Connection timeout
        """
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.username = username
        self.password = password
        self.timeout = timeout

        self.connection: Optional[poplib.POP3_SSL | poplib.POP3] = None
        self.is_connected: bool = False

    async def connect(self) -> bool:
        """
        Connect to POP3 server.

        Returns:
            bool: Success status
        """
        try:
            loop = asyncio.get_event_loop()

            if self.use_ssl:
                ssl_context = ssl.create_default_context()
                self.connection = await loop.run_in_executor(
                    None,
                    lambda: poplib.POP3_SSL(
                        self.host,
                        self.port,
                        timeout=self.timeout,
                        context=ssl_context
                    )
                )
            else:
                self.connection = await loop.run_in_executor(
                    None,
                    lambda: poplib.POP3(self.host, self.port, timeout=self.timeout)
                )

            # Authenticate
            await loop.run_in_executor(
                None,
                self.connection.user,
                self.username
            )
            await loop.run_in_executor(
                None,
                self.connection.pass_,
                self.password
            )

            self.is_connected = True
            logger.info(f"Connected to POP3 server: {self.host}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to POP3 server: {e}")
            self.is_connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from POP3 server."""
        if self.connection and self.is_connected:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.connection.quit)
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")
            finally:
                self.connection = None
                self.is_connected = False

    async def get_message_count(self) -> int:
        """
        Get number of messages in mailbox.

        Returns:
            int: Message count
        """
        if not self.connection:
            return 0

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.connection.stat)
            return result[0]  # (message_count, mailbox_size)

        except Exception as e:
            logger.error(f"Failed to get message count: {e}")
            return 0

    async def get_mailbox_size(self) -> int:
        """
        Get total size of mailbox in bytes.

        Returns:
            int: Mailbox size
        """
        if not self.connection:
            return 0

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.connection.stat)
            return result[1]  # (message_count, mailbox_size)

        except Exception as e:
            logger.error(f"Failed to get mailbox size: {e}")
            return 0

    async def list_messages(self) -> List[Tuple[int, int]]:
        """
        List all messages with their sizes.

        Returns:
            List[Tuple[int, int]]: List of (message_number, size) tuples
        """
        if not self.connection:
            return []

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.connection.list)

            messages = []
            for item in result[1]:
                parts = item.decode().split()
                if len(parts) >= 2:
                    msg_num = int(parts[0])
                    msg_size = int(parts[1])
                    messages.append((msg_num, msg_size))

            return messages

        except Exception as e:
            logger.error(f"Failed to list messages: {e}")
            return []

    async def fetch_message(self, message_number: int) -> Optional[bytes]:
        """
        Fetch a complete message.

        Args:
            message_number: Message number (1-indexed)

        Returns:
            Optional[bytes]: Raw message data
        """
        if not self.connection:
            return None

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.connection.retr,
                message_number
            )

            # Combine lines into single message
            lines = result[1]
            message = b'\n'.join(lines)

            return message

        except Exception as e:
            logger.error(f"Failed to fetch message {message_number}: {e}")
            return None

    async def fetch_messages(
        self,
        limit: Optional[int] = None,
        delete_after_fetch: bool = False
    ) -> List[bytes]:
        """
        Fetch multiple messages.

        Args:
            limit: Maximum number of messages to fetch
            delete_after_fetch: Delete messages after fetching

        Returns:
            List[bytes]: Raw message data
        """
        messages = []

        # Get message list
        msg_list = await self.list_messages()

        # Apply limit
        if limit:
            msg_list = msg_list[:limit]

        # Fetch each message
        for msg_num, _ in msg_list:
            msg_data = await self.fetch_message(msg_num)
            if msg_data:
                messages.append(msg_data)

                # Delete if requested
                if delete_after_fetch:
                    await self.delete_message(msg_num)

        return messages

    async def fetch_message_headers(self, message_number: int, num_lines: int = 0) -> Optional[bytes]:
        """
        Fetch message headers (and optionally top N lines).

        Args:
            message_number: Message number
            num_lines: Number of body lines to include

        Returns:
            Optional[bytes]: Message headers
        """
        if not self.connection:
            return None

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.connection.top,
                message_number,
                num_lines
            )

            # Combine lines
            lines = result[1]
            headers = b'\n'.join(lines)

            return headers

        except Exception as e:
            logger.error(f"Failed to fetch headers for message {message_number}: {e}")
            return None

    async def delete_message(self, message_number: int) -> bool:
        """
        Mark a message for deletion.

        Args:
            message_number: Message number

        Returns:
            bool: Success status
        """
        if not self.connection:
            return False

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.connection.dele,
                message_number
            )
            return True

        except Exception as e:
            logger.error(f"Failed to delete message {message_number}: {e}")
            return False

    async def reset_deletions(self) -> bool:
        """
        Unmark all messages marked for deletion.

        Returns:
            bool: Success status
        """
        if not self.connection:
            return False

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.connection.rset)
            return True

        except Exception as e:
            logger.error(f"Failed to reset deletions: {e}")
            return False

    async def get_unique_id(self, message_number: int) -> Optional[str]:
        """
        Get unique ID for a message.

        Args:
            message_number: Message number

        Returns:
            Optional[str]: Unique ID
        """
        if not self.connection:
            return None

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.connection.uidl,
                message_number
            )

            # Parse UIDL response
            parts = result.decode().split()
            if len(parts) >= 2:
                return parts[1]

            return None

        except Exception as e:
            logger.error(f"Failed to get UID for message {message_number}: {e}")
            return None

    async def list_unique_ids(self) -> List[Tuple[int, str]]:
        """
        List all messages with their unique IDs.

        Returns:
            List[Tuple[int, str]]: List of (message_number, uid) tuples
        """
        if not self.connection:
            return []

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.connection.uidl)

            uids = []
            for item in result[1]:
                parts = item.decode().split()
                if len(parts) >= 2:
                    msg_num = int(parts[0])
                    uid = parts[1]
                    uids.append((msg_num, uid))

            return uids

        except Exception as e:
            logger.error(f"Failed to list UIDs: {e}")
            return []

    async def noop(self) -> bool:
        """
        Send NOOP command to keep connection alive.

        Returns:
            bool: Success status
        """
        if not self.connection:
            return False

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.connection.noop)
            return True

        except Exception as e:
            logger.error(f"NOOP failed: {e}")
            return False
