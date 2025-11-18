"""
Tests for data validation.
"""

import pytest
from modules.etl.validation import (
    ValidationResult,
    DataQualityCheck,
    SchemaValidator,
    BusinessRuleValidator,
    DataProfiler
)


def test_validation_result():
    """Test validation result."""
    result = ValidationResult()

    assert result.is_valid is True
    assert len(result.errors) == 0

    result.add_error("field1", "Error message", "value")
    assert result.is_valid is False
    assert len(result.errors) == 1


def test_data_quality_check_nulls():
    """Test null value checking."""
    data = [
        {"id": 1, "name": "John", "email": "john@example.com"},
        {"id": 2, "name": None, "email": "jane@example.com"},
        {"id": 3, "name": "Bob", "email": None}
    ]

    config = {
        "required_fields": ["name", "email"]
    }

    checker = DataQualityCheck(config)
    result = checker.validate(data)

    assert not result.is_valid
    assert len(result.errors) >= 2


def test_data_quality_check_duplicates():
    """Test duplicate detection."""
    data = [
        {"id": 1, "name": "John"},
        {"id": 1, "name": "John"},  # Duplicate
        {"id": 2, "name": "Jane"}
    ]

    config = {
        "unique_fields": ["id"]
    }

    checker = DataQualityCheck(config)
    result = checker.validate(data)

    assert len(result.warnings) >= 1


def test_schema_validator():
    """Test schema validation."""
    schema = {
        "id": {"type": "integer", "required": True},
        "name": {"type": "string", "required": True, "min_length": 2},
        "age": {"type": "integer", "min": 0, "max": 150},
        "email": {"type": "string", "pattern": r"^[\w\.-]+@[\w\.-]+\.\w+$"}
    }

    data = [
        {"id": 1, "name": "John", "age": 30, "email": "john@example.com"},
        {"id": 2, "name": "J", "age": 200, "email": "invalid-email"}  # Invalid
    ]

    validator = SchemaValidator(schema)
    result = validator.validate(data)

    assert not result.is_valid
    assert len(result.errors) >= 2


def test_business_rule_validator():
    """Test business rule validation."""
    data = [
        {"price": 100, "discount": 10},
        {"price": 50, "discount": 60}  # Invalid: discount > price
    ]

    rules = [
        {
            "type": "cross_field",
            "field1": "discount",
            "field2": "price",
            "operator": "<",
            "message": "Discount must be less than price"
        }
    ]

    validator = BusinessRuleValidator(rules)
    result = validator.validate(data)

    assert not result.is_valid
    assert len(result.errors) >= 1


def test_data_profiler():
    """Test data profiling."""
    data = [
        {"id": 1, "name": "John", "age": 30, "score": 85.5},
        {"id": 2, "name": "Jane", "age": 25, "score": 92.0},
        {"id": 3, "name": "Bob", "age": None, "score": 78.5}
    ]

    profiler = DataProfiler()
    profile = profiler.profile(data)

    assert "summary" in profile
    assert "columns" in profile
    assert "quality" in profile

    assert profile["summary"]["record_count"] == 3
    assert profile["summary"]["column_count"] == 4

    # Check column profiling
    assert "age" in profile["columns"]
    assert profile["columns"]["age"]["null_count"] == 1


def test_data_quality_metrics():
    """Test data quality metrics calculation."""
    data = [
        {"id": 1, "name": "John", "age": 30},
        {"id": 2, "name": "Jane", "age": 25},
        {"id": 3, "name": "Bob", "age": 35}
    ]

    config = {}
    checker = DataQualityCheck(config)
    result = checker.validate(data)

    assert "record_count" in result.metrics
    assert result.metrics["record_count"] == 3
