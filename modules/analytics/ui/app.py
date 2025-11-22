"""
Streamlit Analytics Dashboard

Main Streamlit application for analytics visualization.
"""

import streamlit as st
from datetime import datetime, timedelta

from modules.analytics.storage.database import DatabaseConfig, init_database
from shared.utils import get_utc_now

# Page config
st.set_page_config(
    page_title="NEXUS Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main > div {padding-top: 2rem;}
    .stMetric {background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem;}
</style>
""", unsafe_allow_html=True)


def init_app():
    """Initialize application."""
    if 'db' not in st.session_state:
        db_config = DatabaseConfig("postgresql://localhost/nexus_analytics")
        st.session_state.db = init_database(db_config)


def main():
    """Main application entry point."""
    init_app()

    # Sidebar
    st.sidebar.title("📊 NEXUS Analytics")
    st.sidebar.markdown("---")

    # Navigation
    page = st.sidebar.radio(
        "Navigation",
        ["Overview", "Events", "Users", "Funnels", "Cohorts", "A/B Tests", "Reports"]
    )

    # Date range selector
    st.sidebar.markdown("### Date Range")
    date_range = st.sidebar.selectbox(
        "Select Period",
        ["Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom"]
    )

    if date_range == "Custom":
        start_date = st.sidebar.date_input("Start Date")
        end_date = st.sidebar.date_input("End Date")
    else:
        days = {"Last 7 Days": 7, "Last 30 Days": 30, "Last 90 Days": 90}[date_range]
        end_date = get_utc_now().date()
        start_date = (get_utc_now() - timedelta(days=days)).date()

    st.sidebar.markdown("---")

    # Route to pages
    if page == "Overview":
        show_overview(start_date, end_date)
    elif page == "Events":
        show_events(start_date, end_date)
    elif page == "Users":
        show_users(start_date, end_date)
    elif page == "Funnels":
        show_funnels(start_date, end_date)
    elif page == "Cohorts":
        show_cohorts(start_date, end_date)
    elif page == "A/B Tests":
        show_ab_tests(start_date, end_date)
    elif page == "Reports":
        show_reports(start_date, end_date)


def show_overview(start_date, end_date):
    """Show overview dashboard."""
    st.title("Analytics Overview")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Events", "125,430", "+12.3%")
    with col2:
        st.metric("Active Users", "8,234", "+5.7%")
    with col3:
        st.metric("Avg Session Duration", "5m 23s", "-2.1%")
    with col4:
        st.metric("Conversion Rate", "3.2%", "+0.4%")

    st.markdown("---")

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Events Over Time")
        st.line_chart({"Events": [100, 120, 140, 130, 150, 160, 155]})

    with col2:
        st.subheader("Top Events")
        st.bar_chart({"Count": [450, 320, 280, 210, 190]})


def show_events(start_date, end_date):
    """Show events page."""
    st.title("Events")
    st.write(f"Showing events from {start_date} to {end_date}")
    # TODO: Implement events table


def show_users(start_date, end_date):
    """Show users page."""
    st.title("Users")
    st.write(f"Showing users from {start_date} to {end_date}")
    # TODO: Implement users analytics


def show_funnels(start_date, end_date):
    """Show funnels page."""
    st.title("Funnels")
    st.write(f"Analyzing funnels from {start_date} to {end_date}")
    # TODO: Implement funnel visualization


def show_cohorts(start_date, end_date):
    """Show cohorts page."""
    st.title("Cohorts")
    st.write(f"Cohort analysis from {start_date} to {end_date}")
    # TODO: Implement cohort analysis


def show_ab_tests(start_date, end_date):
    """Show A/B tests page."""
    st.title("A/B Tests")
    st.write(f"A/B test results from {start_date} to {end_date}")
    # TODO: Implement A/B test results


def show_reports(start_date, end_date):
    """Show reports page."""
    st.title("Reports")
    st.write("Generate and export custom reports")
    # TODO: Implement report generation


if __name__ == "__main__":
    main()
