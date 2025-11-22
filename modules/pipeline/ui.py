"""Streamlit UI for Pipeline module."""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import json

from config.database import get_db_context
from .services import PipelineService
from .models import PipelineStatus, ExecutionStatus
from .connectors import ConnectorFactory
from .transformations import TransformationFactory


class PipelineUI:
    """Streamlit UI for Pipeline module."""

    @staticmethod
    def render():
        """Main UI rendering method."""
        st.set_page_config(
            page_title="NEXUS Pipeline Builder",
            page_icon="⚙️",
            layout="wide"
        )

        st.title("⚙️ NEXUS Pipeline Builder")
        st.markdown("Visual pipeline builder for data workflows, ETL, and stream processing")

        # Sidebar navigation
        with st.sidebar:
            st.header("Navigation")
            page = st.radio(
                "Select Page",
                [
                    "📊 Dashboard",
                    "➕ Create Pipeline",
                    "📋 Pipeline List",
                    "🔌 Connectors",
                    "▶️ Executions",
                    "📅 Schedules",
                    "📈 Monitoring"
                ]
            )

        # Route to appropriate page
        if page == "📊 Dashboard":
            PipelineUI.render_dashboard()
        elif page == "➕ Create Pipeline":
            PipelineUI.render_create_pipeline()
        elif page == "📋 Pipeline List":
            PipelineUI.render_pipeline_list()
        elif page == "🔌 Connectors":
            PipelineUI.render_connectors()
        elif page == "▶️ Executions":
            PipelineUI.render_executions()
        elif page == "📅 Schedules":
            PipelineUI.render_schedules()
        elif page == "📈 Monitoring":
            PipelineUI.render_monitoring()

    @staticmethod
    def render_dashboard():
        """Render dashboard page."""
        st.header("📊 Dashboard")

        with get_db_context() as db:
            service = PipelineService(db)

            # Get statistics
            pipelines = service.list_pipelines()
            executions = service.list_executions(limit=100)

            # Display metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Pipelines", len(pipelines))

            with col2:
                active_pipelines = len([p for p in pipelines if p.status == PipelineStatus.ACTIVE])
                st.metric("Active Pipelines", active_pipelines)

            with col3:
                successful = len([e for e in executions if e.status == ExecutionStatus.SUCCESS])
                st.metric("Successful Executions", successful)

            with col4:
                failed = len([e for e in executions if e.status == ExecutionStatus.FAILED])
                st.metric("Failed Executions", failed)

            # Recent executions
            st.subheader("Recent Executions")

            if executions:
                exec_data = []
                for e in executions[:10]:
                    pipeline = service.get_pipeline(e.pipeline_id)
                    exec_data.append({
                        "Pipeline": pipeline.name if pipeline else "Unknown",
                        "Status": e.status.value,
                        "Started": e.started_at.strftime("%Y-%m-%d %H:%M:%S") if e.started_at else "N/A",
                        "Duration": f"{e.duration:.2f}s" if e.duration else "N/A",
                        "Records": e.records_processed
                    })

                df = pd.DataFrame(exec_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No executions yet")

    @staticmethod
    def render_create_pipeline():
        """Render create pipeline page."""
        st.header("➕ Create New Pipeline")

        with st.form("create_pipeline_form"):
            # Basic information
            st.subheader("Basic Information")

            name = st.text_input("Pipeline Name *", placeholder="My ETL Pipeline")
            description = st.text_area("Description", placeholder="Describe what this pipeline does...")

            tags = st.text_input("Tags (comma-separated)", placeholder="etl, daily, production")

            # Visual pipeline builder
            st.subheader("Pipeline Steps")

            # Initialize session state for steps
            if 'pipeline_steps' not in st.session_state:
                st.session_state.pipeline_steps = []

            # Add step button
            if st.form_submit_button("Add Step"):
                st.session_state.pipeline_steps.append({
                    "name": "",
                    "type": "extract",
                    "config": {}
                })

            # Display steps
            for i, step in enumerate(st.session_state.pipeline_steps):
                with st.expander(f"Step {i + 1}: {step.get('name', 'Unnamed')}", expanded=True):
                    col1, col2 = st.columns(2)

                    with col1:
                        step_name = st.text_input(f"Step Name", key=f"step_name_{i}", value=step.get("name", ""))

                    with col2:
                        step_type = st.selectbox(
                            "Step Type",
                            ["extract", "transform", "load"],
                            key=f"step_type_{i}",
                            index=["extract", "transform", "load"].index(step.get("type", "extract"))
                        )

                    # Update step
                    st.session_state.pipeline_steps[i]["name"] = step_name
                    st.session_state.pipeline_steps[i]["type"] = step_type

            # Submit button
            submitted = st.form_submit_button("Create Pipeline")

            if submitted and name:
                with get_db_context() as db:
                    service = PipelineService(db)

                    try:
                        # Create pipeline
                        pipeline = service.create_pipeline(
                            name=name,
                            description=description,
                            tags=[t.strip() for t in tags.split(",")] if tags else []
                        )

                        # Add steps
                        for i, step in enumerate(st.session_state.pipeline_steps):
                            if step.get("name"):
                                service.add_step(
                                    pipeline_id=pipeline.id,
                                    name=step["name"],
                                    step_type=step["type"],
                                    config=step.get("config", {}),
                                    order=i + 1
                                )

                        st.success(f"Pipeline '{name}' created successfully!")
                        st.session_state.pipeline_steps = []

                    except Exception as e:
                        st.error(f"Error creating pipeline: {e}")

    @staticmethod
    def render_pipeline_list():
        """Render pipeline list page."""
        st.header("📋 Pipeline List")

        with get_db_context() as db:
            service = PipelineService(db)

            # Filters
            col1, col2 = st.columns(2)

            with col1:
                status_filter = st.selectbox(
                    "Filter by Status",
                    ["All", "Draft", "Active", "Paused", "Archived"]
                )

            # Get pipelines
            status = None
            if status_filter != "All":
                status = PipelineStatus[status_filter.upper()]

            pipelines = service.list_pipelines(status=status)

            if pipelines:
                for pipeline in pipelines:
                    with st.expander(f"{pipeline.name} - {pipeline.status.value}", expanded=False):
                        col1, col2, col3 = st.columns([2, 2, 1])

                        with col1:
                            st.write(f"**Description:** {pipeline.description or 'N/A'}")
                            st.write(f"**Created:** {pipeline.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                            st.write(f"**Tags:** {', '.join(pipeline.tags) if pipeline.tags else 'None'}")

                        with col2:
                            # Get metrics
                            metrics = service.get_pipeline_metrics(pipeline.id)
                            st.write(f"**Total Executions:** {metrics['total_executions']}")
                            st.write(f"**Success Rate:** {metrics['success_rate']:.1%}")
                            st.write(f"**Avg Duration:** {metrics['avg_duration']:.2f}s")

                        with col3:
                            # Actions
                            if st.button("▶️ Execute", key=f"exec_{pipeline.id}"):
                                try:
                                    execution = service.execute_pipeline(pipeline.id)
                                    st.success(f"Execution started: {execution.id}")
                                except Exception as e:
                                    st.error(f"Error: {e}")

                            if st.button("✏️ Edit", key=f"edit_{pipeline.id}"):
                                st.info("Edit functionality coming soon")

                            if st.button("🗑️ Delete", key=f"delete_{pipeline.id}"):
                                try:
                                    service.delete_pipeline(pipeline.id)
                                    st.success("Pipeline deleted")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")

                        # Show steps
                        if pipeline.steps:
                            st.write("**Steps:**")
                            for step in sorted(pipeline.steps, key=lambda x: x.order):
                                st.write(f"  {step.order}. {step.name} ({step.step_type})")

            else:
                st.info("No pipelines found. Create your first pipeline!")

    @staticmethod
    def render_connectors():
        """Render connectors page."""
        st.header("🔌 Data Connectors")

        tab1, tab2 = st.tabs(["Connector List", "Create Connector"])

        with tab1:
            with get_db_context() as db:
                service = PipelineService(db)
                connectors = service.list_connectors()

                if connectors:
                    for connector in connectors:
                        with st.expander(f"{connector.name} ({connector.connector_type})", expanded=False):
                            col1, col2 = st.columns([3, 1])

                            with col1:
                                st.write(f"**Type:** {connector.connector_type}")
                                st.write(f"**Description:** {connector.description or 'N/A'}")
                                st.write(f"**Status:** {'Active' if connector.is_active else 'Inactive'}")
                                if connector.last_tested_at:
                                    st.write(f"**Last Tested:** {connector.last_tested_at.strftime('%Y-%m-%d %H:%M:%S')}")
                                    st.write(f"**Test Status:** {connector.last_test_status}")

                            with col2:
                                if st.button("🔍 Test", key=f"test_{connector.id}"):
                                    result = service.test_connector(connector.id)
                                    st.info(f"Test started: {result['task_id']}")

                else:
                    st.info("No connectors found. Create your first connector!")

        with tab2:
            with st.form("create_connector_form"):
                st.subheader("Create New Connector")

                name = st.text_input("Connector Name *")
                connector_type = st.selectbox(
                    "Connector Type *",
                    ConnectorFactory.get_available_connectors()
                )
                description = st.text_area("Description")

                st.write("**Configuration (JSON)**")
                config = st.text_area("Config", value="{}", height=150)

                st.write("**Credentials (JSON)**")
                credentials = st.text_area("Credentials", value="{}", height=100)

                submitted = st.form_submit_button("Create Connector")

                if submitted and name:
                    try:
                        config_dict = json.loads(config)
                        credentials_dict = json.loads(credentials)

                        with get_db_context() as db:
                            service = PipelineService(db)
                            connector = service.create_connector(
                                name=name,
                                connector_type=connector_type,
                                config=config_dict,
                                credentials=credentials_dict,
                                description=description
                            )

                            st.success(f"Connector '{name}' created successfully!")

                    except json.JSONDecodeError as e:
                        st.error(f"Invalid JSON: {e}")
                    except Exception as e:
                        st.error(f"Error: {e}")

    @staticmethod
    def render_executions():
        """Render executions page."""
        st.header("▶️ Pipeline Executions")

        with get_db_context() as db:
            service = PipelineService(db)

            # Filters
            col1, col2 = st.columns(2)

            with col1:
                pipelines = service.list_pipelines()
                pipeline_options = {"All": None}
                pipeline_options.update({p.name: p.id for p in pipelines})

                selected_pipeline = st.selectbox("Filter by Pipeline", list(pipeline_options.keys()))

            with col2:
                status_filter = st.selectbox(
                    "Filter by Status",
                    ["All", "Pending", "Running", "Success", "Failed", "Cancelled"]
                )

            # Get executions
            pipeline_id = pipeline_options[selected_pipeline]

            status = None
            if status_filter != "All":
                status = ExecutionStatus[status_filter.upper()]

            executions = service.list_executions(pipeline_id=pipeline_id, status=status, limit=50)

            if executions:
                exec_data = []
                for e in executions:
                    pipeline = service.get_pipeline(e.pipeline_id)
                    exec_data.append({
                        "ID": e.id,
                        "Pipeline": pipeline.name if pipeline else "Unknown",
                        "Status": e.status.value,
                        "Trigger": e.trigger_type.value,
                        "Started": e.started_at.strftime("%Y-%m-%d %H:%M:%S") if e.started_at else "N/A",
                        "Duration": f"{e.duration:.2f}s" if e.duration else "N/A",
                        "Records": e.records_processed,
                        "Failed Records": e.records_failed
                    })

                df = pd.DataFrame(exec_data)
                st.dataframe(df, use_container_width=True)

                # Execution details
                selected_exec = st.selectbox("Select execution for details", [e["ID"] for e in exec_data])

                if selected_exec:
                    execution = service.get_execution(selected_exec)

                    if execution:
                        st.subheader(f"Execution #{execution.id} Details")

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric("Status", execution.status.value)

                        with col2:
                            st.metric("Records Processed", execution.records_processed)

                        with col3:
                            st.metric("Duration", f"{execution.duration:.2f}s" if execution.duration else "N/A")

                        if execution.error_message:
                            st.error(f"Error: {execution.error_message}")

                        # Step executions
                        if execution.step_executions:
                            st.write("**Step Executions:**")
                            step_data = []
                            for se in execution.step_executions:
                                step_data.append({
                                    "Step": se.step.name,
                                    "Status": se.status.value,
                                    "Duration": f"{se.duration:.2f}s" if se.duration else "N/A",
                                    "Records": se.records_processed,
                                    "Failed": se.records_failed
                                })

                            st.dataframe(pd.DataFrame(step_data), use_container_width=True)

            else:
                st.info("No executions found")

    @staticmethod
    def render_schedules():
        """Render schedules page."""
        st.header("📅 Pipeline Schedules")

        with get_db_context() as db:
            service = PipelineService(db)

            # Create schedule form
            with st.form("create_schedule_form"):
                st.subheader("Create New Schedule")

                pipelines = service.list_pipelines(status=PipelineStatus.ACTIVE)
                pipeline_options = {p.name: p.id for p in pipelines}

                selected_pipeline = st.selectbox("Select Pipeline", list(pipeline_options.keys()))
                cron_expression = st.text_input("Cron Expression", value="0 0 * * *", help="Format: minute hour day month weekday")
                timezone = st.text_input("Timezone", value="UTC")

                submitted = st.form_submit_button("Create Schedule")

                if submitted and selected_pipeline:
                    try:
                        pipeline_id = pipeline_options[selected_pipeline]
                        schedule = service.create_schedule(
                            pipeline_id=pipeline_id,
                            cron_expression=cron_expression,
                            timezone=timezone
                        )

                        st.success(f"Schedule created for '{selected_pipeline}'!")

                    except Exception as e:
                        st.error(f"Error: {e}")

    @staticmethod
    def render_monitoring():
        """Render monitoring page."""
        st.header("📈 Pipeline Monitoring")

        with get_db_context() as db:
            service = PipelineService(db)

            # Select pipeline
            pipelines = service.list_pipelines()
            pipeline_options = {p.name: p.id for p in pipelines}

            if pipeline_options:
                selected_pipeline = st.selectbox("Select Pipeline", list(pipeline_options.keys()))

                if selected_pipeline:
                    pipeline_id = pipeline_options[selected_pipeline]

                    # Get metrics
                    metrics = service.get_pipeline_metrics(pipeline_id)

                    # Display metrics
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("Total Executions", metrics["total_executions"])

                    with col2:
                        st.metric("Success Rate", f"{metrics['success_rate']:.1%}")

                    with col3:
                        st.metric("Avg Duration", f"{metrics['avg_duration']:.2f}s")

                    with col4:
                        st.metric("Total Records", metrics["total_records_processed"])

                    # Execution history chart
                    st.subheader("Execution History")

                    executions = service.list_executions(pipeline_id=pipeline_id, limit=100)

                    if executions:
                        chart_data = []
                        for e in executions:
                            if e.started_at:
                                chart_data.append({
                                    "Date": e.started_at.date(),
                                    "Status": e.status.value,
                                    "Duration": e.duration or 0,
                                    "Records": e.records_processed
                                })

                        df = pd.DataFrame(chart_data)

                        # Group by date and status
                        st.bar_chart(df.groupby("Status").size())

                    else:
                        st.info("No execution history available")

            else:
                st.info("No pipelines available for monitoring")
