"""
Form Builder Module

Core form builder functionality with drag-drop support, form management, and distribution.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid
import json
import hashlib
from .field_types import Field, FieldType
from .logic import ConditionalLogic, BranchingLogic
from .validation import Validator


@dataclass
class FormSettings:
    """Form-level settings and configuration"""
    # Basic settings
    title: str = "Untitled Form"
    description: str = ""

    # Appearance
    theme: str = "default"  # default, minimal, modern, classic
    primary_color: str = "#4F46E5"
    background_color: str = "#FFFFFF"
    custom_css: str = ""
    logo_url: Optional[str] = None

    # Behavior
    allow_multiple_submissions: bool = True
    show_progress_bar: bool = True
    randomize_fields: bool = False
    auto_save: bool = True

    # Multi-page settings
    is_multi_page: bool = False
    page_titles: Dict[int, str] = field(default_factory=dict)

    # Submission settings
    success_message: str = "Thank you for your submission!"
    redirect_url: Optional[str] = None
    collect_email: bool = False
    require_login: bool = False

    # Notifications
    send_confirmation_email: bool = False
    notification_emails: List[str] = field(default_factory=list)

    # Advanced
    enable_analytics: bool = True
    enable_captcha: bool = False
    submission_limit: Optional[int] = None
    close_date: Optional[datetime] = None

    # Distribution
    share_link: Optional[str] = None
    embed_code: Optional[str] = None
    qr_code_url: Optional[str] = None


@dataclass
class Form:
    """Represents a complete form"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    fields: List[Field] = field(default_factory=list)
    settings: FormSettings = field(default_factory=FormSettings)
    logic: ConditionalLogic = field(default_factory=ConditionalLogic)
    branching: BranchingLogic = field(default_factory=BranchingLogic)
    validator: Validator = field(default_factory=Validator)

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None
    status: str = "draft"  # draft, published, closed

    def to_dict(self) -> Dict[str, Any]:
        """Convert form to dictionary"""
        return {
            "id": self.id,
            "fields": [f.to_dict() for f in self.fields],
            "settings": vars(self.settings),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Form":
        """Create form from dictionary"""
        fields = [Field.from_dict(f) for f in data.get("fields", [])]
        settings = FormSettings(**data.get("settings", {}))

        form = cls(
            id=data.get("id", str(uuid.uuid4())),
            fields=fields,
            settings=settings,
            created_at=datetime.fromisoformat(data["created_at"])
                if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"])
                if "updated_at" in data else datetime.now(),
            created_by=data.get("created_by"),
            status=data.get("status", "draft"),
        )
        return form

    def add_field(self, field: Field, position: Optional[int] = None) -> None:
        """Add a field to the form"""
        if position is None:
            position = len(self.fields)

        field.position = position
        self.fields.insert(position, field)
        self._reorder_fields()
        self.updated_at = datetime.now()

    def remove_field(self, field_id: str) -> bool:
        """Remove a field from the form"""
        for i, field in enumerate(self.fields):
            if field.id == field_id:
                self.fields.pop(i)
                self._reorder_fields()
                self.updated_at = datetime.now()
                return True
        return False

    def move_field(self, field_id: str, new_position: int) -> bool:
        """Move a field to a new position"""
        field = self.get_field(field_id)
        if not field:
            return False

        self.fields.remove(field)
        self.fields.insert(new_position, field)
        self._reorder_fields()
        self.updated_at = datetime.now()
        return True

    def get_field(self, field_id: str) -> Optional[Field]:
        """Get a field by ID"""
        for field in self.fields:
            if field.id == field_id:
                return field
        return None

    def duplicate_field(self, field_id: str) -> Optional[Field]:
        """Duplicate a field"""
        field = self.get_field(field_id)
        if not field:
            return None

        new_field = field.clone()
        self.add_field(new_field, field.position + 1)
        return new_field

    def _reorder_fields(self) -> None:
        """Reorder field positions"""
        for i, field in enumerate(self.fields):
            field.position = i

    def get_fields_by_page(self, page: int) -> List[Field]:
        """Get all fields for a specific page"""
        return [f for f in self.fields if f.page == page]

    def get_page_count(self) -> int:
        """Get the number of pages in the form"""
        if not self.settings.is_multi_page:
            return 1
        return max([f.page for f in self.fields], default=0) + 1

    def validate_submission(self, submission_data: Dict[str, Any]) -> tuple[bool, Dict[str, List[str]]]:
        """
        Validate a form submission

        Returns:
            Tuple of (is_valid, field_errors)
        """
        return self.validator.validate_form(submission_data)

    def publish(self) -> str:
        """
        Publish the form and generate share link

        Returns:
            Share link
        """
        if self.status != "published":
            self.status = "published"
            self.updated_at = datetime.now()

        # Generate share link if not exists
        if not self.settings.share_link:
            self.settings.share_link = self._generate_share_link()

        # Generate embed code
        if not self.settings.embed_code:
            self.settings.embed_code = self._generate_embed_code()

        return self.settings.share_link

    def unpublish(self) -> None:
        """Unpublish the form"""
        self.status = "draft"
        self.updated_at = datetime.now()

    def close(self) -> None:
        """Close the form to new submissions"""
        self.status = "closed"
        self.updated_at = datetime.now()

    def _generate_share_link(self) -> str:
        """Generate a shareable link for the form"""
        base_url = "https://nexus-forms.app/f/"
        short_id = hashlib.md5(self.id.encode()).hexdigest()[:8]
        return f"{base_url}{short_id}"

    def _generate_embed_code(self) -> str:
        """Generate embed code for the form"""
        share_link = self.settings.share_link or self._generate_share_link()
        return f'''<iframe src="{share_link}" width="100%" height="600" frameborder="0">
</iframe>'''

    def generate_qr_code(self) -> str:
        """Generate QR code URL for the form"""
        share_link = self.settings.share_link or self._generate_share_link()
        # In production, this would use a QR code generation service
        qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={share_link}"
        self.settings.qr_code_url = qr_api_url
        return qr_api_url


class FormBuilder:
    """Builder class for creating and managing forms"""

    def __init__(self):
        self.forms: Dict[str, Form] = {}

    def create_form(self, title: str = "Untitled Form") -> Form:
        """Create a new form"""
        form = Form()
        form.settings.title = title
        self.forms[form.id] = form
        return form

    def delete_form(self, form_id: str) -> bool:
        """Delete a form"""
        if form_id in self.forms:
            del self.forms[form_id]
            return True
        return False

    def get_form(self, form_id: str) -> Optional[Form]:
        """Get a form by ID"""
        return self.forms.get(form_id)

    def duplicate_form(self, form_id: str) -> Optional[Form]:
        """Duplicate a form"""
        original = self.get_form(form_id)
        if not original:
            return None

        # Create a new form with copied data
        new_form = Form.from_dict(original.to_dict())
        new_form.id = str(uuid.uuid4())
        new_form.settings.title = f"{original.settings.title} (Copy)"
        new_form.status = "draft"
        new_form.created_at = datetime.now()
        new_form.updated_at = datetime.now()

        # Reset share links
        new_form.settings.share_link = None
        new_form.settings.embed_code = None
        new_form.settings.qr_code_url = None

        self.forms[new_form.id] = new_form
        return new_form

    def list_forms(self, status: Optional[str] = None) -> List[Form]:
        """List all forms, optionally filtered by status"""
        if status:
            return [f for f in self.forms.values() if f.status == status]
        return list(self.forms.values())

    def save_form(self, form: Form, filepath: str) -> None:
        """Save form to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(form.to_dict(), f, indent=2, default=str)

    def load_form(self, filepath: str) -> Form:
        """Load form from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        form = Form.from_dict(data)
        self.forms[form.id] = form
        return form

    def export_form_schema(self, form_id: str) -> Dict[str, Any]:
        """Export form schema for API integration"""
        form = self.get_form(form_id)
        if not form:
            return {}

        return {
            "form_id": form.id,
            "title": form.settings.title,
            "description": form.settings.description,
            "fields": [
                {
                    "id": f.id,
                    "type": f.field_type.value,
                    "label": f.label,
                    "required": f.config.required,
                    "options": f.config.options,
                }
                for f in form.fields
            ],
            "settings": {
                "multi_page": form.settings.is_multi_page,
                "allow_multiple_submissions": form.settings.allow_multiple_submissions,
            }
        }


class FormRenderer:
    """Renders forms for display"""

    @staticmethod
    def render_field_html(field: Field) -> str:
        """Render a field as HTML"""
        html_parts = [f'<div class="form-field" data-field-id="{field.id}">']

        # Label
        required_marker = '<span class="required">*</span>' if field.config.required else ''
        html_parts.append(f'<label>{field.label}{required_marker}</label>')

        # Description
        if field.description:
            html_parts.append(f'<p class="field-description">{field.description}</p>')

        # Field input based on type
        if field.field_type == FieldType.SHORT_TEXT:
            html_parts.append(
                f'<input type="text" name="{field.id}" '
                f'placeholder="{field.config.placeholder or ""}" />'
            )

        elif field.field_type == FieldType.LONG_TEXT:
            html_parts.append(
                f'<textarea name="{field.id}" '
                f'placeholder="{field.config.placeholder or ""}"></textarea>'
            )

        elif field.field_type == FieldType.EMAIL:
            html_parts.append(
                f'<input type="email" name="{field.id}" '
                f'placeholder="{field.config.placeholder or ""}" />'
            )

        elif field.field_type == FieldType.DROPDOWN:
            html_parts.append(f'<select name="{field.id}">')
            html_parts.append('<option value="">Select an option</option>')
            for option in field.config.options or []:
                html_parts.append(f'<option value="{option}">{option}</option>')
            html_parts.append('</select>')

        elif field.field_type == FieldType.RADIO:
            for option in field.config.options or []:
                html_parts.append(
                    f'<label><input type="radio" name="{field.id}" '
                    f'value="{option}" /> {option}</label>'
                )

        elif field.field_type == FieldType.CHECKBOX:
            for option in field.config.options or []:
                html_parts.append(
                    f'<label><input type="checkbox" name="{field.id}" '
                    f'value="{option}" /> {option}</label>'
                )

        html_parts.append('</div>')
        return '\n'.join(html_parts)

    @staticmethod
    def render_form_html(form: Form) -> str:
        """Render complete form as HTML"""
        html_parts = [
            f'<form id="form-{form.id}" class="nexus-form">',
            f'<h1>{form.settings.title}</h1>',
        ]

        if form.settings.description:
            html_parts.append(f'<p class="form-description">{form.settings.description}</p>')

        for field in form.fields:
            html_parts.append(FormRenderer.render_field_html(field))

        html_parts.append('<button type="submit">Submit</button>')
        html_parts.append('</form>')

        return '\n'.join(html_parts)


class FormTheme:
    """Predefined form themes"""

    THEMES = {
        "default": {
            "primary_color": "#4F46E5",
            "background_color": "#FFFFFF",
            "text_color": "#1F2937",
            "border_color": "#D1D5DB",
            "font_family": "'Inter', sans-serif",
        },
        "minimal": {
            "primary_color": "#000000",
            "background_color": "#FFFFFF",
            "text_color": "#000000",
            "border_color": "#E5E5E5",
            "font_family": "'Helvetica Neue', sans-serif",
        },
        "modern": {
            "primary_color": "#8B5CF6",
            "background_color": "#F9FAFB",
            "text_color": "#111827",
            "border_color": "#E5E7EB",
            "font_family": "'Poppins', sans-serif",
        },
        "classic": {
            "primary_color": "#2563EB",
            "background_color": "#FFFFFF",
            "text_color": "#374151",
            "border_color": "#9CA3AF",
            "font_family": "'Georgia', serif",
        },
    }

    @classmethod
    def apply_theme(cls, form: Form, theme_name: str) -> None:
        """Apply a theme to a form"""
        if theme_name in cls.THEMES:
            theme = cls.THEMES[theme_name]
            form.settings.theme = theme_name
            form.settings.primary_color = theme["primary_color"]
            form.settings.background_color = theme["background_color"]

    @classmethod
    def get_theme_css(cls, theme_name: str) -> str:
        """Get CSS for a theme"""
        if theme_name not in cls.THEMES:
            theme_name = "default"

        theme = cls.THEMES[theme_name]
        return f"""
        .nexus-form {{
            font-family: {theme['font_family']};
            color: {theme['text_color']};
            background-color: {theme['background_color']};
        }}
        .nexus-form button[type="submit"] {{
            background-color: {theme['primary_color']};
        }}
        .nexus-form input, .nexus-form textarea, .nexus-form select {{
            border: 1px solid {theme['border_color']};
        }}
        """
