"""
SMTP Protocol Handler

Handles SMTP operations for sending emails.
"""

import asyncio
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Any, List, Optional

logger = logging.getLogger(__name__)


class SMTPHandler:
    """
    SMTP protocol handler for sending emails.

    Supports SMTP with TLS/STARTTLS and OAuth2 authentication.
    """

    def __init__(
        self,
        host: str,
        port: int = 587,
        use_tls: bool = True,
        use_ssl: bool = False,
        username: str = "",
        password: str = "",
        oauth2_token: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize SMTP handler.

        Args:
            host: SMTP server hostname
            port: SMTP server port
            use_tls: Use STARTTLS
            use_ssl: Use SSL from start
            username: Login username
            password: Login password
            oauth2_token: OAuth2 access token
            timeout: Connection timeout
        """
        self.host = host
        self.port = port
        self.use_tls = use_tls
        self.use_ssl = use_ssl
        self.username = username
        self.password = password
        self.oauth2_token = oauth2_token
        self.timeout = timeout

        self.connection: Optional[smtplib.SMTP | smtplib.SMTP_SSL] = None

    async def connect(self) -> bool:
        """
        Connect to SMTP server.

        Returns:
            bool: Success status
        """
        try:
            loop = asyncio.get_event_loop()

            if self.use_ssl:
                # SSL from start
                ssl_context = ssl.create_default_context()
                self.connection = await loop.run_in_executor(
                    None,
                    lambda: smtplib.SMTP_SSL(
                        self.host,
                        self.port,
                        timeout=self.timeout,
                        context=ssl_context
                    )
                )
            else:
                # Regular connection
                self.connection = await loop.run_in_executor(
                    None,
                    lambda: smtplib.SMTP(
                        self.host,
                        self.port,
                        timeout=self.timeout
                    )
                )

                # STARTTLS
                if self.use_tls:
                    ssl_context = ssl.create_default_context()
                    await loop.run_in_executor(
                        None,
                        self.connection.starttls,
                        ssl_context
                    )

            # Authenticate
            if self.oauth2_token:
                await self._oauth2_authenticate()
            elif self.username and self.password:
                await self._password_authenticate()

            logger.info(f"Connected to SMTP server: {self.host}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to SMTP server: {e}")
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

        # Build OAuth2 auth string
        auth_string = f"user={self.username}\x01auth=Bearer {self.oauth2_token}\x01\x01"

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self.connection.docmd,
            "AUTH",
            "XOAUTH2 " + auth_string.encode().decode()
        )

    async def disconnect(self) -> None:
        """Disconnect from SMTP server."""
        if self.connection:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.connection.quit)
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")
            finally:
                self.connection = None

    async def send_message(self, message: Any) -> bool:
        """
        Send an email message.

        Args:
            message: EmailMessage object to send

        Returns:
            bool: Success status
        """
        try:
            # Connect (SMTP connections are typically per-send)
            if not self.connection:
                if not await self.connect():
                    return False

            # Build MIME message
            mime_msg = await self._build_mime_message(message)

            # Send
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.connection.send_message,
                mime_msg
            )

            logger.info(f"Sent email: {message.subject}")

            # Disconnect
            await self.disconnect()

            return True

        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    async def _build_mime_message(self, message: Any) -> MIMEMultipart:
        """
        Build MIME message from EmailMessage object.

        Args:
            message: EmailMessage object

        Returns:
            MIMEMultipart: MIME message
        """
        # Create message container
        msg = MIMEMultipart('alternative')

        # Headers
        msg['Subject'] = message.subject
        msg['From'] = message.from_address
        msg['To'] = ', '.join(message.to_addresses)

        if message.cc_addresses:
            msg['Cc'] = ', '.join(message.cc_addresses)

        if message.reply_to:
            msg['Reply-To'] = message.reply_to

        # Body
        if message.body_text:
            part_text = MIMEText(message.body_text, 'plain', 'utf-8')
            msg.attach(part_text)

        if message.body_html:
            part_html = MIMEText(message.body_html, 'html', 'utf-8')
            msg.attach(part_html)

        # Attachments
        if message.attachments:
            for attachment in message.attachments:
                part = MIMEBase('application', 'octet-stream')

                # Read file
                if 'file_path' in attachment:
                    with open(attachment['file_path'], 'rb') as f:
                        part.set_payload(f.read())
                elif 'data' in attachment:
                    part.set_payload(attachment['data'])

                # Encode
                encoders.encode_base64(part)

                # Add header
                filename = attachment.get('filename', 'attachment')
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {filename}'
                )

                msg.attach(part)

        # Inline images
        if message.inline_images:
            for inline_img in message.inline_images:
                part = MIMEBase('image', inline_img.get('subtype', 'png'))

                # Read image
                if 'file_path' in inline_img:
                    with open(inline_img['file_path'], 'rb') as f:
                        part.set_payload(f.read())
                elif 'data' in inline_img:
                    part.set_payload(inline_img['data'])

                # Encode
                encoders.encode_base64(part)

                # Add header for inline
                cid = inline_img.get('cid', 'image1')
                part.add_header('Content-ID', f'<{cid}>')
                part.add_header(
                    'Content-Disposition',
                    'inline',
                    filename=inline_img.get('filename', 'image.png')
                )

                msg.attach(part)

        return msg

    async def send_raw(
        self,
        from_address: str,
        to_addresses: List[str],
        message: str
    ) -> bool:
        """
        Send a raw email message.

        Args:
            from_address: Sender address
            to_addresses: Recipient addresses
            message: Raw message string

        Returns:
            bool: Success status
        """
        try:
            # Connect
            if not self.connection:
                if not await self.connect():
                    return False

            # Send
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.connection.sendmail,
                from_address,
                to_addresses,
                message
            )

            # Disconnect
            await self.disconnect()

            return True

        except Exception as e:
            logger.error(f"Failed to send raw message: {e}")
            return False

    async def verify_address(self, email_address: str) -> bool:
        """
        Verify if an email address exists (VRFY command).

        Args:
            email_address: Email address to verify

        Returns:
            bool: True if address exists
        """
        try:
            if not self.connection:
                if not await self.connect():
                    return False

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.connection.verify,
                email_address
            )

            return result[0] == 250

        except Exception as e:
            logger.error(f"Failed to verify address {email_address}: {e}")
            return False
        finally:
            await self.disconnect()

    async def test_connection(self) -> bool:
        """
        Test SMTP connection.

        Returns:
            bool: True if connection successful
        """
        try:
            if await self.connect():
                await self.disconnect()
                return True
            return False

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
