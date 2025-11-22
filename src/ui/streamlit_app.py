"""
Main Streamlit application for NEXUS Platform
"""
import streamlit as st
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from streamlit_option_menu import option_menu

# Page configuration
st.set_page_config(
    page_title="NEXUS Platform - RPA Module",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #ff7f0e;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Initialize session state
if "current_user" not in st.session_state:
    st.session_state.current_user = "admin"  # Default user

# Sidebar
with st.sidebar:
    st.markdown("# 🤖 NEXUS Platform")
    st.markdown("### RPA Module")

    selected = option_menu(
        menu_title="Navigation",
        options=[
            "Dashboard",
            "Bot Builder",
            "Automations",
            "Bots",
            "Schedules",
            "Executions",
            "Audit Logs",
        ],
        icons=[
            "speedometer2",
            "tools",
            "robot",
            "cpu",
            "calendar-event",
            "play-circle",
            "journal-text",
        ],
        menu_icon="cast",
        default_index=0,
    )

    st.markdown("---")
    st.markdown(f"**User:** {st.session_state.current_user}")
    st.markdown("**Environment:** Development")

# Main content area
if selected == "Dashboard":
    from src.ui.pages import dashboard

    dashboard.show()

elif selected == "Bot Builder":
    from src.ui.pages import bot_builder

    bot_builder.show()

elif selected == "Automations":
    from src.ui.pages import automations

    automations.show()

elif selected == "Bots":
    from src.ui.pages import bots

    bots.show()

elif selected == "Schedules":
    from src.ui.pages import schedules

    schedules.show()

elif selected == "Executions":
    from src.ui.pages import executions

    executions.show()

elif selected == "Audit Logs":
    from src.ui.pages import audit_logs

    audit_logs.show()
