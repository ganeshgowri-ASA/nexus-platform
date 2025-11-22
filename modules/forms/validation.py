"""
Validation Module

Provides comprehensive validation rules and validators for form fields.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Union
from enum import Enum
import re
from datetime import datetime


class ValidationType(Enum):
    """Types of validation rules"""
    REQUIRED = "required"
    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    MIN_VALUE = "min_value"
    MAX_VALUE = "max_value"
    PATTERN = "pattern"
    EMAIL = "email"
    URL = "url"
    PHONE = "phone"
    DATE_RANGE = "date_range"
    FILE_SIZE = "file_size"
    FILE_TYPE = "file_type"
    CUSTOM = "custom"
    UNIQUE = "unique"
    MATCH_FIELD = "match_field"
    NUMERIC = "numeric"
    ALPHA = "alpha"
    ALPHANUMERIC = "alphanumeric"


@dataclass
class ValidationRule:
    """Represents a validation rule"""
    rule_type: ValidationType
    value: Any = None
    error_message: Optional[str] = None
    custom_validator: Optional[Callable[[Any], bool]] = None

    def validate(self, input_value: Any, form_data: Optional[Dict[str, Any]] = None) -> tuple[bool, Optional[str]]:
        """
        Validate input value against this rule

        Args:
            input_value: The value to validate
            form_data: Complete form data (for cross-field validation)

        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.rule_type == ValidationType.REQUIRED:
            is_valid = input_value is not None and input_value != ""
            if isinstance(input_value, list):
                is_valid = len(input_value) > 0
            return is_valid, self.error_message or "This field is required"

        # Skip other validations if value is empty
        if input_value is None or input_value == "":
            return True, None

        if self.rule_type == ValidationType.MIN_LENGTH:
            is_valid = len(str(input_value)) >= self.value
            return is_valid, self.error_message or f"Minimum length is {self.value} characters"

        elif self.rule_type == ValidationType.MAX_LENGTH:
            is_valid = len(str(input_value)) <= self.value
            return is_valid, self.error_message or f"Maximum length is {self.value} characters"

        elif self.rule_type == ValidationType.MIN_VALUE:
            try:
                is_valid = float(input_value) >= self.value
                return is_valid, self.error_message or f"Minimum value is {self.value}"
            except ValueError:
                return False, "Invalid numeric value"

        elif self.rule_type == ValidationType.MAX_VALUE:
            try:
                is_valid = float(input_value) <= self.value
                return is_valid, self.error_message or f"Maximum value is {self.value}"
            except ValueError:
                return False, "Invalid numeric value"

        elif self.rule_type == ValidationType.PATTERN:
            is_valid = bool(re.match(self.value, str(input_value)))
            return is_valid, self.error_message or "Invalid format"

        elif self.rule_type == ValidationType.EMAIL:
            is_valid = self._validate_email(str(input_value))
            return is_valid, self.error_message or "Invalid email address"

        elif self.rule_type == ValidationType.URL:
            is_valid = self._validate_url(str(input_value))
            return is_valid, self.error_message or "Invalid URL"

        elif self.rule_type == ValidationType.PHONE:
            is_valid = self._validate_phone(str(input_value))
            return is_valid, self.error_message or "Invalid phone number"

        elif self.rule_type == ValidationType.NUMERIC:
            try:
                float(input_value)
                return True, None
            except ValueError:
                return False, self.error_message or "Must be a number"

        elif self.rule_type == ValidationType.ALPHA:
            is_valid = str(input_value).isalpha()
            return is_valid, self.error_message or "Must contain only letters"

        elif self.rule_type == ValidationType.ALPHANUMERIC:
            is_valid = str(input_value).isalnum()
            return is_valid, self.error_message or "Must contain only letters and numbers"

        elif self.rule_type == ValidationType.MATCH_FIELD:
            if form_data and self.value in form_data:
                is_valid = input_value == form_data[self.value]
                return is_valid, self.error_message or f"Must match {self.value}"
            return False, "Cannot verify field match"

        elif self.rule_type == ValidationType.CUSTOM:
            if self.custom_validator:
                try:
                    is_valid = self.custom_validator(input_value)
                    return is_valid, self.error_message or "Validation failed"
                except Exception as e:
                    return False, f"Validation error: {str(e)}"
            return True, None

        return True, None

    @staticmethod
    def _validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def _validate_url(url: str) -> bool:
        """Validate URL format"""
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, url))

    @staticmethod
    def _validate_phone(phone: str) -> bool:
        """Validate phone number format"""
        # Remove common formatting characters
        cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)
        # Check if it's a valid phone number (10-15 digits, optional + prefix)
        pattern = r'^\+?\d{10,15}$'
        return bool(re.match(pattern, cleaned))


class Validator:
    """Validator class for managing multiple validation rules"""

    def __init__(self):
        self.rules: Dict[str, List[ValidationRule]] = {}

    def add_rule(self, field_id: str, rule: ValidationRule) -> None:
        """Add a validation rule for a field"""
        if field_id not in self.rules:
            self.rules[field_id] = []
        self.rules[field_id].append(rule)

    def remove_rule(self, field_id: str, rule_type: ValidationType) -> None:
        """Remove a validation rule"""
        if field_id in self.rules:
            self.rules[field_id] = [
                rule for rule in self.rules[field_id]
                if rule.rule_type != rule_type
            ]

    def validate_field(self, field_id: str, value: Any,
                      form_data: Optional[Dict[str, Any]] = None) -> tuple[bool, List[str]]:
        """
        Validate a field value against all its rules

        Returns:
            Tuple of (is_valid, error_messages)
        """
        if field_id not in self.rules:
            return True, []

        errors = []
        for rule in self.rules[field_id]:
            is_valid, error_msg = rule.validate(value, form_data)
            if not is_valid and error_msg:
                errors.append(error_msg)

        return len(errors) == 0, errors

    def validate_form(self, form_data: Dict[str, Any]) -> tuple[bool, Dict[str, List[str]]]:
        """
        Validate entire form data

        Returns:
            Tuple of (is_valid, field_errors_dict)
        """
        all_errors: Dict[str, List[str]] = {}

        for field_id in self.rules.keys():
            value = form_data.get(field_id)
            is_valid, errors = self.validate_field(field_id, value, form_data)
            if not is_valid:
                all_errors[field_id] = errors

        return len(all_errors) == 0, all_errors

    def clear_rules(self, field_id: Optional[str] = None) -> None:
        """Clear validation rules"""
        if field_id:
            self.rules.pop(field_id, None)
        else:
            self.rules.clear()


class ValidationRuleBuilder:
    """Builder pattern for creating validation rules"""

    @staticmethod
    def required(error_msg: Optional[str] = None) -> ValidationRule:
        """Create a required field rule"""
        return ValidationRule(
            rule_type=ValidationType.REQUIRED,
            error_message=error_msg
        )

    @staticmethod
    def min_length(length: int, error_msg: Optional[str] = None) -> ValidationRule:
        """Create a minimum length rule"""
        return ValidationRule(
            rule_type=ValidationType.MIN_LENGTH,
            value=length,
            error_message=error_msg
        )

    @staticmethod
    def max_length(length: int, error_msg: Optional[str] = None) -> ValidationRule:
        """Create a maximum length rule"""
        return ValidationRule(
            rule_type=ValidationType.MAX_LENGTH,
            value=length,
            error_message=error_msg
        )

    @staticmethod
    def min_value(value: Union[int, float],
                 error_msg: Optional[str] = None) -> ValidationRule:
        """Create a minimum value rule"""
        return ValidationRule(
            rule_type=ValidationType.MIN_VALUE,
            value=value,
            error_message=error_msg
        )

    @staticmethod
    def max_value(value: Union[int, float],
                 error_msg: Optional[str] = None) -> ValidationRule:
        """Create a maximum value rule"""
        return ValidationRule(
            rule_type=ValidationType.MAX_VALUE,
            value=value,
            error_message=error_msg
        )

    @staticmethod
    def pattern(regex: str, error_msg: Optional[str] = None) -> ValidationRule:
        """Create a pattern matching rule"""
        return ValidationRule(
            rule_type=ValidationType.PATTERN,
            value=regex,
            error_message=error_msg
        )

    @staticmethod
    def email(error_msg: Optional[str] = None) -> ValidationRule:
        """Create an email validation rule"""
        return ValidationRule(
            rule_type=ValidationType.EMAIL,
            error_message=error_msg
        )

    @staticmethod
    def url(error_msg: Optional[str] = None) -> ValidationRule:
        """Create a URL validation rule"""
        return ValidationRule(
            rule_type=ValidationType.URL,
            error_message=error_msg
        )

    @staticmethod
    def phone(error_msg: Optional[str] = None) -> ValidationRule:
        """Create a phone number validation rule"""
        return ValidationRule(
            rule_type=ValidationType.PHONE,
            error_message=error_msg
        )

    @staticmethod
    def numeric(error_msg: Optional[str] = None) -> ValidationRule:
        """Create a numeric validation rule"""
        return ValidationRule(
            rule_type=ValidationType.NUMERIC,
            error_message=error_msg
        )

    @staticmethod
    def alpha(error_msg: Optional[str] = None) -> ValidationRule:
        """Create an alphabetic validation rule"""
        return ValidationRule(
            rule_type=ValidationType.ALPHA,
            error_message=error_msg
        )

    @staticmethod
    def alphanumeric(error_msg: Optional[str] = None) -> ValidationRule:
        """Create an alphanumeric validation rule"""
        return ValidationRule(
            rule_type=ValidationType.ALPHANUMERIC,
            error_message=error_msg
        )

    @staticmethod
    def match_field(field_id: str,
                   error_msg: Optional[str] = None) -> ValidationRule:
        """Create a field matching rule (e.g., confirm password)"""
        return ValidationRule(
            rule_type=ValidationType.MATCH_FIELD,
            value=field_id,
            error_message=error_msg
        )

    @staticmethod
    def custom(validator_func: Callable[[Any], bool],
              error_msg: Optional[str] = None) -> ValidationRule:
        """Create a custom validation rule"""
        return ValidationRule(
            rule_type=ValidationType.CUSTOM,
            custom_validator=validator_func,
            error_message=error_msg
        )


# Pre-defined common validation sets
class CommonValidations:
    """Common validation rule combinations"""

    @staticmethod
    def email_field() -> List[ValidationRule]:
        """Standard email field validation"""
        return [
            ValidationRuleBuilder.required("Email is required"),
            ValidationRuleBuilder.email("Please enter a valid email address"),
        ]

    @staticmethod
    def password_field(min_length: int = 8) -> List[ValidationRule]:
        """Standard password field validation"""
        return [
            ValidationRuleBuilder.required("Password is required"),
            ValidationRuleBuilder.min_length(
                min_length,
                f"Password must be at least {min_length} characters"
            ),
            ValidationRuleBuilder.pattern(
                r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)',
                "Password must contain uppercase, lowercase, and numbers"
            ),
        ]

    @staticmethod
    def phone_field(required: bool = True) -> List[ValidationRule]:
        """Standard phone field validation"""
        rules = []
        if required:
            rules.append(ValidationRuleBuilder.required("Phone number is required"))
        rules.append(ValidationRuleBuilder.phone("Please enter a valid phone number"))
        return rules

    @staticmethod
    def url_field(required: bool = False) -> List[ValidationRule]:
        """Standard URL field validation"""
        rules = []
        if required:
            rules.append(ValidationRuleBuilder.required("URL is required"))
        rules.append(ValidationRuleBuilder.url("Please enter a valid URL"))
        return rules

    @staticmethod
    def name_field(required: bool = True) -> List[ValidationRule]:
        """Standard name field validation"""
        rules = []
        if required:
            rules.append(ValidationRuleBuilder.required("Name is required"))
        rules.extend([
            ValidationRuleBuilder.min_length(2, "Name must be at least 2 characters"),
            ValidationRuleBuilder.max_length(50, "Name must be at most 50 characters"),
        ])
        return rules

    @staticmethod
    def age_field(min_age: int = 0, max_age: int = 120) -> List[ValidationRule]:
        """Standard age field validation"""
        return [
            ValidationRuleBuilder.required("Age is required"),
            ValidationRuleBuilder.numeric("Age must be a number"),
            ValidationRuleBuilder.min_value(min_age, f"Age must be at least {min_age}"),
            ValidationRuleBuilder.max_value(max_age, f"Age must be at most {max_age}"),
        ]
