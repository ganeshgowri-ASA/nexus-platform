"""Settings page"""
import streamlit as st
from modules.scheduler.utils.timezone_utils import get_common_timezones

def show():
    """Display settings page"""
    st.markdown('<div class="main-header">⚙️ Settings</div>', unsafe_allow_html=True)

    # General Settings
    st.subheader("🌐 General Settings")

    col1, col2 = st.columns(2)

    with col1:
        default_timezone = st.selectbox(
            "Default Timezone",
            ["UTC", "US/Eastern", "US/Pacific", "Europe/London", "Asia/Tokyo"],
            index=0
        )

        max_retry_attempts = st.number_input(
            "Default Max Retry Attempts",
            min_value=0,
            max_value=10,
            value=3
        )

    with col2:
        task_timeout = st.number_input(
            "Task Timeout (seconds)",
            min_value=60,
            max_value=7200,
            value=3600
        )

        enable_scheduler = st.checkbox("Enable Scheduler", value=True)

    # Database Settings
    st.markdown("---")
    st.subheader("🗄️ Database Settings")

    db_url = st.text_input(
        "PostgreSQL Database URL",
        value="postgresql://nexus:nexus@localhost:5432/nexus_scheduler",
        type="password"
    )

    # Redis Settings
    st.markdown("---")
    st.subheader("📦 Redis Settings")

    col1, col2 = st.columns(2)

    with col1:
        redis_host = st.text_input("Redis Host", value="localhost")
        redis_db = st.number_input("Redis DB", min_value=0, max_value=15, value=0)

    with col2:
        redis_port = st.number_input("Redis Port", min_value=1, max_value=65535, value=6379)

    # Notification Settings
    st.markdown("---")
    st.subheader("📧 Notification Settings")

    with st.expander("Email (SMTP)"):
        smtp_host = st.text_input("SMTP Host", value="smtp.gmail.com")
        smtp_port = st.number_input("SMTP Port", value=587)
        smtp_user = st.text_input("SMTP Username")
        smtp_password = st.text_input("SMTP Password", type="password")

    with st.expander("Telegram"):
        telegram_token = st.text_input("Bot Token", type="password")
        st.info("Create a bot via @BotFather on Telegram to get a token")

    # System Information
    st.markdown("---")
    st.subheader("ℹ️ System Information")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("API Version", "v1.0.0")

    with col2:
        st.metric("Scheduler Status", "Running" if enable_scheduler else "Stopped")

    with col3:
        st.metric("Database", "PostgreSQL")

    # Timezone Reference
    st.markdown("---")
    st.subheader("🌍 Available Timezones")

    with st.expander("View All Timezones"):
        timezones = get_common_timezones()

        for region, tz_list in timezones.items():
            st.write(f"**{region}:**")
            st.write(", ".join(tz_list))
            st.write("")

    # Save button
    st.markdown("---")

    if st.button("💾 Save Settings", type="primary"):
        st.success("Settings saved successfully!")
        st.info("Note: Some settings require application restart to take effect.")

    # Danger Zone
    st.markdown("---")
    st.subheader("⚠️ Danger Zone")

    with st.expander("⚠️ Advanced Operations"):
        st.warning("These operations are irreversible!")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🗑️ Clear All Execution History"):
                st.error("This feature requires confirmation")

        with col2:
            if st.button("🔄 Reset All Job Schedules"):
                st.error("This feature requires confirmation")
