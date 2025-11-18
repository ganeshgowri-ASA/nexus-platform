"""
NEXUS Dashboard Builder - Widgets Module
Comprehensive widget library: KPIs, charts, tables, filters, and custom widgets
"""

import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid


class WidgetType(Enum):
    """Available widget types"""
    KPI = "kpi"
    CHART = "chart"
    TABLE = "table"
    FILTER = "filter"
    TEXT = "text"
    IMAGE = "image"
    IFRAME = "iframe"
    MAP = "map"
    GAUGE = "gauge"
    SPARKLINE = "sparkline"
    PROGRESS = "progress"
    STAT = "stat"
    HEATMAP = "heatmap"
    CUSTOM = "custom"


class KPITrend(Enum):
    """KPI trend indicators"""
    UP = "up"
    DOWN = "down"
    FLAT = "flat"
    UNKNOWN = "unknown"


@dataclass
class WidgetStyle:
    """Widget styling configuration"""
    background_color: str = "#ffffff"
    border_color: str = "#e0e0e0"
    border_width: int = 1
    border_radius: int = 4
    padding: int = 16
    shadow: bool = True
    font_family: str = "Arial, sans-serif"
    title_size: int = 16
    title_color: str = "#333333"
    title_bold: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            'background_color': self.background_color,
            'border_color': self.border_color,
            'border_width': self.border_width,
            'border_radius': self.border_radius,
            'padding': self.padding,
            'shadow': self.shadow,
            'font_family': self.font_family,
            'title_size': self.title_size,
            'title_color': self.title_color,
            'title_bold': self.title_bold
        }


class Widget:
    """Base widget class"""

    def __init__(self, widget_id: Optional[str] = None, title: str = ""):
        self.widget_id = widget_id or str(uuid.uuid4())
        self.title = title
        self.widget_type = WidgetType.CUSTOM
        self.style = WidgetStyle()
        self.data: Any = None
        self.last_updated: Optional[datetime] = None
        self.loading = False
        self.error: Optional[str] = None

    def update_data(self, data: Any):
        """Update widget data"""
        self.data = data
        self.last_updated = datetime.now()
        self.loading = False
        self.error = None

    def set_error(self, error: str):
        """Set widget error state"""
        self.error = error
        self.loading = False

    def render(self) -> Any:
        """Render the widget (to be implemented by subclasses)"""
        raise NotImplementedError


class KPIWidget(Widget):
    """KPI (Key Performance Indicator) widget"""

    def __init__(self, widget_id: Optional[str] = None, title: str = "KPI"):
        super().__init__(widget_id, title)
        self.widget_type = WidgetType.KPI
        self.value: float = 0.0
        self.prefix: str = ""
        self.suffix: str = ""
        self.previous_value: Optional[float] = None
        self.trend: KPITrend = KPITrend.UNKNOWN
        self.trend_percentage: float = 0.0
        self.target: Optional[float] = None
        self.format_string: str = "{:,.2f}"
        self.value_color: str = "#1976d2"
        self.show_sparkline: bool = False
        self.sparkline_data: List[float] = []

    def calculate_trend(self):
        """Calculate trend from previous value"""
        if self.previous_value is None or self.previous_value == 0:
            self.trend = KPITrend.UNKNOWN
            self.trend_percentage = 0.0
            return

        change = self.value - self.previous_value
        self.trend_percentage = (change / self.previous_value) * 100

        if change > 0:
            self.trend = KPITrend.UP
        elif change < 0:
            self.trend = KPITrend.DOWN
        else:
            self.trend = KPITrend.FLAT

    def set_value(self, value: float, previous_value: Optional[float] = None):
        """Set KPI value and calculate trend"""
        self.value = value
        self.previous_value = previous_value
        self.calculate_trend()
        self.last_updated = datetime.now()

    def render(self) -> Dict[str, Any]:
        """Render KPI widget"""
        formatted_value = self.format_string.format(self.value)

        return {
            'type': 'kpi',
            'title': self.title,
            'value': f"{self.prefix}{formatted_value}{self.suffix}",
            'trend': self.trend.value,
            'trend_percentage': self.trend_percentage,
            'value_color': self.value_color,
            'target': self.target,
            'sparkline_data': self.sparkline_data if self.show_sparkline else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class ChartWidget(Widget):
    """Chart widget supporting multiple chart types"""

    def __init__(self, widget_id: Optional[str] = None, title: str = "Chart"):
        super().__init__(widget_id, title)
        self.widget_type = WidgetType.CHART
        self.chart_type: str = "line"  # line, bar, pie, scatter, etc.
        self.chart_config: Dict[str, Any] = {}
        self.x_axis: str = ""
        self.y_axis: str = ""
        self.color_by: Optional[str] = None
        self.size_by: Optional[str] = None
        self.show_legend: bool = True
        self.legend_position: str = "right"
        self.show_toolbar: bool = True

    def set_data(self, df: pd.DataFrame, x_axis: str, y_axis: str):
        """Set chart data"""
        self.data = df
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.last_updated = datetime.now()

    def render(self) -> go.Figure:
        """Render chart widget"""
        if self.data is None or self.data.empty:
            return go.Figure()

        if self.chart_type == "line":
            fig = go.Figure(data=go.Scatter(
                x=self.data[self.x_axis],
                y=self.data[self.y_axis],
                mode='lines+markers'
            ))
        elif self.chart_type == "bar":
            fig = go.Figure(data=go.Bar(
                x=self.data[self.x_axis],
                y=self.data[self.y_axis]
            ))
        elif self.chart_type == "pie":
            fig = go.Figure(data=go.Pie(
                labels=self.data[self.x_axis],
                values=self.data[self.y_axis]
            ))
        else:
            fig = go.Figure()

        fig.update_layout(
            title=self.title,
            showlegend=self.show_legend,
            legend=dict(orientation="h" if self.legend_position == "bottom" else "v")
        )

        return fig


class TableWidget(Widget):
    """Interactive table widget"""

    def __init__(self, widget_id: Optional[str] = None, title: str = "Table"):
        super().__init__(widget_id, title)
        self.widget_type = WidgetType.TABLE
        self.columns: List[str] = []
        self.sortable: bool = True
        self.filterable: bool = True
        self.paginated: bool = True
        self.page_size: int = 20
        self.current_page: int = 1
        self.column_config: Dict[str, Dict[str, Any]] = {}
        self.row_selection: bool = False
        self.selected_rows: List[int] = []

    def set_data(self, df: pd.DataFrame):
        """Set table data"""
        self.data = df
        self.columns = list(df.columns)
        self.last_updated = datetime.now()

    def render(self) -> Dict[str, Any]:
        """Render table widget"""
        if self.data is None or self.data.empty:
            return {'type': 'table', 'data': [], 'columns': []}

        # Apply pagination
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        paginated_data = self.data.iloc[start_idx:end_idx]

        return {
            'type': 'table',
            'title': self.title,
            'data': paginated_data.to_dict('records'),
            'columns': self.columns,
            'total_rows': len(self.data),
            'current_page': self.current_page,
            'page_size': self.page_size,
            'total_pages': (len(self.data) + self.page_size - 1) // self.page_size
        }


class FilterWidget(Widget):
    """Filter widget for dashboard-wide filtering"""

    def __init__(self, widget_id: Optional[str] = None, title: str = "Filter"):
        super().__init__(widget_id, title)
        self.widget_type = WidgetType.FILTER
        self.filter_type: str = "dropdown"  # dropdown, multiselect, date, range, text
        self.options: List[Any] = []
        self.selected_value: Any = None
        self.selected_values: List[Any] = []
        self.placeholder: str = "Select..."
        self.allow_clear: bool = True

    def set_options(self, options: List[Any]):
        """Set filter options"""
        self.options = options

    def set_value(self, value: Any):
        """Set selected value"""
        self.selected_value = value
        self.last_updated = datetime.now()

    def render(self) -> Dict[str, Any]:
        """Render filter widget"""
        return {
            'type': 'filter',
            'title': self.title,
            'filter_type': self.filter_type,
            'options': self.options,
            'selected_value': self.selected_value,
            'placeholder': self.placeholder
        }


class GaugeWidget(Widget):
    """Gauge widget for displaying metrics"""

    def __init__(self, widget_id: Optional[str] = None, title: str = "Gauge"):
        super().__init__(widget_id, title)
        self.widget_type = WidgetType.GAUGE
        self.value: float = 0.0
        self.min_value: float = 0.0
        self.max_value: float = 100.0
        self.threshold_low: float = 30.0
        self.threshold_medium: float = 70.0
        self.units: str = ""
        self.color_low: str = "#d32f2f"
        self.color_medium: str = "#ffa726"
        self.color_high: str = "#388e3c"

    def set_value(self, value: float):
        """Set gauge value"""
        self.value = max(self.min_value, min(value, self.max_value))
        self.last_updated = datetime.now()

    def get_color(self) -> str:
        """Get color based on value"""
        percentage = (self.value - self.min_value) / (self.max_value - self.min_value) * 100

        if percentage < self.threshold_low:
            return self.color_low
        elif percentage < self.threshold_medium:
            return self.color_medium
        else:
            return self.color_high

    def render(self) -> go.Figure:
        """Render gauge widget"""
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=self.value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': self.title},
            number={'suffix': f" {self.units}"},
            gauge={
                'axis': {'range': [self.min_value, self.max_value]},
                'bar': {'color': self.get_color()},
                'steps': [
                    {'range': [self.min_value, self.threshold_low], 'color': "lightgray"},
                    {'range': [self.threshold_low, self.threshold_medium], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': self.threshold_medium
                }
            }
        ))

        return fig


class TextWidget(Widget):
    """Text/markdown widget"""

    def __init__(self, widget_id: Optional[str] = None, title: str = ""):
        super().__init__(widget_id, title)
        self.widget_type = WidgetType.TEXT
        self.content: str = ""
        self.markdown_enabled: bool = True
        self.text_align: str = "left"
        self.font_size: int = 14

    def set_content(self, content: str):
        """Set text content"""
        self.content = content
        self.last_updated = datetime.now()

    def render(self) -> Dict[str, Any]:
        """Render text widget"""
        return {
            'type': 'text',
            'title': self.title,
            'content': self.content,
            'markdown_enabled': self.markdown_enabled,
            'text_align': self.text_align,
            'font_size': self.font_size
        }


class ProgressWidget(Widget):
    """Progress bar widget"""

    def __init__(self, widget_id: Optional[str] = None, title: str = "Progress"):
        super().__init__(widget_id, title)
        self.widget_type = WidgetType.PROGRESS
        self.current: float = 0.0
        self.total: float = 100.0
        self.percentage: float = 0.0
        self.show_percentage: bool = True
        self.show_value: bool = True
        self.color: str = "#1976d2"

    def set_progress(self, current: float, total: float):
        """Set progress values"""
        self.current = current
        self.total = total
        self.percentage = (current / total * 100) if total > 0 else 0
        self.last_updated = datetime.now()

    def render(self) -> Dict[str, Any]:
        """Render progress widget"""
        return {
            'type': 'progress',
            'title': self.title,
            'current': self.current,
            'total': self.total,
            'percentage': self.percentage,
            'show_percentage': self.show_percentage,
            'show_value': self.show_value,
            'color': self.color
        }


class StatWidget(Widget):
    """Simple stat display widget"""

    def __init__(self, widget_id: Optional[str] = None, title: str = ""):
        super().__init__(widget_id, title)
        self.widget_type = WidgetType.STAT
        self.value: str = ""
        self.label: str = ""
        self.icon: str = ""
        self.color: str = "#1976d2"
        self.size: str = "medium"  # small, medium, large

    def set_value(self, value: str, label: str = ""):
        """Set stat value"""
        self.value = value
        self.label = label
        self.last_updated = datetime.now()

    def render(self) -> Dict[str, Any]:
        """Render stat widget"""
        return {
            'type': 'stat',
            'value': self.value,
            'label': self.label,
            'icon': self.icon,
            'color': self.color,
            'size': self.size
        }


class WidgetFactory:
    """Factory for creating widgets"""

    @staticmethod
    def create_widget(widget_type: WidgetType, **kwargs) -> Widget:
        """Create a widget of the specified type"""
        if widget_type == WidgetType.KPI:
            return KPIWidget(**kwargs)
        elif widget_type == WidgetType.CHART:
            return ChartWidget(**kwargs)
        elif widget_type == WidgetType.TABLE:
            return TableWidget(**kwargs)
        elif widget_type == WidgetType.FILTER:
            return FilterWidget(**kwargs)
        elif widget_type == WidgetType.GAUGE:
            return GaugeWidget(**kwargs)
        elif widget_type == WidgetType.TEXT:
            return TextWidget(**kwargs)
        elif widget_type == WidgetType.PROGRESS:
            return ProgressWidget(**kwargs)
        elif widget_type == WidgetType.STAT:
            return StatWidget(**kwargs)
        else:
            return Widget(**kwargs)

    @staticmethod
    def create_kpi(title: str, value: float, **kwargs) -> KPIWidget:
        """Create a KPI widget"""
        widget = KPIWidget(title=title)
        widget.set_value(value)
        for key, val in kwargs.items():
            if hasattr(widget, key):
                setattr(widget, key, val)
        return widget

    @staticmethod
    def create_chart(title: str, df: pd.DataFrame, chart_type: str = "line", **kwargs) -> ChartWidget:
        """Create a chart widget"""
        widget = ChartWidget(title=title)
        widget.chart_type = chart_type
        widget.data = df
        for key, val in kwargs.items():
            if hasattr(widget, key):
                setattr(widget, key, val)
        return widget

    @staticmethod
    def create_table(title: str, df: pd.DataFrame, **kwargs) -> TableWidget:
        """Create a table widget"""
        widget = TableWidget(title=title)
        widget.set_data(df)
        for key, val in kwargs.items():
            if hasattr(widget, key):
                setattr(widget, key, val)
        return widget


class WidgetManager:
    """Manages widget instances"""

    def __init__(self):
        self.widgets: Dict[str, Widget] = {}

    def add_widget(self, widget: Widget) -> str:
        """Add a widget"""
        self.widgets[widget.widget_id] = widget
        return widget.widget_id

    def remove_widget(self, widget_id: str) -> bool:
        """Remove a widget"""
        if widget_id in self.widgets:
            del self.widgets[widget_id]
            return True
        return False

    def get_widget(self, widget_id: str) -> Optional[Widget]:
        """Get a widget by ID"""
        return self.widgets.get(widget_id)

    def update_widget_data(self, widget_id: str, data: Any):
        """Update widget data"""
        widget = self.get_widget(widget_id)
        if widget:
            widget.update_data(data)

    def render_widget(self, widget_id: str) -> Any:
        """Render a widget"""
        widget = self.get_widget(widget_id)
        if widget:
            return widget.render()
        return None

    def list_widgets(self) -> List[str]:
        """List all widget IDs"""
        return list(self.widgets.keys())
