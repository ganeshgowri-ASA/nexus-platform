"""
Streamlit UI for NEXUS Marketing Automation Platform.

This is the main entry point for the Streamlit user interface.
"""
import streamlit as st
import requests
from datetime import datetime
from typing import Dict, Any

# Page configuration
st.set_page_config(
    page_title="NEXUS Marketing Automation",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1/marketing"

# Sidebar navigation
st.sidebar.title("NEXUS Marketing Automation")
page = st.sidebar.selectbox(
    "Navigate",
    ["Dashboard", "Campaigns", "Contacts", "Automations", "Analytics"]
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #1f77b4;
    margin-bottom: 1rem;
}
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)


def show_dashboard():
    """Display dashboard page."""
    st.markdown('<h1 class="main-header">Marketing Dashboard</h1>', unsafe_allow_html=True)

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Campaigns", "24", "+3")

    with col2:
        st.metric("Active Contacts", "1,234", "+56")

    with col3:
        st.metric("Open Rate", "28.5%", "+2.1%")

    with col4:
        st.metric("Click Rate", "12.3%", "+1.5%")

    st.markdown("---")

    # Recent campaigns
    st.subheader("📧 Recent Campaigns")

    campaigns_data = {
        "Campaign": ["Summer Sale 2024", "Product Launch", "Newsletter #42"],
        "Status": ["Completed", "Running", "Scheduled"],
        "Recipients": [1234, 856, 2100],
        "Open Rate": ["32.5%", "28.1%", "-"],
        "Created": ["2024-01-15", "2024-01-20", "2024-01-22"],
    }

    st.dataframe(campaigns_data, use_container_width=True)


def show_campaigns():
    """Display campaigns page."""
    st.markdown('<h1 class="main-header">📧 Email Campaigns</h1>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["All Campaigns", "Create Campaign"])

    with tab1:
        st.subheader("Campaign List")

        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox("Status", ["All", "Draft", "Running", "Completed"])
        with col2:
            sort_by = st.selectbox("Sort by", ["Created Date", "Name", "Status"])
        with col3:
            st.write("")  # Spacer

        # Mock campaigns list
        st.info("Connect to API to load campaigns")

    with tab2:
        st.subheader("Create New Campaign")

        with st.form("create_campaign_form"):
            campaign_name = st.text_input("Campaign Name*", placeholder="Summer Sale 2024")
            campaign_desc = st.text_area("Description", placeholder="Campaign description...")

            col1, col2 = st.columns(2)

            with col1:
                campaign_type = st.selectbox("Type", ["Email", "SMS", "Multi-Channel"])
                from_name = st.text_input("From Name", value="NEXUS Team")

            with col2:
                segment = st.selectbox("Target Segment", ["All Subscribers", "Engaged Users", "VIP Customers"])
                from_email = st.text_input("From Email", value="noreply@nexus.com")

            subject_line = st.text_input("Subject Line*", placeholder="Don't miss our summer sale!")

            # AI Content Generation
            st.subheader("✨ AI-Powered Content Generation")

            col1, col2 = st.columns(2)
            with col1:
                campaign_goal = st.text_input("Campaign Goal", placeholder="Drive summer sales")
            with col2:
                tone = st.selectbox("Tone", ["Professional", "Casual", "Friendly", "Urgent"])

            if st.button("🤖 Generate Content with AI"):
                with st.spinner("Generating AI content..."):
                    st.success("AI content generated! Review below.")

            email_content = st.text_area(
                "Email Content (HTML)*",
                height=300,
                placeholder="<h1>Hello {{first_name}}</h1>\n<p>Your content here...</p>"
            )

            scheduled_send = st.checkbox("Schedule for later")
            if scheduled_send:
                schedule_date = st.date_input("Schedule Date")
                schedule_time = st.time_input("Schedule Time")

            submitted = st.form_submit_button("Create Campaign", type="primary")

            if submitted:
                if campaign_name and email_content:
                    st.success(f"Campaign '{campaign_name}' created successfully!")
                else:
                    st.error("Please fill in all required fields")


def show_contacts():
    """Display contacts page."""
    st.markdown('<h1 class="main-header">👥 Contact Management</h1>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Contacts", "Segments", "Import"])

    with tab1:
        st.subheader("Contact List")

        # Search and filter
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            search = st.text_input("🔍 Search contacts", placeholder="Search by email, name...")
        with col2:
            status_filter = st.selectbox("Status", ["All", "Subscribed", "Unsubscribed"])
        with col3:
            score_filter = st.selectbox("Lead Score", ["All", "Cold", "Warm", "Hot"])

        st.info("Connect to API to load contacts")

    with tab2:
        st.subheader("Audience Segments")

        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("Dynamic audience segmentation for targeted campaigns")
        with col2:
            if st.button("Create Segment", type="primary"):
                st.info("Segment creation form would appear here")

        # Mock segments
        segments = {
            "Segment Name": ["Engaged Users", "VIP Customers", "Inactive Users"],
            "Contact Count": [456, 89, 234],
            "Created": ["2024-01-10", "2024-01-15", "2024-01-18"],
        }
        st.dataframe(segments, use_container_width=True)

    with tab3:
        st.subheader("Import Contacts")

        uploaded_file = st.file_uploader("Upload CSV file", type=["csv", "xlsx"])

        if uploaded_file:
            st.success("File uploaded successfully!")
            st.info("Preview and map fields before importing")


def show_automations():
    """Display automations page."""
    st.markdown('<h1 class="main-header">⚙️ Marketing Automation</h1>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Workflows", "Drip Campaigns"])

    with tab1:
        st.subheader("Automation Workflows")

        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("Build powerful automation workflows with visual editor")
        with col2:
            if st.button("Create Workflow", type="primary"):
                st.info("Workflow builder would appear here")

        # Mock workflows
        workflows = {
            "Workflow": ["Welcome Series", "Abandoned Cart", "Re-engagement"],
            "Status": ["Active", "Active", "Paused"],
            "Trigger": ["Contact Subscribed", "Cart Abandoned", "30 Days Inactive"],
            "Executions": [234, 45, 12],
        }
        st.dataframe(workflows, use_container_width=True)

    with tab2:
        st.subheader("Drip Campaigns")

        st.write("Create multi-step nurture campaigns that guide leads through your funnel")

        if st.button("Create Drip Campaign", type="primary"):
            st.info("Drip campaign builder would appear here")


def show_analytics():
    """Display analytics page."""
    st.markdown('<h1 class="main-header">📊 Analytics & Reports</h1>', unsafe_allow_html=True)

    # Date range selector
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        start_date = st.date_input("From")
    with col2:
        end_date = st.date_input("To")
    with col3:
        st.write("")  # Spacer

    st.markdown("---")

    # Key metrics
    st.subheader("📈 Performance Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Sent", "12,345", "+1,234")
    with col2:
        st.metric("Open Rate", "28.5%", "+2.1%")
    with col3:
        st.metric("Click Rate", "12.3%", "+1.5%")
    with col4:
        st.metric("Conversions", "456", "+23")

    st.markdown("---")

    # Charts
    st.subheader("Campaign Performance Over Time")
    st.line_chart({"Opens": [100, 120, 140, 160, 180], "Clicks": [30, 35, 42, 48, 54]})

    st.subheader("Top Performing Campaigns")
    st.bar_chart({"Campaign A": 85, "Campaign B": 72, "Campaign C": 68})


# Page routing
if page == "Dashboard":
    show_dashboard()
elif page == "Campaigns":
    show_campaigns()
elif page == "Contacts":
    show_contacts()
elif page == "Automations":
    show_automations()
elif page == "Analytics":
    show_analytics()

# Footer
st.sidebar.markdown("---")
st.sidebar.info("""
**NEXUS Marketing Automation**
Version 0.1.0
AI-powered marketing platform
""")
