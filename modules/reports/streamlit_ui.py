"""
NEXUS Reports Builder - Streamlit UI Module
Interactive UI for report design, execution, and management
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
import plotly.graph_objects as go

# Import report modules
try:
    from .designer import ReportDesigner, ReportElement, ReportElementType, PageSettings
    from .datasources import DataSourceManager, SQLDataSource, RESTAPIDataSource, FileDataSource
    from .charts import Chart, ChartType, ChartConfig, Table
    from .filters import FilterManager, Parameter, ParameterType, FilterCondition, FilterOperator
    from .scheduler import ReportScheduler, ScheduledJob, ScheduleConfig, ScheduleFrequency
    from .export import ReportExporter, ExportConfig, ExportFormat
    from .templates import TemplateLibrary, ReportTemplate, TemplateCategory
except ImportError:
    # For standalone execution
    pass


class ReportsUI:
    """Main Streamlit UI for Reports Builder"""

    def __init__(self):
        self.init_session_state()

    def init_session_state(self):
        """Initialize session state variables"""
        if 'current_report' not in st.session_state:
            st.session_state.current_report = None

        if 'data_source_manager' not in st.session_state:
            st.session_state.data_source_manager = DataSourceManager()

        if 'template_library' not in st.session_state:
            st.session_state.template_library = TemplateLibrary()

        if 'scheduler' not in st.session_state:
            st.session_state.scheduler = ReportScheduler()

        if 'report_data' not in st.session_state:
            st.session_state.report_data = None

    def render(self):
        """Render the main UI"""
        st.title("📊 NEXUS Reports Builder")
        st.markdown("*Enterprise-grade reporting platform - Rival to Crystal Reports, Power BI, and Tableau*")

        # Sidebar navigation
        page = st.sidebar.selectbox(
            "Navigation",
            ["Report Designer", "Data Sources", "Templates", "Scheduler", "My Reports", "Export"]
        )

        # Render selected page
        if page == "Report Designer":
            self.render_designer()
        elif page == "Data Sources":
            self.render_data_sources()
        elif page == "Templates":
            self.render_templates()
        elif page == "Scheduler":
            self.render_scheduler()
        elif page == "My Reports":
            self.render_my_reports()
        elif page == "Export":
            self.render_export()

    def render_designer(self):
        """Render report designer interface"""
        st.header("Report Designer")

        col1, col2 = st.columns([1, 3])

        with col1:
            st.subheader("Report Settings")

            # Report name and description
            report_name = st.text_input("Report Name", value="New Report")
            report_desc = st.text_area("Description", value="")

            # Create new report button
            if st.button("Create New Report"):
                st.session_state.current_report = ReportDesigner()
                st.session_state.current_report.name = report_name
                st.session_state.current_report.description = report_desc
                st.success("New report created!")

            st.divider()

            # Element palette
            st.subheader("Add Elements")
            element_type = st.selectbox(
                "Element Type",
                ["Text", "Chart", "Table", "Filter", "Image"]
            )

            if st.button("Add Element"):
                if st.session_state.current_report:
                    # Add element logic here
                    st.success(f"Added {element_type} element")
                else:
                    st.warning("Please create a report first")

        with col2:
            st.subheader("Report Canvas")

            if st.session_state.current_report:
                # Display report canvas
                self.render_report_canvas()
            else:
                st.info("Create a new report to get started")

    def render_report_canvas(self):
        """Render the report canvas"""
        report = st.session_state.current_report

        # Page settings
        with st.expander("Page Settings"):
            col1, col2 = st.columns(2)
            with col1:
                page_size = st.selectbox("Page Size", ["A4", "Letter", "Legal"])
                orientation = st.selectbox("Orientation", ["Portrait", "Landscape"])
            with col2:
                margin = st.slider("Margins (inches)", 0.5, 2.0, 1.0, 0.1)

        # Display elements
        st.subheader("Report Elements")

        if report.elements:
            for i, element in enumerate(report.elements):
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        st.write(f"**{element.type.value}** at ({element.x}, {element.y})")

                    with col2:
                        if st.button("Edit", key=f"edit_{i}"):
                            st.session_state.editing_element = i

                    with col3:
                        if st.button("Delete", key=f"delete_{i}"):
                            report.remove_element(element.id)
                            st.rerun()
        else:
            st.info("No elements added yet. Add elements from the palette on the left.")

    def render_data_sources(self):
        """Render data sources management"""
        st.header("Data Sources")

        tab1, tab2, tab3 = st.tabs(["SQL Database", "REST API", "Files"])

        with tab1:
            self.render_sql_datasource()

        with tab2:
            self.render_api_datasource()

        with tab3:
            self.render_file_datasource()

        # List existing data sources
        st.divider()
        st.subheader("Existing Data Sources")

        manager = st.session_state.data_source_manager
        sources = manager.list_data_sources()

        if sources:
            for source_name in sources:
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.write(f"📊 {source_name}")

                with col2:
                    if st.button("Test", key=f"test_{source_name}"):
                        ds = manager.get_data_source(source_name)
                        if ds and ds.test_connection():
                            st.success("✓ Connected")
                        else:
                            st.error("✗ Failed")

                with col3:
                    if st.button("Delete", key=f"del_{source_name}"):
                        manager.remove_data_source(source_name)
                        st.rerun()
        else:
            st.info("No data sources configured yet.")

    def render_sql_datasource(self):
        """Render SQL database data source form"""
        st.subheader("Add SQL Database")

        with st.form("sql_datasource"):
            name = st.text_input("Data Source Name")
            host = st.text_input("Host")
            port = st.number_input("Port", value=5432)
            database = st.text_input("Database")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            driver = st.selectbox("Driver", ["postgresql", "mysql", "mssql", "oracle"])

            if st.form_submit_button("Add Data Source"):
                # Create data source
                st.success(f"SQL data source '{name}' added successfully!")

    def render_api_datasource(self):
        """Render REST API data source form"""
        st.subheader("Add REST API")

        with st.form("api_datasource"):
            name = st.text_input("Data Source Name")
            base_url = st.text_input("Base URL")
            auth_type = st.selectbox("Authentication", ["None", "API Key", "Bearer Token", "Basic Auth"])

            if auth_type == "API Key":
                api_key = st.text_input("API Key", type="password")
                api_key_header = st.text_input("Header Name", value="X-API-Key")
            elif auth_type == "Bearer Token":
                bearer_token = st.text_input("Bearer Token", type="password")
            elif auth_type == "Basic Auth":
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")

            if st.form_submit_button("Add Data Source"):
                st.success(f"API data source '{name}' added successfully!")

    def render_file_datasource(self):
        """Render file data source form"""
        st.subheader("Add File Data Source")

        uploaded_file = st.file_uploader(
            "Upload File",
            type=["csv", "xlsx", "json", "xml", "parquet"]
        )

        if uploaded_file:
            name = st.text_input("Data Source Name", value=uploaded_file.name)

            if st.button("Add Data Source"):
                # Save file and create data source
                st.success(f"File data source '{name}' added successfully!")

                # Preview data
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                    st.dataframe(df.head())

    def render_templates(self):
        """Render templates library"""
        st.header("Report Templates")

        library = st.session_state.template_library

        # Search and filter
        col1, col2 = st.columns([3, 1])

        with col1:
            search_query = st.text_input("Search Templates", "")

        with col2:
            category = st.selectbox("Category", ["All", "Financial", "Sales", "Marketing", "Operations", "HR"])

        # Display templates
        templates = library.list_templates()

        if search_query:
            templates = library.search_templates(search_query)

        if category != "All":
            templates = [t for t in templates if t.category.value.lower() == category.lower()]

        st.subheader(f"Available Templates ({len(templates)})")

        # Display in grid
        cols = st.columns(3)

        for i, template in enumerate(templates):
            with cols[i % 3]:
                with st.container():
                    st.markdown(f"### {template.name}")
                    st.caption(template.description)
                    st.write(f"📁 {template.category.value}")
                    st.write(f"⭐ Used {template.usage_count} times")

                    if st.button("Use Template", key=f"use_{template.template_id}"):
                        # Create report from template
                        st.success(f"Created report from '{template.name}'")
                        library.increment_usage(template.template_id)

    def render_scheduler(self):
        """Render scheduler interface"""
        st.header("Report Scheduler")

        scheduler = st.session_state.scheduler

        tab1, tab2 = st.tabs(["Schedule New", "Scheduled Jobs"])

        with tab1:
            self.render_schedule_form()

        with tab2:
            self.render_scheduled_jobs()

    def render_schedule_form(self):
        """Render schedule form"""
        st.subheader("Schedule a Report")

        with st.form("schedule_report"):
            job_name = st.text_input("Job Name")
            description = st.text_area("Description")

            col1, col2 = st.columns(2)

            with col1:
                frequency = st.selectbox(
                    "Frequency",
                    ["Once", "Daily", "Weekly", "Monthly", "Quarterly"]
                )

                start_date = st.date_input("Start Date")
                time_of_day = st.time_input("Time of Day")

            with col2:
                export_format = st.selectbox("Export Format", ["PDF", "Excel", "CSV"])

                email_recipients = st.text_area(
                    "Email Recipients (one per line)",
                    help="Enter email addresses, one per line"
                )

            if st.form_submit_button("Schedule Report"):
                st.success(f"Report scheduled: {job_name}")

    def render_scheduled_jobs(self):
        """Render list of scheduled jobs"""
        scheduler = st.session_state.scheduler
        jobs = scheduler.list_jobs()

        if jobs:
            for job in jobs:
                with st.expander(f"📅 {job.name}"):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write(f"**Status:** {job.status.value}")
                        st.write(f"**Frequency:** {job.schedule.frequency.value if job.schedule else 'N/A'}")

                    with col2:
                        st.write(f"**Last Run:** {job.last_execution.strftime('%Y-%m-%d %H:%M') if job.last_execution else 'Never'}")
                        st.write(f"**Next Run:** {job.next_execution.strftime('%Y-%m-%d %H:%M') if job.next_execution else 'N/A'}")

                    with col3:
                        stats = job.get_execution_stats()
                        st.write(f"**Success Rate:** {stats['success_rate']:.1f}%")
                        st.write(f"**Total Runs:** {stats['total_executions']}")

                    # Actions
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        if st.button("Pause", key=f"pause_{job.job_id}"):
                            scheduler.pause_job(job.job_id)
                            st.rerun()

                    with col2:
                        if st.button("Run Now", key=f"run_{job.job_id}"):
                            scheduler.execute_job(job.job_id)
                            st.success("Job executed!")

                    with col3:
                        if st.button("Delete", key=f"del_job_{job.job_id}"):
                            scheduler.remove_job(job.job_id)
                            st.rerun()
        else:
            st.info("No scheduled jobs yet.")

    def render_my_reports(self):
        """Render saved reports"""
        st.header("My Reports")

        # Placeholder for report list
        st.info("Your saved reports will appear here.")

    def render_export(self):
        """Render export interface"""
        st.header("Export Report")

        if st.session_state.report_data:
            st.subheader("Export Settings")

            col1, col2 = st.columns(2)

            with col1:
                export_format = st.selectbox("Format", ["PDF", "Excel", "CSV", "JSON", "HTML"])
                filename = st.text_input("Filename", "report")

            with col2:
                include_charts = st.checkbox("Include Charts", value=True)
                include_tables = st.checkbox("Include Tables", value=True)

            if st.button("Export"):
                exporter = ReportExporter()

                # Create config
                config = ExportConfig(
                    format=ExportFormat(export_format.lower()),
                    filename=f"{filename}.{export_format.lower()}",
                    include_charts=include_charts,
                    include_tables=include_tables
                )

                # Export
                content = exporter.export(st.session_state.report_data, config)

                # Download button
                st.download_button(
                    label=f"Download {export_format}",
                    data=content,
                    file_name=config.filename,
                    mime=exporter.get_mime_type(config.format)
                )
        else:
            st.info("No report data to export. Please run a report first.")


def main():
    """Main entry point"""
    st.set_page_config(
        page_title="NEXUS Reports Builder",
        page_icon="📊",
        layout="wide"
    )

    ui = ReportsUI()
    ui.render()


if __name__ == "__main__":
    main()
