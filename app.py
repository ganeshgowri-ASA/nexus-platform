"""
NEXUS Platform - AI-Powered Productivity Suite
Main Streamlit Application
"""
import streamlit as st
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from modules.word.module import WordEditorModule
from config.settings import settings
from config.constants import MODULES
from core.logging import app_logger


def initialize_app() -> None:
    """Initialize the application."""
    # Set page config
    st.set_page_config(
        page_title="NEXUS - AI Productivity Platform",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialize session state
    if "current_module" not in st.session_state:
        st.session_state.current_module = "Word Editor"

    if "app_initialized" not in st.session_state:
        st.session_state.app_initialized = True
        app_logger.info("NEXUS application initialized")


def render_welcome_banner() -> None:
    """Render welcome banner."""
    st.markdown(
        """
        <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 2rem;'>
            <h1 style='color: white; margin: 0;'>🚀 NEXUS</h1>
            <p style='color: white; margin: 0.5rem 0 0 0; font-size: 1.2rem;'>AI-Powered Productivity Platform</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_module_selector() -> str:
    """
    Render module selector in sidebar.

    Returns:
        Selected module name
    """
    st.sidebar.title("📱 NEXUS Modules")

    # Available modules (currently only Word Editor is implemented)
    available_modules = ["Word Editor"]

    # Coming soon modules
    coming_soon = [
        "Excel Analyzer",
        "PowerPoint Creator",
        "PDF Manager",
        "Project Manager",
        "Email Client",
        "AI Chat Assistant",
        "Flowchart Designer",
        "Analytics Dashboard",
        "Meeting Scheduler",
    ]

    selected_module = st.sidebar.radio(
        "Select Module",
        available_modules,
        key="module_selector",
    )

    st.sidebar.divider()

    # Show coming soon modules
    with st.sidebar.expander("🔜 Coming Soon", expanded=False):
        for module in coming_soon:
            st.markdown(f"- {module}")

    st.sidebar.divider()

    # App info
    with st.sidebar.expander("ℹ️ About NEXUS", expanded=False):
        st.markdown(
            f"""
            **Version:** {settings.app_version}

            NEXUS is an AI-powered productivity platform that integrates
            24 essential tools for modern work.

            **Current Features:**
            - 📝 Word Editor with AI assistance
            - 🤖 Claude AI integration
            - 📊 Document statistics
            - 💾 Multiple export formats
            - 🕐 Version history
            - 💬 Comments and collaboration
            - 📋 Document templates

            **Powered by:**
            - Streamlit
            - Claude AI (Anthropic)
            - Python
            """
        )

    return selected_module


def render_api_key_setup() -> bool:
    """
    Render API key setup if not configured.

    Returns:
        True if API key is configured
    """
    if not settings.anthropic_api_key:
        st.warning("⚠️ Anthropic API Key not configured")

        with st.expander("🔑 Configure API Key", expanded=True):
            st.markdown(
                """
                To use AI features, you need to configure your Anthropic API key.

                **Steps:**
                1. Get your API key from [Anthropic Console](https://console.anthropic.com/)
                2. Create a `.env` file in the project root
                3. Add: `ANTHROPIC_API_KEY=your_key_here`
                4. Restart the application

                **Or** set it as an environment variable:
                ```bash
                export ANTHROPIC_API_KEY=your_key_here
                ```
                """
            )

            # Allow temporary key input
            temp_key = st.text_input(
                "Enter API key (temporary, for this session):",
                type="password",
                key="temp_api_key",
            )

            if st.button("Save for this session", key="save_temp_key"):
                if temp_key:
                    settings.anthropic_api_key = temp_key
                    st.success("✅ API key saved for this session!")
                    st.rerun()
                else:
                    st.error("Please enter a valid API key")

        return False

    return True


def render_module(module_name: str) -> None:
    """
    Render the selected module.

    Args:
        module_name: Name of the module to render
    """
    try:
        if module_name == "Word Editor":
            module = WordEditorModule()
            module.render()
        else:
            st.info(f"Module '{module_name}' is coming soon!")

    except Exception as e:
        st.error(f"Error loading module: {str(e)}")
        app_logger.error(f"Module loading error: {e}", exc_info=True)


def render_footer() -> None:
    """Render application footer."""
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; padding: 1rem;'>
            <p>NEXUS Platform v1.0.0 | Powered by Claude AI & Streamlit</p>
            <p>© 2024 NEXUS | Built with ❤️ for productivity</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Main application entry point."""
    # Initialize app
    initialize_app()

    # Render welcome banner
    render_welcome_banner()

    # Check API key configuration
    api_configured = render_api_key_setup()

    # Module selector
    selected_module = render_module_selector()

    # Update session state
    st.session_state.current_module = selected_module

    # Render selected module
    if api_configured or selected_module in ["Word Editor"]:  # Word Editor works without AI
        render_module(selected_module)
    else:
        st.info("Please configure your API key to use AI features.")

    # Footer
    render_footer()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        app_logger.critical(f"Critical application error: {e}", exc_info=True)
