"""Pivot table functionality for data analysis."""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np


class AggregationFunction(Enum):
    """Aggregation functions for pivot tables."""
    SUM = "sum"
    COUNT = "count"
    AVERAGE = "mean"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    STD = "std"
    VAR = "var"


@dataclass
class PivotConfig:
    """Pivot table configuration."""

    rows: List[str]
    columns: List[str]
    values: List[str]
    aggfunc: Dict[str, str]  # column -> aggregation function
    fill_value: Optional[Any] = None
    margins: bool = False
    margins_name: str = "Total"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'rows': self.rows,
            'columns': self.columns,
            'values': self.values,
            'aggfunc': self.aggfunc,
            'fill_value': self.fill_value,
            'margins': self.margins,
            'margins_name': self.margins_name
        }


class PivotTable:
    """Create and manage pivot tables."""

    def __init__(self, data: pd.DataFrame):
        """
        Initialize pivot table.

        Args:
            data: Source data
        """
        self.data = data
        self.pivot_result: Optional[pd.DataFrame] = None

    def create(self, config: PivotConfig) -> pd.DataFrame:
        """
        Create pivot table.

        Args:
            config: Pivot configuration

        Returns:
            Pivot table DataFrame
        """
        # Map aggregation function names to pandas functions
        aggfunc_map = {col: config.aggfunc.get(col, 'sum') for col in config.values}

        try:
            self.pivot_result = pd.pivot_table(
                self.data,
                values=config.values,
                index=config.rows,
                columns=config.columns,
                aggfunc=aggfunc_map,
                fill_value=config.fill_value,
                margins=config.margins,
                margins_name=config.margins_name
            )
            return self.pivot_result
        except Exception as e:
            raise ValueError(f"Failed to create pivot table: {str(e)}")

    def filter(self, filters: Dict[str, Any]) -> pd.DataFrame:
        """
        Apply filters to pivot table.

        Args:
            filters: Dictionary of column -> filter value

        Returns:
            Filtered DataFrame
        """
        if self.pivot_result is None:
            raise ValueError("No pivot table created yet")

        filtered = self.pivot_result.copy()

        for column, value in filters.items():
            if column in filtered.columns:
                filtered = filtered[filtered[column] == value]

        return filtered

    def drill_down(self, row_values: Dict[str, Any], col_values: Dict[str, Any]) -> pd.DataFrame:
        """
        Drill down to source data.

        Args:
            row_values: Row dimension values
            col_values: Column dimension values

        Returns:
            Source data matching the criteria
        """
        filtered = self.data.copy()

        for column, value in {**row_values, **col_values}.items():
            filtered = filtered[filtered[column] == value]

        return filtered

    def export_to_excel(self, filename: str) -> None:
        """
        Export pivot table to Excel.

        Args:
            filename: Output filename
        """
        if self.pivot_result is None:
            raise ValueError("No pivot table created yet")

        self.pivot_result.to_excel(filename)


class PivotTableBuilder:
    """Builder for creating pivot table configurations."""

    def __init__(self):
        """Initialize builder."""
        self.config = {
            'rows': [],
            'columns': [],
            'values': [],
            'aggfunc': {}
        }

    def add_row_field(self, field: str) -> 'PivotTableBuilder':
        """Add field to rows."""
        self.config['rows'].append(field)
        return self

    def add_column_field(self, field: str) -> 'PivotTableBuilder':
        """Add field to columns."""
        self.config['columns'].append(field)
        return self

    def add_value_field(self, field: str, aggregation: str = 'sum') -> 'PivotTableBuilder':
        """Add field to values with aggregation."""
        self.config['values'].append(field)
        self.config['aggfunc'][field] = aggregation
        return self

    def with_margins(self, enabled: bool = True, name: str = "Total") -> 'PivotTableBuilder':
        """Enable/disable margins (totals)."""
        self.config['margins'] = enabled
        self.config['margins_name'] = name
        return self

    def with_fill_value(self, value: Any) -> 'PivotTableBuilder':
        """Set fill value for missing data."""
        self.config['fill_value'] = value
        return self

    def build(self) -> PivotConfig:
        """Build pivot configuration."""
        return PivotConfig(**self.config)
