"""
Tests for field_types module
"""

import pytest
from datetime import datetime
from modules.forms.field_types import (
    Field, FieldType, FieldConfig, FieldFactory
)


class TestFieldConfig:
    """Test FieldConfig class"""

    def test_field_config_defaults(self):
        config = FieldConfig()
        assert config.required == False
        assert config.placeholder is None
        assert config.options is None

    def test_field_config_with_values(self):
        config = FieldConfig(
            required=True,
            placeholder="Enter text",
            min_length=5,
            max_length=100
        )
        assert config.required == True
        assert config.placeholder == "Enter text"
        assert config.min_length == 5
        assert config.max_length == 100


class TestField:
    """Test Field class"""

    def test_field_creation(self):
        field = Field(
            field_type=FieldType.SHORT_TEXT,
            label="Name"
        )
        assert field.field_type == FieldType.SHORT_TEXT
        assert field.label == "Name"
        assert field.id is not None

    def test_field_to_dict(self):
        field = Field(
            field_type=FieldType.EMAIL,
            label="Email Address",
            config=FieldConfig(required=True)
        )
        data = field.to_dict()
        assert data["field_type"] == "email"
        assert data["label"] == "Email Address"
        assert data["config"]["required"] == True

    def test_field_from_dict(self):
        data = {
            "id": "test-123",
            "field_type": "short_text",
            "label": "Test Field",
            "config": {"required": True},
            "position": 0,
            "page": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        field = Field.from_dict(data)
        assert field.id == "test-123"
        assert field.field_type == FieldType.SHORT_TEXT
        assert field.label == "Test Field"

    def test_validate_required_field(self):
        field = Field(
            field_type=FieldType.SHORT_TEXT,
            label="Name",
            config=FieldConfig(required=True)
        )
        is_valid, error = field.validate_value("")
        assert is_valid == False
        assert error is not None

    def test_validate_email(self):
        field = Field(
            field_type=FieldType.EMAIL,
            label="Email"
        )
        is_valid, error = field.validate_value("test@example.com")
        assert is_valid == True
        assert error is None

        is_valid, error = field.validate_value("invalid-email")
        assert is_valid == False

    def test_validate_number_range(self):
        field = Field(
            field_type=FieldType.NUMBER,
            label="Age",
            config=FieldConfig(min_value=0, max_value=120)
        )
        is_valid, error = field.validate_value(25)
        assert is_valid == True

        is_valid, error = field.validate_value(150)
        assert is_valid == False

    def test_validate_min_max_length(self):
        field = Field(
            field_type=FieldType.SHORT_TEXT,
            label="Username",
            config=FieldConfig(min_length=3, max_length=20)
        )
        is_valid, error = field.validate_value("ab")
        assert is_valid == False

        is_valid, error = field.validate_value("validuser")
        assert is_valid == True

    def test_field_clone(self):
        original = Field(
            field_type=FieldType.SHORT_TEXT,
            label="Original"
        )
        cloned = original.clone()
        assert cloned.id != original.id
        assert cloned.label == "Original (Copy)"
        assert cloned.field_type == original.field_type


class TestFieldFactory:
    """Test FieldFactory class"""

    def test_create_short_text(self):
        field = FieldFactory.create_short_text("Name", required=True)
        assert field.field_type == FieldType.SHORT_TEXT
        assert field.label == "Name"
        assert field.config.required == True

    def test_create_email(self):
        field = FieldFactory.create_email()
        assert field.field_type == FieldType.EMAIL
        assert field.label == "Email"

    def test_create_dropdown(self):
        options = ["Option 1", "Option 2", "Option 3"]
        field = FieldFactory.create_dropdown("Select", options)
        assert field.field_type == FieldType.DROPDOWN
        assert field.config.options == options

    def test_create_rating(self):
        field = FieldFactory.create_rating("Rate us", max_rating=5)
        assert field.field_type == FieldType.RATING
        assert field.config.max_rating == 5

    def test_create_nps(self):
        field = FieldFactory.create_nps()
        assert field.field_type == FieldType.NPS
        assert field.config.min_rating == 0
        assert field.config.max_rating == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
