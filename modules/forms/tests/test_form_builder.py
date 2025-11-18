"""
Tests for form_builder module
"""

import pytest
from datetime import datetime
from modules.forms.form_builder import FormBuilder, Form, FormSettings
from modules.forms.field_types import Field, FieldType, FieldFactory


class TestFormSettings:
    """Test FormSettings class"""

    def test_default_settings(self):
        settings = FormSettings()
        assert settings.title == "Untitled Form"
        assert settings.allow_multiple_submissions == True
        assert settings.show_progress_bar == True

    def test_custom_settings(self):
        settings = FormSettings(
            title="Custom Form",
            theme="modern",
            primary_color="#FF5733"
        )
        assert settings.title == "Custom Form"
        assert settings.theme == "modern"
        assert settings.primary_color == "#FF5733"


class TestForm:
    """Test Form class"""

    def test_form_creation(self):
        form = Form()
        assert form.id is not None
        assert form.status == "draft"
        assert len(form.fields) == 0

    def test_add_field(self):
        form = Form()
        field = FieldFactory.create_short_text("Name")

        form.add_field(field)
        assert len(form.fields) == 1
        assert form.fields[0].position == 0

    def test_remove_field(self):
        form = Form()
        field = FieldFactory.create_short_text("Name")
        form.add_field(field)

        success = form.remove_field(field.id)
        assert success == True
        assert len(form.fields) == 0

    def test_move_field(self):
        form = Form()
        field1 = FieldFactory.create_short_text("Field 1")
        field2 = FieldFactory.create_short_text("Field 2")
        field3 = FieldFactory.create_short_text("Field 3")

        form.add_field(field1)
        form.add_field(field2)
        form.add_field(field3)

        form.move_field(field1.id, 2)
        assert form.fields[2].id == field1.id

    def test_get_field(self):
        form = Form()
        field = FieldFactory.create_email("Email")
        form.add_field(field)

        retrieved = form.get_field(field.id)
        assert retrieved is not None
        assert retrieved.id == field.id

    def test_duplicate_field(self):
        form = Form()
        field = FieldFactory.create_short_text("Original")
        form.add_field(field)

        duplicated = form.duplicate_field(field.id)
        assert duplicated is not None
        assert duplicated.id != field.id
        assert "Copy" in duplicated.label
        assert len(form.fields) == 2

    def test_publish_form(self):
        form = Form()
        assert form.status == "draft"

        share_link = form.publish()
        assert form.status == "published"
        assert share_link is not None
        assert form.settings.share_link is not None

    def test_unpublish_form(self):
        form = Form()
        form.publish()
        form.unpublish()
        assert form.status == "draft"

    def test_close_form(self):
        form = Form()
        form.close()
        assert form.status == "closed"

    def test_form_to_dict(self):
        form = Form()
        form.settings.title = "Test Form"
        field = FieldFactory.create_short_text("Name")
        form.add_field(field)

        data = form.to_dict()
        assert data["id"] == form.id
        assert len(data["fields"]) == 1
        assert data["status"] == "draft"

    def test_form_from_dict(self):
        data = {
            "id": "test-123",
            "fields": [],
            "settings": {"title": "Test Form"},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "draft"
        }

        form = Form.from_dict(data)
        assert form.id == "test-123"
        assert form.settings.title == "Test Form"

    def test_get_page_count(self):
        form = Form()
        form.settings.is_multi_page = True

        field1 = FieldFactory.create_short_text("Field 1")
        field1.page = 0
        field2 = FieldFactory.create_short_text("Field 2")
        field2.page = 1
        field3 = FieldFactory.create_short_text("Field 3")
        field3.page = 2

        form.add_field(field1)
        form.add_field(field2)
        form.add_field(field3)

        assert form.get_page_count() == 3


class TestFormBuilder:
    """Test FormBuilder class"""

    def test_create_form(self):
        builder = FormBuilder()
        form = builder.create_form("My Form")

        assert form is not None
        assert form.settings.title == "My Form"
        assert form.id in builder.forms

    def test_delete_form(self):
        builder = FormBuilder()
        form = builder.create_form("Test")

        success = builder.delete_form(form.id)
        assert success == True
        assert form.id not in builder.forms

    def test_get_form(self):
        builder = FormBuilder()
        form = builder.create_form("Test")

        retrieved = builder.get_form(form.id)
        assert retrieved is not None
        assert retrieved.id == form.id

    def test_duplicate_form(self):
        builder = FormBuilder()
        original = builder.create_form("Original")
        original.add_field(FieldFactory.create_short_text("Name"))

        duplicated = builder.duplicate_form(original.id)
        assert duplicated is not None
        assert duplicated.id != original.id
        assert "Copy" in duplicated.settings.title
        assert len(duplicated.fields) == len(original.fields)

    def test_list_forms(self):
        builder = FormBuilder()
        form1 = builder.create_form("Form 1")
        form2 = builder.create_form("Form 2")
        form2.publish()

        all_forms = builder.list_forms()
        assert len(all_forms) == 2

        published_forms = builder.list_forms(status="published")
        assert len(published_forms) == 1
        assert published_forms[0].id == form2.id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
