"""
Notification template engine
Renders notification templates with variable substitution
"""
from typing import Dict, Any, Optional
from jinja2 import Template, Environment, select_autoescape
import re


class TemplateEngine:
    """
    Template engine for notification templates
    Supports Jinja2 templating with safe variable substitution
    """

    def __init__(self):
        """Initialize template engine"""
        self.env = Environment(
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(
        self,
        template_string: str,
        variables: Dict[str, Any],
        is_html: bool = False
    ) -> str:
        """
        Render a template with variables

        Args:
            template_string: Template string with Jinja2 syntax
            variables: Dictionary of variables to substitute
            is_html: Whether this is an HTML template (affects escaping)

        Returns:
            Rendered string

        Example:
            template = "Hello {{ user_name }}, your order #{{ order_id }} is ready!"
            variables = {"user_name": "John", "order_id": "12345"}
            result = render(template, variables)
            # Result: "Hello John, your order #12345 is ready!"
        """
        try:
            template = self.env.from_string(template_string)
            return template.render(**variables)
        except Exception as e:
            raise TemplateRenderError(f"Failed to render template: {str(e)}")

    def render_subject(self, subject: str, variables: Dict[str, Any]) -> str:
        """
        Render email subject with variables

        Args:
            subject: Subject template string
            variables: Variables to substitute

        Returns:
            Rendered subject
        """
        return self.render(subject, variables, is_html=False)

    def render_body(self, body: str, variables: Dict[str, Any]) -> str:
        """
        Render notification body with variables

        Args:
            body: Body template string
            variables: Variables to substitute

        Returns:
            Rendered body
        """
        return self.render(body, variables, is_html=False)

    def render_html_body(self, html_body: str, variables: Dict[str, Any]) -> str:
        """
        Render HTML email body with variables

        Args:
            html_body: HTML body template string
            variables: Variables to substitute

        Returns:
            Rendered HTML body
        """
        return self.render(html_body, variables, is_html=True)

    def validate_template(self, template_string: str, required_variables: Optional[list] = None) -> tuple[bool, Optional[str]]:
        """
        Validate a template

        Args:
            template_string: Template to validate
            required_variables: List of required variable names

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Try to parse the template
            template = self.env.from_string(template_string)

            # Get all variables used in the template
            ast = self.env.parse(template_string)
            used_variables = set(meta.find_undeclared_variables(ast))

            # Check if all required variables are present
            if required_variables:
                missing = set(required_variables) - used_variables
                if missing:
                    return False, f"Missing required variables: {', '.join(missing)}"

            return True, None

        except Exception as e:
            return False, f"Template syntax error: {str(e)}"

    def extract_variables(self, template_string: str) -> list:
        """
        Extract all variable names from a template

        Args:
            template_string: Template to analyze

        Returns:
            List of variable names used in the template
        """
        try:
            ast = self.env.parse(template_string)
            from jinja2 import meta
            return list(meta.find_undeclared_variables(ast))
        except:
            # Fallback to regex-based extraction
            return re.findall(r'\{\{\s*(\w+)', template_string)

    def render_template_from_db(
        self,
        template: Any,  # NotificationTemplate model
        variables: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Render a complete template from database

        Args:
            template: NotificationTemplate model instance
            variables: Variables to substitute

        Returns:
            Dictionary with rendered content
            {
                "subject": "...",
                "body": "...",
                "html_body": "..."
            }
        """
        result = {}

        if template.subject:
            result["subject"] = self.render_subject(template.subject, variables)

        if template.body:
            result["body"] = self.render_body(template.body, variables)

        if template.html_body:
            result["html_body"] = self.render_html_body(template.html_body, variables)

        return result


class TemplateRenderError(Exception):
    """Exception raised when template rendering fails"""
    pass
