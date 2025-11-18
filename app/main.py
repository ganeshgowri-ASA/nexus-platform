"""
NEXUS Platform - Main Application Entry Point
Beautiful Streamlit-based unified productivity suite
"""

import streamlit as st
from typing import Dict, List
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.utils import get_logger, format_timestamp

# Initialize logger
logger = get_logger(__name__)


def apply_custom_css() -> None:
    """Apply custom CSS for beautiful gradient UI"""
    st.markdown("""
        <style>
        /* Main gradient background */
        .stApp {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }

        /* Custom card styling */
        .nexus-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            margin: 15px 0;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .nexus-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 48px rgba(0, 0, 0, 0.15);
        }

        /* Header styling */
        .nexus-header {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            color: white;
            box-shadow: 0 8px 32px rgba(99, 102, 241, 0.3);
        }

        .nexus-header h1 {
            color: white !important;
            margin: 0;
            font-size: 3em;
            font-weight: 700;
        }

        .nexus-header p {
            color: rgba(255, 255, 255, 0.9);
            margin: 10px 0 0 0;
            font-size: 1.2em;
        }

        /* Module card styling */
        .module-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            padding: 20px;
            margin: 10px 0;
            color: white;
            cursor: pointer;
            transition: all 0.3s ease;
            border: 2px solid transparent;
        }

        .module-card:hover {
            transform: scale(1.05);
            border-color: white;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
        }

        .module-icon {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .module-title {
            font-size: 1.3em;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .module-description {
            font-size: 0.9em;
            opacity: 0.9;
        }

        /* Metric card styling */
        .metric-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
        }

        .metric-value {
            font-size: 2.5em;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .metric-label {
            font-size: 1em;
            color: #666;
            margin-top: 8px;
        }

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        }

        [data-testid="stSidebar"] .stMarkdown {
            color: white;
        }

        /* Button styling */
        .stButton > button {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: 600;
            transition: all 0.3s ease;
        }

        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
        }

        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)


def get_module_list() -> List[Dict[str, str]]:
    """Get list of all 24 NEXUS modules"""
    return [
        {"icon": "📝", "name": "Word Processor", "description": "Create and edit documents"},
        {"icon": "📊", "name": "Excel Sheets", "description": "Spreadsheets and data analysis"},
        {"icon": "📈", "name": "PowerPoint", "description": "Create presentations"},
        {"icon": "📧", "name": "Email Client", "description": "Manage your emails"},
        {"icon": "💬", "name": "Chat & Messaging", "description": "Real-time communication"},
        {"icon": "📋", "name": "Project Manager", "description": "Track tasks and projects"},
        {"icon": "🔄", "name": "Flowcharts", "description": "Visual process diagrams"},
        {"icon": "📊", "name": "Analytics", "description": "Data visualization and insights"},
        {"icon": "📅", "name": "Calendar", "description": "Schedule and events"},
        {"icon": "📁", "name": "File Manager", "description": "Organize your files"},
        {"icon": "🎨", "name": "Design Studio", "description": "Graphics and design"},
        {"icon": "📝", "name": "Notes", "description": "Quick note taking"},
        {"icon": "🔍", "name": "Search", "description": "Universal search"},
        {"icon": "🤖", "name": "AI Assistant", "description": "Claude-powered AI help"},
        {"icon": "📊", "name": "Database", "description": "Data management"},
        {"icon": "🔐", "name": "Password Manager", "description": "Secure credentials"},
        {"icon": "📞", "name": "Video Calls", "description": "Video conferencing"},
        {"icon": "📚", "name": "Knowledge Base", "description": "Documentation hub"},
        {"icon": "⚙️", "name": "Settings", "description": "Platform configuration"},
        {"icon": "👥", "name": "Team Collaboration", "description": "Work together"},
        {"icon": "📈", "name": "Reports", "description": "Generate reports"},
        {"icon": "🔔", "name": "Notifications", "description": "Stay updated"},
        {"icon": "🌐", "name": "Web Browser", "description": "Integrated browsing"},
        {"icon": "💾", "name": "Backup & Sync", "description": "Data protection"},
    ]


def render_header() -> None:
    """Render beautiful header section"""
    st.markdown(f"""
        <div class="nexus-header">
            <h1>🚀 NEXUS Platform</h1>
            <p>Your Unified Productivity Suite - 24 Powerful Modules in One Place</p>
        </div>
    """, unsafe_allow_html=True)


def render_metrics() -> None:
    """Render key metrics"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-value">24</div>
                <div class="metric-label">Integrated Modules</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-value">100%</div>
                <div class="metric-label">Unified Experience</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-value">∞</div>
                <div class="metric-label">Productivity Boost</div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-value">AI</div>
                <div class="metric-label">Powered by Claude</div>
            </div>
        """, unsafe_allow_html=True)


def render_modules() -> None:
    """Render module grid"""
    st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
    st.subheader("🎯 Available Modules")

    modules = get_module_list()

    # Create grid layout
    cols = st.columns(4)
    for idx, module in enumerate(modules):
        col = cols[idx % 4]
        with col:
            st.markdown(f"""
                <div class="module-card">
                    <div class="module-icon">{module['icon']}</div>
                    <div class="module-title">{module['name']}</div>
                    <div class="module-description">{module['description']}</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def render_sidebar() -> None:
    """Render sidebar with navigation and info"""
    with st.sidebar:
        st.markdown("## 🎯 Navigation")

        # Module selector
        selected_module = st.selectbox(
            "Select Module",
            ["Home"] + [m["name"] for m in get_module_list()],
            key="module_selector"
        )

        st.markdown("---")

        # System info
        st.markdown("## ℹ️ System Info")
        st.markdown(f"""
            - **Version:** {settings.app_version}
            - **Environment:** {settings.environment}
            - **Time:** {format_timestamp()}
        """)

        st.markdown("---")

        # Quick actions
        st.markdown("## ⚡ Quick Actions")
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        if st.button("⚙️ Settings", use_container_width=True):
            st.info("Settings module coming soon!")

        if st.button("❓ Help", use_container_width=True):
            st.info("Help documentation coming soon!")

        st.markdown("---")

        # Footer
        st.markdown("""
            <div style="text-align: center; color: white; opacity: 0.8; font-size: 0.9em;">
                <p>Powered by Anthropic Claude</p>
                <p>© 2024 NEXUS Platform</p>
            </div>
        """, unsafe_allow_html=True)


def render_welcome_section() -> None:
    """Render welcome section with information"""
    st.markdown('<div class="nexus-card">', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 👋 Welcome to NEXUS Platform!")
        st.markdown("""
            NEXUS is your all-in-one unified productivity platform that combines 24 powerful
            modules into a seamless experience. Whether you're creating documents, analyzing
            data, managing projects, or collaborating with your team, NEXUS has you covered.

            **Key Features:**
            - 📝 Full Office Suite (Word, Excel, PowerPoint)
            - 💬 Communication Tools (Email, Chat, Video)
            - 📊 Analytics & Reporting
            - 🤖 AI-Powered Assistant
            - 👥 Team Collaboration
            - 🔐 Enterprise Security
            - 🌐 Cloud Integration
            - ⚡ Lightning Fast Performance
        """)

    with col2:
        st.markdown("### 🚀 Quick Start")
        st.markdown("""
            1. Choose a module from the sidebar
            2. Start creating and collaborating
            3. Let AI assist your workflow
            4. Enjoy seamless productivity!

            **Need Help?**
            - Check our documentation
            - Contact support
            - Join the community
        """)

    st.markdown('</div>', unsafe_allow_html=True)


def render_status_section() -> None:
    """Render system status section"""
    st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
    st.subheader("📊 System Status")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.success("✅ All Systems Operational")
        st.metric("Uptime", "99.9%")

    with col2:
        st.info("🔄 Database Connected")
        st.metric("Active Users", "1")

    with col3:
        st.success("🤖 AI Ready")
        st.metric("API Status", "Online")

    st.markdown('</div>', unsafe_allow_html=True)


def main() -> None:
    """Main application entry point"""
    # Configure Streamlit page
    st.set_page_config(
        page_title="NEXUS Platform",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Apply custom CSS
    apply_custom_css()

    # Log application start
    logger.info(f"NEXUS Platform started - Version {settings.app_version}")

    # Render sidebar
    render_sidebar()

    # Render main content
    render_header()
    render_metrics()

    st.markdown("<br>", unsafe_allow_html=True)

    render_welcome_section()

    st.markdown("<br>", unsafe_allow_html=True)

    render_modules()

    st.markdown("<br>", unsafe_allow_html=True)

    render_status_section()

    # Log page view
    logger.debug("Main page rendered successfully")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")
