"""
NEXUS Dashboard Builder - Streamlit UI Module
Interactive UI for dashboard creation, editing, and viewing
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Optional, Any
from datetime import datetime

# Import dashboard modules
try:
    from .builder import DashboardBuilder, DashboardWidget, GridPosition, DashboardTheme, RefreshInterval
    from .widgets import WidgetFactory, WidgetType, KPIWidget, ChartWidget, TableWidget
    from .layouts import LayoutManager, GridConfig
    from .datasources import DataSourceManager, RealtimeDataSource
    from .sharing import SharingManager, SharePermission, ShareExpiry
    from .templates import TemplateLibrary, DashboardTemplate
except ImportError:
    # For standalone execution
    pass


class DashboardUI:
    """Main Streamlit UI for Dashboard Builder"""

    def __init__(self):
        self.init_session_state()

    def init_session_state(self):
        """Initialize session state variables"""
        if 'current_dashboard' not in st.session_state:
            st.session_state.current_dashboard = None

        if 'data_source_manager' not in st.session_state:
            st.session_state.data_source_manager = DataSourceManager()

        if 'template_library' not in st.session_state:
            st.session_state.template_library = TemplateLibrary()

        if 'sharing_manager' not in st.session_state:
            st.session_state.sharing_manager = SharingManager()

        if 'selected_widgets' not in st.session_state:
            st.session_state.selected_widgets = []

        if 'edit_mode' not in st.session_state:
            st.session_state.edit_mode = False

    def render(self):
        """Render the main UI"""
        st.title("📊 NEXUS Dashboard Builder")
        st.markdown("*Rival to Grafana, Metabase - Build stunning real-time dashboards*")

        # Sidebar navigation
        page = st.sidebar.selectbox(
            "Navigation",
            ["Dashboard Builder", "Templates", "Data Sources", "Sharing", "My Dashboards"]
        )

        # Render selected page
        if page == "Dashboard Builder":
            self.render_builder()
        elif page == "Templates":
            self.render_templates()
        elif page == "Data Sources":
            self.render_data_sources()
        elif page == "Sharing":
            self.render_sharing()
        elif page == "My Dashboards":
            self.render_my_dashboards()

    def render_builder(self):
        """Render dashboard builder interface"""
        st.header("Dashboard Builder")

        # Top toolbar
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

        with col1:
            if st.session_state.current_dashboard:
                dashboard_name = st.text_input(
                    "Dashboard Name",
                    value=st.session_state.current_dashboard.name,
                    key="dashboard_name"
                )
                st.session_state.current_dashboard.name = dashboard_name

        with col2:
            if st.button("➕ New Dashboard"):
                st.session_state.current_dashboard = DashboardBuilder()
                st.session_state.edit_mode = True
                st.rerun()

        with col3:
            edit_mode = st.checkbox(
                "Edit Mode",
                value=st.session_state.edit_mode,
                key="edit_mode_toggle"
            )
            st.session_state.edit_mode = edit_mode

        with col4:
            if st.session_state.current_dashboard:
                if st.button("💾 Save"):
                    st.success("Dashboard saved!")

        st.divider()

        if not st.session_state.current_dashboard:
            self.render_welcome_screen()
            return

        # Main builder interface
        col_left, col_right = st.columns([1, 3])

        with col_left:
            self.render_widget_panel()

        with col_right:
            self.render_canvas()

    def render_welcome_screen(self):
        """Render welcome screen"""
        st.info("👈 Create a new dashboard or select a template to get started!")

        # Quick start templates
        st.subheader("Quick Start Templates")

        library = st.session_state.template_library
        templates = library.get_popular_templates(limit=6)

        cols = st.columns(3)

        for i, template in enumerate(templates):
            with cols[i % 3]:
                st.markdown(f"### {template.name}")
                st.caption(template.description)

                if st.button("Use Template", key=f"quick_use_{template.template_id}"):
                    self.create_from_template(template)

    def render_widget_panel(self):
        """Render widget selection panel"""
        st.subheader("Widgets")

        if not st.session_state.edit_mode:
            st.info("Enable Edit Mode to add widgets")
            return

        # Widget categories
        category = st.selectbox(
            "Category",
            ["KPIs", "Charts", "Tables", "Filters", "Text"]
        )

        if category == "KPIs":
            self.render_kpi_widgets()
        elif category == "Charts":
            self.render_chart_widgets()
        elif category == "Tables":
            self.render_table_widgets()
        elif category == "Filters":
            self.render_filter_widgets()
        elif category == "Text":
            self.render_text_widgets()

        st.divider()

        # Dashboard settings
        with st.expander("⚙️ Dashboard Settings"):
            self.render_dashboard_settings()

    def render_kpi_widgets(self):
        """Render KPI widget options"""
        st.markdown("#### KPI Widgets")

        if st.button("➕ Add KPI", use_container_width=True):
            dashboard = st.session_state.current_dashboard
            widget = DashboardWidget(
                widget_type="kpi",
                title="New KPI",
                position=GridPosition(0, 0, 3, 2)
            )
            dashboard.add_widget(widget)
            st.rerun()

    def render_chart_widgets(self):
        """Render chart widget options"""
        st.markdown("#### Chart Widgets")

        chart_types = ["Line", "Bar", "Pie", "Area", "Scatter", "Heatmap"]

        for chart_type in chart_types:
            if st.button(f"➕ {chart_type} Chart", use_container_width=True, key=f"add_{chart_type.lower()}"):
                dashboard = st.session_state.current_dashboard
                widget = DashboardWidget(
                    widget_type="chart",
                    title=f"{chart_type} Chart",
                    position=GridPosition(0, 0, 6, 4),
                    config={"chart_type": chart_type.lower()}
                )
                dashboard.add_widget(widget)
                st.rerun()

    def render_table_widgets(self):
        """Render table widget options"""
        st.markdown("#### Table Widgets")

        if st.button("➕ Add Table", use_container_width=True):
            dashboard = st.session_state.current_dashboard
            widget = DashboardWidget(
                widget_type="table",
                title="Data Table",
                position=GridPosition(0, 0, 12, 4)
            )
            dashboard.add_widget(widget)
            st.rerun()

    def render_filter_widgets(self):
        """Render filter widget options"""
        st.markdown("#### Filter Widgets")

        filter_types = ["Dropdown", "Multiselect", "Date Range", "Text Search"]

        for filter_type in filter_types:
            if st.button(f"➕ {filter_type}", use_container_width=True, key=f"add_{filter_type.lower().replace(' ', '_')}"):
                dashboard = st.session_state.current_dashboard
                widget = DashboardWidget(
                    widget_type="filter",
                    title=filter_type,
                    position=GridPosition(0, 0, 3, 1),
                    config={"filter_type": filter_type.lower().replace(' ', '_')}
                )
                dashboard.add_widget(widget)
                st.rerun()

    def render_text_widgets(self):
        """Render text widget options"""
        st.markdown("#### Text Widgets")

        if st.button("➕ Add Text", use_container_width=True):
            dashboard = st.session_state.current_dashboard
            widget = DashboardWidget(
                widget_type="text",
                title="",
                position=GridPosition(0, 0, 6, 2),
                config={"content": "Enter your text here..."}
            )
            dashboard.add_widget(widget)
            st.rerun()

    def render_dashboard_settings(self):
        """Render dashboard settings"""
        dashboard = st.session_state.current_dashboard

        # Theme
        theme = st.selectbox(
            "Theme",
            ["Light", "Dark", "Blue"],
            index=0 if dashboard.theme.value == "light" else 1
        )
        dashboard.theme = DashboardTheme(theme.lower())

        # Auto-refresh
        refresh_enabled = st.checkbox("Auto Refresh", value=dashboard.auto_refresh_enabled)
        dashboard.auto_refresh_enabled = refresh_enabled

        if refresh_enabled:
            refresh_options = {
                "5 seconds": 5,
                "10 seconds": 10,
                "30 seconds": 30,
                "1 minute": 60,
                "5 minutes": 300
            }

            refresh_label = st.selectbox("Refresh Interval", list(refresh_options.keys()))
            dashboard.refresh_interval = RefreshInterval(refresh_options[refresh_label])

        # Layout
        st.markdown("**Layout**")
        columns = st.slider("Grid Columns", 6, 24, dashboard.layout_config['columns'])
        dashboard.layout_config['columns'] = columns

        responsive = st.checkbox("Responsive", value=dashboard.layout_config['responsive'])
        dashboard.layout_config['responsive'] = responsive

    def render_canvas(self):
        """Render dashboard canvas"""
        dashboard = st.session_state.current_dashboard

        # Canvas toolbar
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"**Widgets:** {len(dashboard.widgets)}")

        with col2:
            if st.button("🔄 Refresh All"):
                st.rerun()

        with col3:
            if st.button("📐 Auto Layout"):
                dashboard.auto_layout()
                st.rerun()

        with col4:
            if st.button("🗑️ Clear All"):
                if st.session_state.edit_mode:
                    dashboard.widgets.clear()
                    st.rerun()

        st.divider()

        # Render widgets
        if not dashboard.widgets:
            st.info("No widgets yet. Add widgets from the panel on the left.")
            return

        # Group widgets by row for layout
        widgets_by_row = {}
        for widget in dashboard.widgets:
            row = widget.position.y
            if row not in widgets_by_row:
                widgets_by_row[row] = []
            widgets_by_row[row].append(widget)

        # Render each row
        for row in sorted(widgets_by_row.keys()):
            row_widgets = sorted(widgets_by_row[row], key=lambda w: w.position.x)

            # Create columns based on widget widths
            col_widths = [w.position.width for w in row_widgets]
            cols = st.columns(col_widths)

            for i, widget in enumerate(row_widgets):
                with cols[i]:
                    self.render_widget(widget)

    def render_widget(self, widget: DashboardWidget):
        """Render a single widget"""
        with st.container():
            # Widget header
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                if widget.title:
                    st.markdown(f"**{widget.title}**")

            with col2:
                if st.session_state.edit_mode:
                    if st.button("✏️", key=f"edit_{widget.widget_id}"):
                        self.edit_widget(widget)

            with col3:
                if st.session_state.edit_mode:
                    if st.button("🗑️", key=f"delete_{widget.widget_id}"):
                        st.session_state.current_dashboard.remove_widget(widget.widget_id)
                        st.rerun()

            # Widget content
            self.render_widget_content(widget)

    def render_widget_content(self, widget: DashboardWidget):
        """Render widget content based on type"""
        if widget.widget_type == "kpi":
            self.render_kpi_content(widget)
        elif widget.widget_type == "chart":
            self.render_chart_content(widget)
        elif widget.widget_type == "table":
            self.render_table_content(widget)
        elif widget.widget_type == "filter":
            self.render_filter_content(widget)
        elif widget.widget_type == "text":
            self.render_text_content(widget)
        else:
            st.info(f"Widget type: {widget.widget_type}")

    def render_kpi_content(self, widget: DashboardWidget):
        """Render KPI widget content"""
        # Sample data
        value = widget.config.get('value', 12345)
        trend = widget.config.get('trend', 15.2)

        col1, col2 = st.columns([2, 1])

        with col1:
            st.metric(
                label="",
                value=f"{value:,}",
                delta=f"{trend:+.1f}%"
            )

        with col2:
            # Sparkline placeholder
            st.markdown("📈")

    def render_chart_content(self, widget: DashboardWidget):
        """Render chart widget content"""
        # Sample data
        df = pd.DataFrame({
            'x': range(1, 11),
            'y': [10, 15, 13, 17, 20, 18, 25, 22, 28, 30]
        })

        chart_type = widget.config.get('chart_type', 'line')

        if chart_type == 'line':
            st.line_chart(df.set_index('x'))
        elif chart_type == 'bar':
            st.bar_chart(df.set_index('x'))
        elif chart_type == 'area':
            st.area_chart(df.set_index('x'))
        else:
            st.info(f"Chart type: {chart_type}")

    def render_table_content(self, widget: DashboardWidget):
        """Render table widget content"""
        # Sample data
        df = pd.DataFrame({
            'Product': ['Product A', 'Product B', 'Product C'],
            'Sales': [1000, 1500, 1200],
            'Growth': ['+15%', '+22%', '+8%']
        })

        st.dataframe(df, use_container_width=True)

    def render_filter_content(self, widget: DashboardWidget):
        """Render filter widget content"""
        filter_type = widget.config.get('filter_type', 'dropdown')

        if filter_type == 'dropdown':
            st.selectbox(
                "",
                ["Option 1", "Option 2", "Option 3"],
                key=f"filter_{widget.widget_id}"
            )
        elif filter_type == 'multiselect':
            st.multiselect(
                "",
                ["Option 1", "Option 2", "Option 3"],
                key=f"filter_{widget.widget_id}"
            )
        elif filter_type == 'date_range':
            col1, col2 = st.columns(2)
            with col1:
                st.date_input("From", key=f"filter_from_{widget.widget_id}")
            with col2:
                st.date_input("To", key=f"filter_to_{widget.widget_id}")

    def render_text_content(self, widget: DashboardWidget):
        """Render text widget content"""
        content = widget.config.get('content', 'Enter text here...')
        st.markdown(content)

    def edit_widget(self, widget: DashboardWidget):
        """Open widget edit dialog"""
        # Would open a modal or sidebar for editing
        pass

    def render_templates(self):
        """Render templates page"""
        st.header("Dashboard Templates")

        library = st.session_state.template_library

        # Search and filter
        col1, col2 = st.columns([3, 1])

        with col1:
            search_query = st.text_input("Search Templates", "")

        with col2:
            category = st.selectbox("Category", ["All", "Analytics", "Business", "Sales", "Marketing", "Finance"])

        # Display templates
        if search_query:
            templates = library.search_templates(search_query)
        else:
            templates = library.list_templates()

        st.subheader(f"Available Templates ({len(templates)})")

        # Display in grid
        cols = st.columns(3)

        for i, template in enumerate(templates):
            with cols[i % 3]:
                with st.container():
                    st.markdown(f"### {template.name}")
                    st.caption(template.description)
                    st.markdown(f"📁 {template.category.value}")
                    st.markdown(f"⭐ Used {template.usage_count} times")

                    if st.button("Use Template", key=f"use_{template.template_id}"):
                        self.create_from_template(template)

    def create_from_template(self, template: DashboardTemplate):
        """Create dashboard from template"""
        dashboard = DashboardBuilder()
        dashboard.name = template.name
        dashboard.description = template.description

        # Create widgets from template
        for widget_config in template.widgets:
            widget = DashboardWidget(
                widget_type=widget_config['type'],
                title=widget_config['title'],
                position=GridPosition(**widget_config['position']),
                config=widget_config.get('config', {})
            )
            dashboard.add_widget(widget)

        st.session_state.current_dashboard = dashboard
        st.session_state.edit_mode = True

        template_lib = st.session_state.template_library
        template_lib.increment_usage(template.template_id)

        st.success(f"Created dashboard from '{template.name}'!")
        st.rerun()

    def render_data_sources(self):
        """Render data sources page"""
        st.header("Data Sources")

        st.info("Configure data sources for real-time dashboard updates")

        # Add data source form
        with st.expander("➕ Add Data Source"):
            name = st.text_input("Name")
            source_type = st.selectbox("Type", ["SQL Database", "REST API", "File Upload", "Streaming"])

            if st.button("Add Data Source"):
                st.success(f"Data source '{name}' added!")

        # List data sources
        st.subheader("Configured Data Sources")
        st.info("No data sources configured yet.")

    def render_sharing(self):
        """Render sharing page"""
        st.header("Dashboard Sharing")

        if not st.session_state.current_dashboard:
            st.info("Select or create a dashboard to share")
            return

        dashboard = st.session_state.current_dashboard

        # Share link
        st.subheader("Share Link")

        col1, col2 = st.columns([3, 1])

        with col1:
            share_link = st.text_input(
                "Share URL",
                value="https://nexus.example.com/share/abc123",
                disabled=True
            )

        with col2:
            if st.button("📋 Copy"):
                st.success("Link copied!")

        # Share settings
        st.subheader("Share Settings")

        col1, col2 = st.columns(2)

        with col1:
            permission = st.selectbox(
                "Permission",
                ["View Only", "Can Interact", "Can Edit"]
            )

            expiry = st.selectbox(
                "Expires",
                ["Never", "1 Hour", "1 Day", "1 Week", "1 Month"]
            )

        with col2:
            password_protected = st.checkbox("Password Protected")

            if password_protected:
                password = st.text_input("Password", type="password")

        # Embed code
        st.subheader("Embed Code")

        embed_code = f'''<iframe src="https://nexus.example.com/embed/{dashboard.dashboard_id}"
    width="100%" height="800" frameborder="0"></iframe>'''

        st.code(embed_code, language="html")

        if st.button("📋 Copy Embed Code"):
            st.success("Embed code copied!")

    def render_my_dashboards(self):
        """Render my dashboards page"""
        st.header("My Dashboards")

        st.info("Your saved dashboards will appear here.")


def main():
    """Main entry point"""
    st.set_page_config(
        page_title="NEXUS Dashboard Builder",
        page_icon="📊",
        layout="wide"
    )

    ui = DashboardUI()
    ui.render()


if __name__ == "__main__":
    main()
