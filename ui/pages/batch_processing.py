"""Streamlit page for Batch Processing module."""

import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time
from typing import Optional, Dict, Any
import plotly.express as px
import plotly.graph_objects as go

# API Base URL - adjust as needed
API_BASE_URL = "http://localhost:8000/api/v1/batch"


def init_session_state():
    """Initialize session state variables."""
    if "selected_job_id" not in st.session_state:
        st.session_state.selected_job_id = None
    if "auto_refresh" not in st.session_state:
        st.session_state.auto_refresh = False


def make_api_request(endpoint: str, method: str = "GET", data: Dict = None) -> Optional[Dict]:
    """Make API request with error handling."""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        elif method == "PATCH":
            response = requests.patch(url, json=data)

        response.raise_for_status()
        return response.json() if response.content else None
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None


def show_stats():
    """Display batch processing statistics."""
    stats = make_api_request("/stats")

    if stats:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Jobs", stats["total_jobs"])
        with col2:
            st.metric("Running Jobs", stats["running_jobs"])
        with col3:
            st.metric("Completed Jobs", stats["completed_jobs"])
        with col4:
            st.metric("Success Rate", f"{stats['average_success_rate']:.1f}%")

        # Status distribution chart
        status_data = {
            "Status": ["Pending", "Running", "Completed", "Failed", "Cancelled"],
            "Count": [
                stats["pending_jobs"],
                stats["running_jobs"],
                stats["completed_jobs"],
                stats["failed_jobs"],
                stats["cancelled_jobs"]
            ]
        }

        fig = px.pie(
            status_data,
            values="Count",
            names="Status",
            title="Job Status Distribution",
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        st.plotly_chart(fig, use_container_width=True)


def create_batch_job():
    """Form to create a new batch job."""
    st.subheader("📝 Create New Batch Job")

    with st.form("create_job_form"):
        job_name = st.text_input("Job Name*", placeholder="My Batch Job")
        job_description = st.text_area("Description", placeholder="Optional description")

        job_type = st.selectbox(
            "Job Type*",
            ["csv_import", "data_transformation", "data_export", "custom"]
        )

        # File upload
        uploaded_file = st.file_uploader(
            "Upload Data File (CSV/Excel)",
            type=["csv", "xlsx", "xls"]
        )

        # Advanced options
        with st.expander("⚙️ Advanced Options"):
            chunk_size = st.slider("Chunk Size", 10, 1000, 100)
            parallel_workers = st.slider("Parallel Workers", 1, 16, 4)
            max_retries = st.slider("Max Retries", 0, 10, 3)

        submitted = st.form_submit_button("Create Job", type="primary")

        if submitted:
            if not job_name:
                st.error("Job name is required")
                return

            # Create job
            job_data = {
                "name": job_name,
                "description": job_description,
                "job_type": job_type,
                "config": {
                    "chunk_size": chunk_size,
                    "parallel_workers": parallel_workers,
                    "max_retries": max_retries
                },
                "metadata": {}
            }

            if uploaded_file:
                # TODO: Handle file upload
                st.info(f"File uploaded: {uploaded_file.name}")

            result = make_api_request("/jobs", method="POST", data=job_data)

            if result:
                st.success(f"✅ Job created successfully! Job ID: {result['id']}")
                st.session_state.selected_job_id = result["id"]
                st.rerun()


def list_batch_jobs():
    """Display list of batch jobs."""
    st.subheader("📋 Batch Jobs")

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "pending", "running", "completed", "failed", "cancelled"]
        )

    with col2:
        job_type_filter = st.text_input("Job Type", "")

    with col3:
        limit = st.number_input("Items per page", 10, 100, 20)

    # Build query params
    query_params = f"?limit={limit}"
    if status_filter != "All":
        query_params += f"&status={status_filter}"
    if job_type_filter:
        query_params += f"&job_type={job_type_filter}"

    # Fetch jobs
    response = make_api_request(f"/jobs{query_params}")

    if response and response.get("jobs"):
        jobs = response["jobs"]

        # Display as table
        for job in jobs:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

                with col1:
                    st.write(f"**{job['name']}**")
                    st.caption(f"ID: {job['id']} | Type: {job['job_type']}")

                with col2:
                    status_emoji = {
                        "pending": "⏳",
                        "running": "▶️",
                        "completed": "✅",
                        "failed": "❌",
                        "cancelled": "🚫"
                    }
                    st.write(f"{status_emoji.get(job['status'], '❓')} {job['status'].upper()}")

                with col3:
                    if job['total_items'] > 0:
                        st.progress(job['progress_percentage'] / 100)
                        st.caption(f"{job['processed_items']}/{job['total_items']} items")
                    else:
                        st.caption("No items")

                with col4:
                    if st.button("View Details", key=f"view_{job['id']}"):
                        st.session_state.selected_job_id = job['id']
                        st.rerun()

                st.divider()
    else:
        st.info("No batch jobs found")


def show_job_details(job_id: int):
    """Display detailed view of a batch job."""
    job = make_api_request(f"/jobs/{job_id}")

    if not job:
        st.error(f"Job {job_id} not found")
        return

    # Header
    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader(f"📊 {job['name']}")
        st.caption(f"Job ID: {job['id']} | Type: {job['job_type']}")

    with col2:
        if st.button("← Back to List"):
            st.session_state.selected_job_id = None
            st.rerun()

    # Status badge
    status_colors = {
        "pending": "🟡",
        "running": "🔵",
        "completed": "🟢",
        "failed": "🔴",
        "cancelled": "⚫"
    }
    st.markdown(f"### Status: {status_colors.get(job['status'], '⚪')} {job['status'].upper()}")

    # Progress
    if job['total_items'] > 0:
        st.progress(job['progress_percentage'] / 100)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Items", job['total_items'])
        col2.metric("Processed", job['processed_items'])
        col3.metric("Successful", job['successful_items'])
        col4.metric("Failed", job['failed_items'])

    # Actions
    st.subheader("Actions")
    action_col1, action_col2, action_col3, action_col4 = st.columns(4)

    with action_col1:
        if job['status'] == 'pending':
            if st.button("▶️ Start Job", type="primary"):
                result = make_api_request(f"/jobs/{job_id}/start", method="POST")
                if result:
                    st.success("Job started!")
                    time.sleep(1)
                    st.rerun()

    with action_col2:
        if job['status'] in ['running', 'pending']:
            if st.button("⏸️ Cancel Job", type="secondary"):
                result = make_api_request(f"/jobs/{job_id}/cancel", method="POST")
                if result:
                    st.warning("Job cancelled")
                    time.sleep(1)
                    st.rerun()

    with action_col3:
        if job['failed_items'] > 0:
            if st.button("🔄 Retry Failed"):
                result = make_api_request(f"/jobs/{job_id}/retry", method="POST")
                if result:
                    st.info("Retrying failed tasks...")
                    time.sleep(1)
                    st.rerun()

    with action_col4:
        if st.button("🔄 Refresh"):
            st.rerun()

    # Timing information
    st.subheader("Timing")
    timing_col1, timing_col2, timing_col3 = st.columns(3)

    with timing_col1:
        created_at = datetime.fromisoformat(job['created_at'].replace('Z', '+00:00'))
        st.write(f"**Created:** {created_at.strftime('%Y-%m-%d %H:%M:%S')}")

    with timing_col2:
        if job['started_at']:
            started_at = datetime.fromisoformat(job['started_at'].replace('Z', '+00:00'))
            st.write(f"**Started:** {started_at.strftime('%Y-%m-%d %H:%M:%S')}")

    with timing_col3:
        if job['completed_at']:
            completed_at = datetime.fromisoformat(job['completed_at'].replace('Z', '+00:00'))
            st.write(f"**Completed:** {completed_at.strftime('%Y-%m-%d %H:%M:%S')}")

    # Tasks
    st.subheader("Tasks")
    tasks_response = make_api_request(f"/jobs/{job_id}/tasks?limit=50")

    if tasks_response and tasks_response.get("tasks"):
        tasks = tasks_response["tasks"]

        # Task status summary
        task_statuses = {}
        for task in tasks:
            status = task['status']
            task_statuses[status] = task_statuses.get(status, 0) + 1

        status_cols = st.columns(len(task_statuses))
        for idx, (status, count) in enumerate(task_statuses.items()):
            status_cols[idx].metric(status.title(), count)

        # Task table
        task_df = pd.DataFrame([
            {
                "Task #": task['task_number'],
                "Status": task['status'],
                "Duration (s)": task['duration_seconds'] or 0,
                "Retries": task['retry_count']
            }
            for task in tasks
        ])

        st.dataframe(task_df, use_container_width=True)

    # Error logs
    if job['failed_items'] > 0:
        st.subheader("❌ Error Logs")
        errors_response = make_api_request(f"/jobs/{job_id}/errors")

        if errors_response and errors_response.get("errors"):
            with st.expander(f"View {len(errors_response['errors'])} errors"):
                for error in errors_response["errors"][:10]:  # Show first 10
                    st.error(f"Task #{error['task_number']}: {error['error_message']}")

    # Configuration
    with st.expander("⚙️ Configuration"):
        st.json(job.get('config', {}))

    # Auto-refresh toggle
    st.session_state.auto_refresh = st.checkbox("Auto-refresh (5s)", value=st.session_state.auto_refresh)

    if st.session_state.auto_refresh and job['status'] == 'running':
        time.sleep(5)
        st.rerun()


def main():
    """Main function for Batch Processing page."""
    st.set_page_config(
        page_title="Batch Processing - NEXUS",
        page_icon="⚙️",
        layout="wide"
    )

    st.title("⚙️ Batch Processing")
    st.markdown("Manage large-scale data processing jobs with parallel execution and monitoring.")

    init_session_state()

    # Sidebar
    with st.sidebar:
        st.header("📊 Statistics")
        show_stats()

    # Main content
    if st.session_state.selected_job_id:
        show_job_details(st.session_state.selected_job_id)
    else:
        tab1, tab2 = st.tabs(["📋 Job List", "➕ Create Job"])

        with tab1:
            list_batch_jobs()

        with tab2:
            create_batch_job()


if __name__ == "__main__":
    main()
