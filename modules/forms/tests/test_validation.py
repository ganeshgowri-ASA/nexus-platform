"""
Tests for validation module
"""

import pytest
from modules.forms.validation import (
    ValidationRule, ValidationType, Validator,
    ValidationRuleBuilder, CommonValidations
)


class TestValidationRule:
    """Test ValidationRule class"""

    def test_required_validation(self):
        rule = ValidationRule(ValidationType.REQUIRED)
        is_valid, error = rule.validate("")
        assert is_valid == False
        assert "required" in error.lower()

        is_valid, error = rule.validate("value")
        assert is_valid == True

    def test_email_validation(self):
        rule = ValidationRule(ValidationType.EMAIL)
        is_valid, error = rule.validate("test@example.com")
        assert is_valid == True

        is_valid, error = rule.validate("invalid")
        assert is_valid == False

    def test_min_length_validation(self):
        rule = ValidationRule(ValidationType.MIN_LENGTH, value=5)
        is_valid, error = rule.validate("abc")
        assert is_valid == False

        is_valid, error = rule.validate("abcdef")
        assert is_valid == True

    def test_max_length_validation(self):
        rule = ValidationRule(ValidationType.MAX_LENGTH, value=10)
        is_valid, error = rule.validate("short")
        assert is_valid == True

        is_valid, error = rule.validate("this is too long")
        assert is_valid == False

    def test_numeric_validation(self):
        rule = ValidationRule(ValidationType.NUMERIC)
        is_valid, error = rule.validate("123")
        assert is_valid == True

        is_valid, error = rule.validate("abc")
        assert is_valid == False

    def test_pattern_validation(self):
        rule = ValidationRule(ValidationType.PATTERN, value=r'^\d{3}-\d{3}-\d{4}$')
        is_valid, error = rule.validate("123-456-7890")
        assert is_valid == True

        is_valid, error = rule.validate("invalid")
        assert is_valid == False

    def test_custom_validation(self):
        def custom_validator(value):
            return len(value) % 2 == 0

        rule = ValidationRule(
            ValidationType.CUSTOM,
            custom_validator=custom_validator
        )

        is_valid, error = rule.validate("even")
        assert is_valid == True

        is_valid, error = rule.validate("odd")
        assert is_valid == False


class TestValidator:
    """Test Validator class"""

    def test_add_rule(self):
        validator = Validator()
        rule = ValidationRuleBuilder.required()
        validator.add_rule("field1", rule)
        assert "field1" in validator.rules

    def test_validate_field(self):
        validator = Validator()
        validator.add_rule("email", ValidationRuleBuilder.required())
        validator.add_rule("email", ValidationRuleBuilder.email())

        is_valid, errors = validator.validate_field("email", "")
        assert is_valid == False
        assert len(errors) > 0

        is_valid, errors = validator.validate_field("email", "test@example.com")
        assert is_valid == True

    def test_validate_form(self):
        validator = Validator()
        validator.add_rule("name", ValidationRuleBuilder.required())
        validator.add_rule("email", ValidationRuleBuilder.email())

        form_data = {
            "name": "",
            "email": "invalid"
        }

        is_valid, errors = validator.validate_form(form_data)
        assert is_valid == False
        assert "name" in errors
        assert "email" in errors

    def test_validate_form_success(self):
        validator = Validator()
        validator.add_rule("name", ValidationRuleBuilder.required())
        validator.add_rule("email", ValidationRuleBuilder.email())

        form_data = {
            "name": "John Doe",
            "email": "john@example.com"
        }

        is_valid, errors = validator.validate_form(form_data)
        assert is_valid == True
        assert len(errors) == 0


class TestValidationRuleBuilder:
    """Test ValidationRuleBuilder class"""

    def test_build_required(self):
        rule = ValidationRuleBuilder.required("Field is required")
        assert rule.rule_type == ValidationType.REQUIRED
        assert rule.error_message == "Field is required"

    def test_build_email(self):
        rule = ValidationRuleBuilder.email()
        assert rule.rule_type == ValidationType.EMAIL

    def test_build_min_length(self):
        rule = ValidationRuleBuilder.min_length(5)
        assert rule.rule_type == ValidationType.MIN_LENGTH
        assert rule.value == 5

    def test_build_pattern(self):
        rule = ValidationRuleBuilder.pattern(r'^\d+$')
        assert rule.rule_type == ValidationType.PATTERN


class TestCommonValidations:
    """Test CommonValidations class"""

    def test_email_field_validation(self):
        rules = CommonValidations.email_field()
        assert len(rules) == 2
        assert rules[0].rule_type == ValidationType.REQUIRED
        assert rules[1].rule_type == ValidationType.EMAIL

    def test_password_field_validation(self):
        rules = CommonValidations.password_field(min_length=8)
        assert len(rules) >= 2
        assert any(r.rule_type == ValidationType.MIN_LENGTH for r in rules)

    def test_phone_field_validation(self):
        rules = CommonValidations.phone_field(required=True)
        assert len(rules) == 2
        assert rules[0].rule_type == ValidationType.REQUIRED
        assert rules[1].rule_type == ValidationType.PHONE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
