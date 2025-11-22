"""
NEXUS Reports Builder - Charts and Tables Module
Comprehensive charting library with support for all major chart types and interactive tables
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import json


class ChartType(Enum):
    """Supported chart types"""
    BAR = "bar"
    LINE = "line"
    AREA = "area"
    PIE = "pie"
    DONUT = "donut"
    SCATTER = "scatter"
    BUBBLE = "bubble"
    HISTOGRAM = "histogram"
    BOX = "box"
    VIOLIN = "violin"
    HEATMAP = "heatmap"
    TREEMAP = "treemap"
    SUNBURST = "sunburst"
    FUNNEL = "funnel"
    WATERFALL = "waterfall"
    GAUGE = "gauge"
    CANDLESTICK = "candlestick"
    SANKEY = "sankey"
    RADAR = "radar"
    POLAR = "polar"


class AggregationType(Enum):
    """Data aggregation types"""
    SUM = "sum"
    AVG = "avg"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    STD = "std"
    VAR = "var"


@dataclass
class ChartConfig:
    """Configuration for chart appearance and behavior"""
    title: str = ""
    subtitle: str = ""
    width: int = 800
    height: int = 600
    theme: str = "plotly"  # plotly, plotly_white, plotly_dark, ggplot2, seaborn
    show_legend: bool = True
    legend_position: str = "right"  # right, left, top, bottom
    show_grid: bool = True
    show_toolbar: bool = True
    animation: bool = False
    responsive: bool = True


@dataclass
class AxisConfig:
    """Configuration for chart axes"""
    title: str = ""
    show_title: bool = True
    show_labels: bool = True
    show_grid: bool = True
    log_scale: bool = False
    reverse: bool = False
    range_min: Optional[float] = None
    range_max: Optional[float] = None
    tick_format: str = ""


@dataclass
class ColorScheme:
    """Color scheme for charts"""
    colors: List[str] = None
    color_scale: str = "Viridis"  # Viridis, Plasma, Blues, Reds, etc.
    reverse_scale: bool = False

    def __post_init__(self):
        if self.colors is None:
            self.colors = [
                "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
                "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
                "#bcbd22", "#17becf"
            ]


class Chart:
    """Base chart class"""

    def __init__(self, chart_type: ChartType, data: pd.DataFrame, config: ChartConfig = None):
        self.chart_type = chart_type
        self.data = data
        self.config = config or ChartConfig()
        self.color_scheme = ColorScheme()
        self.x_axis = AxisConfig()
        self.y_axis = AxisConfig()
        self.figure = None

    def set_axis_config(self, axis: str, config: AxisConfig):
        """Set axis configuration"""
        if axis.lower() == "x":
            self.x_axis = config
        elif axis.lower() == "y":
            self.y_axis = config

    def set_color_scheme(self, scheme: ColorScheme):
        """Set color scheme"""
        self.color_scheme = scheme

    def render(self) -> go.Figure:
        """Render the chart"""
        if self.chart_type == ChartType.BAR:
            return self._render_bar()
        elif self.chart_type == ChartType.LINE:
            return self._render_line()
        elif self.chart_type == ChartType.AREA:
            return self._render_area()
        elif self.chart_type == ChartType.PIE:
            return self._render_pie()
        elif self.chart_type == ChartType.DONUT:
            return self._render_donut()
        elif self.chart_type == ChartType.SCATTER:
            return self._render_scatter()
        elif self.chart_type == ChartType.BUBBLE:
            return self._render_bubble()
        elif self.chart_type == ChartType.HISTOGRAM:
            return self._render_histogram()
        elif self.chart_type == ChartType.BOX:
            return self._render_box()
        elif self.chart_type == ChartType.HEATMAP:
            return self._render_heatmap()
        elif self.chart_type == ChartType.TREEMAP:
            return self._render_treemap()
        elif self.chart_type == ChartType.SUNBURST:
            return self._render_sunburst()
        elif self.chart_type == ChartType.FUNNEL:
            return self._render_funnel()
        elif self.chart_type == ChartType.WATERFALL:
            return self._render_waterfall()
        elif self.chart_type == ChartType.GAUGE:
            return self._render_gauge()
        elif self.chart_type == ChartType.RADAR:
            return self._render_radar()
        else:
            raise ValueError(f"Unsupported chart type: {self.chart_type}")

    def _render_bar(self, x: str = None, y: str = None, orientation: str = "v") -> go.Figure:
        """Render bar chart"""
        if x is None and len(self.data.columns) > 0:
            x = self.data.columns[0]
        if y is None and len(self.data.columns) > 1:
            y = self.data.columns[1]

        fig = px.bar(
            self.data,
            x=x,
            y=y,
            orientation=orientation,
            title=self.config.title,
            color_discrete_sequence=self.color_scheme.colors
        )

        self._apply_layout(fig)
        return fig

    def _render_line(self, x: str = None, y: str = None) -> go.Figure:
        """Render line chart"""
        if x is None and len(self.data.columns) > 0:
            x = self.data.columns[0]
        if y is None and len(self.data.columns) > 1:
            y = self.data.columns[1]

        fig = px.line(
            self.data,
            x=x,
            y=y,
            title=self.config.title,
            color_discrete_sequence=self.color_scheme.colors
        )

        self._apply_layout(fig)
        return fig

    def _render_area(self, x: str = None, y: str = None) -> go.Figure:
        """Render area chart"""
        if x is None and len(self.data.columns) > 0:
            x = self.data.columns[0]
        if y is None and len(self.data.columns) > 1:
            y = self.data.columns[1]

        fig = px.area(
            self.data,
            x=x,
            y=y,
            title=self.config.title,
            color_discrete_sequence=self.color_scheme.colors
        )

        self._apply_layout(fig)
        return fig

    def _render_pie(self, names: str = None, values: str = None) -> go.Figure:
        """Render pie chart"""
        if names is None and len(self.data.columns) > 0:
            names = self.data.columns[0]
        if values is None and len(self.data.columns) > 1:
            values = self.data.columns[1]

        fig = px.pie(
            self.data,
            names=names,
            values=values,
            title=self.config.title,
            color_discrete_sequence=self.color_scheme.colors
        )

        self._apply_layout(fig)
        return fig

    def _render_donut(self, names: str = None, values: str = None) -> go.Figure:
        """Render donut chart"""
        fig = self._render_pie(names, values)
        fig.update_traces(hole=0.4)
        return fig

    def _render_scatter(self, x: str = None, y: str = None) -> go.Figure:
        """Render scatter plot"""
        if x is None and len(self.data.columns) > 0:
            x = self.data.columns[0]
        if y is None and len(self.data.columns) > 1:
            y = self.data.columns[1]

        fig = px.scatter(
            self.data,
            x=x,
            y=y,
            title=self.config.title,
            color_discrete_sequence=self.color_scheme.colors
        )

        self._apply_layout(fig)
        return fig

    def _render_bubble(self, x: str = None, y: str = None, size: str = None) -> go.Figure:
        """Render bubble chart"""
        if x is None and len(self.data.columns) > 0:
            x = self.data.columns[0]
        if y is None and len(self.data.columns) > 1:
            y = self.data.columns[1]
        if size is None and len(self.data.columns) > 2:
            size = self.data.columns[2]

        fig = px.scatter(
            self.data,
            x=x,
            y=y,
            size=size,
            title=self.config.title,
            color_discrete_sequence=self.color_scheme.colors
        )

        self._apply_layout(fig)
        return fig

    def _render_histogram(self, x: str = None) -> go.Figure:
        """Render histogram"""
        if x is None and len(self.data.columns) > 0:
            x = self.data.columns[0]

        fig = px.histogram(
            self.data,
            x=x,
            title=self.config.title,
            color_discrete_sequence=self.color_scheme.colors
        )

        self._apply_layout(fig)
        return fig

    def _render_box(self, y: str = None) -> go.Figure:
        """Render box plot"""
        if y is None and len(self.data.columns) > 0:
            y = self.data.columns[0]

        fig = px.box(
            self.data,
            y=y,
            title=self.config.title,
            color_discrete_sequence=self.color_scheme.colors
        )

        self._apply_layout(fig)
        return fig

    def _render_heatmap(self) -> go.Figure:
        """Render heatmap"""
        fig = px.imshow(
            self.data,
            title=self.config.title,
            color_continuous_scale=self.color_scheme.color_scale
        )

        self._apply_layout(fig)
        return fig

    def _render_treemap(self, path: List[str] = None, values: str = None) -> go.Figure:
        """Render treemap"""
        if path is None:
            path = [self.data.columns[0]]
        if values is None and len(self.data.columns) > 1:
            values = self.data.columns[1]

        fig = px.treemap(
            self.data,
            path=path,
            values=values,
            title=self.config.title,
            color_discrete_sequence=self.color_scheme.colors
        )

        self._apply_layout(fig)
        return fig

    def _render_sunburst(self, path: List[str] = None, values: str = None) -> go.Figure:
        """Render sunburst chart"""
        if path is None:
            path = [self.data.columns[0]]
        if values is None and len(self.data.columns) > 1:
            values = self.data.columns[1]

        fig = px.sunburst(
            self.data,
            path=path,
            values=values,
            title=self.config.title,
            color_discrete_sequence=self.color_scheme.colors
        )

        self._apply_layout(fig)
        return fig

    def _render_funnel(self, x: str = None, y: str = None) -> go.Figure:
        """Render funnel chart"""
        if x is None and len(self.data.columns) > 0:
            x = self.data.columns[0]
        if y is None and len(self.data.columns) > 1:
            y = self.data.columns[1]

        fig = px.funnel(
            self.data,
            x=x,
            y=y,
            title=self.config.title,
            color_discrete_sequence=self.color_scheme.colors
        )

        self._apply_layout(fig)
        return fig

    def _render_waterfall(self, x: str = None, y: str = None) -> go.Figure:
        """Render waterfall chart"""
        if x is None and len(self.data.columns) > 0:
            x = self.data.columns[0]
        if y is None and len(self.data.columns) > 1:
            y = self.data.columns[1]

        fig = go.Figure(go.Waterfall(
            name="",
            orientation="v",
            x=self.data[x],
            y=self.data[y],
            connector={"line": {"color": "rgb(63, 63, 63)"}}
        ))

        fig.update_layout(title=self.config.title)
        self._apply_layout(fig)
        return fig

    def _render_gauge(self, value: float, max_value: float = 100) -> go.Figure:
        """Render gauge chart"""
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': self.config.title},
            gauge={
                'axis': {'range': [None, max_value]},
                'bar': {'color': self.color_scheme.colors[0]},
                'steps': [
                    {'range': [0, max_value * 0.5], 'color': "lightgray"},
                    {'range': [max_value * 0.5, max_value * 0.75], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': max_value * 0.9
                }
            }
        ))

        self._apply_layout(fig)
        return fig

    def _render_radar(self, r: str = None, theta: str = None) -> go.Figure:
        """Render radar/spider chart"""
        if theta is None and len(self.data.columns) > 0:
            theta = self.data.columns[0]
        if r is None and len(self.data.columns) > 1:
            r = self.data.columns[1]

        fig = px.line_polar(
            self.data,
            r=r,
            theta=theta,
            line_close=True,
            title=self.config.title
        )

        self._apply_layout(fig)
        return fig

    def _apply_layout(self, fig: go.Figure):
        """Apply common layout settings"""
        fig.update_layout(
            width=self.config.width,
            height=self.config.height,
            template=self.config.theme,
            showlegend=self.config.show_legend,
            title=self.config.title
        )

        # Apply x-axis settings
        if self.x_axis.title:
            fig.update_xaxes(
                title_text=self.x_axis.title,
                showgrid=self.x_axis.show_grid,
                type="log" if self.x_axis.log_scale else "linear"
            )

        # Apply y-axis settings
        if self.y_axis.title:
            fig.update_yaxes(
                title_text=self.y_axis.title,
                showgrid=self.y_axis.show_grid,
                type="log" if self.y_axis.log_scale else "linear"
            )

    def add_annotation(self, text: str, x: float, y: float, **kwargs):
        """Add annotation to chart"""
        if self.figure:
            self.figure.add_annotation(text=text, x=x, y=y, **kwargs)

    def to_html(self) -> str:
        """Export chart to HTML"""
        if not self.figure:
            self.figure = self.render()
        return self.figure.to_html()

    def to_json(self) -> str:
        """Export chart to JSON"""
        if not self.figure:
            self.figure = self.render()
        return self.figure.to_json()

    def to_image(self, format: str = "png") -> bytes:
        """Export chart to image"""
        if not self.figure:
            self.figure = self.render()
        return self.figure.to_image(format=format)


class Table:
    """Interactive table component"""

    def __init__(self, data: pd.DataFrame, config: Dict[str, Any] = None):
        self.data = data
        self.config = config or {}
        self.filters: Dict[str, Any] = {}
        self.sort_column: Optional[str] = None
        self.sort_ascending: bool = True
        self.page_size: int = 20
        self.current_page: int = 1

    def apply_filter(self, column: str, value: Any, operator: str = "equals"):
        """Apply filter to table"""
        self.filters[column] = {"value": value, "operator": operator}

    def remove_filter(self, column: str):
        """Remove filter from table"""
        if column in self.filters:
            del self.filters[column]

    def clear_filters(self):
        """Clear all filters"""
        self.filters.clear()

    def get_filtered_data(self) -> pd.DataFrame:
        """Get filtered data"""
        df = self.data.copy()

        for column, filter_config in self.filters.items():
            value = filter_config["value"]
            operator = filter_config["operator"]

            if operator == "equals":
                df = df[df[column] == value]
            elif operator == "not_equals":
                df = df[df[column] != value]
            elif operator == "contains":
                df = df[df[column].str.contains(str(value), na=False)]
            elif operator == "starts_with":
                df = df[df[column].str.startswith(str(value), na=False)]
            elif operator == "ends_with":
                df = df[df[column].str.endswith(str(value), na=False)]
            elif operator == "greater_than":
                df = df[df[column] > value]
            elif operator == "less_than":
                df = df[df[column] < value]
            elif operator == "between":
                if isinstance(value, (list, tuple)) and len(value) == 2:
                    df = df[(df[column] >= value[0]) & (df[column] <= value[1])]

        return df

    def sort(self, column: str, ascending: bool = True):
        """Sort table by column"""
        self.sort_column = column
        self.sort_ascending = ascending

    def get_sorted_data(self) -> pd.DataFrame:
        """Get sorted data"""
        df = self.get_filtered_data()

        if self.sort_column:
            df = df.sort_values(by=self.sort_column, ascending=self.sort_ascending)

        return df

    def get_paginated_data(self) -> pd.DataFrame:
        """Get paginated data"""
        df = self.get_sorted_data()

        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size

        return df.iloc[start:end]

    def get_total_pages(self) -> int:
        """Get total number of pages"""
        df = self.get_filtered_data()
        return (len(df) + self.page_size - 1) // self.page_size

    def next_page(self) -> bool:
        """Go to next page"""
        if self.current_page < self.get_total_pages():
            self.current_page += 1
            return True
        return False

    def previous_page(self) -> bool:
        """Go to previous page"""
        if self.current_page > 1:
            self.current_page -= 1
            return True
        return False

    def render(self) -> go.Figure:
        """Render table as Plotly table"""
        df = self.get_paginated_data()

        fig = go.Figure(data=[go.Table(
            header=dict(
                values=list(df.columns),
                fill_color='paleturquoise',
                align='left'
            ),
            cells=dict(
                values=[df[col] for col in df.columns],
                fill_color='lavender',
                align='left'
            )
        )])

        fig.update_layout(
            title=f"Page {self.current_page} of {self.get_total_pages()}",
            width=self.config.get('width', 800),
            height=self.config.get('height', 600)
        )

        return fig

    def to_html(self) -> str:
        """Export table to HTML"""
        df = self.get_sorted_data()
        return df.to_html(index=False)

    def to_json(self) -> str:
        """Export table to JSON"""
        df = self.get_sorted_data()
        return df.to_json(orient='records')

    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get summary statistics for numeric columns"""
        df = self.get_filtered_data()
        numeric_cols = df.select_dtypes(include=['number']).columns

        stats = {}
        for col in numeric_cols:
            stats[col] = {
                'mean': df[col].mean(),
                'median': df[col].median(),
                'min': df[col].min(),
                'max': df[col].max(),
                'std': df[col].std(),
                'count': df[col].count()
            }

        return stats
