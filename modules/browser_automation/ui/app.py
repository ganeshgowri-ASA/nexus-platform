"""Streamlit UI for Browser Automation Module"""
import streamlit as st
import httpx
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

# Page config
st.set_page_config(
    page_title="NEXUS Browser Automation",
    page_icon="🤖",
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
        margin-bottom: 1rem;
    }
    .step-card {
        border: 1px solid #ddd;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 0.5rem;
        background-color: #f9f9f9;
    }
    .success-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    </style>
""", unsafe_allow_html=True)


async def api_request(method: str, endpoint: str, data: Dict = None) -> Dict:
    """Make API request"""
    url = f"{API_BASE_URL}{endpoint}"
    async with httpx.AsyncClient() as client:
        if method == "GET":
            response = await client.get(url)
        elif method == "POST":
            response = await client.post(url, json=data)
        elif method == "PUT":
            response = await client.put(url, json=data)
        elif method == "DELETE":
            response = await client.delete(url)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        return response.json()


def main():
    """Main application"""
    st.markdown('<div class="main-header">🤖 NEXUS Browser Automation</div>', unsafe_allow_html=True)

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["📋 Workflows", "➕ Create Workflow", "🔄 Executions", "📅 Schedules", "📊 Dashboard"]
    )

    if page == "📋 Workflows":
        show_workflows_page()
    elif page == "➕ Create Workflow":
        show_create_workflow_page()
    elif page == "🔄 Executions":
        show_executions_page()
    elif page == "📅 Schedules":
        show_schedules_page()
    elif page == "📊 Dashboard":
        show_dashboard_page()


def show_workflows_page():
    """Display workflows page"""
    st.header("📋 Workflows")

    # Fetch workflows
    try:
        import asyncio
        workflows = asyncio.run(api_request("GET", "/workflows"))

        if not workflows:
            st.info("No workflows found. Create your first workflow!")
            return

        # Display workflows
        for workflow in workflows:
            with st.expander(f"🔧 {workflow['name']} (ID: {workflow['id']})"):
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    st.write(f"**Description:** {workflow.get('description', 'N/A')}")
                    st.write(f"**Browser:** {workflow['browser_type']} ({'Headless' if workflow['headless'] else 'Headed'})")
                    st.write(f"**Status:** {'✅ Active' if workflow['is_active'] else '❌ Inactive'}")
                    st.write(f"**Steps:** {len(workflow.get('steps', []))}")

                with col2:
                    if st.button(f"▶️ Execute", key=f"exec_{workflow['id']}"):
                        with st.spinner("Executing workflow..."):
                            result = asyncio.run(api_request("POST", f"/workflows/{workflow['id']}/execute"))
                            if result.get('status') == 'completed':
                                st.success("Workflow executed successfully!")
                            else:
                                st.error(f"Execution failed: {result.get('error_message')}")

                with col3:
                    if st.button(f"🗑️ Delete", key=f"del_{workflow['id']}"):
                        asyncio.run(api_request("DELETE", f"/workflows/{workflow['id']}"))
                        st.success("Workflow deleted!")
                        st.rerun()

                # Show steps
                if workflow.get('steps'):
                    st.write("**Steps:**")
                    for step in sorted(workflow['steps'], key=lambda s: s['step_order']):
                        st.markdown(
                            f"<div class='step-card'>"
                            f"<strong>{step['step_order']}. {step['name']}</strong> "
                            f"({step['step_type']})<br>"
                            f"Selector: {step.get('selector', 'N/A')}"
                            f"</div>",
                            unsafe_allow_html=True
                        )

    except Exception as e:
        st.error(f"Error loading workflows: {e}")


def show_create_workflow_page():
    """Display create workflow page"""
    st.header("➕ Create New Workflow")

    with st.form("create_workflow_form"):
        # Basic info
        st.subheader("Basic Information")
        name = st.text_input("Workflow Name*", placeholder="My Web Scraping Workflow")
        description = st.text_area("Description", placeholder="Optional description")

        col1, col2, col3 = st.columns(3)
        with col1:
            browser_type = st.selectbox("Browser", ["chromium", "firefox", "webkit"])
        with col2:
            headless = st.checkbox("Headless Mode", value=True)
        with col3:
            timeout = st.number_input("Timeout (ms)", value=30000, step=1000)

        # Steps
        st.subheader("Workflow Steps")
        num_steps = st.number_input("Number of Steps", min_value=1, max_value=20, value=1)

        steps = []
        for i in range(num_steps):
            with st.expander(f"Step {i + 1}", expanded=True):
                step_col1, step_col2 = st.columns(2)

                with step_col1:
                    step_name = st.text_input(f"Step Name*", key=f"step_name_{i}")
                    step_type = st.selectbox(
                        "Step Type*",
                        ["navigate", "click", "type", "extract", "screenshot", "pdf", "wait", "scroll", "select"],
                        key=f"step_type_{i}"
                    )

                with step_col2:
                    selector = st.text_input(f"Selector", key=f"selector_{i}")
                    selector_type = st.selectbox(
                        "Selector Type",
                        ["css", "xpath", "id", "name"],
                        key=f"selector_type_{i}"
                    )

                value = st.text_input(f"Value", key=f"value_{i}")

                step_col3, step_col4 = st.columns(2)
                with step_col3:
                    wait_before = st.number_input(f"Wait Before (ms)", value=0, key=f"wait_before_{i}")
                with step_col4:
                    wait_after = st.number_input(f"Wait After (ms)", value=0, key=f"wait_after_{i}")

                steps.append({
                    "step_order": i,
                    "step_type": step_type,
                    "name": step_name,
                    "selector": selector if selector else None,
                    "selector_type": selector_type,
                    "value": value if value else None,
                    "wait_before": wait_before,
                    "wait_after": wait_after,
                    "error_handling": "stop",
                    "max_retries": 3
                })

        # Submit
        submitted = st.form_submit_button("Create Workflow", type="primary")

        if submitted:
            if not name:
                st.error("Workflow name is required!")
            elif not all(step['name'] for step in steps):
                st.error("All steps must have a name!")
            else:
                try:
                    import asyncio
                    workflow_data = {
                        "name": name,
                        "description": description,
                        "is_active": True,
                        "headless": headless,
                        "browser_type": browser_type,
                        "timeout": timeout,
                        "steps": steps
                    }

                    result = asyncio.run(api_request("POST", "/workflows", workflow_data))
                    st.success(f"✅ Workflow '{name}' created successfully!")
                    st.balloons()

                except Exception as e:
                    st.error(f"Error creating workflow: {e}")


def show_executions_page():
    """Display executions page"""
    st.header("🔄 Workflow Executions")

    try:
        import asyncio
        executions = asyncio.run(api_request("GET", "/executions"))

        if not executions:
            st.info("No executions found.")
            return

        # Create DataFrame
        df_data = []
        for ex in executions:
            df_data.append({
                "ID": ex['id'],
                "Workflow": ex['workflow_id'],
                "Status": ex['status'],
                "Started": ex.get('started_at', 'N/A'),
                "Duration (s)": ex.get('duration_seconds', 'N/A'),
                "Triggered By": ex['triggered_by']
            })

        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)

        # Detailed view
        st.subheader("Execution Details")
        selected_id = st.selectbox("Select Execution", [ex['id'] for ex in executions])

        if selected_id:
            execution = next(ex for ex in executions if ex['id'] == selected_id)

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Status", execution['status'].upper())
                st.metric("Duration", f"{execution.get('duration_seconds', 0)}s")

            with col2:
                st.metric("Workflow ID", execution['workflow_id'])
                st.metric("Triggered By", execution['triggered_by'])

            # Results
            if execution.get('result_data'):
                st.subheader("Extracted Data")
                st.json(execution['result_data'])

            if execution.get('screenshots'):
                st.subheader("Screenshots")
                st.write(execution['screenshots'])

            if execution.get('error_message'):
                st.error(f"Error: {execution['error_message']}")

    except Exception as e:
        st.error(f"Error loading executions: {e}")


def show_schedules_page():
    """Display schedules page"""
    st.header("📅 Workflow Schedules")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Existing Schedules")
        try:
            import asyncio
            schedules = asyncio.run(api_request("GET", "/schedules"))

            if schedules:
                for schedule in schedules:
                    with st.expander(f"⏰ {schedule['name']}"):
                        st.write(f"**Workflow ID:** {schedule['workflow_id']}")
                        st.write(f"**Cron:** {schedule['cron_expression']}")
                        st.write(f"**Status:** {'✅ Active' if schedule['is_active'] else '❌ Inactive'}")
                        st.write(f"**Run Count:** {schedule['run_count']}")
                        st.write(f"**Last Run:** {schedule.get('last_run_at', 'Never')}")

                        if st.button(f"Toggle", key=f"toggle_{schedule['id']}"):
                            asyncio.run(api_request("POST", f"/schedules/{schedule['id']}/toggle"))
                            st.rerun()
            else:
                st.info("No schedules found.")

        except Exception as e:
            st.error(f"Error loading schedules: {e}")

    with col2:
        st.subheader("Create Schedule")
        with st.form("create_schedule_form"):
            import asyncio
            workflows = asyncio.run(api_request("GET", "/workflows"))
            workflow_options = {w['id']: w['name'] for w in workflows}

            workflow_id = st.selectbox("Workflow", options=list(workflow_options.keys()),
                                        format_func=lambda x: workflow_options[x])
            schedule_name = st.text_input("Schedule Name")
            cron_expr = st.text_input("Cron Expression", value="0 0 * * *",
                                       help="Example: 0 0 * * * (daily at midnight)")

            submitted = st.form_submit_button("Create Schedule")

            if submitted and schedule_name and workflow_id:
                try:
                    schedule_data = {
                        "workflow_id": workflow_id,
                        "name": schedule_name,
                        "cron_expression": cron_expr,
                        "is_active": True
                    }
                    asyncio.run(api_request("POST", "/schedules", schedule_data))
                    st.success("Schedule created!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")


def show_dashboard_page():
    """Display dashboard page"""
    st.header("📊 Dashboard")

    try:
        import asyncio

        # Get stats
        stats = asyncio.run(api_request("GET", "/executions/stats/summary"))

        # Metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Executions", stats['total_executions'])

        with col2:
            completed = stats['by_status'].get('completed', 0)
            st.metric("Completed", completed)

        with col3:
            failed = stats['by_status'].get('failed', 0)
            st.metric("Failed", failed)

        with col4:
            st.metric("Avg Duration", f"{stats['average_duration_seconds']:.1f}s")

        # Charts
        st.subheader("Execution Status Distribution")
        if stats['by_status']:
            chart_data = pd.DataFrame(
                list(stats['by_status'].items()),
                columns=['Status', 'Count']
            )
            st.bar_chart(chart_data.set_index('Status'))

    except Exception as e:
        st.error(f"Error loading dashboard: {e}")


if __name__ == "__main__":
    main()
