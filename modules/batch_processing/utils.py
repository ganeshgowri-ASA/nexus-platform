"""Utility functions for batch processing module."""

import os
import json
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
import pandas as pd
from loguru import logger
from core.config import settings


class FileImporter:
    """Utility class for importing files (CSV, Excel, JSON)."""

    @staticmethod
    def import_csv(
        file_path: str,
        delimiter: str = ",",
        has_header: bool = True,
        encoding: str = "utf-8",
        skip_rows: int = 0,
        max_rows: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Import CSV file into DataFrame.

        Args:
            file_path: Path to CSV file
            delimiter: CSV delimiter
            has_header: Whether file has header row
            encoding: File encoding
            skip_rows: Number of rows to skip at start
            max_rows: Maximum number of rows to read

        Returns:
            DataFrame with imported data
        """
        try:
            df = pd.read_csv(
                file_path,
                delimiter=delimiter,
                header=0 if has_header else None,
                encoding=encoding,
                skiprows=skip_rows,
                nrows=max_rows
            )
            logger.info(f"Imported CSV: {file_path} - {len(df)} rows, {len(df.columns)} columns")
            return df
        except Exception as e:
            logger.error(f"Error importing CSV {file_path}: {str(e)}")
            raise

    @staticmethod
    def import_excel(
        file_path: str,
        sheet_name: Optional[str] = None,
        has_header: bool = True,
        skip_rows: int = 0,
        max_rows: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Import Excel file into DataFrame.

        Args:
            file_path: Path to Excel file
            sheet_name: Name of sheet to read (None = first sheet)
            has_header: Whether file has header row
            skip_rows: Number of rows to skip at start
            max_rows: Maximum number of rows to read

        Returns:
            DataFrame with imported data
        """
        try:
            df = pd.read_excel(
                file_path,
                sheet_name=sheet_name or 0,
                header=0 if has_header else None,
                skiprows=skip_rows,
                nrows=max_rows
            )
            logger.info(f"Imported Excel: {file_path} - {len(df)} rows, {len(df.columns)} columns")
            return df
        except Exception as e:
            logger.error(f"Error importing Excel {file_path}: {str(e)}")
            raise

    @staticmethod
    def import_json(file_path: str, max_rows: Optional[int] = None) -> pd.DataFrame:
        """
        Import JSON file into DataFrame.

        Args:
            file_path: Path to JSON file
            max_rows: Maximum number of rows to read

        Returns:
            DataFrame with imported data
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Handle both list of objects and single object
            if isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame([data])

            if max_rows:
                df = df.head(max_rows)

            logger.info(f"Imported JSON: {file_path} - {len(df)} rows, {len(df.columns)} columns")
            return df
        except Exception as e:
            logger.error(f"Error importing JSON {file_path}: {str(e)}")
            raise

    @staticmethod
    def detect_file_type(file_path: str) -> str:
        """
        Detect file type from extension.

        Args:
            file_path: Path to file

        Returns:
            File type (csv, excel, json)
        """
        extension = Path(file_path).suffix.lower()
        if extension == ".csv":
            return "csv"
        elif extension in [".xlsx", ".xls"]:
            return "excel"
        elif extension == ".json":
            return "json"
        else:
            raise ValueError(f"Unsupported file type: {extension}")

    @staticmethod
    def validate_file_size(file_path: str) -> bool:
        """
        Validate file size is within limits.

        Args:
            file_path: Path to file

        Returns:
            True if valid, False otherwise
        """
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        return file_size_mb <= settings.MAX_FILE_SIZE_MB


class DataTransformer:
    """Utility class for data transformation operations."""

    @staticmethod
    def transform_uppercase(value: Any) -> str:
        """Convert value to uppercase string."""
        return str(value).upper() if value is not None else ""

    @staticmethod
    def transform_lowercase(value: Any) -> str:
        """Convert value to lowercase string."""
        return str(value).lower() if value is not None else ""

    @staticmethod
    def transform_strip(value: Any) -> str:
        """Strip whitespace from string value."""
        return str(value).strip() if value is not None else ""

    @staticmethod
    def transform_replace(value: Any, old: str, new: str) -> str:
        """Replace substring in value."""
        return str(value).replace(old, new) if value is not None else ""

    @staticmethod
    def transform_numeric(value: Any, default: float = 0.0) -> float:
        """Convert value to numeric."""
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def transform_boolean(value: Any) -> bool:
        """Convert value to boolean."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ["true", "yes", "1", "y"]
        return bool(value)

    @staticmethod
    def transform_date(value: Any, format: str = "%Y-%m-%d") -> str:
        """Convert value to date string."""
        try:
            return pd.to_datetime(value).strftime(format)
        except Exception:
            return str(value)

    @staticmethod
    def apply_transformation(
        df: pd.DataFrame,
        source_column: str,
        target_column: str,
        transformation_type: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Apply transformation to DataFrame column.

        Args:
            df: Input DataFrame
            source_column: Source column name
            target_column: Target column name (can be same as source)
            transformation_type: Type of transformation
            parameters: Additional parameters for transformation

        Returns:
            Transformed DataFrame
        """
        if source_column not in df.columns:
            raise ValueError(f"Source column '{source_column}' not found in DataFrame")

        params = parameters or {}

        # Map transformation types to functions
        transformations = {
            "uppercase": DataTransformer.transform_uppercase,
            "lowercase": DataTransformer.transform_lowercase,
            "strip": DataTransformer.transform_strip,
            "numeric": DataTransformer.transform_numeric,
            "boolean": DataTransformer.transform_boolean,
            "date": DataTransformer.transform_date,
        }

        if transformation_type == "replace":
            old = params.get("old", "")
            new = params.get("new", "")
            df[target_column] = df[source_column].apply(
                lambda x: DataTransformer.transform_replace(x, old, new)
            )
        elif transformation_type in transformations:
            transform_func = transformations[transformation_type]
            df[target_column] = df[source_column].apply(transform_func)
        else:
            raise ValueError(f"Unknown transformation type: {transformation_type}")

        logger.info(
            f"Applied transformation '{transformation_type}' "
            f"from '{source_column}' to '{target_column}'"
        )

        return df

    @staticmethod
    def apply_transformations(
        df: pd.DataFrame,
        transformations: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        Apply multiple transformations to DataFrame.

        Args:
            df: Input DataFrame
            transformations: List of transformation configs

        Returns:
            Transformed DataFrame
        """
        result_df = df.copy()

        for transform_config in transformations:
            result_df = DataTransformer.apply_transformation(
                result_df,
                source_column=transform_config["source_column"],
                target_column=transform_config["target_column"],
                transformation_type=transform_config["transformation_type"],
                parameters=transform_config.get("parameters")
            )

        return result_df


class DataChunker:
    """Utility class for chunking data for parallel processing."""

    @staticmethod
    def chunk_dataframe(
        df: pd.DataFrame,
        chunk_size: int = 100
    ) -> List[pd.DataFrame]:
        """
        Split DataFrame into chunks.

        Args:
            df: Input DataFrame
            chunk_size: Size of each chunk

        Returns:
            List of DataFrame chunks
        """
        chunks = []
        for i in range(0, len(df), chunk_size):
            chunk = df.iloc[i:i + chunk_size]
            chunks.append(chunk)

        logger.info(f"Split DataFrame into {len(chunks)} chunks of size {chunk_size}")
        return chunks

    @staticmethod
    def chunk_list(
        items: List[Any],
        chunk_size: int = 100
    ) -> List[List[Any]]:
        """
        Split list into chunks.

        Args:
            items: Input list
            chunk_size: Size of each chunk

        Returns:
            List of list chunks
        """
        chunks = []
        for i in range(0, len(items), chunk_size):
            chunk = items[i:i + chunk_size]
            chunks.append(chunk)

        logger.info(f"Split list into {len(chunks)} chunks of size {chunk_size}")
        return chunks


class DataExporter:
    """Utility class for exporting processed data."""

    @staticmethod
    def export_to_csv(
        df: pd.DataFrame,
        file_path: str,
        include_index: bool = False
    ) -> str:
        """
        Export DataFrame to CSV file.

        Args:
            df: DataFrame to export
            file_path: Output file path
            include_index: Whether to include index

        Returns:
            Path to exported file
        """
        try:
            df.to_csv(file_path, index=include_index)
            logger.info(f"Exported {len(df)} rows to CSV: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Error exporting to CSV {file_path}: {str(e)}")
            raise

    @staticmethod
    def export_to_excel(
        df: pd.DataFrame,
        file_path: str,
        sheet_name: str = "Sheet1",
        include_index: bool = False
    ) -> str:
        """
        Export DataFrame to Excel file.

        Args:
            df: DataFrame to export
            file_path: Output file path
            sheet_name: Name of Excel sheet
            include_index: Whether to include index

        Returns:
            Path to exported file
        """
        try:
            df.to_excel(file_path, sheet_name=sheet_name, index=include_index)
            logger.info(f"Exported {len(df)} rows to Excel: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Error exporting to Excel {file_path}: {str(e)}")
            raise

    @staticmethod
    def export_to_json(
        df: pd.DataFrame,
        file_path: str,
        orient: str = "records"
    ) -> str:
        """
        Export DataFrame to JSON file.

        Args:
            df: DataFrame to export
            file_path: Output file path
            orient: JSON orientation (records, index, columns, values)

        Returns:
            Path to exported file
        """
        try:
            df.to_json(file_path, orient=orient, indent=2)
            logger.info(f"Exported {len(df)} rows to JSON: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Error exporting to JSON {file_path}: {str(e)}")
            raise


class ProgressTracker:
    """Utility class for tracking batch processing progress."""

    def __init__(self, total_items: int):
        """
        Initialize progress tracker.

        Args:
            total_items: Total number of items to process
        """
        self.total_items = total_items
        self.processed_items = 0
        self.successful_items = 0
        self.failed_items = 0

    def update(self, success: bool = True):
        """
        Update progress.

        Args:
            success: Whether the item was processed successfully
        """
        self.processed_items += 1
        if success:
            self.successful_items += 1
        else:
            self.failed_items += 1

    @property
    def progress_percentage(self) -> float:
        """Get progress percentage."""
        if self.total_items == 0:
            return 0.0
        return (self.processed_items / self.total_items) * 100

    @property
    def success_rate(self) -> float:
        """Get success rate percentage."""
        if self.processed_items == 0:
            return 0.0
        return (self.successful_items / self.processed_items) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_items": self.total_items,
            "processed_items": self.processed_items,
            "successful_items": self.successful_items,
            "failed_items": self.failed_items,
            "progress_percentage": self.progress_percentage,
            "success_rate": self.success_rate
        }


def validate_file_extension(filename: str) -> bool:
    """
    Validate file extension is allowed.

    Args:
        filename: Name of file

    Returns:
        True if valid, False otherwise
    """
    extension = Path(filename).suffix.lower().lstrip(".")
    return extension in settings.allowed_extensions_list
