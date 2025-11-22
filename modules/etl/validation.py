"""
Data validation and quality checks for ETL module.

This module provides comprehensive data quality validation including
schema validation, business rules, and data profiling.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import Counter

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class ValidationException(Exception):
    """Base exception for validation errors."""
    pass


class ValidationResult:
    """Container for validation results."""

    def __init__(self):
        """Initialize validation result."""
        self.is_valid = True
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.info: List[Dict[str, Any]] = []
        self.metrics: Dict[str, Any] = {}

    def add_error(self, field: str, message: str, value: Any = None) -> None:
        """Add validation error."""
        self.is_valid = False
        self.errors.append({
            "field": field,
            "message": message,
            "value": value,
            "severity": "error"
        })

    def add_warning(self, field: str, message: str, value: Any = None) -> None:
        """Add validation warning."""
        self.warnings.append({
            "field": field,
            "message": message,
            "value": value,
            "severity": "warning"
        })

    def add_info(self, field: str, message: str, value: Any = None) -> None:
        """Add validation info."""
        self.info.append({
            "field": field,
            "message": message,
            "value": value,
            "severity": "info"
        })

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "metrics": self.metrics,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings)
        }


class DataQualityCheck:
    """Performs data quality checks on datasets."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize data quality checker.

        Args:
            config: Configuration options
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

    def validate(self, data: List[Dict[str, Any]]) -> ValidationResult:
        """
        Run all data quality checks.

        Args:
            data: Data records to validate

        Returns:
            ValidationResult object
        """
        result = ValidationResult()

        if not data:
            result.add_error("data", "No data to validate")
            return result

        # Run various checks
        self._check_nulls(data, result)
        self._check_duplicates(data, result)
        self._check_data_types(data, result)
        self._check_value_ranges(data, result)
        self._check_patterns(data, result)
        self._check_referential_integrity(data, result)
        self._profile_data(data, result)

        return result

    def _check_nulls(self, data: List[Dict[str, Any]], result: ValidationResult) -> None:
        """Check for null values in required fields."""
        required_fields = self.config.get("required_fields", [])

        for idx, record in enumerate(data):
            for field in required_fields:
                value = record.get(field)
                if value is None or value == "" or (isinstance(value, float) and np.isnan(value)):
                    result.add_error(
                        field,
                        f"Required field is null at record {idx}",
                        value
                    )

    def _check_duplicates(self, data: List[Dict[str, Any]], result: ValidationResult) -> None:
        """Check for duplicate records."""
        key_fields = self.config.get("unique_fields", [])

        if not key_fields:
            return

        seen = set()
        for idx, record in enumerate(data):
            key = tuple(record.get(f) for f in key_fields)
            if key in seen:
                result.add_warning(
                    ",".join(key_fields),
                    f"Duplicate record found at index {idx}",
                    dict(zip(key_fields, key))
                )
            seen.add(key)

    def _check_data_types(self, data: List[Dict[str, Any]], result: ValidationResult) -> None:
        """Check data types match expected types."""
        type_checks = self.config.get("type_checks", {})

        for idx, record in enumerate(data):
            for field, expected_type in type_checks.items():
                value = record.get(field)
                if value is not None:
                    if not self._is_valid_type(value, expected_type):
                        result.add_error(
                            field,
                            f"Invalid type at record {idx}: expected {expected_type}, got {type(value).__name__}",
                            value
                        )

    def _is_valid_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type."""
        type_map = {
            "string": str,
            "integer": int,
            "float": (int, float),
            "boolean": bool,
            "date": (datetime, str),
            "array": list,
            "object": dict
        }

        expected = type_map.get(expected_type.lower())
        if expected:
            return isinstance(value, expected)
        return True

    def _check_value_ranges(self, data: List[Dict[str, Any]], result: ValidationResult) -> None:
        """Check if values are within expected ranges."""
        range_checks = self.config.get("range_checks", {})

        for idx, record in enumerate(data):
            for field, range_config in range_checks.items():
                value = record.get(field)
                if value is not None:
                    min_val = range_config.get("min")
                    max_val = range_config.get("max")

                    if min_val is not None and value < min_val:
                        result.add_error(
                            field,
                            f"Value below minimum at record {idx}: {value} < {min_val}",
                            value
                        )
                    if max_val is not None and value > max_val:
                        result.add_error(
                            field,
                            f"Value above maximum at record {idx}: {value} > {max_val}",
                            value
                        )

    def _check_patterns(self, data: List[Dict[str, Any]], result: ValidationResult) -> None:
        """Check if string values match expected patterns."""
        pattern_checks = self.config.get("pattern_checks", {})

        for idx, record in enumerate(data):
            for field, pattern in pattern_checks.items():
                value = record.get(field)
                if value is not None and isinstance(value, str):
                    if not re.match(pattern, value):
                        result.add_error(
                            field,
                            f"Value does not match pattern at record {idx}",
                            value
                        )

    def _check_referential_integrity(
        self,
        data: List[Dict[str, Any]],
        result: ValidationResult
    ) -> None:
        """Check referential integrity constraints."""
        ref_checks = self.config.get("referential_checks", {})

        for field, config in ref_checks.items():
            valid_values = set(config.get("valid_values", []))
            if valid_values:
                for idx, record in enumerate(data):
                    value = record.get(field)
                    if value is not None and value not in valid_values:
                        result.add_error(
                            field,
                            f"Invalid reference at record {idx}: {value}",
                            value
                        )

    def _profile_data(self, data: List[Dict[str, Any]], result: ValidationResult) -> None:
        """Generate data profiling metrics."""
        if not data:
            return

        df = pd.DataFrame(data)

        # Basic statistics
        result.metrics["record_count"] = len(data)
        result.metrics["field_count"] = len(df.columns)

        # Null counts
        null_counts = df.isnull().sum().to_dict()
        result.metrics["null_counts"] = null_counts

        # Null percentages
        null_percentages = (df.isnull().sum() / len(df) * 100).to_dict()
        result.metrics["null_percentages"] = null_percentages

        # Unique value counts
        unique_counts = df.nunique().to_dict()
        result.metrics["unique_counts"] = unique_counts

        # Data types
        data_types = df.dtypes.astype(str).to_dict()
        result.metrics["data_types"] = data_types


class SchemaValidator:
    """Validates data against a defined schema."""

    def __init__(self, schema: Dict[str, Any]):
        """
        Initialize schema validator.

        Args:
            schema: Schema definition
        """
        self.schema = schema
        self.logger = logging.getLogger(__name__)

    def validate(self, data: List[Dict[str, Any]]) -> ValidationResult:
        """
        Validate data against schema.

        Args:
            data: Data records to validate

        Returns:
            ValidationResult object
        """
        result = ValidationResult()

        for idx, record in enumerate(data):
            self._validate_record(record, idx, result)

        return result

    def _validate_record(
        self,
        record: Dict[str, Any],
        index: int,
        result: ValidationResult
    ) -> None:
        """Validate a single record against schema."""
        # Check for required fields
        for field, field_schema in self.schema.items():
            if field_schema.get("required", False):
                if field not in record or record[field] is None:
                    result.add_error(
                        field,
                        f"Required field missing at record {index}"
                    )

            # Validate field if present
            if field in record and record[field] is not None:
                self._validate_field(field, record[field], field_schema, index, result)

        # Check for unexpected fields
        if self.schema.get("_strict", False):
            for field in record:
                if field not in self.schema:
                    result.add_warning(
                        field,
                        f"Unexpected field at record {index}",
                        record[field]
                    )

    def _validate_field(
        self,
        field: str,
        value: Any,
        field_schema: Dict[str, Any],
        index: int,
        result: ValidationResult
    ) -> None:
        """Validate a single field value."""
        # Type validation
        expected_type = field_schema.get("type")
        if expected_type and not self._check_type(value, expected_type):
            result.add_error(
                field,
                f"Invalid type at record {index}: expected {expected_type}",
                value
            )

        # Min/max validation for numbers
        if isinstance(value, (int, float)):
            min_val = field_schema.get("min")
            max_val = field_schema.get("max")
            if min_val is not None and value < min_val:
                result.add_error(field, f"Value below minimum at record {index}", value)
            if max_val is not None and value > max_val:
                result.add_error(field, f"Value above maximum at record {index}", value)

        # Length validation for strings
        if isinstance(value, str):
            min_length = field_schema.get("min_length")
            max_length = field_schema.get("max_length")
            if min_length is not None and len(value) < min_length:
                result.add_error(field, f"String too short at record {index}", value)
            if max_length is not None and len(value) > max_length:
                result.add_error(field, f"String too long at record {index}", value)

        # Pattern validation
        pattern = field_schema.get("pattern")
        if pattern and isinstance(value, str):
            if not re.match(pattern, value):
                result.add_error(field, f"Value does not match pattern at record {index}", value)

        # Enum validation
        enum_values = field_schema.get("enum")
        if enum_values and value not in enum_values:
            result.add_error(
                field,
                f"Value not in allowed values at record {index}",
                value
            )

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type."""
        type_map = {
            "string": str,
            "integer": int,
            "float": (int, float),
            "boolean": bool,
            "date": datetime,
            "array": list,
            "object": dict
        }

        expected = type_map.get(expected_type.lower())
        if expected:
            return isinstance(value, expected)
        return True


class BusinessRuleValidator:
    """Validates business rules and complex logic."""

    def __init__(self, rules: List[Dict[str, Any]]):
        """
        Initialize business rule validator.

        Args:
            rules: List of business rule definitions
        """
        self.rules = rules
        self.logger = logging.getLogger(__name__)

    def validate(self, data: List[Dict[str, Any]]) -> ValidationResult:
        """
        Validate data against business rules.

        Args:
            data: Data records to validate

        Returns:
            ValidationResult object
        """
        result = ValidationResult()

        for rule in self.rules:
            self._apply_rule(data, rule, result)

        return result

    def _apply_rule(
        self,
        data: List[Dict[str, Any]],
        rule: Dict[str, Any],
        result: ValidationResult
    ) -> None:
        """Apply a single business rule."""
        rule_type = rule.get("type")

        if rule_type == "conditional":
            self._apply_conditional_rule(data, rule, result)
        elif rule_type == "aggregate":
            self._apply_aggregate_rule(data, rule, result)
        elif rule_type == "cross_field":
            self._apply_cross_field_rule(data, rule, result)
        elif rule_type == "custom":
            self._apply_custom_rule(data, rule, result)
        else:
            self.logger.warning(f"Unknown rule type: {rule_type}")

    def _apply_conditional_rule(
        self,
        data: List[Dict[str, Any]],
        rule: Dict[str, Any],
        result: ValidationResult
    ) -> None:
        """Apply conditional business rule."""
        condition = rule.get("condition")
        action = rule.get("action")

        for idx, record in enumerate(data):
            if self._evaluate_condition(record, condition):
                if action == "error":
                    result.add_error(
                        rule.get("field", "rule"),
                        f"Business rule violation at record {idx}: {rule.get('message')}",
                        record
                    )
                elif action == "warning":
                    result.add_warning(
                        rule.get("field", "rule"),
                        f"Business rule warning at record {idx}: {rule.get('message')}",
                        record
                    )

    def _apply_aggregate_rule(
        self,
        data: List[Dict[str, Any]],
        rule: Dict[str, Any],
        result: ValidationResult
    ) -> None:
        """Apply aggregate business rule."""
        field = rule.get("field")
        agg_type = rule.get("aggregation")
        threshold = rule.get("threshold")

        df = pd.DataFrame(data)
        if field not in df.columns:
            return

        if agg_type == "sum":
            value = df[field].sum()
        elif agg_type == "avg":
            value = df[field].mean()
        elif agg_type == "count":
            value = len(df)
        else:
            return

        operator = rule.get("operator", "==")
        if not self._compare_values(value, operator, threshold):
            result.add_error(
                field,
                f"Aggregate rule violation: {agg_type}({field}) {operator} {threshold}, got {value}"
            )

    def _apply_cross_field_rule(
        self,
        data: List[Dict[str, Any]],
        rule: Dict[str, Any],
        result: ValidationResult
    ) -> None:
        """Apply cross-field validation rule."""
        field1 = rule.get("field1")
        field2 = rule.get("field2")
        operator = rule.get("operator")

        for idx, record in enumerate(data):
            value1 = record.get(field1)
            value2 = record.get(field2)

            if value1 is not None and value2 is not None:
                if not self._compare_values(value1, operator, value2):
                    result.add_error(
                        f"{field1},{field2}",
                        f"Cross-field rule violation at record {idx}: {field1} {operator} {field2}",
                        {field1: value1, field2: value2}
                    )

    def _apply_custom_rule(
        self,
        data: List[Dict[str, Any]],
        rule: Dict[str, Any],
        result: ValidationResult
    ) -> None:
        """Apply custom validation rule."""
        # Placeholder for custom rule implementation
        self.logger.info("Custom rule validation not implemented")

    def _evaluate_condition(self, record: Dict[str, Any], condition: str) -> bool:
        """Evaluate a condition expression."""
        try:
            # Simple expression evaluation
            # In production, use a safer expression evaluator
            return eval(condition, {"__builtins__": {}}, record)
        except Exception as e:
            self.logger.error(f"Condition evaluation failed: {str(e)}")
            return False

    def _compare_values(self, value1: Any, operator: str, value2: Any) -> bool:
        """Compare two values using an operator."""
        operators = {
            "==": lambda x, y: x == y,
            "!=": lambda x, y: x != y,
            ">": lambda x, y: x > y,
            "<": lambda x, y: x < y,
            ">=": lambda x, y: x >= y,
            "<=": lambda x, y: x <= y
        }

        compare_func = operators.get(operator)
        if compare_func:
            try:
                return compare_func(value1, value2)
            except Exception:
                return False
        return False


class DataProfiler:
    """Generates comprehensive data profiling reports."""

    def profile(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate data profile.

        Args:
            data: Data records to profile

        Returns:
            Profiling report as dictionary
        """
        if not data:
            return {"error": "No data to profile"}

        df = pd.DataFrame(data)

        profile = {
            "summary": self._generate_summary(df),
            "columns": self._profile_columns(df),
            "quality": self._assess_quality(df)
        }

        return profile

    def _generate_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate summary statistics."""
        return {
            "record_count": len(df),
            "column_count": len(df.columns),
            "memory_usage": int(df.memory_usage(deep=True).sum()),
            "duplicate_rows": int(df.duplicated().sum())
        }

    def _profile_columns(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Profile individual columns."""
        column_profiles = {}

        for column in df.columns:
            series = df[column]
            column_profiles[column] = {
                "dtype": str(series.dtype),
                "null_count": int(series.isnull().sum()),
                "null_percentage": float(series.isnull().sum() / len(df) * 100),
                "unique_count": int(series.nunique()),
                "unique_percentage": float(series.nunique() / len(df) * 100)
            }

            # Numeric statistics
            if pd.api.types.is_numeric_dtype(series):
                column_profiles[column].update({
                    "min": float(series.min()) if not series.empty else None,
                    "max": float(series.max()) if not series.empty else None,
                    "mean": float(series.mean()) if not series.empty else None,
                    "median": float(series.median()) if not series.empty else None,
                    "std": float(series.std()) if not series.empty else None
                })

            # String statistics
            elif pd.api.types.is_string_dtype(series):
                non_null = series.dropna()
                if not non_null.empty:
                    column_profiles[column].update({
                        "min_length": int(non_null.str.len().min()),
                        "max_length": int(non_null.str.len().max()),
                        "avg_length": float(non_null.str.len().mean())
                    })

        return column_profiles

    def _assess_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess overall data quality."""
        total_cells = len(df) * len(df.columns)
        null_cells = df.isnull().sum().sum()

        return {
            "completeness": float((total_cells - null_cells) / total_cells * 100) if total_cells > 0 else 0,
            "consistency_score": 100.0,  # Placeholder
            "validity_score": 100.0,  # Placeholder
            "overall_score": float((total_cells - null_cells) / total_cells * 100) if total_cells > 0 else 0
        }
