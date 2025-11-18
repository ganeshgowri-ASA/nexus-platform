"""
NEXUS Platform - Main Application Entry Point

Streamlit-based web application for the NEXUS productivity platform.
"""

import streamlit as st
from config.logging import setup_logging, get_logger
from config.database import check_db_connection, init_db

# Initialize logging
setup_logging()
logger = get_logger(__name__)


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="NEXUS Platform",
        page_icon="🚀",
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
        }
        .sub-header {
            font-size: 1.2rem;
            color: #666;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar navigation
    with st.sidebar:
        st.markdown("# 🚀 NEXUS Platform")
        st.markdown("---")

        module = st.selectbox(
            "Select Module",
            [
                "Home",
                "Translation",
                "Authentication",
                "File Storage",
                "AI Orchestrator",
                "Settings",
            ],
        )

    # Route to appropriate module
    if module == "Home":
        render_home()
    elif module == "Translation":
        from nexus.modules.translation.ui import render_translation_ui
        render_translation_ui()
    elif module == "Authentication":
        render_auth_placeholder()
    elif module == "File Storage":
        render_storage_placeholder()
    elif module == "AI Orchestrator":
        render_ai_placeholder()
    elif module == "Settings":
        render_settings()


def render_home():
    """Render home page."""
    st.markdown('<div class="main-header">Welcome to NEXUS Platform</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Unified AI-Powered Productivity Platform</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # Feature cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🌐 Translation")
        st.write("Multi-engine translation with AI enhancement")
        st.write("✅ Google Translate, DeepL, Azure")
        st.write("✅ Translation Memory & Glossaries")
        st.write("✅ Quality Assessment")

    with col2:
        st.markdown("### 🤖 AI Orchestrator")
        st.write("Claude & GPT-4 integration")
        st.write("✅ Context-aware translation")
        st.write("✅ Quality assessment")
        st.write("✅ Language detection")

    with col3:
        st.markdown("### 📁 File Storage")
        st.write("Multi-provider file storage")
        st.write("✅ Local, S3, MinIO, Azure")
        st.write("✅ Document processing")
        st.write("✅ Secure storage")

    st.markdown("---")

    # System status
    st.markdown("### 🔧 System Status")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Check database
        db_status = check_db_connection()
        if db_status:
            st.success("✅ Database Connected")
        else:
            st.error("❌ Database Disconnected")

    with col2:
        # Check Redis (cache)
        try:
            import redis
            from config.settings import settings
            redis_client = redis.from_url(settings.REDIS_URL)
            redis_client.ping()
            st.success("✅ Redis Connected")
        except:
            st.warning("⚠️ Redis Not Available")

    with col3:
        # Translation engines
        from nexus.modules.translation.engines import EngineFactory
        available = EngineFactory.get_available_engines()
        st.info(f"🔄 {len(available)} Translation Engines")

    # Quick start guide
    st.markdown("---")
    st.markdown("### 🚀 Quick Start")

    st.markdown("""
    1. **Configure Environment**: Copy `.env.example` to `.env` and add your API keys
    2. **Initialize Database**: Run `python -m scripts.init_db`
    3. **Start Application**: Run `streamlit run nexus/app.py`
    4. **Access Translation**: Select "Translation" from the sidebar
    5. **Explore Features**: Try language detection, glossaries, and quality assessment
    """)

    # Module overview
    with st.expander("📚 Module Documentation"):
        st.markdown("""
        **Translation Module**:
        - Multi-engine support (Google, DeepL, Azure, AWS, OpenAI, Claude)
        - Automatic language detection
        - Translation memory and glossaries
        - Quality assessment and validation
        - Batch and streaming translation
        - Document translation (PDF, DOCX, XLSX, HTML)
        - Caching and optimization

        **AI Orchestrator**:
        - Claude (Anthropic) integration
        - OpenAI GPT integration
        - Context-aware translation
        - Quality assessment
        - Language detection

        **File Storage**:
        - Local filesystem storage
        - AWS S3 integration
        - MinIO object storage
        - Azure Blob Storage
        - Google Cloud Storage
        """)


def render_auth_placeholder():
    """Placeholder for authentication module."""
    st.header("🔐 Authentication Module")
    st.info("Authentication module UI coming soon...")
    st.markdown("""
    **Features:**
    - User registration and login
    - JWT token authentication
    - Role-based access control
    - API key management
    - Session management
    """)


def render_storage_placeholder():
    """Placeholder for file storage module."""
    st.header("📁 File Storage Module")
    st.info("File storage UI coming soon...")
    st.markdown("""
    **Features:**
    - Upload and download files
    - Multi-provider support
    - File organization
    - Access control
    - Storage analytics
    """)


def render_ai_placeholder():
    """Placeholder for AI orchestrator module."""
    st.header("🤖 AI Orchestrator Module")
    st.info("AI orchestrator UI coming soon...")
    st.markdown("""
    **Features:**
    - Claude API integration
    - OpenAI API integration
    - Prompt management
    - Model selection
    - Response streaming
    """)


def render_settings():
    """Render settings page."""
    st.header("⚙️ Settings")

    st.markdown("### Database Settings")
    from config.settings import settings

    st.text_input("Database URL", value=settings.DATABASE_URL, disabled=True)

    st.markdown("### Translation Settings")
    st.text_input("Default Engine", value=settings.DEFAULT_TRANSLATION_ENGINE, disabled=True)
    st.slider("Cache TTL (seconds)", 0, 86400, settings.TRANSLATION_CACHE_TTL, disabled=True)
    st.slider("Quality Threshold", 0.0, 1.0, settings.TRANSLATION_QUALITY_THRESHOLD, disabled=True)

    st.markdown("### AI Settings")
    st.text_input("Claude Model", value=settings.CLAUDE_MODEL, disabled=True)
    st.text_input("OpenAI Model", value=settings.OPENAI_MODEL, disabled=True)

    st.info("💡 To modify settings, edit the `.env` file and restart the application")


if __name__ == "__main__":
    main()
