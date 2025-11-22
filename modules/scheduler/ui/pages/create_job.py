"""Create job page with visual cron builder"""
import streamlit as st
import httpx
from datetime import datetime, timedelta
import json

API_BASE_URL = "http://localhost:8000/api/v1"


def show():
    """Display create job page"""
    st.markdown('<div class="main-header">➕ Create New Job</div>', unsafe_allow_html=True)

    # Job basic information
    st.subheader("📋 Basic Information")

    col1, col2 = st.columns(2)

    with col1:
        job_name = st.text_input("Job Name*", placeholder="e.g., Daily Report Generation")
        task_name = st.text_input("Task Name*", placeholder="e.g., tasks.generate_report")

    with col2:
        job_type = st.selectbox(
            "Schedule Type*",
            ["cron", "interval", "date", "calendar"]
        )
        timezone = st.selectbox(
            "Timezone",
            ["UTC", "US/Eastern", "US/Pacific", "Europe/London", "Asia/Tokyo", "Asia/Shanghai"],
            index=0
        )

    description = st.text_area("Description", placeholder="Describe what this job does...")

    st.markdown("---")

    # Schedule configuration
    st.subheader("⏰ Schedule Configuration")

    cron_expression = None
    interval_seconds = None
    scheduled_time = None

    if job_type == "cron":
        st.write("**Visual Cron Builder**")

        # Fetch presets
        try:
            response = httpx.get(f"{API_BASE_URL}/cron/presets", timeout=10)
            if response.status_code == 200:
                presets = response.json()
                preset_options = {v['description']: k for k, v in presets.items()}

                selected_preset = st.selectbox(
                    "Choose a preset or build custom",
                    ["Custom"] + list(preset_options.keys())
                )

                if selected_preset != "Custom":
                    preset_key = preset_options[selected_preset]
                    cron_expression = presets[preset_key]['expression']
                    st.code(cron_expression)
                else:
                    # Custom cron builder
                    col1, col2, col3, col4, col5 = st.columns(5)

                    with col1:
                        minute = st.text_input("Minute", value="*", help="0-59 or *")
                    with col2:
                        hour = st.text_input("Hour", value="*", help="0-23 or *")
                    with col3:
                        day = st.text_input("Day", value="*", help="1-31 or *")
                    with col4:
                        month = st.text_input("Month", value="*", help="1-12 or *")
                    with col5:
                        dow = st.text_input("Day of Week", value="*", help="0-6 or *")

                    cron_expression = f"{minute} {hour} {day} {month} {dow}"

                # Validate cron expression
                if cron_expression:
                    try:
                        response = httpx.post(
                            f"{API_BASE_URL}/cron/validate",
                            json={
                                "expression": cron_expression,
                                "timezone": timezone
                            },
                            timeout=10
                        )

                        if response.status_code == 200:
                            result = response.json()

                            if result['is_valid']:
                                st.success(f"✅ Valid cron expression: {result['description']}")

                                if result['next_runs']:
                                    st.write("**Next 5 runs:**")
                                    for run_time in result['next_runs']:
                                        st.write(f"- {run_time}")
                            else:
                                st.error(f"❌ Invalid cron expression: {result['error']}")

                    except Exception as e:
                        st.warning(f"Could not validate cron expression: {e}")

        except Exception as e:
            st.error(f"Failed to load presets: {e}")
            cron_expression = st.text_input("Cron Expression*", placeholder="*/5 * * * *")

    elif job_type == "interval":
        st.write("**Interval Configuration**")

        col1, col2 = st.columns(2)

        with col1:
            interval_value = st.number_input("Interval Value", min_value=1, value=5)

        with col2:
            interval_unit = st.selectbox("Interval Unit", ["seconds", "minutes", "hours", "days"])

        # Convert to seconds
        multipliers = {"seconds": 1, "minutes": 60, "hours": 3600, "days": 86400}
        interval_seconds = interval_value * multipliers[interval_unit]

        st.info(f"Job will run every {interval_value} {interval_unit} ({interval_seconds} seconds)")

    elif job_type == "date":
        st.write("**One-Time Schedule**")

        col1, col2 = st.columns(2)

        with col1:
            date = st.date_input("Date", value=datetime.now().date() + timedelta(days=1))

        with col2:
            time = st.time_input("Time", value=datetime.now().time())

        scheduled_time = datetime.combine(date, time).isoformat()

        st.info(f"Job will run once at {scheduled_time}")

    elif job_type == "calendar":
        st.write("**Calendar-Based Schedule**")
        st.warning("Calendar-based scheduling is a custom feature. Define your calendar rules below.")

        calendar_rule = st.text_area(
            "Calendar Rule (JSON)",
            value='{"weekdays": [1, 2, 3, 4, 5], "time": "09:00"}',
            help="Define calendar rules in JSON format"
        )

    st.markdown("---")

    # Task configuration
    st.subheader("⚙️ Task Configuration")

    col1, col2 = st.columns(2)

    with col1:
        priority = st.slider("Priority (1-10)", min_value=1, max_value=10, value=5)
        max_retries = st.number_input("Max Retries", min_value=0, max_value=10, value=3)

    with col2:
        retry_delay = st.number_input("Retry Delay (seconds)", min_value=0, value=60)
        retry_backoff = st.checkbox("Enable Retry Backoff", value=True)

    # Task arguments
    st.write("**Task Arguments**")

    col1, col2 = st.columns(2)

    with col1:
        task_args = st.text_area(
            "Positional Arguments (JSON array)",
            value='[]',
            help="e.g., [1, 2, \"hello\"]"
        )

    with col2:
        task_kwargs = st.text_area(
            "Keyword Arguments (JSON object)",
            value='{}',
            help='e.g., {"name": "John", "age": 30}'
        )

    # Tags and metadata
    st.write("**Tags and Metadata**")

    col1, col2 = st.columns(2)

    with col1:
        tags = st.text_input("Tags (comma-separated)", placeholder="report, daily, analytics")

    with col2:
        is_active = st.checkbox("Active", value=True)

    # Submit button
    st.markdown("---")

    if st.button("✅ Create Job", type="primary"):
        # Validate required fields
        if not job_name or not task_name:
            st.error("Please fill in all required fields (marked with *)")
            return

        # Prepare job data
        try:
            job_data = {
                "name": job_name,
                "description": description,
                "job_type": job_type,
                "task_name": task_name,
                "timezone": timezone,
                "is_active": is_active,
                "priority": priority,
                "max_retries": max_retries,
                "retry_delay": retry_delay,
                "retry_backoff": retry_backoff,
                "task_args": json.loads(task_args),
                "task_kwargs": json.loads(task_kwargs),
                "tags": [t.strip() for t in tags.split(",")] if tags else []
            }

            # Add schedule-specific fields
            if job_type == "cron":
                job_data["cron_expression"] = cron_expression
            elif job_type == "interval":
                job_data["interval_seconds"] = interval_seconds
            elif job_type == "date":
                job_data["scheduled_time"] = scheduled_time
            elif job_type == "calendar":
                job_data["calendar_rule"] = json.loads(calendar_rule)

            # Create job
            response = httpx.post(
                f"{API_BASE_URL}/jobs/",
                json=job_data,
                timeout=10
            )

            if response.status_code == 201:
                st.success(f"✅ Job '{job_name}' created successfully!")
                st.balloons()

                # Show created job details
                job = response.json()
                with st.expander("View Job Details"):
                    st.json(job)

            else:
                st.error(f"Failed to create job: {response.text}")

        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON in task arguments: {e}")
        except Exception as e:
            st.error(f"Error creating job: {e}")
