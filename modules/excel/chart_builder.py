"""Chart and visualization builder for spreadsheets."""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


class ChartType(Enum):
    """Chart types."""
    LINE = "line"
    BAR = "bar"
    COLUMN = "column"
    PIE = "pie"
    SCATTER = "scatter"
    AREA = "area"
    COMBO = "combo"
    HISTOGRAM = "histogram"
    BOX = "box"
    HEATMAP = "heatmap"


@dataclass
class ChartConfig:
    """Chart configuration."""

    chart_type: ChartType
    title: str
    x_axis: Optional[str] = None
    y_axis: Optional[List[str]] = None
    data_range: Optional[tuple] = None  # (start_row, start_col, end_row, end_col)
    width: int = 800
    height: int = 600
    show_legend: bool = True
    show_grid: bool = True
    colors: Optional[List[str]] = None
    x_label: Optional[str] = None
    y_label: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'chart_type': self.chart_type.value,
            'title': self.title,
            'x_axis': self.x_axis,
            'y_axis': self.y_axis,
            'data_range': self.data_range,
            'width': self.width,
            'height': self.height,
            'show_legend': self.show_legend,
            'show_grid': self.show_grid,
            'colors': self.colors,
            'x_label': self.x_label,
            'y_label': self.y_label
        }


class ChartBuilder:
    """Build charts and visualizations."""

    def __init__(self):
        """Initialize chart builder."""
        self.charts: Dict[str, ChartConfig] = {}

    def create_chart(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """
        Create a chart from DataFrame.

        Args:
            df: Data source
            config: Chart configuration

        Returns:
            Plotly figure
        """
        if config.chart_type == ChartType.LINE:
            return self._create_line_chart(df, config)
        elif config.chart_type == ChartType.BAR:
            return self._create_bar_chart(df, config)
        elif config.chart_type == ChartType.COLUMN:
            return self._create_column_chart(df, config)
        elif config.chart_type == ChartType.PIE:
            return self._create_pie_chart(df, config)
        elif config.chart_type == ChartType.SCATTER:
            return self._create_scatter_chart(df, config)
        elif config.chart_type == ChartType.AREA:
            return self._create_area_chart(df, config)
        elif config.chart_type == ChartType.HISTOGRAM:
            return self._create_histogram(df, config)
        elif config.chart_type == ChartType.BOX:
            return self._create_box_chart(df, config)
        elif config.chart_type == ChartType.HEATMAP:
            return self._create_heatmap(df, config)
        else:
            raise ValueError(f"Unsupported chart type: {config.chart_type}")

    def _create_line_chart(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create line chart."""
        fig = go.Figure()

        for y_col in (config.y_axis or []):
            fig.add_trace(go.Scatter(
                x=df[config.x_axis] if config.x_axis else df.index,
                y=df[y_col],
                mode='lines+markers',
                name=y_col
            ))

        fig.update_layout(
            title=config.title,
            xaxis_title=config.x_label or config.x_axis,
            yaxis_title=config.y_label or 'Value',
            width=config.width,
            height=config.height,
            showlegend=config.show_legend
        )

        if config.show_grid:
            fig.update_xaxes(showgrid=True)
            fig.update_yaxes(showgrid=True)

        return fig

    def _create_bar_chart(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create horizontal bar chart."""
        fig = go.Figure()

        for y_col in (config.y_axis or []):
            fig.add_trace(go.Bar(
                y=df[config.x_axis] if config.x_axis else df.index,
                x=df[y_col],
                name=y_col,
                orientation='h'
            ))

        fig.update_layout(
            title=config.title,
            xaxis_title=config.x_label or 'Value',
            yaxis_title=config.y_label or config.x_axis,
            width=config.width,
            height=config.height,
            showlegend=config.show_legend,
            barmode='group'
        )

        return fig

    def _create_column_chart(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create vertical column chart."""
        fig = go.Figure()

        for y_col in (config.y_axis or []):
            fig.add_trace(go.Bar(
                x=df[config.x_axis] if config.x_axis else df.index,
                y=df[y_col],
                name=y_col
            ))

        fig.update_layout(
            title=config.title,
            xaxis_title=config.x_label or config.x_axis,
            yaxis_title=config.y_label or 'Value',
            width=config.width,
            height=config.height,
            showlegend=config.show_legend,
            barmode='group'
        )

        return fig

    def _create_pie_chart(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create pie chart."""
        fig = go.Figure(data=[go.Pie(
            labels=df[config.x_axis] if config.x_axis else df.index,
            values=df[config.y_axis[0]] if config.y_axis else df.iloc[:, 0]
        )])

        fig.update_layout(
            title=config.title,
            width=config.width,
            height=config.height,
            showlegend=config.show_legend
        )

        return fig

    def _create_scatter_chart(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create scatter plot."""
        fig = go.Figure()

        y_cols = config.y_axis or [df.columns[1]]

        for y_col in y_cols:
            fig.add_trace(go.Scatter(
                x=df[config.x_axis] if config.x_axis else df.iloc[:, 0],
                y=df[y_col],
                mode='markers',
                name=y_col
            ))

        fig.update_layout(
            title=config.title,
            xaxis_title=config.x_label or config.x_axis,
            yaxis_title=config.y_label or 'Value',
            width=config.width,
            height=config.height,
            showlegend=config.show_legend
        )

        return fig

    def _create_area_chart(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create area chart."""
        fig = go.Figure()

        for y_col in (config.y_axis or []):
            fig.add_trace(go.Scatter(
                x=df[config.x_axis] if config.x_axis else df.index,
                y=df[y_col],
                mode='lines',
                fill='tonexty',
                name=y_col
            ))

        fig.update_layout(
            title=config.title,
            xaxis_title=config.x_label or config.x_axis,
            yaxis_title=config.y_label or 'Value',
            width=config.width,
            height=config.height,
            showlegend=config.show_legend
        )

        return fig

    def _create_histogram(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create histogram."""
        fig = px.histogram(
            df,
            x=config.x_axis or df.columns[0],
            title=config.title,
            width=config.width,
            height=config.height
        )

        return fig

    def _create_box_chart(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create box plot."""
        fig = go.Figure()

        for y_col in (config.y_axis or df.columns):
            fig.add_trace(go.Box(
                y=df[y_col],
                name=y_col
            ))

        fig.update_layout(
            title=config.title,
            yaxis_title=config.y_label or 'Value',
            width=config.width,
            height=config.height,
            showlegend=config.show_legend
        )

        return fig

    def _create_heatmap(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create heatmap."""
        fig = go.Figure(data=go.Heatmap(
            z=df.values,
            x=df.columns,
            y=df.index,
            colorscale='Viridis'
        ))

        fig.update_layout(
            title=config.title,
            width=config.width,
            height=config.height
        )

        return fig

    def create_sparkline(self, data: List[float], width: int = 200,
                        height: int = 50) -> go.Figure:
        """
        Create a sparkline (mini chart).

        Args:
            data: Data points
            width: Chart width
            height: Chart height

        Returns:
            Plotly figure
        """
        fig = go.Figure(data=go.Scatter(
            y=data,
            mode='lines',
            line=dict(color='blue', width=2)
        ))

        fig.update_layout(
            width=width,
            height=height,
            showlegend=False,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )

        return fig
