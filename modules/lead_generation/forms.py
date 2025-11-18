"""
Form builder and management for lead generation.

This module provides drag-and-drop form builder functionality with
conditional logic, multi-step forms, and embed code generation.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .lead_types import Form, FormCreate, FormField
from .models import Form as FormModel
from shared.utils import generate_uuid, sanitize_input
from shared.exceptions import ValidationError, NotFoundError, DatabaseError
from config.logging_config import get_logger

logger = get_logger(__name__)


class FormBuilder:
    """Form builder service for creating and managing forms."""

    def __init__(self, db: Session):
        """
        Initialize form builder.

        Args:
            db: Database session.
        """
        self.db = db

    async def create_form(self, form_data: FormCreate) -> Form:
        """
        Create a new form.

        Args:
            form_data: Form creation data.

        Returns:
            Created form object.

        Raises:
            ValidationError: If form data is invalid.
            DatabaseError: If database operation fails.
        """
        try:
            # Validate form fields
            self._validate_form_fields(form_data.fields)

            # Generate embed code
            embed_code = self._generate_embed_code(form_data.name)

            # Create form
            form = FormModel(
                id=generate_uuid(),
                name=form_data.name,
                title=sanitize_input(form_data.title),
                description=sanitize_input(form_data.description) if form_data.description else None,
                fields=[field.model_dump() for field in form_data.fields],
                submit_button_text=form_data.submit_button_text,
                success_message=sanitize_input(form_data.success_message),
                is_active=form_data.is_active,
                embed_code=embed_code,
            )

            self.db.add(form)
            self.db.commit()
            self.db.refresh(form)

            logger.info(f"Form created: {form.name} (ID: {form.id})")

            return Form.model_validate(form)

        except IntegrityError:
            self.db.rollback()
            raise ValidationError(f"Form with name '{form_data.name}' already exists")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating form: {e}")
            raise DatabaseError(f"Failed to create form: {str(e)}")

    async def get_form(self, form_id: str) -> Form:
        """
        Get form by ID.

        Args:
            form_id: Form ID.

        Returns:
            Form object.

        Raises:
            NotFoundError: If form not found.
        """
        form = self.db.query(FormModel).filter(FormModel.id == form_id).first()
        if not form:
            raise NotFoundError(f"Form not found: {form_id}")

        return Form.model_validate(form)

    async def list_forms(
        self,
        skip: int = 0,
        limit: int = 20,
        active_only: bool = False,
    ) -> List[Form]:
        """
        List all forms.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            active_only: Only return active forms.

        Returns:
            List of form objects.
        """
        query = self.db.query(FormModel)

        if active_only:
            query = query.filter(FormModel.is_active == True)

        forms = query.offset(skip).limit(limit).all()

        return [Form.model_validate(form) for form in forms]

    async def update_form(self, form_id: str, updates: dict) -> Form:
        """
        Update form.

        Args:
            form_id: Form ID.
            updates: Update data.

        Returns:
            Updated form object.

        Raises:
            NotFoundError: If form not found.
        """
        form = self.db.query(FormModel).filter(FormModel.id == form_id).first()
        if not form:
            raise NotFoundError(f"Form not found: {form_id}")

        # Update fields
        for key, value in updates.items():
            if hasattr(form, key):
                setattr(form, key, value)

        self.db.commit()
        self.db.refresh(form)

        logger.info(f"Form updated: {form.name} (ID: {form.id})")

        return Form.model_validate(form)

    async def delete_form(self, form_id: str) -> None:
        """
        Delete form.

        Args:
            form_id: Form ID.

        Raises:
            NotFoundError: If form not found.
        """
        form = self.db.query(FormModel).filter(FormModel.id == form_id).first()
        if not form:
            raise NotFoundError(f"Form not found: {form_id}")

        self.db.delete(form)
        self.db.commit()

        logger.info(f"Form deleted: {form.name} (ID: {form.id})")

    async def increment_submissions(self, form_id: str) -> None:
        """
        Increment form submission count.

        Args:
            form_id: Form ID.
        """
        form = self.db.query(FormModel).filter(FormModel.id == form_id).first()
        if form:
            form.submissions_count += 1
            self.db.commit()

    def _validate_form_fields(self, fields: List[FormField]) -> None:
        """
        Validate form fields.

        Args:
            fields: List of form fields.

        Raises:
            ValidationError: If fields are invalid.
        """
        if not fields:
            raise ValidationError("Form must have at least one field")

        # Check for required email field
        email_fields = [f for f in fields if f.type == "email"]
        if not email_fields:
            raise ValidationError("Form must have an email field")

        # Check for duplicate field names
        field_names = [f.name for f in fields]
        if len(field_names) != len(set(field_names)):
            raise ValidationError("Form fields must have unique names")

    def _generate_embed_code(self, form_name: str) -> str:
        """
        Generate embed code for form.

        Args:
            form_name: Form name.

        Returns:
            HTML embed code.
        """
        return f'''<div id="nexus-form-{form_name}"></div>
<script src="https://cdn.nexus.com/forms.js"></script>
<script>
    NexusForms.render('{form_name}', {{
        container: '#nexus-form-{form_name}',
        onSubmit: function(data) {{
            console.log('Form submitted:', data);
        }}
    }});
</script>'''


class MultiStepFormBuilder(FormBuilder):
    """Multi-step form builder with conditional logic."""

    async def create_multi_step_form(
        self,
        name: str,
        title: str,
        steps: List[dict],
        conditional_logic: Optional[dict] = None,
    ) -> Form:
        """
        Create a multi-step form.

        Args:
            name: Form name.
            title: Form title.
            steps: List of form steps with fields.
            conditional_logic: Conditional logic rules.

        Returns:
            Created form object.
        """
        try:
            # Flatten all fields from all steps
            all_fields = []
            for step_idx, step in enumerate(steps):
                for field_data in step.get("fields", []):
                    field = FormField(**field_data)
                    field_dict = field.model_dump()
                    field_dict["step"] = step_idx + 1
                    all_fields.append(field_dict)

            # Create form with multi-step configuration
            form = FormModel(
                id=generate_uuid(),
                name=name,
                title=title,
                fields=all_fields,
                is_active=True,
                embed_code=self._generate_embed_code(name),
            )

            # Store multi-step configuration in custom field
            form.description = f"Multi-step form with {len(steps)} steps"

            self.db.add(form)
            self.db.commit()
            self.db.refresh(form)

            logger.info(f"Multi-step form created: {name} (ID: {form.id})")

            return Form.model_validate(form)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating multi-step form: {e}")
            raise
