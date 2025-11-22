"""
Field mapping and data transformation system.

Handles field mapping between different systems, data transformation rules,
and schema conversion with AI-assisted suggestions.
"""

from typing import Dict, Any, Optional, List, Tuple
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from .models import FieldMapping, Connection, SyncDirection

logger = logging.getLogger(__name__)


class FieldMapper:
    """
    Maps fields between source and target systems.

    Provides intelligent field mapping with transformation support.
    """

    def __init__(self, db: Session):
        """
        Initialize field mapper.

        Args:
            db: Database session
        """
        self.db = db

    def create_mapping(
        self,
        connection_id: int,
        name: str,
        entity_type: str,
        direction: SyncDirection,
        mappings: Dict[str, str],
        **kwargs
    ) -> FieldMapping:
        """
        Create a new field mapping.

        Args:
            connection_id: Connection ID
            name: Mapping name
            entity_type: Entity type (e.g., 'contact', 'deal')
            direction: Sync direction
            mappings: Field mappings {source: target}
            **kwargs: Additional mapping configuration

        Returns:
            Created FieldMapping object
        """
        mapping = FieldMapping(
            connection_id=connection_id,
            name=name,
            entity_type=entity_type,
            direction=direction,
            mappings=mappings,
            **kwargs
        )

        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)

        logger.info(f"Created field mapping: {name}")
        return mapping

    def map_fields(
        self,
        record: Dict[str, Any],
        mapping: FieldMapping,
        direction: str = 'forward'
    ) -> Dict[str, Any]:
        """
        Map fields in a record according to mapping rules.

        Args:
            record: Source record
            mapping: Field mapping configuration
            direction: 'forward' or 'reverse'

        Returns:
            Transformed record
        """
        result = {}
        mappings = mapping.mappings or {}

        if direction == 'forward':
            # Apply mappings as defined
            for source, target in mappings.items():
                value = self._get_value(record, source)
                if value is not None:
                    self._set_value(result, target, value)
        else:
            # Reverse mappings
            for source, target in mappings.items():
                value = self._get_value(record, target)
                if value is not None:
                    self._set_value(result, source, value)

        # Apply default values
        if mapping.default_values:
            for field, default in mapping.default_values.items():
                if field not in result:
                    result[field] = default

        return result

    def _get_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get value using dot notation path."""
        keys = path.split('.')
        value = data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return None
            elif isinstance(value, list) and key.isdigit():
                try:
                    value = value[int(key)]
                except (IndexError, ValueError):
                    return None
            else:
                return None

        return value

    def _set_value(self, data: Dict[str, Any], path: str, value: Any) -> None:
        """Set value using dot notation path."""
        keys = path.split('.')
        current = data

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def suggest_mappings(
        self,
        source_schema: Dict[str, Any],
        target_schema: Dict[str, Any],
        existing_mappings: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Suggest field mappings using simple heuristics.

        Args:
            source_schema: Source field schema
            target_schema: Target field schema
            existing_mappings: Existing mappings to preserve

        Returns:
            List of mapping suggestions
        """
        suggestions = []
        source_fields = set(source_schema.keys())
        target_fields = set(target_schema.keys())
        existing = existing_mappings or {}

        # Exact matches
        exact_matches = source_fields & target_fields
        for field in exact_matches:
            if field not in existing:
                suggestions.append({
                    'source': field,
                    'target': field,
                    'confidence': 1.0,
                    'reason': 'Exact field name match'
                })

        # Similar name matches
        for source in source_fields - exact_matches:
            best_match = None
            best_score = 0.0

            for target in target_fields:
                if target not in [s['target'] for s in suggestions]:
                    score = self._calculate_similarity(source, target)
                    if score > best_score and score > 0.7:
                        best_score = score
                        best_match = target

            if best_match:
                suggestions.append({
                    'source': source,
                    'target': best_match,
                    'confidence': best_score,
                    'reason': f'Similar field names ({best_score:.2%})'
                })

        return suggestions

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity (simple Levenshtein-based)."""
        str1 = str1.lower()
        str2 = str2.lower()

        if str1 == str2:
            return 1.0

        # Check if one contains the other
        if str1 in str2 or str2 in str1:
            return 0.8

        # Simple character overlap
        set1 = set(str1)
        set2 = set(str2)
        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0


class DataTransformer:
    """
    Transforms data according to defined rules.

    Supports various transformation types including format conversion,
    validation, and custom transformations.
    """

    def __init__(self):
        """Initialize data transformer."""
        self._transformers = {
            'uppercase': self._uppercase,
            'lowercase': self._lowercase,
            'trim': self._trim,
            'split': self._split,
            'join': self._join,
            'replace': self._replace,
            'regex': self._regex,
            'date_format': self._date_format,
            'number_format': self._number_format,
            'boolean': self._boolean,
            'default': self._default,
        }

    def transform(
        self,
        value: Any,
        transformation: Dict[str, Any]
    ) -> Any:
        """
        Apply transformation to value.

        Args:
            value: Input value
            transformation: Transformation definition

        Returns:
            Transformed value
        """
        transform_type = transformation.get('type')
        transformer = self._transformers.get(transform_type)

        if transformer:
            return transformer(value, transformation)

        logger.warning(f"Unknown transformation type: {transform_type}")
        return value

    def _uppercase(self, value: Any, config: Dict) -> str:
        """Convert to uppercase."""
        return str(value).upper() if value is not None else ''

    def _lowercase(self, value: Any, config: Dict) -> str:
        """Convert to lowercase."""
        return str(value).lower() if value is not None else ''

    def _trim(self, value: Any, config: Dict) -> str:
        """Trim whitespace."""
        return str(value).strip() if value is not None else ''

    def _split(self, value: Any, config: Dict) -> List[str]:
        """Split string."""
        delimiter = config.get('delimiter', ',')
        if value is not None:
            return str(value).split(delimiter)
        return []

    def _join(self, value: List, config: Dict) -> str:
        """Join list into string."""
        delimiter = config.get('delimiter', ',')
        if isinstance(value, list):
            return delimiter.join(str(v) for v in value)
        return str(value)

    def _replace(self, value: Any, config: Dict) -> str:
        """Replace substring."""
        if value is not None:
            old = config.get('old', '')
            new = config.get('new', '')
            return str(value).replace(old, new)
        return ''

    def _regex(self, value: Any, config: Dict) -> str:
        """Apply regex transformation."""
        import re
        if value is not None:
            pattern = config.get('pattern', '')
            replacement = config.get('replacement', '')
            return re.sub(pattern, replacement, str(value))
        return ''

    def _date_format(self, value: Any, config: Dict) -> str:
        """Format date."""
        if value is not None:
            from datetime import datetime
            try:
                if isinstance(value, str):
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                elif isinstance(value, datetime):
                    dt = value
                else:
                    return str(value)

                format_str = config.get('format', '%Y-%m-%d')
                return dt.strftime(format_str)
            except (ValueError, AttributeError):
                return str(value)
        return ''

    def _number_format(self, value: Any, config: Dict) -> str:
        """Format number."""
        if value is not None:
            try:
                num = float(value)
                decimals = config.get('decimals', 2)
                return f"{num:.{decimals}f}"
            except (ValueError, TypeError):
                return str(value)
        return ''

    def _boolean(self, value: Any, config: Dict) -> bool:
        """Convert to boolean."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', 'yes', '1', 'on')
        return bool(value)

    def _default(self, value: Any, config: Dict) -> Any:
        """Return default if value is None or empty."""
        default = config.get('value')
        if value is None or value == '':
            return default
        return value


class SchemaConverter:
    """
    Converts data between different schema formats.

    Handles schema validation and conversion between various formats.
    """

    def __init__(self):
        """Initialize schema converter."""
        pass

    def convert_schema(
        self,
        data: Dict[str, Any],
        from_format: str,
        to_format: str
    ) -> Dict[str, Any]:
        """
        Convert data from one schema format to another.

        Args:
            data: Input data
            from_format: Source format (e.g., 'salesforce', 'hubspot')
            to_format: Target format

        Returns:
            Converted data
        """
        # Placeholder for schema conversion logic
        logger.info(f"Converting schema from {from_format} to {to_format}")
        return data

    def validate_schema(
        self,
        data: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate data against schema.

        Args:
            data: Data to validate
            schema: Schema definition

        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []

        # Check required fields
        required = schema.get('required', [])
        for field in required:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        # Check field types
        properties = schema.get('properties', {})
        for field, field_schema in properties.items():
            if field in data:
                expected_type = field_schema.get('type')
                value = data[field]

                if expected_type == 'string' and not isinstance(value, str):
                    errors.append(f"Field {field} should be string, got {type(value).__name__}")
                elif expected_type == 'number' and not isinstance(value, (int, float)):
                    errors.append(f"Field {field} should be number, got {type(value).__name__}")
                elif expected_type == 'boolean' and not isinstance(value, bool):
                    errors.append(f"Field {field} should be boolean, got {type(value).__name__}")
                elif expected_type == 'array' and not isinstance(value, list):
                    errors.append(f"Field {field} should be array, got {type(value).__name__}")
                elif expected_type == 'object' and not isinstance(value, dict):
                    errors.append(f"Field {field} should be object, got {type(value).__name__}")

        return len(errors) == 0, errors
