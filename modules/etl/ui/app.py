"""Streamlit UI for ETL module."""
import streamlit as st
import requests
import pandas as pd
import os
from typing import Optional

# Configuration
API_URL = os.getenv("ETL_API_URL", "http://localhost:8001")

st.set_page_config(page_title="NEXUS ETL", page_icon="🔄", layout="wide")

# Sidebar navigation
st.sidebar.title("🔄 NEXUS ETL")
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Data Sources", "Pipelines", "Transformations", "Jobs", "Executions"],
)


def api_request(method: str, endpoint: str, data: Optional[dict] = None):
    """Make API request."""
    url = f"{API_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            return None

        if response.status_code < 400:
            return response.json() if response.content else None
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Request failed: {e}")
        return None


if page == "Dashboard":
    st.title("📊 ETL Dashboard")

    # Get execution stats
    stats = api_request("GET", "/api/v1/executions/stats/summary?days=7")

    if stats:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Executions", stats.get("total_executions", 0))

        with col2:
            st.metric("Successful", stats.get("successful", 0), delta_color="normal")

        with col3:
            st.metric("Failed", stats.get("failed", 0), delta_color="inverse")

        with col4:
            st.metric(
                "Avg Duration",
                f"{stats.get('avg_duration_seconds', 0):.2f}s",
            )

        st.metric("Total Records Processed", f"{stats.get('total_records_processed', 0):,}")

    # Recent executions
    st.subheader("Recent Executions")
    executions = api_request("GET", "/api/v1/executions?limit=10")

    if executions:
        df = pd.DataFrame(executions)
        if not df.empty:
            df = df[["pipeline_id", "status", "records_loaded", "started_at", "duration_seconds"]]
            st.dataframe(df, use_container_width=True)
    else:
        st.info("No executions found")

elif page == "Data Sources":
    st.title("📁 Data Sources")

    # List existing sources
    st.subheader("Existing Data Sources")
    sources = api_request("GET", "/api/v1/sources")

    if sources:
        for source in sources:
            with st.expander(f"{source['name']} ({source['source_type']})"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Description:** {source.get('description', 'N/A')}")
                    st.write(f"**Active:** {source['is_active']}")
                    st.write(f"**Created:** {source['created_at']}")
                with col2:
                    if st.button("Test Connection", key=f"test_{source['id']}"):
                        result = api_request("POST", f"/api/v1/sources/{source['id']}/test")
                        if result:
                            st.success("Connection test started")
                    if st.button("Delete", key=f"del_{source['id']}"):
                        api_request("DELETE", f"/api/v1/sources/{source['id']}")
                        st.rerun()
    else:
        st.info("No data sources configured")

    # Create new source
    st.subheader("Create New Data Source")
    with st.form("new_source"):
        name = st.text_input("Name")
        description = st.text_area("Description")
        source_type = st.selectbox("Type", ["csv", "json", "sql", "postgresql", "api"])

        st.write("**Connection Configuration:**")

        if source_type == "csv":
            file_path = st.text_input("File Path")
            delimiter = st.text_input("Delimiter", ",")
            encoding = st.text_input("Encoding", "utf-8")
            config = {"file_path": file_path, "delimiter": delimiter, "encoding": encoding}

        elif source_type == "json":
            file_path = st.text_input("File Path")
            encoding = st.text_input("Encoding", "utf-8")
            config = {"file_path": file_path, "encoding": encoding}

        elif source_type in ["sql", "postgresql"]:
            connection_string = st.text_input("Connection String", type="password")
            config = {"connection_string": connection_string}

        elif source_type == "api":
            base_url = st.text_input("Base URL")
            api_key = st.text_input("API Key", type="password")
            config = {"base_url": base_url, "api_key": api_key}

        if st.form_submit_button("Create Data Source"):
            if name and config:
                data = {
                    "name": name,
                    "description": description,
                    "source_type": source_type,
                    "connection_config": config,
                    "is_active": True,
                }
                result = api_request("POST", "/api/v1/sources/", data)
                if result:
                    st.success("Data source created successfully!")
                    st.rerun()

elif page == "Pipelines":
    st.title("🔧 ETL Pipelines")

    # List pipelines
    st.subheader("Existing Pipelines")
    pipelines = api_request("GET", "/api/v1/pipelines")

    if pipelines:
        for pipeline in pipelines:
            with st.expander(f"{pipeline['name']}"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Description:** {pipeline.get('description', 'N/A')}")
                    st.write(f"**Active:** {pipeline['is_active']}")
                    st.write(f"**Last Run:** {pipeline.get('last_run', 'Never')}")
                with col2:
                    if st.button("Execute", key=f"exec_{pipeline['id']}"):
                        result = api_request("POST", f"/api/v1/pipelines/{pipeline['id']}/execute")
                        if result:
                            st.success(f"Pipeline execution started! Task ID: {result['task_id']}")
                    if st.button("Delete", key=f"del_pipe_{pipeline['id']}"):
                        api_request("DELETE", f"/api/v1/pipelines/{pipeline['id']}")
                        st.rerun()
    else:
        st.info("No pipelines configured")

elif page == "Transformations":
    st.title("⚙️ Transformation Templates")

    # List transformations
    transformations = api_request("GET", "/api/v1/transformations")

    if transformations:
        df = pd.DataFrame(transformations)
        st.dataframe(df[["name", "category", "transformation_type", "usage_count"]], use_container_width=True)
    else:
        st.info("No transformation templates found")

elif page == "Jobs":
    st.title("⏰ Scheduled Jobs")

    # List jobs
    jobs = api_request("GET", "/api/v1/jobs")

    if jobs:
        for job in jobs:
            with st.expander(f"Job {job['id']}"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Pipeline ID:** {job['pipeline_id']}")
                    st.write(f"**Schedule:** {job['schedule_expression']} ({job['schedule_type']})")
                    st.write(f"**Active:** {job['is_active']}")
                    st.write(f"**Next Run:** {job.get('next_run', 'N/A')}")
                with col2:
                    if job['is_active']:
                        if st.button("Pause", key=f"pause_{job['id']}"):
                            api_request("POST", f"/api/v1/jobs/{job['id']}/pause")
                            st.rerun()
                    else:
                        if st.button("Resume", key=f"resume_{job['id']}"):
                            api_request("POST", f"/api/v1/jobs/{job['id']}/resume")
                            st.rerun()
    else:
        st.info("No scheduled jobs")

elif page == "Executions":
    st.title("📈 Execution History")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        days = st.selectbox("Time Range", [1, 7, 30, 90], index=1)
    with col2:
        status_filter = st.selectbox("Status", ["All", "completed", "failed", "running"])
    with col3:
        limit = st.number_input("Limit", min_value=10, max_value=100, value=50)

    # Build query
    query = f"/api/v1/executions?limit={limit}&days={days}"
    if status_filter != "All":
        query += f"&status={status_filter}"

    executions = api_request("GET", query)

    if executions:
        df = pd.DataFrame(executions)
        if not df.empty:
            # Display summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total", len(df))
            with col2:
                completed = len(df[df["status"] == "completed"])
                st.metric("Completed", completed)
            with col3:
                failed = len(df[df["status"] == "failed"])
                st.metric("Failed", failed)

            # Display table
            display_df = df[
                [
                    "id",
                    "pipeline_id",
                    "status",
                    "records_extracted",
                    "records_loaded",
                    "started_at",
                    "duration_seconds",
                ]
            ]
            st.dataframe(display_df, use_container_width=True)

            # Execution details
            st.subheader("Execution Details")
            selected_id = st.selectbox("Select Execution", df["id"].tolist())
            if selected_id:
                execution = api_request("GET", f"/api/v1/executions/{selected_id}")
                if execution:
                    st.json(execution)
    else:
        st.info("No executions found")

# Footer
st.sidebar.markdown("---")
st.sidebar.info("🔄 NEXUS ETL Module v0.1.0")
