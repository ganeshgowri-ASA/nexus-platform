"""Jobs list page"""
import streamlit as st
import httpx
import pandas as pd

API_BASE_URL = "http://localhost:8000/api/v1"


def show():
    """Display jobs list"""
    st.markdown('<div class="main-header">📋 Scheduled Jobs</div>', unsafe_allow_html=True)

    # Filters
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        filter_active = st.selectbox("Status", ["All", "Active", "Inactive"])

    with col2:
        filter_type = st.selectbox("Type", ["All", "cron", "interval", "date", "calendar"])

    with col3:
        search_query = st.text_input("Search", placeholder="Search by name...")

    with col4:
        st.write("")
        st.write("")
        if st.button("🔄 Refresh"):
            st.rerun()

    # Fetch jobs
    try:
        params = {}
        if filter_active != "All":
            params['is_active'] = filter_active == "Active"
        if filter_type != "All":
            params['job_type'] = filter_type

        response = httpx.get(f"{API_BASE_URL}/jobs/", params=params, timeout=10)

        if response.status_code == 200:
            jobs = response.json()

            # Filter by search query
            if search_query:
                jobs = [j for j in jobs if search_query.lower() in j['name'].lower()]

            if jobs:
                st.write(f"**Total Jobs:** {len(jobs)}")
                st.markdown("---")

                # Display jobs
                for job in jobs:
                    with st.expander(f"**{job['name']}** - {job['job_type'].upper()} {'✅' if job['is_active'] else '❌'}"):
                        col1, col2, col3 = st.columns([2, 2, 1])

                        with col1:
                            st.write(f"**ID:** {job['id']}")
                            st.write(f"**Type:** {job['job_type']}")
                            st.write(f"**Status:** {job['status']}")
                            st.write(f"**Active:** {'Yes' if job['is_active'] else 'No'}")

                            if job['description']:
                                st.write(f"**Description:** {job['description']}")

                        with col2:
                            st.write(f"**Task:** {job['task_name']}")
                            st.write(f"**Timezone:** {job['timezone']}")
                            st.write(f"**Priority:** {job['priority']}")
                            st.write(f"**Max Retries:** {job['max_retries']}")

                            if job['cron_expression']:
                                st.write(f"**Cron:** `{job['cron_expression']}`")
                            if job['interval_seconds']:
                                st.write(f"**Interval:** {job['interval_seconds']}s")

                        with col3:
                            # Action buttons
                            if job['is_active']:
                                if st.button(f"⏸️ Pause", key=f"pause_{job['id']}"):
                                    try:
                                        response = httpx.post(
                                            f"{API_BASE_URL}/jobs/{job['id']}/pause",
                                            timeout=10
                                        )
                                        if response.status_code == 200:
                                            st.success("Job paused")
                                            st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                            else:
                                if st.button(f"▶️ Resume", key=f"resume_{job['id']}"):
                                    try:
                                        response = httpx.post(
                                            f"{API_BASE_URL}/jobs/{job['id']}/resume",
                                            timeout=10
                                        )
                                        if response.status_code == 200:
                                            st.success("Job resumed")
                                            st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")

                            if st.button(f"▶️ Execute Now", key=f"exec_{job['id']}"):
                                try:
                                    response = httpx.post(
                                        f"{API_BASE_URL}/jobs/{job['id']}/execute",
                                        timeout=10
                                    )
                                    if response.status_code == 200:
                                        result = response.json()
                                        st.success(f"Execution started: {result['task_id']}")
                                except Exception as e:
                                    st.error(f"Error: {e}")

                            if st.button(f"🗑️ Delete", key=f"del_{job['id']}"):
                                try:
                                    response = httpx.delete(
                                        f"{API_BASE_URL}/jobs/{job['id']}",
                                        timeout=10
                                    )
                                    if response.status_code == 204:
                                        st.success("Job deleted")
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")

                        # Show schedule info
                        st.write("**Schedule Information:**")
                        schedule_col1, schedule_col2 = st.columns(2)

                        with schedule_col1:
                            if job['next_run_at']:
                                st.write(f"⏭️ **Next Run:** {job['next_run_at']}")
                            else:
                                st.write("⏭️ **Next Run:** Not scheduled")

                        with schedule_col2:
                            if job['last_run_at']:
                                st.write(f"⏮️ **Last Run:** {job['last_run_at']}")
                            else:
                                st.write("⏮️ **Last Run:** Never")

                        # Show tags
                        if job['tags']:
                            st.write(f"**Tags:** {', '.join(job['tags'])}")

            else:
                st.info("No jobs found matching the filters.")

        else:
            st.error(f"Failed to fetch jobs: {response.text}")

    except Exception as e:
        st.error(f"Error loading jobs: {e}")
        st.info("Make sure the API server is running at http://localhost:8000")
