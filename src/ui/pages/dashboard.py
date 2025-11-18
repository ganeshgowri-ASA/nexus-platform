"""
Dashboard page for RPA module
"""
import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

API_URL = "http://localhost:8000"


def show():
    """Display the dashboard page"""
    st.markdown('<p class="main-header">🤖 RPA Dashboard</p>', unsafe_allow_html=True)

    # Fetch statistics
    try:
        # Execution statistics
        exec_stats_response = requests.get(f"{API_URL}/api/v1/rpa/statistics/executions")
        exec_stats = (
            exec_stats_response.json() if exec_stats_response.status_code == 200 else {}
        )

        # Metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Total Executions",
                value=exec_stats.get("total", 0),
                delta=None,
            )

        with col2:
            success_rate = exec_stats.get("success_rate", 0)
            st.metric(
                label="Success Rate",
                value=f"{success_rate:.1f}%",
                delta=None,
            )

        with col3:
            st.metric(
                label="Running",
                value=exec_stats.get("running", 0),
                delta=None,
            )

        with col4:
            st.metric(
                label="Failed",
                value=exec_stats.get("failed", 0),
                delta=None,
            )

        # Charts
        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Execution Status Distribution")

            # Pie chart for execution status
            statuses = ["success", "failed", "running", "pending"]
            values = [
                exec_stats.get("success", 0),
                exec_stats.get("failed", 0),
                exec_stats.get("running", 0),
                exec_stats.get("pending", 0),
            ]

            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=statuses,
                        values=values,
                        hole=0.3,
                        marker=dict(
                            colors=["#28a745", "#dc3545", "#ffc107", "#6c757d"]
                        ),
                    )
                ]
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("### Recent Activity")

            # Fetch recent executions
            try:
                executions_response = requests.get(
                    f"{API_URL}/api/v1/rpa/executions?limit=5"
                )
                if executions_response.status_code == 200:
                    executions = executions_response.json()

                    if executions:
                        for execution in executions:
                            status = execution["status"]
                            created_at = datetime.fromisoformat(
                                execution["created_at"].replace("Z", "+00:00")
                            )

                            status_emoji = {
                                "success": "✅",
                                "failed": "❌",
                                "running": "🔄",
                                "pending": "⏳",
                            }.get(status, "❓")

                            st.markdown(
                                f"""
                            <div class="metric-card">
                                {status_emoji} <strong>{execution['automation_id'][:8]}</strong><br>
                                Status: {status.upper()}<br>
                                Time: {created_at.strftime('%Y-%m-%d %H:%M:%S')}
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )
                            st.markdown("<br>", unsafe_allow_html=True)
                    else:
                        st.info("No recent executions")
            except Exception as e:
                st.error(f"Failed to fetch executions: {str(e)}")

        # Automations list
        st.markdown("---")
        st.markdown("### Active Automations")

        try:
            automations_response = requests.get(
                f"{API_URL}/api/v1/rpa/automations?status=active&limit=10"
            )
            if automations_response.status_code == 200:
                automations = automations_response.json()

                if automations:
                    for automation in automations:
                        col1, col2, col3 = st.columns([3, 2, 1])

                        with col1:
                            st.markdown(f"**{automation['name']}**")
                            st.caption(automation.get("description", "No description"))

                        with col2:
                            st.text(f"Status: {automation['status']}")
                            if automation.get("last_executed_at"):
                                last_exec = datetime.fromisoformat(
                                    automation["last_executed_at"].replace("Z", "+00:00")
                                )
                                st.caption(f"Last run: {last_exec.strftime('%Y-%m-%d %H:%M')}")

                        with col3:
                            if st.button("▶️ Run", key=f"run_{automation['id']}"):
                                st.info("Execution feature requires additional setup")

                        st.markdown("---")
                else:
                    st.info("No active automations found")
        except Exception as e:
            st.error(f"Failed to fetch automations: {str(e)}")

    except Exception as e:
        st.error(f"Failed to load dashboard: {str(e)}")
        st.info("Make sure the API server is running at http://localhost:8000")
