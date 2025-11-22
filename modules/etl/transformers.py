"""
Data transformers for ETL module.

This module provides various data transformation capabilities including
cleaning, validation, enrichment, aggregation, and mapping.
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from decimal import Decimal
import hashlib
import json

import pandas as pd
import numpy as np
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)


class TransformerException(Exception):
    """Base exception for transformer errors."""
    pass


class ValidationException(TransformerException):
    """Exception for validation failures."""
    pass


class BaseTransformer(ABC):
    """Abstract base class for all transformers."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the transformer.

        Args:
            config: Configuration options
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform the data.

        Args:
            data: Input data records

        Returns:
            Transformed data records
        """
        pass

    def transform_single(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a single record.

        Args:
            record: Input record

        Returns:
            Transformed record
        """
        return self.transform([record])[0]


class DataCleaner(BaseTransformer):
    """Transformer for data cleaning operations."""

    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean the data."""
        cleaned_data = []

        for record in data:
            cleaned_record = self._clean_record(record)
            cleaned_data.append(cleaned_record)

        self.logger.info(f"Cleaned {len(cleaned_data)} records")
        return cleaned_data

    def _clean_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Clean a single record."""
        cleaned = {}

        for key, value in record.items():
            # Handle null values
            if value is None or value == "" or (isinstance(value, float) and np.isnan(value)):
                if self.config.get("fill_null"):
                    cleaned[key] = self.config.get("null_value", None)
                elif self.config.get("drop_null"):
                    continue
                else:
                    cleaned[key] = None
            else:
                # Clean strings
                if isinstance(value, str):
                    value = self._clean_string(value)

                # Clean numbers
                elif isinstance(value, (int, float)):
                    value = self._clean_number(value)

                cleaned[key] = value

        return cleaned

    def _clean_string(self, value: str) -> str:
        """Clean string values."""
        # Trim whitespace
        if self.config.get("trim_whitespace", True):
            value = value.strip()

        # Remove extra spaces
        if self.config.get("remove_extra_spaces", True):
            value = re.sub(r'\s+', ' ', value)

        # Convert to lowercase/uppercase
        if self.config.get("lowercase"):
            value = value.lower()
        elif self.config.get("uppercase"):
            value = value.upper()

        # Remove special characters
        if self.config.get("remove_special_chars"):
            value = re.sub(r'[^a-zA-Z0-9\s]', '', value)

        return value

    def _clean_number(self, value: float) -> float:
        """Clean numeric values."""
        # Handle outliers
        if self.config.get("handle_outliers"):
            min_val = self.config.get("min_value")
            max_val = self.config.get("max_value")

            if min_val is not None and value < min_val:
                value = min_val
            if max_val is not None and value > max_val:
                value = max_val

        # Round numbers
        if self.config.get("round_decimals") is not None:
            value = round(value, self.config["round_decimals"])

        return value

    def remove_duplicates(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate records."""
        key_fields = self.config.get("duplicate_keys", [])

        if not key_fields:
            # Remove exact duplicates
            seen = set()
            unique_data = []
            for record in data:
                record_hash = hashlib.md5(
                    json.dumps(record, sort_keys=True).encode()
                ).hexdigest()
                if record_hash not in seen:
                    seen.add(record_hash)
                    unique_data.append(record)
        else:
            # Remove duplicates based on key fields
            seen = set()
            unique_data = []
            for record in data:
                key = tuple(record.get(k) for k in key_fields)
                if key not in seen:
                    seen.add(key)
                    unique_data.append(record)

        removed_count = len(data) - len(unique_data)
        self.logger.info(f"Removed {removed_count} duplicate records")
        return unique_data


class DataValidator(BaseTransformer):
    """Transformer for data validation."""

    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and filter data."""
        valid_data = []
        invalid_count = 0

        for record in data:
            try:
                if self._validate_record(record):
                    valid_data.append(record)
                else:
                    invalid_count += 1
            except ValidationException as e:
                self.logger.warning(f"Validation failed for record: {str(e)}")
                invalid_count += 1

        self.logger.info(f"Validated {len(valid_data)} records, rejected {invalid_count}")
        return valid_data

    def _validate_record(self, record: Dict[str, Any]) -> bool:
        """Validate a single record."""
        validation_rules = self.config.get("validation_rules", {})

        for field, rules in validation_rules.items():
            value = record.get(field)

            # Check required fields
            if rules.get("required") and value is None:
                raise ValidationException(f"Required field '{field}' is missing")

            if value is not None:
                # Type validation
                if "type" in rules:
                    if not self._validate_type(value, rules["type"]):
                        raise ValidationException(f"Field '{field}' has invalid type")

                # Range validation
                if "min" in rules and value < rules["min"]:
                    raise ValidationException(f"Field '{field}' below minimum value")
                if "max" in rules and value > rules["max"]:
                    raise ValidationException(f"Field '{field}' above maximum value")

                # Pattern validation
                if "pattern" in rules and isinstance(value, str):
                    if not re.match(rules["pattern"], value):
                        raise ValidationException(f"Field '{field}' does not match pattern")

                # Length validation
                if "min_length" in rules and len(str(value)) < rules["min_length"]:
                    raise ValidationException(f"Field '{field}' below minimum length")
                if "max_length" in rules and len(str(value)) > rules["max_length"]:
                    raise ValidationException(f"Field '{field}' above maximum length")

                # Enum validation
                if "enum" in rules and value not in rules["enum"]:
                    raise ValidationException(f"Field '{field}' not in allowed values")

        return True

    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate value type."""
        type_mapping = {
            "string": str,
            "integer": int,
            "float": (int, float),
            "boolean": bool,
            "date": (datetime, str),
            "array": list,
            "object": dict
        }

        expected = type_mapping.get(expected_type)
        if expected:
            return isinstance(value, expected)
        return True


class DataEnricher(BaseTransformer):
    """Transformer for data enrichment."""

    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich the data."""
        enriched_data = []

        for record in data:
            enriched_record = self._enrich_record(record)
            enriched_data.append(enriched_record)

        self.logger.info(f"Enriched {len(enriched_data)} records")
        return enriched_data

    def _enrich_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich a single record."""
        enriched = record.copy()

        # Add computed fields
        computed_fields = self.config.get("computed_fields", {})
        for field_name, expression in computed_fields.items():
            try:
                enriched[field_name] = self._compute_field(record, expression)
            except Exception as e:
                self.logger.warning(f"Failed to compute field '{field_name}': {str(e)}")

        # Add constant fields
        constant_fields = self.config.get("constant_fields", {})
        for field_name, value in constant_fields.items():
            enriched[field_name] = value

        # Add timestamps
        if self.config.get("add_timestamp"):
            enriched["_enriched_at"] = datetime.utcnow().isoformat()

        # Add hash/checksum
        if self.config.get("add_hash"):
            enriched["_record_hash"] = self._compute_hash(record)

        return enriched

    def _compute_field(self, record: Dict[str, Any], expression: str) -> Any:
        """Compute a field value from an expression."""
        # Support simple expressions like: "{field1} + {field2}"
        for field, value in record.items():
            expression = expression.replace(f"{{{field}}}", str(value))

        try:
            # Use eval with restricted globals for safety
            return eval(expression, {"__builtins__": {}}, {})
        except Exception:
            return None

    def _compute_hash(self, record: Dict[str, Any]) -> str:
        """Compute hash of record."""
        record_str = json.dumps(record, sort_keys=True)
        return hashlib.sha256(record_str.encode()).hexdigest()


class DataAggregator(BaseTransformer):
    """Transformer for data aggregation."""

    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate the data."""
        group_by = self.config.get("group_by", [])
        aggregations = self.config.get("aggregations", {})

        if not group_by or not aggregations:
            self.logger.warning("No grouping or aggregations specified")
            return data

        # Convert to DataFrame for easier aggregation
        df = pd.DataFrame(data)

        # Perform aggregation
        agg_dict = {}
        for field, agg_func in aggregations.items():
            if agg_func == "sum":
                agg_dict[field] = "sum"
            elif agg_func == "avg" or agg_func == "mean":
                agg_dict[field] = "mean"
            elif agg_func == "count":
                agg_dict[field] = "count"
            elif agg_func == "min":
                agg_dict[field] = "min"
            elif agg_func == "max":
                agg_dict[field] = "max"
            else:
                agg_dict[field] = agg_func

        result_df = df.groupby(group_by).agg(agg_dict).reset_index()
        aggregated_data = result_df.to_dict(orient="records")

        self.logger.info(f"Aggregated {len(data)} records into {len(aggregated_data)} groups")
        return aggregated_data


class DataMapper(BaseTransformer):
    """Transformer for field mapping and renaming."""

    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Map fields in the data."""
        field_mappings = self.config.get("field_mappings", {})
        mapped_data = []

        for record in data:
            mapped_record = self._map_record(record, field_mappings)
            mapped_data.append(mapped_record)

        self.logger.info(f"Mapped {len(mapped_data)} records")
        return mapped_data

    def _map_record(self, record: Dict[str, Any], mappings: Dict[str, str]) -> Dict[str, Any]:
        """Map a single record."""
        mapped = {}

        for source_field, target_field in mappings.items():
            if source_field in record:
                mapped[target_field] = record[source_field]

        # Include unmapped fields if configured
        if self.config.get("include_unmapped", True):
            for field, value in record.items():
                if field not in mappings and field not in mapped:
                    mapped[field] = value

        return mapped


class TypeConverter(BaseTransformer):
    """Transformer for data type conversion."""

    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert data types."""
        type_conversions = self.config.get("type_conversions", {})
        converted_data = []

        for record in data:
            converted_record = self._convert_record(record, type_conversions)
            converted_data.append(converted_record)

        self.logger.info(f"Converted types for {len(converted_data)} records")
        return converted_data

    def _convert_record(
        self,
        record: Dict[str, Any],
        conversions: Dict[str, str]
    ) -> Dict[str, Any]:
        """Convert types in a single record."""
        converted = record.copy()

        for field, target_type in conversions.items():
            if field in converted:
                value = converted[field]
                try:
                    converted[field] = self._convert_value(value, target_type)
                except Exception as e:
                    self.logger.warning(f"Failed to convert field '{field}' to {target_type}: {str(e)}")

        return converted

    def _convert_value(self, value: Any, target_type: str) -> Any:
        """Convert a value to target type."""
        if value is None:
            return None

        if target_type == "string":
            return str(value)
        elif target_type == "integer":
            return int(float(value))
        elif target_type == "float":
            return float(value)
        elif target_type == "boolean":
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ["true", "yes", "1", "t", "y"]
            return bool(value)
        elif target_type == "date" or target_type == "datetime":
            if isinstance(value, datetime):
                return value
            return date_parser.parse(str(value))
        elif target_type == "json":
            if isinstance(value, str):
                return json.loads(value)
            return value
        else:
            return value


class CustomTransformer(BaseTransformer):
    """Transformer for custom transformation functions."""

    def __init__(self, transform_func: Callable, config: Optional[Dict[str, Any]] = None):
        """
        Initialize with custom transformation function.

        Args:
            transform_func: Custom transformation function
            config: Configuration options
        """
        super().__init__(config)
        self.transform_func = transform_func

    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply custom transformation."""
        try:
            transformed_data = self.transform_func(data, self.config)
            self.logger.info(f"Applied custom transformation to {len(transformed_data)} records")
            return transformed_data
        except Exception as e:
            raise TransformerException(f"Custom transformation failed: {str(e)}")


class TransformationPipeline:
    """Pipeline for chaining multiple transformers."""

    def __init__(self, transformers: Optional[List[BaseTransformer]] = None):
        """
        Initialize transformation pipeline.

        Args:
            transformers: List of transformer instances
        """
        self.transformers = transformers or []
        self.logger = logging.getLogger(__name__)

    def add_transformer(self, transformer: BaseTransformer) -> None:
        """Add a transformer to the pipeline."""
        self.transformers.append(transformer)

    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute all transformers in sequence.

        Args:
            data: Input data

        Returns:
            Transformed data
        """
        result = data
        for i, transformer in enumerate(self.transformers):
            try:
                self.logger.info(f"Executing transformer {i + 1}/{len(self.transformers)}: {transformer.__class__.__name__}")
                result = transformer.transform(result)
            except Exception as e:
                self.logger.error(f"Transformer {transformer.__class__.__name__} failed: {str(e)}")
                raise

        return result

    def clear(self) -> None:
        """Clear all transformers from pipeline."""
        self.transformers = []


class TransformerFactory:
    """Factory for creating transformer instances."""

    @staticmethod
    def create_transformer(
        transformer_type: str,
        config: Optional[Dict[str, Any]] = None
    ) -> BaseTransformer:
        """
        Create a transformer instance.

        Args:
            transformer_type: Type of transformer
            config: Configuration options

        Returns:
            Transformer instance
        """
        transformer_map = {
            "cleaner": DataCleaner,
            "validator": DataValidator,
            "enricher": DataEnricher,
            "aggregator": DataAggregator,
            "mapper": DataMapper,
            "type_converter": TypeConverter
        }

        transformer_class = transformer_map.get(transformer_type.lower())
        if not transformer_class:
            raise ValueError(f"Unknown transformer type: {transformer_type}")

        return transformer_class(config)

    @staticmethod
    def create_pipeline(
        transformer_configs: List[Dict[str, Any]]
    ) -> TransformationPipeline:
        """
        Create a transformation pipeline from configuration.

        Args:
            transformer_configs: List of transformer configurations

        Returns:
            TransformationPipeline instance
        """
        pipeline = TransformationPipeline()

        for config in transformer_configs:
            transformer_type = config.get("type")
            transformer_config = config.get("config", {})

            transformer = TransformerFactory.create_transformer(
                transformer_type,
                transformer_config
            )
            pipeline.add_transformer(transformer)

        return pipeline
