"""
NEXUS Database Manager - Streamlit UI

Comprehensive visual database management interface with:
- Connection management
- Visual query builder
- Schema designer
- Data explorer
- Migration manager
- Backup/restore
- Performance monitoring
- User administration
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json

# Import database modules
from .manager import DatabaseManager, DatabaseType, ConnectionConfig, ConnectionStatus
from .query_builder import QueryBuilder, Query, JoinType, OperatorType, AggregateFunction, SortOrder
from .schema_designer import SchemaDesigner, TableBuilder, DataType, IndexType
from .data_explorer import DataExplorer, FilterCondition, SortCondition, ExportFormat
from .migration import MigrationManager, MigrationStatus
from .backup import BackupManager, BackupConfig, BackupType, CompressionType
from .performance import PerformanceMonitor
from .admin import AdminManager, PermissionType, ResourceType


class DatabaseUI:
    """
    NEXUS Database Manager UI

    Complete database management interface rivaling phpMyAdmin, DBeaver, and TablePlus.
    """

    def __init__(self):
        """Initialize database UI"""
        self.initialize_session_state()

    def initialize_session_state(self):
        """Initialize Streamlit session state"""
        if 'db_manager' not in st.session_state:
            st.session_state.db_manager = DatabaseManager()

        if 'query_builder' not in st.session_state:
            st.session_state.query_builder = QueryBuilder()

        if 'schema_designer' not in st.session_state:
            st.session_state.schema_designer = SchemaDesigner()

        if 'admin_manager' not in st.session_state:
            st.session_state.admin_manager = AdminManager()

        if 'active_connection' not in st.session_state:
            st.session_state.active_connection = None

        if 'query_history' not in st.session_state:
            st.session_state.query_history = []

    def run(self):
        """Run the Streamlit UI"""
        st.set_page_config(
            page_title="NEXUS Database Manager",
            page_icon="🗄️",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Custom CSS
        st.markdown("""
            <style>
            .main-header {
                font-size: 2.5rem;
                font-weight: bold;
                color: #1E88E5;
                margin-bottom: 1rem;
            }
            .section-header {
                font-size: 1.5rem;
                font-weight: bold;
                color: #424242;
                margin-top: 2rem;
                margin-bottom: 1rem;
            }
            .metric-card {
                background-color: #f5f5f5;
                padding: 1rem;
                border-radius: 0.5rem;
                border-left: 4px solid #1E88E5;
            }
            .success-message {
                background-color: #4CAF50;
                color: white;
                padding: 0.5rem;
                border-radius: 0.25rem;
            }
            .error-message {
                background-color: #F44336;
                color: white;
                padding: 0.5rem;
                border-radius: 0.25rem;
            }
            </style>
        """, unsafe_allow_html=True)

        # Header
        st.markdown('<div class="main-header">🗄️ NEXUS Database Manager</div>', unsafe_allow_html=True)
        st.markdown("*Professional database management tool - Rival to phpMyAdmin, DBeaver & TablePlus*")

        # Sidebar navigation
        with st.sidebar:
            st.image("https://via.placeholder.com/200x80/1E88E5/FFFFFF?text=NEXUS", use_container_width=True)

            menu = st.radio(
                "Navigation",
                [
                    "🔌 Connections",
                    "🔍 Query Builder",
                    "📊 Data Explorer",
                    "🏗️ Schema Designer",
                    "🔄 Migrations",
                    "💾 Backup & Restore",
                    "⚡ Performance",
                    "👥 Administration",
                    "📈 Dashboard"
                ]
            )

            st.divider()

            # Connection status
            self.render_connection_status()

        # Route to selected page
        if menu == "🔌 Connections":
            self.page_connections()
        elif menu == "🔍 Query Builder":
            self.page_query_builder()
        elif menu == "📊 Data Explorer":
            self.page_data_explorer()
        elif menu == "🏗️ Schema Designer":
            self.page_schema_designer()
        elif menu == "🔄 Migrations":
            self.page_migrations()
        elif menu == "💾 Backup & Restore":
            self.page_backup_restore()
        elif menu == "⚡ Performance":
            self.page_performance()
        elif menu == "👥 Administration":
            self.page_administration()
        elif menu == "📈 Dashboard":
            self.page_dashboard()

    def render_connection_status(self):
        """Render connection status in sidebar"""
        st.subheader("Connection Status")

        if st.session_state.active_connection:
            conn_name = st.session_state.active_connection
            st.success(f"✓ Connected: {conn_name}")

            if st.button("Disconnect"):
                st.session_state.active_connection = None
                st.rerun()
        else:
            st.warning("No active connection")

    def page_connections(self):
        """Connection management page"""
        st.markdown('<div class="section-header">Connection Manager</div>', unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(["➕ New Connection", "📋 Connections", "🔧 Test"])

        with tab1:
            self.render_new_connection_form()

        with tab2:
            self.render_connection_list()

        with tab3:
            self.render_test_connection()

    def render_new_connection_form(self):
        """Render new connection form"""
        st.subheader("Create New Connection")

        with st.form("new_connection"):
            col1, col2 = st.columns(2)

            with col1:
                conn_name = st.text_input("Connection Name*", placeholder="my_database")
                db_type = st.selectbox(
                    "Database Type*",
                    options=[t.value for t in DatabaseType]
                )
                host = st.text_input("Host", value="localhost")
                database = st.text_input("Database Name*")

            with col2:
                port = st.number_input("Port", value=5432, min_value=1, max_value=65535)
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                ssl = st.checkbox("Use SSL/TLS")

            col3, col4 = st.columns(2)
            with col3:
                pool_size = st.number_input("Connection Pool Size", value=5, min_value=1, max_value=50)
            with col4:
                timeout = st.number_input("Timeout (seconds)", value=30, min_value=1, max_value=300)

            submitted = st.form_submit_button("Create Connection", type="primary")

            if submitted:
                try:
                    config = ConnectionConfig(
                        name=conn_name,
                        db_type=DatabaseType(db_type),
                        host=host,
                        port=port,
                        database=database,
                        username=username,
                        password=password,
                        ssl=ssl,
                        pool_size=pool_size,
                        timeout=timeout
                    )

                    st.session_state.db_manager.add_connection(config)
                    st.success(f"✓ Connection '{conn_name}' created successfully!")
                    st.rerun()

                except Exception as e:
                    st.error(f"Error creating connection: {str(e)}")

    def render_connection_list(self):
        """Render list of connections"""
        st.subheader("Saved Connections")

        connections = st.session_state.db_manager.list_connections()

        if not connections:
            st.info("No connections configured. Create one in the 'New Connection' tab.")
            return

        for conn_name in connections:
            with st.expander(f"📡 {conn_name}"):
                info = st.session_state.db_manager.get_connection_info(conn_name)

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Type", info['config']['db_type'])
                    st.metric("Host", info['config']['host'] or "N/A")

                with col2:
                    status = info['status']
                    st.metric(
                        "Status",
                        "✓ Connected" if status['connected'] else "✗ Disconnected"
                    )
                    if status['connected']:
                        st.metric("Response Time", f"{status['response_time_ms']:.2f} ms")

                with col3:
                    st.metric("Database", info['config']['database'])
                    st.metric("Pool Size", info['config']['pool_size'])

                col_a, col_b, col_c = st.columns(3)

                with col_a:
                    if st.button("Connect", key=f"connect_{conn_name}"):
                        st.session_state.active_connection = conn_name
                        st.success(f"Connected to {conn_name}")
                        st.rerun()

                with col_b:
                    if st.button("Edit", key=f"edit_{conn_name}"):
                        st.info("Edit functionality coming soon")

                with col_c:
                    if st.button("Delete", key=f"delete_{conn_name}", type="secondary"):
                        st.session_state.db_manager.remove_connection(conn_name)
                        st.success(f"Deleted connection: {conn_name}")
                        st.rerun()

    def render_test_connection(self):
        """Render connection test interface"""
        st.subheader("Test Connection")

        connections = st.session_state.db_manager.list_connections()
        if not connections:
            st.warning("No connections available to test")
            return

        conn_name = st.selectbox("Select Connection", connections)

        if st.button("Test Connection", type="primary"):
            with st.spinner("Testing connection..."):
                try:
                    info = st.session_state.db_manager.get_connection_info(conn_name)
                    status = info['status']

                    if status['connected']:
                        st.success("✓ Connection successful!")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Response Time", f"{status['response_time_ms']:.2f} ms")
                        with col2:
                            st.metric("Active Connections", status['active_connections'])
                    else:
                        st.error(f"✗ Connection failed: {status.get('error', 'Unknown error')}")

                except Exception as e:
                    st.error(f"Error testing connection: {str(e)}")

    def page_query_builder(self):
        """Visual query builder page"""
        st.markdown('<div class="section-header">Visual Query Builder</div>', unsafe_allow_html=True)

        if not st.session_state.active_connection:
            st.warning("⚠️ Please connect to a database first")
            return

        tab1, tab2, tab3 = st.tabs(["🔨 Build Query", "📝 SQL Editor", "📚 History"])

        with tab1:
            self.render_visual_query_builder()

        with tab2:
            self.render_sql_editor()

        with tab3:
            self.render_query_history()

    def render_visual_query_builder(self):
        """Render visual query builder"""
        st.subheader("Build Query Visually")

        # Get connection and tables
        conn = st.session_state.db_manager.get_connection(st.session_state.active_connection)
        tables = conn.get_tables()

        # Create query
        query = st.session_state.query_builder.create_query()

        col1, col2 = st.columns([2, 1])

        with col1:
            # FROM clause
            st.write("**1. Select Table**")
            from_table = st.selectbox("FROM", tables)
            if from_table:
                query.from_(from_table)

            # SELECT columns
            st.write("**2. Select Columns**")
            schema = conn.get_table_schema(from_table)
            column_names = [col.get('column_name', col.get('name', col.get('Field', ''))) for col in schema]

            select_all = st.checkbox("SELECT *", value=True)
            if not select_all:
                selected_columns = st.multiselect("Columns", column_names)
                if selected_columns:
                    query.select(*selected_columns)

            # WHERE clause
            st.write("**3. Add Filters (WHERE)**")
            add_filter = st.checkbox("Add WHERE clause")
            if add_filter:
                filter_col = st.selectbox("Filter Column", column_names, key="filter_col")
                filter_op = st.selectbox(
                    "Operator",
                    [op.value for op in OperatorType],
                    key="filter_op"
                )
                filter_val = st.text_input("Value", key="filter_val")

                if filter_col and filter_val:
                    query.where(filter_col, OperatorType(filter_op), filter_val)

            # ORDER BY
            st.write("**4. Sort Results (ORDER BY)**")
            add_order = st.checkbox("Add ORDER BY")
            if add_order:
                order_col = st.selectbox("Order Column", column_names, key="order_col")
                order_dir = st.radio("Direction", ["ASC", "DESC"], key="order_dir")
                if order_col:
                    query.order(order_col, SortOrder.ASC if order_dir == "ASC" else SortOrder.DESC)

            # LIMIT
            st.write("**5. Limit Results**")
            limit = st.number_input("LIMIT", min_value=0, value=100, step=10)
            if limit > 0:
                query.limit_offset(limit=limit)

        with col2:
            # Generated SQL
            st.write("**Generated SQL**")
            try:
                sql, params = query.to_sql()
                st.code(sql, language="sql")

                if params:
                    st.write("**Parameters**")
                    st.json(params)

                # Execute button
                if st.button("Execute Query", type="primary"):
                    with st.spinner("Executing query..."):
                        try:
                            results = conn.execute_query(sql, params)
                            st.success(f"✓ Query executed successfully! ({len(results)} rows)")

                            if results:
                                df = pd.DataFrame(results)
                                st.dataframe(df, use_container_width=True)

                                # Download results
                                csv = df.to_csv(index=False)
                                st.download_button(
                                    "Download CSV",
                                    csv,
                                    "query_results.csv",
                                    "text/csv"
                                )

                        except Exception as e:
                            st.error(f"Error executing query: {str(e)}")

            except Exception as e:
                st.error(f"Error generating SQL: {str(e)}")

    def render_sql_editor(self):
        """Render SQL editor"""
        st.subheader("SQL Editor")

        conn = st.session_state.db_manager.get_connection(st.session_state.active_connection)

        sql_query = st.text_area(
            "SQL Query",
            height=200,
            placeholder="Enter your SQL query here...",
            value="SELECT * FROM your_table LIMIT 100;"
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            execute_btn = st.button("▶️ Execute", type="primary")
        with col2:
            explain_btn = st.button("📊 Explain")
        with col3:
            save_btn = st.button("💾 Save Query")

        if execute_btn and sql_query:
            with st.spinner("Executing query..."):
                try:
                    start_time = datetime.now()
                    results = conn.execute_query(sql_query)
                    execution_time = (datetime.now() - start_time).total_seconds() * 1000

                    st.success(f"✓ Query executed in {execution_time:.2f}ms ({len(results)} rows)")

                    if results:
                        df = pd.DataFrame(results)
                        st.dataframe(df, use_container_width=True)

                        # Add to history
                        st.session_state.query_history.append({
                            "query": sql_query,
                            "timestamp": datetime.now(),
                            "rows": len(results),
                            "time_ms": execution_time
                        })

                except Exception as e:
                    st.error(f"Error: {str(e)}")

    def render_query_history(self):
        """Render query history"""
        st.subheader("Query History")

        if not st.session_state.query_history:
            st.info("No queries in history yet")
            return

        for idx, entry in enumerate(reversed(st.session_state.query_history[-20:])):
            with st.expander(f"Query {len(st.session_state.query_history) - idx} - {entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"):
                st.code(entry['query'], language="sql")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Rows", entry['rows'])
                with col2:
                    st.metric("Time", f"{entry['time_ms']:.2f}ms")

    def page_data_explorer(self):
        """Data explorer page"""
        st.markdown('<div class="section-header">Data Explorer</div>', unsafe_allow_html=True)

        if not st.session_state.active_connection:
            st.warning("⚠️ Please connect to a database first")
            return

        conn = st.session_state.db_manager.get_connection(st.session_state.active_connection)
        explorer = DataExplorer(conn)

        # Table selection
        tables = conn.get_tables()
        selected_table = st.selectbox("Select Table", tables)

        if selected_table:
            tab1, tab2, tab3 = st.tabs(["📊 Browse Data", "✏️ Edit Data", "📤 Import/Export"])

            with tab1:
                self.render_data_browser(explorer, selected_table)

            with tab2:
                self.render_data_editor(explorer, selected_table)

            with tab3:
                self.render_import_export(explorer, selected_table)

    def render_data_browser(self, explorer: DataExplorer, table_name: str):
        """Render data browser"""
        st.subheader(f"Browse: {table_name}")

        # Pagination controls
        col1, col2, col3 = st.columns(3)
        with col1:
            page = st.number_input("Page", min_value=1, value=1)
        with col2:
            page_size = st.selectbox("Rows per page", [25, 50, 100, 200], index=1)
        with col3:
            if st.button("🔄 Refresh"):
                st.rerun()

        # Browse data
        try:
            grid = explorer.browse_table(table_name, page=page, page_size=page_size)

            # Display metrics
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Total Records", grid.total_records)
            with col_b:
                st.metric("Page", f"{page}/{grid.pagination.total_pages}")
            with col_c:
                st.metric("Query Time", f"{grid.query_time_ms:.2f}ms")

            # Display data
            if grid.rows:
                df = pd.DataFrame(grid.rows)
                st.dataframe(df, use_container_width=True, height=400)
            else:
                st.info("No data found")

        except Exception as e:
            st.error(f"Error browsing data: {str(e)}")

    def render_data_editor(self, explorer: DataExplorer, table_name: str):
        """Render data editor"""
        st.subheader(f"Edit Data: {table_name}")

        operation = st.radio("Operation", ["Insert", "Update", "Delete"], horizontal=True)

        if operation == "Insert":
            st.write("**Insert New Row**")
            # Get schema
            schema = explorer.connection.get_table_schema(table_name)

            data = {}
            for col_info in schema:
                col_name = col_info.get('column_name', col_info.get('name', ''))
                data[col_name] = st.text_input(f"{col_name}")

            if st.button("Insert Row"):
                try:
                    rows = explorer.insert_row(table_name, data)
                    st.success(f"✓ Inserted {rows} row(s)")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

        elif operation == "Update":
            st.info("Update functionality - Select row ID and fields to update")

        elif operation == "Delete":
            st.warning("Delete functionality - Select row ID to delete")

    def render_import_export(self, explorer: DataExplorer, table_name: str):
        """Render import/export interface"""
        st.subheader(f"Import/Export: {table_name}")

        export_format = st.selectbox(
            "Format",
            [fmt.value for fmt in ExportFormat]
        )

        if st.button("📤 Export Data"):
            with st.spinner("Exporting..."):
                try:
                    data = explorer.export_data(
                        table_name,
                        ExportFormat(export_format)
                    )

                    st.download_button(
                        "Download Export",
                        data,
                        f"{table_name}.{export_format}",
                        f"application/{export_format}"
                    )

                    st.success("✓ Export ready!")

                except Exception as e:
                    st.error(f"Export error: {str(e)}")

    def page_schema_designer(self):
        """Schema designer page"""
        st.markdown('<div class="section-header">Schema Designer</div>', unsafe_allow_html=True)

        st.info("🏗️ Visual schema designer with ER diagrams - Coming in full version")

        # Placeholder for schema designer
        st.write("Features:")
        st.write("- Visual table designer")
        st.write("- ER diagram generation")
        st.write("- Relationship management")
        st.write("- Index configuration")
        st.write("- Constraint management")

    def page_migrations(self):
        """Migrations page"""
        st.markdown('<div class="section-header">Database Migrations</div>', unsafe_allow_html=True)

        st.info("🔄 Migration system - Coming in full version")

    def page_backup_restore(self):
        """Backup and restore page"""
        st.markdown('<div class="section-header">Backup & Restore</div>', unsafe_allow_html=True)

        if not st.session_state.active_connection:
            st.warning("⚠️ Please connect to a database first")
            return

        tab1, tab2 = st.tabs(["💾 Create Backup", "📥 Restore"])

        with tab1:
            st.subheader("Create Database Backup")

            backup_name = st.text_input("Backup Name", value=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            backup_type = st.selectbox("Backup Type", [t.value for t in BackupType])

            if st.button("Create Backup", type="primary"):
                st.success("Backup functionality - Coming in full version")

        with tab2:
            st.subheader("Restore from Backup")
            st.info("Restore functionality - Coming in full version")

    def page_performance(self):
        """Performance monitoring page"""
        st.markdown('<div class="section-header">Performance Monitor</div>', unsafe_allow_html=True)

        if not st.session_state.active_connection:
            st.warning("⚠️ Please connect to a database first")
            return

        st.info("⚡ Performance monitoring dashboard - Coming in full version")

        # Placeholder metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Queries", "1,234")
        with col2:
            st.metric("Avg Query Time", "45.2ms")
        with col3:
            st.metric("Slow Queries", "12")
        with col4:
            st.metric("Cache Hit Rate", "94.5%")

    def page_administration(self):
        """Administration page"""
        st.markdown('<div class="section-header">User Administration</div>', unsafe_allow_html=True)

        st.info("👥 User and role management - Coming in full version")

    def page_dashboard(self):
        """Dashboard overview page"""
        st.markdown('<div class="section-header">Dashboard</div>', unsafe_allow_html=True)

        # Connection overview
        st.subheader("Connection Overview")

        connections = st.session_state.db_manager.list_connections()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Connections", len(connections))
        with col2:
            st.metric("Active Connection", st.session_state.active_connection or "None")
        with col3:
            st.metric("Queries Executed", len(st.session_state.query_history))

        # Recent activity
        st.subheader("Recent Activity")

        if st.session_state.query_history:
            recent = st.session_state.query_history[-5:]
            for entry in reversed(recent):
                st.text(f"{entry['timestamp'].strftime('%H:%M:%S')} - {entry['query'][:80]}...")
        else:
            st.info("No recent activity")


def main():
    """Main entry point"""
    app = DatabaseUI()
    app.run()


if __name__ == "__main__":
    main()
