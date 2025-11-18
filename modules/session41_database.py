"""
Session 41: Database Manager
Features: Visual designer, query builder, schema management, AI-powered queries
"""
import streamlit as st
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.ai_assistant import ai_assistant
from utils.storage import storage


class DatabaseManager:
    """Database Manager with visual designer and query builder"""

    def __init__(self):
        """Initialize database manager"""
        if 'databases' not in st.session_state:
            st.session_state.databases = self.load_databases()
        if 'current_db' not in st.session_state:
            st.session_state.current_db = None

    def load_databases(self) -> List[Dict]:
        """Load saved databases"""
        databases = []
        files = storage.list_files('databases', '.json')
        for file in files:
            data = storage.load_json(file, 'databases')
            if data:
                databases.append(data)
        return databases

    def save_database(self, db: Dict) -> bool:
        """Save database"""
        filename = f"database_{db['id']}.json"
        return storage.save_json(filename, db, 'databases')

    def create_database(self, name: str) -> Dict:
        """Create new database"""
        return {
            'id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'name': name,
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat(),
            'tables': [],
            'queries': [],
            'relationships': []
        }

    def render(self):
        """Render database manager"""
        st.title("🗄️ Database Manager")
        st.markdown("*Visual designer, query builder, and schema management*")

        # Sidebar
        with st.sidebar:
            st.header("Database Manager")

            with st.expander("➕ New Database", expanded=False):
                new_name = st.text_input("Database Name", key="new_db_name")
                if st.button("Create Database", type="primary"):
                    if new_name:
                        db = self.create_database(new_name)
                        st.session_state.databases.append(db)
                        st.session_state.current_db = db
                        self.save_database(db)
                        st.success(f"Created '{new_name}'")
                        st.rerun()

            if st.session_state.databases:
                st.subheader("Databases")
                for db in st.session_state.databases:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.button(db['name'], key=f"load_{db['id']}"):
                            st.session_state.current_db = db
                            st.rerun()
                    with col2:
                        if st.button("🗑️", key=f"del_{db['id']}"):
                            storage.delete_file(f"database_{db['id']}.json", 'databases')
                            st.session_state.databases.remove(db)
                            st.rerun()

        if st.session_state.current_db:
            db = st.session_state.current_db

            tabs = st.tabs(["📋 Schema Designer", "🔍 Query Builder", "📊 Data Viewer", "🤖 AI Assistant"])

            with tabs[0]:
                st.subheader(f"Database: {db['name']}")

                with st.expander("➕ Add Table", expanded=True):
                    table_name = st.text_input("Table Name")
                    if st.button("Create Table"):
                        if table_name:
                            db['tables'].append({
                                'name': table_name,
                                'columns': [],
                                'data': []
                            })
                            self.save_database(db)
                            st.success(f"Table '{table_name}' created!")
                            st.rerun()

                if db['tables']:
                    for t_idx, table in enumerate(db['tables']):
                        with st.expander(f"📊 {table['name']}"):
                            # Add column
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                col_name = st.text_input("Column Name", key=f"col_name_{t_idx}")
                            with col2:
                                col_type = st.selectbox(
                                    "Type",
                                    ["INTEGER", "TEXT", "REAL", "BOOLEAN", "DATE"],
                                    key=f"col_type_{t_idx}"
                                )
                            with col3:
                                st.write("")
                                st.write("")
                                if st.button("Add Column", key=f"add_col_{t_idx}"):
                                    if col_name:
                                        table['columns'].append({
                                            'name': col_name,
                                            'type': col_type
                                        })
                                        self.save_database(db)
                                        st.rerun()

                            # Show columns
                            if table['columns']:
                                st.markdown("**Columns:**")
                                for c_idx, col in enumerate(table['columns']):
                                    col_a, col_b = st.columns([3, 1])
                                    with col_a:
                                        st.write(f"• {col['name']} ({col['type']})")
                                    with col_b:
                                        if st.button("❌", key=f"del_col_{t_idx}_{c_idx}"):
                                            table['columns'].pop(c_idx)
                                            self.save_database(db)
                                            st.rerun()

                            if st.button("🗑️ Delete Table", key=f"del_table_{t_idx}"):
                                db['tables'].pop(t_idx)
                                self.save_database(db)
                                st.rerun()

            with tabs[1]:
                st.subheader("🔍 Query Builder")

                query_type = st.selectbox("Query Type", ["SELECT", "INSERT", "UPDATE", "DELETE"])

                if query_type == "SELECT":
                    if db['tables']:
                        table = st.selectbox("Table", [t['name'] for t in db['tables']])
                        selected_table = next(t for t in db['tables'] if t['name'] == table)

                        if selected_table['columns']:
                            columns = st.multiselect(
                                "Columns",
                                [c['name'] for c in selected_table['columns']],
                                default=[c['name'] for c in selected_table['columns']]
                            )

                            where_clause = st.text_input("WHERE clause (optional)")
                            order_by = st.text_input("ORDER BY (optional)")
                            limit = st.number_input("LIMIT", 0, 1000, 0)

                            # Build query
                            cols_str = ", ".join(columns) if columns else "*"
                            query = f"SELECT {cols_str} FROM {table}"
                            if where_clause:
                                query += f" WHERE {where_clause}"
                            if order_by:
                                query += f" ORDER BY {order_by}"
                            if limit > 0:
                                query += f" LIMIT {limit}"

                            st.code(query, language='sql')

                            if st.button("💾 Save Query"):
                                db['queries'].append({
                                    'name': f"Query_{len(db['queries'])+1}",
                                    'sql': query,
                                    'created': datetime.now().isoformat()
                                })
                                self.save_database(db)
                                st.success("Query saved!")

                # Saved queries
                if db['queries']:
                    st.markdown("### 📝 Saved Queries")
                    for idx, query in enumerate(db['queries']):
                        with st.expander(query['name']):
                            st.code(query['sql'], language='sql')
                            if st.button("🗑️ Delete", key=f"del_query_{idx}"):
                                db['queries'].pop(idx)
                                self.save_database(db)
                                st.rerun()

            with tabs[2]:
                st.subheader("📊 Data Viewer")

                if db['tables']:
                    table_name = st.selectbox("Select Table", [t['name'] for t in db['tables']], key="data_viewer_table")
                    selected_table = next(t for t in db['tables'] if t['name'] == table_name)

                    if selected_table['columns']:
                        # Add data
                        with st.expander("➕ Add Row"):
                            row_data = {}
                            cols = st.columns(len(selected_table['columns']))
                            for idx, col in enumerate(selected_table['columns']):
                                with cols[idx]:
                                    row_data[col['name']] = st.text_input(col['name'], key=f"data_{col['name']}")

                            if st.button("Add Row"):
                                selected_table['data'].append(row_data)
                                self.save_database(db)
                                st.success("Row added!")
                                st.rerun()

                        # Display data
                        if selected_table['data']:
                            df = pd.DataFrame(selected_table['data'])
                            st.dataframe(df, use_container_width=True)

                            # Export
                            csv = df.to_csv(index=False)
                            st.download_button(
                                "📥 Download CSV",
                                csv,
                                file_name=f"{table_name}.csv",
                                mime="text/csv"
                            )
                        else:
                            st.info("No data yet. Add rows to see data.")
                    else:
                        st.info("Add columns first!")
                else:
                    st.info("Create a table first!")

            with tabs[3]:
                st.subheader("🤖 AI Query Assistant")

                natural_query = st.text_area("Describe what you want to query in plain English")

                # Schema context
                schema_info = "\n".join([
                    f"Table: {table['name']}\nColumns: {', '.join([c['name'] + ' (' + c['type'] + ')' for c in table['columns']])}"
                    for table in db['tables']
                ])

                if st.button("✨ Generate SQL"):
                    if natural_query and schema_info:
                        with st.spinner("Generating SQL..."):
                            sql = ai_assistant.generate_sql_query(natural_query, schema_info)
                            st.code(sql, language='sql')

                            if st.button("💾 Save Generated Query"):
                                db['queries'].append({
                                    'name': f"AI_Query_{len(db['queries'])+1}",
                                    'sql': sql,
                                    'created': datetime.now().isoformat()
                                })
                                self.save_database(db)
                                st.success("Query saved!")

        else:
            st.info("👈 Create or select a database to get started")


def main():
    """Main entry point"""
    manager = DatabaseManager()
    manager.render()


if __name__ == "__main__":
    main()
