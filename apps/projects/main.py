"""Project Management Application with Kanban"""


def main():
    import streamlit as st
    from datetime import datetime, timedelta

    try:
        # Lazy import database
        from database import init_database
        init_database()

        st.set_page_config(
            page_title="Projects - NEXUS",
            page_icon="📊",
            layout="wide"
        )

        st.title("📊 Project Management")

        # Session state
        if 'projects' not in st.session_state:
            st.session_state.projects = []
        if 'current_project' not in st.session_state:
            st.session_state.current_project = None
        if 'view_mode' not in st.session_state:
            st.session_state.view_mode = 'kanban'

        # Sidebar
        st.sidebar.title("📊 Projects")

        if st.sidebar.button("➕ New Project", use_container_width=True):
            st.session_state.current_project = None
            st.rerun()

        st.sidebar.divider()
        st.sidebar.subheader("View")

        for label, mode in [("📋 Kanban", "kanban"), ("📝 List", "list")]:
            if st.sidebar.button(label, key=f"view_{mode}", use_container_width=True):
                st.session_state.view_mode = mode
                st.rerun()

        st.sidebar.divider()
        st.sidebar.subheader("Projects")

        for idx, project in enumerate(st.session_state.projects):
            status_icons = {'Not Started': '⚪', 'Planning': '🔵', 'In Progress': '🟢', 'Completed': '✅'}
            icon = status_icons.get(project.get('status', 'Not Started'), '⚪')
            if st.sidebar.button(f"{icon} {project['name']}", key=f"proj_{idx}", use_container_width=True):
                st.session_state.current_project = idx
                st.rerun()

        # Main content
        if st.session_state.current_project is not None and st.session_state.current_project < len(st.session_state.projects):
            project = st.session_state.projects[st.session_state.current_project]

            col1, col2 = st.columns([2, 1])
            with col1:
                project['name'] = st.text_input("Project Name", value=project.get('name', ''))
                project['description'] = st.text_area("Description", value=project.get('description', ''), height=100)
            with col2:
                project['status'] = st.selectbox("Status", ["Not Started", "Planning", "In Progress", "On Hold", "Completed"],
                                                  index=["Not Started", "Planning", "In Progress", "On Hold", "Completed"].index(project.get('status', 'Not Started')))
                project['owner'] = st.text_input("Owner", value=project.get('owner', ''))

            if st.button("💾 Save Project", type="primary"):
                st.success("Project saved!")

            st.divider()

            # Tasks
            if 'tasks' not in project:
                project['tasks'] = []

            if st.session_state.view_mode == 'kanban':
                st.subheader("📋 Kanban Board")

                statuses = ['Not Started', 'In Progress', 'On Hold', 'Completed']
                cols = st.columns(len(statuses))

                for idx, status in enumerate(statuses):
                    with cols[idx]:
                        st.markdown(f"### {status}")
                        st.markdown("---")
                        status_tasks = [t for t in project['tasks'] if t.get('status') == status]
                        for task in status_tasks:
                            st.write(f"**{task['title']}**")
                            if task.get('assignee'):
                                st.caption(f"👤 {task['assignee']}")
                            st.divider()

            else:  # list view
                st.subheader("📝 Task List")
                for task_idx, task in enumerate(project['tasks']):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"**{task['title']}**")
                    with col2:
                        st.caption(task.get('status', 'Not Started'))
                    with col3:
                        if st.button("🗑️", key=f"del_task_{task_idx}"):
                            project['tasks'].pop(task_idx)
                            st.rerun()
                    st.divider()

            # Add task
            with st.expander("➕ Add Task"):
                task_title = st.text_input("Task Title")
                col1, col2 = st.columns(2)
                with col1:
                    task_status = st.selectbox("Task Status", ["Not Started", "In Progress", "On Hold", "Completed"])
                    task_assignee = st.text_input("Assignee")
                with col2:
                    task_priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
                    task_due = st.date_input("Due Date")

                if st.button("Add Task", type="primary"):
                    if task_title:
                        project['tasks'].append({
                            'title': task_title,
                            'status': task_status,
                            'assignee': task_assignee,
                            'priority': task_priority,
                            'due_date': str(task_due)
                        })
                        st.success("Task added!")
                        st.rerun()

        else:
            # New project form
            st.subheader("➕ Create New Project")

            name = st.text_input("Project Name")
            description = st.text_area("Description", height=100)

            col1, col2 = st.columns(2)
            with col1:
                status = st.selectbox("Status", ["Not Started", "Planning", "In Progress"])
                owner = st.text_input("Owner")
            with col2:
                start_date = st.date_input("Start Date", value=datetime.now().date())
                end_date = st.date_input("End Date", value=(datetime.now() + timedelta(days=30)).date())

            if st.button("Create Project", type="primary"):
                if name:
                    st.session_state.projects.append({
                        'name': name,
                        'description': description,
                        'status': status,
                        'owner': owner,
                        'start_date': str(start_date),
                        'end_date': str(end_date),
                        'tasks': []
                    })
                    st.success("Project created!")
                    st.session_state.current_project = len(st.session_state.projects) - 1
                    st.rerun()

    except Exception as e:
        import streamlit as st
        st.error(f"Error loading module: {str(e)}")
        with st.expander("Technical Details"):
            import traceback
            st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
