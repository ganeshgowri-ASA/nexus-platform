"""
Field mapping and schema mapping for ETL module.

This module provides utilities for mapping fields between source and target schemas,
type conversions, and transformation rules.
"""

import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import re

from modules.etl.models import Mapping

logger = logging.getLogger(__name__)


class MappingException(Exception):
    """Base exception for mapping errors."""
    pass


class FieldMapper:
    """Handles field-level mappings between source and target schemas."""

    def __init__(self, mapping: Mapping):
        """
        Initialize the field mapper.

        Args:
            mapping: Mapping configuration
        """
        self.mapping = mapping
        self.logger = logging.getLogger(__name__)

    def map_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map a single record from source to target schema.

        Args:
            record: Source record

        Returns:
            Mapped target record
        """
        mapped_record = {}

        # Apply field mappings
        for source_field, target_field in self.mapping.field_mappings.items():
            if source_field in record:
                value = record[source_field]

                # Apply transformation rules if defined
                if source_field in self.mapping.transformation_rules:
                    value = self._apply_transformation(
                        value,
                        self.mapping.transformation_rules[source_field]
                    )

                # Apply type conversion if defined
                if target_field in self.mapping.type_conversions:
                    value = self._convert_type(
                        value,
                        self.mapping.type_conversions[target_field]
                    )

                mapped_record[target_field] = value
            elif target_field in self.mapping.default_values:
                # Use default value if source field is missing
                mapped_record[target_field] = self.mapping.default_values[target_field]

        return mapped_record

    def map_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Map multiple records.

        Args:
            records: List of source records

        Returns:
            List of mapped target records
        """
        return [self.map_record(record) for record in records]

    def _apply_transformation(self, value: Any, transformation: str) -> Any:
        """
        Apply a transformation rule to a value.

        Args:
            value: Input value
            transformation: Transformation rule

        Returns:
            Transformed value
        """
        try:
            if transformation == "uppercase":
                return str(value).upper()
            elif transformation == "lowercase":
                return str(value).lower()
            elif transformation == "trim":
                return str(value).strip()
            elif transformation == "capitalize":
                return str(value).capitalize()
            elif transformation.startswith("substring"):
                # Format: substring(start,end)
                match = re.match(r"substring\((\d+),(\d+)\)", transformation)
                if match:
                    start, end = int(match.group(1)), int(match.group(2))
                    return str(value)[start:end]
            elif transformation.startswith("replace"):
                # Format: replace(old,new)
                match = re.match(r"replace\((.+?),(.+?)\)", transformation)
                if match:
                    old, new = match.group(1), match.group(2)
                    return str(value).replace(old, new)
            elif transformation == "concat":
                # Handled separately for multiple fields
                return value
            else:
                self.logger.warning(f"Unknown transformation: {transformation}")
                return value
        except Exception as e:
            self.logger.error(f"Transformation failed: {str(e)}")
            return value

    def _convert_type(self, value: Any, target_type: str) -> Any:
        """
        Convert value to target type.

        Args:
            value: Input value
            target_type: Target type name

        Returns:
            Converted value
        """
        if value is None:
            return None

        try:
            if target_type == "string":
                return str(value)
            elif target_type == "integer":
                return int(float(value))
            elif target_type == "float":
                return float(value)
            elif target_type == "boolean":
                if isinstance(value, bool):
                    return value
                return str(value).lower() in ["true", "yes", "1", "t", "y"]
            elif target_type == "date":
                if isinstance(value, datetime):
                    return value.date()
                from dateutil import parser
                return parser.parse(str(value)).date()
            elif target_type == "datetime":
                if isinstance(value, datetime):
                    return value
                from dateutil import parser
                return parser.parse(str(value))
            else:
                return value
        except Exception as e:
            self.logger.error(f"Type conversion failed: {str(e)}")
            return value


class TypeConverter:
    """Handles type conversions between different data types."""

    @staticmethod
    def convert(value: Any, target_type: str) -> Any:
        """
        Convert value to target type.

        Args:
            value: Input value
            target_type: Target type

        Returns:
            Converted value
        """
        if value is None:
            return None

        converters = {
            "string": str,
            "integer": lambda x: int(float(x)),
            "float": float,
            "boolean": TypeConverter._to_boolean,
            "date": TypeConverter._to_date,
            "datetime": TypeConverter._to_datetime,
            "json": TypeConverter._to_json
        }

        converter = converters.get(target_type.lower())
        if converter:
            try:
                return converter(value)
            except Exception as e:
                logger.error(f"Type conversion failed for {target_type}: {str(e)}")
                return value
        return value

    @staticmethod
    def _to_boolean(value: Any) -> bool:
        """Convert value to boolean."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ["true", "yes", "1", "t", "y"]
        return bool(value)

    @staticmethod
    def _to_date(value: Any):
        """Convert value to date."""
        if isinstance(value, datetime):
            return value.date()
        from dateutil import parser
        return parser.parse(str(value)).date()

    @staticmethod
    def _to_datetime(value: Any) -> datetime:
        """Convert value to datetime."""
        if isinstance(value, datetime):
            return value
        from dateutil import parser
        return parser.parse(str(value))

    @staticmethod
    def _to_json(value: Any) -> Any:
        """Convert value to JSON."""
        if isinstance(value, str):
            import json
            return json.loads(value)
        return value

    @staticmethod
    def infer_type(value: Any) -> str:
        """
        Infer the type of a value.

        Args:
            value: Input value

        Returns:
            Type name as string
        """
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, datetime):
            return "datetime"
        elif isinstance(value, dict):
            return "object"
        elif isinstance(value, list):
            return "array"
        else:
            return "string"


class SchemaMapper:
    """Handles schema-level mappings and transformations."""

    def __init__(self, source_schema: Dict[str, Any], target_schema: Dict[str, Any]):
        """
        Initialize schema mapper.

        Args:
            source_schema: Source schema definition
            target_schema: Target schema definition
        """
        self.source_schema = source_schema
        self.target_schema = target_schema
        self.logger = logging.getLogger(__name__)

    def generate_mapping(self) -> Dict[str, str]:
        """
        Auto-generate field mappings based on schema analysis.

        Returns:
            Dictionary of field mappings
        """
        mappings = {}

        # Direct name matches
        source_fields = set(self.source_schema.keys())
        target_fields = set(self.target_schema.keys())

        for field in source_fields.intersection(target_fields):
            mappings[field] = field

        # Fuzzy matching for similar names
        unmapped_source = source_fields - set(mappings.keys())
        unmapped_target = target_fields - set(mappings.values())

        for source_field in unmapped_source:
            for target_field in unmapped_target:
                if self._are_similar(source_field, target_field):
                    mappings[source_field] = target_field
                    unmapped_target.remove(target_field)
                    break

        self.logger.info(f"Generated {len(mappings)} field mappings")
        return mappings

    def _are_similar(self, field1: str, field2: str, threshold: float = 0.8) -> bool:
        """
        Check if two field names are similar.

        Args:
            field1: First field name
            field2: Second field name
            threshold: Similarity threshold (0-1)

        Returns:
            True if fields are similar
        """
        # Normalize field names
        f1 = field1.lower().replace("_", "").replace("-", "")
        f2 = field2.lower().replace("_", "").replace("-", "")

        # Simple similarity check
        if f1 == f2:
            return True

        # Check if one contains the other
        if f1 in f2 or f2 in f1:
            return True

        # Levenshtein distance-based similarity
        distance = self._levenshtein_distance(f1, f2)
        max_len = max(len(f1), len(f2))
        similarity = 1 - (distance / max_len)

        return similarity >= threshold

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def validate_mapping(self, mappings: Dict[str, str]) -> Dict[str, List[str]]:
        """
        Validate field mappings against schemas.

        Args:
            mappings: Field mappings to validate

        Returns:
            Dictionary of validation errors
        """
        errors = {}

        for source_field, target_field in mappings.items():
            field_errors = []

            # Check if source field exists
            if source_field not in self.source_schema:
                field_errors.append(f"Source field '{source_field}' not in source schema")

            # Check if target field exists
            if target_field not in self.target_schema:
                field_errors.append(f"Target field '{target_field}' not in target schema")

            # Check type compatibility
            if source_field in self.source_schema and target_field in self.target_schema:
                source_type = self.source_schema[source_field].get("type")
                target_type = self.target_schema[target_field].get("type")

                if source_type and target_type:
                    if not self._are_types_compatible(source_type, target_type):
                        field_errors.append(
                            f"Type mismatch: {source_type} -> {target_type}"
                        )

            if field_errors:
                errors[f"{source_field} -> {target_field}"] = field_errors

        return errors

    def _are_types_compatible(self, source_type: str, target_type: str) -> bool:
        """
        Check if source and target types are compatible.

        Args:
            source_type: Source data type
            target_type: Target data type

        Returns:
            True if types are compatible
        """
        # Same types are always compatible
        if source_type == target_type:
            return True

        # Define compatible type conversions
        compatible_conversions = {
            "integer": ["float", "string", "boolean"],
            "float": ["string"],
            "string": ["integer", "float", "boolean", "date", "datetime"],
            "boolean": ["integer", "string"],
            "date": ["string", "datetime"],
            "datetime": ["string", "date"]
        }

        return target_type in compatible_conversions.get(source_type, [])


class TransformationRules:
    """Defines and applies transformation rules."""

    @staticmethod
    def apply_rule(value: Any, rule: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Apply a transformation rule to a value.

        Args:
            value: Input value
            rule: Rule name
            params: Rule parameters

        Returns:
            Transformed value
        """
        params = params or {}

        rules = {
            "uppercase": lambda v: str(v).upper(),
            "lowercase": lambda v: str(v).lower(),
            "trim": lambda v: str(v).strip(),
            "capitalize": lambda v: str(v).capitalize(),
            "truncate": lambda v: str(v)[:params.get("length", 100)],
            "pad_left": lambda v: str(v).ljust(params.get("length", 10), params.get("char", " ")),
            "pad_right": lambda v: str(v).rjust(params.get("length", 10), params.get("char", " ")),
            "remove_whitespace": lambda v: re.sub(r"\s+", "", str(v)),
            "remove_special_chars": lambda v: re.sub(r"[^a-zA-Z0-9\s]", "", str(v)),
            "extract_numbers": lambda v: re.sub(r"[^0-9]", "", str(v)),
            "hash": lambda v: TransformationRules._hash_value(v, params.get("algorithm", "sha256"))
        }

        rule_func = rules.get(rule)
        if rule_func:
            try:
                return rule_func(value)
            except Exception as e:
                logger.error(f"Rule '{rule}' failed: {str(e)}")
                return value
        else:
            logger.warning(f"Unknown rule: {rule}")
            return value

    @staticmethod
    def _hash_value(value: Any, algorithm: str) -> str:
        """Hash a value using specified algorithm."""
        import hashlib
        value_str = str(value)
        if algorithm == "md5":
            return hashlib.md5(value_str.encode()).hexdigest()
        elif algorithm == "sha256":
            return hashlib.sha256(value_str.encode()).hexdigest()
        elif algorithm == "sha512":
            return hashlib.sha512(value_str.encode()).hexdigest()
        else:
            return hashlib.sha256(value_str.encode()).hexdigest()

    @staticmethod
    def chain_rules(value: Any, rules: List[Dict[str, Any]]) -> Any:
        """
        Apply multiple transformation rules in sequence.

        Args:
            value: Input value
            rules: List of rule configurations

        Returns:
            Transformed value
        """
        result = value
        for rule_config in rules:
            rule_name = rule_config.get("rule")
            params = rule_config.get("params", {})
            result = TransformationRules.apply_rule(result, rule_name, params)
        return result
