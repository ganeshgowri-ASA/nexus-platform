"""
Email Parser

Parse raw email messages into structured format.
"""

import email
import logging
from datetime import datetime
from email.header import decode_header
from email.utils import parseaddr, parsedate_to_datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class EmailParser:
    """
    Email message parser.

    Parses raw email messages (RFC822 format) into structured data.
    """

    def __init__(self):
        """Initialize email parser."""
        pass

    def parse(self, raw_message: bytes) -> Dict[str, Any]:
        """
        Parse a raw email message.

        Args:
            raw_message: Raw message bytes (RFC822 format)

        Returns:
            Dict: Parsed message data
        """
        try:
            # Parse with email library
            msg = email.message_from_bytes(raw_message)

            # Extract all components
            parsed = {
                'message_id': self._generate_message_id(msg),
                'from_address': self._parse_address(msg.get('From', '')),
                'to_addresses': self._parse_address_list(msg.get('To', '')),
                'cc_addresses': self._parse_address_list(msg.get('Cc', '')),
                'bcc_addresses': self._parse_address_list(msg.get('Bcc', '')),
                'reply_to': self._parse_address(msg.get('Reply-To', '')),
                'subject': self._decode_header(msg.get('Subject', '')),
                'date': self._parse_date(msg.get('Date')),
                'body_text': '',
                'body_html': '',
                'attachments': [],
                'inline_images': [],
                'headers': self._extract_headers(msg),
                'raw_content': raw_message,
                'size_bytes': len(raw_message)
            }

            # Extract body and attachments
            self._extract_body_and_attachments(msg, parsed)

            # Set flags
            parsed['has_attachments'] = len(parsed['attachments']) > 0

            # Extract thread info
            parsed['thread_id'] = self._extract_thread_id(msg)

            return parsed

        except Exception as e:
            logger.error(f"Failed to parse email: {e}")
            return self._empty_message()

    def _generate_message_id(self, msg: email.message.Message) -> str:
        """Generate or extract message ID."""
        msg_id = msg.get('Message-ID', '').strip('<>')
        if msg_id:
            return msg_id
        return str(uuid4())

    def _extract_thread_id(self, msg: email.message.Message) -> Optional[str]:
        """Extract thread ID from headers."""
        # Try References header first
        references = msg.get('References', '')
        if references:
            # First message ID in references is thread root
            parts = references.strip().split()
            if parts:
                return parts[0].strip('<>')

        # Try In-Reply-To
        in_reply_to = msg.get('In-Reply-To', '').strip('<>')
        if in_reply_to:
            return in_reply_to

        # No thread info
        return None

    def _decode_header(self, header_value: str) -> str:
        """
        Decode email header (handles encoding).

        Args:
            header_value: Raw header value

        Returns:
            str: Decoded string
        """
        if not header_value:
            return ""

        decoded_parts = []
        for part, encoding in decode_header(header_value):
            if isinstance(part, bytes):
                if encoding:
                    try:
                        decoded_parts.append(part.decode(encoding))
                    except Exception:
                        decoded_parts.append(part.decode('utf-8', errors='ignore'))
                else:
                    decoded_parts.append(part.decode('utf-8', errors='ignore'))
            else:
                decoded_parts.append(str(part))

        return ' '.join(decoded_parts)

    def _parse_address(self, address_str: str) -> str:
        """
        Parse a single email address.

        Args:
            address_str: Address string (e.g., "Name <email@example.com>")

        Returns:
            str: Email address
        """
        if not address_str:
            return ""

        decoded = self._decode_header(address_str)
        _, email_addr = parseaddr(decoded)
        return email_addr

    def _parse_address_list(self, address_str: str) -> List[str]:
        """
        Parse a list of email addresses.

        Args:
            address_str: Comma-separated addresses

        Returns:
            List[str]: Email addresses
        """
        if not address_str:
            return []

        decoded = self._decode_header(address_str)
        addresses = []

        for addr in decoded.split(','):
            addr = addr.strip()
            if addr:
                _, email_addr = parseaddr(addr)
                if email_addr:
                    addresses.append(email_addr)

        return addresses

    def _parse_date(self, date_str: Optional[str]) -> datetime:
        """
        Parse email date header.

        Args:
            date_str: Date header value

        Returns:
            datetime: Parsed datetime
        """
        if not date_str:
            return datetime.utcnow()

        try:
            return parsedate_to_datetime(date_str)
        except Exception as e:
            logger.warning(f"Failed to parse date '{date_str}': {e}")
            return datetime.utcnow()

    def _extract_headers(self, msg: email.message.Message) -> Dict[str, str]:
        """Extract all headers."""
        headers = {}
        for key, value in msg.items():
            headers[key.lower()] = self._decode_header(value)
        return headers

    def _extract_body_and_attachments(
        self,
        msg: email.message.Message,
        parsed: Dict[str, Any]
    ) -> None:
        """
        Extract body content and attachments from message.

        Args:
            msg: Email message
            parsed: Parsed message dict to populate
        """
        if msg.is_multipart():
            # Multipart message
            for part in msg.walk():
                self._process_part(part, parsed)
        else:
            # Single part message
            self._process_part(msg, parsed)

    def _process_part(
        self,
        part: email.message.Message,
        parsed: Dict[str, Any]
    ) -> None:
        """Process a single message part."""
        content_type = part.get_content_type()
        content_disposition = part.get('Content-Disposition', '')

        # Skip multipart containers
        if part.is_multipart():
            return

        # Check if it's an attachment
        if 'attachment' in content_disposition.lower():
            self._extract_attachment(part, parsed)
            return

        # Check for inline images
        if content_type.startswith('image/') and 'inline' in content_disposition.lower():
            self._extract_inline_image(part, parsed)
            return

        # Extract body content
        if content_type == 'text/plain' and not parsed['body_text']:
            parsed['body_text'] = self._get_part_content(part)

        elif content_type == 'text/html' and not parsed['body_html']:
            parsed['body_html'] = self._get_part_content(part)

    def _get_part_content(self, part: email.message.Message) -> str:
        """Get content from a message part."""
        try:
            payload = part.get_payload(decode=True)
            if payload:
                charset = part.get_content_charset() or 'utf-8'
                return payload.decode(charset, errors='ignore')
            return ""
        except Exception as e:
            logger.error(f"Failed to extract part content: {e}")
            return ""

    def _extract_attachment(
        self,
        part: email.message.Message,
        parsed: Dict[str, Any]
    ) -> None:
        """Extract attachment from message part."""
        filename = part.get_filename()
        if filename:
            filename = self._decode_header(filename)

        attachment = {
            'filename': filename or 'attachment',
            'content_type': part.get_content_type(),
            'size': len(part.get_payload(decode=True) or b''),
            'data': part.get_payload(decode=True)
        }

        parsed['attachments'].append(attachment)

    def _extract_inline_image(
        self,
        part: email.message.Message,
        parsed: Dict[str, Any]
    ) -> None:
        """Extract inline image from message part."""
        filename = part.get_filename()
        if filename:
            filename = self._decode_header(filename)

        # Get Content-ID for inline referencing
        content_id = part.get('Content-ID', '').strip('<>')

        inline_image = {
            'filename': filename or 'image',
            'content_type': part.get_content_type(),
            'content_id': content_id,
            'size': len(part.get_payload(decode=True) or b''),
            'data': part.get_payload(decode=True)
        }

        parsed['inline_images'].append(inline_image)

    def _empty_message(self) -> Dict[str, Any]:
        """Return an empty message structure."""
        return {
            'message_id': str(uuid4()),
            'from_address': '',
            'to_addresses': [],
            'cc_addresses': [],
            'bcc_addresses': [],
            'reply_to': None,
            'subject': '',
            'date': datetime.utcnow(),
            'body_text': '',
            'body_html': '',
            'attachments': [],
            'inline_images': [],
            'headers': {},
            'raw_content': b'',
            'size_bytes': 0,
            'has_attachments': False,
            'thread_id': None
        }

    def extract_urls(self, text: str) -> List[str]:
        """
        Extract URLs from text.

        Args:
            text: Text content

        Returns:
            List[str]: Found URLs
        """
        import re

        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)
        return urls

    def extract_email_addresses(self, text: str) -> List[str]:
        """
        Extract email addresses from text.

        Args:
            text: Text content

        Returns:
            List[str]: Found email addresses
        """
        import re

        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return emails

    def extract_phone_numbers(self, text: str) -> List[str]:
        """
        Extract phone numbers from text.

        Args:
            text: Text content

        Returns:
            List[str]: Found phone numbers
        """
        import re

        # Simple phone number patterns
        patterns = [
            r'\+?1?\d{9,15}',  # International
            r'\(\d{3}\)\s*\d{3}-\d{4}',  # (123) 456-7890
            r'\d{3}-\d{3}-\d{4}',  # 123-456-7890
        ]

        numbers = []
        for pattern in patterns:
            numbers.extend(re.findall(pattern, text))

        return numbers

    def extract_calendar_info(self, msg: email.message.Message) -> Optional[Dict[str, Any]]:
        """
        Extract calendar/meeting information from message.

        Args:
            msg: Email message

        Returns:
            Optional[Dict]: Calendar info if found
        """
        # Look for iCalendar attachment
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/calendar':
                    # Found calendar data
                    cal_data = self._get_part_content(part)
                    return self._parse_icalendar(cal_data)

        return None

    def _parse_icalendar(self, ical_data: str) -> Dict[str, Any]:
        """Parse iCalendar data (simple implementation)."""
        # This is a simplified parser
        # For production, use a library like icalendar

        info = {
            'type': 'meeting',
            'summary': '',
            'description': '',
            'location': '',
            'start': None,
            'end': None,
            'organizer': ''
        }

        for line in ical_data.split('\n'):
            line = line.strip()

            if line.startswith('SUMMARY:'):
                info['summary'] = line.split(':', 1)[1]
            elif line.startswith('DESCRIPTION:'):
                info['description'] = line.split(':', 1)[1]
            elif line.startswith('LOCATION:'):
                info['location'] = line.split(':', 1)[1]
            elif line.startswith('ORGANIZER:'):
                organizer = line.split(':', 1)[1]
                # Extract email from MAILTO:
                if 'mailto:' in organizer.lower():
                    info['organizer'] = organizer.split('mailto:', 1)[1]

        return info

    def get_text_preview(self, message: Dict[str, Any], length: int = 200) -> str:
        """
        Get text preview of message.

        Args:
            message: Parsed message
            length: Preview length

        Returns:
            str: Preview text
        """
        text = message.get('body_text', '')

        if not text and message.get('body_html'):
            # Convert HTML to text for preview
            import re
            text = re.sub(r'<[^>]+>', '', message['body_html'])

        # Clean and truncate
        text = ' '.join(text.split())  # Normalize whitespace
        if len(text) > length:
            text = text[:length] + '...'

        return text
