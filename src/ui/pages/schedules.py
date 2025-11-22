"""
Schedules management page
"""
import streamlit as st
import requests
from datetime import datetime

API_URL = "http://localhost:8000"


def show():
    """Display schedules page"""
    st.markdown('<p class="main-header">📅 Schedules</p>', unsafe_allow_html=True)

    # Create new schedule
    with st.expander("➕ Create New Schedule"):
        with st.form("create_schedule_form"):
            # Get automations for selection
            try:
                auto_response = requests.get(
                    f"{API_URL}/api/v1/rpa/automations?status=active"
                )
                if auto_response.status_code == 200:
                    automations = auto_response.json()
                    automation_options = {a["name"]: a["id"] for a in automations}

                    selected_automation = st.selectbox(
                        "Automation*", list(automation_options.keys())
                    )
                    automation_id = automation_options.get(selected_automation)
            except Exception:
                st.error("Could not load automations")
                automation_id = st.text_input("Automation ID*")

            name = st.text_input("Schedule Name*")
            cron_expression = st.text_input(
                "Cron Expression*",
                placeholder="0 9 * * *",
                help="e.g., 0 9 * * * for daily at 9 AM",
            )
            timezone = st.text_input("Timezone", value="UTC")

            submitted = st.form_submit_button("Create Schedule")

            if submitted and name and cron_expression and automation_id:
                schedule_data = {
                    "automation_id": automation_id,
                    "name": name,
                    "cron_expression": cron_expression,
                    "timezone": timezone,
                    "input_data": {},
                    "created_by": st.session_state.current_user,
                }

                try:
                    response = requests.post(
                        f"{API_URL}/api/v1/rpa/schedules", json=schedule_data
                    )
                    if response.status_code == 200:
                        st.success(f"Schedule '{name}' created!")
                        st.rerun()
                    else:
                        st.error(f"Error: {response.json()}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    # List schedules
    st.markdown("### Existing Schedules")

    try:
        response = requests.get(f"{API_URL}/api/v1/rpa/schedules")

        if response.status_code == 200:
            schedules = response.json()

            if schedules:
                for schedule in schedules:
                    col1, col2, col3 = st.columns([3, 2, 2])

                    with col1:
                        st.markdown(f"### {schedule['name']}")
                        st.caption(f"Cron: {schedule['cron_expression']}")

                    with col2:
                        active_emoji = "🟢" if schedule["is_active"] else "🔴"
                        st.text(f"Status: {active_emoji} {'Active' if schedule['is_active'] else 'Inactive'}")
                        if schedule.get("next_run_at"):
                            next_run = datetime.fromisoformat(
                                schedule["next_run_at"].replace("Z", "+00:00")
                            )
                            st.caption(f"Next run: {next_run.strftime('%Y-%m-%d %H:%M')}")

                    with col3:
                        if st.button("🗑️ Delete", key=f"delete_{schedule['id']}"):
                            try:
                                del_response = requests.delete(
                                    f"{API_URL}/api/v1/rpa/schedules/{schedule['id']}"
                                )
                                if del_response.status_code == 200:
                                    st.success("Schedule deleted")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")

                    st.markdown("---")
            else:
                st.info("No schedules found")
        else:
            st.error("Failed to fetch schedules")

    except Exception as e:
        st.error(f"Error: {str(e)}")
