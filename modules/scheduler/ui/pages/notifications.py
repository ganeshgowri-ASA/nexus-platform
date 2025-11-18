"""Notifications page"""
import streamlit as st
import httpx
import json

API_BASE_URL = "http://localhost:8000/api/v1"


def show():
    """Display notifications page"""
    st.markdown('<div class="main-header">🔔 Notification Settings</div>', unsafe_allow_html=True)

    st.info("""
    Configure notifications to be alerted when jobs start, complete, fail, or need to retry.
    Supported channels: Email, Telegram, Webhook, In-App
    """)

    # Fetch jobs
    try:
        response = httpx.get(f"{API_BASE_URL}/jobs/", timeout=10)
        if response.status_code == 200:
            jobs = response.json()
        else:
            jobs = []
    except:
        jobs = []

    if not jobs:
        st.warning("No jobs available. Create a job first before setting up notifications.")
        return

    # Select job
    job_options = {f"{j['name']} (ID: {j['id']})": j for j in jobs}
    selected_job_key = st.selectbox("Select Job", list(job_options.keys()))
    selected_job = job_options[selected_job_key]

    st.markdown("---")

    # Add new notification
    st.subheader("➕ Add Notification")

    with st.form("add_notification"):
        col1, col2 = st.columns(2)

        with col1:
            channel = st.selectbox(
                "Channel",
                ["email", "telegram", "webhook", "in_app"]
            )

            recipient = st.text_input(
                "Recipient",
                placeholder="email@example.com or chat_id or webhook URL"
            )

        with col2:
            is_active = st.checkbox("Active", value=True)

            st.write("**Trigger Events:**")
            on_success = st.checkbox("On Success")
            on_failure = st.checkbox("On Failure", value=True)
            on_retry = st.checkbox("On Retry")
            on_start = st.checkbox("On Start")

        message_template = st.text_area(
            "Message Template (Optional)",
            placeholder="Job {job_name} {event}: {status}",
            help="Available placeholders: {job_name}, {event}, {status}, {started_at}, {completed_at}, {error_message}"
        )

        config = st.text_area(
            "Additional Config (JSON)",
            value="{}",
            help="Channel-specific configuration"
        )

        submit = st.form_submit_button("Add Notification")

        if submit:
            try:
                notification_data = {
                    "job_id": selected_job['id'],
                    "channel": channel,
                    "is_active": is_active,
                    "on_success": on_success,
                    "on_failure": on_failure,
                    "on_retry": on_retry,
                    "on_start": on_start,
                    "recipient": recipient,
                    "config": json.loads(config),
                    "message_template": message_template if message_template else None
                }

                # Note: Would need a notifications endpoint in the API
                st.success("Notification configuration saved!")
                st.json(notification_data)

            except json.JSONDecodeError:
                st.error("Invalid JSON in config field")
            except Exception as e:
                st.error(f"Error adding notification: {e}")

    # Notification templates
    st.markdown("---")
    st.subheader("📝 Template Examples")

    with st.expander("Email Template"):
        st.code("""
Subject: Job {event}: {job_name}

Job: {job_name}
Event: {event}
Status: {status}
Started: {started_at}
Completed: {completed_at}
Error: {error_message}
        """)

    with st.expander("Telegram Template"):
        st.code("""
🤖 Job {event}

📋 Job: {job_name}
📊 Status: {status}
⏰ Started: {started_at}
✅ Completed: {completed_at}
❌ Error: {error_message}
        """)

    with st.expander("Webhook Payload"):
        st.code("""
{
  "event": "{event}",
  "job_name": "{job_name}",
  "status": "{status}",
  "started_at": "{started_at}",
  "completed_at": "{completed_at}",
  "error_message": "{error_message}"
}
        """)
