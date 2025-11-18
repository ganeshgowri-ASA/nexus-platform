"""
Email Composition Module

Rich email composition with templates, formatting, and scheduling.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class EmailTemplate:
    """Email template for reusable content."""
    template_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    subject: str = ""
    body_html: str = ""
    body_text: str = ""
    variables: List[str] = field(default_factory=list)  # Variable placeholders
    category: str = "general"
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EmailSignature:
    """Email signature."""
    signature_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    html_content: str = ""
    text_content: str = ""
    is_default: bool = False


class EmailComposer:
    """
    Email composition engine.

    Provides rich email composition with templates, formatting, and scheduling.
    """

    def __init__(self, db_connection: Optional[Any] = None):
        """
        Initialize email composer.

        Args:
            db_connection: Database connection for templates/signatures
        """
        self.db_connection = db_connection
        self.templates: Dict[str, EmailTemplate] = {}
        self.signatures: Dict[str, EmailSignature] = {}

    def create_message(
        self,
        from_address: str,
        to_addresses: List[str],
        subject: str,
        body: str,
        is_html: bool = True,
        cc_addresses: Optional[List[str]] = None,
        bcc_addresses: Optional[List[str]] = None,
        reply_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new email message.

        Args:
            from_address: Sender email
            to_addresses: Recipient emails
            subject: Email subject
            body: Email body content
            is_html: Whether body is HTML
            cc_addresses: CC recipients
            bcc_addresses: BCC recipients
            reply_to: Reply-to address

        Returns:
            Dict: Email message data
        """
        message = {
            'message_id': str(uuid4()),
            'from_address': from_address,
            'to_addresses': to_addresses,
            'cc_addresses': cc_addresses or [],
            'bcc_addresses': bcc_addresses or [],
            'reply_to': reply_to,
            'subject': subject,
            'body_html': body if is_html else self._text_to_html(body),
            'body_text': self._html_to_text(body) if is_html else body,
            'attachments': [],
            'inline_images': [],
            'date': datetime.utcnow(),
            'is_draft': False
        }

        return message

    def create_reply(
        self,
        original_message: Dict[str, Any],
        body: str,
        is_html: bool = True,
        reply_all: bool = False
    ) -> Dict[str, Any]:
        """
        Create a reply to an email.

        Args:
            original_message: Original message to reply to
            body: Reply body
            is_html: Whether body is HTML
            reply_all: Reply to all recipients

        Returns:
            Dict: Reply message data
        """
        # Determine recipients
        to_addresses = [original_message.get('from_address', '')]

        if reply_all:
            # Include original TO and CC (excluding self)
            to_addresses.extend(original_message.get('to_addresses', []))
            cc_addresses = original_message.get('cc_addresses', [])
        else:
            cc_addresses = []

        # Format subject
        subject = original_message.get('subject', '')
        if not subject.lower().startswith('re:'):
            subject = f"Re: {subject}"

        # Format body with quoted original
        quoted_body = self._quote_message(original_message)
        full_body = f"{body}<br><br>{quoted_body}" if is_html else f"{body}\n\n{quoted_body}"

        message = self.create_message(
            from_address="",  # Will be set by EmailClient
            to_addresses=to_addresses,
            subject=subject,
            body=full_body,
            is_html=is_html,
            cc_addresses=cc_addresses,
            reply_to=None
        )

        message['thread_id'] = original_message.get('thread_id') or original_message.get('message_id')

        return message

    def create_forward(
        self,
        original_message: Dict[str, Any],
        to_addresses: List[str],
        body: str = "",
        is_html: bool = True
    ) -> Dict[str, Any]:
        """
        Create a forwarded email.

        Args:
            original_message: Original message to forward
            to_addresses: New recipients
            body: Additional message to add
            is_html: Whether body is HTML

        Returns:
            Dict: Forward message data
        """
        # Format subject
        subject = original_message.get('subject', '')
        if not subject.lower().startswith('fwd:'):
            subject = f"Fwd: {subject}"

        # Format forwarded content
        forwarded_content = self._format_forwarded_message(original_message)

        full_body = f"{body}<br><br>{forwarded_content}" if body else forwarded_content

        message = self.create_message(
            from_address="",  # Will be set by EmailClient
            to_addresses=to_addresses,
            subject=subject,
            body=full_body,
            is_html=is_html
        )

        # Copy attachments
        message['attachments'] = original_message.get('attachments', []).copy()

        return message

    def _quote_message(self, message: Dict[str, Any]) -> str:
        """Format a message as a quote for reply."""
        from_addr = message.get('from_address', '')
        date = message.get('date', datetime.utcnow())
        body = message.get('body_html', message.get('body_text', ''))

        quoted = f"""
        <blockquote style="margin: 0 0 0 .8ex; border-left: 1px #ccc solid; padding-left: 1ex;">
            <div>On {date.strftime('%Y-%m-%d %H:%M')}, {from_addr} wrote:</div>
            <br>
            {body}
        </blockquote>
        """

        return quoted

    def _format_forwarded_message(self, message: Dict[str, Any]) -> str:
        """Format a message for forwarding."""
        headers = f"""
        <div style="border-left: 2px solid #0066cc; padding-left: 10px; margin: 10px 0;">
            <strong>---------- Forwarded message ----------</strong><br>
            <strong>From:</strong> {message.get('from_address', '')}<br>
            <strong>Date:</strong> {message.get('date', datetime.utcnow()).strftime('%Y-%m-%d %H:%M')}<br>
            <strong>Subject:</strong> {message.get('subject', '')}<br>
            <strong>To:</strong> {', '.join(message.get('to_addresses', []))}<br>
            <br>
            {message.get('body_html', message.get('body_text', ''))}
        </div>
        """

        return headers

    def create_from_template(
        self,
        template_id: str,
        variables: Dict[str, str],
        to_addresses: List[str],
        from_address: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        Create a message from a template.

        Args:
            template_id: Template ID
            variables: Variable substitutions
            to_addresses: Recipients
            from_address: Sender

        Returns:
            Optional[Dict]: Message data
        """
        template = self.templates.get(template_id)
        if not template:
            logger.error(f"Template {template_id} not found")
            return None

        # Substitute variables
        subject = template.subject
        body_html = template.body_html
        body_text = template.body_text

        for var_name, var_value in variables.items():
            placeholder = f"{{{{{var_name}}}}}"  # {{variable}}
            subject = subject.replace(placeholder, var_value)
            body_html = body_html.replace(placeholder, var_value)
            body_text = body_text.replace(placeholder, var_value)

        return self.create_message(
            from_address=from_address,
            to_addresses=to_addresses,
            subject=subject,
            body=body_html,
            is_html=True
        )

    def add_template(self, template: EmailTemplate) -> str:
        """
        Add an email template.

        Args:
            template: Email template

        Returns:
            str: Template ID
        """
        self.templates[template.template_id] = template
        logger.info(f"Added template: {template.name}")
        return template.template_id

    def remove_template(self, template_id: str) -> bool:
        """Remove a template."""
        if template_id in self.templates:
            del self.templates[template_id]
            return True
        return False

    def list_templates(self, category: Optional[str] = None) -> List[EmailTemplate]:
        """
        List available templates.

        Args:
            category: Filter by category

        Returns:
            List[EmailTemplate]: Templates
        """
        templates = list(self.templates.values())

        if category:
            templates = [t for t in templates if t.category == category]

        return templates

    def add_signature(self, signature: EmailSignature) -> str:
        """
        Add an email signature.

        Args:
            signature: Email signature

        Returns:
            str: Signature ID
        """
        # If setting as default, unset other defaults
        if signature.is_default:
            for sig in self.signatures.values():
                sig.is_default = False

        self.signatures[signature.signature_id] = signature
        logger.info(f"Added signature: {signature.name}")
        return signature.signature_id

    def remove_signature(self, signature_id: str) -> bool:
        """Remove a signature."""
        if signature_id in self.signatures:
            del self.signatures[signature_id]
            return True
        return False

    def get_default_signature(self) -> Optional[EmailSignature]:
        """Get the default signature."""
        for sig in self.signatures.values():
            if sig.is_default:
                return sig
        return None

    def apply_signature(
        self,
        message: Dict[str, Any],
        signature_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Apply a signature to a message.

        Args:
            message: Email message
            signature_id: Specific signature ID, or None for default

        Returns:
            Dict: Message with signature
        """
        if signature_id:
            signature = self.signatures.get(signature_id)
        else:
            signature = self.get_default_signature()

        if not signature:
            return message

        # Add signature to body
        if message.get('body_html'):
            message['body_html'] += f"<br><br>{signature.html_content}"

        if message.get('body_text'):
            message['body_text'] += f"\n\n{signature.text_content}"

        return message

    def format_html(self, text: str) -> str:
        """
        Apply basic HTML formatting to plain text.

        Args:
            text: Plain text

        Returns:
            str: HTML formatted text
        """
        # Convert newlines to <br>
        html = text.replace('\n', '<br>')

        # Wrap in basic HTML structure
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; font-size: 14px; color: #333;">
                {html}
            </body>
        </html>
        """

        return html

    def _text_to_html(self, text: str) -> str:
        """Convert plain text to HTML."""
        return self.format_html(text)

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text (simple implementation)."""
        import re

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)

        # Convert common HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&amp;', '&')
        text = text.replace('<br>', '\n')
        text = text.replace('<br/>', '\n')
        text = text.replace('<br />', '\n')

        # Clean up whitespace
        text = '\n'.join(line.strip() for line in text.split('\n'))

        return text

    def create_draft(
        self,
        from_address: str,
        to_addresses: List[str],
        subject: str = "",
        body: str = "",
        is_html: bool = True
    ) -> Dict[str, Any]:
        """
        Create a draft email.

        Args:
            from_address: Sender
            to_addresses: Recipients
            subject: Subject
            body: Body content
            is_html: HTML or plain text

        Returns:
            Dict: Draft message
        """
        message = self.create_message(
            from_address=from_address,
            to_addresses=to_addresses,
            subject=subject,
            body=body,
            is_html=is_html
        )

        message['is_draft'] = True

        return message

    def validate_email_address(self, email: str) -> bool:
        """
        Validate email address format.

        Args:
            email: Email address

        Returns:
            bool: True if valid
        """
        import re

        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def validate_message(self, message: Dict[str, Any]) -> List[str]:
        """
        Validate a message before sending.

        Args:
            message: Email message

        Returns:
            List[str]: List of validation errors (empty if valid)
        """
        errors = []

        # Check required fields
        if not message.get('from_address'):
            errors.append("Missing from_address")

        if not message.get('to_addresses'):
            errors.append("Missing to_addresses")
        elif not isinstance(message['to_addresses'], list) or len(message['to_addresses']) == 0:
            errors.append("to_addresses must be a non-empty list")

        if not message.get('subject'):
            errors.append("Missing subject")

        if not message.get('body_html') and not message.get('body_text'):
            errors.append("Missing body content")

        # Validate email addresses
        if message.get('from_address') and not self.validate_email_address(message['from_address']):
            errors.append(f"Invalid from_address: {message['from_address']}")

        for to_addr in message.get('to_addresses', []):
            if not self.validate_email_address(to_addr):
                errors.append(f"Invalid to_address: {to_addr}")

        for cc_addr in message.get('cc_addresses', []):
            if not self.validate_email_address(cc_addr):
                errors.append(f"Invalid cc_address: {cc_addr}")

        return errors


# Default templates
DEFAULT_TEMPLATES = [
    EmailTemplate(
        name="Welcome Email",
        subject="Welcome to {{company_name}}!",
        body_html="""
        <p>Hi {{name}},</p>
        <p>Welcome to {{company_name}}! We're excited to have you on board.</p>
        <p>Best regards,<br>The Team</p>
        """,
        body_text="Hi {{name}},\n\nWelcome to {{company_name}}! We're excited to have you on board.\n\nBest regards,\nThe Team",
        variables=["name", "company_name"],
        category="business"
    ),
    EmailTemplate(
        name="Meeting Request",
        subject="Meeting Request: {{topic}}",
        body_html="""
        <p>Hi {{name}},</p>
        <p>I'd like to schedule a meeting to discuss {{topic}}.</p>
        <p>Are you available on {{date}} at {{time}}?</p>
        <p>Best regards</p>
        """,
        body_text="Hi {{name}},\n\nI'd like to schedule a meeting to discuss {{topic}}.\n\nAre you available on {{date}} at {{time}}?\n\nBest regards",
        variables=["name", "topic", "date", "time"],
        category="business"
    )
]
