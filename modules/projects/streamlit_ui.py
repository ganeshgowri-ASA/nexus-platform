"""
NEXUS Project Management Streamlit UI
Comprehensive web interface for the NEXUS project management system.
"""

import streamlit as st
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any
import pandas as pd

# Import project modules
from .project_manager import ProjectManager, Project, ProjectStatus, ProjectPriority
from .task_manager import TaskManager, Task, TaskStatus, TaskPriority, RecurrencePattern
from .dependencies import DependencyManager, DependencyType
from .kanban import KanbanManager
from .gantt import GanttChart
from .timeline import TimelineManager, TimelineViewType
from .resource_manager import ResourceManager, ExpenseCategory
from .milestones import MilestoneManager
from .time_tracking import TimeTrackingManager
from .budget import BudgetManager, ExpenseCategory, ExpenseStatus
from .collaboration import CollaborationManager, ActivityType
from .reporting import ReportingManager, ReportType
from .ai_assistant import AIProjectAssistant


class ProjectManagementUI:
    """
    Streamlit UI for NEXUS Project Management.
    Provides a comprehensive web interface for all project management features.
    """

    def __init__(self):
        """Initialize the project management UI."""
        self.initialize_session_state()
        self.initialize_managers()

    def initialize_session_state(self):
        """Initialize Streamlit session state."""
        if 'current_view' not in st.session_state:
            st.session_state.current_view = 'dashboard'
        if 'selected_project' not in st.session_state:
            st.session_state.selected_project = None
        if 'selected_task' not in st.session_state:
            st.session_state.selected_task = None

    def initialize_managers(self):
        """Initialize all manager instances."""
        if 'project_manager' not in st.session_state:
            st.session_state.project_manager = ProjectManager()
            st.session_state.task_manager = TaskManager()
            st.session_state.dependency_manager = DependencyManager(st.session_state.task_manager)
            st.session_state.kanban_manager = KanbanManager(st.session_state.task_manager)
            st.session_state.resource_manager = ResourceManager(st.session_state.task_manager)
            st.session_state.milestone_manager = MilestoneManager(st.session_state.task_manager)
            st.session_state.time_tracking_manager = TimeTrackingManager(st.session_state.task_manager)
            st.session_state.budget_manager = BudgetManager(st.session_state.resource_manager)
            st.session_state.collaboration_manager = CollaborationManager()

            # Initialize reporting and AI
            st.session_state.reporting_manager = ReportingManager(
                st.session_state.project_manager,
                st.session_state.task_manager,
                st.session_state.resource_manager,
                st.session_state.time_tracking_manager,
                st.session_state.budget_manager,
                st.session_state.milestone_manager
            )

            st.session_state.ai_assistant = AIProjectAssistant(
                st.session_state.project_manager,
                st.session_state.task_manager,
                st.session_state.dependency_manager,
                st.session_state.resource_manager,
                st.session_state.time_tracking_manager,
                st.session_state.budget_manager
            )

            # Create demo data
            self.create_demo_data()

    def create_demo_data(self):
        """Create demo project and tasks."""
        # Create demo project
        demo_project = st.session_state.project_manager.create_project(
            name="Website Redesign",
            description="Complete redesign of company website",
            status=ProjectStatus.ACTIVE,
            priority=ProjectPriority.HIGH,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=90),
            budget=50000.0
        )

        # Create demo tasks
        tasks_data = [
            ("Requirements Gathering", "Gather and document requirements", 40, 1),
            ("Design Mockups", "Create design mockups", 80, 3),
            ("Frontend Development", "Develop frontend components", 120, 7),
            ("Backend Development", "Develop backend APIs", 100, 7),
            ("Testing", "QA and testing", 60, 5),
            ("Deployment", "Deploy to production", 20, 2)
        ]

        for name, desc, hours, days_offset in tasks_data:
            st.session_state.task_manager.create_task(
                project_id=demo_project.id,
                name=name,
                description=desc,
                priority=TaskPriority.MEDIUM,
                start_date=date.today() + timedelta(days=days_offset),
                due_date=date.today() + timedelta(days=days_offset + 14),
                estimated_hours=hours
            )

        st.session_state.selected_project = demo_project.id

    def render(self):
        """Render the main UI."""
        st.set_page_config(
            page_title="NEXUS Project Management",
            page_icon="📊",
            layout="wide"
        )

        # Sidebar navigation
        with st.sidebar:
            st.title("🚀 NEXUS PM")
            st.markdown("---")

            # Project selector
            projects = st.session_state.project_manager.list_projects()
            if projects:
                project_names = {p.id: p.name for p in projects}
                selected_project_id = st.selectbox(
                    "Select Project",
                    options=list(project_names.keys()),
                    format_func=lambda x: project_names[x],
                    key="project_selector"
                )
                st.session_state.selected_project = selected_project_id
            else:
                st.warning("No projects available")

            st.markdown("---")

            # View navigation
            st.subheader("Navigation")
            views = {
                "📊 Dashboard": "dashboard",
                "📋 Tasks": "tasks",
                "📅 Kanban": "kanban",
                "📈 Gantt Chart": "gantt",
                "🗓️ Timeline": "timeline",
                "🎯 Milestones": "milestones",
                "👥 Resources": "resources",
                "⏱️ Time Tracking": "time_tracking",
                "💰 Budget": "budget",
                "💬 Collaboration": "collaboration",
                "📊 Reports": "reports",
                "🤖 AI Insights": "ai_insights"
            }

            for label, view in views.items():
                if st.button(label, key=f"nav_{view}", use_container_width=True):
                    st.session_state.current_view = view
                    st.rerun()

            st.markdown("---")

            # Quick actions
            st.subheader("Quick Actions")
            if st.button("➕ New Project", use_container_width=True):
                st.session_state.current_view = "new_project"
                st.rerun()

            if st.button("✅ New Task", use_container_width=True):
                st.session_state.current_view = "new_task"
                st.rerun()

        # Main content area
        if st.session_state.current_view == "dashboard":
            self.render_dashboard()
        elif st.session_state.current_view == "tasks":
            self.render_tasks_view()
        elif st.session_state.current_view == "kanban":
            self.render_kanban_view()
        elif st.session_state.current_view == "gantt":
            self.render_gantt_view()
        elif st.session_state.current_view == "timeline":
            self.render_timeline_view()
        elif st.session_state.current_view == "milestones":
            self.render_milestones_view()
        elif st.session_state.current_view == "resources":
            self.render_resources_view()
        elif st.session_state.current_view == "time_tracking":
            self.render_time_tracking_view()
        elif st.session_state.current_view == "budget":
            self.render_budget_view()
        elif st.session_state.current_view == "collaboration":
            self.render_collaboration_view()
        elif st.session_state.current_view == "reports":
            self.render_reports_view()
        elif st.session_state.current_view == "ai_insights":
            self.render_ai_insights_view()

    def render_dashboard(self):
        """Render the project dashboard."""
        st.title("📊 Project Dashboard")

        if not st.session_state.selected_project:
            st.warning("Please select a project")
            return

        project = st.session_state.project_manager.get_project(st.session_state.selected_project)
        if not project:
            st.error("Project not found")
            return

        # Project header
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.subheader(project.name)
            st.caption(project.description)

        with col2:
            st.metric("Status", project.status.value.replace("_", " ").title())

        with col3:
            st.metric("Priority", project.priority.value.title())

        st.markdown("---")

        # Metrics row
        col1, col2, col3, col4 = st.columns(4)

        task_stats = st.session_state.task_manager.get_task_statistics(project.id)

        with col1:
            st.metric("Total Tasks", task_stats["total_tasks"])

        with col2:
            completed = task_stats["by_status"].get("done", 0)
            st.metric("Completed", completed)

        with col3:
            overdue = task_stats.get("overdue", 0)
            st.metric("Overdue", overdue, delta=f"-{overdue}" if overdue > 0 else None)

        with col4:
            progress = project.get_progress(st.session_state.task_manager)
            st.metric("Progress", f"{progress:.0f}%")

        # Progress bar
        st.progress(progress / 100)

        st.markdown("---")

        # Charts row
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Task Status Distribution")
            if task_stats["total_tasks"] > 0:
                status_df = pd.DataFrame([
                    {"Status": status.replace("_", " ").title(), "Count": count}
                    for status, count in task_stats["by_status"].items()
                ])
                st.bar_chart(status_df.set_index("Status"))

        with col2:
            st.subheader("Priority Distribution")
            if task_stats["total_tasks"] > 0:
                priority_df = pd.DataFrame([
                    {"Priority": priority.title(), "Count": count}
                    for priority, count in task_stats["by_priority"].items()
                ])
                st.bar_chart(priority_df.set_index("Priority"))

        # Recent activity
        st.markdown("---")
        st.subheader("Recent Activity")
        activities = st.session_state.collaboration_manager.get_project_activity_feed(
            project.id, limit=10
        )

        if activities:
            for activity in activities:
                with st.container():
                    st.markdown(f"**{activity.title}**")
                    st.caption(f"{activity.description} • {activity.created_at.strftime('%Y-%m-%d %H:%M')}")
        else:
            st.info("No recent activity")

    def render_tasks_view(self):
        """Render the tasks view."""
        st.title("📋 Tasks")

        if not st.session_state.selected_project:
            st.warning("Please select a project")
            return

        # Task filters
        col1, col2, col3 = st.columns(3)

        with col1:
            status_filter = st.selectbox(
                "Status",
                ["All"] + [s.value for s in TaskStatus],
                key="task_status_filter"
            )

        with col2:
            priority_filter = st.selectbox(
                "Priority",
                ["All"] + [p.value for p in TaskPriority],
                key="task_priority_filter"
            )

        with col3:
            sort_by = st.selectbox(
                "Sort by",
                ["Due Date", "Priority", "Status", "Progress"],
                key="task_sort"
            )

        # Get tasks
        tasks = st.session_state.task_manager.get_tasks_by_project(st.session_state.selected_project)

        # Apply filters
        if status_filter != "All":
            tasks = [t for t in tasks if t.status.value == status_filter]

        if priority_filter != "All":
            tasks = [t for t in tasks if t.priority.value == priority_filter]

        # Display tasks
        st.markdown(f"**{len(tasks)} tasks**")

        for task in tasks:
            with st.expander(f"{'✅' if task.status.value == 'done' else '📌'} {task.name}"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write(f"**Status:** {task.status.value.replace('_', ' ').title()}")
                    st.write(f"**Priority:** {task.priority.value.title()}")

                with col2:
                    st.write(f"**Due:** {task.due_date or 'Not set'}")
                    st.write(f"**Assignee:** {task.assignee or 'Unassigned'}")

                with col3:
                    st.write(f"**Progress:** {task.progress:.0f}%")
                    st.progress(task.progress / 100)

                st.write(f"**Description:** {task.description or 'No description'}")

                # Task actions
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("Edit", key=f"edit_{task.id}"):
                        st.session_state.selected_task = task.id
                        st.session_state.current_view = "edit_task"
                        st.rerun()

                with col2:
                    if task.status.value != "done":
                        if st.button("Mark Done", key=f"done_{task.id}"):
                            st.session_state.task_manager.update_task(
                                task.id, status=TaskStatus.DONE
                            )
                            st.rerun()

                with col3:
                    if st.button("Delete", key=f"delete_{task.id}"):
                        st.session_state.task_manager.delete_task(task.id)
                        st.rerun()

    def render_kanban_view(self):
        """Render the Kanban board view."""
        st.title("📅 Kanban Board")

        if not st.session_state.selected_project:
            st.warning("Please select a project")
            return

        # Get or create Kanban board
        boards = st.session_state.kanban_manager.get_boards_by_project(
            st.session_state.selected_project
        )

        if not boards:
            board = st.session_state.kanban_manager.create_board(
                st.session_state.selected_project,
                "Main Board"
            )
        else:
            board = boards[0]

        # Display columns
        columns = board.columns
        cols = st.columns(len(columns))

        for idx, column in enumerate(columns):
            with cols[idx]:
                st.subheader(column.name)

                if column.wip_limit:
                    card_count = board.get_column_card_count(column.id)
                    st.caption(f"WIP: {card_count}/{column.wip_limit}")

                cards = board.get_cards_by_column(column.id)

                for card in cards:
                    task = st.session_state.task_manager.get_task(card.task_id)
                    if task:
                        with st.container():
                            st.markdown(f"**{task.name}**")
                            st.caption(f"Priority: {task.priority.value}")
                            st.progress(task.progress / 100)

                            if st.button("View", key=f"view_card_{card.task_id}"):
                                st.session_state.selected_task = card.task_id
                                st.rerun()

    def render_gantt_view(self):
        """Render the Gantt chart view."""
        st.title("📈 Gantt Chart")

        if not st.session_state.selected_project:
            st.warning("Please select a project")
            return

        # Options
        col1, col2, col3 = st.columns(3)

        with col1:
            show_dependencies = st.checkbox("Show Dependencies", value=True)

        with col2:
            show_critical_path = st.checkbox("Show Critical Path", value=True)

        with col3:
            show_progress = st.checkbox("Show Progress", value=True)

        # Generate Gantt chart
        gantt_chart = GanttChart(
            st.session_state.task_manager,
            st.session_state.dependency_manager
        )

        fig = gantt_chart.create_plotly_gantt(
            st.session_state.selected_project,
            show_dependencies=show_dependencies,
            show_critical_path=show_critical_path,
            show_progress=show_progress
        )

        st.plotly_chart(fig, use_container_width=True)

    def render_timeline_view(self):
        """Render the timeline view."""
        st.title("🗓️ Timeline")

        if not st.session_state.selected_project:
            st.warning("Please select a project")
            return

        # Timeline options
        col1, col2 = st.columns(2)

        with col1:
            view_type = st.selectbox(
                "View Type",
                [v.value for v in TimelineViewType],
                key="timeline_view_type"
            )

        with col2:
            group_by = st.selectbox(
                "Group By",
                ["None", "assignee", "priority", "status"],
                key="timeline_group_by"
            )

        # Generate timeline
        timeline_manager = TimelineManager(
            st.session_state.task_manager,
            st.session_state.milestone_manager
        )

        fig = timeline_manager.create_timeline_view(
            st.session_state.selected_project,
            view_type=TimelineViewType(view_type),
            group_by=group_by if group_by != "None" else None
        )

        st.plotly_chart(fig, use_container_width=True)

    def render_milestones_view(self):
        """Render the milestones view."""
        st.title("🎯 Milestones")

        if not st.session_state.selected_project:
            st.warning("Please select a project")
            return

        milestones = st.session_state.milestone_manager.get_milestones_by_project(
            st.session_state.selected_project
        )

        st.markdown(f"**{len(milestones)} milestones**")

        for milestone in milestones:
            with st.expander(f"{'✅' if milestone.is_completed else '🎯'} {milestone.name}"):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**Due Date:** {milestone.due_date or 'Not set'}")
                    st.write(f"**Status:** {milestone.status.value.replace('_', ' ').title()}")

                with col2:
                    st.write(f"**Progress:** {milestone.progress:.0f}%")
                    st.progress(milestone.progress / 100)

                st.write(f"**Description:** {milestone.description or 'No description'}")

                if not milestone.is_completed:
                    if st.button("Mark Completed", key=f"complete_milestone_{milestone.id}"):
                        milestone.mark_completed()
                        st.rerun()

    def render_resources_view(self):
        """Render the resources view."""
        st.title("👥 Resources")

        # Resource list
        resources = list(st.session_state.resource_manager.resources.values())

        if resources:
            st.subheader("Team Members")

            for resource in resources:
                with st.expander(f"👤 {resource.name}"):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(f"**Role:** {resource.role}")
                        st.write(f"**Skills:** {', '.join(resource.skills) if resource.skills else 'None'}")

                    with col2:
                        st.write(f"**Capacity:** {resource.capacity_hours_per_day} hrs/day")
                        st.write(f"**Cost:** ${resource.cost_per_hour}/hr")
        else:
            st.info("No resources added yet")

        # Add new resource
        with st.expander("➕ Add Resource"):
            with st.form("add_resource_form"):
                name = st.text_input("Name")
                email = st.text_input("Email")
                role = st.text_input("Role")
                skills = st.text_input("Skills (comma-separated)")
                capacity = st.number_input("Capacity (hrs/day)", value=8.0)
                cost = st.number_input("Cost per hour", value=0.0)

                if st.form_submit_button("Add Resource"):
                    st.session_state.resource_manager.add_resource(
                        name=name,
                        email=email,
                        role=role,
                        skills=skills.split(",") if skills else [],
                        capacity_hours_per_day=capacity,
                        cost_per_hour=cost
                    )
                    st.success(f"Resource '{name}' added!")
                    st.rerun()

    def render_time_tracking_view(self):
        """Render the time tracking view."""
        st.title("⏱️ Time Tracking")

        if not st.session_state.selected_project:
            st.warning("Please select a project")
            return

        # Time entries
        time_summary = st.session_state.time_tracking_manager.get_project_time_summary(
            st.session_state.selected_project
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Hours", f"{time_summary.get('total_hours', 0):.1f}")

        with col2:
            st.metric("Billable Hours", f"{time_summary.get('billable_hours', 0):.1f}")

        with col3:
            st.metric("Entries", time_summary.get('entry_count', 0))

        # Log time
        st.markdown("---")
        st.subheader("Log Time")

        with st.form("log_time_form"):
            tasks = st.session_state.task_manager.get_tasks_by_project(
                st.session_state.selected_project
            )
            task_options = {t.id: t.name for t in tasks}

            task_id = st.selectbox("Task", options=list(task_options.keys()), format_func=lambda x: task_options[x])
            hours = st.number_input("Hours", min_value=0.0, step=0.5)
            description = st.text_area("Description")
            is_billable = st.checkbox("Billable", value=True)

            if st.form_submit_button("Log Time"):
                st.session_state.time_tracking_manager.log_time(
                    task_id=task_id,
                    user_id="current_user",
                    duration_hours=hours,
                    description=description,
                    is_billable=is_billable
                )
                st.success("Time logged successfully!")
                st.rerun()

    def render_budget_view(self):
        """Render the budget view."""
        st.title("💰 Budget")

        if not st.session_state.selected_project:
            st.warning("Please select a project")
            return

        # Budget utilization
        budget_util = st.session_state.budget_manager.get_budget_utilization(
            st.session_state.selected_project
        )

        if "error" not in budget_util:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Budget", f"${budget_util['budget']['total']:,.2f}")

            with col2:
                st.metric("Spent", f"${budget_util['actual']['total']:,.2f}")

            with col3:
                st.metric("Remaining", f"${budget_util['remaining']:,.2f}")

            with col4:
                st.metric("Utilization", f"{budget_util['utilization_percentage']:.1f}%")

            # Progress bar
            st.progress(min(1.0, budget_util['utilization_percentage'] / 100))

            if budget_util['is_over_budget']:
                st.error("⚠️ Project is over budget!")

        # Expenses
        st.markdown("---")
        st.subheader("Expenses")

        expenses = st.session_state.budget_manager.get_project_expenses(
            st.session_state.selected_project
        )

        if expenses:
            expense_data = [{
                "Category": e.category.value.title(),
                "Amount": f"${e.amount:,.2f}",
                "Vendor": e.vendor,
                "Date": e.date.isoformat(),
                "Status": e.status.value.title()
            } for e in expenses]

            st.dataframe(expense_data, use_container_width=True)

    def render_collaboration_view(self):
        """Render the collaboration view."""
        st.title("💬 Collaboration")

        if not st.session_state.selected_project:
            st.warning("Please select a project")
            return

        # Activity feed
        st.subheader("Activity Feed")

        activities = st.session_state.collaboration_manager.get_project_activity_feed(
            st.session_state.selected_project,
            limit=20
        )

        if activities:
            for activity in activities:
                with st.container():
                    st.markdown(f"**{activity.title}**")
                    st.caption(f"{activity.description} • {activity.created_at.strftime('%Y-%m-%d %H:%M')}")
                    st.markdown("---")
        else:
            st.info("No activity yet")

    def render_reports_view(self):
        """Render the reports view."""
        st.title("📊 Reports")

        if not st.session_state.selected_project:
            st.warning("Please select a project")
            return

        # Report type selector
        report_type = st.selectbox(
            "Report Type",
            ["Project Summary", "Task Status", "Burndown Chart", "Velocity Chart"],
            key="report_type"
        )

        if report_type == "Project Summary":
            summary = st.session_state.reporting_manager.generate_project_summary(
                st.session_state.selected_project
            )
            st.json(summary)

        elif report_type == "Task Status":
            group_by = st.selectbox("Group By", ["status", "priority", "assignee"])
            report = st.session_state.reporting_manager.generate_task_status_report(
                st.session_state.selected_project,
                group_by=group_by
            )
            st.json(report)

        elif report_type == "Burndown Chart":
            fig = st.session_state.reporting_manager.generate_burndown_chart(
                st.session_state.selected_project
            )
            st.plotly_chart(fig, use_container_width=True)

        elif report_type == "Velocity Chart":
            fig = st.session_state.reporting_manager.generate_velocity_chart(
                st.session_state.selected_project
            )
            st.plotly_chart(fig, use_container_width=True)

        # Export options
        st.markdown("---")
        st.subheader("Export Data")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Export to CSV"):
                csv_data = st.session_state.reporting_manager.export_to_csv(
                    st.session_state.selected_project, "tasks"
                )
                st.download_button(
                    "Download CSV",
                    csv_data,
                    "project_tasks.csv",
                    "text/csv"
                )

        with col2:
            if st.button("Export to JSON"):
                json_data = st.session_state.reporting_manager.export_to_json(
                    st.session_state.selected_project
                )
                st.download_button(
                    "Download JSON",
                    json_data,
                    "project_data.json",
                    "application/json"
                )

    def render_ai_insights_view(self):
        """Render the AI insights view."""
        st.title("🤖 AI Insights")

        if not st.session_state.selected_project:
            st.warning("Please select a project")
            return

        # Project health
        st.subheader("Project Health")
        health = st.session_state.ai_assistant.analyze_project_health(
            st.session_state.selected_project
        )

        col1, col2 = st.columns([1, 2])

        with col1:
            st.metric("Health Score", f"{health['health_score']:.0f}/100")
            status_colors = {"healthy": "🟢", "at_risk": "🟡", "critical": "🔴"}
            st.markdown(f"### {status_colors.get(health['status'], '⚪')} {health['status'].upper()}")

        with col2:
            if health.get('issues'):
                st.markdown("**Issues:**")
                for issue in health['issues']:
                    st.markdown(f"- {issue}")

        # AI insights
        st.markdown("---")
        st.subheader("AI Insights")

        insights = st.session_state.ai_assistant.generate_insights(
            st.session_state.selected_project
        )

        for insight in insights:
            severity_icons = {
                "info": "ℹ️",
                "warning": "⚠️",
                "critical": "🚨"
            }

            with st.expander(f"{severity_icons.get(insight.severity, 'ℹ️')} {insight.title}"):
                st.write(insight.description)

                if insight.recommendations:
                    st.markdown("**Recommendations:**")
                    for rec in insight.recommendations:
                        st.markdown(f"- {rec}")

                st.caption(f"Confidence: {insight.confidence * 100:.0f}%")

        # Completion prediction
        st.markdown("---")
        st.subheader("Completion Prediction")

        prediction = st.session_state.ai_assistant.predict_completion_date(
            st.session_state.selected_project
        )

        if "error" not in prediction:
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Predicted Completion:** {prediction['predicted_completion_date']}")
                st.write(f"**Planned Completion:** {prediction.get('planned_completion_date', 'Not set')}")

            with col2:
                if prediction['on_track']:
                    st.success("✅ Project is on track!")
                else:
                    st.warning(f"⚠️ Project is {abs(prediction['variance_days'])} days behind schedule")

        # Priority suggestions
        st.markdown("---")
        st.subheader("Task Priority Suggestions")

        suggestions = st.session_state.ai_assistant.suggest_task_priorities(
            st.session_state.selected_project
        )

        if suggestions:
            for suggestion in suggestions[:5]:
                with st.container():
                    st.markdown(f"**{suggestion['task_name']}**")
                    st.caption(f"Suggested Priority: {suggestion['suggested_priority'].upper()} (Score: {suggestion['priority_score']:.0f})")
                    st.caption(suggestion['recommendation'])
                    st.markdown("---")


def main():
    """Main entry point for the Streamlit app."""
    ui = ProjectManagementUI()
    ui.render()


if __name__ == "__main__":
    main()
