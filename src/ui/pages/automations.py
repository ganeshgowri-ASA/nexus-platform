"""
Automations management page
"""
import streamlit as st
import requests
from datetime import datetime

API_URL = "http://localhost:8000"


def show():
    """Display automations page"""
    st.markdown('<p class="main-header">🤖 Automations</p>', unsafe_allow_html=True)

    # Filters
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        status_filter = st.selectbox(
            "Filter by Status", ["All", "active", "paused", "draft", "archived"]
        )

    with col2:
        search = st.text_input("Search", placeholder="Search automations...")

    with col3:
        st.write("")
        st.write("")
        if st.button("🔄 Refresh"):
            st.rerun()

    # Fetch automations
    try:
        params = {}
        if status_filter != "All":
            params["status"] = status_filter

        response = requests.get(f"{API_URL}/api/v1/rpa/automations", params=params)

        if response.status_code == 200:
            automations = response.json()

            # Filter by search
            if search:
                automations = [
                    a
                    for a in automations
                    if search.lower() in a["name"].lower()
                    or search.lower() in a.get("description", "").lower()
                ]

            st.markdown(f"**Total Automations:** {len(automations)}")
            st.markdown("---")

            if automations:
                for automation in automations:
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

                        with col1:
                            st.markdown(f"### {automation['name']}")
                            st.caption(automation.get("description", "No description"))

                        with col2:
                            status = automation["status"]
                            status_color = {
                                "active": "🟢",
                                "paused": "🟡",
                                "draft": "⚪",
                                "archived": "⚫",
                            }.get(status, "❓")
                            st.markdown(f"**Status:** {status_color} {status}")

                        with col3:
                            st.text(f"Trigger: {automation['trigger_type']}")
                            if automation.get("last_executed_at"):
                                last_exec = datetime.fromisoformat(
                                    automation["last_executed_at"].replace("Z", "+00:00")
                                )
                                st.caption(f"Last run: {last_exec.strftime('%Y-%m-%d %H:%M')}")

                        with col4:
                            if st.button("▶️ Run", key=f"run_{automation['id']}"):
                                st.info("Run feature: See Bot Builder page")

                            if st.button("✏️ Edit", key=f"edit_{automation['id']}"):
                                st.session_state.current_automation = automation
                                st.info("Set as current automation for editing")

                        st.markdown("---")
            else:
                st.info("No automations found")

        else:
            st.error(f"Failed to fetch automations: {response.status_code}")

    except Exception as e:
        st.error(f"Error: {str(e)}")
