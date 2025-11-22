"""
Infographics Designer - Charts Module

This module provides various chart types with data binding support including
bar charts, pie charts, line charts, scatter plots, donut charts, funnel charts,
and comparison charts.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import uuid

from .elements import BaseElement, ElementType, Position, Style


class ChartType(Enum):
    """Types of charts."""
    BAR = "bar"
    HORIZONTAL_BAR = "horizontal_bar"
    STACKED_BAR = "stacked_bar"
    PIE = "pie"
    DONUT = "donut"
    LINE = "line"
    AREA = "area"
    SCATTER = "scatter"
    BUBBLE = "bubble"
    FUNNEL = "funnel"
    RADAR = "radar"
    GAUGE = "gauge"
    HEATMAP = "heatmap"
    TREEMAP = "treemap"
    WATERFALL = "waterfall"
    COMPARISON = "comparison"


class LegendPosition(Enum):
    """Legend position options."""
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
    NONE = "none"


@dataclass
class DataSeries:
    """Data series for charts."""
    name: str
    data: List[float]
    color: Optional[str] = None
    labels: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'data': self.data,
            'color': self.color,
            'labels': self.labels,
            'metadata': self.metadata
        }


@dataclass
class ChartConfig:
    """Configuration for chart appearance and behavior."""
    title: str = "Chart Title"
    show_title: bool = True
    show_legend: bool = True
    legend_position: LegendPosition = LegendPosition.RIGHT
    show_grid: bool = True
    show_axis_labels: bool = True
    show_data_labels: bool = False
    animation_enabled: bool = True
    animation_duration: float = 1000  # milliseconds
    color_scheme: List[str] = field(default_factory=lambda: [
        '#3498DB', '#E74C3C', '#27AE60', '#F39C12', '#9B59B6',
        '#1ABC9C', '#E67E22', '#34495E', '#16A085', '#C0392B'
    ])
    custom_colors: Dict[str, str] = field(default_factory=dict)
    font_family: str = "Arial"
    font_size: float = 12.0
    background_color: str = "#FFFFFF"
    grid_color: str = "#E0E0E0"
    axis_color: str = "#666666"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'title': self.title,
            'show_title': self.show_title,
            'show_legend': self.show_legend,
            'legend_position': self.legend_position.value,
            'show_grid': self.show_grid,
            'show_axis_labels': self.show_axis_labels,
            'show_data_labels': self.show_data_labels,
            'animation_enabled': self.animation_enabled,
            'animation_duration': self.animation_duration,
            'color_scheme': self.color_scheme,
            'custom_colors': self.custom_colors,
            'font_family': self.font_family,
            'font_size': self.font_size,
            'background_color': self.background_color,
            'grid_color': self.grid_color,
            'axis_color': self.axis_color
        }


@dataclass
class AxisConfig:
    """Configuration for chart axes."""
    x_label: str = "X Axis"
    y_label: str = "Y Axis"
    x_min: Optional[float] = None
    x_max: Optional[float] = None
    y_min: Optional[float] = None
    y_max: Optional[float] = None
    x_scale: str = "linear"  # linear, log, time
    y_scale: str = "linear"
    x_tick_count: Optional[int] = None
    y_tick_count: Optional[int] = None
    x_tick_format: Optional[str] = None
    y_tick_format: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'x_label': self.x_label,
            'y_label': self.y_label,
            'x_min': self.x_min,
            'x_max': self.x_max,
            'y_min': self.y_min,
            'y_max': self.y_max,
            'x_scale': self.x_scale,
            'y_scale': self.y_scale,
            'x_tick_count': self.x_tick_count,
            'y_tick_count': self.y_tick_count,
            'x_tick_format': self.x_tick_format,
            'y_tick_format': self.y_tick_format
        }


@dataclass
class ChartElement(BaseElement):
    """Chart element for infographics."""
    chart_type: ChartType = ChartType.BAR
    data_series: List[DataSeries] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    config: ChartConfig = field(default_factory=ChartConfig)
    axis_config: AxisConfig = field(default_factory=AxisConfig)
    data_binding: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Set element type."""
        self.element_type = ElementType.SHAPE  # Charts are rendered as shapes

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            'chart_type': self.chart_type.value,
            'data_series': [series.to_dict() for series in self.data_series],
            'categories': self.categories,
            'config': self.config.to_dict(),
            'axis_config': self.axis_config.to_dict(),
            'data_binding': self.data_binding
        })
        return data

    def add_series(self, series: DataSeries) -> None:
        """Add data series to chart."""
        self.data_series.append(series)

    def remove_series(self, series_name: str) -> None:
        """Remove data series from chart."""
        self.data_series = [s for s in self.data_series if s.name != series_name]

    def update_data(self, series_name: str, data: List[float]) -> None:
        """Update data for a specific series."""
        for series in self.data_series:
            if series.name == series_name:
                series.data = data
                break

    def bind_data_source(self, source: Dict[str, Any]) -> None:
        """Bind chart to external data source."""
        self.data_binding = source

    def duplicate(self) -> 'ChartElement':
        """Create a duplicate."""
        from copy import deepcopy
        new_elem = deepcopy(self)
        new_elem.id = str(uuid.uuid4())
        new_elem.position.x += 10
        new_elem.position.y += 10
        return new_elem


class ChartFactory:
    """Factory for creating charts."""

    @staticmethod
    def create_bar_chart(categories: List[str], data: List[float],
                        title: str = "Bar Chart", **kwargs) -> ChartElement:
        """Create a bar chart."""
        series = DataSeries(name="Series 1", data=data)
        config = ChartConfig(title=title)

        return ChartElement(
            chart_type=ChartType.BAR,
            data_series=[series],
            categories=categories,
            config=config,
            position=Position(x=0, y=0, width=600, height=400),
            **kwargs
        )

    @staticmethod
    def create_pie_chart(labels: List[str], data: List[float],
                        title: str = "Pie Chart", **kwargs) -> ChartElement:
        """Create a pie chart."""
        series = DataSeries(name="Series 1", data=data, labels=labels)
        config = ChartConfig(title=title, show_grid=False, show_axis_labels=False)

        return ChartElement(
            chart_type=ChartType.PIE,
            data_series=[series],
            config=config,
            position=Position(x=0, y=0, width=400, height=400),
            **kwargs
        )

    @staticmethod
    def create_donut_chart(labels: List[str], data: List[float],
                          title: str = "Donut Chart", **kwargs) -> ChartElement:
        """Create a donut chart."""
        series = DataSeries(name="Series 1", data=data, labels=labels)
        config = ChartConfig(title=title, show_grid=False, show_axis_labels=False)

        return ChartElement(
            chart_type=ChartType.DONUT,
            data_series=[series],
            config=config,
            position=Position(x=0, y=0, width=400, height=400),
            **kwargs
        )

    @staticmethod
    def create_line_chart(categories: List[str], data: List[float],
                         title: str = "Line Chart", **kwargs) -> ChartElement:
        """Create a line chart."""
        series = DataSeries(name="Series 1", data=data)
        config = ChartConfig(title=title)

        return ChartElement(
            chart_type=ChartType.LINE,
            data_series=[series],
            categories=categories,
            config=config,
            position=Position(x=0, y=0, width=600, height=400),
            **kwargs
        )

    @staticmethod
    def create_area_chart(categories: List[str], data: List[float],
                         title: str = "Area Chart", **kwargs) -> ChartElement:
        """Create an area chart."""
        series = DataSeries(name="Series 1", data=data)
        config = ChartConfig(title=title)

        return ChartElement(
            chart_type=ChartType.AREA,
            data_series=[series],
            categories=categories,
            config=config,
            position=Position(x=0, y=0, width=600, height=400),
            **kwargs
        )

    @staticmethod
    def create_scatter_chart(x_data: List[float], y_data: List[float],
                           title: str = "Scatter Chart", **kwargs) -> ChartElement:
        """Create a scatter chart."""
        # For scatter, we use x_data as categories and y_data as values
        series = DataSeries(name="Series 1", data=y_data)
        config = ChartConfig(title=title)

        return ChartElement(
            chart_type=ChartType.SCATTER,
            data_series=[series],
            categories=[str(x) for x in x_data],
            config=config,
            position=Position(x=0, y=0, width=600, height=400),
            **kwargs
        )

    @staticmethod
    def create_funnel_chart(labels: List[str], data: List[float],
                          title: str = "Funnel Chart", **kwargs) -> ChartElement:
        """Create a funnel chart."""
        series = DataSeries(name="Series 1", data=data, labels=labels)
        config = ChartConfig(title=title, show_grid=False)

        return ChartElement(
            chart_type=ChartType.FUNNEL,
            data_series=[series],
            config=config,
            position=Position(x=0, y=0, width=400, height=500),
            **kwargs
        )

    @staticmethod
    def create_comparison_chart(categories: List[str],
                               series_data: List[Tuple[str, List[float]]],
                               title: str = "Comparison Chart",
                               **kwargs) -> ChartElement:
        """Create a comparison chart with multiple series."""
        series_list = [
            DataSeries(name=name, data=data)
            for name, data in series_data
        ]
        config = ChartConfig(title=title)

        return ChartElement(
            chart_type=ChartType.BAR,
            data_series=series_list,
            categories=categories,
            config=config,
            position=Position(x=0, y=0, width=700, height=400),
            **kwargs
        )

    @staticmethod
    def create_stacked_bar_chart(categories: List[str],
                                series_data: List[Tuple[str, List[float]]],
                                title: str = "Stacked Bar Chart",
                                **kwargs) -> ChartElement:
        """Create a stacked bar chart."""
        series_list = [
            DataSeries(name=name, data=data)
            for name, data in series_data
        ]
        config = ChartConfig(title=title)

        return ChartElement(
            chart_type=ChartType.STACKED_BAR,
            data_series=series_list,
            categories=categories,
            config=config,
            position=Position(x=0, y=0, width=700, height=400),
            **kwargs
        )

    @staticmethod
    def create_gauge_chart(value: float, min_val: float = 0, max_val: float = 100,
                          title: str = "Gauge", **kwargs) -> ChartElement:
        """Create a gauge chart."""
        series = DataSeries(name="Value", data=[value])
        config = ChartConfig(title=title, show_grid=False, show_axis_labels=False)
        axis_config = AxisConfig(y_min=min_val, y_max=max_val)

        return ChartElement(
            chart_type=ChartType.GAUGE,
            data_series=[series],
            config=config,
            axis_config=axis_config,
            position=Position(x=0, y=0, width=300, height=300),
            **kwargs
        )

    @staticmethod
    def create_radar_chart(categories: List[str], data: List[float],
                          title: str = "Radar Chart", **kwargs) -> ChartElement:
        """Create a radar chart."""
        series = DataSeries(name="Series 1", data=data)
        config = ChartConfig(title=title, show_grid=True)

        return ChartElement(
            chart_type=ChartType.RADAR,
            data_series=[series],
            categories=categories,
            config=config,
            position=Position(x=0, y=0, width=400, height=400),
            **kwargs
        )


class ChartStyler:
    """Utility class for styling charts."""

    # Predefined color schemes
    COLOR_SCHEMES = {
        'default': ['#3498DB', '#E74C3C', '#27AE60', '#F39C12', '#9B59B6'],
        'pastel': ['#AED6F1', '#F5B7B1', '#A9DFBF', '#FAD7A0', '#D7BDE2'],
        'vibrant': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8'],
        'professional': ['#2C3E50', '#3498DB', '#95A5A6', '#E74C3C', '#34495E'],
        'earth': ['#8B4513', '#D2691E', '#CD853F', '#DEB887', '#F4A460'],
        'ocean': ['#006994', '#0892D0', '#33A1C9', '#7FCCE1', '#C4E3F3'],
        'sunset': ['#FF6B35', '#F7931E', '#FDC830', '#F37335', '#C9485B'],
        'monochrome': ['#2C3E50', '#34495E', '#7F8C8D', '#95A5A6', '#BDC3C7']
    }

    @staticmethod
    def apply_color_scheme(chart: ChartElement, scheme_name: str) -> None:
        """Apply a color scheme to a chart."""
        if scheme_name in ChartStyler.COLOR_SCHEMES:
            chart.config.color_scheme = ChartStyler.COLOR_SCHEMES[scheme_name]

            # Apply colors to series
            colors = ChartStyler.COLOR_SCHEMES[scheme_name]
            for i, series in enumerate(chart.data_series):
                series.color = colors[i % len(colors)]

    @staticmethod
    def set_gradient_colors(chart: ChartElement, start_color: str,
                          end_color: str, steps: int = 5) -> None:
        """Set gradient colors for chart series."""
        # Simplified gradient - in production would calculate intermediate colors
        chart.config.color_scheme = [start_color, end_color]

    @staticmethod
    def apply_minimal_style(chart: ChartElement) -> None:
        """Apply minimal styling to chart."""
        chart.config.show_grid = False
        chart.config.background_color = "#FFFFFF"
        chart.config.grid_color = "#F0F0F0"
        chart.config.axis_color = "#CCCCCC"

    @staticmethod
    def apply_bold_style(chart: ChartElement) -> None:
        """Apply bold styling to chart."""
        chart.config.show_grid = True
        chart.config.font_size = 14.0
        chart.config.show_data_labels = True
        ChartStyler.apply_color_scheme(chart, 'vibrant')

    @staticmethod
    def apply_professional_style(chart: ChartElement) -> None:
        """Apply professional styling to chart."""
        chart.config.background_color = "#F8F9FA"
        chart.config.font_family = "Arial"
        chart.config.font_size = 11.0
        ChartStyler.apply_color_scheme(chart, 'professional')


class ChartDataTransformer:
    """Utility class for transforming chart data."""

    @staticmethod
    def normalize_data(data: List[float], min_val: float = 0,
                      max_val: float = 100) -> List[float]:
        """Normalize data to a specific range."""
        if not data:
            return []

        data_min = min(data)
        data_max = max(data)

        if data_max == data_min:
            return [min_val] * len(data)

        scale = (max_val - min_val) / (data_max - data_min)
        return [(val - data_min) * scale + min_val for val in data]

    @staticmethod
    def calculate_percentages(data: List[float]) -> List[float]:
        """Convert values to percentages."""
        total = sum(data)
        if total == 0:
            return [0.0] * len(data)
        return [(val / total) * 100 for val in data]

    @staticmethod
    def aggregate_data(data: List[float], method: str = 'sum') -> float:
        """Aggregate data using specified method."""
        if not data:
            return 0.0

        if method == 'sum':
            return sum(data)
        elif method == 'average':
            return sum(data) / len(data)
        elif method == 'max':
            return max(data)
        elif method == 'min':
            return min(data)
        elif method == 'median':
            sorted_data = sorted(data)
            n = len(sorted_data)
            mid = n // 2
            if n % 2 == 0:
                return (sorted_data[mid - 1] + sorted_data[mid]) / 2
            return sorted_data[mid]
        return 0.0

    @staticmethod
    def smooth_data(data: List[float], window_size: int = 3) -> List[float]:
        """Smooth data using moving average."""
        if len(data) < window_size:
            return data

        smoothed = []
        for i in range(len(data)):
            start = max(0, i - window_size // 2)
            end = min(len(data), i + window_size // 2 + 1)
            window = data[start:end]
            smoothed.append(sum(window) / len(window))

        return smoothed


__all__ = [
    'ChartType', 'LegendPosition',
    'DataSeries', 'ChartConfig', 'AxisConfig', 'ChartElement',
    'ChartFactory', 'ChartStyler', 'ChartDataTransformer'
]
