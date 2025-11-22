"""Dashboard page"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import httpx
import pandas as pd

API_BASE_URL = "http://localhost:8000/api/v1"


def show():
    """Display dashboard"""
    st.markdown('<div class="main-header">📊 Scheduler Dashboard</div>', unsafe_allow_html=True)

    # Fetch stats
    try:
        response = httpx.get(f"{API_BASE_URL}/jobs/stats/overview", timeout=10)
        if response.status_code == 200:
            stats = response.json()
        else:
            stats = None
    except Exception as e:
        st.error(f"Failed to fetch statistics: {e}")
        stats = None

    if stats:
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Total Jobs",
                value=stats['total_jobs'],
                delta=None
            )

        with col2:
            st.metric(
                label="Active Jobs",
                value=stats['active_jobs'],
                delta=None
            )

        with col3:
            st.metric(
                label="Total Executions",
                value=stats['total_executions'],
                delta=None
            )

        with col4:
            success_rate = 0
            if stats['total_executions'] > 0:
                success_rate = (stats['successful_executions'] / stats['total_executions']) * 100
            st.metric(
                label="Success Rate",
                value=f"{success_rate:.1f}%",
                delta=None
            )

        st.markdown("---")

        # Charts
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📈 Execution Status Distribution")

            # Pie chart
            labels = ['Successful', 'Failed', 'Running']
            values = [
                stats['successful_executions'],
                stats['failed_executions'],
                stats['running_executions']
            ]

            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.3,
                marker=dict(colors=['#28a745', '#dc3545', '#ffc107'])
            )])

            fig.update_layout(
                showlegend=True,
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("📊 Job Status")

            # Bar chart
            job_labels = ['Active', 'Paused']
            job_values = [stats['active_jobs'], stats['paused_jobs']]

            fig = go.Figure(data=[go.Bar(
                x=job_labels,
                y=job_values,
                marker=dict(color=['#1f77b4', '#ff7f0e'])
            )])

            fig.update_layout(
                showlegend=False,
                height=400,
                yaxis_title="Count"
            )

            st.plotly_chart(fig, use_container_width=True)

        # Recent activity
        st.markdown("---")
        st.subheader("⚡ Recent Activity")

        st.info(f"""
        **Last 24 Hours**
        - Executions: {stats['last_24h_executions']}
        - Average Duration: {stats['average_duration']:.2f}s (if stats['average_duration'] else 'N/A')
        """)

        # Fetch recent jobs
        try:
            response = httpx.get(f"{API_BASE_URL}/jobs/?limit=5", timeout=10)
            if response.status_code == 200:
                jobs = response.json()

                if jobs:
                    st.subheader("📋 Recent Jobs")

                    for job in jobs:
                        with st.expander(f"**{job['name']}** - {job['job_type']}"):
                            col1, col2, col3 = st.columns(3)

                            with col1:
                                st.write(f"**Status:** {job['status']}")
                                st.write(f"**Active:** {'✅' if job['is_active'] else '❌'}")

                            with col2:
                                st.write(f"**Type:** {job['job_type']}")
                                if job['cron_expression']:
                                    st.write(f"**Cron:** `{job['cron_expression']}`")

                            with col3:
                                if job['next_run_at']:
                                    st.write(f"**Next Run:** {job['next_run_at']}")
                                if job['last_run_at']:
                                    st.write(f"**Last Run:** {job['last_run_at']}")

        except Exception as e:
            st.error(f"Failed to fetch recent jobs: {e}")

    else:
        st.warning("Unable to load dashboard statistics. Make sure the API server is running.")

    # Refresh button
    if st.button("🔄 Refresh Dashboard"):
        st.rerun()
