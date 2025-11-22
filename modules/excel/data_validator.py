"""Data validation for spreadsheet cells."""
from typing import Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import re


class ValidationType(Enum):
    """Types of validation."""
    ANY = "any"
    WHOLE_NUMBER = "whole_number"
    DECIMAL = "decimal"
    LIST = "list"
    DATE = "date"
    TIME = "time"
    TEXT_LENGTH = "text_length"
    CUSTOM = "custom"


class ValidationOperator(Enum):
    """Validation operators."""
    BETWEEN = "between"
    NOT_BETWEEN = "not_between"
    EQUAL = "equal"
    NOT_EQUAL = "not_equal"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"


@dataclass
class ValidationRule:
    """Data validation rule."""

    type: ValidationType
    operator: Optional[ValidationOperator] = None
    value1: Optional[Any] = None
    value2: Optional[Any] = None
    allow_blank: bool = True
    show_input_message: bool = False
    input_title: Optional[str] = None
    input_message: Optional[str] = None
    show_error_alert: bool = True
    error_title: Optional[str] = None
    error_message: Optional[str] = None
    error_style: str = "stop"  # stop, warning, information

    # For list validation
    list_values: Optional[List[str]] = None

    # For custom validation
    custom_formula: Optional[str] = None

    def validate(self, value: Any) -> tuple[bool, Optional[str]]:
        """
        Validate a value against this rule.

        Args:
            value: Value to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Allow blank if configured
        if self.allow_blank and (value is None or value == ''):
            return True, None

        # Type-specific validation
        if self.type == ValidationType.ANY:
            return True, None

        elif self.type == ValidationType.WHOLE_NUMBER:
            return self._validate_whole_number(value)

        elif self.type == ValidationType.DECIMAL:
            return self._validate_decimal(value)

        elif self.type == ValidationType.LIST:
            return self._validate_list(value)

        elif self.type == ValidationType.DATE:
            return self._validate_date(value)

        elif self.type == ValidationType.TIME:
            return self._validate_time(value)

        elif self.type == ValidationType.TEXT_LENGTH:
            return self._validate_text_length(value)

        elif self.type == ValidationType.CUSTOM:
            return self._validate_custom(value)

        return True, None

    def _validate_whole_number(self, value: Any) -> tuple[bool, Optional[str]]:
        """Validate whole number."""
        try:
            num = int(value)
        except (ValueError, TypeError):
            return False, "Value must be a whole number"

        return self._apply_operator(num)

    def _validate_decimal(self, value: Any) -> tuple[bool, Optional[str]]:
        """Validate decimal number."""
        try:
            num = float(value)
        except (ValueError, TypeError):
            return False, "Value must be a number"

        return self._apply_operator(num)

    def _validate_list(self, value: Any) -> tuple[bool, Optional[str]]:
        """Validate against list of values."""
        if not self.list_values:
            return True, None

        if str(value) not in self.list_values:
            return False, f"Value must be one of: {', '.join(self.list_values)}"

        return True, None

    def _validate_date(self, value: Any) -> tuple[bool, Optional[str]]:
        """Validate date."""
        # Simplified date validation
        # In production, use proper date parsing
        return True, None

    def _validate_time(self, value: Any) -> tuple[bool, Optional[str]]:
        """Validate time."""
        # Simplified time validation
        return True, None

    def _validate_text_length(self, value: Any) -> tuple[bool, Optional[str]]:
        """Validate text length."""
        text = str(value)
        length = len(text)
        return self._apply_operator(length)

    def _validate_custom(self, value: Any) -> tuple[bool, Optional[str]]:
        """Validate using custom formula."""
        if not self.custom_formula:
            return True, None

        # In production, evaluate custom formula
        # For now, just return True
        return True, None

    def _apply_operator(self, value: Union[int, float]) -> tuple[bool, Optional[str]]:
        """Apply comparison operator."""
        if not self.operator:
            return True, None

        try:
            val1 = float(self.value1) if self.value1 is not None else None
            val2 = float(self.value2) if self.value2 is not None else None
        except (ValueError, TypeError):
            return False, "Invalid comparison value"

        if self.operator == ValidationOperator.BETWEEN:
            if val1 is not None and val2 is not None:
                if not (val1 <= value <= val2):
                    return False, f"Value must be between {val1} and {val2}"

        elif self.operator == ValidationOperator.NOT_BETWEEN:
            if val1 is not None and val2 is not None:
                if val1 <= value <= val2:
                    return False, f"Value must not be between {val1} and {val2}"

        elif self.operator == ValidationOperator.EQUAL:
            if val1 is not None and value != val1:
                return False, f"Value must equal {val1}"

        elif self.operator == ValidationOperator.NOT_EQUAL:
            if val1 is not None and value == val1:
                return False, f"Value must not equal {val1}"

        elif self.operator == ValidationOperator.GREATER_THAN:
            if val1 is not None and not (value > val1):
                return False, f"Value must be greater than {val1}"

        elif self.operator == ValidationOperator.LESS_THAN:
            if val1 is not None and not (value < val1):
                return False, f"Value must be less than {val1}"

        elif self.operator == ValidationOperator.GREATER_THAN_OR_EQUAL:
            if val1 is not None and not (value >= val1):
                return False, f"Value must be greater than or equal to {val1}"

        elif self.operator == ValidationOperator.LESS_THAN_OR_EQUAL:
            if val1 is not None and not (value <= val1):
                return False, f"Value must be less than or equal to {val1}"

        return True, None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'type': self.type.value,
            'operator': self.operator.value if self.operator else None,
            'value1': self.value1,
            'value2': self.value2,
            'allow_blank': self.allow_blank,
            'show_input_message': self.show_input_message,
            'input_title': self.input_title,
            'input_message': self.input_message,
            'show_error_alert': self.show_error_alert,
            'error_title': self.error_title,
            'error_message': self.error_message,
            'error_style': self.error_style,
            'list_values': self.list_values,
            'custom_formula': self.custom_formula
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ValidationRule':
        """Create from dictionary."""
        return cls(
            type=ValidationType(data['type']),
            operator=ValidationOperator(data['operator']) if data.get('operator') else None,
            value1=data.get('value1'),
            value2=data.get('value2'),
            allow_blank=data.get('allow_blank', True),
            show_input_message=data.get('show_input_message', False),
            input_title=data.get('input_title'),
            input_message=data.get('input_message'),
            show_error_alert=data.get('show_error_alert', True),
            error_title=data.get('error_title'),
            error_message=data.get('error_message'),
            error_style=data.get('error_style', 'stop'),
            list_values=data.get('list_values'),
            custom_formula=data.get('custom_formula')
        )


class DataValidator:
    """Manage data validation rules for cells."""

    def __init__(self):
        """Initialize data validator."""
        self.rules: dict[tuple[int, int], ValidationRule] = {}

    def add_rule(self, row: int, col: int, rule: ValidationRule) -> None:
        """
        Add validation rule to a cell.

        Args:
            row: Row index
            col: Column index
            rule: Validation rule
        """
        self.rules[(row, col)] = rule

    def remove_rule(self, row: int, col: int) -> None:
        """
        Remove validation rule from a cell.

        Args:
            row: Row index
            col: Column index
        """
        if (row, col) in self.rules:
            del self.rules[(row, col)]

    def get_rule(self, row: int, col: int) -> Optional[ValidationRule]:
        """
        Get validation rule for a cell.

        Args:
            row: Row index
            col: Column index

        Returns:
            Validation rule if exists, None otherwise
        """
        return self.rules.get((row, col))

    def validate_cell(self, row: int, col: int, value: Any) -> tuple[bool, Optional[str]]:
        """
        Validate a cell value.

        Args:
            row: Row index
            col: Column index
            value: Value to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        rule = self.get_rule(row, col)
        if rule:
            return rule.validate(value)
        return True, None

    def apply_rule_to_range(self, start_row: int, start_col: int,
                          end_row: int, end_col: int, rule: ValidationRule) -> None:
        """
        Apply validation rule to a range of cells.

        Args:
            start_row: Starting row
            start_col: Starting column
            end_row: Ending row
            end_col: Ending column
            rule: Validation rule to apply
        """
        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                self.add_rule(row, col, rule)

    def create_dropdown_rule(self, options: List[str], allow_blank: bool = True) -> ValidationRule:
        """
        Create a dropdown list validation rule.

        Args:
            options: List of dropdown options
            allow_blank: Whether to allow blank values

        Returns:
            Validation rule
        """
        return ValidationRule(
            type=ValidationType.LIST,
            list_values=options,
            allow_blank=allow_blank,
            show_input_message=True,
            input_title="Select Value",
            input_message=f"Choose from: {', '.join(options)}",
            show_error_alert=True,
            error_title="Invalid Value",
            error_message=f"Please select one of: {', '.join(options)}",
            error_style="stop"
        )

    def create_number_range_rule(self, min_value: float, max_value: float,
                                allow_blank: bool = True) -> ValidationRule:
        """
        Create a number range validation rule.

        Args:
            min_value: Minimum value
            max_value: Maximum value
            allow_blank: Whether to allow blank values

        Returns:
            Validation rule
        """
        return ValidationRule(
            type=ValidationType.DECIMAL,
            operator=ValidationOperator.BETWEEN,
            value1=min_value,
            value2=max_value,
            allow_blank=allow_blank,
            show_input_message=True,
            input_title="Number Range",
            input_message=f"Enter a number between {min_value} and {max_value}",
            show_error_alert=True,
            error_title="Invalid Number",
            error_message=f"Value must be between {min_value} and {max_value}",
            error_style="stop"
        )

    def create_text_length_rule(self, min_length: Optional[int] = None,
                               max_length: Optional[int] = None,
                               allow_blank: bool = True) -> ValidationRule:
        """
        Create a text length validation rule.

        Args:
            min_length: Minimum text length
            max_length: Maximum text length
            allow_blank: Whether to allow blank values

        Returns:
            Validation rule
        """
        if min_length is not None and max_length is not None:
            operator = ValidationOperator.BETWEEN
            value1 = min_length
            value2 = max_length
            message = f"between {min_length} and {max_length} characters"
        elif min_length is not None:
            operator = ValidationOperator.GREATER_THAN_OR_EQUAL
            value1 = min_length
            value2 = None
            message = f"at least {min_length} characters"
        elif max_length is not None:
            operator = ValidationOperator.LESS_THAN_OR_EQUAL
            value1 = max_length
            value2 = None
            message = f"at most {max_length} characters"
        else:
            operator = None
            value1 = None
            value2 = None
            message = "any length"

        return ValidationRule(
            type=ValidationType.TEXT_LENGTH,
            operator=operator,
            value1=value1,
            value2=value2,
            allow_blank=allow_blank,
            show_input_message=True,
            input_title="Text Length",
            input_message=f"Text must be {message}",
            show_error_alert=True,
            error_title="Invalid Text Length",
            error_message=f"Text must be {message}",
            error_style="stop"
        )
