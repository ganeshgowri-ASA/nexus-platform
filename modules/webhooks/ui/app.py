"""
Streamlit UI for Webhook Management
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json

# Configuration
API_BASE_URL = st.secrets.get("API_BASE_URL", "http://localhost:8000/api/v1")

st.set_page_config(
    page_title="NEXUS Webhooks",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    .success-box {
        padding: 10px;
        border-radius: 5px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 10px;
        border-radius: 5px;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)


def make_request(method, endpoint, **kwargs):
    """Make HTTP request to API"""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json() if response.text else None
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None


def main():
    st.title("🔗 NEXUS Webhooks Management")
    st.markdown("Manage webhook endpoints, event subscriptions, and monitor deliveries")

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Dashboard", "Webhooks", "Event Subscriptions", "Deliveries", "Trigger Event"]
    )

    if page == "Dashboard":
        show_dashboard()
    elif page == "Webhooks":
        show_webhooks()
    elif page == "Event Subscriptions":
        show_event_subscriptions()
    elif page == "Deliveries":
        show_deliveries()
    elif page == "Trigger Event":
        show_trigger_event()


def show_dashboard():
    """Dashboard page"""
    st.header("📊 Dashboard")

    # Fetch webhooks
    webhooks = make_request("GET", "/webhooks/")
    if webhooks:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Webhooks", len(webhooks))
        with col2:
            active_count = sum(1 for w in webhooks if w.get("is_active"))
            st.metric("Active Webhooks", active_count)
        with col3:
            inactive_count = len(webhooks) - active_count
            st.metric("Inactive Webhooks", inactive_count)

        st.markdown("---")

        # Show webhook stats
        st.subheader("Webhook Statistics")
        for webhook in webhooks[:5]:  # Show top 5
            with st.expander(f"📌 {webhook['name']}"):
                stats = make_request("GET", f"/webhooks/{webhook['id']}/stats?days=7")
                if stats:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Deliveries", stats.get("total_deliveries", 0))
                    with col2:
                        st.metric("Successful", stats.get("successful_deliveries", 0))
                    with col3:
                        st.metric("Failed", stats.get("failed_deliveries", 0))
                    with col4:
                        st.metric("Success Rate", f"{stats.get('success_rate', 0):.1f}%")


def show_webhooks():
    """Webhooks management page"""
    st.header("🔗 Webhooks")

    tab1, tab2 = st.tabs(["All Webhooks", "Create New"])

    with tab1:
        # Filters
        col1, col2 = st.columns([3, 1])
        with col2:
            filter_active = st.selectbox(
                "Filter by status",
                ["All", "Active", "Inactive"]
            )

        # Fetch webhooks
        params = {}
        if filter_active == "Active":
            params["is_active"] = "true"
        elif filter_active == "Inactive":
            params["is_active"] = "false"

        webhooks = make_request("GET", "/webhooks/", params=params)

        if webhooks:
            for webhook in webhooks:
                with st.expander(f"{'🟢' if webhook['is_active'] else '🔴'} {webhook['name']}"):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.write(f"**URL:** {webhook['url']}")
                        st.write(f"**Description:** {webhook.get('description', 'N/A')}")
                        st.write(f"**Created:** {webhook['created_at']}")

                        # Show subscribed events
                        events = webhook.get('events', [])
                        if events:
                            event_types = [e['event_type'] for e in events if e['is_active']]
                            st.write(f"**Subscribed Events:** {', '.join(event_types)}")

                    with col2:
                        st.write(f"**ID:** {webhook['id']}")
                        st.write(f"**Timeout:** {webhook['timeout']}s")
                        st.write(f"**Status:** {'Active' if webhook['is_active'] else 'Inactive'}")

                        # Actions
                        if st.button(f"View Stats", key=f"stats_{webhook['id']}"):
                            stats = make_request("GET", f"/webhooks/{webhook['id']}/stats")
                            if stats:
                                st.json(stats)

                        if st.button(f"Delete", key=f"delete_{webhook['id']}"):
                            if make_request("DELETE", f"/webhooks/{webhook['id']}"):
                                st.success("Webhook deleted!")
                                st.rerun()

    with tab2:
        st.subheader("Create New Webhook")

        with st.form("create_webhook"):
            name = st.text_input("Name*", placeholder="My Webhook")
            url = st.text_input("URL*", placeholder="https://example.com/webhook")
            description = st.text_area("Description", placeholder="Optional description")

            # Get available events
            available_events = make_request("GET", "/events/available")
            if available_events:
                event_types = st.multiselect(
                    "Subscribe to Events*",
                    options=available_events,
                    help="Select one or more event types"
                )

            col1, col2 = st.columns(2)
            with col1:
                timeout = st.number_input("Timeout (seconds)", min_value=1, max_value=300, value=30)
            with col2:
                is_active = st.checkbox("Active", value=True)

            submitted = st.form_submit_button("Create Webhook")

            if submitted:
                if not name or not url or not event_types:
                    st.error("Please fill in all required fields")
                else:
                    payload = {
                        "name": name,
                        "url": url,
                        "description": description,
                        "event_types": event_types,
                        "timeout": timeout,
                        "is_active": is_active
                    }
                    result = make_request("POST", "/webhooks/", json=payload)
                    if result:
                        st.success(f"✅ Webhook created successfully!")
                        st.json({"webhook_id": result["id"], "secret": result["secret"]})
                        st.info("⚠️ Save the secret key! You'll need it to verify webhook signatures.")


def show_event_subscriptions():
    """Event subscriptions page"""
    st.header("📋 Event Subscriptions")

    # Select webhook
    webhooks = make_request("GET", "/webhooks/")
    if not webhooks:
        st.warning("No webhooks found. Create a webhook first.")
        return

    webhook_options = {f"{w['name']} (ID: {w['id']})": w['id'] for w in webhooks}
    selected = st.selectbox("Select Webhook", options=list(webhook_options.keys()))

    if selected:
        webhook_id = webhook_options[selected]

        tab1, tab2 = st.tabs(["Current Subscriptions", "Add Subscription"])

        with tab1:
            events = make_request("GET", f"/webhooks/{webhook_id}/events")
            if events:
                df = pd.DataFrame(events)
                df['is_active'] = df['is_active'].map({True: '🟢 Active', False: '🔴 Inactive'})
                st.dataframe(df[['event_type', 'is_active', 'created_at']], use_container_width=True)

                # Remove subscription
                st.subheader("Remove Subscription")
                event_to_remove = st.selectbox(
                    "Select event to remove",
                    options=[e['event_type'] for e in events]
                )
                if st.button("Remove"):
                    if make_request("DELETE", f"/webhooks/{webhook_id}/events/{event_to_remove}"):
                        st.success("Subscription removed!")
                        st.rerun()
            else:
                st.info("No event subscriptions found.")

        with tab2:
            available_events = make_request("GET", "/events/available")
            if available_events:
                new_event = st.selectbox("Select Event Type", options=available_events)
                if st.button("Add Subscription"):
                    payload = {"event_type": new_event}
                    result = make_request("POST", f"/webhooks/{webhook_id}/events", json=payload)
                    if result:
                        st.success("Subscription added!")
                        st.rerun()


def show_deliveries():
    """Deliveries monitoring page"""
    st.header("📨 Webhook Deliveries")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        webhooks = make_request("GET", "/webhooks/")
        webhook_filter = st.selectbox(
            "Filter by Webhook",
            options=["All"] + [f"{w['name']} ({w['id']})" for w in (webhooks or [])]
        )
    with col2:
        status_filter = st.selectbox(
            "Filter by Status",
            options=["All", "pending", "sending", "success", "failed", "retrying"]
        )
    with col3:
        limit = st.number_input("Limit", min_value=10, max_value=500, value=50)

    # Fetch deliveries
    params = {"limit": limit}
    if webhook_filter != "All":
        webhook_id = int(webhook_filter.split("(")[-1].strip(")"))
        params["webhook_id"] = webhook_id
    if status_filter != "All":
        params["status"] = status_filter

    deliveries = make_request("GET", "/deliveries/", params=params)

    if deliveries:
        st.write(f"**Showing {len(deliveries)} deliveries**")

        for delivery in deliveries:
            status_emoji = {
                "success": "✅",
                "failed": "❌",
                "pending": "⏳",
                "sending": "📤",
                "retrying": "🔄"
            }.get(delivery['status'], "❓")

            with st.expander(f"{status_emoji} {delivery['event_type']} - {delivery['created_at']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Delivery ID:** {delivery['id']}")
                    st.write(f"**Webhook ID:** {delivery['webhook_id']}")
                    st.write(f"**Event Type:** {delivery['event_type']}")
                    st.write(f"**Status:** {delivery['status']}")
                with col2:
                    st.write(f"**Attempts:** {delivery['attempt_count']}/{delivery['max_attempts']}")
                    st.write(f"**Status Code:** {delivery.get('status_code', 'N/A')}")
                    st.write(f"**Created:** {delivery['created_at']}")
                    if delivery.get('completed_at'):
                        st.write(f"**Completed:** {delivery['completed_at']}")

                if delivery.get('error_message'):
                    st.error(f"Error: {delivery['error_message']}")

                # Show payload
                if st.button(f"View Details", key=f"view_{delivery['id']}"):
                    detail = make_request("GET", f"/deliveries/{delivery['id']}")
                    if detail:
                        st.json(detail.get('payload', {}))

                # Retry button
                if delivery['status'] in ['failed', 'retrying']:
                    if st.button(f"Retry Now", key=f"retry_{delivery['id']}"):
                        result = make_request("POST", f"/deliveries/{delivery['id']}/retry")
                        if result:
                            st.success("Delivery queued for retry!")
                            st.rerun()
    else:
        st.info("No deliveries found.")


def show_trigger_event():
    """Trigger event page"""
    st.header("🚀 Trigger Event")

    st.markdown("""
    Manually trigger an event to test your webhooks. All active webhooks
    subscribed to the event type will receive the payload.
    """)

    with st.form("trigger_event"):
        # Get available events
        available_events = make_request("GET", "/events/available")

        event_type = st.selectbox(
            "Event Type*",
            options=available_events or []
        )

        event_id = st.text_input(
            "Event ID (optional)",
            placeholder="unique-event-id-123"
        )

        st.subheader("Payload")
        payload_text = st.text_area(
            "JSON Payload*",
            value='{\n  "user_id": 123,\n  "action": "created",\n  "timestamp": "2025-01-01T00:00:00Z"\n}',
            height=200
        )

        submitted = st.form_submit_button("Trigger Event")

        if submitted:
            try:
                payload = json.loads(payload_text)
                request_data = {
                    "event_type": event_type,
                    "event_id": event_id or None,
                    "payload": payload
                }

                result = make_request("POST", "/events/trigger", json=request_data)
                if result:
                    st.success(f"✅ Event triggered successfully!")
                    st.json(result)

            except json.JSONDecodeError:
                st.error("Invalid JSON payload. Please check your syntax.")


if __name__ == "__main__":
    main()
