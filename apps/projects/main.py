"""Project Management Application with Gantt, Kanban, Dependencies, Milestones"""
import streamlit as st
from datetime import datetime, timedelta
from pathlib import Path
import sys
import plotly.figure_factory as ff
import plotly.express as px
import pandas as pd
sys.path.append(str(Path(__file__).parent.parent.parent))

from database.connection import SessionLocal, init_db
from database.models import Project, Task, Milestone
from ai.claude_client import ClaudeClient
from config.settings import settings
from config.constants import PROJECT_STATUS, TASK_PRIORITY
from utils.exporters import export_to_xlsx, export_to_pdf
from utils.formatters import format_date, format_percentage

def initialize_session_state():
    """Initialize session state variables"""
    if 'current_project' not in st.session_state:
        st.session_state.current_project = None
    if 'view_mode' not in st.session_state:
        st.session_state.view_mode = 'kanban'

def render_sidebar():
    """Render sidebar with project list"""
    st.sidebar.title("📊 Projects")

    # New project button
    if st.sidebar.button("➕ New Project", use_container_width=True):
        st.session_state.current_project = None
        st.rerun()

    st.sidebar.divider()

    # View mode selector
    st.sidebar.subheader("View")
    view_options = {
        "Kanban Board": "kanban",
        "Gantt Chart": "gantt",
        "Task List": "list",
        "Milestones": "milestones"
    }

    for label, mode in view_options.items():
        if st.sidebar.button(label, key=f"view_{mode}", use_container_width=True):
            st.session_state.view_mode = mode
            st.rerun()

    st.sidebar.divider()

    # Project list
    st.sidebar.subheader("Projects")
    db = SessionLocal()
    projects = db.query(Project).order_by(Project.updated_at.desc()).all()

    for project in projects:
        col1, col2 = st.sidebar.columns([4, 1])
        with col1:
            status_icon = {
                'Not Started': '⚪',
                'Planning': '🔵',
                'In Progress': '🟢',
                'On Hold': '🟡',
                'Completed': '✅',
                'Cancelled': '🔴'
            }.get(project.status, '⚪')

            if st.button(f"{status_icon} {project.name}", key=f"proj_{project.id}",
                        use_container_width=True):
                st.session_state.current_project = project.id
                st.rerun()

        with col2:
            if st.button("🗑️", key=f"del_proj_{project.id}"):
                db.query(Task).filter(Task.project_id == project.id).delete()
                db.query(Milestone).filter(Milestone.project_id == project.id).delete()
                db.delete(project)
                db.commit()
                st.rerun()

    db.close()

def render_kanban_view(db, project):
    """Render Kanban board view"""
    st.subheader("📋 Kanban Board")

    # Get tasks
    tasks = db.query(Task).filter(Task.project_id == project.id).all()

    # Group by status
    statuses = ['Not Started', 'In Progress', 'On Hold', 'Completed']
    columns = st.columns(len(statuses))

    for idx, status in enumerate(statuses):
        with columns[idx]:
            st.markdown(f"### {status}")
            st.markdown(f"---")

            status_tasks = [t for t in tasks if t.status == status]

            for task in status_tasks:
                with st.container():
                    st.markdown(f"**{task.title}**")

                    if task.priority:
                        priority_colors = {
                            'Low': '🟢',
                            'Medium': '🟡',
                            'High': '🟠',
                            'Critical': '🔴'
                        }
                        st.caption(f"{priority_colors.get(task.priority, '')} {task.priority}")

                    if task.assignee:
                        st.caption(f"👤 {task.assignee}")

                    if task.due_date:
                        st.caption(f"📅 {format_date(task.due_date, '%Y-%m-%d')}")

                    # Progress bar
                    if task.progress:
                        st.progress(task.progress / 100.0)
                        st.caption(format_percentage(task.progress))

                    # Move buttons
                    col1, col2 = st.columns(2)

                    current_idx = statuses.index(status)

                    with col1:
                        if current_idx > 0:
                            if st.button("←", key=f"left_{task.id}"):
                                task.status = statuses[current_idx - 1]
                                db.commit()
                                st.rerun()

                    with col2:
                        if current_idx < len(statuses) - 1:
                            if st.button("→", key=f"right_{task.id}"):
                                task.status = statuses[current_idx + 1]
                                if task.status == 'Completed':
                                    task.progress = 100
                                    task.completed_date = datetime.utcnow()
                                db.commit()
                                st.rerun()

                    st.markdown("---")

def render_gantt_view(db, project):
    """Render Gantt chart view"""
    st.subheader("📊 Gantt Chart")

    tasks = db.query(Task).filter(Task.project_id == project.id).all()

    if not tasks:
        st.info("No tasks to display")
        return

    # Prepare data for Gantt chart
    gantt_data = []

    for task in tasks:
        start_date = task.start_date or datetime.utcnow()
        end_date = task.due_date or start_date + timedelta(days=7)

        gantt_data.append({
            'Task': task.title,
            'Start': start_date,
            'Finish': end_date,
            'Resource': task.assignee or 'Unassigned'
        })

    if gantt_data:
        df = pd.DataFrame(gantt_data)

        # Create Gantt chart
        fig = ff.create_gantt(
            df,
            colors='Viridis',
            index_col='Resource',
            show_colorbar=True,
            group_tasks=True
        )

        fig.update_layout(
            xaxis_title="Timeline",
            height=max(400, len(tasks) * 30)
        )

        st.plotly_chart(fig, use_container_width=True)

def render_task_list(db, project):
    """Render task list view"""
    st.subheader("📝 Task List")

    tasks = db.query(Task).filter(Task.project_id == project.id).order_by(Task.due_date).all()

    if tasks:
        # Task table
        for task in tasks:
            with st.expander(f"{'✅' if task.status == 'Completed' else '⬜'} {task.title}"):
                col1, col2 = st.columns(2)

                with col1:
                    task.title = st.text_input("Title", value=task.title, key=f"title_{task.id}")
                    task.description = st.text_area("Description", value=task.description or "",
                                                   key=f"desc_{task.id}", height=100)
                    task.assignee = st.text_input("Assignee", value=task.assignee or "",
                                                 key=f"assignee_{task.id}")

                with col2:
                    task.status = st.selectbox("Status", PROJECT_STATUS,
                                              index=PROJECT_STATUS.index(task.status) if task.status in PROJECT_STATUS else 0,
                                              key=f"status_{task.id}")
                    task.priority = st.selectbox("Priority", TASK_PRIORITY,
                                                index=TASK_PRIORITY.index(task.priority) if task.priority in TASK_PRIORITY else 1,
                                                key=f"priority_{task.id}")
                    task.progress = st.slider("Progress (%)", 0, 100, int(task.progress or 0),
                                             key=f"progress_{task.id}")

                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("Start Date",
                                              value=task.start_date.date() if task.start_date else datetime.now().date(),
                                              key=f"start_{task.id}")
                    task.start_date = datetime.combine(start_date, datetime.min.time())

                with col2:
                    due_date = st.date_input("Due Date",
                                            value=task.due_date.date() if task.due_date else datetime.now().date(),
                                            key=f"due_{task.id}")
                    task.due_date = datetime.combine(due_date, datetime.min.time())

                # Dependencies
                other_tasks = [t for t in tasks if t.id != task.id]
                task_options = {t.title: t.id for t in other_tasks}

                selected_deps = st.multiselect("Dependencies",
                                              options=list(task_options.keys()),
                                              default=[t.title for t in other_tasks
                                                      if task.dependencies and t.id in task.dependencies],
                                              key=f"deps_{task.id}")

                task.dependencies = [task_options[title] for title in selected_deps]

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Save", key=f"save_{task.id}"):
                        db.commit()
                        st.success("Task updated!")

                with col2:
                    if st.button("🗑️ Delete", key=f"del_task_{task.id}"):
                        db.delete(task)
                        db.commit()
                        st.rerun()

    # Add new task
    with st.expander("➕ Add New Task"):
        new_title = st.text_input("Title")
        new_description = st.text_area("Description", height=100)

        col1, col2 = st.columns(2)
        with col1:
            new_assignee = st.text_input("Assignee")
            new_status = st.selectbox("Status", PROJECT_STATUS)
        with col2:
            new_priority = st.selectbox("Priority", TASK_PRIORITY)
            new_progress = st.slider("Progress (%)", 0, 100, 0)

        col1, col2 = st.columns(2)
        with col1:
            new_start = st.date_input("Start Date")
        with col2:
            new_due = st.date_input("Due Date")

        if st.button("Add Task", type="primary"):
            if new_title:
                task = Task(
                    project_id=project.id,
                    title=new_title,
                    description=new_description,
                    status=new_status,
                    priority=new_priority,
                    assignee=new_assignee,
                    start_date=datetime.combine(new_start, datetime.min.time()),
                    due_date=datetime.combine(new_due, datetime.min.time()),
                    progress=new_progress
                )
                db.add(task)
                db.commit()
                st.success("Task added!")
                st.rerun()

def render_milestones_view(db, project):
    """Render milestones view"""
    st.subheader("🎯 Milestones")

    milestones = db.query(Milestone).filter(
        Milestone.project_id == project.id
    ).order_by(Milestone.due_date).all()

    if milestones:
        for milestone in milestones:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    icon = "✅" if milestone.is_completed else "⬜"
                    st.markdown(f"### {icon} {milestone.title}")
                    if milestone.description:
                        st.write(milestone.description)

                with col2:
                    if milestone.due_date:
                        st.caption(f"📅 {format_date(milestone.due_date, '%Y-%m-%d')}")

                with col3:
                    if st.button("Toggle", key=f"toggle_{milestone.id}"):
                        milestone.is_completed = not milestone.is_completed
                        if milestone.is_completed:
                            milestone.completion_date = datetime.utcnow()
                        else:
                            milestone.completion_date = None
                        db.commit()
                        st.rerun()

                    if st.button("🗑️", key=f"del_milestone_{milestone.id}"):
                        db.delete(milestone)
                        db.commit()
                        st.rerun()

                st.divider()

    # Add new milestone
    with st.expander("➕ Add Milestone"):
        mile_title = st.text_input("Title")
        mile_desc = st.text_area("Description", height=80)
        mile_due = st.date_input("Due Date")

        if st.button("Add Milestone", type="primary"):
            if mile_title:
                milestone = Milestone(
                    project_id=project.id,
                    title=mile_title,
                    description=mile_desc,
                    due_date=datetime.combine(mile_due, datetime.min.time())
                )
                db.add(milestone)
                db.commit()
                st.success("Milestone added!")
                st.rerun()

def render_project_editor(db):
    """Render project editor"""

    if st.session_state.current_project:
        project = db.query(Project).filter(Project.id == st.session_state.current_project).first()

        if not project:
            st.error("Project not found")
            return
    else:
        # New project
        project = Project(
            name="New Project",
            status="Planning",
            progress=0.0
        )

    # Project details
    col1, col2 = st.columns([2, 1])

    with col1:
        project.name = st.text_input("Project Name", value=project.name)
        project.description = st.text_area("Description", value=project.description or "", height=100)

    with col2:
        project.status = st.selectbox("Status", PROJECT_STATUS,
                                     index=PROJECT_STATUS.index(project.status) if project.status in PROJECT_STATUS else 0)
        project.owner = st.text_input("Owner", value=project.owner or "")

    col1, col2, col3 = st.columns(3)

    with col1:
        if project.start_date:
            start_val = project.start_date.date()
        else:
            start_val = datetime.now().date()
        start_date = st.date_input("Start Date", value=start_val)
        project.start_date = datetime.combine(start_date, datetime.min.time())

    with col2:
        if project.end_date:
            end_val = project.end_date.date()
        else:
            end_val = (datetime.now() + timedelta(days=30)).date()
        end_date = st.date_input("End Date", value=end_val)
        project.end_date = datetime.combine(end_date, datetime.min.time())

    with col3:
        project.budget = st.number_input("Budget ($)", value=float(project.budget or 0), min_value=0.0)

    # Team members
    team_input = st.text_area("Team Members (one per line)",
                             value='\n'.join(project.team_members or []) if project.team_members else "")
    project.team_members = [m.strip() for m in team_input.split('\n') if m.strip()]

    # Save button
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("💾 Save Project", type="primary"):
            if project.name:
                if not st.session_state.current_project:
                    db.add(project)
                    db.flush()
                    st.session_state.current_project = project.id

                db.commit()
                st.success("Project saved!")
                st.rerun()

    with col2:
        if st.button("📊 Export to Excel"):
            tasks = db.query(Task).filter(Task.project_id == project.id).all()
            tasks_data = [
                {
                    'Title': t.title,
                    'Status': t.status,
                    'Priority': t.priority,
                    'Assignee': t.assignee,
                    'Progress': f"{t.progress}%",
                    'Start Date': format_date(t.start_date, '%Y-%m-%d'),
                    'Due Date': format_date(t.due_date, '%Y-%m-%d')
                }
                for t in tasks
            ]

            if tasks_data:
                output_path = settings.EXPORTS_DIR / f"{project.name.replace(' ', '_')}_tasks.xlsx"
                export_to_xlsx(tasks_data, str(output_path))

                with open(output_path, 'rb') as f:
                    st.download_button(
                        "⬇️ Download Excel",
                        f,
                        file_name=output_path.name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

    # AI Task Generation
    if settings.ENABLE_AI_FEATURES:
        with st.expander("🤖 AI Task Generator"):
            if st.button("Generate Tasks from Description", type="primary"):
                if project.description:
                    try:
                        with st.spinner("Generating tasks..."):
                            ai_client = ClaudeClient()
                            suggested_tasks = ai_client.suggest_project_tasks(project.description)

                            for task_title in suggested_tasks[:10]:  # Limit to 10
                                if isinstance(task_title, str) and task_title.strip():
                                    task = Task(
                                        project_id=project.id,
                                        title=task_title.strip(),
                                        status='Not Started',
                                        priority='Medium',
                                        progress=0.0
                                    )
                                    db.add(task)

                            db.commit()
                            st.success(f"Generated {len(suggested_tasks)} tasks!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    st.divider()

    # Views
    if st.session_state.current_project:
        if st.session_state.view_mode == 'kanban':
            render_kanban_view(db, project)
        elif st.session_state.view_mode == 'gantt':
            render_gantt_view(db, project)
        elif st.session_state.view_mode == 'list':
            render_task_list(db, project)
        elif st.session_state.view_mode == 'milestones':
            render_milestones_view(db, project)

def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="Projects - NEXUS",
        page_icon="📊",
        layout="wide"
    )

    # Initialize database
    init_db()

    # Initialize session state
    initialize_session_state()

    # Render sidebar
    render_sidebar()

    # Render main content
    st.title("📊 Project Management")

    db = SessionLocal()
    render_project_editor(db)
    db.close()

if __name__ == "__main__":
    main()
