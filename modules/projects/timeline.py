"""
NEXUS Timeline Module
Timeline views for projects and tasks with filtering and grouping.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import date, datetime, timedelta
from enum import Enum
import plotly.graph_objects as go
from plotly.subplots import make_subplots


class TimelineViewType(Enum):
    """Timeline view types."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class TimelineEvent:
    """
    Represents an event on the timeline.

    Attributes:
        id: Event identifier
        title: Event title
        description: Event description
        start_date: Start date
        end_date: End date (None for single-day events)
        event_type: Type of event (task, milestone, meeting, etc.)
        color: Event color
        metadata: Additional metadata
    """

    def __init__(
        self,
        title: str,
        start_date: date,
        event_type: str = "task",
        end_date: Optional[date] = None,
        description: str = "",
        color: str = "#3b82f6",
        metadata: Optional[Dict[str, Any]] = None,
        event_id: Optional[str] = None
    ):
        """Initialize a timeline event."""
        import uuid
        self.id: str = event_id or str(uuid.uuid4())
        self.title: str = title
        self.description: str = description
        self.start_date: date = start_date
        self.end_date: Optional[date] = end_date
        self.event_type: str = event_type
        self.color: str = color
        self.metadata: Dict[str, Any] = metadata or {}

    @property
    def is_single_day(self) -> bool:
        """Check if event is a single-day event."""
        return self.end_date is None or self.start_date == self.end_date

    @property
    def duration_days(self) -> int:
        """Calculate event duration in days."""
        if self.is_single_day:
            return 1
        return (self.end_date - self.start_date).days + 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "event_type": self.event_type,
            "color": self.color,
            "metadata": self.metadata
        }


class TimelineManager:
    """
    Timeline view manager.
    Creates and manages timeline views for projects.
    """

    def __init__(self, task_manager, milestone_manager=None):
        """
        Initialize the timeline manager.

        Args:
            task_manager: Task manager instance
            milestone_manager: Milestone manager instance (optional)
        """
        self.task_manager = task_manager
        self.milestone_manager = milestone_manager

    def get_project_events(self, project_id: str) -> List[TimelineEvent]:
        """
        Get all timeline events for a project.

        Args:
            project_id: Project identifier

        Returns:
            List of timeline events
        """
        events = []

        # Add tasks
        tasks = self.task_manager.get_tasks_by_project(project_id)
        for task in tasks:
            if task.start_date and task.due_date:
                event = TimelineEvent(
                    title=task.name,
                    start_date=task.start_date,
                    end_date=task.due_date,
                    description=task.description,
                    event_type="task",
                    color=self._get_task_color(task),
                    metadata={
                        "task_id": task.id,
                        "status": task.status.value,
                        "priority": task.priority.value,
                        "assignee": task.assignee
                    }
                )
                events.append(event)

        # Add milestones
        if self.milestone_manager:
            milestones = self.milestone_manager.get_milestones_by_project(project_id)
            for milestone in milestones:
                if milestone.due_date:
                    event = TimelineEvent(
                        title=f"🎯 {milestone.name}",
                        start_date=milestone.due_date,
                        event_type="milestone",
                        description=milestone.description,
                        color="#10b981" if milestone.is_completed else "#f59e0b",
                        metadata={
                            "milestone_id": milestone.id,
                            "progress": milestone.progress
                        }
                    )
                    events.append(event)

        return events

    def _get_task_color(self, task) -> str:
        """Get color for a task based on its properties."""
        if task.is_overdue():
            return "#ef4444"  # Red for overdue

        status_colors = {
            "todo": "#6b7280",
            "in_progress": "#3b82f6",
            "done": "#10b981",
            "blocked": "#f59e0b",
            "cancelled": "#9ca3af"
        }

        return status_colors.get(task.status.value, "#6b7280")

    def create_timeline_view(
        self,
        project_id: str,
        view_type: TimelineViewType = TimelineViewType.MONTH,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        group_by: Optional[str] = None
    ) -> go.Figure:
        """
        Create a timeline view.

        Args:
            project_id: Project identifier
            view_type: Type of view (day, week, month, etc.)
            start_date: View start date (None = auto)
            end_date: View end date (None = auto)
            group_by: Group events by field (assignee, priority, status)

        Returns:
            Plotly Figure object
        """
        events = self.get_project_events(project_id)

        if not events:
            fig = go.Figure()
            fig.add_annotation(
                text="No events to display",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig

        # Determine date range if not provided
        if not start_date:
            start_date = min(e.start_date for e in events)
        if not end_date:
            end_date = max(e.end_date or e.start_date for e in events)

        # Group events if requested
        if group_by:
            grouped_events = self._group_events(events, group_by)
        else:
            grouped_events = {"All Events": events}

        # Create figure
        fig = go.Figure()

        # Track y-positions for non-overlapping display
        y_positions: Dict[str, List[Tuple[date, date, int]]] = {
            group: [] for group in grouped_events.keys()
        }

        for group_idx, (group_name, group_events) in enumerate(grouped_events.items()):
            # Sort events by start date
            group_events.sort(key=lambda e: e.start_date)

            for event in group_events:
                # Find non-overlapping y-position
                y_pos = self._find_y_position(
                    event.start_date,
                    event.end_date or event.start_date,
                    y_positions[group_name]
                )

                if event.is_single_day:
                    # Single-day event - show as marker
                    fig.add_trace(go.Scatter(
                        x=[event.start_date],
                        y=[f"{group_name} - {y_pos}"],
                        mode='markers+text',
                        name=event.title,
                        marker=dict(
                            size=15,
                            color=event.color,
                            symbol='diamond' if event.event_type == 'milestone' else 'circle',
                            line=dict(color='white', width=2)
                        ),
                        text=event.title,
                        textposition='top center',
                        hovertemplate=(
                            f"<b>{event.title}</b><br>"
                            f"Date: {event.start_date}<br>"
                            f"{event.description}<br>"
                            "<extra></extra>"
                        ),
                        showlegend=False
                    ))
                else:
                    # Multi-day event - show as bar
                    fig.add_trace(go.Scatter(
                        x=[event.start_date, event.end_date],
                        y=[f"{group_name} - {y_pos}", f"{group_name} - {y_pos}"],
                        mode='lines+text',
                        name=event.title,
                        line=dict(color=event.color, width=15),
                        text=[event.title, ""],
                        textposition='middle center',
                        hovertemplate=(
                            f"<b>{event.title}</b><br>"
                            f"Start: {event.start_date}<br>"
                            f"End: {event.end_date}<br>"
                            f"Duration: {event.duration_days} days<br>"
                            f"{event.description}<br>"
                            "<extra></extra>"
                        ),
                        showlegend=False
                    ))

        # Update layout
        fig.update_layout(
            title=f"Project Timeline - {view_type.value.title()} View",
            xaxis=dict(
                title="Date",
                type='date',
                range=[start_date, end_date],
                tickformat=self._get_tick_format(view_type)
            ),
            yaxis=dict(
                title="Events",
                showticklabels=len(grouped_events) > 1
            ),
            height=max(400, len(events) * 30),
            hovermode='closest',
            plot_bgcolor='rgba(240, 240, 240, 0.5)'
        )

        # Add today marker
        today = date.today()
        if start_date <= today <= end_date:
            fig.add_vline(
                x=today.isoformat(),
                line_dash="dash",
                line_color="red",
                annotation_text="Today",
                annotation_position="top"
            )

        return fig

    def _group_events(self, events: List[TimelineEvent], group_by: str) -> Dict[str, List[TimelineEvent]]:
        """Group events by specified criteria."""
        groups: Dict[str, List[TimelineEvent]] = {}

        for event in events:
            if event.event_type == "milestone":
                key = "Milestones"
            elif group_by in event.metadata:
                key = str(event.metadata[group_by]) or "Unassigned"
            else:
                key = "Other"

            if key not in groups:
                groups[key] = []
            groups[key].append(event)

        return groups

    def _find_y_position(
        self,
        start: date,
        end: date,
        existing: List[Tuple[date, date, int]]
    ) -> int:
        """Find non-overlapping y-position for an event."""
        if not existing:
            existing.append((start, end, 0))
            return 0

        # Check each y-level
        for y in range(len(existing) + 1):
            # Check if this level has overlap
            has_overlap = False
            for ex_start, ex_end, ex_y in existing:
                if ex_y == y:
                    # Check date overlap
                    if not (end < ex_start or start > ex_end):
                        has_overlap = True
                        break

            if not has_overlap:
                existing.append((start, end, y))
                return y

        # Shouldn't reach here
        existing.append((start, end, len(existing)))
        return len(existing) - 1

    def _get_tick_format(self, view_type: TimelineViewType) -> str:
        """Get tick format for view type."""
        formats = {
            TimelineViewType.DAY: "%Y-%m-%d",
            TimelineViewType.WEEK: "%Y-%m-%d",
            TimelineViewType.MONTH: "%Y-%m",
            TimelineViewType.QUARTER: "%Y-Q%q",
            TimelineViewType.YEAR: "%Y"
        }
        return formats.get(view_type, "%Y-%m-%d")

    def create_calendar_view(
        self,
        project_id: str,
        year: int,
        month: int
    ) -> go.Figure:
        """
        Create a calendar month view.

        Args:
            project_id: Project identifier
            year: Year
            month: Month (1-12)

        Returns:
            Plotly Figure object
        """
        events = self.get_project_events(project_id)

        # Filter events for this month
        start_of_month = date(year, month, 1)
        if month == 12:
            end_of_month = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_of_month = date(year, month + 1, 1) - timedelta(days=1)

        month_events = [
            e for e in events
            if e.start_date <= end_of_month and (e.end_date or e.start_date) >= start_of_month
        ]

        # Create calendar grid
        fig = go.Figure()

        # Build calendar days
        current_date = start_of_month
        weeks = []
        current_week = [None] * current_date.weekday()  # Fill leading days

        while current_date <= end_of_month:
            # Get events for this day
            day_events = [
                e for e in month_events
                if e.start_date <= current_date <= (e.end_date or e.start_date)
            ]

            current_week.append({
                "date": current_date,
                "events": day_events
            })

            if len(current_week) == 7:
                weeks.append(current_week)
                current_week = []

            current_date += timedelta(days=1)

        # Fill trailing days
        if current_week:
            current_week.extend([None] * (7 - len(current_week)))
            weeks.append(current_week)

        # Create calendar visualization
        for week_idx, week in enumerate(weeks):
            for day_idx, day_data in enumerate(week):
                if day_data is None:
                    continue

                day_date = day_data["date"]
                day_events = day_data["events"]

                # Determine cell color
                if day_events:
                    cell_color = "lightblue"
                    event_count = len(day_events)
                else:
                    cell_color = "white"
                    event_count = 0

                # Add cell
                fig.add_trace(go.Scatter(
                    x=[day_idx],
                    y=[len(weeks) - week_idx - 1],
                    mode='markers+text',
                    marker=dict(
                        size=60,
                        color=cell_color,
                        symbol='square',
                        line=dict(color='gray', width=1)
                    ),
                    text=f"{day_date.day}<br>({event_count})",
                    textposition='middle center',
                    hovertemplate=(
                        f"<b>{day_date.strftime('%B %d, %Y')}</b><br>"
                        f"Events: {event_count}<br>"
                        + "<br>".join([e.title for e in day_events[:3]])
                        + ("<br>..." if event_count > 3 else "")
                        + "<extra></extra>"
                    ),
                    showlegend=False
                ))

        # Update layout
        fig.update_layout(
            title=f"Calendar - {start_of_month.strftime('%B %Y')}",
            xaxis=dict(
                tickmode='array',
                tickvals=list(range(7)),
                ticktext=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                showgrid=False
            ),
            yaxis=dict(
                showticklabels=False,
                showgrid=False
            ),
            height=600,
            width=800,
            hovermode='closest',
            plot_bgcolor='white'
        )

        return fig

    def get_upcoming_events(
        self,
        project_id: str,
        days: int = 7
    ) -> List[TimelineEvent]:
        """
        Get upcoming events for a project.

        Args:
            project_id: Project identifier
            days: Number of days to look ahead

        Returns:
            List of upcoming events
        """
        events = self.get_project_events(project_id)
        today = date.today()
        future_date = today + timedelta(days=days)

        upcoming = [
            e for e in events
            if today <= e.start_date <= future_date
        ]

        return sorted(upcoming, key=lambda e: e.start_date)

    def get_overdue_events(self, project_id: str) -> List[TimelineEvent]:
        """
        Get overdue events for a project.

        Args:
            project_id: Project identifier

        Returns:
            List of overdue events
        """
        events = self.get_project_events(project_id)
        today = date.today()

        overdue = [
            e for e in events
            if e.event_type == "task"
            and (e.end_date or e.start_date) < today
            and e.metadata.get("status") not in ["done", "cancelled"]
        ]

        return sorted(overdue, key=lambda e: e.end_date or e.start_date)
