"""Calendar view page"""
import streamlit as st
import httpx
from datetime import datetime, timedelta
import pandas as pd
from streamlit_calendar import calendar as st_calendar

API_BASE_URL = "http://localhost:8000/api/v1"


def show():
    """Display calendar view"""
    st.markdown('<div class="main-header">📅 Calendar View</div>', unsafe_allow_html=True)

    # Fetch all active jobs
    try:
        response = httpx.get(f"{API_BASE_URL}/jobs/?is_active=true", timeout=10)

        if response.status_code == 200:
            jobs = response.json()

            # Prepare calendar events
            events = []

            for job in jobs:
                if job['next_run_at']:
                    events.append({
                        'title': job['name'],
                        'start': job['next_run_at'],
                        'color': '#1f77b4' if job['job_type'] == 'cron' else '#ff7f0e',
                        'resourceId': str(job['id'])
                    })

            # Calendar options
            calendar_options = {
                "editable": False,
                "selectable": True,
                "headerToolbar": {
                    "left": "today prev,next",
                    "center": "title",
                    "right": "dayGridMonth,timeGridWeek,timeGridDay"
                },
                "initialView": "timeGridWeek",
                "slotMinTime": "00:00:00",
                "slotMaxTime": "24:00:00",
            }

            # Display calendar
            if events:
                st.write(f"**Showing {len(events)} upcoming job executions**")

                try:
                    calendar_result = st_calendar(
                        events=events,
                        options=calendar_options
                    )

                    if calendar_result and calendar_result.get('eventClick'):
                        event = calendar_result['eventClick']['event']
                        st.info(f"Selected: {event['title']}")

                except Exception as e:
                    st.warning("Calendar component not available. Showing list view instead.")

                    # Fallback to list view
                    st.markdown("---")
                    st.subheader("Upcoming Executions")

                    df = pd.DataFrame([
                        {
                            'Job': e['title'],
                            'Scheduled Time': e['start'],
                            'Type': '🔄 Cron' if e['color'] == '#1f77b4' else '⏱️ Other'
                        }
                        for e in sorted(events, key=lambda x: x['start'])
                    ])

                    st.dataframe(df, use_container_width=True)

            else:
                st.info("No upcoming job executions scheduled.")

            # Show jobs grouped by day
            st.markdown("---")
            st.subheader("📊 Jobs by Schedule")

            # Group jobs by type
            job_types = {}
            for job in jobs:
                job_type = job['job_type']
                if job_type not in job_types:
                    job_types[job_type] = []
                job_types[job_type].append(job)

            for job_type, type_jobs in job_types.items():
                with st.expander(f"{job_type.upper()} Jobs ({len(type_jobs)})"):
                    for job in type_jobs:
                        st.write(f"**{job['name']}**")
                        if job['next_run_at']:
                            st.write(f"Next run: {job['next_run_at']}")
                        st.write("---")

        else:
            st.error("Failed to fetch jobs")

    except Exception as e:
        st.error(f"Error loading calendar: {e}")
        st.info("Make sure the API server is running at http://localhost:8000")
