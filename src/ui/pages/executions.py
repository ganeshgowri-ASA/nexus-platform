"""
Executions monitoring page
"""
import streamlit as st
import requests
from datetime import datetime

API_URL = "http://localhost:8000"


def show():
    """Display executions page"""
    st.markdown('<p class="main-header">▶️ Executions</p>', unsafe_allow_html=True)

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.selectbox(
            "Status", ["All", "pending", "running", "success", "failed", "cancelled"]
        )

    with col2:
        limit = st.number_input("Limit", min_value=10, max_value=500, value=50)

    with col3:
        st.write("")
        st.write("")
        if st.button("🔄 Refresh"):
            st.rerun()

    # Fetch executions
    try:
        params = {"limit": limit}
        if status_filter != "All":
            params["status"] = status_filter

        response = requests.get(f"{API_URL}/api/v1/rpa/executions", params=params)

        if response.status_code == 200:
            executions = response.json()

            st.markdown(f"**Total Executions:** {len(executions)}")
            st.markdown("---")

            if executions:
                for execution in executions:
                    status = execution["status"]
                    status_emoji = {
                        "success": "✅",
                        "failed": "❌",
                        "running": "🔄",
                        "pending": "⏳",
                        "cancelled": "⛔",
                    }.get(status, "❓")

                    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

                    with col1:
                        st.markdown(f"**ID:** {execution['id'][:12]}...")
                        created_at = datetime.fromisoformat(
                            execution["created_at"].replace("Z", "+00:00")
                        )
                        st.caption(f"Created: {created_at.strftime('%Y-%m-%d %H:%M:%S')}")

                    with col2:
                        st.text(f"Status: {status_emoji} {status}")
                        st.text(f"Trigger: {execution['trigger_type']}")

                    with col3:
                        duration = execution.get("duration")
                        if duration:
                            st.text(f"Duration: {duration}s")
                        if execution.get("error_message"):
                            st.error("Error occurred")

                    with col4:
                        if st.button("📋 Details", key=f"details_{execution['id']}"):
                            with st.expander("Execution Details", expanded=True):
                                st.json(execution)

                        if status in ["pending", "running"]:
                            if st.button("⛔ Cancel", key=f"cancel_{execution['id']}"):
                                try:
                                    cancel_response = requests.post(
                                        f"{API_URL}/api/v1/rpa/executions/{execution['id']}/cancel"
                                    )
                                    if cancel_response.status_code == 200:
                                        st.success("Execution cancelled")
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")

                    st.markdown("---")
            else:
                st.info("No executions found")

        else:
            st.error("Failed to fetch executions")

    except Exception as e:
        st.error(f"Error: {str(e)}")
