"""Data transformation service."""
from typing import Any, Dict, List, Callable
import pandas as pd
import numpy as np
from modules.etl.core.constants import TransformationType
from shared.utils.logger import get_logger
import re
from datetime import datetime

logger = get_logger(__name__)


class TransformationService:
    """Service for applying data transformations."""

    def __init__(self):
        self.logger = logger
        self.transformation_map: Dict[str, Callable] = {
            TransformationType.RENAME_COLUMNS: self.rename_columns,
            TransformationType.SELECT_COLUMNS: self.select_columns,
            TransformationType.DROP_COLUMNS: self.drop_columns,
            TransformationType.FILTER_ROWS: self.filter_rows,
            TransformationType.CONVERT_TYPE: self.convert_type,
            TransformationType.FILL_NULL: self.fill_null,
            TransformationType.DROP_NULL: self.drop_null,
            TransformationType.REPLACE_VALUE: self.replace_value,
            TransformationType.AGGREGATE: self.aggregate,
            TransformationType.GROUP_BY: self.group_by,
            TransformationType.SORT: self.sort,
            TransformationType.DEDUPLICATE: self.deduplicate,
            TransformationType.REGEX_EXTRACT: self.regex_extract,
            TransformationType.STRING_OPERATION: self.string_operation,
            TransformationType.DATE_OPERATION: self.date_operation,
            TransformationType.MATH_OPERATION: self.math_operation,
        }

    def apply_transformations(self, df: pd.DataFrame, transformations: List[Dict[str, Any]]) -> pd.DataFrame:
        """Apply a list of transformations to a DataFrame."""
        result_df = df.copy()

        for idx, transform in enumerate(transformations):
            try:
                transform_type = transform.get("type")
                config = transform.get("config", {})

                if transform_type not in self.transformation_map:
                    self.logger.warning(f"Unknown transformation type: {transform_type}")
                    continue

                transformation_func = self.transformation_map[transform_type]
                result_df = transformation_func(result_df, config)

                self.logger.info(f"Applied transformation {idx + 1}/{len(transformations)}: {transform_type}")

            except Exception as e:
                self.logger.error(f"Error applying transformation {transform_type}: {e}")
                raise

        return result_df

    def rename_columns(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Rename columns."""
        column_mapping = config.get("mapping", {})
        return df.rename(columns=column_mapping)

    def select_columns(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Select specific columns."""
        columns = config.get("columns", [])
        return df[columns]

    def drop_columns(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Drop specified columns."""
        columns = config.get("columns", [])
        return df.drop(columns=columns)

    def filter_rows(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Filter rows based on conditions."""
        conditions = config.get("conditions", [])
        result_df = df.copy()

        for condition in conditions:
            column = condition.get("column")
            operator = condition.get("operator")
            value = condition.get("value")

            if operator == "==":
                result_df = result_df[result_df[column] == value]
            elif operator == "!=":
                result_df = result_df[result_df[column] != value]
            elif operator == ">":
                result_df = result_df[result_df[column] > value]
            elif operator == ">=":
                result_df = result_df[result_df[column] >= value]
            elif operator == "<":
                result_df = result_df[result_df[column] < value]
            elif operator == "<=":
                result_df = result_df[result_df[column] <= value]
            elif operator == "in":
                result_df = result_df[result_df[column].isin(value)]
            elif operator == "not in":
                result_df = result_df[~result_df[column].isin(value)]
            elif operator == "contains":
                result_df = result_df[result_df[column].str.contains(value, na=False)]
            elif operator == "startswith":
                result_df = result_df[result_df[column].str.startswith(value, na=False)]
            elif operator == "endswith":
                result_df = result_df[result_df[column].str.endswith(value, na=False)]

        return result_df

    def convert_type(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Convert column data types."""
        conversions = config.get("conversions", {})
        result_df = df.copy()

        for column, dtype in conversions.items():
            if column not in result_df.columns:
                continue

            try:
                if dtype == "int":
                    result_df[column] = pd.to_numeric(result_df[column], errors="coerce").astype("Int64")
                elif dtype == "float":
                    result_df[column] = pd.to_numeric(result_df[column], errors="coerce")
                elif dtype == "str":
                    result_df[column] = result_df[column].astype(str)
                elif dtype == "datetime":
                    result_df[column] = pd.to_datetime(result_df[column], errors="coerce")
                elif dtype == "bool":
                    result_df[column] = result_df[column].astype(bool)
            except Exception as e:
                self.logger.warning(f"Failed to convert column {column} to {dtype}: {e}")

        return result_df

    def fill_null(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Fill null values."""
        strategy = config.get("strategy", "constant")
        columns = config.get("columns", None)
        value = config.get("value", None)

        result_df = df.copy()
        target_columns = columns if columns else result_df.columns

        if strategy == "constant":
            result_df[target_columns] = result_df[target_columns].fillna(value)
        elif strategy == "mean":
            result_df[target_columns] = result_df[target_columns].fillna(result_df[target_columns].mean())
        elif strategy == "median":
            result_df[target_columns] = result_df[target_columns].fillna(result_df[target_columns].median())
        elif strategy == "mode":
            result_df[target_columns] = result_df[target_columns].fillna(result_df[target_columns].mode().iloc[0])
        elif strategy == "forward_fill":
            result_df[target_columns] = result_df[target_columns].fillna(method="ffill")
        elif strategy == "backward_fill":
            result_df[target_columns] = result_df[target_columns].fillna(method="bfill")

        return result_df

    def drop_null(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Drop rows with null values."""
        columns = config.get("columns", None)
        how = config.get("how", "any")  # any or all

        if columns:
            return df.dropna(subset=columns, how=how)
        return df.dropna(how=how)

    def replace_value(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Replace values in specified columns."""
        column = config.get("column")
        replacements = config.get("replacements", {})

        result_df = df.copy()
        result_df[column] = result_df[column].replace(replacements)
        return result_df

    def aggregate(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Aggregate data."""
        aggregations = config.get("aggregations", {})
        return df.agg(aggregations)

    def group_by(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Group data by columns and aggregate."""
        group_columns = config.get("columns", [])
        aggregations = config.get("aggregations", {})

        return df.groupby(group_columns).agg(aggregations).reset_index()

    def sort(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Sort data by columns."""
        columns = config.get("columns", [])
        ascending = config.get("ascending", True)

        return df.sort_values(by=columns, ascending=ascending)

    def deduplicate(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Remove duplicate rows."""
        subset = config.get("subset", None)
        keep = config.get("keep", "first")  # first, last, False

        return df.drop_duplicates(subset=subset, keep=keep)

    def regex_extract(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Extract data using regular expressions."""
        column = config.get("column")
        pattern = config.get("pattern")
        new_column = config.get("new_column", f"{column}_extracted")

        result_df = df.copy()
        result_df[new_column] = result_df[column].str.extract(pattern, expand=False)
        return result_df

    def string_operation(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Perform string operations."""
        column = config.get("column")
        operation = config.get("operation")  # upper, lower, strip, etc.

        result_df = df.copy()

        if operation == "upper":
            result_df[column] = result_df[column].str.upper()
        elif operation == "lower":
            result_df[column] = result_df[column].str.lower()
        elif operation == "strip":
            result_df[column] = result_df[column].str.strip()
        elif operation == "title":
            result_df[column] = result_df[column].str.title()
        elif operation == "capitalize":
            result_df[column] = result_df[column].str.capitalize()
        elif operation == "replace":
            old = config.get("old", "")
            new = config.get("new", "")
            result_df[column] = result_df[column].str.replace(old, new)
        elif operation == "split":
            separator = config.get("separator", ",")
            new_columns = config.get("new_columns", [])
            split_data = result_df[column].str.split(separator, expand=True)
            for idx, col_name in enumerate(new_columns):
                if idx < len(split_data.columns):
                    result_df[col_name] = split_data[idx]

        return result_df

    def date_operation(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Perform date/time operations."""
        column = config.get("column")
        operation = config.get("operation")

        result_df = df.copy()
        result_df[column] = pd.to_datetime(result_df[column], errors="coerce")

        if operation == "extract_year":
            new_column = config.get("new_column", f"{column}_year")
            result_df[new_column] = result_df[column].dt.year
        elif operation == "extract_month":
            new_column = config.get("new_column", f"{column}_month")
            result_df[new_column] = result_df[column].dt.month
        elif operation == "extract_day":
            new_column = config.get("new_column", f"{column}_day")
            result_df[new_column] = result_df[column].dt.day
        elif operation == "extract_weekday":
            new_column = config.get("new_column", f"{column}_weekday")
            result_df[new_column] = result_df[column].dt.weekday
        elif operation == "format":
            format_string = config.get("format", "%Y-%m-%d")
            result_df[column] = result_df[column].dt.strftime(format_string)
        elif operation == "add_days":
            days = config.get("days", 0)
            result_df[column] = result_df[column] + pd.Timedelta(days=days)
        elif operation == "diff":
            other_column = config.get("other_column")
            new_column = config.get("new_column", f"{column}_diff")
            result_df[new_column] = (result_df[column] - result_df[other_column]).dt.days

        return result_df

    def math_operation(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Perform mathematical operations."""
        operation = config.get("operation")
        column = config.get("column")
        new_column = config.get("new_column", f"{column}_result")

        result_df = df.copy()

        if operation == "add":
            value = config.get("value", 0)
            result_df[new_column] = result_df[column] + value
        elif operation == "subtract":
            value = config.get("value", 0)
            result_df[new_column] = result_df[column] - value
        elif operation == "multiply":
            value = config.get("value", 1)
            result_df[new_column] = result_df[column] * value
        elif operation == "divide":
            value = config.get("value", 1)
            result_df[new_column] = result_df[column] / value
        elif operation == "power":
            power = config.get("power", 2)
            result_df[new_column] = result_df[column] ** power
        elif operation == "round":
            decimals = config.get("decimals", 0)
            result_df[new_column] = result_df[column].round(decimals)
        elif operation == "abs":
            result_df[new_column] = result_df[column].abs()
        elif operation == "log":
            result_df[new_column] = np.log(result_df[column])
        elif operation == "sqrt":
            result_df[new_column] = np.sqrt(result_df[column])

        return result_df
