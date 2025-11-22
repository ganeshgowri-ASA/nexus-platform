"""Streamlit UI for workflow orchestration and visual designer."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import httpx
import json
from typing import Dict, Any, List, Optional

# Configure page
st.set_page_config(
    page_title="NEXUS Workflow Orchestration",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# API base URL
API_BASE_URL = st.secrets.get("API_BASE_URL", "http://localhost:8000/api/v1")


# API client functions
async def api_request(method: str, endpoint: str, data: Optional[Dict] = None):
    """Make API request."""
    url = f"{API_BASE_URL}{endpoint}"
    async with httpx.AsyncClient() as client:
        if method == "GET":
            response = await client.get(url)
        elif method == "POST":
            response = await client.post(url, json=data)
        elif method == "PUT":
            response = await client.put(url, json=data)
        elif method == "DELETE":
            response = await client.delete(url)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        return response.json() if response.content else None


# Page: Workflow Designer
def workflow_designer_page():
    """Visual workflow designer page."""
    st.title("🎨 Workflow Designer")
    st.markdown("Design and configure your workflows visually")

    # Workflow configuration
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Workflow Configuration")

        workflow_name = st.text_input("Workflow Name", value="My Workflow")
        workflow_description = st.text_area(
            "Description", value="Workflow description"
        )
        workflow_category = st.selectbox(
            "Category",
            ["Data Processing", "ETL", "ML Pipeline", "API Integration", "Other"],
        )

        # Enable scheduling
        enable_schedule = st.checkbox("Enable Scheduling")
        if enable_schedule:
            cron_expression = st.text_input(
                "Cron Expression", value="0 0 * * *", help="Run daily at midnight"
            )
        else:
            cron_expression = None

    with col2:
        st.subheader("Quick Actions")
        if st.button("📥 Load Template", use_container_width=True):
            st.info("Load a workflow template")
        if st.button("💾 Save Draft", use_container_width=True):
            st.success("Draft saved!")
        if st.button("🔍 Validate", use_container_width=True):
            st.info("Validating workflow...")

    st.divider()

    # Task builder
    st.subheader("📋 Task Builder")

    # Initialize session state for tasks
    if "tasks" not in st.session_state:
        st.session_state.tasks = []

    # Add task form
    with st.expander("➕ Add New Task", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            task_key = st.text_input("Task Key", value="task_1")
            task_name = st.text_input("Task Name", value="New Task")

        with col2:
            task_type = st.selectbox(
                "Task Type", ["python", "http", "bash", "sql", "docker"]
            )
            depends_on = st.multiselect(
                "Depends On",
                [task["task_key"] for task in st.session_state.tasks],
            )

        with col3:
            max_retries = st.number_input("Max Retries", min_value=0, value=3)
            timeout = st.number_input("Timeout (seconds)", min_value=1, value=3600)

        # Task configuration based on type
        st.subheader("Task Configuration")

        if task_type == "python":
            code = st.text_area(
                "Python Code",
                value='output["result"] = "Hello from task!"',
                height=150,
            )
            task_config = {"code": code}

        elif task_type == "http":
            method = st.selectbox("HTTP Method", ["GET", "POST", "PUT", "DELETE"])
            url = st.text_input("URL", value="https://api.example.com/endpoint")
            headers = st.text_area("Headers (JSON)", value="{}")
            task_config = {
                "method": method,
                "url": url,
                "headers": json.loads(headers) if headers else {},
            }

        elif task_type == "bash":
            command = st.text_area("Bash Command", value="echo 'Hello World'")
            task_config = {"command": command}

        elif task_type == "sql":
            query = st.text_area("SQL Query", value="SELECT * FROM users LIMIT 10")
            task_config = {"query": query}

        else:
            task_config = {}

        if st.button("Add Task", type="primary"):
            task = {
                "task_key": task_key,
                "name": task_name,
                "task_type": task_type,
                "config": task_config,
                "depends_on": depends_on,
                "retry_config": {
                    "max_retries": max_retries,
                    "retry_delay": 60,
                    "timeout": timeout,
                },
            }
            st.session_state.tasks.append(task)
            st.success(f"Task '{task_name}' added!")
            st.rerun()

    # Display tasks
    if st.session_state.tasks:
        st.subheader("📊 Workflow Tasks")

        tasks_df = pd.DataFrame(
            [
                {
                    "Task Key": task["task_key"],
                    "Name": task["name"],
                    "Type": task["task_type"],
                    "Dependencies": ", ".join(task["depends_on"]),
                }
                for task in st.session_state.tasks
            ]
        )

        st.dataframe(tasks_df, use_container_width=True)

        # Visualize DAG
        st.subheader("🔄 Workflow Visualization")
        visualize_dag(st.session_state.tasks)

        # Actions
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🚀 Create Workflow", type="primary", use_container_width=True):
                create_workflow(
                    workflow_name,
                    workflow_description,
                    workflow_category,
                    cron_expression,
                    st.session_state.tasks,
                )

        with col2:
            if st.button("🗑️ Clear All Tasks", use_container_width=True):
                st.session_state.tasks = []
                st.rerun()

        with col3:
            if st.button("📋 Export JSON", use_container_width=True):
                dag_definition = {"tasks": {task["task_key"]: task for task in st.session_state.tasks}}
                st.download_button(
                    "Download Workflow JSON",
                    data=json.dumps(dag_definition, indent=2),
                    file_name="workflow.json",
                    mime="application/json",
                )


def visualize_dag(tasks: List[Dict[str, Any]]):
    """Visualize workflow DAG."""
    if not tasks:
        st.info("No tasks to visualize")
        return

    # Create nodes and edges
    nodes = []
    edges = []

    for task in tasks:
        nodes.append(task["task_key"])

        for dep in task["depends_on"]:
            edges.append((dep, task["task_key"]))

    # Create network graph using Plotly
    import networkx as nx

    G = nx.DiGraph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)

    # Layout
    try:
        pos = nx.spring_layout(G, k=2, iterations=50)
    except:
        pos = {node: (i, 0) for i, node in enumerate(nodes)}

    # Create traces
    edge_trace = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_trace.append(
            go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode="lines",
                line=dict(width=2, color="#888"),
                hoverinfo="none",
            )
        )

    node_trace = go.Scatter(
        x=[pos[node][0] for node in G.nodes()],
        y=[pos[node][1] for node in G.nodes()],
        mode="markers+text",
        text=[node for node in G.nodes()],
        textposition="top center",
        marker=dict(size=20, color="#1f77b4", line=dict(width=2, color="white")),
        hoverinfo="text",
    )

    # Create figure
    fig = go.Figure(data=edge_trace + [node_trace])
    fig.update_layout(
        showlegend=False,
        hovermode="closest",
        margin=dict(b=0, l=0, r=0, t=0),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)


def create_workflow(
    name: str,
    description: str,
    category: str,
    cron_expression: Optional[str],
    tasks: List[Dict[str, Any]],
):
    """Create workflow via API."""
    try:
        dag_definition = {"tasks": {task["task_key"]: task for task in tasks}}

        workflow_data = {
            "name": name,
            "description": description,
            "category": category,
            "dag_definition": dag_definition,
            "schedule_cron": cron_expression,
            "is_scheduled": bool(cron_expression),
            "tags": [],
        }

        # Make API request (synchronous for now)
        import requests

        response = requests.post(f"{API_BASE_URL}/workflows/", json=workflow_data)
        response.raise_for_status()

        st.success(f"✅ Workflow '{name}' created successfully!")
        st.session_state.tasks = []

    except Exception as e:
        st.error(f"❌ Failed to create workflow: {str(e)}")


# Page: Workflows List
def workflows_list_page():
    """List all workflows."""
    st.title("📋 Workflows")
    st.markdown("Manage and monitor your workflows")

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.selectbox(
            "Filter by Status", ["All", "created", "running", "completed", "failed"]
        )

    with col2:
        category_filter = st.text_input("Filter by Category")

    with col3:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    # Fetch workflows
    try:
        import requests

        params = {}
        if status_filter != "All":
            params["status"] = status_filter
        if category_filter:
            params["category"] = category_filter

        response = requests.get(f"{API_BASE_URL}/workflows/", params=params)
        response.raise_for_status()
        workflows = response.json()

        if workflows:
            # Display workflows
            for workflow in workflows:
                with st.expander(
                    f"🔄 {workflow['name']} - {workflow['status'].upper()}", expanded=False
                ):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write(f"**ID:** {workflow['id']}")
                        st.write(f"**Category:** {workflow.get('category', 'N/A')}")
                        st.write(f"**Status:** {workflow['status']}")

                    with col2:
                        st.write(f"**Total Runs:** {workflow['total_runs']}")
                        st.write(f"**Successful:** {workflow['successful_runs']}")
                        st.write(f"**Failed:** {workflow['failed_runs']}")

                    with col3:
                        if st.button(f"▶️ Run", key=f"run_{workflow['id']}"):
                            trigger_workflow(workflow['id'])
                        if st.button(f"🗑️ Delete", key=f"del_{workflow['id']}"):
                            delete_workflow(workflow['id'])

                    st.write(f"**Description:** {workflow.get('description', 'No description')}")

        else:
            st.info("No workflows found. Create your first workflow!")

    except Exception as e:
        st.error(f"Failed to load workflows: {str(e)}")


def trigger_workflow(workflow_id: int):
    """Trigger workflow execution."""
    try:
        import requests

        response = requests.post(f"{API_BASE_URL}/workflows/{workflow_id}/trigger")
        response.raise_for_status()

        st.success(f"✅ Workflow {workflow_id} triggered successfully!")

    except Exception as e:
        st.error(f"❌ Failed to trigger workflow: {str(e)}")


def delete_workflow(workflow_id: int):
    """Delete workflow."""
    try:
        import requests

        response = requests.delete(f"{API_BASE_URL}/workflows/{workflow_id}")
        response.raise_for_status()

        st.success(f"✅ Workflow {workflow_id} deleted successfully!")
        st.rerun()

    except Exception as e:
        st.error(f"❌ Failed to delete workflow: {str(e)}")


# Page: Executions
def executions_page():
    """View workflow executions."""
    st.title("⚡ Executions")
    st.markdown("Monitor workflow execution history")

    # Fetch executions
    try:
        import requests

        response = requests.get(f"{API_BASE_URL}/executions/", params={"limit": 50})
        response.raise_for_status()
        executions = response.json()

        if executions:
            # Create DataFrame
            executions_df = pd.DataFrame(
                [
                    {
                        "Run ID": exec["run_id"],
                        "Workflow ID": exec["workflow_id"],
                        "Status": exec["status"],
                        "Started": exec["started_at"],
                        "Duration": f"{exec.get('duration', 0):.2f}s",
                        "Tasks": f"{exec['completed_tasks']}/{exec['total_tasks']}",
                    }
                    for exec in executions
                ]
            )

            # Display
            st.dataframe(executions_df, use_container_width=True)

            # Execution details
            selected_run_id = st.selectbox(
                "Select execution for details",
                [exec["run_id"] for exec in executions],
            )

            if selected_run_id:
                selected_exec = next(
                    exec for exec in executions if exec["run_id"] == selected_run_id
                )

                st.subheader(f"Execution Details: {selected_run_id}")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Status", selected_exec["status"].upper())
                with col2:
                    st.metric("Duration", f"{selected_exec.get('duration', 0):.2f}s")
                with col3:
                    st.metric("Completed Tasks", selected_exec["completed_tasks"])
                with col4:
                    st.metric("Failed Tasks", selected_exec["failed_tasks"])

                if selected_exec.get("error_message"):
                    st.error(f"**Error:** {selected_exec['error_message']}")

        else:
            st.info("No executions found")

    except Exception as e:
        st.error(f"Failed to load executions: {str(e)}")


# Page: Dashboard
def dashboard_page():
    """Statistics dashboard."""
    st.title("📊 Dashboard")
    st.markdown("Overview of workflow orchestration system")

    # Fetch statistics
    try:
        import requests

        response = requests.get(f"{API_BASE_URL}/statistics/workflows")
        response.raise_for_status()
        stats = response.json()

        # Metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Workflows", stats["total_workflows"])
        with col2:
            st.metric("Active Workflows", stats["active_workflows"])
        with col3:
            st.metric("Total Executions", stats["total_executions"])
        with col4:
            st.metric("Success Rate", f"{stats['success_rate']:.1f}%")

        st.divider()

        # Charts
        col1, col2 = st.columns(2)

        with col1:
            # Execution status pie chart
            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=["Completed", "Failed", "Running"],
                        values=[
                            stats["completed_executions"],
                            stats["failed_executions"],
                            stats["running_executions"],
                        ],
                        marker=dict(colors=["#28a745", "#dc3545", "#007bff"]),
                    )
                ]
            )
            fig.update_layout(title="Execution Status Distribution")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Average duration
            st.metric(
                "Average Duration",
                f"{stats.get('average_duration', 0):.2f}s" if stats.get('average_duration') else "N/A",
            )

    except Exception as e:
        st.error(f"Failed to load statistics: {str(e)}")


# Main app
def main():
    """Main application."""
    st.sidebar.title("🔄 NEXUS Orchestration")

    # Navigation
    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Workflows", "Workflow Designer", "Executions"],
    )

    st.sidebar.divider()

    # API status
    st.sidebar.subheader("🔌 API Status")
    try:
        import requests

        response = requests.get(f"{API_BASE_URL}/../health", timeout=2)
        if response.status_code == 200:
            st.sidebar.success("✅ Connected")
        else:
            st.sidebar.error("❌ Disconnected")
    except:
        st.sidebar.error("❌ Disconnected")

    # Route to pages
    if page == "Dashboard":
        dashboard_page()
    elif page == "Workflows":
        workflows_list_page()
    elif page == "Workflow Designer":
        workflow_designer_page()
    elif page == "Executions":
        executions_page()


if __name__ == "__main__":
    main()
