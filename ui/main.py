"""Main Streamlit application for NEXUS Platform."""

import streamlit as st
from streamlit_option_menu import option_menu


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="NEXUS Platform",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Sidebar navigation
    with st.sidebar:
        st.title("🚀 NEXUS Platform")
        st.markdown("---")

        selected = option_menu(
            "Main Menu",
            ["Home", "Batch Processing", "Settings"],
            icons=["house", "gear-wide-connected", "sliders"],
            menu_icon="cast",
            default_index=0
        )

        st.markdown("---")
        st.caption("Version 1.0.0")

    # Main content based on selection
    if selected == "Home":
        show_home()
    elif selected == "Batch Processing":
        st.info("Navigate to the Batch Processing page using the pages dropdown in the sidebar.")
    elif selected == "Settings":
        show_settings()


def show_home():
    """Display home page."""
    st.title("🚀 Welcome to NEXUS Platform")

    st.markdown("""
    ### 24 Integrated Modules for Complete Productivity

    NEXUS is a comprehensive platform that brings together all your productivity needs
    in one place, powered by Claude AI and modern web technologies.
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔧 Current Modules")
        st.markdown("""
        - ⚙️ **Batch Processing** - Large-scale data processing with job queuing
        - 📊 **Analytics** - Data visualization and insights
        - 📧 **Email** - Email management and automation
        - 💬 **Chat** - AI-powered conversations
        """)

    with col2:
        st.subheader("🚀 Getting Started")
        st.markdown("""
        1. Select a module from the sidebar
        2. Follow the on-screen instructions
        3. Leverage Claude AI for assistance
        4. Monitor your tasks and jobs
        """)

    st.markdown("---")

    # Quick stats
    st.subheader("📊 Platform Statistics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Active Modules", "24")
    with col2:
        st.metric("Total Jobs", "0")
    with col3:
        st.metric("Success Rate", "0%")
    with col4:
        st.metric("Uptime", "100%")


def show_settings():
    """Display settings page."""
    st.title("⚙️ Settings")

    st.subheader("Application Settings")

    with st.form("settings_form"):
        st.text_input("API Endpoint", value="http://localhost:8000")
        st.text_input("Claude API Key", type="password")

        st.subheader("Batch Processing Settings")
        st.slider("Default Chunk Size", 10, 1000, 100)
        st.slider("Default Parallel Workers", 1, 16, 4)
        st.slider("Default Max Retries", 0, 10, 3)

        submitted = st.form_submit_button("Save Settings")

        if submitted:
            st.success("Settings saved successfully!")


if __name__ == "__main__":
    main()
