<<<<<<< HEAD
"""
<<<<<<< HEAD
NEXUS Platform - Streamlit Frontend Application

Main entry point for the Streamlit-based Document Management System UI.
Provides authentication, navigation, and modular page routing.
"""

import os
import sys
from pathlib import Path

import streamlit as st
from streamlit_option_menu import streamlit_option_menu

# Add project root to path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.core.config import get_settings
from modules.documents.streamlit_ui import render_document_management

# Page configuration
st.set_page_config(
    page_title="NEXUS - Document Management System",
    page_icon="📁",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://nexus-platform.com/help',
        'Report a bug': 'https://nexus-platform.com/bug-report',
        'About': "NEXUS Platform - Enterprise Document Management System"
    }
)

# Load settings
settings = get_settings()

# Custom CSS for modern UI
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #1f77b4;
        --secondary-color: #ff7f0e;
        --success-color: #2ca02c;
        --danger-color: #d62728;
        --warning-color: #ff9800;
        --info-color: #17a2b8;
        --dark-color: #212529;
        --light-color: #f8f9fa;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Custom header */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }

    .main-header p {
        color: rgba(255, 255, 255, 0.9);
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
    }

    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }

    /* Card styling */
    .custom-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        border-left: 4px solid var(--primary-color);
    }

    /* Button styling */
    .stButton > button {
        border-radius: 5px;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }

    /* File uploader */
    .uploadedFile {
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        transition: all 0.3s ease;
    }

    .uploadedFile:hover {
        border-color: #764ba2;
        background-color: #f8f9fa;
    }

    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }

    /* Metrics */
    .metric-container {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        text-align: center;
    }

    /* Tags */
    .tag {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        margin: 0.25rem;
        border-radius: 20px;
        background-color: #e9ecef;
        font-size: 0.875rem;
        font-weight: 500;
    }

    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 4px;
        font-size: 0.875rem;
        font-weight: 600;
    }

    .status-active { background-color: #d4edda; color: #155724; }
    .status-draft { background-color: #fff3cd; color: #856404; }
    .status-archived { background-color: #d1ecf1; color: #0c5460; }
    .status-locked { background-color: #f8d7da; color: #721c24; }

    /* Tables */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }

    /* Alerts */
    .alert {
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }

    .alert-success {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        color: #155724;
    }

    .alert-error {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        color: #721c24;
    }

    .alert-warning {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        color: #856404;
    }

    .alert-info {
        background-color: #d1ecf1;
        border-left: 4px solid #17a2b8;
        color: #0c5460;
    }

    /* Breadcrumbs */
    .breadcrumb {
        background-color: transparent;
        padding: 0.75rem 0;
        margin-bottom: 1rem;
    }

    .breadcrumb-item {
        display: inline-block;
        color: #6c757d;
    }

    .breadcrumb-item + .breadcrumb-item::before {
        content: ">";
        padding: 0 0.5rem;
        color: #6c757d;
    }

    /* Loading animation */
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .loading-spinner {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #667eea;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 2rem auto;
=======
"""NEXUS Platform - Streamlit Frontend"""
import streamlit as st
from streamlit_option_menu import option_menu
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="NEXUS Platform",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .feature-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 0.5rem;
        color: white;
        text-align: center;
>>>>>>> origin/claude/ocr-translation-modules-01Kv1eeHRaW9ea224g8V59NS
    }
</style>
""", unsafe_allow_html=True)

<<<<<<< HEAD

def initialize_session_state():
    """Initialize session state variables."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if 'user' not in st.session_state:
        st.session_state.user = None

    if 'api_token' not in st.session_state:
        st.session_state.api_token = None

    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Documents"

    if 'selected_folder' not in st.session_state:
        st.session_state.selected_folder = None

    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""

    if 'view_mode' not in st.session_state:
        st.session_state.view_mode = "grid"  # grid or list


def render_login_page():
    """Render the login page."""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""
        <div class="main-header" style="text-align: center; margin-top: 3rem;">
            <h1>📁 NEXUS Platform</h1>
            <p>Enterprise Document Management System</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        with st.container():
            st.markdown('<div class="custom-card">', unsafe_allow_html=True)

            tab1, tab2 = st.tabs(["Login", "Register"])

            with tab1:
                st.markdown("### Sign In")
                username = st.text_input("Username", key="login_username")
                password = st.text_input("Password", type="password", key="login_password")
                remember_me = st.checkbox("Remember me")

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("Login", use_container_width=True, type="primary"):
                        # TODO: Implement actual authentication with backend
                        # For now, use demo mode
                        if username and password:
                            st.session_state.authenticated = True
                            st.session_state.user = {
                                "id": 1,
                                "username": username,
                                "email": f"{username}@example.com",
                                "full_name": username.title(),
                                "is_admin": username == "admin"
                            }
                            st.session_state.api_token = "demo_token_12345"
                            st.rerun()
                        else:
                            st.error("Please enter username and password")

                with col_btn2:
                    if st.button("Forgot Password?", use_container_width=True):
                        st.info("Password reset functionality coming soon!")

            with tab2:
                st.markdown("### Create Account")
                new_username = st.text_input("Username", key="reg_username")
                new_email = st.text_input("Email", key="reg_email")
                new_password = st.text_input("Password", type="password", key="reg_password")
                confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")

                if st.button("Register", use_container_width=True, type="primary"):
                    if new_password != confirm_password:
                        st.error("Passwords do not match!")
                    elif len(new_password) < 8:
                        st.error("Password must be at least 8 characters long!")
                    else:
                        st.success("Registration successful! Please login.")

            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; color: #6c757d; font-size: 0.875rem;">
            <p>© 2025 NEXUS Platform. All rights reserved.</p>
            <p>Version {}</p>
        </div>
        """.format(settings.APP_VERSION), unsafe_allow_html=True)


def render_sidebar():
    """Render the sidebar navigation."""
    with st.sidebar:
        # User info
        st.markdown("""
        <div class="custom-card">
            <h3 style="margin: 0; color: #667eea;">👤 {}</h3>
            <p style="margin: 0.5rem 0 0 0; color: #6c757d; font-size: 0.875rem;">{}</p>
        </div>
        """.format(
            st.session_state.user.get('full_name', 'User'),
            st.session_state.user.get('email', 'user@example.com')
        ), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Navigation menu
        selected = streamlit_option_menu(
            menu_title="Navigation",
            options=[
                "Documents",
                "Search",
                "Recent",
                "Shared",
                "Starred",
                "Trash",
                "Analytics",
                "Settings"
            ],
            icons=[
                "folder",
                "search",
                "clock-history",
                "share",
                "star",
                "trash",
                "bar-chart",
                "gear"
            ],
            menu_icon="list",
            default_index=0,
            styles={
                "container": {"padding": "0"},
                "nav-link": {
                    "font-size": "0.95rem",
                    "text-align": "left",
                    "margin": "0.25rem 0",
                    "padding": "0.75rem 1rem",
                },
                "nav-link-selected": {
                    "background-color": "#667eea",
                    "font-weight": "600",
                },
            }
        )

        st.session_state.current_page = selected

        st.markdown("<br>", unsafe_allow_html=True)

        # Storage info
        st.markdown("### 💾 Storage")
        storage_used = 45.2  # GB
        storage_total = 100.0  # GB
        storage_percent = (storage_used / storage_total) * 100

        st.progress(storage_percent / 100)
        st.markdown(f"""
        <div style="text-align: center; margin-top: 0.5rem;">
            <span style="font-weight: 600;">{storage_used:.1f} GB</span>
            <span style="color: #6c757d;"> / {storage_total:.1f} GB</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Quick actions
        st.markdown("### ⚡ Quick Actions")
        if st.button("📤 Upload Files", use_container_width=True):
            st.session_state.show_upload_modal = True

        if st.button("📁 New Folder", use_container_width=True):
            st.session_state.show_new_folder_modal = True

        if st.button("🔍 Advanced Search", use_container_width=True):
            st.session_state.current_page = "Search"
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.divider()

        # Logout button
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.api_token = None
            st.rerun()


def render_header():
    """Render the main header."""
    col1, col2, col3 = st.columns([3, 2, 1])

    with col1:
        st.markdown("""
        <div class="main-header">
            <h1>📁 {}</h1>
            <p>Welcome back, {}!</p>
        </div>
        """.format(
            st.session_state.current_page,
            st.session_state.user.get('full_name', 'User')
        ), unsafe_allow_html=True)

    with col2:
        if st.session_state.current_page == "Documents":
            view_mode = st.radio(
                "View",
                ["Grid", "List"],
                horizontal=True,
                key="view_mode_selector"
            )
            st.session_state.view_mode = view_mode.lower()

    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        notifications = st.button("🔔 Notifications (3)", use_container_width=True)
        if notifications:
            st.info("You have 3 new notifications")


def render_dashboard():
    """Render the main dashboard based on current page."""
    page = st.session_state.current_page

    if page == "Documents":
        render_document_management()

    elif page == "Search":
        st.markdown("### 🔍 Advanced Search")
        render_search_page()

    elif page == "Recent":
        st.markdown("### 🕐 Recent Documents")
        st.info("Recently accessed documents will appear here")

    elif page == "Shared":
        st.markdown("### 👥 Shared with Me")
        st.info("Documents shared with you will appear here")

    elif page == "Starred":
        st.markdown("### ⭐ Starred Documents")
        st.info("Your starred documents will appear here")

    elif page == "Trash":
        st.markdown("### 🗑️ Trash")
        st.info("Deleted documents will appear here")

    elif page == "Analytics":
        render_analytics_page()

    elif page == "Settings":
        render_settings_page()


def render_search_page():
    """Render advanced search page."""
    col1, col2 = st.columns([2, 1])

    with col1:
        search_query = st.text_input(
            "Search documents",
            placeholder="Enter keywords, tags, or file names...",
            key="advanced_search_query"
        )

    with col2:
        search_button = st.button("🔍 Search", use_container_width=True, type="primary")

    with st.expander("🔧 Advanced Filters", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            file_types = st.multiselect(
                "File Types",
                ["PDF", "Word", "Excel", "PowerPoint", "Images", "Text", "Other"]
            )

            date_range = st.date_input(
                "Date Range",
                value=None,
                key="search_date_range"
            )

        with col2:
            status_filter = st.multiselect(
                "Status",
                ["Active", "Draft", "Archived", "In Review"]
            )

            size_range = st.slider(
                "File Size (MB)",
                min_value=0,
                max_value=100,
                value=(0, 100),
                key="search_size_range"
            )

        with col3:
            tags_filter = st.multiselect(
                "Tags",
                ["Important", "Urgent", "Reviewed", "Approved"]
            )

            owner_filter = st.text_input("Owner")

    if search_button and search_query:
        with st.spinner("Searching..."):
            st.success(f"Found 0 results for '{search_query}'")
            st.info("Search functionality will be integrated with backend API")


def render_analytics_page():
    """Render analytics dashboard."""
    st.markdown("### 📊 Document Analytics")

    # Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Documents",
            value="1,234",
            delta="12 this week"
        )

    with col2:
        st.metric(
            label="Storage Used",
            value="45.2 GB",
            delta="2.3 GB"
        )

    with col3:
        st.metric(
            label="Users Active",
            value="56",
            delta="8"
        )

    with col4:
        st.metric(
            label="Shared Files",
            value="89",
            delta="-3"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts placeholder
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📈 Upload Trends")
        st.line_chart({"Uploads": [10, 15, 13, 17, 20, 18, 25]})

    with col2:
        st.markdown("#### 📁 Documents by Type")
        st.bar_chart({"PDF": 45, "Word": 30, "Excel": 15, "Other": 10})


def render_settings_page():
    """Render settings page."""
    st.markdown("### ⚙️ Settings")

    tab1, tab2, tab3, tab4 = st.tabs([
        "Profile",
        "Preferences",
        "Security",
        "Notifications"
    ])

    with tab1:
        st.markdown("#### 👤 Profile Settings")
        col1, col2 = st.columns(2)

        with col1:
            st.text_input("Full Name", value=st.session_state.user.get('full_name', ''))
            st.text_input("Email", value=st.session_state.user.get('email', ''))

        with col2:
            st.text_input("Phone", value="")
            st.text_input("Department", value="")

        if st.button("Save Profile", type="primary"):
            st.success("Profile updated successfully!")

    with tab2:
        st.markdown("#### 🎨 Preferences")
        st.selectbox("Default View", ["Grid", "List"])
        st.selectbox("Items per Page", [10, 20, 50, 100])
        st.checkbox("Enable Notifications", value=True)
        st.checkbox("Auto-save Drafts", value=True)

    with tab3:
        st.markdown("#### 🔒 Security")
        st.text_input("Current Password", type="password")
        st.text_input("New Password", type="password")
        st.text_input("Confirm New Password", type="password")

        if st.button("Change Password", type="primary"):
            st.success("Password changed successfully!")

    with tab4:
        st.markdown("#### 🔔 Notification Settings")
        st.checkbox("Email notifications", value=True)
        st.checkbox("Document upload notifications", value=True)
        st.checkbox("Comment notifications", value=True)
        st.checkbox("Share notifications", value=True)
        st.checkbox("Workflow notifications", value=True)


def main():
    """Main application entry point."""
    initialize_session_state()

    if not st.session_state.authenticated:
        render_login_page()
    else:
        render_sidebar()
        render_header()
        st.markdown("<br>", unsafe_allow_html=True)
        render_dashboard()
=======
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
>>>>>>> origin/claude/build-campaign-manager-01KFpVYVNSuz2bfrpAMAZpwp


if __name__ == "__main__":
    main()
=======
# Sidebar navigation
with st.sidebar:
    st.markdown("# 🚀 NEXUS Platform")
    st.markdown("### AI-Powered Productivity Suite")
    st.markdown("---")

    selected = option_menu(
        menu_title="Main Menu",
        options=["Home", "OCR", "Translation", "Settings"],
        icons=["house", "file-text", "translate", "gear"],
        menu_icon="cast",
        default_index=0,
    )

    st.markdown("---")
    st.markdown("### About")
    st.info("NEXUS Platform v0.1.0\n\n24 Integrated Modules for Enhanced Productivity")

# Main content
if selected == "Home":
    # Home page
    st.markdown('<p class="main-header">Welcome to NEXUS Platform 🚀</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Your AI-Powered Productivity Suite with 24 Integrated Modules</p>', unsafe_allow_html=True)

    # Feature cards
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📄 OCR Module")
        st.markdown("""
        <div class="feature-box">
        <h4>Text Extraction Made Easy</h4>
        <ul>
            <li>Extract text from images and PDFs</li>
            <li>Handwriting recognition</li>
            <li>Table detection and extraction</li>
            <li>100+ languages supported</li>
            <li>Layout analysis</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("### 🌐 Translation Module")
        st.markdown("""
        <div class="feature-box">
        <h4>Professional Translation Services</h4>
        <ul>
            <li>Translate text to 100+ languages</li>
            <li>Custom glossaries</li>
            <li>Batch translation</li>
            <li>Quality scoring</li>
            <li>Context-aware translation</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

    # Quick stats
    st.markdown("---")
    st.markdown("### 📊 Platform Capabilities")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="stat-card">
            <h2>100+</h2>
            <p>Languages Supported</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="stat-card">
            <h2>24</h2>
            <p>Integrated Modules</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="stat-card">
            <h2>3</h2>
            <p>OCR Engines</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="stat-card">
            <h2>∞</h2>
            <p>Possibilities</p>
        </div>
        """, unsafe_allow_html=True)

    # Getting started
    st.markdown("---")
    st.markdown("### 🚀 Getting Started")

    with st.expander("📖 Quick Start Guide"):
        st.markdown("""
        1. **OCR Module**: Navigate to the OCR page to extract text from images and PDFs
        2. **Translation Module**: Go to Translation page to translate text between languages
        3. **Settings**: Configure API keys and preferences
        4. **API Documentation**: Visit `/api/v1/docs` for full API documentation
        """)

    with st.expander("🔑 API Keys Configuration"):
        st.markdown("""
        To use all features, configure the following API keys in Settings or `.env` file:

        - **Google Cloud API Key**: For Google Vision OCR and Translation
        - **AWS Credentials**: For AWS Textract OCR
        - **Anthropic API Key**: For Claude-powered translation

        Note: Tesseract OCR works without any API keys!
        """)

elif selected == "OCR":
    # Import OCR page
    from pages import ocr_page
    ocr_page.show()

elif selected == "Translation":
    # Import Translation page
    from pages import translation_page
    translation_page.show()

elif selected == "Settings":
    st.markdown("# ⚙️ Settings")
    st.markdown("### Configure your NEXUS Platform")

    with st.expander("🔑 API Keys", expanded=True):
        google_api_key = st.text_input("Google Cloud API Key", type="password")
        aws_access_key = st.text_input("AWS Access Key ID", type="password")
        aws_secret_key = st.text_input("AWS Secret Access Key", type="password")
        anthropic_api_key = st.text_input("Anthropic API Key", type="password")

        if st.button("Save API Keys"):
            st.success("API keys saved successfully!")
            st.info("Note: In production, these should be saved securely in environment variables or a secrets manager.")

    with st.expander("⚙️ OCR Settings"):
        ocr_engine = st.selectbox(
            "Default OCR Engine",
            ["tesseract", "google_vision", "aws_textract"]
        )
        confidence_threshold = st.slider(
            "Confidence Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1
        )

        if st.button("Save OCR Settings"):
            st.success("OCR settings saved!")

    with st.expander("🌐 Translation Settings"):
        translation_service = st.selectbox(
            "Default Translation Service",
            ["google", "anthropic", "deepl"]
        )
        default_target_lang = st.selectbox(
            "Default Target Language",
            ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]
        )

        if st.button("Save Translation Settings"):
            st.success("Translation settings saved!")

    with st.expander("ℹ️ System Information"):
        st.markdown(f"""
        **Version:** 0.1.0
        **Backend API:** http://localhost:8000
        **API Docs:** http://localhost:8000/api/v1/docs
        **Environment:** {os.getenv('APP_ENV', 'development')}
        """)
>>>>>>> origin/claude/ocr-translation-modules-01Kv1eeHRaW9ea224g8V59NS
