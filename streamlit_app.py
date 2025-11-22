"""
Streamlit UI for NEXUS Platform.
"""
import streamlit as st

# Configure page
st.set_page_config(
    page_title="NEXUS Platform",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .success-message {
        color: #28a745;
        font-weight: bold;
    }
    .error-message {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("🚀 NEXUS Platform")
st.sidebar.markdown("---")

module = st.sidebar.radio(
    "Select Module",
    ["Dashboard", "Lead Generation", "Advertising", "Settings"]
)

# Main content
if module == "Dashboard":
    st.markdown('<p class="main-header">NEXUS Platform Dashboard</p>', unsafe_allow_html=True)

    # KPI metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Leads", "1,234", "+12%")

    with col2:
        st.metric("Active Campaigns", "8", "+2")

    with col3:
        st.metric("Ad Spend (MTD)", "$12,450", "-5%")

    with col4:
        st.metric("ROAS", "4.2x", "+0.3x")

    st.markdown("---")

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Lead Generation Trends")
        # Placeholder for chart
        st.info("Lead generation chart will be displayed here")

    with col2:
        st.subheader("Campaign Performance")
        # Placeholder for chart
        st.info("Campaign performance chart will be displayed here")

elif module == "Lead Generation":
    from ui.lead_generation_ui import render_lead_generation
    render_lead_generation()

elif module == "Advertising":
    from ui.advertising_ui import render_advertising
    render_advertising()

elif module == "Settings":
    st.markdown('<p class="main-header">Settings</p>', unsafe_allow_html=True)

    st.subheader("API Configuration")

    with st.expander("Lead Enrichment APIs"):
        clearbit_key = st.text_input("Clearbit API Key", type="password")
        hunter_key = st.text_input("Hunter API Key", type="password")

    with st.expander("Ad Platform APIs"):
        google_ads_token = st.text_input("Google Ads Developer Token", type="password")
        facebook_token = st.text_input("Facebook Access Token", type="password")
        linkedin_token = st.text_input("LinkedIn Access Token", type="password")

    with st.expander("AI/LLM Configuration"):
        anthropic_key = st.text_input("Anthropic API Key", type="password")
        openai_key = st.text_input("OpenAI API Key", type="password")

    if st.button("Save Settings"):
        st.success("Settings saved successfully!")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**NEXUS Platform v1.0.0**")
st.sidebar.markdown("Built with Streamlit & FastAPI")
