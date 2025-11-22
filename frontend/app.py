"""
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
    }
</style>
""", unsafe_allow_html=True)


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


if __name__ == "__main__":
    main()
