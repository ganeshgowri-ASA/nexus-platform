"""
NEXUS Gantt Chart Module
Gantt chart generation, rendering, and timeline visualization.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import date, datetime, timedelta
from dataclasses import dataclass
import plotly.figure_factory as ff
import plotly.graph_objects as go
from plotly.subplots import make_subplots


@dataclass
class GanttTask:
    """
    Gantt chart task representation.

    Attributes:
        task_id: Task identifier
        name: Task name
        start: Start date
        end: End date
        progress: Progress percentage (0-100)
        resource: Assigned resource/person
        dependencies: List of predecessor task IDs
        color: Task color
        is_milestone: Whether task is a milestone
        is_critical: Whether task is on critical path
    """
    task_id: str
    name: str
    start: date
    end: date
    progress: float = 0.0
    resource: Optional[str] = None
    dependencies: List[str] = None
    color: Optional[str] = None
    is_milestone: bool = False
    is_critical: bool = False

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

    @property
    def duration_days(self) -> int:
        """Calculate task duration in days."""
        return (self.end - self.start).days + 1


class GanttChart:
    """
    Gantt chart generator and manager.
    Creates interactive Gantt charts with dependencies, critical path, and baselines.
    """

    def __init__(self, task_manager, dependency_manager=None):
        """
        Initialize Gantt chart generator.

        Args:
            task_manager: Task manager instance
            dependency_manager: Dependency manager instance (optional)
        """
        self.task_manager = task_manager
        self.dependency_manager = dependency_manager
        self.baseline_dates: Dict[str, Tuple[date, date]] = {}

    def generate_gantt_data(self, project_id: str) -> List[GanttTask]:
        """
        Generate Gantt chart data for a project.

        Args:
            project_id: Project identifier

        Returns:
            List of GanttTask objects
        """
        tasks = self.task_manager.get_tasks_by_project(project_id)
        gantt_tasks = []

        # Get critical path if dependency manager available
        critical_path = set()
        if self.dependency_manager:
            critical_path = set(self.dependency_manager.get_critical_path(project_id))

        for task in tasks:
            # Skip tasks without dates
            if not task.start_date or not task.due_date:
                continue

            gantt_task = GanttTask(
                task_id=task.id,
                name=task.name,
                start=task.start_date,
                end=task.due_date,
                progress=task.progress,
                resource=task.assignee,
                dependencies=task.dependencies.copy() if task.dependencies else [],
                color=self._get_color_for_priority(task.priority.value),
                is_critical=task.id in critical_path
            )

            gantt_tasks.append(gantt_task)

        return gantt_tasks

    def _get_color_for_priority(self, priority: str) -> str:
        """Get color based on priority."""
        color_map = {
            "low": "#10b981",
            "medium": "#3b82f6",
            "high": "#f59e0b",
            "urgent": "#ef4444"
        }
        return color_map.get(priority, "#6b7280")

    def create_plotly_gantt(
        self,
        project_id: str,
        show_dependencies: bool = True,
        show_critical_path: bool = True,
        show_baseline: bool = False,
        show_progress: bool = True,
        title: Optional[str] = None
    ) -> go.Figure:
        """
        Create an interactive Plotly Gantt chart.

        Args:
            project_id: Project identifier
            show_dependencies: Show dependency arrows
            show_critical_path: Highlight critical path
            show_baseline: Show baseline comparison
            show_progress: Show task progress
            title: Chart title

        Returns:
            Plotly Figure object
        """
        gantt_tasks = self.generate_gantt_data(project_id)

        if not gantt_tasks:
            # Return empty figure
            fig = go.Figure()
            fig.add_annotation(
                text="No tasks with dates to display",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig

        # Create figure
        fig = go.Figure()

        # Sort tasks by start date
        gantt_tasks.sort(key=lambda t: t.start)

        # Create task bars
        for i, task in enumerate(gantt_tasks):
            # Main task bar
            bar_color = "#ef4444" if show_critical_path and task.is_critical else task.color

            fig.add_trace(go.Bar(
                name=task.name,
                x=[task.duration_days],
                y=[task.name],
                orientation='h',
                marker=dict(
                    color=bar_color,
                    line=dict(color='rgba(0,0,0,0.3)', width=1)
                ),
                base=task.start,
                text=f"{task.progress:.0f}%" if show_progress else "",
                textposition='inside',
                hovertemplate=(
                    f"<b>{task.name}</b><br>"
                    f"Start: {task.start}<br>"
                    f"End: {task.end}<br>"
                    f"Duration: {task.duration_days} days<br>"
                    f"Progress: {task.progress:.0f}%<br>"
                    f"Resource: {task.resource or 'Unassigned'}<br>"
                    "<extra></extra>"
                ),
                showlegend=False
            ))

            # Progress bar overlay
            if show_progress and task.progress > 0:
                progress_days = int(task.duration_days * task.progress / 100)
                fig.add_trace(go.Bar(
                    x=[progress_days],
                    y=[task.name],
                    orientation='h',
                    marker=dict(
                        color='rgba(16, 185, 129, 0.6)',
                        line=dict(color='rgba(16, 185, 129, 0.8)', width=1)
                    ),
                    base=task.start,
                    showlegend=False,
                    hoverinfo='skip'
                ))

            # Baseline comparison
            if show_baseline and task.task_id in self.baseline_dates:
                baseline_start, baseline_end = self.baseline_dates[task.task_id]
                baseline_duration = (baseline_end - baseline_start).days + 1

                fig.add_trace(go.Bar(
                    x=[baseline_duration],
                    y=[task.name],
                    orientation='h',
                    marker=dict(
                        color='rgba(150, 150, 150, 0.3)',
                        line=dict(color='rgba(100, 100, 100, 0.5)', width=1, dash='dash')
                    ),
                    base=baseline_start,
                    showlegend=False,
                    hovertemplate=(
                        f"<b>Baseline</b><br>"
                        f"Start: {baseline_start}<br>"
                        f"End: {baseline_end}<br>"
                        "<extra></extra>"
                    )
                ))

        # Add dependency arrows
        if show_dependencies and self.dependency_manager:
            task_positions = {task.name: i for i, task in enumerate(gantt_tasks)}

            for task in gantt_tasks:
                if task.dependencies:
                    for dep_id in task.dependencies:
                        dep_task = next((t for t in gantt_tasks if t.task_id == dep_id), None)
                        if dep_task:
                            # Add arrow annotation
                            fig.add_annotation(
                                x=dep_task.end,
                                y=dep_task.name,
                                ax=task.start,
                                ay=task.name,
                                xref='x',
                                yref='y',
                                axref='x',
                                ayref='y',
                                showarrow=True,
                                arrowhead=2,
                                arrowsize=1,
                                arrowwidth=1,
                                arrowcolor='rgba(100, 100, 100, 0.5)'
                            )

        # Update layout
        fig.update_layout(
            title=title or f"Project Gantt Chart",
            xaxis=dict(
                title="Date",
                type='date',
                tickformat='%Y-%m-%d'
            ),
            yaxis=dict(
                title="Tasks",
                autorange="reversed"
            ),
            barmode='overlay',
            height=max(400, len(gantt_tasks) * 40),
            showlegend=False,
            hovermode='closest',
            plot_bgcolor='rgba(240, 240, 240, 0.5)',
            bargap=0.3
        )

        # Add today marker
        today = date.today()
        fig.add_vline(
            x=today.isoformat(),
            line_dash="dash",
            line_color="red",
            annotation_text="Today",
            annotation_position="top"
        )

        return fig

    def create_timeline_chart(
        self,
        project_id: str,
        group_by: str = "assignee"
    ) -> go.Figure:
        """
        Create a timeline chart grouped by resource or other criteria.

        Args:
            project_id: Project identifier
            group_by: Grouping criteria ("assignee", "priority", "status")

        Returns:
            Plotly Figure object
        """
        gantt_tasks = self.generate_gantt_data(project_id)

        if not gantt_tasks:
            fig = go.Figure()
            fig.add_annotation(
                text="No tasks with dates to display",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig

        # Group tasks
        groups: Dict[str, List[GanttTask]] = {}
        for task in gantt_tasks:
            if group_by == "assignee":
                key = task.resource or "Unassigned"
            elif group_by == "priority":
                # Get from task manager
                t = self.task_manager.get_task(task.task_id)
                key = t.priority.value if t else "medium"
            elif group_by == "status":
                t = self.task_manager.get_task(task.task_id)
                key = t.status.value if t else "todo"
            else:
                key = "All Tasks"

            if key not in groups:
                groups[key] = []
            groups[key].append(task)

        # Create timeline
        fig = go.Figure()

        for group_name, tasks in groups.items():
            for task in tasks:
                fig.add_trace(go.Scatter(
                    x=[task.start, task.end],
                    y=[group_name, group_name],
                    mode='lines+markers',
                    name=task.name,
                    line=dict(color=task.color, width=10),
                    marker=dict(size=8, color=task.color),
                    hovertemplate=(
                        f"<b>{task.name}</b><br>"
                        f"Start: {task.start}<br>"
                        f"End: {task.end}<br>"
                        f"Duration: {task.duration_days} days<br>"
                        "<extra></extra>"
                    )
                ))

        fig.update_layout(
            title=f"Timeline by {group_by.title()}",
            xaxis_title="Date",
            yaxis_title=group_by.title(),
            height=max(400, len(groups) * 60),
            showlegend=False,
            hovermode='closest'
        )

        # Add today marker
        today = date.today()
        fig.add_vline(
            x=today.isoformat(),
            line_dash="dash",
            line_color="red",
            annotation_text="Today"
        )

        return fig

    def set_baseline(self, project_id: str) -> None:
        """
        Set current schedule as baseline for comparison.

        Args:
            project_id: Project identifier
        """
        tasks = self.task_manager.get_tasks_by_project(project_id)

        for task in tasks:
            if task.start_date and task.due_date:
                self.baseline_dates[task.id] = (task.start_date, task.due_date)

    def clear_baseline(self, project_id: Optional[str] = None) -> None:
        """
        Clear baseline dates.

        Args:
            project_id: Project identifier (None = clear all)
        """
        if project_id:
            tasks = self.task_manager.get_tasks_by_project(project_id)
            for task in tasks:
                self.baseline_dates.pop(task.id, None)
        else:
            self.baseline_dates.clear()

    def export_to_image(self, fig: go.Figure, filepath: str, format: str = "png") -> None:
        """
        Export Gantt chart to image file.

        Args:
            fig: Plotly figure
            filepath: Output file path
            format: Image format (png, jpg, svg, pdf)
        """
        fig.write_image(filepath, format=format)

    def export_to_html(self, fig: go.Figure, filepath: str) -> None:
        """
        Export Gantt chart to interactive HTML.

        Args:
            fig: Plotly figure
            filepath: Output file path
        """
        fig.write_html(filepath)

    def get_task_slack(self, project_id: str) -> Dict[str, float]:
        """
        Calculate slack (float) time for all tasks.

        Args:
            project_id: Project identifier

        Returns:
            Dictionary mapping task IDs to slack days
        """
        if not self.dependency_manager:
            return {}

        tasks = self.task_manager.get_tasks_by_project(project_id)
        task_ids = [t.id for t in tasks]

        # Get critical path
        critical_path = set(self.dependency_manager.get_critical_path(project_id))

        slack = {}
        for task_id in task_ids:
            if task_id in critical_path:
                slack[task_id] = 0.0
            else:
                # Calculate based on earliest and latest start
                # This is a simplified calculation
                task = self.task_manager.get_task(task_id)
                if task and task.start_date and task.due_date:
                    # Get all dependents
                    dependents = self.dependency_manager.get_dependents(task_id)
                    if dependents:
                        # Calculate slack based on dependent's earliest start
                        min_dependent_start = None
                        for dep in dependents:
                            dep_task = self.task_manager.get_task(dep.successor_id)
                            if dep_task and dep_task.start_date:
                                if min_dependent_start is None or dep_task.start_date < min_dependent_start:
                                    min_dependent_start = dep_task.start_date

                        if min_dependent_start:
                            slack[task_id] = (min_dependent_start - task.due_date).days - 1
                        else:
                            slack[task_id] = 0.0
                    else:
                        slack[task_id] = 0.0

        return slack

    def create_resource_load_chart(self, project_id: str) -> go.Figure:
        """
        Create a resource workload chart.

        Args:
            project_id: Project identifier

        Returns:
            Plotly Figure object
        """
        gantt_tasks = self.generate_gantt_data(project_id)

        # Calculate daily workload per resource
        resource_load: Dict[str, Dict[date, float]] = {}

        for task in gantt_tasks:
            resource = task.resource or "Unassigned"
            if resource not in resource_load:
                resource_load[resource] = {}

            # Distribute hours across task duration
            total_task = self.task_manager.get_task(task.task_id)
            if total_task:
                hours_per_day = total_task.estimated_hours / max(1, task.duration_days)

                current_date = task.start
                while current_date <= task.end:
                    if current_date not in resource_load[resource]:
                        resource_load[resource][current_date] = 0.0
                    resource_load[resource][current_date] += hours_per_day
                    current_date += timedelta(days=1)

        # Create stacked area chart
        fig = go.Figure()

        for resource, daily_load in resource_load.items():
            dates = sorted(daily_load.keys())
            loads = [daily_load[d] for d in dates]

            fig.add_trace(go.Scatter(
                x=dates,
                y=loads,
                mode='lines',
                name=resource,
                stackgroup='one',
                hovertemplate=f"<b>{resource}</b><br>Hours: %{{y:.1f}}<br><extra></extra>"
            ))

        fig.update_layout(
            title="Resource Workload Over Time",
            xaxis_title="Date",
            yaxis_title="Hours per Day",
            hovermode='x unified',
            height=500
        )

        # Add 8-hour reference line
        fig.add_hline(
            y=8,
            line_dash="dash",
            line_color="red",
            annotation_text="8 hours/day"
        )

        return fig

    def create_milestone_chart(self, project_id: str, milestone_manager) -> go.Figure:
        """
        Create a milestone timeline chart.

        Args:
            project_id: Project identifier
            milestone_manager: Milestone manager instance

        Returns:
            Plotly Figure object
        """
        milestones = milestone_manager.get_milestones_by_project(project_id)

        if not milestones:
            fig = go.Figure()
            fig.add_annotation(
                text="No milestones to display",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig

        fig = go.Figure()

        # Sort by due date
        milestones.sort(key=lambda m: m.due_date or date.max)

        for milestone in milestones:
            if milestone.due_date:
                color = "#10b981" if milestone.is_completed else "#3b82f6"

                fig.add_trace(go.Scatter(
                    x=[milestone.due_date],
                    y=[milestone.name],
                    mode='markers',
                    marker=dict(
                        size=20,
                        color=color,
                        symbol='diamond',
                        line=dict(color='white', width=2)
                    ),
                    name=milestone.name,
                    hovertemplate=(
                        f"<b>{milestone.name}</b><br>"
                        f"Due: {milestone.due_date}<br>"
                        f"Status: {'Completed' if milestone.is_completed else 'Pending'}<br>"
                        f"Progress: {milestone.progress:.0f}%<br>"
                        "<extra></extra>"
                    )
                ))

        fig.update_layout(
            title="Project Milestones",
            xaxis_title="Date",
            yaxis_title="Milestone",
            height=max(300, len(milestones) * 60),
            showlegend=False,
            yaxis=dict(autorange="reversed")
        )

        # Add today marker
        today = date.today()
        fig.add_vline(
            x=today.isoformat(),
            line_dash="dash",
            line_color="red",
            annotation_text="Today"
        )

        return fig
