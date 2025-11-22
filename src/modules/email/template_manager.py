"""Email template manager using Jinja2."""

from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import logging

from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound
from sqlalchemy.orm import Session

from src.modules.email.models import EmailTemplate

logger = logging.getLogger(__name__)


class TemplateManager:
    """Manager for email templates using Jinja2."""

    def __init__(
        self,
        template_dir: Optional[str] = None,
        db: Optional[Session] = None
    ):
        """Initialize template manager.

        Args:
            template_dir: Directory containing template files
            db: Database session for template storage
        """
        self.template_dir = Path(template_dir or "./src/modules/email/templates")
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.db = db

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Add custom filters
        self._add_custom_filters()

    def _add_custom_filters(self):
        """Add custom Jinja2 filters."""

        def format_date(value, format_string='%Y-%m-%d'):
            """Format datetime object."""
            if isinstance(value, datetime):
                return value.strftime(format_string)
            return value

        def format_currency(value, currency='$'):
            """Format currency."""
            try:
                return f"{currency}{float(value):,.2f}"
            except (ValueError, TypeError):
                return value

        def truncate_text(value, length=100, suffix='...'):
            """Truncate text to specified length."""
            if len(str(value)) > length:
                return str(value)[:length] + suffix
            return value

        self.env.filters['format_date'] = format_date
        self.env.filters['format_currency'] = format_currency
        self.env.filters['truncate_text'] = truncate_text

    def render_template(
        self,
        template_name: str,
        context: Dict[str, Any],
        from_string: bool = False
    ) -> str:
        """Render a template with context.

        Args:
            template_name: Template name or template string
            context: Template context variables
            from_string: Whether template_name is a template string

        Returns:
            Rendered template string

        Raises:
            TemplateNotFound: If template file not found
        """
        try:
            if from_string:
                template = self.env.from_string(template_name)
            else:
                template = self.env.get_template(template_name)

            rendered = template.render(**context)
            logger.debug(f"Rendered template: {template_name}")
            return rendered

        except TemplateNotFound:
            logger.error(f"Template not found: {template_name}")
            raise
        except Exception as e:
            logger.error(f"Failed to render template: {e}")
            raise

    def render_email(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> Dict[str, str]:
        """Render email template (both HTML and text versions).

        Args:
            template_name: Template name (without extension)
            context: Template context variables

        Returns:
            Dict with 'html' and 'text' rendered content
        """
        result = {}

        # Try to render HTML version
        try:
            html_template = f"{template_name}.html"
            result['html'] = self.render_template(html_template, context)
        except TemplateNotFound:
            logger.warning(f"HTML template not found: {html_template}")
            result['html'] = None

        # Try to render text version
        try:
            text_template = f"{template_name}.txt"
            result['text'] = self.render_template(text_template, context)
        except TemplateNotFound:
            logger.warning(f"Text template not found: {text_template}")
            result['text'] = None

        if not result['html'] and not result['text']:
            raise ValueError(f"No templates found for: {template_name}")

        return result

    def create_template(
        self,
        name: str,
        subject: str,
        body_html: Optional[str] = None,
        body_text: Optional[str] = None,
        description: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None
    ) -> EmailTemplate:
        """Create a new email template in database.

        Args:
            name: Template name
            subject: Email subject template
            body_html: HTML body template
            body_text: Text body template
            description: Template description
            variables: Template variable schema

        Returns:
            Created EmailTemplate object

        Raises:
            ValueError: If database session not provided
        """
        if not self.db:
            raise ValueError("Database session required to create template")

        # Check if template already exists
        existing = self.db.query(EmailTemplate).filter_by(name=name).first()
        if existing:
            raise ValueError(f"Template already exists: {name}")

        # Create template
        template = EmailTemplate(
            name=name,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            description=description,
            variables=variables or {}
        )

        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)

        logger.info(f"Created template: {name}")
        return template

    def get_template(self, name: str) -> Optional[EmailTemplate]:
        """Get template from database by name.

        Args:
            name: Template name

        Returns:
            EmailTemplate object or None
        """
        if not self.db:
            raise ValueError("Database session required to get template")

        return self.db.query(EmailTemplate).filter_by(name=name).first()

    def update_template(
        self,
        name: str,
        subject: Optional[str] = None,
        body_html: Optional[str] = None,
        body_text: Optional[str] = None,
        description: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None
    ) -> Optional[EmailTemplate]:
        """Update existing template.

        Args:
            name: Template name
            subject: Email subject template
            body_html: HTML body template
            body_text: Text body template
            description: Template description
            variables: Template variable schema
            is_active: Active status

        Returns:
            Updated EmailTemplate object or None
        """
        if not self.db:
            raise ValueError("Database session required to update template")

        template = self.get_template(name)
        if not template:
            logger.error(f"Template not found: {name}")
            return None

        # Update fields
        if subject is not None:
            template.subject = subject
        if body_html is not None:
            template.body_html = body_html
        if body_text is not None:
            template.body_text = body_text
        if description is not None:
            template.description = description
        if variables is not None:
            template.variables = variables
        if is_active is not None:
            template.is_active = is_active

        template.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(template)

        logger.info(f"Updated template: {name}")
        return template

    def delete_template(self, name: str) -> bool:
        """Delete template from database.

        Args:
            name: Template name

        Returns:
            True if deleted successfully
        """
        if not self.db:
            raise ValueError("Database session required to delete template")

        template = self.get_template(name)
        if not template:
            logger.error(f"Template not found: {name}")
            return False

        self.db.delete(template)
        self.db.commit()

        logger.info(f"Deleted template: {name}")
        return True

    def list_templates(self, active_only: bool = True) -> List[EmailTemplate]:
        """List all templates.

        Args:
            active_only: Only return active templates

        Returns:
            List of EmailTemplate objects
        """
        if not self.db:
            raise ValueError("Database session required to list templates")

        query = self.db.query(EmailTemplate)

        if active_only:
            query = query.filter_by(is_active=True)

        return query.order_by(EmailTemplate.name).all()

    def render_from_db(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> Dict[str, str]:
        """Render template from database.

        Args:
            template_name: Template name
            context: Template context variables

        Returns:
            Dict with 'subject', 'html', and 'text' rendered content
        """
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template not found: {template_name}")

        if not template.is_active:
            raise ValueError(f"Template is inactive: {template_name}")

        result = {}

        # Render subject
        if template.subject:
            result['subject'] = self.render_template(
                template.subject,
                context,
                from_string=True
            )

        # Render HTML body
        if template.body_html:
            result['html'] = self.render_template(
                template.body_html,
                context,
                from_string=True
            )

        # Render text body
        if template.body_text:
            result['text'] = self.render_template(
                template.body_text,
                context,
                from_string=True
            )

        logger.info(f"Rendered template from DB: {template_name}")
        return result

    def save_template_file(
        self,
        filename: str,
        content: str
    ):
        """Save template to file.

        Args:
            filename: Template filename
            content: Template content
        """
        file_path = self.template_dir / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Saved template file: {filename}")

    def load_default_templates(self):
        """Load default email templates."""
        default_templates = [
            {
                'name': 'welcome',
                'subject': 'Welcome to {{ app_name }}!',
                'description': 'Welcome email for new users',
                'body_html': '''
                    <h1>Welcome, {{ user_name }}!</h1>
                    <p>Thank you for joining {{ app_name }}.</p>
                    <p>We're excited to have you on board!</p>
                    <p>Best regards,<br>The {{ app_name }} Team</p>
                ''',
                'body_text': '''
                    Welcome, {{ user_name }}!

                    Thank you for joining {{ app_name }}.
                    We're excited to have you on board!

                    Best regards,
                    The {{ app_name }} Team
                ''',
                'variables': {
                    'user_name': 'string',
                    'app_name': 'string'
                }
            },
            {
                'name': 'notification',
                'subject': 'New notification from {{ app_name }}',
                'description': 'General notification template',
                'body_html': '''
                    <h2>{{ title }}</h2>
                    <p>{{ message }}</p>
                    <p>Received at: {{ timestamp | format_date('%Y-%m-%d %H:%M') }}</p>
                ''',
                'body_text': '''
                    {{ title }}

                    {{ message }}

                    Received at: {{ timestamp | format_date('%Y-%m-%d %H:%M') }}
                ''',
                'variables': {
                    'title': 'string',
                    'message': 'string',
                    'timestamp': 'datetime',
                    'app_name': 'string'
                }
            },
            {
                'name': 'reset_password',
                'subject': 'Password Reset Request',
                'description': 'Password reset email',
                'body_html': '''
                    <h2>Password Reset Request</h2>
                    <p>Hi {{ user_name }},</p>
                    <p>We received a request to reset your password.</p>
                    <p>Click the link below to reset your password:</p>
                    <p><a href="{{ reset_link }}">Reset Password</a></p>
                    <p>This link will expire in {{ expiry_hours }} hours.</p>
                    <p>If you didn't request this, please ignore this email.</p>
                ''',
                'body_text': '''
                    Password Reset Request

                    Hi {{ user_name }},

                    We received a request to reset your password.
                    Click the link below to reset your password:

                    {{ reset_link }}

                    This link will expire in {{ expiry_hours }} hours.

                    If you didn't request this, please ignore this email.
                ''',
                'variables': {
                    'user_name': 'string',
                    'reset_link': 'string',
                    'expiry_hours': 'integer'
                }
            }
        ]

        if not self.db:
            logger.warning("Database session not provided, skipping default templates")
            return

        for template_data in default_templates:
            try:
                # Check if already exists
                existing = self.get_template(template_data['name'])
                if not existing:
                    self.create_template(**template_data)
                    logger.info(f"Created default template: {template_data['name']}")
            except Exception as e:
                logger.error(f"Failed to create default template: {e}")
