"""
NEXUS Platform - Unified AI-Powered Productivity Suite
Main entry point for the multi-page Streamlit application
"""
import streamlit as st
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from database.connection import init_db
from config.settings import settings

# Page configuration
st.set_page_config(
    page_title="NEXUS - AI Productivity Platform",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main home page"""

    # Initialize database
    init_db()

    # Header
    st.title("🚀 NEXUS - AI Productivity Platform")
    st.markdown("### Your Unified Workspace for Maximum Productivity")

    st.divider()

    # Welcome section
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        ## Welcome to NEXUS

        NEXUS is your all-in-one productivity platform, powered by Claude AI, bringing together
        essential business tools in a unified, intelligent workspace.

        ### 🎯 What's Included

        Navigate through the sidebar to access:

        **Communication & Collaboration:**
        - 📧 **Email Client** - Smart inbox with AI-powered replies and threading
        - 💬 **Chat** - Real-time messaging with rooms and file sharing
        - 📹 **Video Conference** - WebRTC-based video calls with recording

        **Content Creation:**
        - 📊 **PowerPoint** - Presentation editor with AI content generation
        - 📝 **Notes** - Rich text notes with AI summaries and organization

        **Project Management:**
        - 📊 **Projects** - Gantt charts, Kanban boards, dependencies
        - 📅 **Calendar** - Day/Week/Month views with smart scheduling

        **Business Operations:**
        - 💼 **CRM** - Contact management, deals pipeline, email integration

        ### 🤖 AI Features

        Every application is enhanced with Claude AI capabilities:
        - Smart content generation
        - Intelligent summaries
        - Automated suggestions
        - Context-aware assistance

        ### 🚀 Getting Started

        1. Select an application from the sidebar
        2. Create your first item (note, project, contact, etc.)
        3. Explore AI features to boost productivity
        4. Export and share your work

        """)

    with col2:
        st.markdown("### 📊 Quick Stats")

        # Get stats from database
        from database.connection import SessionLocal
        from database.models import (
            Presentation, EmailMessage, ChatRoom, Project,
            CalendarEvent, VideoConference, Note, CRMContact
        )

        db = SessionLocal()

        stats = {
            "📊 Presentations": db.query(Presentation).count(),
            "📧 Emails": db.query(EmailMessage).count(),
            "💬 Chat Rooms": db.query(ChatRoom).count(),
            "📊 Projects": db.query(Project).count(),
            "📅 Events": db.query(CalendarEvent).count(),
            "📹 Conferences": db.query(VideoConference).count(),
            "📝 Notes": db.query(Note).count(),
            "💼 Contacts": db.query(CRMContact).count(),
        }

        db.close()

        for label, count in stats.items():
            st.metric(label, count)

        st.divider()

        st.markdown("### ⚙️ Settings")
        st.write(f"**Environment:** {settings.ENVIRONMENT}")
        st.write(f"**AI Enabled:** {'✅' if settings.ENABLE_AI_FEATURES else '❌'}")
        st.write(f"**Export Enabled:** {'✅' if settings.ENABLE_EXPORT else '❌'}")

    st.divider()

    # Features grid
    st.markdown("## 🎨 Featured Applications")

    col1, col2, col3, col4 = st.columns(4)

    apps = [
        {
            "icon": "📊",
            "name": "PowerPoint",
            "desc": "Create stunning presentations",
            "path": "pages/1_📊_PowerPoint.py"
        },
        {
            "icon": "📧",
            "name": "Email",
            "desc": "Smart email management",
            "path": "pages/2_📧_Email.py"
        },
        {
            "icon": "💬",
            "name": "Chat",
            "desc": "Team messaging",
            "path": "pages/3_💬_Chat.py"
        },
        {
            "icon": "📊",
            "name": "Projects",
            "desc": "Project management",
            "path": "pages/4_📊_Projects.py"
        },
        {
            "icon": "📅",
            "name": "Calendar",
            "desc": "Schedule & events",
            "path": "pages/5_📅_Calendar.py"
        },
        {
            "icon": "📹",
            "name": "Video",
            "desc": "Video conferencing",
            "path": "pages/6_📹_Video_Conference.py"
        },
        {
            "icon": "📝",
            "name": "Notes",
            "desc": "Note-taking & organization",
            "path": "pages/7_📝_Notes.py"
        },
        {
            "icon": "💼",
            "name": "CRM",
            "desc": "Customer relationships",
            "path": "pages/8_💼_CRM.py"
        },
    ]

    columns = [col1, col2, col3, col4]

    for idx, app in enumerate(apps):
        with columns[idx % 4]:
            st.markdown(f"""
            <div style='text-align: center; padding: 20px; border: 1px solid #ddd; border-radius: 10px; margin: 10px 0;'>
                <h1>{app['icon']}</h1>
                <h3>{app['name']}</h3>
                <p>{app['desc']}</p>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # Footer
    st.markdown("""
    ---
    ### 💡 Tips

    - Use the sidebar to navigate between applications
    - All data is stored locally in SQLite database
    - Export capabilities available in PDF, PPTX, XLSX, DOCX formats
    - AI features require ANTHROPIC_API_KEY in .env file

    ### 📚 Need Help?

    - Check application-specific help sections
    - Review documentation in README.md
    - Each app has intuitive UI with tooltips

    **Built with ❤️ using Streamlit and Claude AI**
    """)

if __name__ == "__main__":
    main()
