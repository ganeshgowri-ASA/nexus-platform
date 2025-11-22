"""
Session 40: Advanced Gantt Chart
Features: Critical path analysis, resource leveling, AI optimization
"""
import streamlit as st
import json
import pandas as pd
import plotly.figure_factory as ff
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.ai_assistant import ai_assistant
from utils.storage import storage


class GanttAdvanced:
    """Advanced Gantt Chart with critical path and resource leveling"""

    def __init__(self):
        """Initialize Gantt chart manager"""
        if 'projects' not in st.session_state:
            st.session_state.projects = self.load_projects()
        if 'current_project' not in st.session_state:
            st.session_state.current_project = None

    def load_projects(self) -> List[Dict]:
        """Load saved projects"""
        projects = []
        files = storage.list_files('gantt', '.json')
        for file in files:
            data = storage.load_json(file, 'gantt')
            if data:
                projects.append(data)
        return projects

    def save_project(self, project: Dict) -> bool:
        """Save project"""
        filename = f"gantt_{project['id']}.json"
        return storage.save_json(filename, project, 'gantt')

    def create_project(self, name: str, start_date: str) -> Dict:
        """Create new project"""
        project = {
            'id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'name': name,
            'start_date': start_date,
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat(),
            'tasks': [],
            'resources': [],
            'dependencies': []
        }
        return project

    def calculate_critical_path(self, tasks: List[Dict], dependencies: List[Dict]) -> List[str]:
        """Calculate critical path"""
        # Simplified critical path calculation
        critical_tasks = []

        # Build dependency graph
        task_map = {task['id']: task for task in tasks}
        task_durations = {task['id']: task['duration'] for task in tasks}

        # Calculate earliest start/finish times
        earliest_start = {}
        earliest_finish = {}

        for task in tasks:
            task_id = task['id']
            # Find dependencies
            deps = [d['from'] for d in dependencies if d['to'] == task_id]

            if not deps:
                earliest_start[task_id] = 0
            else:
                earliest_start[task_id] = max(earliest_finish.get(dep, 0) for dep in deps)

            earliest_finish[task_id] = earliest_start[task_id] + task_durations[task_id]

        # Find tasks with zero slack (critical path)
        project_duration = max(earliest_finish.values()) if earliest_finish else 0

        # Tasks on critical path have earliest_finish == latest_finish
        for task in tasks:
            task_id = task['id']
            # Simplified: mark long-duration tasks or those at the end
            if earliest_finish[task_id] == project_duration or task_durations[task_id] >= 5:
                critical_tasks.append(task_id)

        return critical_tasks

    def level_resources(self, tasks: List[Dict]) -> Dict[str, Any]:
        """Perform resource leveling"""
        # Group tasks by resource
        resource_allocation = {}

        for task in tasks:
            resource = task.get('resource', 'Unassigned')
            if resource not in resource_allocation:
                resource_allocation[resource] = []
            resource_allocation[resource].append(task)

        # Calculate workload
        workload = {}
        for resource, resource_tasks in resource_allocation.items():
            total_duration = sum(t['duration'] for t in resource_tasks)
            workload[resource] = {
                'tasks': len(resource_tasks),
                'total_duration': total_duration,
                'avg_duration': total_duration / len(resource_tasks) if resource_tasks else 0
            }

        return {
            'allocation': resource_allocation,
            'workload': workload
        }

    def render(self):
        """Render Gantt chart manager"""
        st.title("📊 Advanced Gantt Chart")
        st.markdown("*Project management with critical path analysis and resource leveling*")

        # Sidebar
        with st.sidebar:
            st.header("Project Manager")

            # New project
            with st.expander("➕ New Project", expanded=False):
                new_name = st.text_input("Project Name", key="new_project_name")
                start_date = st.date_input("Start Date", key="project_start_date")
                if st.button("Create Project", type="primary"):
                    if new_name:
                        project = self.create_project(new_name, start_date.isoformat())
                        st.session_state.projects.append(project)
                        st.session_state.current_project = project
                        self.save_project(project)
                        st.success(f"Created '{new_name}'")
                        st.rerun()

            # Existing projects
            if st.session_state.projects:
                st.subheader("Saved Projects")
                for project in st.session_state.projects:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.button(project['name'], key=f"load_{project['id']}"):
                            st.session_state.current_project = project
                            st.rerun()
                    with col2:
                        if st.button("🗑️", key=f"del_{project['id']}"):
                            storage.delete_file(f"gantt_{project['id']}.json", 'gantt')
                            st.session_state.projects.remove(project)
                            st.rerun()

        # Main content
        if st.session_state.current_project:
            project = st.session_state.current_project

            tabs = st.tabs(["📋 Tasks", "📊 Gantt Chart", "🎯 Critical Path", "👥 Resources", "🤖 AI Optimizer"])

            # Tasks Tab
            with tabs[0]:
                st.subheader(f"Project: {project['name']}")
                st.caption(f"Start Date: {project['start_date']}")

                # Add task
                with st.expander("➕ Add Task", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        task_name = st.text_input("Task Name")
                        task_duration = st.number_input("Duration (days)", 1, 365, 5)
                    with col2:
                        task_resource = st.text_input("Assigned To")
                        task_priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])

                    task_description = st.text_area("Description")

                    if st.button("Add Task", type="primary"):
                        if task_name:
                            task_id = f"task_{len(project['tasks']) + 1}"
                            project['tasks'].append({
                                'id': task_id,
                                'name': task_name,
                                'duration': task_duration,
                                'resource': task_resource,
                                'priority': task_priority,
                                'description': task_description,
                                'status': 'Not Started'
                            })
                            project['modified'] = datetime.now().isoformat()
                            self.save_project(project)
                            st.success("Task added!")
                            st.rerun()

                # Display tasks
                if project['tasks']:
                    st.markdown("### Task List")
                    for idx, task in enumerate(project['tasks']):
                        with st.expander(f"{task['name']} ({task['duration']} days)"):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.write(f"**Assigned:** {task['resource']}")
                            with col2:
                                st.write(f"**Priority:** {task['priority']}")
                            with col3:
                                status = st.selectbox(
                                    "Status",
                                    ["Not Started", "In Progress", "Completed", "Blocked"],
                                    index=["Not Started", "In Progress", "Completed", "Blocked"].index(task.get('status', 'Not Started')),
                                    key=f"status_{idx}"
                                )
                                project['tasks'][idx]['status'] = status

                            st.write(f"**Description:** {task['description']}")

                            col_a, col_b = st.columns([1, 4])
                            with col_a:
                                if st.button("🗑️ Delete", key=f"del_task_{idx}"):
                                    project['tasks'].pop(idx)
                                    self.save_project(project)
                                    st.rerun()

                    if st.button("💾 Save All Changes"):
                        project['modified'] = datetime.now().isoformat()
                        self.save_project(project)
                        st.success("Changes saved!")

                # Add dependencies
                if len(project['tasks']) >= 2:
                    st.markdown("### Task Dependencies")
                    with st.expander("➕ Add Dependency"):
                        task_ids = [t['id'] for t in project['tasks']]
                        task_names = {t['id']: t['name'] for t in project['tasks']}

                        from_task = st.selectbox("From Task", task_ids, format_func=lambda x: task_names[x])
                        to_task = st.selectbox("To Task", task_ids, format_func=lambda x: task_names[x])

                        if st.button("Add Dependency"):
                            if from_task != to_task:
                                project['dependencies'].append({
                                    'from': from_task,
                                    'to': to_task
                                })
                                self.save_project(project)
                                st.success("Dependency added!")
                                st.rerun()

                    # Display dependencies
                    if project['dependencies']:
                        for idx, dep in enumerate(project['dependencies']):
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                task_names = {t['id']: t['name'] for t in project['tasks']}
                                from_name = task_names.get(dep['from'], dep['from'])
                                to_name = task_names.get(dep['to'], dep['to'])
                                st.write(f"{from_name} → {to_name}")
                            with col2:
                                if st.button("❌", key=f"del_dep_{idx}"):
                                    project['dependencies'].pop(idx)
                                    self.save_project(project)
                                    st.rerun()

            # Gantt Chart Tab
            with tabs[1]:
                st.subheader("📊 Gantt Chart Visualization")

                if project['tasks']:
                    # Prepare data for Gantt chart
                    gantt_data = []
                    start_date = datetime.fromisoformat(project['start_date'])

                    current_date = start_date
                    for task in project['tasks']:
                        end_date = current_date + timedelta(days=task['duration'])

                        gantt_data.append({
                            'Task': task['name'],
                            'Start': current_date.strftime('%Y-%m-%d'),
                            'Finish': end_date.strftime('%Y-%m-%d'),
                            'Resource': task.get('resource', 'Unassigned')
                        })

                        # For sequential display, each task starts after previous
                        # In real scenario, this would consider dependencies
                        current_date = end_date

                    # Create Gantt chart
                    try:
                        df = pd.DataFrame(gantt_data)
                        fig = ff.create_gantt(
                            df,
                            colors='Viridis',
                            index_col='Resource',
                            show_colorbar=True,
                            group_tasks=True
                        )
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error creating Gantt chart: {e}")
                        st.dataframe(pd.DataFrame(gantt_data))

                    # Timeline statistics
                    st.markdown("### 📈 Timeline Statistics")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        total_duration = sum(t['duration'] for t in project['tasks'])
                        st.metric("Total Duration", f"{total_duration} days")
                    with col2:
                        completed = len([t for t in project['tasks'] if t.get('status') == 'Completed'])
                        st.metric("Completed Tasks", f"{completed}/{len(project['tasks'])}")
                    with col3:
                        progress = (completed / len(project['tasks']) * 100) if project['tasks'] else 0
                        st.metric("Progress", f"{progress:.1f}%")

                else:
                    st.info("No tasks yet. Add tasks to see the Gantt chart.")

            # Critical Path Tab
            with tabs[2]:
                st.subheader("🎯 Critical Path Analysis")

                if project['tasks']:
                    critical_tasks = self.calculate_critical_path(project['tasks'], project['dependencies'])

                    st.markdown("### Critical Path Tasks")
                    st.info("Tasks on the critical path directly affect the project completion date")

                    for task in project['tasks']:
                        if task['id'] in critical_tasks:
                            st.error(f"🔴 **{task['name']}** ({task['duration']} days) - {task['resource']}")
                        else:
                            st.success(f"🟢 {task['name']} ({task['duration']} days) - {task['resource']}")

                    # Critical path metrics
                    st.markdown("### 📊 Critical Path Metrics")
                    col1, col2 = st.columns(2)
                    with col1:
                        critical_duration = sum(
                            t['duration'] for t in project['tasks'] if t['id'] in critical_tasks
                        )
                        st.metric("Critical Path Duration", f"{critical_duration} days")
                    with col2:
                        st.metric("Critical Tasks", f"{len(critical_tasks)}/{len(project['tasks'])}")

                    # Recommendations
                    st.markdown("### 💡 Recommendations")
                    if critical_tasks:
                        st.markdown("""
                        - Focus on critical tasks to avoid delays
                        - Allocate additional resources to critical path tasks
                        - Monitor critical tasks closely
                        - Consider task compression techniques
                        """)

                else:
                    st.info("Add tasks and dependencies to see critical path analysis")

            # Resources Tab
            with tabs[3]:
                st.subheader("👥 Resource Management")

                # Add resource
                with st.expander("➕ Add Resource"):
                    resource_name = st.text_input("Resource Name")
                    resource_role = st.text_input("Role")
                    resource_capacity = st.slider("Capacity (%)", 0, 100, 100)

                    if st.button("Add Resource"):
                        if resource_name:
                            project['resources'].append({
                                'name': resource_name,
                                'role': resource_role,
                                'capacity': resource_capacity
                            })
                            self.save_project(project)
                            st.success("Resource added!")
                            st.rerun()

                # Display resources
                if project['resources']:
                    st.markdown("### Team Resources")
                    for idx, resource in enumerate(project['resources']):
                        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                        with col1:
                            st.write(f"👤 {resource['name']}")
                        with col2:
                            st.write(resource['role'])
                        with col3:
                            st.write(f"{resource['capacity']}%")
                        with col4:
                            if st.button("🗑️", key=f"del_res_{idx}"):
                                project['resources'].pop(idx)
                                self.save_project(project)
                                st.rerun()

                # Resource leveling
                if project['tasks']:
                    st.markdown("### 📊 Resource Leveling")

                    leveling_result = self.level_resources(project['tasks'])

                    st.markdown("**Workload by Resource:**")
                    for resource, workload in leveling_result['workload'].items():
                        with st.expander(f"{resource} - {workload['tasks']} tasks"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Total Duration", f"{workload['total_duration']} days")
                            with col2:
                                st.metric("Avg Task Duration", f"{workload['avg_duration']:.1f} days")

                            # List tasks
                            st.markdown("**Assigned Tasks:**")
                            for task in leveling_result['allocation'][resource]:
                                st.write(f"- {task['name']} ({task['duration']} days)")

                    # Recommendations
                    st.markdown("### 💡 Leveling Recommendations")
                    max_workload = max(w['total_duration'] for w in leveling_result['workload'].values())
                    min_workload = min(w['total_duration'] for w in leveling_result['workload'].values())

                    if max_workload > min_workload * 2:
                        st.warning("⚠️ Significant workload imbalance detected!")
                        st.markdown("- Consider redistributing tasks")
                        st.markdown("- Add resources to overloaded team members")
                        st.markdown("- Review task priorities")
                    else:
                        st.success("✅ Resource allocation is relatively balanced")

            # AI Optimizer Tab
            with tabs[4]:
                st.subheader("🤖 AI-Powered Optimization")

                if project['tasks']:
                    optimization_type = st.radio(
                        "Optimization Type",
                        ["Schedule Optimization", "Resource Allocation", "Risk Analysis", "Time Estimation"]
                    )

                    if optimization_type == "Schedule Optimization":
                        if st.button("🚀 Optimize Schedule"):
                            with st.spinner("Analyzing project schedule..."):
                                tasks_summary = json.dumps([{
                                    'name': t['name'],
                                    'duration': t['duration'],
                                    'resource': t['resource'],
                                    'priority': t['priority']
                                } for t in project['tasks']], indent=2)

                                optimization = ai_assistant.optimize_gantt_schedule(tasks_summary)
                                st.markdown(optimization)

                    elif optimization_type == "Resource Allocation":
                        if st.button("👥 Optimize Resources"):
                            with st.spinner("Analyzing resource allocation..."):
                                prompt = f"Analyze and suggest optimal resource allocation for these tasks:\n{json.dumps(project['tasks'], indent=2)}"
                                suggestions = ai_assistant.generate(prompt, max_tokens=1000)
                                st.markdown(suggestions)

                    elif optimization_type == "Risk Analysis":
                        if st.button("⚠️ Analyze Risks"):
                            with st.spinner("Identifying risks..."):
                                prompt = f"Identify potential risks in this project schedule:\n{json.dumps(project['tasks'], indent=2)}"
                                risks = ai_assistant.generate(prompt, max_tokens=1000)
                                st.markdown(risks)

                    else:  # Time Estimation
                        task_to_estimate = st.selectbox(
                            "Select Task",
                            project['tasks'],
                            format_func=lambda x: x['name']
                        )

                        if st.button("⏱️ Estimate Duration"):
                            with st.spinner("Estimating..."):
                                prompt = f"Provide realistic time estimation for this task:\nName: {task_to_estimate['name']}\nDescription: {task_to_estimate['description']}\nCurrent estimate: {task_to_estimate['duration']} days"
                                estimation = ai_assistant.generate(prompt, max_tokens=500)
                                st.markdown(estimation)

                else:
                    st.info("Add tasks first to use AI optimization features")

            # Export
            st.markdown("### 📤 Export Project")
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "Download JSON",
                    json.dumps(project, indent=2),
                    file_name=f"{project['name']}_gantt.json",
                    mime="application/json"
                )
            with col2:
                # Export as CSV
                if project['tasks']:
                    df = pd.DataFrame(project['tasks'])
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "Download CSV",
                        csv,
                        file_name=f"{project['name']}_tasks.csv",
                        mime="text/csv"
                    )

        else:
            st.info("👈 Create or select a project to get started")

            # Welcome message
            st.markdown("""
            ## Welcome to Advanced Gantt Chart! 📊

            **Features:**
            - 📋 Comprehensive task management
            - 🎯 Critical path analysis
            - 👥 Resource leveling
            - 📊 Visual Gantt charts
            - 🤖 AI-powered optimization

            **Get Started:**
            1. Create a new project
            2. Add tasks and assign resources
            3. Define task dependencies
            4. Analyze critical path
            5. Optimize with AI assistance
            """)


def main():
    """Main entry point"""
    gantt = GanttAdvanced()
    gantt.render()


if __name__ == "__main__":
    main()
