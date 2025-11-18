"""
NEXUS Reporting Module
Project reports, dashboards, analytics, and data export.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import date, datetime, timedelta
from enum import Enum
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import csv
from io import StringIO


class ReportType(Enum):
    """Report types."""
    PROJECT_SUMMARY = "project_summary"
    TASK_STATUS = "task_status"
    RESOURCE_UTILIZATION = "resource_utilization"
    BUDGET_VARIANCE = "budget_variance"
    TIME_TRACKING = "time_tracking"
    BURNDOWN = "burndown"
    VELOCITY = "velocity"
    CUSTOM = "custom"


class ReportingManager:
    """
    Reporting and analytics engine.
    Generates reports, dashboards, and data exports.
    """

    def __init__(
        self,
        project_manager,
        task_manager,
        resource_manager=None,
        time_tracking_manager=None,
        budget_manager=None,
        milestone_manager=None
    ):
        """
        Initialize the reporting manager.

        Args:
            project_manager: Project manager instance
            task_manager: Task manager instance
            resource_manager: Resource manager instance (optional)
            time_tracking_manager: Time tracking manager instance (optional)
            budget_manager: Budget manager instance (optional)
            milestone_manager: Milestone manager instance (optional)
        """
        self.project_manager = project_manager
        self.task_manager = task_manager
        self.resource_manager = resource_manager
        self.time_tracking_manager = time_tracking_manager
        self.budget_manager = budget_manager
        self.milestone_manager = milestone_manager

    def generate_project_summary(self, project_id: str) -> Dict[str, Any]:
        """
        Generate a comprehensive project summary report.

        Args:
            project_id: Project identifier

        Returns:
            Project summary dictionary
        """
        project = self.project_manager.get_project(project_id)
        if not project:
            return {"error": "Project not found"}

        # Get tasks
        tasks = self.task_manager.get_tasks_by_project(project_id)

        # Calculate task statistics
        task_stats = self.task_manager.get_task_statistics(project_id)

        # Get milestones
        milestones = []
        if self.milestone_manager:
            milestones = self.milestone_manager.get_milestones_by_project(project_id)

        # Get budget info
        budget_info = None
        if self.budget_manager:
            budget_info = self.budget_manager.get_budget_utilization(project_id)

        # Get time tracking info
        time_info = None
        if self.time_tracking_manager:
            time_info = self.time_tracking_manager.get_project_time_summary(project_id)

        # Calculate progress
        progress = project.get_progress(self.task_manager)

        return {
            "project": project.to_dict(),
            "progress": progress,
            "task_statistics": task_stats,
            "milestone_count": len(milestones),
            "milestones_completed": sum(1 for m in milestones if m.is_completed),
            "budget": budget_info,
            "time_tracking": time_info,
            "generated_at": datetime.now().isoformat()
        }

    def generate_task_status_report(
        self,
        project_id: str,
        group_by: str = "status"
    ) -> Dict[str, Any]:
        """
        Generate a task status report.

        Args:
            project_id: Project identifier
            group_by: Group tasks by (status, priority, assignee)

        Returns:
            Task status report dictionary
        """
        tasks = self.task_manager.get_tasks_by_project(project_id)

        grouped: Dict[str, List] = {}

        for task in tasks:
            if group_by == "status":
                key = task.status.value
            elif group_by == "priority":
                key = task.priority.value
            elif group_by == "assignee":
                key = task.assignee or "Unassigned"
            else:
                key = "All"

            if key not in grouped:
                grouped[key] = []
            grouped[key].append(task.to_dict())

        # Calculate summaries
        summaries = {}
        for key, group_tasks in grouped.items():
            summaries[key] = {
                "count": len(group_tasks),
                "estimated_hours": sum(t.get("estimated_hours", 0) for t in group_tasks),
                "actual_hours": sum(t.get("actual_hours", 0) for t in group_tasks),
                "progress": sum(t.get("progress", 0) for t in group_tasks) / len(group_tasks) if group_tasks else 0
            }

        return {
            "project_id": project_id,
            "group_by": group_by,
            "grouped_tasks": grouped,
            "summaries": summaries,
            "total_tasks": len(tasks),
            "generated_at": datetime.now().isoformat()
        }

    def generate_burndown_chart(
        self,
        project_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> go.Figure:
        """
        Generate a burndown chart for a project.

        Args:
            project_id: Project identifier
            start_date: Chart start date
            end_date: Chart end date

        Returns:
            Plotly Figure object
        """
        project = self.project_manager.get_project(project_id)
        tasks = self.task_manager.get_tasks_by_project(project_id)

        if not project or not tasks:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available for burndown chart",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig

        # Determine date range
        if not start_date:
            start_date = project.start_date or min(
                (t.start_date for t in tasks if t.start_date),
                default=date.today()
            )

        if not end_date:
            end_date = project.end_date or max(
                (t.due_date for t in tasks if t.due_date),
                default=date.today()
            )

        # Calculate total story points (using estimated hours as proxy)
        total_points = sum(t.estimated_hours for t in tasks)

        # Calculate ideal burndown line
        total_days = (end_date - start_date).days + 1
        ideal_line = []
        dates = []

        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date)
            days_elapsed = (current_date - start_date).days
            remaining = total_points * (1 - days_elapsed / max(1, total_days))
            ideal_line.append(max(0, remaining))
            current_date += timedelta(days=1)

        # Calculate actual burndown (simplified - would need historical data)
        actual_line = []
        for current_date in dates:
            # Count remaining work (tasks not done by this date)
            remaining_work = sum(
                t.estimated_hours for t in tasks
                if not (t.status.value == "done" and t.completed_at and t.completed_at.date() <= current_date)
            )
            actual_line.append(remaining_work)

        # Create figure
        fig = go.Figure()

        # Add ideal line
        fig.add_trace(go.Scatter(
            x=dates,
            y=ideal_line,
            mode='lines',
            name='Ideal Burndown',
            line=dict(color='blue', dash='dash')
        ))

        # Add actual line
        fig.add_trace(go.Scatter(
            x=dates,
            y=actual_line,
            mode='lines+markers',
            name='Actual Burndown',
            line=dict(color='red')
        ))

        # Add today marker
        today = date.today()
        if start_date <= today <= end_date:
            fig.add_vline(
                x=today.isoformat(),
                line_dash="dash",
                line_color="green",
                annotation_text="Today"
            )

        fig.update_layout(
            title=f"Burndown Chart - {project.name}",
            xaxis_title="Date",
            yaxis_title="Remaining Work (hours)",
            hovermode='x unified',
            height=500
        )

        return fig

    def generate_velocity_chart(
        self,
        project_id: str,
        weeks: int = 4
    ) -> go.Figure:
        """
        Generate a velocity chart showing completed work over time.

        Args:
            project_id: Project identifier
            weeks: Number of weeks to include

        Returns:
            Plotly Figure object
        """
        tasks = self.task_manager.get_tasks_by_project(project_id)

        # Calculate weekly velocity
        end_date = date.today()
        start_date = end_date - timedelta(weeks=weeks)

        weekly_velocity = []
        week_labels = []

        for week in range(weeks):
            week_start = start_date + timedelta(weeks=week)
            week_end = week_start + timedelta(days=6)

            # Count completed work in this week
            completed_work = sum(
                t.estimated_hours for t in tasks
                if t.status.value == "done"
                and t.completed_at
                and week_start <= t.completed_at.date() <= week_end
            )

            weekly_velocity.append(completed_work)
            week_labels.append(f"Week of {week_start.strftime('%m/%d')}")

        # Calculate average velocity
        avg_velocity = sum(weekly_velocity) / len(weekly_velocity) if weekly_velocity else 0

        # Create figure
        fig = go.Figure()

        # Add velocity bars
        fig.add_trace(go.Bar(
            x=week_labels,
            y=weekly_velocity,
            name='Velocity',
            marker_color='lightblue'
        ))

        # Add average line
        fig.add_hline(
            y=avg_velocity,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Average: {avg_velocity:.1f} hrs/week",
            annotation_position="right"
        )

        fig.update_layout(
            title="Team Velocity",
            xaxis_title="Week",
            yaxis_title="Completed Work (hours)",
            height=400
        )

        return fig

    def generate_resource_utilization_chart(
        self,
        project_id: str,
        start_date: date,
        end_date: date
    ) -> go.Figure:
        """
        Generate a resource utilization chart.

        Args:
            project_id: Project identifier
            start_date: Chart start date
            end_date: Chart end date

        Returns:
            Plotly Figure object
        """
        if not self.resource_manager:
            fig = go.Figure()
            fig.add_annotation(
                text="Resource manager not available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig

        # Get capacity report
        report = self.resource_manager.generate_capacity_report(start_date, end_date)

        resources = report["resources"]
        names = [r["name"] for r in resources]
        utilizations = [r["utilization_percentage"] for r in resources]

        # Color code by utilization
        colors = []
        for util in utilizations:
            if util > 100:
                colors.append('red')  # Overallocated
            elif util > 80:
                colors.append('orange')  # Near capacity
            else:
                colors.append('green')  # Available capacity

        # Create figure
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=names,
            y=utilizations,
            marker_color=colors,
            text=[f"{u:.1f}%" for u in utilizations],
            textposition='outside'
        ))

        # Add 100% reference line
        fig.add_hline(
            y=100,
            line_dash="dash",
            line_color="black",
            annotation_text="100% Capacity"
        )

        fig.update_layout(
            title="Resource Utilization",
            xaxis_title="Resource",
            yaxis_title="Utilization (%)",
            height=500
        )

        return fig

    def create_dashboard(self, project_id: str) -> Dict[str, Any]:
        """
        Create a comprehensive project dashboard.

        Args:
            project_id: Project identifier

        Returns:
            Dashboard data dictionary with charts and metrics
        """
        summary = self.generate_project_summary(project_id)
        task_stats = self.task_manager.get_task_statistics(project_id)

        dashboard = {
            "project_id": project_id,
            "summary": summary,
            "metrics": {
                "tasks": task_stats,
                "completion_rate": (
                    task_stats["by_status"].get("done", 0) / task_stats["total_tasks"] * 100
                    if task_stats["total_tasks"] > 0 else 0
                ),
            },
            "generated_at": datetime.now().isoformat()
        }

        return dashboard

    def export_to_csv(self, project_id: str, export_type: str = "tasks") -> str:
        """
        Export project data to CSV format.

        Args:
            project_id: Project identifier
            export_type: Type of data to export (tasks, time, expenses)

        Returns:
            CSV string
        """
        output = StringIO()
        writer = csv.writer(output)

        if export_type == "tasks":
            tasks = self.task_manager.get_tasks_by_project(project_id)

            # Write header
            writer.writerow([
                "ID", "Name", "Status", "Priority", "Assignee",
                "Start Date", "Due Date", "Estimated Hours", "Actual Hours",
                "Progress", "Created At"
            ])

            # Write data
            for task in tasks:
                writer.writerow([
                    task.id,
                    task.name,
                    task.status.value,
                    task.priority.value,
                    task.assignee or "",
                    task.start_date.isoformat() if task.start_date else "",
                    task.due_date.isoformat() if task.due_date else "",
                    task.estimated_hours,
                    task.actual_hours,
                    task.progress,
                    task.created_at.isoformat()
                ])

        elif export_type == "time" and self.time_tracking_manager:
            entries = self.time_tracking_manager.get_time_entries_by_project(project_id)

            writer.writerow([
                "ID", "Task ID", "User ID", "Duration (hours)",
                "Date", "Is Billable", "Status", "Description"
            ])

            for entry in entries:
                entry_date = entry.start_time.date() if entry.start_time else entry.created_at.date()
                writer.writerow([
                    entry.id,
                    entry.task_id,
                    entry.user_id,
                    entry.duration_hours,
                    entry_date.isoformat(),
                    entry.is_billable,
                    entry.status.value,
                    entry.description
                ])

        elif export_type == "expenses" and self.budget_manager:
            expenses = self.budget_manager.get_project_expenses(project_id)

            writer.writerow([
                "ID", "Category", "Amount", "Currency", "Vendor",
                "Date", "Status", "Description"
            ])

            for expense in expenses:
                writer.writerow([
                    expense.id,
                    expense.category.value,
                    expense.amount,
                    expense.currency,
                    expense.vendor,
                    expense.date.isoformat(),
                    expense.status.value,
                    expense.description
                ])

        return output.getvalue()

    def export_to_json(self, project_id: str) -> str:
        """
        Export complete project data to JSON.

        Args:
            project_id: Project identifier

        Returns:
            JSON string
        """
        project = self.project_manager.get_project(project_id)
        tasks = self.task_manager.get_tasks_by_project(project_id)

        data = {
            "project": project.to_dict() if project else None,
            "tasks": [t.to_dict() for t in tasks],
        }

        # Add milestones if available
        if self.milestone_manager:
            milestones = self.milestone_manager.get_milestones_by_project(project_id)
            data["milestones"] = [m.to_dict() for m in milestones]

        # Add budget if available
        if self.budget_manager:
            budget = self.budget_manager.get_project_budget(project_id)
            if budget:
                data["budget"] = budget.to_dict()

            expenses = self.budget_manager.get_project_expenses(project_id)
            data["expenses"] = [e.to_dict() for e in expenses]

        # Add time entries if available
        if self.time_tracking_manager:
            time_entries = self.time_tracking_manager.get_time_entries_by_project(project_id)
            data["time_entries"] = [e.to_dict() for e in time_entries]

        return json.dumps(data, indent=2)

    def generate_custom_report(
        self,
        project_id: str,
        metrics: List[str],
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a custom report with specified metrics.

        Args:
            project_id: Project identifier
            metrics: List of metrics to include
            filters: Optional filters to apply

        Returns:
            Custom report dictionary
        """
        report = {
            "project_id": project_id,
            "metrics": {},
            "generated_at": datetime.now().isoformat()
        }

        tasks = self.task_manager.get_tasks_by_project(project_id)

        # Apply filters
        if filters:
            if "status" in filters:
                tasks = [t for t in tasks if t.status.value == filters["status"]]
            if "priority" in filters:
                tasks = [t for t in tasks if t.priority.value == filters["priority"]]
            if "assignee" in filters:
                tasks = [t for t in tasks if t.assignee == filters["assignee"]]

        # Calculate requested metrics
        for metric in metrics:
            if metric == "task_count":
                report["metrics"]["task_count"] = len(tasks)

            elif metric == "completion_rate":
                completed = sum(1 for t in tasks if t.status.value == "done")
                report["metrics"]["completion_rate"] = (
                    completed / len(tasks) * 100 if tasks else 0
                )

            elif metric == "avg_progress":
                report["metrics"]["avg_progress"] = (
                    sum(t.progress for t in tasks) / len(tasks) if tasks else 0
                )

            elif metric == "total_estimated_hours":
                report["metrics"]["total_estimated_hours"] = sum(t.estimated_hours for t in tasks)

            elif metric == "total_actual_hours":
                report["metrics"]["total_actual_hours"] = sum(t.actual_hours for t in tasks)

            elif metric == "overdue_count":
                report["metrics"]["overdue_count"] = sum(1 for t in tasks if t.is_overdue())

        return report
