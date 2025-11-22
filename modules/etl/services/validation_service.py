"""Data validation and quality service."""
from typing import Any, Dict, List, Tuple
import pandas as pd
import numpy as np
from modules.etl.core.constants import ValidationRule
from shared.utils.logger import get_logger
import re

logger = get_logger(__name__)


class ValidationService:
    """Service for data validation and quality checks."""

    def __init__(self):
        self.logger = logger

    def validate_data(
        self, df: pd.DataFrame, validation_rules: List[Dict[str, Any]]
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Validate data against rules.

        Returns:
            Tuple of (validated DataFrame, quality report)
        """
        quality_report = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "validations_passed": 0,
            "validations_failed": 0,
            "errors": [],
            "warnings": [],
            "statistics": {},
        }

        result_df = df.copy()
        result_df["_validation_errors"] = ""

        for rule in validation_rules:
            try:
                rule_type = rule.get("type")
                column = rule.get("column")
                config = rule.get("config", {})

                is_valid, error_msg = self._apply_validation_rule(result_df, rule_type, column, config)

                if is_valid:
                    quality_report["validations_passed"] += 1
                else:
                    quality_report["validations_failed"] += 1
                    quality_report["errors"].append(
                        {"rule": rule_type, "column": column, "message": error_msg}
                    )

            except Exception as e:
                self.logger.error(f"Error applying validation rule: {e}")
                quality_report["errors"].append({"rule": rule.get("type"), "error": str(e)})

        # Add data statistics
        quality_report["statistics"] = self._calculate_statistics(df)

        return result_df, quality_report

    def _apply_validation_rule(
        self, df: pd.DataFrame, rule_type: str, column: str, config: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Apply a single validation rule."""

        if rule_type == ValidationRule.NOT_NULL:
            null_count = df[column].isna().sum()
            if null_count > 0:
                return False, f"Column '{column}' has {null_count} null values"
            return True, ""

        elif rule_type == ValidationRule.UNIQUE:
            duplicate_count = df[column].duplicated().sum()
            if duplicate_count > 0:
                return False, f"Column '{column}' has {duplicate_count} duplicate values"
            return True, ""

        elif rule_type == ValidationRule.RANGE:
            min_val = config.get("min")
            max_val = config.get("max")
            out_of_range = df[(df[column] < min_val) | (df[column] > max_val)]
            if len(out_of_range) > 0:
                return (
                    False,
                    f"Column '{column}' has {len(out_of_range)} values out of range [{min_val}, {max_val}]",
                )
            return True, ""

        elif rule_type == ValidationRule.REGEX:
            pattern = config.get("pattern")
            invalid_count = (~df[column].astype(str).str.match(pattern, na=False)).sum()
            if invalid_count > 0:
                return False, f"Column '{column}' has {invalid_count} values not matching pattern"
            return True, ""

        elif rule_type == ValidationRule.TYPE_CHECK:
            expected_type = config.get("type")
            try:
                if expected_type == "int":
                    pd.to_numeric(df[column], errors="raise")
                elif expected_type == "float":
                    pd.to_numeric(df[column], errors="raise")
                elif expected_type == "datetime":
                    pd.to_datetime(df[column], errors="raise")
                return True, ""
            except Exception:
                return False, f"Column '{column}' has values that cannot be converted to {expected_type}"

        elif rule_type == ValidationRule.MIN_LENGTH:
            min_length = config.get("value", 0)
            invalid_count = (df[column].astype(str).str.len() < min_length).sum()
            if invalid_count > 0:
                return (
                    False,
                    f"Column '{column}' has {invalid_count} values shorter than {min_length}",
                )
            return True, ""

        elif rule_type == ValidationRule.MAX_LENGTH:
            max_length = config.get("value", 0)
            invalid_count = (df[column].astype(str).str.len() > max_length).sum()
            if invalid_count > 0:
                return (
                    False,
                    f"Column '{column}' has {invalid_count} values longer than {max_length}",
                )
            return True, ""

        elif rule_type == ValidationRule.IN_LIST:
            allowed_values = config.get("values", [])
            invalid_count = (~df[column].isin(allowed_values)).sum()
            if invalid_count > 0:
                return (
                    False,
                    f"Column '{column}' has {invalid_count} values not in allowed list",
                )
            return True, ""

        return True, ""

    def _calculate_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate data quality statistics."""
        stats = {
            "null_counts": df.isnull().sum().to_dict(),
            "null_percentages": (df.isnull().sum() / len(df) * 100).to_dict(),
            "unique_counts": {col: df[col].nunique() for col in df.columns},
            "duplicate_rows": df.duplicated().sum(),
        }

        # Add numeric column statistics
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            stats["numeric_stats"] = df[numeric_cols].describe().to_dict()

        return stats

    def check_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform comprehensive data quality check."""
        quality_report = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
            "null_analysis": {},
            "duplicate_analysis": {},
            "data_type_analysis": {},
            "outlier_analysis": {},
        }

        # Null analysis
        null_counts = df.isnull().sum()
        quality_report["null_analysis"] = {
            "columns_with_nulls": null_counts[null_counts > 0].to_dict(),
            "total_null_cells": df.isnull().sum().sum(),
            "null_percentage": (df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100),
        }

        # Duplicate analysis
        quality_report["duplicate_analysis"] = {
            "duplicate_rows": df.duplicated().sum(),
            "duplicate_percentage": (df.duplicated().sum() / len(df) * 100) if len(df) > 0 else 0,
        }

        # Data type analysis
        quality_report["data_type_analysis"] = df.dtypes.astype(str).to_dict()

        # Outlier analysis for numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        outliers = {}
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outlier_count = ((df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))).sum()
            if outlier_count > 0:
                outliers[col] = int(outlier_count)

        quality_report["outlier_analysis"] = outliers

        return quality_report

    def profile_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create detailed data profile."""
        profile = {
            "shape": {"rows": len(df), "columns": len(df.columns)},
            "columns": {},
        }

        for col in df.columns:
            col_profile = {
                "dtype": str(df[col].dtype),
                "null_count": int(df[col].isnull().sum()),
                "null_percentage": float(df[col].isnull().sum() / len(df) * 100) if len(df) > 0 else 0,
                "unique_count": int(df[col].nunique()),
                "unique_percentage": float(df[col].nunique() / len(df) * 100) if len(df) > 0 else 0,
            }

            # Add numeric statistics
            if df[col].dtype in [np.int64, np.float64]:
                col_profile.update(
                    {
                        "min": float(df[col].min()),
                        "max": float(df[col].max()),
                        "mean": float(df[col].mean()),
                        "median": float(df[col].median()),
                        "std": float(df[col].std()),
                    }
                )

            # Add top values
            if df[col].dtype == object:
                top_values = df[col].value_counts().head(5).to_dict()
                col_profile["top_values"] = {str(k): int(v) for k, v in top_values.items()}

            profile["columns"][col] = col_profile

        return profile
