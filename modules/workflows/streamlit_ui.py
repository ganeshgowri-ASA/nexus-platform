"""
NEXUS Workflow Automation - Streamlit UI
Visual workflow builder with drag-drop interface
"""

import streamlit as st
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid

# Import workflow modules
from .engine import workflow_engine, NodeType, ExecutionStatus
from .triggers import trigger_manager, TriggerType
from .actions import action_executor, ActionType
from .scheduler import workflow_scheduler, ScheduleType
from .integrations import integration_registry, IntegrationCategory
from .templates import template_library, TemplateCategory
from .monitoring import workflow_monitor


def init_session_state():
    """Initialize Streamlit session state"""
    if 'current_workflow' not in st.session_state:
        st.session_state.current_workflow = None
    if 'selected_node' not in st.session_state:
        st.session_state.selected_node = None
    if 'workflow_nodes' not in st.session_state:
        st.session_state.workflow_nodes = []
    if 'workflow_connections' not in st.session_state:
        st.session_state.workflow_connections = []


def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="NEXUS Workflow Automation",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    init_session_state()

    # Sidebar navigation
    st.sidebar.title("⚡ NEXUS Workflows")
    st.sidebar.markdown("---")

    page = st.sidebar.radio(
        "Navigate",
        [
            "🏠 Dashboard",
            "🎨 Workflow Builder",
            "📋 Templates",
            "🔗 Integrations",
            "📅 Scheduler",
            "📊 Monitoring",
            "⚙️ Settings"
        ]
    )

    # Page routing
    if "Dashboard" in page:
        show_dashboard()
    elif "Workflow Builder" in page:
        show_workflow_builder()
    elif "Templates" in page:
        show_templates()
    elif "Integrations" in page:
        show_integrations()
    elif "Scheduler" in page:
        show_scheduler()
    elif "Monitoring" in page:
        show_monitoring()
    elif "Settings" in page:
        show_settings()


def show_dashboard():
    """Show main dashboard"""
    st.title("🏠 Workflow Dashboard")

    # Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Workflows",
            len(workflow_engine.workflows),
            delta=None
        )

    with col2:
        active_workflows = len([w for w in workflow_engine.workflows.values() if w.is_active])
        st.metric("Active Workflows", active_workflows)

    with col3:
        st.metric("Total Executions", len(workflow_engine.executions))

    with col4:
        successful = len([e for e in workflow_engine.executions.values() if e.status == ExecutionStatus.SUCCESS])
        st.metric("Successful Executions", successful)

    st.markdown("---")

    # Recent executions
    st.subheader("📊 Recent Executions")
    executions = workflow_engine.list_executions(limit=10)

    if executions:
        for execution in executions:
            with st.expander(f"Execution {execution.id[:8]} - {execution.status.value}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Workflow ID:** {execution.workflow_id}")
                    st.write(f"**Status:** {execution.status.value}")
                    st.write(f"**Started:** {execution.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
                with col2:
                    if execution.duration_ms:
                        st.write(f"**Duration:** {execution.duration_ms:.2f}ms")
                    if execution.error:
                        st.error(f"**Error:** {execution.error}")
    else:
        st.info("No executions yet. Create a workflow and run it!")

    # Quick actions
    st.markdown("---")
    st.subheader("🚀 Quick Actions")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("➕ Create New Workflow", use_container_width=True):
            st.session_state.current_workflow = None
            st.session_state.workflow_nodes = []
            st.session_state.workflow_connections = []
            st.rerun()

    with col2:
        if st.button("📋 Browse Templates", use_container_width=True):
            st.session_state.page = "templates"
            st.rerun()

    with col3:
        if st.button("🔗 Connect Integration", use_container_width=True):
            st.session_state.page = "integrations"
            st.rerun()


def show_workflow_builder():
    """Show visual workflow builder"""
    st.title("🎨 Workflow Builder")

    # Workflow selector
    col1, col2 = st.columns([3, 1])
    with col1:
        workflows = list(workflow_engine.workflows.values())
        workflow_options = ["<Create New>"] + [f"{w.name} ({w.id[:8]})" for w in workflows]
        selected = st.selectbox("Select Workflow", workflow_options)

    with col2:
        if st.button("💾 Save Workflow", use_container_width=True):
            save_workflow()

    st.markdown("---")

    # Two columns: Node Library and Canvas
    col1, col2 = st.columns([1, 3])

    with col1:
        st.subheader("📚 Node Library")
        show_node_library()

    with col2:
        st.subheader("🎨 Workflow Canvas")
        show_workflow_canvas()


def show_node_library():
    """Show library of available nodes"""
    node_categories = {
        "🎯 Triggers": [
            ("Webhook", TriggerType.WEBHOOK),
            ("Schedule", TriggerType.SCHEDULE),
            ("Email", TriggerType.EMAIL),
            ("Form Submission", TriggerType.FORM_SUBMISSION),
            ("Database Change", TriggerType.DATABASE_CHANGE),
            ("API Call", TriggerType.API_CALL),
        ],
        "⚡ Actions": [
            ("Send Email", ActionType.SEND_EMAIL),
            ("API Request", ActionType.API_REQUEST),
            ("Database Query", ActionType.DATABASE_QUERY),
            ("Send Notification", ActionType.SEND_NOTIFICATION),
            ("Execute Script", ActionType.EXECUTE_SCRIPT),
            ("Transform Data", ActionType.TRANSFORM_DATA),
        ],
        "🔀 Logic": [
            ("Condition", "condition"),
            ("Loop", "loop"),
            ("Delay", "delay"),
        ]
    }

    for category, nodes in node_categories.items():
        with st.expander(category, expanded=True):
            for node_name, node_type in nodes:
                if st.button(f"➕ {node_name}", key=f"add_{node_name}", use_container_width=True):
                    add_node_to_workflow(node_name, str(node_type))


def show_workflow_canvas():
    """Show workflow canvas with nodes and connections"""
    if not st.session_state.workflow_nodes:
        st.info("👈 Add nodes from the library to start building your workflow")
        return

    # Display nodes
    st.subheader("Nodes")
    for i, node in enumerate(st.session_state.workflow_nodes):
        with st.expander(f"{node['name']} - {node['type']}", expanded=True):
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                node['name'] = st.text_input(
                    "Node Name",
                    value=node['name'],
                    key=f"node_name_{i}"
                )

            with col2:
                if st.button("⚙️", key=f"config_{i}"):
                    st.session_state.selected_node = i

            with col3:
                if st.button("🗑️", key=f"delete_{i}"):
                    st.session_state.workflow_nodes.pop(i)
                    st.rerun()

            # Node configuration
            if st.session_state.selected_node == i:
                st.markdown("**Node Configuration**")
                configure_node(node)

    # Display connections
    st.markdown("---")
    st.subheader("Connections")

    if st.session_state.workflow_connections:
        for i, conn in enumerate(st.session_state.workflow_connections):
            col1, col2 = st.columns([4, 1])
            with col1:
                source = next((n['name'] for n in st.session_state.workflow_nodes if n['id'] == conn['source']), "Unknown")
                target = next((n['name'] for n in st.session_state.workflow_nodes if n['id'] == conn['target']), "Unknown")
                st.write(f"➡️ {source} → {target}")
            with col2:
                if st.button("🗑️", key=f"delete_conn_{i}"):
                    st.session_state.workflow_connections.pop(i)
                    st.rerun()
    else:
        st.info("No connections yet")

    # Add connection
    st.markdown("---")
    st.subheader("Add Connection")
    col1, col2, col3 = st.columns(3)

    node_names = [n['name'] for n in st.session_state.workflow_nodes]

    with col1:
        source = st.selectbox("From Node", node_names, key="conn_source")
    with col2:
        target = st.selectbox("To Node", node_names, key="conn_target")
    with col3:
        if st.button("➕ Add Connection"):
            source_id = next((n['id'] for n in st.session_state.workflow_nodes if n['name'] == source), None)
            target_id = next((n['id'] for n in st.session_state.workflow_nodes if n['name'] == target), None)

            if source_id and target_id:
                st.session_state.workflow_connections.append({
                    'id': str(uuid.uuid4()),
                    'source': source_id,
                    'target': target_id
                })
                st.rerun()


def configure_node(node: Dict[str, Any]):
    """Configure node settings"""
    node_type = node.get('type', '').lower()

    if 'webhook' in node_type:
        node['config']['path'] = st.text_input("Webhook Path", value=node['config'].get('path', '/webhook'))
        node['config']['method'] = st.selectbox("Method", ["POST", "GET", "PUT"], index=0)

    elif 'schedule' in node_type:
        schedule_type = st.radio("Schedule Type", ["Cron", "Interval"])
        if schedule_type == "Cron":
            node['config']['cron'] = st.text_input("Cron Expression", value=node['config'].get('cron', '0 9 * * *'))
            st.caption("Example: `0 9 * * *` = Daily at 9 AM")
        else:
            node['config']['interval'] = st.number_input("Interval (seconds)", value=node['config'].get('interval', 3600))

    elif 'email' in node_type:
        if node['type'] == 'trigger':
            node['config']['email'] = st.text_input("Email Address", value=node['config'].get('email', ''))
        else:
            node['config']['to'] = st.text_input("To", value=node['config'].get('to', ''))
            node['config']['subject'] = st.text_input("Subject", value=node['config'].get('subject', ''))
            node['config']['body'] = st.text_area("Body", value=node['config'].get('body', ''))

    elif 'api' in node_type or 'request' in node_type:
        node['config']['url'] = st.text_input("URL", value=node['config'].get('url', ''))
        node['config']['method'] = st.selectbox("Method", ["GET", "POST", "PUT", "DELETE"], index=0)


def add_node_to_workflow(node_name: str, node_type: str):
    """Add a node to the workflow"""
    node = {
        'id': str(uuid.uuid4()),
        'name': node_name,
        'type': node_type,
        'config': {},
        'position': {'x': 0, 'y': len(st.session_state.workflow_nodes) * 100}
    }
    st.session_state.workflow_nodes.append(node)
    st.rerun()


def save_workflow():
    """Save workflow"""
    if not st.session_state.workflow_nodes:
        st.error("Add at least one node to the workflow")
        return

    # Create workflow
    workflow = workflow_engine.create_workflow(
        name=f"Workflow {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        description="Created via workflow builder",
        nodes=[{
            'id': n['id'],
            'name': n['name'],
            'type': n['type'],
            'config': n.get('config', {}),
            'position': n.get('position', {'x': 0, 'y': 0})
        } for n in st.session_state.workflow_nodes],
        connections=[{
            'id': c['id'],
            'source_node_id': c['source'],
            'target_node_id': c['target']
        } for c in st.session_state.workflow_connections]
    )

    st.success(f"✅ Workflow saved! ID: {workflow.id}")


def show_templates():
    """Show workflow templates"""
    st.title("📋 Workflow Templates")

    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        category = st.selectbox(
            "Category",
            ["All"] + [c.value for c in TemplateCategory]
        )
    with col2:
        search = st.text_input("🔍 Search templates")
    with col3:
        show_featured = st.checkbox("Featured only", value=False)

    # Get templates
    if category != "All":
        templates = template_library.list_templates(
            category=TemplateCategory(category),
            search=search if search else None,
            featured_only=show_featured
        )
    else:
        templates = template_library.list_templates(
            search=search if search else None,
            featured_only=show_featured
        )

    st.markdown("---")

    # Display templates
    if templates:
        for template in templates:
            with st.expander(f"{template.icon} {template.name}"):
                st.write(f"**Description:** {template.description}")
                st.write(f"**Category:** {template.category.value}")
                st.write(f"**Required Integrations:** {', '.join(template.required_integrations)}")
                st.write(f"**Use Count:** {template.use_count}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Use Template", key=f"use_{template.id}"):
                        # Load template into workflow builder
                        workflow_def = template.workflow_definition
                        st.session_state.workflow_nodes = workflow_def.get('nodes', [])
                        st.session_state.workflow_connections = workflow_def.get('connections', [])
                        st.success("Template loaded into workflow builder!")

                with col2:
                    if st.button(f"View Details", key=f"view_{template.id}"):
                        st.json(template.workflow_definition)
    else:
        st.info("No templates found")


def show_integrations():
    """Show integrations"""
    st.title("🔗 Integrations")

    # Categories
    categories = list(IntegrationCategory)
    selected_category = st.selectbox(
        "Select Category",
        ["All"] + [c.value for c in categories]
    )

    # Get integrations
    if selected_category != "All":
        integrations = integration_registry.list_integrations(
            category=IntegrationCategory(selected_category)
        )
    else:
        integrations = integration_registry.list_integrations()

    st.markdown("---")

    # Display integrations in grid
    cols = st.columns(3)
    for i, integration in enumerate(integrations):
        with cols[i % 3]:
            with st.container():
                st.subheader(integration.name)
                st.write(f"**Category:** {integration.category.value}")
                st.write(f"**Actions:** {len(integration.actions)}")
                st.write(f"**Triggers:** {len(integration.triggers)}")

                if st.button(f"Connect", key=f"connect_{integration.id}"):
                    show_integration_setup(integration)


def show_integration_setup(integration):
    """Show integration setup dialog"""
    st.subheader(f"Setup {integration.name}")
    st.write(integration.description)

    with st.form(f"setup_{integration.id}"):
        st.text_input("Connection Name")
        st.text_input("API Key")

        if st.form_submit_button("Connect"):
            st.success("Integration connected!")


def show_scheduler():
    """Show scheduler"""
    st.title("📅 Scheduler")

    # Create new schedule
    with st.expander("➕ Create New Schedule", expanded=False):
        workflows = list(workflow_engine.workflows.values())
        if workflows:
            workflow = st.selectbox(
                "Select Workflow",
                [w.name for w in workflows]
            )

            schedule_type = st.radio(
                "Schedule Type",
                ["Cron", "Interval", "One-time"]
            )

            if schedule_type == "Cron":
                cron = st.text_input("Cron Expression", value="0 9 * * *")
                st.caption("Examples: `0 9 * * *` (daily at 9 AM), `*/15 * * * *` (every 15 min)")

            elif schedule_type == "Interval":
                interval = st.number_input("Interval (seconds)", value=3600)

            if st.button("Create Schedule"):
                st.success("Schedule created!")
        else:
            st.warning("Create a workflow first")

    st.markdown("---")

    # List schedules
    st.subheader("Active Schedules")
    schedules = workflow_scheduler.list_schedules()

    if schedules:
        for schedule in schedules:
            with st.expander(f"Schedule {schedule.id[:8]} - {schedule.status.value}"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write(f"**Workflow ID:** {schedule.workflow_id}")
                    st.write(f"**Type:** {schedule.schedule_type.value}")

                with col2:
                    if schedule.next_run:
                        st.write(f"**Next Run:** {schedule.next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                    st.write(f"**Run Count:** {schedule.run_count}")

                with col3:
                    if st.button("Pause", key=f"pause_{schedule.id}"):
                        workflow_scheduler.pause_schedule(schedule.id)
                        st.rerun()
    else:
        st.info("No schedules configured")


def show_monitoring():
    """Show monitoring dashboard"""
    st.title("📊 Monitoring & Logs")

    # Dashboard data
    dashboard_data = workflow_monitor.get_dashboard_data()

    # Metrics
    if dashboard_data.get('metrics'):
        st.subheader("📈 Metrics")
        for workflow_id, metrics in dashboard_data['metrics'].items():
            with st.expander(f"Workflow {workflow_id[:8]}"):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Executions", metrics.get('total_executions', 0))
                with col2:
                    st.metric("Successful", metrics.get('successful_executions', 0))
                with col3:
                    st.metric("Failed", metrics.get('failed_executions', 0))
                with col4:
                    st.metric("Avg Duration (ms)", f"{metrics.get('average_duration_ms', 0):.2f}")

    st.markdown("---")

    # Recent errors
    st.subheader("🚨 Recent Errors")
    errors = dashboard_data.get('recent_errors', [])
    if errors:
        for error in errors:
            with st.expander(f"{error['error_type']}: {error['error_message'][:50]}..."):
                st.write(f"**Workflow ID:** {error['workflow_id']}")
                st.write(f"**Timestamp:** {error['timestamp']}")
                st.write(f"**Error Message:** {error['error_message']}")
                st.write(f"**Resolved:** {'✅' if error['resolved'] else '❌'}")
    else:
        st.success("No recent errors!")

    st.markdown("---")

    # Recent logs
    st.subheader("📝 Recent Logs")
    logs = dashboard_data.get('recent_logs', [])
    if logs:
        for log in logs:
            level_emoji = {
                'debug': '🐛',
                'info': 'ℹ️',
                'warning': '⚠️',
                'error': '❌',
                'critical': '🔥'
            }
            emoji = level_emoji.get(log['level'], 'ℹ️')
            st.text(f"{emoji} [{log['timestamp']}] {log['message']}")
    else:
        st.info("No logs yet")


def show_settings():
    """Show settings"""
    st.title("⚙️ Settings")

    st.subheader("General Settings")
    st.text_input("Organization Name", value="NEXUS")
    st.text_input("Default Email", value="workflows@nexus.com")

    st.markdown("---")

    st.subheader("Notification Settings")
    st.checkbox("Email notifications", value=True)
    st.checkbox("Slack notifications", value=False)

    st.markdown("---")

    st.subheader("Security Settings")
    st.text_input("API Key", type="password")
    st.checkbox("Require authentication", value=True)

    if st.button("💾 Save Settings"):
        st.success("Settings saved!")


if __name__ == "__main__":
    main()
