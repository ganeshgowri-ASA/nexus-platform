"""Main NEXUS Platform Application."""
import streamlit as st
from config.settings import settings
from core.database.session import init_db
from core.auth.middleware import render_login_page, logout

# Page configuration
st.set_page_config(
    page_title=settings.PAGE_TITLE,
    page_icon=settings.PAGE_ICON,
    layout=settings.LAYOUT,
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
    }

    .main-title {
        font-size: 3rem;
        font-weight: bold;
        margin: 0;
    }

    .main-subtitle {
        font-size: 1.3rem;
        opacity: 0.9;
        margin-top: 0.5rem;
    }

    .module-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
        cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .module-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }

    .module-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }

    .module-name {
        font-size: 1.5rem;
        font-weight: bold;
        color: #333;
    }

    .module-description {
        color: #666;
        margin-top: 0.5rem;
    }

    .stButton>button {
        border-radius: 5px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application entry point."""
    # Initialize database
    try:
        init_db()
    except Exception as e:
        st.error(f"Database initialization error: {str(e)}")
        st.stop()

    # Check authentication
    if 'user_id' not in st.session_state or 'user_email' not in st.session_state:
        render_login_page()
        return

    # Main application
    render_main_app()


def render_main_app():
    """Render main application."""
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem;">
            <h1>🚀 NEXUS</h1>
            <p style="color: #666;">Welcome, {st.session_state.get('user_name', 'User')}</p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Module selection
        module = st.selectbox(
            "Select Module",
            [
                "🏠 Dashboard",
                "📊 Excel Spreadsheet",
                "📝 Word Processor",
                "📽️ PowerPoint",
                "📁 File Manager",
                "💬 Chat",
                "📧 Email",
                "📅 Calendar",
                "✅ Tasks",
                "📊 Analytics",
                "👥 Teams",
                "⚙️ Settings"
            ]
        )

        st.divider()

        # User actions
        if st.button("🚪 Logout", use_container_width=True):
            logout()

    # Route to module
    if module == "🏠 Dashboard":
        render_dashboard()
    elif module == "📊 Excel Spreadsheet":
        from modules.excel.streamlit_ui import render_excel_page
        render_excel_page()
    else:
        st.info(f"{module} module coming soon!")


def render_dashboard():
    """Render dashboard."""
    # Header
    st.markdown("""
    <div class="main-header">
        <div class="main-title">🚀 NEXUS Platform</div>
        <div class="main-subtitle">All-in-One Productivity Suite with AI</div>
    </div>
    """, unsafe_allow_html=True)

    # Welcome message
    st.write(f"## Welcome back, {st.session_state.get('user_name', 'User')}! 👋")

    # Quick stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📊 Spreadsheets", "0", "+0")
    with col2:
        st.metric("📝 Documents", "0", "+0")
    with col3:
        st.metric("📽️ Presentations", "0", "+0")
    with col4:
        st.metric("👥 Collaborators", "0", "+0")

    st.divider()

    # Module cards
    st.write("## 📱 Available Modules")

    modules = [
        {
            "icon": "📊",
            "name": "Excel Spreadsheet",
            "description": "World-class spreadsheet with 200+ functions and AI analysis",
            "status": "✅ Ready"
        },
        {
            "icon": "📝",
            "name": "Word Processor",
            "description": "Rich text editor with AI writing assistance",
            "status": "🔜 Coming Soon"
        },
        {
            "icon": "📽️",
            "name": "PowerPoint",
            "description": "Create stunning presentations with AI-generated slides",
            "status": "🔜 Coming Soon"
        },
        {
            "icon": "📁",
            "name": "File Manager",
            "description": "Cloud storage with intelligent organization",
            "status": "🔜 Coming Soon"
        },
        {
            "icon": "💬",
            "name": "Chat",
            "description": "Team messaging with AI chatbot support",
            "status": "🔜 Coming Soon"
        },
        {
            "icon": "📧",
            "name": "Email",
            "description": "Email client with AI-powered inbox management",
            "status": "🔜 Coming Soon"
        }
    ]

    # Display modules in grid
    cols = st.columns(3)
    for idx, module in enumerate(modules):
        with cols[idx % 3]:
            st.markdown(f"""
            <div class="module-card">
                <div class="module-icon">{module['icon']}</div>
                <div class="module-name">{module['name']}</div>
                <div class="module-description">{module['description']}</div>
                <div style="margin-top: 1rem; color: #667eea; font-weight: bold;">{module['status']}</div>
            </div>
            """, unsafe_allow_html=True)

    # Recent activity
    st.divider()
    st.write("## 📈 Recent Activity")
    st.info("No recent activity yet. Start by creating a new spreadsheet!")


if __name__ == "__main__":
    main()
