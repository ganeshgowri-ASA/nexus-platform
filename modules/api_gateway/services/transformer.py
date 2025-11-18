import json
import re
from typing import Any, Dict, Optional


class TransformerService:
    """Service for transforming requests and responses"""

    @staticmethod
    def transform_request(data: Any, rules: Optional[Dict]) -> Any:
        """
        Transform request data based on transformation rules.

        Rules format:
        {
            "rename_fields": {"old_name": "new_name"},
            "remove_fields": ["field1", "field2"],
            "add_fields": {"field": "value"},
            "map_values": {"field": {"old": "new"}},
            "format": "json|xml|form"
        }
        """

        if not rules or not data:
            return data

        try:
            # Parse data if string
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except:
                    return data

            if isinstance(data, dict):
                result = data.copy()

                # Rename fields
                if "rename_fields" in rules:
                    for old_name, new_name in rules["rename_fields"].items():
                        if old_name in result:
                            result[new_name] = result.pop(old_name)

                # Remove fields
                if "remove_fields" in rules:
                    for field in rules["remove_fields"]:
                        result.pop(field, None)

                # Add fields
                if "add_fields" in rules:
                    result.update(rules["add_fields"])

                # Map values
                if "map_values" in rules:
                    for field, mapping in rules["map_values"].items():
                        if field in result and result[field] in mapping:
                            result[field] = mapping[result[field]]

                return result

            return data

        except Exception as e:
            print(f"Request transformation error: {e}")
            return data

    @staticmethod
    def transform_response(data: Any, rules: Optional[Dict]) -> Any:
        """
        Transform response data based on transformation rules.

        Same rules format as transform_request
        """

        if not rules or not data:
            return data

        try:
            # Parse data if string
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except:
                    return data

            if isinstance(data, dict):
                result = data.copy()

                # Apply transformations
                if "rename_fields" in rules:
                    for old_name, new_name in rules["rename_fields"].items():
                        if old_name in result:
                            result[new_name] = result.pop(old_name)

                if "remove_fields" in rules:
                    for field in rules["remove_fields"]:
                        result.pop(field, None)

                if "add_fields" in rules:
                    result.update(rules["add_fields"])

                if "map_values" in rules:
                    for field, mapping in rules["map_values"].items():
                        if field in result and result[field] in mapping:
                            result[field] = mapping[result[field]]

                # Extract nested fields
                if "extract_fields" in rules:
                    for field_path in rules["extract_fields"]:
                        TransformerService._extract_field(result, field_path)

                return result

            return data

        except Exception as e:
            print(f"Response transformation error: {e}")
            return data

    @staticmethod
    def _extract_field(data: dict, field_path: str):
        """Extract nested field to root level"""

        parts = field_path.split(".")
        value = data

        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return

        # Set at root level
        data[parts[-1]] = value

    @staticmethod
    def transform_headers(headers: dict, rules: Optional[Dict]) -> dict:
        """
        Transform headers based on rules.

        Rules format:
        {
            "add": {"Header-Name": "value"},
            "remove": ["Header-Name"],
            "rename": {"Old-Name": "New-Name"}
        }
        """

        if not rules:
            return headers

        result = dict(headers)

        try:
            # Remove headers
            if "remove" in rules:
                for header in rules["remove"]:
                    result.pop(header, None)
                    # Case-insensitive removal
                    result = {k: v for k, v in result.items() if k.lower() != header.lower()}

            # Add headers
            if "add" in rules:
                result.update(rules["add"])

            # Rename headers
            if "rename" in rules:
                for old_name, new_name in rules["rename"].items():
                    if old_name in result:
                        result[new_name] = result.pop(old_name)

            return result

        except Exception as e:
            print(f"Header transformation error: {e}")
            return headers
