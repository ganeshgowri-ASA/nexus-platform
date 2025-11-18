"""Data transformation engine for Pipeline module."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Callable, Optional
import re
from datetime import datetime
from core.utils import get_logger

logger = get_logger(__name__)


class BaseTransformation(ABC):
    """Base class for all transformations."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize transformation.

        Args:
            config: Transformation configuration
        """
        self.config = config

    @abstractmethod
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply transformation to data.

        Args:
            data: Input data records

        Returns:
            Transformed data records
        """
        pass

    def validate_config(self) -> bool:
        """
        Validate transformation configuration.

        Returns:
            True if configuration is valid
        """
        return True


# ============================================================================
# Filter Transformations
# ============================================================================

class FilterTransformation(BaseTransformation):
    """Filter records based on conditions."""

    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter data based on conditions."""
        conditions = self.config.get("conditions", [])

        if not conditions:
            return data

        filtered_data = []

        for record in data:
            if self._evaluate_conditions(record, conditions):
                filtered_data.append(record)

        logger.info(f"Filtered {len(data)} -> {len(filtered_data)} records")
        return filtered_data

    def _evaluate_conditions(self, record: Dict[str, Any], conditions: List[Dict]) -> bool:
        """Evaluate all conditions for a record."""
        operator = self.config.get("operator", "AND")

        results = []
        for condition in conditions:
            field = condition.get("field")
            op = condition.get("operator")
            value = condition.get("value")

            record_value = record.get(field)

            if op == "equals":
                results.append(record_value == value)
            elif op == "not_equals":
                results.append(record_value != value)
            elif op == "greater_than":
                results.append(record_value > value)
            elif op == "less_than":
                results.append(record_value < value)
            elif op == "contains":
                results.append(value in str(record_value))
            elif op == "regex":
                results.append(bool(re.match(value, str(record_value))))
            elif op == "is_null":
                results.append(record_value is None)
            elif op == "is_not_null":
                results.append(record_value is not None)

        if operator == "AND":
            return all(results)
        elif operator == "OR":
            return any(results)
        else:
            return False


# ============================================================================
# Map Transformations
# ============================================================================

class MapTransformation(BaseTransformation):
    """Map/transform fields in records."""

    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply field mappings."""
        mappings = self.config.get("mappings", {})

        if not mappings:
            return data

        transformed_data = []

        for record in data:
            new_record = {}

            for target_field, source_config in mappings.items():
                if isinstance(source_config, str):
                    # Simple field mapping
                    new_record[target_field] = record.get(source_config)
                elif isinstance(source_config, dict):
                    # Complex mapping with transformation
                    source_field = source_config.get("field")
                    transform_type = source_config.get("transform")

                    value = record.get(source_field)

                    if transform_type == "uppercase":
                        value = str(value).upper()
                    elif transform_type == "lowercase":
                        value = str(value).lower()
                    elif transform_type == "trim":
                        value = str(value).strip()
                    elif transform_type == "int":
                        value = int(value) if value else None
                    elif transform_type == "float":
                        value = float(value) if value else None
                    elif transform_type == "bool":
                        value = bool(value)
                    elif transform_type == "date":
                        format_str = source_config.get("format", "%Y-%m-%d")
                        value = datetime.strptime(str(value), format_str)

                    new_record[target_field] = value

            # Include unmapped fields if specified
            if self.config.get("include_unmapped", False):
                for field, value in record.items():
                    if field not in new_record:
                        new_record[field] = value

            transformed_data.append(new_record)

        logger.info(f"Mapped {len(data)} records with {len(mappings)} field mappings")
        return transformed_data


# ============================================================================
# Aggregate Transformations
# ============================================================================

class AggregateTransformation(BaseTransformation):
    """Aggregate records based on grouping and aggregation functions."""

    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate data."""
        group_by = self.config.get("group_by", [])
        aggregations = self.config.get("aggregations", [])

        if not group_by or not aggregations:
            return data

        # Group records
        groups = {}
        for record in data:
            key = tuple(record.get(field) for field in group_by)

            if key not in groups:
                groups[key] = []

            groups[key].append(record)

        # Aggregate each group
        aggregated_data = []

        for key, records in groups.items():
            agg_record = {}

            # Add group by fields
            for i, field in enumerate(group_by):
                agg_record[field] = key[i]

            # Apply aggregations
            for agg in aggregations:
                field = agg.get("field")
                function = agg.get("function")
                alias = agg.get("alias", f"{function}_{field}")

                values = [r.get(field) for r in records if r.get(field) is not None]

                if function == "count":
                    agg_record[alias] = len(records)
                elif function == "sum":
                    agg_record[alias] = sum(values)
                elif function == "avg":
                    agg_record[alias] = sum(values) / len(values) if values else None
                elif function == "min":
                    agg_record[alias] = min(values) if values else None
                elif function == "max":
                    agg_record[alias] = max(values) if values else None
                elif function == "first":
                    agg_record[alias] = values[0] if values else None
                elif function == "last":
                    agg_record[alias] = values[-1] if values else None

            aggregated_data.append(agg_record)

        logger.info(f"Aggregated {len(data)} -> {len(aggregated_data)} records")
        return aggregated_data


# ============================================================================
# Sort Transformation
# ============================================================================

class SortTransformation(BaseTransformation):
    """Sort records."""

    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort data."""
        sort_fields = self.config.get("fields", [])

        if not sort_fields:
            return data

        # Build sort key function
        def sort_key(record):
            keys = []
            for field_config in sort_fields:
                if isinstance(field_config, str):
                    field = field_config
                    reverse = False
                else:
                    field = field_config.get("field")
                    reverse = field_config.get("order", "asc") == "desc"

                value = record.get(field)

                # Handle None values
                if value is None:
                    value = "" if isinstance(value, str) else 0

                keys.append(value if not reverse else -value if isinstance(value, (int, float)) else value)

            return tuple(keys)

        sorted_data = sorted(data, key=sort_key)

        logger.info(f"Sorted {len(data)} records")
        return sorted_data


# ============================================================================
# Deduplicate Transformation
# ============================================================================

class DeduplicateTransformation(BaseTransformation):
    """Remove duplicate records."""

    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate data."""
        key_fields = self.config.get("key_fields", [])

        if not key_fields:
            # Deduplicate based on all fields
            seen = set()
            deduped_data = []

            for record in data:
                record_str = str(sorted(record.items()))
                if record_str not in seen:
                    seen.add(record_str)
                    deduped_data.append(record)
        else:
            # Deduplicate based on specific fields
            seen = set()
            deduped_data = []

            for record in data:
                key = tuple(record.get(field) for field in key_fields)
                if key not in seen:
                    seen.add(key)
                    deduped_data.append(record)

        logger.info(f"Deduplicated {len(data)} -> {len(deduped_data)} records")
        return deduped_data


# ============================================================================
# Join Transformation
# ============================================================================

class JoinTransformation(BaseTransformation):
    """Join two datasets."""

    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Join with another dataset.

        Note: This requires the second dataset to be provided in config
        """
        right_data = self.config.get("right_data", [])
        join_type = self.config.get("join_type", "inner")
        left_key = self.config.get("left_key")
        right_key = self.config.get("right_key")

        if not right_data or not left_key or not right_key:
            logger.warning("Join transformation requires right_data, left_key, and right_key")
            return data

        # Build index for right data
        right_index = {}
        for record in right_data:
            key = record.get(right_key)
            if key not in right_index:
                right_index[key] = []
            right_index[key].append(record)

        # Perform join
        joined_data = []

        for left_record in data:
            left_key_value = left_record.get(left_key)
            right_records = right_index.get(left_key_value, [])

            if right_records:
                for right_record in right_records:
                    # Merge records
                    joined_record = {**left_record, **right_record}
                    joined_data.append(joined_record)
            elif join_type in ["left", "outer"]:
                joined_data.append(left_record)

        logger.info(f"Joined {len(data)} left records with right data")
        return joined_data


# ============================================================================
# Validation Transformation
# ============================================================================

class ValidationTransformation(BaseTransformation):
    """Validate records and mark/remove invalid ones."""

    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate data."""
        validations = self.config.get("validations", [])
        on_error = self.config.get("on_error", "mark")  # mark or remove

        if not validations:
            return data

        validated_data = []
        invalid_count = 0

        for record in data:
            is_valid = True
            errors = []

            for validation in validations:
                field = validation.get("field")
                rule = validation.get("rule")
                params = validation.get("params", {})

                value = record.get(field)

                if rule == "required" and value is None:
                    is_valid = False
                    errors.append(f"{field} is required")
                elif rule == "type":
                    expected_type = params.get("type")
                    if not isinstance(value, eval(expected_type)):
                        is_valid = False
                        errors.append(f"{field} must be {expected_type}")
                elif rule == "min_length" and len(str(value)) < params.get("length"):
                    is_valid = False
                    errors.append(f"{field} must be at least {params.get('length')} characters")
                elif rule == "max_length" and len(str(value)) > params.get("length"):
                    is_valid = False
                    errors.append(f"{field} must be at most {params.get('length')} characters")
                elif rule == "pattern":
                    if not re.match(params.get("pattern"), str(value)):
                        is_valid = False
                        errors.append(f"{field} does not match pattern")

            if is_valid:
                validated_data.append(record)
            else:
                invalid_count += 1
                if on_error == "mark":
                    record["_validation_errors"] = errors
                    validated_data.append(record)

        logger.info(f"Validated {len(data)} records, {invalid_count} invalid")
        return validated_data


# ============================================================================
# Custom Python Transformation
# ============================================================================

class CustomPythonTransformation(BaseTransformation):
    """Execute custom Python code for transformation."""

    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply custom Python transformation."""
        code = self.config.get("code")

        if not code:
            logger.warning("No code provided for custom transformation")
            return data

        try:
            # Create a safe namespace
            namespace = {
                "data": data,
                "logger": logger,
                "datetime": datetime,
                "re": re
            }

            # Execute custom code
            exec(code, namespace)

            # Get transformed data
            transformed_data = namespace.get("result", data)

            logger.info(f"Applied custom transformation to {len(data)} records")
            return transformed_data

        except Exception as e:
            logger.error(f"Error in custom transformation: {e}")
            raise


# ============================================================================
# Transformation Factory
# ============================================================================

class TransformationFactory:
    """Factory for creating transformations."""

    _transformations = {
        "filter": FilterTransformation,
        "map": MapTransformation,
        "aggregate": AggregateTransformation,
        "sort": SortTransformation,
        "deduplicate": DeduplicateTransformation,
        "join": JoinTransformation,
        "validation": ValidationTransformation,
        "custom_python": CustomPythonTransformation,
    }

    @classmethod
    def create(cls, transform_type: str, config: Dict[str, Any]) -> BaseTransformation:
        """
        Create a transformation instance.

        Args:
            transform_type: Type of transformation
            config: Transformation configuration

        Returns:
            Transformation instance
        """
        transformation_class = cls._transformations.get(transform_type)

        if not transformation_class:
            raise ValueError(f"Unknown transformation type: {transform_type}")

        return transformation_class(config)

    @classmethod
    def register(cls, transform_type: str, transformation_class: type):
        """
        Register a new transformation type.

        Args:
            transform_type: Type identifier
            transformation_class: Transformation class
        """
        cls._transformations[transform_type] = transformation_class

    @classmethod
    def get_available_transformations(cls) -> List[str]:
        """
        Get list of available transformation types.

        Returns:
            List of transformation type names
        """
        return list(cls._transformations.keys())


# ============================================================================
# Transformation Pipeline
# ============================================================================

class TransformationPipeline:
    """Chain multiple transformations together."""

    def __init__(self, transformations: List[BaseTransformation]):
        """
        Initialize transformation pipeline.

        Args:
            transformations: List of transformations to apply
        """
        self.transformations = transformations

    def execute(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute all transformations in sequence.

        Args:
            data: Input data

        Returns:
            Transformed data
        """
        current_data = data

        for i, transformation in enumerate(self.transformations):
            logger.info(f"Applying transformation {i + 1}/{len(self.transformations)}")
            current_data = transformation.transform(current_data)

        return current_data
