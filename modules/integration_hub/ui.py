"""
Streamlit dashboard UI for Integration Hub.

Provides a user-friendly interface for managing integrations, connections,
sync jobs, and monitoring.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List
import plotly.graph_objects as go
import plotly.express as px

# This would integrate with actual NEXUS database session
# For now, using placeholder functions


def integration_hub_dashboard():
    """Main Integration Hub dashboard."""
    st.title("🔌 Integration Hub")
    st.markdown("Manage all your third-party integrations in one place")

    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Navigation",
        ["Dashboard", "Integrations", "Connections", "Sync Jobs", "Webhooks", "Field Mappings", "Monitoring"]
    )

    if page == "Dashboard":
        show_dashboard()
    elif page == "Integrations":
        show_integrations()
    elif page == "Connections":
        show_connections()
    elif page == "Sync Jobs":
        show_sync_jobs()
    elif page == "Webhooks":
        show_webhooks()
    elif page == "Field Mappings":
        show_field_mappings()
    elif page == "Monitoring":
        show_monitoring()


def show_dashboard():
    """Show main dashboard with metrics."""
    st.header("📊 Dashboard Overview")

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Active Connections", "12", "+2")

    with col2:
        st.metric("Total Syncs Today", "45", "+15")

    with col3:
        st.metric("Records Synced", "1.2K", "+340")

    with col4:
        st.metric("Success Rate", "98.5%", "+1.2%")

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Sync Activity (Last 7 Days)")
        # Sample data
        dates = pd.date_range(end=datetime.now(), periods=7).tolist()
        data = pd.DataFrame({
            'Date': dates,
            'Successful': [120, 135, 142, 128, 156, 148, 165],
            'Failed': [5, 3, 7, 4, 6, 5, 4]
        })
        fig = px.line(data, x='Date', y=['Successful', 'Failed'], title='Daily Sync Activity')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Connections by Category")
        # Sample data
        categories = pd.DataFrame({
            'Category': ['CRM', 'Communication', 'Storage', 'Payment', 'Marketing'],
            'Count': [3, 2, 2, 2, 3]
        })
        fig = px.pie(categories, values='Count', names='Category', title='Integration Categories')
        st.plotly_chart(fig, use_container_width=True)

    # Recent activity
    st.subheader("📋 Recent Activity")
    activity_data = pd.DataFrame({
        'Timestamp': pd.date_range(end=datetime.now(), periods=5, freq='H')[::-1],
        'Event': [
            'Salesforce sync completed',
            'Slack webhook delivered',
            'HubSpot connection created',
            'Gmail sync started',
            'Stripe payment synced'
        ],
        'Status': ['✅ Success', '✅ Success', '✅ Success', '⏳ Running', '✅ Success']
    })
    st.dataframe(activity_data, use_container_width=True)


def show_integrations():
    """Show available integrations."""
    st.header("🔌 Available Integrations")

    # Category filter
    category = st.selectbox(
        "Filter by Category",
        ["All", "CRM", "Communication", "Storage", "Payment", "Marketing", "Ecommerce"]
    )

    # Search
    search = st.text_input("🔍 Search integrations", "")

    # Sample integrations
    integrations = [
        {"name": "Salesforce", "category": "CRM", "status": "Active", "connections": 3},
        {"name": "HubSpot", "category": "Marketing", "status": "Active", "connections": 2},
        {"name": "Slack", "category": "Communication", "status": "Active", "connections": 1},
        {"name": "Gmail", "category": "Email", "status": "Active", "connections": 1},
        {"name": "Stripe", "category": "Payment", "status": "Active", "connections": 2},
        {"name": "Shopify", "category": "Ecommerce", "status": "Available", "connections": 0},
    ]

    # Display integrations as cards
    cols = st.columns(3)
    for idx, integration in enumerate(integrations):
        with cols[idx % 3]:
            with st.container():
                st.subheader(f"📦 {integration['name']}")
                st.write(f"**Category:** {integration['category']}")
                st.write(f"**Status:** {integration['status']}")
                st.write(f"**Connections:** {integration['connections']}")

                if integration['connections'] > 0:
                    st.button("Configure", key=f"config_{idx}")
                else:
                    st.button("Connect", key=f"connect_{idx}", type="primary")


def show_connections():
    """Show and manage connections."""
    st.header("🔗 Active Connections")

    # Add new connection button
    if st.button("➕ Add New Connection", type="primary"):
        st.info("Connection wizard would open here...")

    # Connections table
    connections_data = pd.DataFrame({
        'Name': ['Salesforce Production', 'HubSpot Marketing', 'Slack Workspace', 'Gmail Account'],
        'Integration': ['Salesforce', 'HubSpot', 'Slack', 'Gmail'],
        'Status': ['🟢 Active', '🟢 Active', '🟡 Warning', '🟢 Active'],
        'Last Sync': ['2 hours ago', '5 hours ago', '1 day ago', '30 minutes ago'],
        'Records': ['1,234', '567', '89', '2,345']
    })

    st.dataframe(connections_data, use_container_width=True)

    # Connection details
    st.subheader("Connection Details")
    selected = st.selectbox("Select connection", connections_data['Name'].tolist())

    col1, col2, col3 = st.columns(3)
    with col1:
        st.button("🧪 Test Connection")
    with col2:
        st.button("🔄 Sync Now")
    with col3:
        st.button("⚙️ Settings")


def show_sync_jobs():
    """Show synchronization jobs."""
    st.header("🔄 Sync Jobs")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Status", ["All", "Running", "Completed", "Failed"])
    with col2:
        connection_filter = st.selectbox("Connection", ["All", "Salesforce", "HubSpot", "Slack"])
    with col3:
        period_filter = st.selectbox("Period", ["Today", "Last 7 Days", "Last 30 Days"])

    # Create new sync job
    if st.button("➕ Create Sync Job", type="primary"):
        with st.expander("Create New Sync Job", expanded=True):
            st.selectbox("Connection", ["Salesforce Production", "HubSpot Marketing"])
            st.selectbox("Direction", ["Inbound", "Outbound", "Bidirectional"])
            st.text_input("Entity Type", "Contact")
            if st.button("Start Sync"):
                st.success("Sync job created and started!")

    # Jobs table
    jobs_data = pd.DataFrame({
        'ID': ['#1234', '#1233', '#1232', '#1231'],
        'Connection': ['Salesforce', 'HubSpot', 'Slack', 'Gmail'],
        'Direction': ['Inbound', 'Outbound', 'Inbound', 'Inbound'],
        'Status': ['✅ Completed', '⏳ Running', '✅ Completed', '❌ Failed'],
        'Progress': ['100%', '45%', '100%', '0%'],
        'Records': ['234/234', '120/267', '89/89', '0/156'],
        'Started': ['1 hour ago', '5 minutes ago', '3 hours ago', '2 hours ago']
    })

    st.dataframe(jobs_data, use_container_width=True)

    # Job details
    st.subheader("Job Progress")
    progress = st.progress(0.45)
    st.write("Processing: 120/267 records (45%)")


def show_webhooks():
    """Show webhooks configuration."""
    st.header("🪝 Webhooks")

    tab1, tab2 = st.tabs(["Outgoing", "Incoming"])

    with tab1:
        st.subheader("Outgoing Webhooks")

        if st.button("➕ Add Outgoing Webhook"):
            with st.expander("Create Outgoing Webhook", expanded=True):
                st.selectbox("Connection", ["Salesforce", "HubSpot"])
                st.text_input("Webhook URL", "https://example.com/webhook")
                st.multiselect("Events", ["sync.completed", "sync.failed", "record.created"])
                if st.button("Create Webhook"):
                    st.success("Webhook created!")

        webhooks = pd.DataFrame({
            'Name': ['Sync Notifications', 'Error Alerts'],
            'URL': ['https://example.com/sync', 'https://example.com/errors'],
            'Events': ['sync.completed', 'sync.failed'],
            'Status': ['🟢 Active', '🟢 Active'],
            'Deliveries': ['1,234', '23']
        })
        st.dataframe(webhooks, use_container_width=True)

    with tab2:
        st.subheader("Incoming Webhooks")
        st.info("Configure incoming webhooks from third-party services")

        incoming = pd.DataFrame({
            'Name': ['Salesforce Changes', 'Stripe Events'],
            'Connection': ['Salesforce', 'Stripe'],
            'Endpoint': ['/webhooks/salesforce/abc123', '/webhooks/stripe/def456'],
            'Status': ['🟢 Active', '🟢 Active'],
            'Last Received': ['5 minutes ago', '1 hour ago']
        })
        st.dataframe(incoming, use_container_width=True)


def show_field_mappings():
    """Show field mapping configuration."""
    st.header("🗺️ Field Mappings")

    if st.button("➕ Create Field Mapping"):
        with st.expander("Create Field Mapping", expanded=True):
            st.selectbox("Connection", ["Salesforce Production", "HubSpot Marketing"])
            st.selectbox("Entity Type", ["Contact", "Account", "Deal"])
            st.selectbox("Direction", ["Inbound", "Outbound", "Bidirectional"])

            st.subheader("Field Mappings")
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Source Field 1", "external_id")
            with col2:
                st.text_input("Target Field 1", "id")

            if st.button("Add Mapping Row"):
                st.info("New row added")

            if st.button("Save Mapping"):
                st.success("Field mapping saved!")

    # Existing mappings
    mappings = pd.DataFrame({
        'Name': ['Salesforce Contacts', 'HubSpot Deals', 'Slack Messages'],
        'Connection': ['Salesforce', 'HubSpot', 'Slack'],
        'Entity Type': ['Contact', 'Deal', 'Message'],
        'Direction': ['Bidirectional', 'Inbound', 'Outbound'],
        'Fields Mapped': ['12', '8', '5']
    })
    st.dataframe(mappings, use_container_width=True)


def show_monitoring():
    """Show monitoring and analytics."""
    st.header("📈 Monitoring & Analytics")

    # Time range selector
    time_range = st.selectbox("Time Range", ["Last Hour", "Last 24 Hours", "Last 7 Days", "Last 30 Days"])

    # System health
    st.subheader("System Health")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Uptime", "99.8%", "+0.2%")
    with col2:
        st.metric("Avg Response Time", "245ms", "-15ms")
    with col3:
        st.metric("Error Rate", "0.5%", "-0.2%")
    with col4:
        st.metric("Active Jobs", "3", "+1")

    # Performance charts
    st.subheader("Performance Metrics")

    col1, col2 = st.columns(2)

    with col1:
        # API calls chart
        dates = pd.date_range(end=datetime.now(), periods=24, freq='H').tolist()
        api_data = pd.DataFrame({
            'Time': dates,
            'API Calls': [120 + (i * 5) for i in range(24)]
        })
        fig = px.line(api_data, x='Time', y='API Calls', title='API Calls per Hour')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Success rate chart
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=98.5,
            title={'text': "Success Rate"},
            gauge={'axis': {'range': [None, 100]},
                   'bar': {'color': "green"},
                   'steps': [
                       {'range': [0, 50], 'color': "red"},
                       {'range': [50, 80], 'color': "yellow"},
                       {'range': [80, 100], 'color': "lightgreen"}
                   ]}
        ))
        st.plotly_chart(fig, use_container_width=True)

    # Error log
    st.subheader("Recent Errors")
    errors = pd.DataFrame({
        'Timestamp': pd.date_range(end=datetime.now(), periods=3, freq='H')[::-1],
        'Connection': ['Salesforce', 'HubSpot', 'Slack'],
        'Error': ['Rate limit exceeded', 'Invalid token', 'Connection timeout'],
        'Severity': ['⚠️ Warning', '❌ Error', '⚠️ Warning']
    })
    st.dataframe(errors, use_container_width=True)


# Run the dashboard
if __name__ == "__main__":
    st.set_page_config(
        page_title="Integration Hub",
        page_icon="🔌",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    integration_hub_dashboard()
