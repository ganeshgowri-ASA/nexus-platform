"""
Visualizations

Charts, graphs, and heatmaps using Plotly.
"""

import plotly.graph_objects as go
import plotly.express as px
from typing import Any, Dict, List
import pandas as pd


class AnalyticsVisualizations:
    """Analytics visualization components."""

    @staticmethod
    def line_chart(data: List[Dict[str, Any]], x: str, y: str, title: str = "") -> go.Figure:
        """Create a line chart."""
        df = pd.DataFrame(data)
        fig = px.line(df, x=x, y=y, title=title)
        fig.update_layout(hovermode='x unified')
        return fig

    @staticmethod
    def bar_chart(data: List[Dict[str, Any]], x: str, y: str, title: str = "") -> go.Figure:
        """Create a bar chart."""
        df = pd.DataFrame(data)
        fig = px.bar(df, x=x, y=y, title=title)
        return fig

    @staticmethod
    def funnel_chart(data: List[Dict[str, Any]], title: str = "Funnel") -> go.Figure:
        """Create a funnel chart."""
        fig = go.Figure(go.Funnel(
            y=[d['name'] for d in data],
            x=[d['value'] for d in data],
            textinfo="value+percent initial"
        ))
        fig.update_layout(title=title)
        return fig

    @staticmethod
    def heatmap(data: List[List[float]], x_labels: List[str], y_labels: List[str], title: str = "") -> go.Figure:
        """Create a heatmap."""
        fig = go.Figure(data=go.Heatmap(
            z=data,
            x=x_labels,
            y=y_labels,
            colorscale='Viridis'
        ))
        fig.update_layout(title=title)
        return fig

    @staticmethod
    def pie_chart(data: Dict[str, float], title: str = "") -> go.Figure:
        """Create a pie chart."""
        fig = go.Figure(data=[go.Pie(
            labels=list(data.keys()),
            values=list(data.values())
        )])
        fig.update_layout(title=title)
        return fig

    @staticmethod
    def retention_chart(retention_data: List[Dict[str, Any]]) -> go.Figure:
        """Create retention cohort heatmap."""
        df = pd.DataFrame(retention_data)
        pivot = df.pivot_table(values='retention_rate', index='cohort', columns='period')

        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale='RdYlGn',
            text=pivot.values,
            texttemplate='%{text:.1f}%',
            textfont={"size": 10}
        ))

        fig.update_layout(
            title="Cohort Retention Analysis",
            xaxis_title="Periods",
            yaxis_title="Cohort"
        )
        return fig
