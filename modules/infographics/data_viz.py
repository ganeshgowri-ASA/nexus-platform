"""
Infographics Designer - Data Visualization Module

This module handles data import from CSV/Excel, auto-generates charts,
and creates data tables for visualization in infographics.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Union
from enum import Enum
import csv
import json
from io import StringIO

from .charts import ChartFactory, ChartElement, ChartType, DataSeries
from .elements import BaseElement, ElementFactory, Position, Style, TextStyle, TextAlign


class DataSourceType(Enum):
    """Types of data sources."""
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    API = "api"
    DATABASE = "database"
    MANUAL = "manual"


class DataType(Enum):
    """Data column types."""
    STRING = "string"
    NUMBER = "number"
    DATE = "date"
    BOOLEAN = "boolean"
    CATEGORY = "category"


@dataclass
class DataColumn:
    """Represents a data column."""
    name: str
    data_type: DataType
    values: List[Any] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'data_type': self.data_type.value,
            'values': self.values,
            'metadata': self.metadata
        }


@dataclass
class DataTable:
    """Represents a data table."""
    name: str
    columns: List[DataColumn] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'columns': [col.to_dict() for col in self.columns],
            'metadata': self.metadata
        }

    def add_column(self, column: DataColumn) -> None:
        """Add column to table."""
        self.columns.append(column)

    def get_column(self, name: str) -> Optional[DataColumn]:
        """Get column by name."""
        for col in self.columns:
            if col.name == name:
                return col
        return None

    def get_row_count(self) -> int:
        """Get number of rows."""
        if not self.columns:
            return 0
        return len(self.columns[0].values)

    def get_column_count(self) -> int:
        """Get number of columns."""
        return len(self.columns)

    def get_row(self, index: int) -> Dict[str, Any]:
        """Get row data by index."""
        if index < 0 or index >= self.get_row_count():
            return {}
        return {
            col.name: col.values[index]
            for col in self.columns
        }

    def get_column_values(self, column_name: str) -> List[Any]:
        """Get all values for a column."""
        col = self.get_column(column_name)
        return col.values if col else []


class DataImporter:
    """Imports data from various sources."""

    @staticmethod
    def import_csv(data: str, has_header: bool = True,
                  delimiter: str = ',') -> DataTable:
        """Import data from CSV string."""
        reader = csv.reader(StringIO(data), delimiter=delimiter)
        rows = list(reader)

        if not rows:
            return DataTable(name="Empty Table")

        # Get headers
        if has_header:
            headers = rows[0]
            data_rows = rows[1:]
        else:
            headers = [f"Column{i+1}" for i in range(len(rows[0]))]
            data_rows = rows

        # Create table
        table = DataTable(name="Imported Data")

        # Create columns
        for i, header in enumerate(headers):
            values = [row[i] if i < len(row) else None for row in data_rows]

            # Infer data type
            data_type = DataImporter._infer_data_type(values)

            # Convert values based on type
            converted_values = DataImporter._convert_values(values, data_type)

            column = DataColumn(
                name=header,
                data_type=data_type,
                values=converted_values
            )
            table.add_column(column)

        return table

    @staticmethod
    def import_json(data: str) -> DataTable:
        """Import data from JSON string."""
        try:
            parsed = json.loads(data)

            if isinstance(parsed, list):
                # List of objects
                if not parsed:
                    return DataTable(name="Empty Table")

                # Get all keys from first object
                if isinstance(parsed[0], dict):
                    keys = list(parsed[0].keys())
                    table = DataTable(name="Imported Data")

                    for key in keys:
                        values = [item.get(key) for item in parsed]
                        data_type = DataImporter._infer_data_type(values)
                        converted_values = DataImporter._convert_values(values, data_type)

                        column = DataColumn(
                            name=key,
                            data_type=data_type,
                            values=converted_values
                        )
                        table.add_column(column)

                    return table

            elif isinstance(parsed, dict):
                # Single object or key-value pairs
                table = DataTable(name="Imported Data")

                for key, value in parsed.items():
                    if isinstance(value, list):
                        data_type = DataImporter._infer_data_type(value)
                        converted_values = DataImporter._convert_values(value, data_type)
                    else:
                        data_type = DataType.STRING
                        converted_values = [value]

                    column = DataColumn(
                        name=key,
                        data_type=data_type,
                        values=converted_values
                    )
                    table.add_column(column)

                return table

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            return DataTable(name="Error")

        return DataTable(name="Empty Table")

    @staticmethod
    def _infer_data_type(values: List[Any]) -> DataType:
        """Infer data type from values."""
        if not values:
            return DataType.STRING

        # Try to detect numbers
        try:
            for val in values:
                if val is not None and val != '':
                    float(str(val))
            return DataType.NUMBER
        except (ValueError, TypeError):
            pass

        # Try to detect booleans
        bool_values = {'true', 'false', 'yes', 'no', '1', '0'}
        if all(str(val).lower() in bool_values for val in values if val):
            return DataType.BOOLEAN

        return DataType.STRING

    @staticmethod
    def _convert_values(values: List[Any], data_type: DataType) -> List[Any]:
        """Convert values to appropriate type."""
        converted = []

        for val in values:
            if val is None or val == '':
                converted.append(None)
                continue

            try:
                if data_type == DataType.NUMBER:
                    converted.append(float(val))
                elif data_type == DataType.BOOLEAN:
                    str_val = str(val).lower()
                    converted.append(str_val in {'true', 'yes', '1'})
                else:
                    converted.append(str(val))
            except (ValueError, TypeError):
                converted.append(None)

        return converted

    @staticmethod
    def import_from_dict(data: Dict[str, List[Any]],
                        table_name: str = "Data") -> DataTable:
        """Import data from dictionary of lists."""
        table = DataTable(name=table_name)

        for column_name, values in data.items():
            data_type = DataImporter._infer_data_type(values)
            converted_values = DataImporter._convert_values(values, data_type)

            column = DataColumn(
                name=column_name,
                data_type=data_type,
                values=converted_values
            )
            table.add_column(column)

        return table


class ChartGenerator:
    """Automatically generates charts from data."""

    @staticmethod
    def auto_generate_chart(table: DataTable,
                          chart_type: Optional[ChartType] = None) -> Optional[ChartElement]:
        """Automatically generate appropriate chart from data."""
        if table.get_column_count() < 1:
            return None

        # If chart type not specified, infer it
        if chart_type is None:
            chart_type = ChartGenerator._infer_chart_type(table)

        if chart_type == ChartType.BAR:
            return ChartGenerator.generate_bar_chart(table)
        elif chart_type == ChartType.PIE:
            return ChartGenerator.generate_pie_chart(table)
        elif chart_type == ChartType.LINE:
            return ChartGenerator.generate_line_chart(table)
        elif chart_type == ChartType.SCATTER:
            return ChartGenerator.generate_scatter_chart(table)

        return None

    @staticmethod
    def _infer_chart_type(table: DataTable) -> ChartType:
        """Infer appropriate chart type from data."""
        col_count = table.get_column_count()
        row_count = table.get_row_count()

        if col_count == 1:
            # Single column - use bar chart
            return ChartType.BAR
        elif col_count == 2:
            # Two columns - check types
            first_col = table.columns[0]
            second_col = table.columns[1]

            if first_col.data_type == DataType.STRING and second_col.data_type == DataType.NUMBER:
                # Category + Value = Bar or Pie
                if row_count <= 7:
                    return ChartType.PIE
                return ChartType.BAR
            elif first_col.data_type == DataType.NUMBER and second_col.data_type == DataType.NUMBER:
                # Number + Number = Scatter or Line
                return ChartType.SCATTER

        # Multiple columns with numbers - use line chart
        return ChartType.LINE

    @staticmethod
    def generate_bar_chart(table: DataTable,
                          category_column: Optional[str] = None,
                          value_column: Optional[str] = None) -> ChartElement:
        """Generate bar chart from table."""
        # Find category and value columns
        if category_column is None:
            # Find first string column
            for col in table.columns:
                if col.data_type in [DataType.STRING, DataType.CATEGORY]:
                    category_column = col.name
                    break

        if value_column is None:
            # Find first number column
            for col in table.columns:
                if col.data_type == DataType.NUMBER:
                    value_column = col.name
                    break

        if not category_column or not value_column:
            # Use first two columns
            if table.get_column_count() >= 2:
                category_column = table.columns[0].name
                value_column = table.columns[1].name
            else:
                return ChartFactory.create_bar_chart([], [])

        categories = [str(v) for v in table.get_column_values(category_column)]
        values = table.get_column_values(value_column)

        return ChartFactory.create_bar_chart(
            categories=categories,
            data=values,
            title=f"{value_column} by {category_column}"
        )

    @staticmethod
    def generate_pie_chart(table: DataTable,
                          label_column: Optional[str] = None,
                          value_column: Optional[str] = None) -> ChartElement:
        """Generate pie chart from table."""
        if label_column is None:
            for col in table.columns:
                if col.data_type in [DataType.STRING, DataType.CATEGORY]:
                    label_column = col.name
                    break

        if value_column is None:
            for col in table.columns:
                if col.data_type == DataType.NUMBER:
                    value_column = col.name
                    break

        if not label_column or not value_column:
            if table.get_column_count() >= 2:
                label_column = table.columns[0].name
                value_column = table.columns[1].name
            else:
                return ChartFactory.create_pie_chart([], [])

        labels = [str(v) for v in table.get_column_values(label_column)]
        values = table.get_column_values(value_column)

        return ChartFactory.create_pie_chart(
            labels=labels,
            data=values,
            title=f"{value_column} Distribution"
        )

    @staticmethod
    def generate_line_chart(table: DataTable,
                          x_column: Optional[str] = None,
                          y_columns: Optional[List[str]] = None) -> ChartElement:
        """Generate line chart from table."""
        if x_column is None:
            x_column = table.columns[0].name

        if y_columns is None:
            y_columns = [
                col.name for col in table.columns[1:]
                if col.data_type == DataType.NUMBER
            ]

        if not y_columns:
            return ChartFactory.create_line_chart([], [])

        categories = [str(v) for v in table.get_column_values(x_column)]

        # Create chart with first series
        values = table.get_column_values(y_columns[0])
        chart = ChartFactory.create_line_chart(
            categories=categories,
            data=values,
            title=f"{', '.join(y_columns)} over {x_column}"
        )

        # Add additional series
        for col_name in y_columns[1:]:
            values = table.get_column_values(col_name)
            series = DataSeries(name=col_name, data=values)
            chart.add_series(series)

        return chart

    @staticmethod
    def generate_scatter_chart(table: DataTable,
                             x_column: Optional[str] = None,
                             y_column: Optional[str] = None) -> ChartElement:
        """Generate scatter chart from table."""
        number_columns = [
            col.name for col in table.columns
            if col.data_type == DataType.NUMBER
        ]

        if len(number_columns) < 2:
            return ChartFactory.create_scatter_chart([], [])

        if x_column is None:
            x_column = number_columns[0]
        if y_column is None:
            y_column = number_columns[1]

        x_values = table.get_column_values(x_column)
        y_values = table.get_column_values(y_column)

        return ChartFactory.create_scatter_chart(
            x_data=x_values,
            y_data=y_values,
            title=f"{y_column} vs {x_column}"
        )


class DataTableElement(BaseElement):
    """Visual data table element."""

    def __init__(self, table: DataTable, **kwargs):
        """Initialize data table element."""
        super().__init__(**kwargs)
        self.table = table
        self.show_header = True
        self.show_row_numbers = False
        self.alternate_row_colors = True
        self.cell_padding = 8.0
        self.border_width = 1.0
        self.header_bg_color = "#F0F0F0"
        self.row_bg_color = "#FFFFFF"
        self.alt_row_bg_color = "#F9F9F9"
        self.text_color = "#333333"
        self.border_color = "#CCCCCC"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            'table': self.table.to_dict(),
            'show_header': self.show_header,
            'show_row_numbers': self.show_row_numbers,
            'alternate_row_colors': self.alternate_row_colors,
            'cell_padding': self.cell_padding,
            'border_width': self.border_width,
            'header_bg_color': self.header_bg_color,
            'row_bg_color': self.row_bg_color,
            'alt_row_bg_color': self.alt_row_bg_color,
            'text_color': self.text_color,
            'border_color': self.border_color
        })
        return data


class DataAnalyzer:
    """Analyzes data and provides insights."""

    @staticmethod
    def get_summary_statistics(column: DataColumn) -> Dict[str, Any]:
        """Get summary statistics for a column."""
        if column.data_type != DataType.NUMBER:
            return {
                'count': len(column.values),
                'unique': len(set(column.values))
            }

        values = [v for v in column.values if v is not None]
        if not values:
            return {}

        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'mean': sum(values) / len(values),
            'sum': sum(values)
        }

    @staticmethod
    def detect_trends(values: List[float]) -> str:
        """Detect trend in numeric values."""
        if len(values) < 2:
            return "insufficient_data"

        # Simple trend detection
        increases = sum(1 for i in range(1, len(values)) if values[i] > values[i-1])
        decreases = sum(1 for i in range(1, len(values)) if values[i] < values[i-1])

        if increases > decreases * 1.5:
            return "increasing"
        elif decreases > increases * 1.5:
            return "decreasing"
        return "stable"

    @staticmethod
    def find_outliers(values: List[float], threshold: float = 2.0) -> List[int]:
        """Find outlier indices using standard deviation."""
        if len(values) < 3:
            return []

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5

        outliers = []
        for i, val in enumerate(values):
            if abs(val - mean) > threshold * std_dev:
                outliers.append(i)

        return outliers


__all__ = [
    'DataSourceType', 'DataType',
    'DataColumn', 'DataTable',
    'DataImporter', 'ChartGenerator', 'DataTableElement', 'DataAnalyzer'
]
