"""
NEXUS Platform - Main Application Launcher

This is the main entry point for the NEXUS platform.
"""

import streamlit as st

# Configure the app
st.set_page_config(
    page_title="NEXUS Platform",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    """Main application entry point."""

    st.title("🚀 NEXUS Platform")
    st.markdown("**Unified AI-powered productivity platform**")
    st.markdown("---")

    st.header("Available Modules")

    # Module cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("📡 API Builder")
        st.write("Professional API development platform")
        st.write("Design, test, document, and deploy APIs")

        if st.button("Launch API Builder", key="api_builder", use_container_width=True):
            st.markdown("**Starting API Builder...**")
            st.code("streamlit run modules/api_builder/streamlit_ui.py", language="bash")

    with col2:
        st.subheader("📊 Coming Soon")
        st.write("Analytics Module")
        st.write("Data visualization and analysis")
        st.button("Coming Soon", key="analytics", disabled=True, use_container_width=True)

    with col3:
        st.subheader("📝 Coming Soon")
        st.write("Document Editor")
        st.write("Word processor and document management")
        st.button("Coming Soon", key="docs", disabled=True, use_container_width=True)

    st.markdown("---")

    # Quick Start
    st.header("Quick Start")

    tab1, tab2, tab3 = st.tabs(["🚀 Get Started", "📖 Documentation", "ℹ️ About"])

    with tab1:
        st.subheader("Getting Started with NEXUS")

        st.markdown("""
        ### 1. API Builder Module

        The API Builder is a comprehensive platform for designing and managing APIs:

        ```bash
        # Launch the API Builder UI
        streamlit run modules/api_builder/streamlit_ui.py
        ```

        **Features:**
        - Visual endpoint designer
        - Authentication (API Keys, JWT, OAuth2, Basic Auth)
        - Rate limiting and quota management
        - Auto-generated OpenAPI/Swagger documentation
        - Built-in testing framework
        - Mock server for development
        - API versioning with migration guides
        - Code generation for multiple languages

        ### 2. Using the Python API

        ```python
        from modules.api_builder import APIBuilder, HTTPMethod

        # Create API
        builder = APIBuilder()

        # Add endpoint
        endpoint = builder.create_endpoint(
            path="/api/users",
            method=HTTPMethod.GET,
            summary="Get all users"
        )

        # Generate documentation
        openapi_spec = builder.generate_openapi_spec()
        ```

        ### 3. Run Example

        ```bash
        python examples/api_builder_example.py
        ```
        """)

    with tab2:
        st.subheader("Documentation")

        st.markdown("""
        ### API Builder Documentation

        - **[Full Documentation](modules/api_builder/README.md)** - Complete guide to API Builder
        - **[Examples](examples/)** - Code examples and tutorials
        - **[API Reference](#)** - Detailed API documentation

        ### Key Concepts

        1. **Endpoints** - Define your API endpoints with paths, methods, and parameters
        2. **Authentication** - Secure your API with various auth schemes
        3. **Rate Limiting** - Control API usage with flexible rate limiting
        4. **Documentation** - Auto-generate OpenAPI specs and Markdown docs
        5. **Testing** - Built-in testing framework with assertions
        6. **Mocking** - Mock server for development and testing
        7. **Versioning** - Manage multiple API versions

        ### Quick Links

        - [OpenAPI Specification](https://swagger.io/specification/)
        - [REST API Best Practices](https://restfulapi.net/)
        """)

    with tab3:
        st.subheader("About NEXUS Platform")

        st.markdown("""
        **NEXUS** is a unified AI-powered productivity platform with integrated modules
        for API development, document editing, data analytics, and more.

        ### Current Modules

        - ✅ **API Builder** - Complete API development platform

        ### Planned Modules

        - 📊 Analytics & Dashboards
        - 📝 Document Editor (Word)
        - 📈 Spreadsheet Editor (Excel)
        - 📽️ Presentation Editor (PowerPoint)
        - 💬 Chat & Collaboration
        - 📧 Email Management
        - 📋 Project Management
        - 🎨 Flowchart Designer
        - 📅 Calendar & Scheduling
        - 🗂️ File Manager

        ### Technology Stack

        - **Frontend:** Streamlit
        - **Backend:** Python
        - **AI:** Claude AI
        - **Standards:** OpenAPI 3.0, REST, GraphQL

        ### Version

        - **Platform Version:** 1.0.0
        - **API Builder Version:** 1.0.0

        ### License

        Part of the NEXUS platform

        ---

        **Built with ❤️ by the NEXUS team**
        """)

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center'>
            <p>NEXUS Platform v1.0.0 | Built with Streamlit & Claude AI</p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
