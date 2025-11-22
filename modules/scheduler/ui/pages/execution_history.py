"""Execution history page"""
import streamlit as st
import httpx
import pandas as pd
from datetime import datetime

API_BASE_URL = "http://localhost:8000/api/v1"


def show():
    """Display execution history"""
    st.markdown('<div class="main-header">📜 Execution History</div>', unsafe_allow_html=True)

    # Fetch all jobs for filter
    try:
        jobs_response = httpx.get(f"{API_BASE_URL}/jobs/", timeout=10)
        if jobs_response.status_code == 200:
            all_jobs = jobs_response.json()
            job_options = {f"{j['name']} (ID: {j['id']})": j['id'] for j in all_jobs}
        else:
            job_options = {}
    except:
        job_options = {}

    # Filters
    col1, col2 = st.columns(2)

    with col1:
        if job_options:
            selected_job = st.selectbox("Filter by Job", ["All Jobs"] + list(job_options.keys()))
        else:
            selected_job = None

    with col2:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "completed", "failed", "running", "pending"]
        )

    # Get selected job ID
    job_id = None
    if selected_job and selected_job != "All Jobs":
        job_id = job_options[selected_job]

    # Fetch executions
    try:
        if job_id:
            response = httpx.get(f"{API_BASE_URL}/jobs/{job_id}/executions", timeout=10)
        else:
            # Would need a general executions endpoint
            st.info("Select a job to view its execution history")
            response = None

        if response and response.status_code == 200:
            executions = response.json()

            # Filter by status
            if status_filter != "All":
                executions = [e for e in executions if e['status'] == status_filter]

            if executions:
                st.write(f"**Total Executions:** {len(executions)}")
                st.markdown("---")

                # Create DataFrame for better display
                df_data = []
                for exec in executions:
                    df_data.append({
                        'ID': exec['id'],
                        'Status': exec['status'],
                        'Scheduled': exec['scheduled_at'],
                        'Started': exec['started_at'] or 'N/A',
                        'Completed': exec['completed_at'] or 'N/A',
                        'Duration (s)': exec['duration_seconds'] or 'N/A',
                        'Attempt': exec['attempt_number'],
                        'Retry': '✅' if exec['is_retry'] else '❌'
                    })

                df = pd.DataFrame(df_data)

                # Style the dataframe
                def color_status(val):
                    if val == 'completed':
                        return 'background-color: #d4edda'
                    elif val == 'failed':
                        return 'background-color: #f8d7da'
                    elif val == 'running':
                        return 'background-color: #fff3cd'
                    return ''

                styled_df = df.style.applymap(color_status, subset=['Status'])
                st.dataframe(styled_df, use_container_width=True)

                # Detailed view
                st.markdown("---")
                st.subheader("📋 Detailed Execution Information")

                for exec in executions:
                    status_emoji = {
                        'completed': '✅',
                        'failed': '❌',
                        'running': '🔄',
                        'pending': '⏳'
                    }.get(exec['status'], '❓')

                    with st.expander(f"{status_emoji} Execution #{exec['id']} - {exec['status'].upper()}"):
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.write(f"**Task ID:** {exec['task_id'] or 'N/A'}")
                            st.write(f"**Status:** {exec['status']}")
                            st.write(f"**Attempt:** {exec['attempt_number']}")
                            st.write(f"**Is Retry:** {'Yes' if exec['is_retry'] else 'No'}")

                        with col2:
                            st.write(f"**Scheduled:** {exec['scheduled_at']}")
                            st.write(f"**Started:** {exec['started_at'] or 'Not started'}")
                            st.write(f"**Completed:** {exec['completed_at'] or 'Not completed'}")
                            if exec['duration_seconds']:
                                st.write(f"**Duration:** {exec['duration_seconds']}s")

                        with col3:
                            if exec['worker_name']:
                                st.write(f"**Worker:** {exec['worker_name']}")

                        # Show result or error
                        if exec['result']:
                            st.write("**Result:**")
                            st.json(exec['result'])

                        if exec['error_message']:
                            st.error(f"**Error:** {exec['error_message']}")

            else:
                st.info("No executions found matching the filters.")

    except Exception as e:
        st.error(f"Error loading execution history: {e}")
