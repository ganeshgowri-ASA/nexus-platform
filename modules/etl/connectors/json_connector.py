"""JSON file connector."""
from typing import Any, Dict, Optional
import pandas as pd
from .base import BaseConnector
import json
import os


class JSONConnector(BaseConnector):
    """Connector for JSON files."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.file_path: Optional[str] = None
        self.df: Optional[pd.DataFrame] = None
        self.data: Optional[Any] = None

    def get_required_fields(self) -> list:
        """Get required configuration fields."""
        return ["file_path"]

    def connect(self) -> bool:
        """Establish connection (validate file exists)."""
        try:
            self.validate_config()
            self.file_path = self.config["file_path"]

            if not os.path.exists(self.file_path):
                raise FileNotFoundError(f"JSON file not found: {self.file_path}")

            self.logger.info(f"Connected to JSON file: {self.file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to JSON file: {e}")
            return False

    def extract(self, query: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Extract data from JSON file."""
        try:
            # Extract JSON options from config
            encoding = self.config.get("encoding", "utf-8")
            orient = self.config.get("orient", "records")  # records, index, columns, values
            json_path = self.config.get("json_path", None)  # JSONPath expression

            # Read JSON
            with open(self.file_path, "r", encoding=encoding) as f:
                self.data = json.load(f)

            # Extract nested data if json_path is provided
            if json_path:
                self.data = self._extract_json_path(self.data, json_path)

            # Convert to DataFrame
            if isinstance(self.data, list):
                self.df = pd.DataFrame(self.data)
            elif isinstance(self.data, dict):
                self.df = pd.DataFrame([self.data])
            else:
                raise ValueError("JSON data must be a list or dict")

            # Apply query filters if provided
            if query:
                if "limit" in query:
                    self.df = self.df.head(query["limit"])
                if "columns" in query:
                    self.df = self.df[query["columns"]]
                if "filters" in query:
                    for col, value in query["filters"].items():
                        self.df = self.df[self.df[col] == value]

            self.logger.info(f"Extracted {len(self.df)} records from JSON")
            return self.df

        except Exception as e:
            self.logger.error(f"Error extracting data from JSON: {e}")
            raise

    def _extract_json_path(self, data: Any, path: str) -> Any:
        """Extract data using simple JSONPath-like syntax."""
        # Simple implementation - supports dot notation like "data.items"
        keys = path.split(".")
        result = data
        for key in keys:
            if isinstance(result, dict):
                result = result.get(key)
            elif isinstance(result, list) and key.isdigit():
                result = result[int(key)]
            else:
                raise ValueError(f"Invalid JSON path: {path}")
        return result

    def disconnect(self) -> None:
        """Close connection (cleanup)."""
        self.df = None
        self.data = None
        self.logger.info("Disconnected from JSON file")

    def test_connection(self) -> bool:
        """Test if file is accessible and readable."""
        try:
            if not os.path.exists(self.file_path):
                return False
            # Try parsing JSON
            with open(self.file_path, "r") as f:
                json.load(f)
            return True
        except Exception:
            return False

    def get_schema(self) -> Optional[Dict[str, Any]]:
        """Get JSON schema information."""
        try:
            if self.df is None:
                with open(self.file_path, "r") as f:
                    sample_data = json.load(f)
                sample_df = pd.DataFrame(sample_data) if isinstance(sample_data, list) else pd.DataFrame([sample_data])
            else:
                sample_df = self.df

            return {
                "columns": list(sample_df.columns),
                "dtypes": {col: str(dtype) for col, dtype in sample_df.dtypes.items()},
                "row_count": len(sample_df),
            }
        except Exception as e:
            self.logger.error(f"Error getting schema: {e}")
            return None
