"""
Custom Assertions Module

Provides CustomAssertions, ValidationHelpers, and MatcherLibrary for advanced assertions.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Callable, Type
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class MatcherLibrary:
    """
    Library of custom matchers for assertions.

    Provides reusable matchers for common assertion patterns.
    """

    @staticmethod
    def matches_pattern(value: str, pattern: str) -> bool:
        """Check if value matches regex pattern."""
        return bool(re.match(pattern, value))

    @staticmethod
    def contains_all(container: List, items: List) -> bool:
        """Check if container contains all items."""
        return all(item in container for item in items)

    @staticmethod
    def contains_any(container: List, items: List) -> bool:
        """Check if container contains any item."""
        return any(item in container for item in items)

    @staticmethod
    def has_length(container: Any, length: int) -> bool:
        """Check if container has specific length."""
        return len(container) == length

    @staticmethod
    def is_between(value: float, min_val: float, max_val: float, inclusive: bool = True) -> bool:
        """Check if value is between min and max."""
        if inclusive:
            return min_val <= value <= max_val
        else:
            return min_val < value < max_val

    @staticmethod
    def has_keys(obj: Dict, keys: List[str]) -> bool:
        """Check if dictionary has all specified keys."""
        return all(key in obj for key in keys)

    @staticmethod
    def has_structure(obj: Dict, structure: Dict) -> bool:
        """Check if object matches expected structure."""
        for key, expected_type in structure.items():
            if key not in obj:
                return False
            if not isinstance(obj[key], expected_type):
                return False
        return True

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Check if string is valid email."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if string is valid URL."""
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, url))

    @staticmethod
    def is_valid_uuid(uuid: str) -> bool:
        """Check if string is valid UUID."""
        pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return bool(re.match(pattern, uuid.lower()))


class ValidationHelpers:
    """
    Validation helper functions for common test validations.

    Provides reusable validation logic.
    """

    def __init__(self):
        """Initialize validation helpers."""
        self.logger = logging.getLogger(__name__)
        self.matcher = MatcherLibrary()

    def validate_response_structure(
        self,
        response: Dict[str, Any],
        expected_fields: List[str],
        optional_fields: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Validate API response structure.

        Args:
            response: Response dictionary
            expected_fields: Required fields
            optional_fields: Optional fields

        Returns:
            Validation result
        """
        optional_fields = optional_fields or []
        missing_fields = [field for field in expected_fields if field not in response]
        extra_fields = [
            field for field in response.keys()
            if field not in expected_fields and field not in optional_fields
        ]

        is_valid = len(missing_fields) == 0

        return {
            "valid": is_valid,
            "missing_fields": missing_fields,
            "extra_fields": extra_fields,
            "message": "Valid structure" if is_valid else f"Missing fields: {missing_fields}",
        }

    def validate_data_types(
        self,
        data: Dict[str, Any],
        type_schema: Dict[str, Type],
    ) -> Dict[str, Any]:
        """
        Validate data types against schema.

        Args:
            data: Data to validate
            type_schema: Expected types for each field

        Returns:
            Validation result
        """
        type_errors = []

        for field, expected_type in type_schema.items():
            if field in data:
                if not isinstance(data[field], expected_type):
                    type_errors.append({
                        "field": field,
                        "expected": expected_type.__name__,
                        "actual": type(data[field]).__name__,
                    })

        is_valid = len(type_errors) == 0

        return {
            "valid": is_valid,
            "type_errors": type_errors,
            "message": "All types valid" if is_valid else f"Type errors: {len(type_errors)}",
        }

    def validate_range(
        self,
        value: float,
        min_val: float = None,
        max_val: float = None,
    ) -> Dict[str, Any]:
        """
        Validate value is within range.

        Args:
            value: Value to validate
            min_val: Minimum value
            max_val: Maximum value

        Returns:
            Validation result
        """
        errors = []

        if min_val is not None and value < min_val:
            errors.append(f"Value {value} is less than minimum {min_val}")

        if max_val is not None and value > max_val:
            errors.append(f"Value {value} is greater than maximum {max_val}")

        is_valid = len(errors) == 0

        return {
            "valid": is_valid,
            "errors": errors,
            "message": "Value in range" if is_valid else "; ".join(errors),
        }

    def validate_format(
        self,
        value: str,
        format_type: str,
    ) -> Dict[str, Any]:
        """
        Validate string format.

        Args:
            value: String to validate
            format_type: Format type (email, url, uuid, iso_date, etc.)

        Returns:
            Validation result
        """
        validators = {
            "email": self.matcher.is_valid_email,
            "url": self.matcher.is_valid_url,
            "uuid": self.matcher.is_valid_uuid,
        }

        validator = validators.get(format_type)

        if not validator:
            return {
                "valid": False,
                "error": f"Unknown format type: {format_type}",
            }

        is_valid = validator(value)

        return {
            "valid": is_valid,
            "message": f"Valid {format_type}" if is_valid else f"Invalid {format_type}: {value}",
        }


class CustomAssertions:
    """
    Custom assertion methods for advanced testing.

    Provides fluent, chainable assertions with detailed error messages.
    """

    def __init__(self):
        """Initialize custom assertions."""
        self.logger = logging.getLogger(__name__)
        self.matcher = MatcherLibrary()
        self.validator = ValidationHelpers()

    def assert_json_equal(
        self,
        actual: Dict[str, Any],
        expected: Dict[str, Any],
        message: str = None,
    ) -> None:
        """Assert JSON objects are equal."""
        assert actual == expected, message or f"JSON mismatch:\nExpected: {expected}\nActual: {actual}"

    def assert_json_contains(
        self,
        json_obj: Dict[str, Any],
        subset: Dict[str, Any],
        message: str = None,
    ) -> None:
        """Assert JSON contains subset."""
        for key, value in subset.items():
            assert key in json_obj, message or f"Key '{key}' not found in JSON"
            assert json_obj[key] == value, message or f"Value mismatch for key '{key}'"

    def assert_response_success(
        self,
        response: Dict[str, Any],
        expected_status: int = 200,
    ) -> None:
        """Assert API response is successful."""
        assert "status_code" in response, "Response missing 'status_code'"
        assert response["status_code"] == expected_status, \
            f"Expected status {expected_status}, got {response['status_code']}"

    def assert_response_time(
        self,
        response_time_ms: float,
        max_time_ms: float,
        message: str = None,
    ) -> None:
        """Assert response time is within limit."""
        assert response_time_ms <= max_time_ms, \
            message or f"Response time {response_time_ms}ms exceeds limit {max_time_ms}ms"

    def assert_matches_pattern(
        self,
        value: str,
        pattern: str,
        message: str = None,
    ) -> None:
        """Assert string matches regex pattern."""
        assert self.matcher.matches_pattern(value, pattern), \
            message or f"'{value}' does not match pattern '{pattern}'"

    def assert_contains_all(
        self,
        container: List,
        items: List,
        message: str = None,
    ) -> None:
        """Assert container contains all items."""
        missing = [item for item in items if item not in container]
        assert len(missing) == 0, \
            message or f"Container missing items: {missing}"

    def assert_contains_any(
        self,
        container: List,
        items: List,
        message: str = None,
    ) -> None:
        """Assert container contains at least one item."""
        found = any(item in container for item in items)
        assert found, message or f"Container contains none of: {items}"

    def assert_has_length(
        self,
        container: Any,
        length: int,
        message: str = None,
    ) -> None:
        """Assert container has specific length."""
        actual_length = len(container)
        assert actual_length == length, \
            message or f"Expected length {length}, got {actual_length}"

    def assert_between(
        self,
        value: float,
        min_val: float,
        max_val: float,
        inclusive: bool = True,
        message: str = None,
    ) -> None:
        """Assert value is between min and max."""
        assert self.matcher.is_between(value, min_val, max_val, inclusive), \
            message or f"Value {value} not between {min_val} and {max_val}"

    def assert_has_keys(
        self,
        obj: Dict,
        keys: List[str],
        message: str = None,
    ) -> None:
        """Assert dictionary has all keys."""
        missing_keys = [key for key in keys if key not in obj]
        assert len(missing_keys) == 0, \
            message or f"Missing keys: {missing_keys}"

    def assert_valid_email(
        self,
        email: str,
        message: str = None,
    ) -> None:
        """Assert string is valid email."""
        assert self.matcher.is_valid_email(email), \
            message or f"Invalid email: {email}"

    def assert_valid_url(
        self,
        url: str,
        message: str = None,
    ) -> None:
        """Assert string is valid URL."""
        assert self.matcher.is_valid_url(url), \
            message or f"Invalid URL: {url}"

    def assert_valid_uuid(
        self,
        uuid: str,
        message: str = None,
    ) -> None:
        """Assert string is valid UUID."""
        assert self.matcher.is_valid_uuid(uuid), \
            message or f"Invalid UUID: {uuid}"

    def assert_datetime_recent(
        self,
        dt: datetime,
        max_age_seconds: int = 60,
        message: str = None,
    ) -> None:
        """Assert datetime is recent."""
        age_seconds = (datetime.utcnow() - dt).total_seconds()
        assert age_seconds <= max_age_seconds, \
            message or f"Datetime {dt} is {age_seconds}s old (max: {max_age_seconds}s)"

    def assert_no_duplicates(
        self,
        items: List,
        message: str = None,
    ) -> None:
        """Assert list has no duplicates."""
        assert len(items) == len(set(items)), \
            message or "List contains duplicates"

    def assert_sorted(
        self,
        items: List,
        reverse: bool = False,
        message: str = None,
    ) -> None:
        """Assert list is sorted."""
        expected = sorted(items, reverse=reverse)
        assert items == expected, \
            message or f"List is not sorted ({'descending' if reverse else 'ascending'})"

    def assert_subset(
        self,
        subset: set,
        superset: set,
        message: str = None,
    ) -> None:
        """Assert set is subset of another."""
        assert subset.issubset(superset), \
            message or f"Not a subset: {subset - superset}"

    def assert_type(
        self,
        obj: Any,
        expected_type: Type,
        message: str = None,
    ) -> None:
        """Assert object is of expected type."""
        assert isinstance(obj, expected_type), \
            message or f"Expected type {expected_type.__name__}, got {type(obj).__name__}"
