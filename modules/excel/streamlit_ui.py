"""Beautiful Streamlit UI for Excel module."""
import streamlit as st
import pandas as pd
from typing import Optional
from core.database.session import get_db_session
from core.auth.middleware import require_auth
from .editor import SpreadsheetEditor
from .cell_manager import CellStyle, HorizontalAlignment, VerticalAlignment, NumberFormat
from .data_validator import ValidationRule, ValidationType, ValidationOperator
from .chart_builder import ChartConfig, ChartType
from .pivot_table import PivotTableBuilder
from .models import Spreadsheet
import plotly.express as px


# Custom CSS for beautiful UI
CUSTOM_CSS = """
<style>
    .excel-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }

    .excel-title {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
    }

    .excel-subtitle {
        font-size: 1.2rem;
        opacity: 0.9;
    }

    .toolbar {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }

    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }

    .stat-value {
        font-size: 2rem;
        font-weight: bold;
        color: #667eea;
    }

    .stat-label {
        color: #6c757d;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }

    .ai-panel {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
    }

    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #28a745;
    }

    .error-message {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #dc3545;
    }

    .stButton>button {
        border-radius: 5px;
        font-weight: 500;
    }
</style>
"""


@require_auth
def render_excel_page():
    """Main Excel module page."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="excel-header">
        <div class="excel-title">📊 Excel Spreadsheet Editor</div>
        <div class="excel-subtitle">World-class spreadsheet with AI-powered features</div>
    </div>
    """, unsafe_allow_html=True)

    # Initialize session state
    if 'excel_editor' not in st.session_state:
        st.session_state.excel_editor = None
    if 'current_sheet_id' not in st.session_state:
        st.session_state.current_sheet_id = None

    # Sidebar navigation
    with st.sidebar:
        st.header("📁 Spreadsheets")

        action = st.radio(
            "Action",
            ["📝 Create New", "📂 Open Existing", "📤 Import File"],
            label_visibility="collapsed"
        )

        if action == "📝 Create New":
            _render_create_new()
        elif action == "📂 Open Existing":
            _render_open_existing()
        elif action == "📤 Import File":
            _render_import_file()

        st.divider()

        # Show current spreadsheet info
        if st.session_state.excel_editor:
            editor = st.session_state.excel_editor
            st.success(f"📊 {editor.spreadsheet.name}")

            if st.button("💾 Save", use_container_width=True):
                editor.save()
                st.success("Saved successfully!")

            if st.button("📥 Export", use_container_width=True):
                st.session_state.show_export = True

    # Main content
    if st.session_state.excel_editor:
        _render_editor()
    else:
        _render_welcome()


def _render_welcome():
    """Render welcome screen."""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-value">∞</div>
            <div class="stat-label">Rows & Columns</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-value">200+</div>
            <div class="stat-label">Excel Functions</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-value">AI</div>
            <div class="stat-label">Powered Analysis</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Features
    st.subheader("✨ Features")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Core Features:**
        - 📊 Infinite grid with cell editing
        - 🔢 200+ Excel-compatible formulas
        - 🎨 Rich formatting options
        - 📈 Advanced charts & visualizations
        - 🔄 Pivot tables & data analysis
        - ✅ Data validation
        """)

    with col2:
        st.markdown("""
        **Advanced Features:**
        - 🤖 AI-powered data analysis
        - 👥 Real-time collaboration
        - 📤 Import/Export (Excel, CSV, JSON)
        - 🎯 Conditional formatting
        - ⏮️ Unlimited undo/redo
        - 📝 Version history
        """)


def _render_create_new():
    """Render create new spreadsheet form."""
    with st.form("create_new_spreadsheet"):
        name = st.text_input("Spreadsheet Name", placeholder="My Spreadsheet")
        description = st.text_area("Description (optional)")

        col1, col2 = st.columns(2)
        with col1:
            rows = st.number_input("Initial Rows", min_value=10, max_value=10000, value=100)
        with col2:
            cols = st.number_input("Initial Columns", min_value=5, max_value=100, value=26)

        submit = st.form_submit_button("Create Spreadsheet", use_container_width=True)

        if submit and name:
            with get_db_session() as db:
                editor = SpreadsheetEditor(db, st.session_state.user_id)
                editor.create_new(name, rows=int(rows), cols=int(cols), description=description)
                st.session_state.excel_editor = editor
                st.session_state.current_sheet_id = editor.spreadsheet_id
                st.success(f"Created '{name}' successfully!")
                st.rerun()


def _render_open_existing():
    """Render open existing spreadsheet."""
    with get_db_session() as db:
        spreadsheets = db.query(Spreadsheet).filter_by(
            user_id=st.session_state.user_id,
            is_active=True
        ).order_by(Spreadsheet.updated_at.desc()).all()

        if not spreadsheets:
            st.info("No spreadsheets found. Create a new one!")
            return

        for sheet in spreadsheets:
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{sheet.name}**")
                    st.caption(f"Updated: {sheet.updated_at.strftime('%Y-%m-%d %H:%M')}")
                with col2:
                    if st.button("Open", key=f"open_{sheet.id}"):
                        editor = SpreadsheetEditor(db, st.session_state.user_id, sheet.id)
                        st.session_state.excel_editor = editor
                        st.session_state.current_sheet_id = sheet.id
                        st.rerun()
                st.divider()


def _render_import_file():
    """Render import file interface."""
    uploaded_file = st.file_uploader(
        "Upload Spreadsheet",
        type=['xlsx', 'xls', 'csv', 'json'],
        help="Upload an Excel, CSV, or JSON file"
    )

    if uploaded_file:
        name = st.text_input("Spreadsheet Name", value=uploaded_file.name.split('.')[0])

        if st.button("Import", use_container_width=True):
            with get_db_session() as db:
                editor = SpreadsheetEditor(db, st.session_state.user_id)

                # Save uploaded file temporarily
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name

                # Create spreadsheet and import data
                editor.create_new(name)
                editor.import_file(tmp_path)
                editor.save()

                st.session_state.excel_editor = editor
                st.session_state.current_sheet_id = editor.spreadsheet_id
                st.success("Imported successfully!")
                st.rerun()


def _render_editor():
    """Render main spreadsheet editor."""
    editor: SpreadsheetEditor = st.session_state.excel_editor

    # Toolbar
    st.markdown('<div class="toolbar">', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📝 Edit",
        "📊 Charts",
        "🔄 Pivot",
        "🤖 AI Assistant",
        "⚙️ Tools",
        "📋 Data"
    ])

    with tab1:
        _render_edit_tab(editor)

    with tab2:
        _render_charts_tab(editor)

    with tab3:
        _render_pivot_tab(editor)

    with tab4:
        _render_ai_tab(editor)

    with tab5:
        _render_tools_tab(editor)

    with tab6:
        _render_data_tab(editor)

    st.markdown('</div>', unsafe_allow_html=True)


def _render_edit_tab(editor: SpreadsheetEditor):
    """Render edit tab with cell editing."""
    st.subheader("📝 Edit Data")

    # Get current data
    df = editor.cell_manager.to_dataframe()

    # Show data editor
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        height=600,
        key="data_editor"
    )

    # Update data if changed
    if not df.equals(edited_df):
        editor.cell_manager.from_dataframe(edited_df)
        st.success("Data updated!")

    # Formula bar
    st.divider()
    col1, col2 = st.columns([3, 1])
    with col1:
        formula = st.text_input("Formula", placeholder="=SUM(A1:A10)", key="formula_input")
    with col2:
        if st.button("Apply Formula"):
            try:
                result = editor.formula_engine.evaluate(formula)
                st.success(f"Result: {result}")
            except Exception as e:
                st.error(f"Error: {str(e)}")


def _render_charts_tab(editor: SpreadsheetEditor):
    """Render charts tab."""
    st.subheader("📊 Create Charts")

    df = editor.cell_manager.to_dataframe()

    if df.empty:
        st.info("Add data to create charts")
        return

    # Chart configuration
    chart_type = st.selectbox(
        "Chart Type",
        ["Line", "Bar", "Column", "Pie", "Scatter", "Area"]
    )

    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    all_cols = df.columns.tolist()

    x_axis = st.selectbox("X-Axis", all_cols)
    y_axis = st.multiselect("Y-Axis", numeric_cols, default=numeric_cols[:1] if numeric_cols else [])

    title = st.text_input("Chart Title", value=f"{chart_type} Chart")

    if st.button("Create Chart") and y_axis:
        config = ChartConfig(
            chart_type=ChartType(chart_type.lower()),
            title=title,
            x_axis=x_axis,
            y_axis=y_axis
        )

        try:
            fig = editor.create_chart(config)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating chart: {str(e)}")


def _render_pivot_tab(editor: SpreadsheetEditor):
    """Render pivot table tab."""
    st.subheader("🔄 Create Pivot Table")

    df = editor.cell_manager.to_dataframe()

    if df.empty:
        st.info("Add data to create pivot tables")
        return

    all_cols = df.columns.tolist()
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()

    # Pivot configuration
    rows = st.multiselect("Rows", all_cols)
    columns = st.multiselect("Columns", all_cols)
    values = st.multiselect("Values", numeric_cols)

    if st.button("Create Pivot Table") and rows and values:
        builder = PivotTableBuilder()

        for row in rows:
            builder.add_row_field(row)
        for col in columns:
            builder.add_column_field(col)
        for val in values:
            builder.add_value_field(val, 'sum')

        config = builder.with_margins(True).build()

        try:
            pivot_result = editor.create_pivot_table(config)
            st.dataframe(pivot_result, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating pivot table: {str(e)}")


def _render_ai_tab(editor: SpreadsheetEditor):
    """Render AI assistant tab."""
    st.markdown("""
    <div class="ai-panel">
        <h3>🤖 AI Assistant</h3>
        <p>Ask questions about your data or get intelligent suggestions</p>
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    # AI Query
    query = st.text_area(
        "Ask AI about your data",
        placeholder="e.g., What are the top 10 values? Show me trends. Find anomalies.",
        height=100
    )

    if st.button("Ask AI", use_container_width=True):
        if query:
            with st.spinner("AI is analyzing..."):
                try:
                    insights = editor.get_ai_insights(query)

                    st.success("✨ AI Analysis Complete")

                    if 'answer' in insights:
                        st.write("**Answer:**")
                        st.write(insights['answer'])

                    if 'insights' in insights and insights['insights']:
                        st.write("**Insights:**")
                        for insight in insights['insights']:
                            st.write(f"• {insight}")

                    if 'suggestions' in insights and insights['suggestions']:
                        st.write("**Suggestions:**")
                        for suggestion in insights['suggestions']:
                            st.write(f"• {suggestion}")

                except Exception as e:
                    st.error(f"AI Error: {str(e)}")

    st.divider()

    # Formula suggestion
    st.subheader("💡 Formula Generator")
    formula_desc = st.text_input(
        "Describe the formula you need",
        placeholder="e.g., sum of all values in column A"
    )

    if st.button("Generate Formula"):
        if formula_desc:
            try:
                formula = editor.get_ai_formula_suggestion(formula_desc)
                st.code(formula, language="excel")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    # Data cleaning suggestions
    st.divider()
    st.subheader("🧹 Data Cleaning")

    if st.button("Get Cleaning Suggestions"):
        try:
            suggestions = editor.get_data_cleaning_suggestions()
            if suggestions:
                for suggestion in suggestions:
                    st.write(f"**{suggestion.get('priority', 'medium').upper()}**: {suggestion.get('issue', '')}")
                    st.write(f"→ {suggestion.get('suggestion', '')}")
                    st.write("")
            else:
                st.success("Your data looks clean!")
        except Exception as e:
            st.error(f"Error: {str(e)}")


def _render_tools_tab(editor: SpreadsheetEditor):
    """Render tools tab."""
    st.subheader("⚙️ Data Tools")

    tool = st.selectbox(
        "Select Tool",
        ["Sort", "Filter", "Find & Replace", "Remove Duplicates", "Data Validation"]
    )

    if tool == "Sort":
        _render_sort_tool(editor)
    elif tool == "Filter":
        _render_filter_tool(editor)
    elif tool == "Find & Replace":
        _render_find_replace_tool(editor)
    elif tool == "Remove Duplicates":
        _render_remove_duplicates_tool(editor)
    elif tool == "Data Validation":
        _render_data_validation_tool(editor)


def _render_sort_tool(editor: SpreadsheetEditor):
    """Render sort tool."""
    df = editor.cell_manager.to_dataframe()

    if df.empty:
        st.info("No data to sort")
        return

    col = st.selectbox("Sort by Column", range(len(df.columns)))
    ascending = st.radio("Order", ["Ascending", "Descending"]) == "Ascending"

    if st.button("Sort"):
        editor.sort_data([col], [ascending])
        st.success("Data sorted!")
        st.rerun()


def _render_filter_tool(editor: SpreadsheetEditor):
    """Render filter tool."""
    st.info("Use the data editor to filter rows visually")


def _render_find_replace_tool(editor: SpreadsheetEditor):
    """Render find & replace tool."""
    col1, col2 = st.columns(2)

    with col1:
        find_text = st.text_input("Find")
    with col2:
        replace_text = st.text_input("Replace with")

    case_sensitive = st.checkbox("Case sensitive")

    if st.button("Replace All"):
        if find_text:
            editor.find_replace(find_text, replace_text, case_sensitive=case_sensitive)
            st.success(f"Replaced '{find_text}' with '{replace_text}'")
            st.rerun()


def _render_remove_duplicates_tool(editor: SpreadsheetEditor):
    """Render remove duplicates tool."""
    if st.button("Remove Duplicate Rows"):
        from .data_tools import DataTools
        df = editor.cell_manager.to_dataframe()
        cleaned_df = DataTools.remove_duplicates(df)
        editor.cell_manager.from_dataframe(cleaned_df)
        st.success("Duplicates removed!")
        st.rerun()


def _render_data_validation_tool(editor: SpreadsheetEditor):
    """Render data validation tool."""
    st.write("Add validation rules to cells")
    st.info("Select a cell range and create a validation rule")


def _render_data_tab(editor: SpreadsheetEditor):
    """Render data tab with statistics."""
    st.subheader("📋 Data Overview")

    df = editor.cell_manager.to_dataframe()

    # Statistics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Rows", len(df))
    with col2:
        st.metric("Columns", len(df.columns))
    with col3:
        st.metric("Cells", len(df) * len(df.columns))
    with col4:
        st.metric("Non-empty", df.count().sum())

    # Data types
    st.divider()
    st.subheader("Data Types")
    st.dataframe(df.dtypes.to_frame('Type'), use_container_width=True)

    # Statistics for numeric columns
    numeric_df = df.select_dtypes(include=['number'])
    if not numeric_df.empty:
        st.divider()
        st.subheader("Numeric Statistics")
        st.dataframe(numeric_df.describe(), use_container_width=True)
