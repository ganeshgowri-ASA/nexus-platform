"""Streamlit UI for Integration Hub module."""
import streamlit as st
import os

# Configuration
API_URL = os.getenv("INTEGRATION_API_URL", "http://localhost:8002")

st.set_page_config(page_title="NEXUS Integration Hub", page_icon="🔌", layout="wide")

# Main UI
st.title("🔌 NEXUS Integration Hub")

st.markdown("""
## Welcome to the Integration Hub

The Integration Hub provides comprehensive tools for managing third-party integrations:

### Features:
- **🔐 OAuth 2.0 Flows**: Secure authentication with popular services
- **🔑 API Key Management**: Encrypted storage and rotation of API keys
- **🪝 Webhook Handling**: Configure and manage webhooks
- **🔄 Data Synchronization**: Bi-directional data sync with rate limiting
- **🛍️ Integration Marketplace**: Pre-built connectors for popular services

### Supported Integrations:
- GitHub
- Google Workspace (Drive, Sheets, Calendar)
- Slack
- Microsoft 365
- Salesforce
- And many more...

### Getting Started:
1. Browse available integrations in the marketplace
2. Configure your authentication (OAuth or API Key)
3. Set up data sync or webhooks
4. Monitor integration health and usage

### API Documentation:
Access the full API documentation at: [API Docs]({API_URL}/docs)
""")

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Overview", "Integrations", "API Keys", "OAuth Connections", "Webhooks", "Sync Configs"])

if page == "Overview":
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Active Integrations", "0")

    with col2:
        st.metric("API Keys", "0")

    with col3:
        st.metric("Webhooks", "0")

elif page == "Integrations":
    st.subheader("Available Integrations")
    st.info("Integration marketplace coming soon! This will include pre-built connectors for GitHub, Slack, Google, and more.")

elif page == "API Keys":
    st.subheader("API Key Management")
    st.info("Manage your API keys securely with encryption and rotation capabilities.")

elif page == "OAuth Connections":
    st.subheader("OAuth 2.0 Connections")
    st.info("Configure OAuth connections with automatic token refresh.")

elif page == "Webhooks":
    st.subheader("Webhook Configuration")
    st.info("Set up and manage webhooks with retry logic and signature verification.")

elif page == "Sync Configs":
    st.subheader("Data Synchronization")
    st.info("Configure bi-directional data sync with field mapping and transformations.")

st.sidebar.markdown("---")
st.sidebar.info("🔌 NEXUS Integration Hub v0.1.0")
