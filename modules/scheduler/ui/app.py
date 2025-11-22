"""Main Streamlit application"""
import streamlit as st
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Page configuration
st.set_page_config(
    page_title="NEXUS Scheduler",
    page_icon="⏰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("⏰ NEXUS Scheduler")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    [
        "📊 Dashboard",
        "📋 Jobs",
        "➕ Create Job",
        "📅 Calendar View",
        "📜 Execution History",
        "🔔 Notifications",
        "⚙️ Settings"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info(f"**Current Time (UTC)**\n\n{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")

# Import page modules
if page == "📊 Dashboard":
    from pages import dashboard
    dashboard.show()

elif page == "📋 Jobs":
    from pages import jobs_list
    jobs_list.show()

elif page == "➕ Create Job":
    from pages import create_job
    create_job.show()

elif page == "📅 Calendar View":
    from pages import calendar_view
    calendar_view.show()

elif page == "📜 Execution History":
    from pages import execution_history
    execution_history.show()

elif page == "🔔 Notifications":
    from pages import notifications
    notifications.show()

elif page == "⚙️ Settings":
    from pages import settings_page
    settings_page.show()
