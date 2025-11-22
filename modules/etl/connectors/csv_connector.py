"""CSV file connector."""
from typing import Any, Dict, Optional
import pandas as pd
from .base import BaseConnector
import os


class CSVConnector(BaseConnector):
    """Connector for CSV files."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.file_path: Optional[str] = None
        self.df: Optional[pd.DataFrame] = None

    def get_required_fields(self) -> list:
        """Get required configuration fields."""
        return ["file_path"]

    def connect(self) -> bool:
        """Establish connection (validate file exists)."""
        try:
            self.validate_config()
            self.file_path = self.config["file_path"]

            if not os.path.exists(self.file_path):
                raise FileNotFoundError(f"CSV file not found: {self.file_path}")

            self.logger.info(f"Connected to CSV file: {self.file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to CSV file: {e}")
            return False

    def extract(self, query: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Extract data from CSV file."""
        try:
            # Extract CSV options from config
            delimiter = self.config.get("delimiter", ",")
            encoding = self.config.get("encoding", "utf-8")
            skip_rows = self.config.get("skip_rows", None)
            use_cols = self.config.get("use_cols", None)
            dtype = self.config.get("dtype", None)

            # Read CSV
            self.df = pd.read_csv(
                self.file_path,
                delimiter=delimiter,
                encoding=encoding,
                skiprows=skip_rows,
                usecols=use_cols,
                dtype=dtype,
            )

            # Apply query filters if provided
            if query:
                if "limit" in query:
                    self.df = self.df.head(query["limit"])
                if "columns" in query:
                    self.df = self.df[query["columns"]]
                if "filters" in query:
                    for col, value in query["filters"].items():
                        self.df = self.df[self.df[col] == value]

            self.logger.info(f"Extracted {len(self.df)} records from CSV")
            return self.df

        except Exception as e:
            self.logger.error(f"Error extracting data from CSV: {e}")
            raise

    def disconnect(self) -> None:
        """Close connection (cleanup)."""
        self.df = None
        self.logger.info("Disconnected from CSV file")

    def test_connection(self) -> bool:
        """Test if file is accessible and readable."""
        try:
            if not os.path.exists(self.file_path):
                return False
            # Try reading first row
            pd.read_csv(self.file_path, nrows=1)
            return True
        except Exception:
            return False

    def get_schema(self) -> Optional[Dict[str, Any]]:
        """Get CSV schema information."""
        try:
            if self.df is None:
                sample_df = pd.read_csv(self.file_path, nrows=100)
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
