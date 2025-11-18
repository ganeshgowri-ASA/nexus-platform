"""
NEXUS Platform - Main Streamlit Application Entry Point
"""

import streamlit as st
from config.settings import settings
from config.database import init_db
from core.utils import setup_logging, get_logger
from modules import get_available_modules

# Setup logging
setup_logging()
logger = get_logger(__name__)


def main():
    """Main application entry point."""

    # Initialize database
    try:
        init_db()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    # Configure Streamlit page
    st.set_page_config(
        page_title=settings.APP_NAME,
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS
    st.markdown("""
        <style>
        .main-header {
            font-size: 3rem;
            font-weight: bold;
            text-align: center;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 2rem;
        }
        .module-card {
            padding: 1rem;
            border-radius: 0.5rem;
            border: 1px solid #e0e0e0;
            margin-bottom: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown("# 🚀 NEXUS Platform")
        st.markdown("---")

        # Get available modules
        available_modules = get_available_modules()

        # Module selection
        st.markdown("### 📦 Modules")

        module_names = list(available_modules.keys())
        module_display_names = {
            "pipeline": "⚙️ Pipeline Builder"
        }

        selected_module = st.radio(
            "Select Module",
            module_names,
            format_func=lambda x: module_display_names.get(x, x)
        )

        st.markdown("---")

        # System info
        st.markdown("### ℹ️ System Info")
        st.markdown(f"**Environment:** {settings.ENVIRONMENT}")
        st.markdown(f"**Debug Mode:** {'On' if settings.DEBUG else 'Off'}")

        # Footer
        st.markdown("---")
        st.markdown("**Version:** 1.0.0")
        st.markdown("**Build:** Pipeline Module")

    # Main content area
    if selected_module:
        # Get module class
        module_class = available_modules.get(selected_module)

        if module_class:
            try:
                # Instantiate and render module
                module_instance = module_class()
                module_instance.render_ui()

            except Exception as e:
                logger.error(f"Error rendering module {selected_module}: {e}")
                st.error(f"Error loading module: {e}")

                # Show error details in debug mode
                if settings.DEBUG:
                    import traceback
                    st.code(traceback.format_exc())

        else:
            st.error(f"Module '{selected_module}' not found")

    else:
        # Welcome screen
        st.markdown('<h1 class="main-header">Welcome to NEXUS</h1>', unsafe_allow_html=True)

        st.markdown("""
        ### 🎯 AI-Powered Productivity Platform

        NEXUS is a unified platform that combines multiple productivity tools with AI capabilities.

        #### 🚀 Getting Started

        Select a module from the sidebar to begin:

        - **⚙️ Pipeline Builder**: Create and manage data pipelines with visual workflow builder
        """)

        # Feature highlights
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            #### 📊 Visual Pipeline Builder
            - Drag-and-drop interface
            - 10+ source connectors
            - Advanced transformations
            - Real-time monitoring
            """)

        with col2:
            st.markdown("""
            #### 🔄 ETL & Stream Processing
            - Batch & real-time processing
            - Data validation
            - Error handling
            - Backfill support
            """)

        with col3:
            st.markdown("""
            #### 📈 Monitoring & Scheduling
            - Cron-based scheduling
            - Apache Airflow integration
            - Execution metrics
            - Alert notifications
            """)

        st.markdown("---")

        # Quick stats
        st.subheader("📊 Platform Status")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Modules", len(available_modules))

        with col2:
            st.metric("Status", "🟢 Running")

        with col3:
            st.metric("Environment", settings.ENVIRONMENT.upper())

        with col4:
            st.metric("Version", "1.0.0")


if __name__ == "__main__":
    main()
