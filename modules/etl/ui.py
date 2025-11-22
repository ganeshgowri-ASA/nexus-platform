"""
Streamlit dashboard for ETL module.

This module provides an interactive web interface for managing
and monitoring ETL jobs, pipelines, and data flows.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Optional

# Configure page
st.set_page_config(
    page_title="NEXUS ETL Dashboard",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded"
)


def init_session_state():
    """Initialize session state variables."""
    if "db_session" not in st.session_state:
        st.session_state.db_session = None
    if "selected_job" not in st.session_state:
        st.session_state.selected_job = None


def main():
    """Main dashboard function."""
    init_session_state()

    st.title("🔄 NEXUS ETL Dashboard")
    st.markdown("---")

    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Navigation",
        [
            "📊 Overview",
            "🔌 Data Sources",
            "🎯 Data Targets",
            "⚙️ ETL Jobs",
            "📈 Job Runs",
            "🗺️ Mappings",
            "✅ Data Quality",
            "📡 Monitoring",
            "⏰ Scheduler"
        ]
    )

    # Route to selected page
    if page == "📊 Overview":
        show_overview()
    elif page == "🔌 Data Sources":
        show_data_sources()
    elif page == "🎯 Data Targets":
        show_data_targets()
    elif page == "⚙️ ETL Jobs":
        show_etl_jobs()
    elif page == "📈 Job Runs":
        show_job_runs()
    elif page == "🗺️ Mappings":
        show_mappings()
    elif page == "✅ Data Quality":
        show_data_quality()
    elif page == "📡 Monitoring":
        show_monitoring()
    elif page == "⏰ Scheduler":
        show_scheduler()


def show_overview():
    """Show overview dashboard."""
    st.header("📊 ETL Overview")

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Jobs",
            value=42,
            delta="3 new"
        )

    with col2:
        st.metric(
            "Success Rate",
            value="94.2%",
            delta="2.1%"
        )

    with col3:
        st.metric(
            "Records Processed",
            value="1.2M",
            delta="150K"
        )

    with col4:
        st.metric(
            "Avg Execution Time",
            value="12.4 min",
            delta="-1.2 min"
        )

    st.markdown("---")

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Job Execution Trend")
        # Sample data
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        data = pd.DataFrame({
            'Date': dates,
            'Successful': [20 + i % 5 for i in range(30)],
            'Failed': [2 + i % 3 for i in range(30)]
        })

        fig = px.line(data, x='Date', y=['Successful', 'Failed'],
                     title='Job Executions (Last 30 Days)')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Job Status Distribution")
        # Sample data
        status_data = pd.DataFrame({
            'Status': ['Completed', 'Running', 'Failed', 'Pending'],
            'Count': [85, 5, 8, 2]
        })

        fig = px.pie(status_data, values='Count', names='Status',
                    title='Current Job Status')
        st.plotly_chart(fig, use_container_width=True)

    # Recent job runs
    st.subheader("Recent Job Runs")
    recent_runs = pd.DataFrame({
        'Job': [f'Job_{i}' for i in range(1, 6)],
        'Status': ['Completed', 'Running', 'Completed', 'Failed', 'Completed'],
        'Duration': ['5m 23s', '2m 15s', '8m 42s', '1m 05s', '12m 34s'],
        'Records': [1200, 500, 3400, 0, 5600],
        'Started': [f'{i}h ago' for i in range(1, 6)]
    })

    st.dataframe(recent_runs, use_container_width=True)


def show_data_sources():
    """Show data sources page."""
    st.header("🔌 Data Sources")

    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("➕ New Source"):
            show_create_source_form()
    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()

    st.markdown("---")

    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        source_type = st.selectbox(
            "Source Type",
            ["All", "Database", "File", "API", "Cloud Storage"]
        )
    with col2:
        status_filter = st.selectbox(
            "Status",
            ["All", "Active", "Inactive"]
        )

    # Sources table
    sources_data = pd.DataFrame({
        'ID': [1, 2, 3, 4],
        'Name': ['MySQL Production', 'S3 Data Lake', 'REST API', 'PostgreSQL DW'],
        'Type': ['Database', 'Cloud Storage', 'API', 'Database'],
        'Status': ['Active', 'Active', 'Inactive', 'Active'],
        'Jobs': [5, 3, 1, 8],
        'Last Used': ['2h ago', '1d ago', '1w ago', '30m ago']
    })

    st.dataframe(sources_data, use_container_width=True)

    # Connection test
    st.subheader("Test Connection")
    test_source = st.selectbox("Select Source", sources_data['Name'])
    if st.button("Test Connection"):
        with st.spinner("Testing connection..."):
            st.success("✅ Connection successful!")


def show_data_targets():
    """Show data targets page."""
    st.header("🎯 Data Targets")

    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("➕ New Target"):
            show_create_target_form()

    st.markdown("---")

    targets_data = pd.DataFrame({
        'ID': [1, 2, 3],
        'Name': ['Data Warehouse', 'Analytics DB', 'Export Bucket'],
        'Type': ['Database', 'Database', 'Cloud Storage'],
        'Status': ['Active', 'Active', 'Active'],
        'Jobs': [12, 5, 3]
    })

    st.dataframe(targets_data, use_container_width=True)


def show_etl_jobs():
    """Show ETL jobs page."""
    st.header("⚙️ ETL Jobs")

    # Action buttons
    col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
    with col1:
        if st.button("➕ New Job"):
            show_create_job_form()
    with col2:
        if st.button("▶️ Run Selected"):
            st.info("Job execution started")
    with col3:
        if st.button("🔄 Refresh"):
            st.rerun()

    st.markdown("---")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.multiselect(
            "Status",
            ["Active", "Inactive", "Scheduled"],
            default=["Active"]
        )
    with col2:
        search = st.text_input("Search Jobs", "")

    # Jobs table
    jobs_data = pd.DataFrame({
        'ID': [1, 2, 3, 4, 5],
        'Name': ['Daily Sales Sync', 'Customer Data ETL', 'Inventory Update', 'Analytics Pipeline', 'Report Generation'],
        'Source': ['MySQL', 'API', 'PostgreSQL', 'S3', 'MongoDB'],
        'Target': ['Data Warehouse', 'Analytics DB', 'Data Warehouse', 'Analytics DB', 'Export Bucket'],
        'Schedule': ['Daily 2AM', 'Hourly', 'Every 4h', 'Daily 3AM', 'Weekly Mon'],
        'Status': ['Active', 'Active', 'Active', 'Inactive', 'Active'],
        'Last Run': ['2h ago', '45m ago', '1h ago', '2d ago', '3d ago'],
        'Success Rate': ['98%', '95%', '100%', '92%', '97%']
    })

    # Allow row selection
    selected_rows = st.dataframe(
        jobs_data,
        use_container_width=True,
        hide_index=True
    )

    # Job details
    if st.session_state.selected_job:
        show_job_details(st.session_state.selected_job)


def show_job_runs():
    """Show job runs history page."""
    st.header("📈 Job Runs History")

    # Filters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        job_filter = st.selectbox("Job", ["All Jobs", "Job 1", "Job 2", "Job 3"])
    with col2:
        status_filter = st.multiselect(
            "Status",
            ["Completed", "Running", "Failed", "Pending"],
            default=["Completed", "Running", "Failed"]
        )
    with col3:
        date_range = st.date_input(
            "Date Range",
            value=(datetime.now() - timedelta(days=7), datetime.now())
        )

    # Runs table
    runs_data = pd.DataFrame({
        'Run ID': list(range(1, 11)),
        'Job': [f'Job {i % 3 + 1}' for i in range(10)],
        'Status': ['Completed'] * 7 + ['Failed', 'Running', 'Pending'],
        'Started': [f'{i}h ago' for i in range(1, 11)],
        'Duration': [f'{5 + i}m {20 + i * 3}s' for i in range(10)],
        'Records': [1000 + i * 500 for i in range(10)],
        'Quality Score': [95.5 + i * 0.3 for i in range(10)]
    })

    # Color code by status
    def highlight_status(row):
        if row['Status'] == 'Failed':
            return ['background-color: #ffebee'] * len(row)
        elif row['Status'] == 'Running':
            return ['background-color: #e3f2fd'] * len(row)
        elif row['Status'] == 'Completed':
            return ['background-color: #e8f5e9'] * len(row)
        return [''] * len(row)

    st.dataframe(
        runs_data.style.apply(highlight_status, axis=1),
        use_container_width=True
    )

    # Execution timeline
    st.subheader("Execution Timeline")
    fig = go.Figure()

    for i, row in runs_data.iterrows():
        color = {
            'Completed': 'green',
            'Failed': 'red',
            'Running': 'blue',
            'Pending': 'gray'
        }[row['Status']]

        fig.add_trace(go.Scatter(
            x=[i],
            y=[row['Records']],
            mode='markers',
            marker=dict(size=10, color=color),
            name=row['Status'],
            showlegend=i == 0
        ))

    fig.update_layout(
        title='Records Processed Over Time',
        xaxis_title='Run ID',
        yaxis_title='Records'
    )
    st.plotly_chart(fig, use_container_width=True)


def show_mappings():
    """Show field mappings page."""
    st.header("🗺️ Field Mappings")

    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("➕ New Mapping"):
            show_create_mapping_form()

    st.markdown("---")

    mappings_data = pd.DataFrame({
        'ID': [1, 2, 3],
        'Name': ['Sales Mapping', 'Customer Mapping', 'Product Mapping'],
        'Fields': [15, 23, 12],
        'Jobs': [3, 5, 2],
        'Status': ['Active', 'Active', 'Inactive']
    })

    st.dataframe(mappings_data, use_container_width=True)


def show_data_quality():
    """Show data quality dashboard."""
    st.header("✅ Data Quality")

    # Quality metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Overall Quality Score", "94.2%", "2.1%")
    with col2:
        st.metric("Data Completeness", "98.5%", "0.5%")
    with col3:
        st.metric("Data Accuracy", "96.8%", "-0.3%")
    with col4:
        st.metric("Validation Errors", "127", "-23")

    st.markdown("---")

    # Quality trends
    st.subheader("Quality Score Trend")
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    quality_data = pd.DataFrame({
        'Date': dates,
        'Quality Score': [92 + i % 8 for i in range(30)]
    })

    fig = px.line(quality_data, x='Date', y='Quality Score',
                 title='Data Quality Score (Last 30 Days)')
    fig.add_hline(y=90, line_dash="dash", line_color="red",
                  annotation_text="Threshold")
    st.plotly_chart(fig, use_container_width=True)

    # Validation rules
    st.subheader("Validation Rules")
    rules_data = pd.DataFrame({
        'Rule': ['Null Check', 'Range Check', 'Format Check', 'Uniqueness'],
        'Fields': [5, 3, 7, 2],
        'Violations': [12, 5, 23, 3],
        'Status': ['Active', 'Active', 'Active', 'Active']
    })

    st.dataframe(rules_data, use_container_width=True)


def show_monitoring():
    """Show monitoring dashboard."""
    st.header("📡 System Monitoring")

    # System health
    st.subheader("System Health")
    health_status = st.success("✅ System is healthy")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Running Jobs", "3")
    with col2:
        st.metric("Queue Size", "5")
    with col3:
        st.metric("System Load", "45%")

    st.markdown("---")

    # Performance metrics
    st.subheader("Performance Metrics")

    col1, col2 = st.columns(2)

    with col1:
        # Execution time distribution
        exec_times = pd.DataFrame({
            'Job': [f'Job {i}' for i in range(1, 11)],
            'Avg Time (min)': [5 + i * 1.5 for i in range(10)]
        })

        fig = px.bar(exec_times, x='Job', y='Avg Time (min)',
                    title='Average Execution Time by Job')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Throughput
        throughput = pd.DataFrame({
            'Hour': list(range(24)),
            'Records/Hour': [1000 + i * 100 + (i % 3) * 200 for i in range(24)]
        })

        fig = px.line(throughput, x='Hour', y='Records/Hour',
                     title='Hourly Throughput')
        st.plotly_chart(fig, use_container_width=True)

    # Alerts
    st.subheader("Recent Alerts")
    alerts_data = pd.DataFrame({
        'Time': ['10 min ago', '2 hours ago', '1 day ago'],
        'Severity': ['Warning', 'Error', 'Info'],
        'Message': [
            'Job execution taking longer than usual',
            'Job failed: Connection timeout',
            'New data source added'
        ]
    })

    st.dataframe(alerts_data, use_container_width=True)


def show_scheduler():
    """Show job scheduler page."""
    st.header("⏰ Job Scheduler")

    st.subheader("Scheduled Jobs")

    scheduled_jobs = pd.DataFrame({
        'Job': ['Daily Sales Sync', 'Customer Data ETL', 'Inventory Update'],
        'Schedule': ['Daily at 2:00 AM', 'Every hour', 'Every 4 hours'],
        'Next Run': ['Today 2:00 AM', 'In 15 minutes', 'In 2 hours'],
        'Enabled': [True, True, False]
    })

    st.dataframe(scheduled_jobs, use_container_width=True)

    # Schedule visualization
    st.subheader("Schedule Timeline")
    st.info("Calendar view of scheduled jobs (coming soon)")


# Helper functions for forms
def show_create_source_form():
    """Show form to create new data source."""
    with st.form("create_source"):
        st.subheader("Create Data Source")

        name = st.text_input("Name")
        source_type = st.selectbox("Type", ["Database", "File", "API", "Cloud Storage"])

        if source_type == "Database":
            db_type = st.selectbox("Database Type", ["PostgreSQL", "MySQL", "MongoDB"])
            host = st.text_input("Host")
            port = st.number_input("Port", value=5432)
            database = st.text_input("Database")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

        submitted = st.form_submit_button("Create")
        if submitted:
            st.success("Data source created successfully!")


def show_create_target_form():
    """Show form to create new data target."""
    st.info("Create target form (implementation needed)")


def show_create_job_form():
    """Show form to create new ETL job."""
    with st.form("create_job"):
        st.subheader("Create ETL Job")

        name = st.text_input("Job Name")
        source = st.selectbox("Source", ["Source 1", "Source 2"])
        target = st.selectbox("Target", ["Target 1", "Target 2"])
        schedule = st.text_input("Schedule (cron)", "0 2 * * *")

        submitted = st.form_submit_button("Create")
        if submitted:
            st.success("ETL job created successfully!")


def show_create_mapping_form():
    """Show form to create new mapping."""
    st.info("Create mapping form (implementation needed)")


def show_job_details(job_id):
    """Show detailed information about a job."""
    st.subheader(f"Job Details: {job_id}")
    st.info("Job details view (implementation needed)")


if __name__ == "__main__":
    main()
