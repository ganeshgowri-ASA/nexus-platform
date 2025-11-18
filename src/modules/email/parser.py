"""Email parser for parsing and extracting email content."""

import email
from email.message import Message
from email.header import decode_header
from email.utils import parseaddr, parsedate_to_datetime
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import re
import logging

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class EmailParser:
    """Parser for email messages."""

    @staticmethod
    def decode_header_value(header_value: str) -> str:
        """Decode email header value.

        Args:
            header_value: Raw header value

        Returns:
            Decoded header value
        """
        if not header_value:
            return ""

        decoded_parts = []
        for part, encoding in decode_header(header_value):
            if isinstance(part, bytes):
                try:
                    decoded_parts.append(
                        part.decode(encoding or 'utf-8', errors='replace')
                    )
                except Exception:
                    decoded_parts.append(part.decode('utf-8', errors='replace'))
            else:
                decoded_parts.append(str(part))

        return ' '.join(decoded_parts)

    @staticmethod
    def parse_email_address(address: str) -> Tuple[str, str]:
        """Parse email address into name and email.

        Args:
            address: Email address string

        Returns:
            Tuple of (name, email)
        """
        name, email_addr = parseaddr(address)
        name = EmailParser.decode_header_value(name)
        return name, email_addr

    @staticmethod
    def parse_email_addresses(addresses: str) -> List[Dict[str, str]]:
        """Parse multiple email addresses.

        Args:
            addresses: Comma-separated email addresses

        Returns:
            List of dicts with 'name' and 'email'
        """
        if not addresses:
            return []

        result = []
        for addr in addresses.split(','):
            name, email_addr = EmailParser.parse_email_address(addr.strip())
            if email_addr:
                result.append({'name': name, 'email': email_addr})

        return result

    @staticmethod
    def extract_text_from_html(html: str) -> str:
        """Extract plain text from HTML.

        Args:
            html: HTML content

        Returns:
            Plain text content
        """
        try:
            soup = BeautifulSoup(html, 'lxml')

            # Remove script and style elements
            for script in soup(['script', 'style']):
                script.decompose()

            # Get text
            text = soup.get_text()

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)

            return text

        except Exception as e:
            logger.error(f"Failed to extract text from HTML: {e}")
            return html

    @staticmethod
    def get_email_body(msg: Message) -> Dict[str, Optional[str]]:
        """Extract email body (text and HTML).

        Args:
            msg: Email message object

        Returns:
            Dict with 'text' and 'html' keys
        """
        body_text = None
        body_html = None

        if msg.is_multipart():
            # Process multipart message
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition', ''))

                # Skip attachments
                if 'attachment' in content_disposition:
                    continue

                try:
                    payload = part.get_payload(decode=True)
                    if not payload:
                        continue

                    charset = part.get_content_charset() or 'utf-8'
                    decoded_payload = payload.decode(charset, errors='replace')

                    if content_type == 'text/plain' and not body_text:
                        body_text = decoded_payload
                    elif content_type == 'text/html' and not body_html:
                        body_html = decoded_payload

                except Exception as e:
                    logger.error(f"Failed to decode message part: {e}")
                    continue

        else:
            # Process single-part message
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or 'utf-8'
                    decoded_payload = payload.decode(charset, errors='replace')

                    content_type = msg.get_content_type()
                    if content_type == 'text/plain':
                        body_text = decoded_payload
                    elif content_type == 'text/html':
                        body_html = decoded_payload

            except Exception as e:
                logger.error(f"Failed to decode message: {e}")

        # If only HTML is available, extract text from it
        if body_html and not body_text:
            body_text = EmailParser.extract_text_from_html(body_html)

        return {
            'text': body_text,
            'html': body_html
        }

    @staticmethod
    def get_attachments_info(msg: Message) -> List[Dict[str, Any]]:
        """Get information about email attachments.

        Args:
            msg: Email message object

        Returns:
            List of attachment info dicts
        """
        attachments = []

        if not msg.is_multipart():
            return attachments

        for part in msg.walk():
            content_disposition = part.get('Content-Disposition', '')

            if 'attachment' in str(content_disposition) or part.get_filename():
                filename = part.get_filename()
                if filename:
                    filename = EmailParser.decode_header_value(filename)

                content_type = part.get_content_type()
                content_id = part.get('Content-ID', '').strip('<>')

                # Get size
                payload = part.get_payload(decode=True)
                size = len(payload) if payload else 0

                attachments.append({
                    'filename': filename or 'unnamed',
                    'content_type': content_type,
                    'content_id': content_id,
                    'size': size,
                    'is_inline': 'inline' in str(content_disposition),
                    'part': part  # Keep reference to part for extraction
                })

        return attachments

    @staticmethod
    def parse_message(msg: Message) -> Dict[str, Any]:
        """Parse email message into structured data.

        Args:
            msg: Email message object

        Returns:
            Dict with parsed email data
        """
        # Parse headers
        subject = EmailParser.decode_header_value(msg.get('Subject', ''))
        message_id = msg.get('Message-ID', '')
        in_reply_to = msg.get('In-Reply-To', '')
        references = msg.get('References', '')

        # Parse addresses
        from_name, from_email = EmailParser.parse_email_address(msg.get('From', ''))
        to_addresses = EmailParser.parse_email_addresses(msg.get('To', ''))
        cc_addresses = EmailParser.parse_email_addresses(msg.get('Cc', ''))
        reply_to = msg.get('Reply-To', '')

        # Parse date
        date_str = msg.get('Date', '')
        try:
            date = parsedate_to_datetime(date_str) if date_str else None
        except Exception as e:
            logger.error(f"Failed to parse date: {e}")
            date = None

        # Extract body
        body = EmailParser.get_email_body(msg)

        # Get attachments info
        attachments = EmailParser.get_attachments_info(msg)

        # Parse priority
        priority = 'normal'
        x_priority = msg.get('X-Priority', '')
        if x_priority in ['1', '2']:
            priority = 'high' if x_priority == '2' else 'urgent'
        elif x_priority == '5':
            priority = 'low'

        return {
            'message_id': message_id,
            'in_reply_to': in_reply_to,
            'references': references,
            'subject': subject,
            'from_name': from_name,
            'from_email': from_email,
            'to_addresses': to_addresses,
            'cc_addresses': cc_addresses,
            'reply_to': reply_to,
            'date': date,
            'body_text': body['text'],
            'body_html': body['html'],
            'attachments': attachments,
            'priority': priority,
            'headers': dict(msg.items())
        }

    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """Extract URLs from text.

        Args:
            text: Text to extract URLs from

        Returns:
            List of URLs
        """
        if not text:
            return []

        # URL regex pattern
        url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )

        urls = url_pattern.findall(text)
        return list(set(urls))  # Remove duplicates

    @staticmethod
    def extract_email_addresses(text: str) -> List[str]:
        """Extract email addresses from text.

        Args:
            text: Text to extract email addresses from

        Returns:
            List of email addresses
        """
        if not text:
            return []

        # Email regex pattern
        email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )

        emails = email_pattern.findall(text)
        return list(set(emails))  # Remove duplicates

    @staticmethod
    def is_reply(msg: Message) -> bool:
        """Check if email is a reply.

        Args:
            msg: Email message object

        Returns:
            True if email is a reply
        """
        in_reply_to = msg.get('In-Reply-To', '')
        references = msg.get('References', '')
        subject = msg.get('Subject', '')

        return bool(in_reply_to or references or subject.lower().startswith('re:'))

    @staticmethod
    def is_forward(msg: Message) -> bool:
        """Check if email is a forward.

        Args:
            msg: Email message object

        Returns:
            True if email is a forward
        """
        subject = msg.get('Subject', '')
        return subject.lower().startswith('fwd:') or subject.lower().startswith('fw:')

    @staticmethod
    def get_thread_id(msg: Message) -> Optional[str]:
        """Get email thread ID.

        Args:
            msg: Email message object

        Returns:
            Thread ID (using References or In-Reply-To)
        """
        references = msg.get('References', '')
        in_reply_to = msg.get('In-Reply-To', '')

        if references:
            # Use first message ID in references as thread ID
            return references.split()[0].strip('<>')
        elif in_reply_to:
            return in_reply_to.strip('<>')
        else:
            # Use message ID as thread starter
            return msg.get('Message-ID', '').strip('<>')
