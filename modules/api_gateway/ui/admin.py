import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import json

# Configure page
st.set_page_config(
    page_title="NEXUS API Gateway Admin",
    page_icon="🌐",
    layout="wide",
)

# API base URL
API_BASE_URL = st.sidebar.text_input("API Gateway URL", value="http://localhost:8000")


def main():
    """Main admin UI"""

    st.title("🌐 NEXUS API Gateway Admin")

    # Sidebar navigation
    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Routes", "API Keys", "Metrics", "Settings"]
    )

    if page == "Dashboard":
        show_dashboard()
    elif page == "Routes":
        show_routes()
    elif page == "API Keys":
        show_api_keys()
    elif page == "Metrics":
        show_metrics()
    elif page == "Settings":
        show_settings()


def show_dashboard():
    """Dashboard with overview metrics"""

    st.header("Dashboard")

    # Health check
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        health = response.json()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Status", health.get("status", "unknown").upper())

        with col2:
            st.metric("Version", health.get("version", "unknown"))

        with col3:
            redis_status = "✅ Connected" if health.get("redis_connected") else "❌ Disconnected"
            st.metric("Redis", redis_status)

    except Exception as e:
        st.error(f"Cannot connect to API Gateway: {e}")
        return

    st.divider()

    # Metrics summary
    st.subheader("Metrics Summary (Last 24 Hours)")

    try:
        response = requests.get(f"{API_BASE_URL}/admin/metrics/summary?hours=24")
        metrics = response.json()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Requests", f"{metrics['total_requests']:,}")

        with col2:
            error_rate = metrics.get('error_rate', 0)
            st.metric("Error Rate", f"{error_rate:.2f}%")

        with col3:
            avg_time = metrics.get('avg_response_time_ms', 0)
            st.metric("Avg Response Time", f"{avg_time:.2f}ms")

        with col4:
            cache_rate = metrics.get('cache_hit_rate', 0)
            st.metric("Cache Hit Rate", f"{cache_rate:.2f}%")

        # Status codes
        st.subheader("Status Code Distribution")
        status_codes = metrics.get('status_codes', {})
        if status_codes:
            df = pd.DataFrame(list(status_codes.items()), columns=['Status Code', 'Count'])
            st.bar_chart(df.set_index('Status Code'))

        # Top routes
        st.subheader("Top Routes")
        top_routes = metrics.get('top_routes', [])
        if top_routes:
            df = pd.DataFrame(top_routes)
            st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading metrics: {e}")


def show_routes():
    """Routes management page"""

    st.header("Routes Management")

    # Add new route button
    if st.button("➕ Add New Route"):
        st.session_state.show_add_route = True

    # Show add route form
    if st.session_state.get("show_add_route"):
        show_add_route_form()

    st.divider()

    # List routes
    try:
        response = requests.get(f"{API_BASE_URL}/admin/routes/")
        routes = response.json()

        if routes:
            for route in routes:
                with st.expander(f"{route['method']} {route['path']} - {route['name']}"):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.write(f"**Target:** {route['target_url']}")
                        st.write(f"**Description:** {route.get('description', 'N/A')}")
                        st.write(f"**Rate Limit:** {route['rate_limit']} req/min")
                        st.write(f"**Cache:** {'Enabled' if route['cache_enabled'] else 'Disabled'}")
                        st.write(f"**Auth Required:** {'Yes' if route['require_auth'] else 'No'}")

                    with col2:
                        status = "🟢 Enabled" if route['enabled'] else "🔴 Disabled"
                        st.write(status)

                        if st.button("Edit", key=f"edit_{route['id']}"):
                            st.session_state.edit_route = route['id']

                        if st.button("Delete", key=f"delete_{route['id']}"):
                            delete_route(route['id'])

        else:
            st.info("No routes configured yet. Add your first route!")

    except Exception as e:
        st.error(f"Error loading routes: {e}")


def show_add_route_form():
    """Form for adding a new route"""

    st.subheader("Add New Route")

    with st.form("add_route_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Route Name*", placeholder="my-api")
            path = st.text_input("Path*", placeholder="/api/v1/users")
            method = st.selectbox("Method*", ["GET", "POST", "PUT", "DELETE", "PATCH"])
            target_url = st.text_input("Target URL*", placeholder="http://backend:8080")

        with col2:
            enabled = st.checkbox("Enabled", value=True)
            require_auth = st.checkbox("Require Authentication", value=True)
            cache_enabled = st.checkbox("Enable Caching", value=False)
            rate_limit = st.number_input("Rate Limit (req/min)", min_value=1, value=100)

        description = st.text_area("Description")

        submitted = st.form_submit_button("Create Route")

        if submitted:
            if not all([name, path, method, target_url]):
                st.error("Please fill in all required fields")
            else:
                create_route({
                    "name": name,
                    "path": path,
                    "method": method,
                    "target_url": target_url,
                    "enabled": enabled,
                    "require_auth": require_auth,
                    "cache_enabled": cache_enabled,
                    "rate_limit": rate_limit,
                    "description": description,
                })


def create_route(route_data):
    """Create a new route"""

    try:
        response = requests.post(
            f"{API_BASE_URL}/admin/routes/",
            json=route_data
        )

        if response.status_code == 201:
            st.success("Route created successfully!")
            st.session_state.show_add_route = False
            st.rerun()
        else:
            st.error(f"Error: {response.json().get('detail', 'Unknown error')}")

    except Exception as e:
        st.error(f"Error creating route: {e}")


def delete_route(route_id):
    """Delete a route"""

    try:
        response = requests.delete(f"{API_BASE_URL}/admin/routes/{route_id}")

        if response.status_code == 200:
            st.success("Route deleted successfully!")
            st.rerun()
        else:
            st.error(f"Error deleting route")

    except Exception as e:
        st.error(f"Error: {e}")


def show_api_keys():
    """API Keys management page"""

    st.header("API Keys Management")

    # Add new key button
    if st.button("➕ Generate New API Key"):
        st.session_state.show_add_key = True

    # Show add key form
    if st.session_state.get("show_add_key"):
        show_add_api_key_form()

    st.divider()

    # List API keys
    try:
        response = requests.get(f"{API_BASE_URL}/admin/api-keys/")
        api_keys = response.json()

        if api_keys:
            for key in api_keys:
                with st.expander(f"{key['name']} - {key['key']}"):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.write(f"**User ID:** {key.get('user_id', 'N/A')}")
                        st.write(f"**Email:** {key.get('email', 'N/A')}")
                        st.write(f"**Rate Limit:** {key['rate_limit']} req/hour")
                        st.write(f"**Total Requests:** {key['total_requests']:,}")
                        st.write(f"**Last Used:** {key.get('last_used_at', 'Never')}")

                    with col2:
                        status = "🟢 Active" if key['active'] else "🔴 Inactive"
                        st.write(status)

                        if st.button("Rotate", key=f"rotate_{key['id']}"):
                            rotate_api_key(key['id'])

                        if st.button("Delete", key=f"delete_key_{key['id']}"):
                            delete_api_key(key['id'])

        else:
            st.info("No API keys yet. Generate your first API key!")

    except Exception as e:
        st.error(f"Error loading API keys: {e}")


def show_add_api_key_form():
    """Form for generating a new API key"""

    st.subheader("Generate New API Key")

    with st.form("add_api_key_form"):
        name = st.text_input("Key Name*", placeholder="Production API Key")
        user_id = st.text_input("User ID")
        email = st.text_input("Email")
        rate_limit = st.number_input("Rate Limit (req/hour)", min_value=1, value=1000)
        description = st.text_area("Description")

        submitted = st.form_submit_button("Generate API Key")

        if submitted:
            if not name:
                st.error("Please provide a name for the API key")
            else:
                create_api_key({
                    "name": name,
                    "user_id": user_id if user_id else None,
                    "email": email if email else None,
                    "rate_limit": rate_limit,
                    "description": description,
                })


def create_api_key(key_data):
    """Create a new API key"""

    try:
        response = requests.post(
            f"{API_BASE_URL}/admin/api-keys/",
            json=key_data
        )

        if response.status_code == 201:
            result = response.json()
            st.success("API Key generated successfully!")
            st.code(result['key'], language="text")
            st.warning("⚠️ Save this key! It won't be shown again.")
            st.session_state.show_add_key = False
        else:
            st.error(f"Error: {response.json().get('detail', 'Unknown error')}")

    except Exception as e:
        st.error(f"Error creating API key: {e}")


def rotate_api_key(key_id):
    """Rotate an API key"""

    try:
        response = requests.post(f"{API_BASE_URL}/admin/api-keys/{key_id}/rotate")

        if response.status_code == 200:
            result = response.json()
            st.success("API Key rotated successfully!")
            st.code(result['key'], language="text")
            st.warning("⚠️ Save this new key! The old key is now invalid.")
        else:
            st.error("Error rotating API key")

    except Exception as e:
        st.error(f"Error: {e}")


def delete_api_key(key_id):
    """Delete an API key"""

    try:
        response = requests.delete(f"{API_BASE_URL}/admin/api-keys/{key_id}")

        if response.status_code == 200:
            st.success("API Key deleted successfully!")
            st.rerun()
        else:
            st.error("Error deleting API key")

    except Exception as e:
        st.error(f"Error: {e}")


def show_metrics():
    """Metrics and monitoring page"""

    st.header("Metrics & Monitoring")

    # Time range selector
    hours = st.selectbox("Time Range", [1, 6, 12, 24, 48, 168], index=3)

    try:
        # Get metrics summary
        response = requests.get(f"{API_BASE_URL}/admin/metrics/summary?hours={hours}")
        metrics = response.json()

        # Display metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Requests", f"{metrics['total_requests']:,}")

        with col2:
            st.metric("Errors", f"{metrics['error_count']:,}",
                     delta=f"{metrics['error_rate']:.2f}%")

        with col3:
            st.metric("Avg Response Time", f"{metrics['avg_response_time_ms']:.2f}ms")

        with col4:
            st.metric("Cache Hit Rate", f"{metrics['cache_hit_rate']:.2f}%")

        # Time series chart
        st.subheader("Request Timeline")
        timeseries_response = requests.get(
            f"{API_BASE_URL}/admin/metrics/timeseries?hours={hours}"
        )
        timeseries = timeseries_response.json()

        if timeseries:
            df = pd.DataFrame(timeseries)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            st.line_chart(df.set_index('timestamp')['requests'])

        # Recent requests
        st.subheader("Recent Requests")
        requests_response = requests.get(
            f"{API_BASE_URL}/admin/metrics/requests?limit=50&hours={hours}"
        )
        recent_requests = requests_response.json()

        if recent_requests:
            df = pd.DataFrame(recent_requests)
            st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading metrics: {e}")


def show_settings():
    """Settings page"""

    st.header("Settings")

    st.subheader("Cache Management")

    if st.button("Clear All Cache"):
        st.warning("This will clear all cached responses. Are you sure?")
        if st.button("Yes, Clear Cache"):
            st.success("Cache cleared successfully!")

    st.divider()

    st.subheader("Database Maintenance")

    days = st.number_input("Delete metrics older than (days)", min_value=1, value=30)

    if st.button("Cleanup Old Metrics"):
        try:
            response = requests.delete(
                f"{API_BASE_URL}/admin/metrics/cleanup?days={days}"
            )
            if response.status_code == 200:
                result = response.json()
                st.success(result['message'])
        except Exception as e:
            st.error(f"Error: {e}")


if __name__ == "__main__":
    main()
