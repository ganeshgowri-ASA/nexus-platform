"""SMTP client for sending emails."""

import asyncio
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr, make_msgid
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging

from src.core.config import settings
from src.modules.email.models import EmailPriority

logger = logging.getLogger(__name__)


class SMTPClient:
    """SMTP client for sending emails."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = True
    ):
        """Initialize SMTP client.

        Args:
            host: SMTP server host
            port: SMTP server port
            username: SMTP username
            password: SMTP password
            use_tls: Whether to use TLS
        """
        self.host = host or settings.email_smtp_host
        self.port = port or settings.email_smtp_port
        self.username = username or settings.email_smtp_username
        self.password = password or settings.email_smtp_password
        self.use_tls = use_tls
        self._connection: Optional[smtplib.SMTP] = None

    def connect(self) -> smtplib.SMTP:
        """Establish SMTP connection.

        Returns:
            SMTP connection object

        Raises:
            ConnectionError: If connection fails
        """
        try:
            logger.info(f"Connecting to SMTP server {self.host}:{self.port}")

            # Create SMTP connection
            smtp = smtplib.SMTP(self.host, self.port, timeout=30)
            smtp.ehlo()

            # Start TLS if enabled
            if self.use_tls:
                context = ssl.create_default_context()
                smtp.starttls(context=context)
                smtp.ehlo()

            # Login if credentials provided
            if self.username and self.password:
                smtp.login(self.username, self.password)

            logger.info("SMTP connection established successfully")
            self._connection = smtp
            return smtp

        except Exception as e:
            logger.error(f"Failed to connect to SMTP server: {e}")
            raise ConnectionError(f"SMTP connection failed: {e}")

    def disconnect(self):
        """Disconnect from SMTP server."""
        if self._connection:
            try:
                self._connection.quit()
                logger.info("SMTP connection closed")
            except Exception as e:
                logger.warning(f"Error closing SMTP connection: {e}")
            finally:
                self._connection = None

    def send_email(
        self,
        to: List[str],
        subject: str,
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
        from_address: Optional[str] = None,
        from_name: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        reply_to: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        priority: EmailPriority = EmailPriority.NORMAL,
        headers: Optional[Dict[str, str]] = None,
        message_id: Optional[str] = None
    ) -> str:
        """Send an email.

        Args:
            to: List of recipient email addresses
            subject: Email subject
            body_text: Plain text body
            body_html: HTML body
            from_address: Sender email address
            from_name: Sender name
            cc: List of CC recipients
            bcc: List of BCC recipients
            reply_to: Reply-to address
            attachments: List of attachment dicts with 'path' and optionally 'filename'
            priority: Email priority
            headers: Additional custom headers
            message_id: Custom message ID

        Returns:
            Message ID of sent email

        Raises:
            ValueError: If invalid parameters
            Exception: If sending fails
        """
        if not to:
            raise ValueError("At least one recipient is required")

        if not body_text and not body_html:
            raise ValueError("Either body_text or body_html must be provided")

        # Create message
        msg = MIMEMultipart('alternative')

        # Set from address
        from_addr = from_address or settings.email_default_sender or self.username
        if not from_addr:
            raise ValueError("From address is required")

        if from_name:
            msg['From'] = formataddr((from_name, from_addr))
        else:
            msg['From'] = from_addr

        # Set recipients
        msg['To'] = ', '.join(to)
        if cc:
            msg['Cc'] = ', '.join(cc)

        # Set subject
        msg['Subject'] = subject

        # Set reply-to
        if reply_to:
            msg['Reply-To'] = reply_to

        # Set message ID
        if message_id:
            msg['Message-ID'] = message_id
        else:
            msg['Message-ID'] = make_msgid()

        # Set priority headers
        if priority == EmailPriority.HIGH or priority == EmailPriority.URGENT:
            msg['X-Priority'] = '1' if priority == EmailPriority.URGENT else '2'
            msg['Importance'] = 'high'
        elif priority == EmailPriority.LOW:
            msg['X-Priority'] = '5'
            msg['Importance'] = 'low'

        # Set custom headers
        if headers:
            for key, value in headers.items():
                msg[key] = value

        # Add text body
        if body_text:
            text_part = MIMEText(body_text, 'plain', 'utf-8')
            msg.attach(text_part)

        # Add HTML body
        if body_html:
            html_part = MIMEText(body_html, 'html', 'utf-8')
            msg.attach(html_part)

        # Add attachments
        if attachments:
            for attachment in attachments:
                self._add_attachment(msg, attachment)

        # Send email
        try:
            # Connect if not already connected
            if not self._connection:
                self.connect()

            # Prepare recipient list
            recipients = to.copy()
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)

            # Send
            logger.info(f"Sending email to {recipients}")
            self._connection.send_message(msg)
            logger.info(f"Email sent successfully. Message-ID: {msg['Message-ID']}")

            return msg['Message-ID']

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise

    def _add_attachment(self, msg: MIMEMultipart, attachment: Dict[str, Any]):
        """Add attachment to message.

        Args:
            msg: MIME message
            attachment: Attachment dict with 'path' and optionally 'filename'
        """
        file_path = Path(attachment['path'])

        if not file_path.exists():
            raise FileNotFoundError(f"Attachment not found: {file_path}")

        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > settings.email_max_attachment_size_mb:
            raise ValueError(
                f"Attachment {file_path.name} is too large "
                f"({file_size_mb:.1f}MB > {settings.email_max_attachment_size_mb}MB)"
            )

        # Read file
        with open(file_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())

        # Encode
        encoders.encode_base64(part)

        # Set filename
        filename = attachment.get('filename', file_path.name)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= {filename}'
        )

        msg.attach(part)
        logger.debug(f"Added attachment: {filename} ({file_size_mb:.2f}MB)")

    def send_bulk(
        self,
        emails: List[Dict[str, Any]],
        batch_size: Optional[int] = None
    ) -> List[str]:
        """Send multiple emails in bulk.

        Args:
            emails: List of email dicts (same format as send_email params)
            batch_size: Number of emails per batch

        Returns:
            List of message IDs
        """
        batch_size = batch_size or settings.email_batch_size
        message_ids = []

        try:
            # Connect once for all emails
            self.connect()

            # Send in batches
            for i in range(0, len(emails), batch_size):
                batch = emails[i:i + batch_size]
                logger.info(f"Sending batch {i // batch_size + 1} ({len(batch)} emails)")

                for email in batch:
                    try:
                        msg_id = self.send_email(**email)
                        message_ids.append(msg_id)
                    except Exception as e:
                        logger.error(f"Failed to send email in batch: {e}")
                        message_ids.append(None)

                # Brief pause between batches
                if i + batch_size < len(emails):
                    asyncio.sleep(1)

        finally:
            self.disconnect()

        return message_ids

    def verify_connection(self) -> bool:
        """Verify SMTP connection.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.connect()
            self.disconnect()
            return True
        except Exception as e:
            logger.error(f"SMTP connection verification failed: {e}")
            return False

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
