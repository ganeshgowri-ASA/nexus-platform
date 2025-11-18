"""
NEXUS Platform - Main Streamlit Application.

This is the entry point for the NEXUS Platform frontend.
"""

import streamlit as st
from frontend.config import config
from frontend.utils import APIClient, is_authenticated, login_user, logout_user


# Configure page
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout=config.LAYOUT,
    initial_sidebar_state="expanded"
)


def show_login():
    """Display login/register page."""
    st.title(f"{config.APP_ICON} Welcome to NEXUS Platform")
    st.markdown("### AI-Powered Productivity & Campaign Management")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.subheader("Login to your account")

        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)

            if submit:
                if not username or not password:
                    st.error("Please enter username and password")
                else:
                    try:
                        with st.spinner("Logging in..."):
                            response = APIClient.login(username, password)
                            user_data = APIClient.get_current_user()

                        login_user(
                            response["access_token"],
                            response["refresh_token"],
                            user_data
                        )
                        st.success("Login successful!")
                        st.rerun()

                    except Exception as e:
                        st.error(f"Login failed: {str(e)}")

    with tab2:
        st.subheader("Create a new account")

        with st.form("register_form"):
            email = st.text_input("Email")
            reg_username = st.text_input("Username", key="reg_username")
            full_name = st.text_input("Full Name")
            reg_password = st.text_input("Password", type="password", key="reg_password")
            confirm_password = st.text_input("Confirm Password", type="password")
            register_submit = st.form_submit_button("Register", use_container_width=True)

            if register_submit:
                if not all([email, reg_username, reg_password]):
                    st.error("Please fill in all required fields")
                elif reg_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    try:
                        with st.spinner("Creating account..."):
                            APIClient.register(
                                email=email,
                                username=reg_username,
                                password=reg_password,
                                full_name=full_name
                            )

                        st.success("Account created! Please login.")

                    except Exception as e:
                        st.error(f"Registration failed: {str(e)}")


def show_main_app():
    """Display main application."""
    # Sidebar
    with st.sidebar:
        st.title(f"{config.APP_ICON} NEXUS Platform")

        user = st.session_state.get("user", {})
        st.write(f"**{user.get('full_name', user.get('username', 'User'))}**")
        st.write(f"*{user.get('role', 'member')}*")

        st.divider()

        # Navigation
        page = st.radio(
            "Navigate",
            [
                "🏠 Dashboard",
                "📊 Campaign Manager",
                "📈 Analytics",
                "👥 Team Management",
                "⚙️ Settings"
            ],
            key="navigation"
        )

        st.divider()

        if st.button("Logout", use_container_width=True):
            logout_user()
            st.rerun()

    # Main content
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "📊 Campaign Manager":
        show_campaign_manager()
    elif page == "📈 Analytics":
        show_analytics()
    elif page == "👥 Team Management":
        show_team_management()
    elif page == "⚙️ Settings":
        show_settings()


def show_dashboard():
    """Display dashboard."""
    st.title("Dashboard")

    try:
        stats = APIClient.get_dashboard_stats()

        # Metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Campaigns",
                stats.get("total_campaigns", 0)
            )

        with col2:
            st.metric(
                "Active Campaigns",
                stats.get("active_campaigns", 0)
            )

        with col3:
            st.metric(
                "Total Budget",
                f"${stats.get('total_budget', 0):,.2f}"
            )

        with col4:
            st.metric(
                "Average ROI",
                f"{stats.get('average_roi', 0):.1f}%"
            )

        st.divider()

        # Recent Campaigns
        st.subheader("Recent Campaigns")

        recent = stats.get("recent_campaigns", [])
        if recent:
            for campaign in recent:
                with st.expander(f"📊 {campaign['name']} - {campaign['status']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Type:** {campaign['campaign_type']}")
                        st.write(f"**Budget:** ${campaign['total_budget']:,.2f}")
                    with col2:
                        st.write(f"**Spent:** ${campaign['spent_budget']:,.2f}")
                        st.write(f"**Utilization:** {campaign['budget_utilization']:.1f}%")
        else:
            st.info("No campaigns yet. Create your first campaign!")

    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")


def show_campaign_manager():
    """Display campaign manager."""
    st.title("Campaign Manager")

    # Show campaign manager page (will be created separately)
    st.info("Campaign Manager page - See pages/campaign_manager.py for full implementation")


def show_analytics():
    """Display analytics."""
    st.title("Analytics")
    st.info("Analytics page coming soon!")


def show_team_management():
    """Display team management."""
    st.title("Team Management")
    st.info("Team management page coming soon!")


def show_settings():
    """Display settings."""
    st.title("Settings")

    user = st.session_state.get("user", {})

    st.subheader("Profile")
    st.write(f"**Email:** {user.get('email')}")
    st.write(f"**Username:** {user.get('username')}")
    st.write(f"**Role:** {user.get('role')}")


# Main application logic
def main():
    """Main application entry point."""
    if not is_authenticated():
        show_login()
    else:
        show_main_app()


if __name__ == "__main__":
    main()
