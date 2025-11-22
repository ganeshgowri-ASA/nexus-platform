"""
Streamlit UI for Testing & QA Module
"""
import streamlit as st
import requests
import pandas as pd
<<<<<<< HEAD
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

# Configuration
API_BASE_URL = "http://localhost:8002"

st.set_page_config(
    page_title="NEXUS Testing & QA",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #4CAF50;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stButton>button {
        width: 100%;
    }
    .status-passed {
        color: #4CAF50;
        font-weight: bold;
    }
    .status-failed {
        color: #F44336;
        font-weight: bold;
    }
    .status-running {
        color: #2196F3;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)


def main():
    st.markdown('<div class="main-header">🧪 NEXUS Testing & QA</div>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80/4CAF50/FFFFFF?text=NEXUS", use_column_width=True)
        st.markdown("---")

        page = st.radio(
            "Navigation",
            ["🏠 Dashboard", "📋 Test Suites", "🧪 Test Cases", "🚀 Test Runs", "🐛 Defects", "📊 Analytics"],
            label_visibility="collapsed"
        )

        st.markdown("---")
        st.markdown("### Settings")
        user_id = st.number_input("User ID", min_value=1, value=1)

    # Page routing
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "📋 Test Suites":
        show_test_suites(user_id)
    elif page == "🧪 Test Cases":
        show_test_cases(user_id)
    elif page == "🚀 Test Runs":
        show_test_runs(user_id)
    elif page == "🐛 Defects":
        show_defects(user_id)
    elif page == "📊 Analytics":
        show_analytics()


def show_dashboard():
    """Dashboard overview"""
    st.markdown("### 📊 Testing Dashboard")

    try:
        response = requests.get(f"{API_BASE_URL}/analytics?days=7")
        if response.status_code == 200:
            data = response.json()

            # Key metrics
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                st.metric("Test Cases", data['total_test_cases'])

            with col2:
                st.metric("Test Runs (7d)", data['total_test_runs'])

            with col3:
                st.metric("Pass Rate", f"{data['test_pass_rate']:.1f}%")

            with col4:
                st.metric("Defects (7d)", data['total_defects'])

            with col5:
                avg_time = data.get('average_execution_time')
                if avg_time:
                    st.metric("Avg Execution", f"{avg_time:.2f}s")
                else:
                    st.metric("Avg Execution", "N/A")

            st.markdown("---")

            col1, col2 = st.columns(2)

            with col1:
                # Tests by type
                if data['tests_by_type']:
                    st.markdown("#### Tests by Type")
                    type_df = pd.DataFrame(list(data['tests_by_type'].items()), columns=['Type', 'Count'])
                    fig = px.pie(type_df, values='Count', names='Type', title='Test Distribution by Type')
                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Tests by status
                if data['tests_by_status']:
                    st.markdown("#### Tests by Status")
                    status_df = pd.DataFrame(list(data['tests_by_status'].items()), columns=['Status', 'Count'])
                    fig = px.bar(status_df, x='Status', y='Count', title='Test Status Distribution')
                    st.plotly_chart(fig, use_container_width=True)

            # Defects by severity
            if data['defects_by_severity']:
                st.markdown("#### 🐛 Defects by Severity")
                severity_df = pd.DataFrame(list(data['defects_by_severity'].items()), columns=['Severity', 'Count'])
                fig = px.bar(severity_df, x='Severity', y='Count', color='Severity',
                           color_discrete_map={
                               'critical': '#D32F2F',
                               'high': '#F57C00',
                               'medium': '#FBC02D',
                               'low': '#388E3C',
                               'blocker': '#7B1FA2'
                           })
                st.plotly_chart(fig, use_container_width=True)

            # Recent failures
            if data['recent_failures']:
                st.markdown("#### ❌ Recent Test Failures")
                failures_df = pd.DataFrame(data['recent_failures'])
                st.dataframe(failures_df[['id', 'name', 'test_type', 'last_status', 'last_run_at']].head(10))

        else:
            st.error("Failed to load analytics")

    except Exception as e:
        st.info("Start the API server to see dashboard data")


def show_test_suites(user_id):
    """Test suites management"""
    st.markdown("### 📋 Test Suites")

    tab1, tab2 = st.tabs(["📝 All Suites", "➕ Create Suite"])

    with tab1:
        col1, col2 = st.columns([3, 1])

        with col1:
            filter_type = st.selectbox("Filter by Type", ["All", "unit", "integration", "e2e", "performance", "security"])

        with col2:
            if st.button("🔄 Refresh"):
                st.rerun()

        try:
            params = {}
            if filter_type != "All":
                params["test_type"] = filter_type

            response = requests.get(f"{API_BASE_URL}/suites", params=params)

            if response.status_code == 200:
                suites = response.json()

                if suites:
                    for suite in suites:
                        with st.expander(f"📦 {suite['name']} ({suite['test_type']})"):
                            col1, col2 = st.columns(2)

                            with col1:
                                st.write(f"**ID:** {suite['id']}")
                                st.write(f"**Type:** {suite['test_type']}")
                                st.write(f"**Environment:** {suite.get('environment', 'N/A')}")

                            with col2:
                                st.write(f"**Created:** {suite['created_at']}")
                                st.write(f"**Active:** {'Yes' if suite['is_active'] else 'No'}")

                            if suite.get('description'):
                                st.write(f"**Description:** {suite['description']}")

                            if suite.get('tags'):
                                st.write(f"**Tags:** {', '.join(suite['tags'])}")

                            if st.button("View Test Cases", key=f"view_cases_{suite['id']}"):
                                st.session_state['selected_suite'] = suite['id']
                                st.success(f"Selected suite: {suite['name']}")
                else:
                    st.info("No test suites found. Create your first suite!")

            else:
                st.error("Failed to load test suites")

        except Exception as e:
            st.error(f"Error: {str(e)}")

    with tab2:
        st.markdown("#### Create New Test Suite")

        with st.form("create_suite_form"):
            name = st.text_input("Suite Name*")
            description = st.text_area("Description")
            test_type = st.selectbox("Test Type*", ["unit", "integration", "e2e", "performance", "security", "regression"])
            environment = st.text_input("Environment", value="development")
            tags_input = st.text_input("Tags (comma-separated)")
            project_id = st.number_input("Project ID", min_value=0, value=0)

            submitted = st.form_submit_button("✅ Create Suite")

            if submitted:
                if name and test_type:
                    try:
                        tags = [tag.strip() for tag in tags_input.split(",")] if tags_input else []

                        payload = {
                            "name": name,
                            "description": description,
                            "test_type": test_type,
                            "environment": environment,
                            "tags": tags,
                            "project_id": project_id if project_id > 0 else None,
                            "created_by": user_id
                        }

                        response = requests.post(f"{API_BASE_URL}/suites", json=payload)

                        if response.status_code == 200:
                            st.success("✅ Test suite created successfully!")
                            st.json(response.json())
                        else:
                            st.error(f"Error: {response.text}")

                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                else:
                    st.warning("Please fill in all required fields")


def show_test_cases(user_id):
    """Test cases management"""
    st.markdown("### 🧪 Test Cases")

    tab1, tab2 = st.tabs(["📝 All Test Cases", "➕ Create Test Case"])

    with tab1:
        col1, col2, col3 = st.columns(3)

        with col1:
            suite_filter = st.text_input("Suite ID (optional)")

        with col2:
            type_filter = st.selectbox("Type", ["All", "unit", "integration", "e2e", "performance", "security"])

        with col3:
            status_filter = st.selectbox("Status", ["All", "passed", "failed", "pending", "running", "error"])

        try:
            params = {"limit": 100}

            if suite_filter:
                params["suite_id"] = int(suite_filter)
            if type_filter != "All":
                params["test_type"] = type_filter
            if status_filter != "All":
                params["status"] = status_filter

            response = requests.get(f"{API_BASE_URL}/cases", params=params)

            if response.status_code == 200:
                cases = response.json()

                if cases:
                    cases_df = pd.DataFrame(cases)
                    st.dataframe(
                        cases_df[['id', 'suite_id', 'name', 'test_type', 'priority', 'last_status', 'last_run_at']],
                        use_container_width=True
                    )

                    # Detailed view
                    selected_id = st.selectbox("Select test case for details:", cases_df['id'].tolist())

                    if selected_id:
                        selected_case = next((c for c in cases if c['id'] == selected_id), None)
                        if selected_case:
                            with st.expander("📋 Test Case Details", expanded=True):
                                st.json(selected_case)
=======
from datetime import datetime
import time
import os
import json

# API configuration
API_BASE_URL = os.getenv("TESTING_API_URL", "http://localhost:8001")


def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="NEXUS Testing & QA",
        page_icon="🧪",
        layout="wide"
    )

    # Sidebar navigation
    st.sidebar.title("🧪 NEXUS Testing & QA")
    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Test Cases", "Test Suites", "Test Runs", "Defects", "Analytics"]
    )

    if page == "Dashboard":
        dashboard_page()
    elif page == "Test Cases":
        test_cases_page()
    elif page == "Test Suites":
        test_suites_page()
    elif page == "Test Runs":
        test_runs_page()
    elif page == "Defects":
        defects_page()
    elif page == "Analytics":
        analytics_page()


def dashboard_page():
    """Dashboard overview page"""
    st.title("📊 Testing Dashboard")

    try:
        response = requests.get(f"{API_BASE_URL}/analytics", timeout=10)

        if response.status_code == 200:
            data = response.json()

            # Overview metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Test Cases", data["total_test_cases"])
            with col2:
                st.metric("Test Runs", data["total_test_runs"])
            with col3:
                st.metric("Pass Rate", f"{data['test_pass_rate']:.1f}%")
            with col4:
                st.metric("Active Defects", data["active_defects"])

            # Charts
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Tests by Type")
                if data["tests_by_type"]:
                    st.bar_chart(data["tests_by_type"])

            with col2:
                st.subheader("Defects by Severity")
                if data["defects_by_severity"]:
                    st.bar_chart(data["defects_by_severity"])

            # Top failing tests
            if data["top_failing_tests"]:
                st.subheader("🔴 Top Failing Tests")
                failing_df = pd.DataFrame(data["top_failing_tests"])
                st.dataframe(failing_df, use_container_width=True)

        else:
            st.error("Failed to load dashboard data")

    except Exception as e:
        st.error(f"Error: {str(e)}")


def test_cases_page():
    """Test cases management page"""
    st.title("📝 Test Cases")

    tab1, tab2 = st.tabs(["View Test Cases", "Create Test Case"])

    with tab1:
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            test_type_filter = st.selectbox(
                "Filter by Type",
                ["All", "unit", "integration", "e2e", "performance", "security", "regression"]
            )
        with col2:
            automated_filter = st.selectbox(
                "Filter by Automation",
                ["All", "Automated", "Manual"]
            )

        # Load test cases
        try:
            params = {}
            if test_type_filter != "All":
                params["test_type"] = test_type_filter
            if automated_filter == "Automated":
                params["is_automated"] = True
            elif automated_filter == "Manual":
                params["is_automated"] = False

            response = requests.get(f"{API_BASE_URL}/test-cases", params=params, timeout=10)

            if response.status_code == 200:
                test_cases = response.json()

                if test_cases:
                    df = pd.DataFrame([
                        {
                            "ID": tc["id"],
                            "Name": tc["name"],
                            "Type": tc["test_type"],
                            "Priority": tc["priority"],
                            "Automated": "✓" if tc["is_automated"] else "✗",
                            "Created": tc["created_at"][:10]
                        }
                        for tc in test_cases
                    ])

                    st.dataframe(df, use_container_width=True)

                    # View details
                    selected_id = st.number_input("Enter Test Case ID to view details", min_value=1, step=1)
                    if st.button("View Details"):
                        detail_response = requests.get(f"{API_BASE_URL}/test-cases/{selected_id}", timeout=10)
                        if detail_response.status_code == 200:
                            test_case = detail_response.json()
                            st.json(test_case)
                        else:
                            st.error("Test case not found")

>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a
                else:
                    st.info("No test cases found")

            else:
                st.error("Failed to load test cases")

        except Exception as e:
            st.error(f"Error: {str(e)}")

    with tab2:
<<<<<<< HEAD
        st.markdown("#### Create New Test Case")

        with st.form("create_case_form"):
            suite_id = st.number_input("Suite ID*", min_value=1, value=1)
            name = st.text_input("Test Name*")
            description = st.text_area("Description")
            test_type = st.selectbox("Test Type*", ["unit", "integration", "e2e", "performance", "security"])
            priority = st.selectbox("Priority", ["low", "medium", "high", "critical"])
            file_path = st.text_input("File Path")
            function_name = st.text_input("Function Name")
            code = st.text_area("Test Code", height=200)

            submitted = st.form_submit_button("✅ Create Test Case")

            if submitted:
                if name and suite_id:
                    try:
                        payload = {
                            "suite_id": suite_id,
                            "name": name,
                            "description": description,
                            "test_type": test_type,
                            "priority": priority,
                            "file_path": file_path if file_path else None,
                            "function_name": function_name if function_name else None,
                            "code": code if code else None,
                            "created_by": user_id
                        }

                        response = requests.post(f"{API_BASE_URL}/cases", json=payload)

                        if response.status_code == 200:
                            st.success("✅ Test case created successfully!")
                            st.json(response.json())
                        else:
                            st.error(f"Error: {response.text}")

                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                else:
                    st.warning("Please fill in required fields")


def show_test_runs(user_id):
    """Test runs management"""
    st.markdown("### 🚀 Test Runs")

    tab1, tab2 = st.tabs(["📝 Test Runs History", "▶️ Execute Test Run"])

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            suite_filter = st.text_input("Suite ID (optional)", key="run_suite_filter")

        with col2:
            status_filter = st.selectbox("Status", ["All", "passed", "failed", "running", "pending"], key="run_status_filter")

        try:
            params = {"limit": 50}

            if suite_filter:
                params["suite_id"] = int(suite_filter)
            if status_filter != "All":
                params["status"] = status_filter

            response = requests.get(f"{API_BASE_URL}/runs", params=params)

            if response.status_code == 200:
                runs = response.json()

                if runs:
                    for run in runs:
                        status_color = {
                            'passed': 'green',
                            'failed': 'red',
                            'running': 'blue',
                            'pending': 'orange'
                        }.get(run['status'], 'gray')

                        with st.expander(f"🚀 {run['name']} - {run['status'].upper()} ({run['created_at']})"):
                            col1, col2, col3 = st.columns(3)

                            with col1:
                                st.metric("Total Tests", run['total_tests'])
                                st.metric("Passed", run['passed_tests'])

                            with col2:
                                st.metric("Failed", run['failed_tests'])
                                st.metric("Skipped", run['skipped_tests'])

                            with col3:
                                st.metric("Errors", run['error_tests'])
                                if run['duration_seconds']:
                                    st.metric("Duration", f"{run['duration_seconds']:.2f}s")

                            # Progress bar
                            if run['total_tests'] > 0:
                                pass_rate = (run['passed_tests'] / run['total_tests']) * 100
                                st.progress(pass_rate / 100)
                                st.write(f"Pass Rate: {pass_rate:.1f}%")

                            if st.button("View Executions", key=f"view_exec_{run['id']}"):
                                show_executions(run['id'])
=======
        # Create test case form
        with st.form("create_test_case"):
            name = st.text_input("Test Name*")
            description = st.text_area("Description")

            col1, col2 = st.columns(2)
            with col1:
                test_type = st.selectbox(
                    "Test Type*",
                    ["unit", "integration", "e2e", "performance", "security", "regression"]
                )
                priority = st.selectbox("Priority", ["low", "medium", "high", "critical"])

            with col2:
                is_automated = st.checkbox("Automated Test")
                test_file = st.text_input("Test File Path")

            test_function = st.text_input("Test Function Name")
            expected_result = st.text_area("Expected Result")

            submitted = st.form_submit_button("Create Test Case")

            if submitted and name:
                try:
                    data = {
                        "name": name,
                        "description": description,
                        "test_type": test_type,
                        "priority": priority,
                        "is_automated": is_automated,
                        "test_file": test_file if test_file else None,
                        "test_function": test_function if test_function else None,
                        "expected_result": expected_result if expected_result else None
                    }

                    response = requests.post(f"{API_BASE_URL}/test-cases", json=data, timeout=10)

                    if response.status_code == 201:
                        st.success("✅ Test case created successfully!")
                        st.json(response.json())
                    else:
                        st.error(f"Error: {response.text}")

                except Exception as e:
                    st.error(f"Error: {str(e)}")


def test_suites_page():
    """Test suites management page"""
    st.title("📦 Test Suites")

    tab1, tab2 = st.tabs(["View Test Suites", "Create Test Suite"])

    with tab1:
        try:
            response = requests.get(f"{API_BASE_URL}/test-suites", timeout=10)

            if response.status_code == 200:
                test_suites = response.json()

                if test_suites:
                    df = pd.DataFrame([
                        {
                            "ID": ts["id"],
                            "Name": ts["name"],
                            "Test Cases": len(ts.get("test_case_ids", [])),
                            "Environment": ts.get("environment", "N/A"),
                            "Created": ts["created_at"][:10]
                        }
                        for ts in test_suites
                    ])

                    st.dataframe(df, use_container_width=True)

                else:
                    st.info("No test suites found")

            else:
                st.error("Failed to load test suites")

        except Exception as e:
            st.error(f"Error: {str(e)}")

    with tab2:
        with st.form("create_test_suite"):
            name = st.text_input("Suite Name*")
            description = st.text_area("Description")
            test_case_ids = st.text_input("Test Case IDs (comma-separated)*", help="e.g., 1,2,3")
            environment = st.text_input("Environment", placeholder="dev, staging, prod")

            submitted = st.form_submit_button("Create Test Suite")

            if submitted and name and test_case_ids:
                try:
                    ids = [int(id.strip()) for id in test_case_ids.split(",")]

                    data = {
                        "name": name,
                        "description": description,
                        "test_case_ids": ids,
                        "environment": environment if environment else None
                    }

                    response = requests.post(f"{API_BASE_URL}/test-suites", json=data, timeout=10)

                    if response.status_code == 201:
                        st.success("✅ Test suite created successfully!")
                        st.json(response.json())
                    else:
                        st.error(f"Error: {response.text}")

                except Exception as e:
                    st.error(f"Error: {str(e)}")


def test_runs_page():
    """Test runs page"""
    st.title("🚀 Test Runs")

    tab1, tab2 = st.tabs(["View Test Runs", "Create Test Run"])

    with tab1:
        try:
            response = requests.get(f"{API_BASE_URL}/test-runs?limit=50", timeout=10)

            if response.status_code == 200:
                test_runs = response.json()

                if test_runs:
                    df = pd.DataFrame([
                        {
                            "ID": tr["id"],
                            "Name": tr.get("name", f"Run {tr['id']}"),
                            "Status": tr["status"].upper(),
                            "Tests": f"{tr['passed_tests']}/{tr['total_tests']}",
                            "Duration": f"{tr.get('duration', 0):.1f}s" if tr.get('duration') else "N/A",
                            "Created": tr["created_at"][:10]
                        }
                        for tr in test_runs
                    ])

                    st.dataframe(df, use_container_width=True)

                    # View details
                    selected_id = st.number_input("Enter Test Run ID to view details", min_value=1, step=1)
                    if st.button("View Details"):
                        detail_response = requests.get(f"{API_BASE_URL}/test-runs/{selected_id}", timeout=10)
                        if detail_response.status_code == 200:
                            test_run = detail_response.json()

                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Total Tests", test_run["total_tests"])
                            with col2:
                                st.metric("Passed", test_run["passed_tests"])
                            with col3:
                                st.metric("Failed", test_run["failed_tests"])
                            with col4:
                                st.metric("Duration", f"{test_run.get('duration', 0):.1f}s")

                            # Get executions
                            exec_response = requests.get(
                                f"{API_BASE_URL}/test-runs/{selected_id}/executions",
                                timeout=10
                            )
                            if exec_response.status_code == 200:
                                executions = exec_response.json()
                                if executions:
                                    exec_df = pd.DataFrame([
                                        {
                                            "Test ID": ex["test_case_id"],
                                            "Status": ex["status"].upper(),
                                            "Duration": f"{ex.get('duration', 0):.2f}s",
                                            "Error": ex.get("error_message", "")[:50]
                                        }
                                        for ex in executions
                                    ])
                                    st.dataframe(exec_df, use_container_width=True)

                        else:
                            st.error("Test run not found")

>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a
                else:
                    st.info("No test runs found")

            else:
                st.error("Failed to load test runs")

        except Exception as e:
            st.error(f"Error: {str(e)}")

    with tab2:
<<<<<<< HEAD
        st.markdown("#### Execute New Test Run")

        with st.form("execute_run_form"):
            suite_id = st.number_input("Suite ID*", min_value=1, value=1)
            run_name = st.text_input("Run Name*", value=f"Test Run {datetime.now().strftime('%Y%m%d_%H%M%S')}")
            description = st.text_area("Description")
            environment = st.text_input("Environment", value="development")
            run_type = st.selectbox("Run Type", ["manual", "automated", "scheduled", "ci/cd"])

            submitted = st.form_submit_button("▶️ Execute Test Run")

            if submitted:
                if run_name and suite_id:
                    try:
                        payload = {
                            "suite_id": suite_id,
                            "name": run_name,
                            "description": description,
                            "environment": environment,
                            "run_type": run_type,
                            "triggered_by": user_id
                        }

                        response = requests.post(f"{API_BASE_URL}/runs", json=payload)

                        if response.status_code == 200:
                            st.success("✅ Test run started successfully!")
                            result = response.json()
                            st.json(result)
                            st.info("Tests are running in the background. Refresh to see results.")
                        else:
                            st.error(f"Error: {response.text}")

                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                else:
                    st.warning("Please fill in required fields")


def show_executions(run_id: int):
    """Show test executions for a run"""
    try:
        response = requests.get(f"{API_BASE_URL}/runs/{run_id}/executions")

        if response.status_code == 200:
            executions = response.json()

            if executions:
                exec_df = pd.DataFrame(executions)
                st.dataframe(exec_df[['id', 'test_case_id', 'status', 'duration_seconds', 'error_message']])
            else:
                st.info("No executions found")

    except Exception as e:
        st.error(f"Error: {str(e)}")


def show_defects(user_id):
    """Defects management"""
    st.markdown("### 🐛 Defects")

    tab1, tab2 = st.tabs(["📝 All Defects", "➕ Report Defect"])

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            severity_filter = st.selectbox("Severity", ["All", "low", "medium", "high", "critical", "blocker"])

        with col2:
            status_filter = st.selectbox("Status", ["All", "new", "open", "in_progress", "resolved", "closed"])

        try:
            params = {"limit": 100}

            if severity_filter != "All":
                params["severity"] = severity_filter
            if status_filter != "All":
                params["status"] = status_filter

            response = requests.get(f"{API_BASE_URL}/defects", params=params)
=======
        with st.form("create_test_run"):
            test_suite_id = st.number_input("Test Suite ID*", min_value=1, step=1)
            run_name = st.text_input("Run Name")
            environment = st.text_input("Environment", placeholder="dev, staging, prod")
            branch = st.text_input("Branch Name", placeholder="main")

            submitted = st.form_submit_button("Start Test Run")

            if submitted and test_suite_id:
                try:
                    data = {
                        "test_suite_id": test_suite_id,
                        "name": run_name if run_name else None,
                        "environment": environment if environment else None,
                        "branch": branch if branch else None,
                        "triggered_by": "manual"
                    }

                    response = requests.post(f"{API_BASE_URL}/test-runs", json=data, timeout=30)

                    if response.status_code == 201:
                        st.success("✅ Test run started successfully!")
                        st.json(response.json())
                        st.info("Test execution is running in the background. Check the results in a few moments.")
                    else:
                        st.error(f"Error: {response.text}")

                except Exception as e:
                    st.error(f"Error: {str(e)}")


def defects_page():
    """Defects management page"""
    st.title("🐛 Defects")

    tab1, tab2 = st.tabs(["View Defects", "Create Defect"])

    with tab1:
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "open", "in_progress", "resolved", "closed"]
            )
        with col2:
            severity_filter = st.selectbox(
                "Filter by Severity",
                ["All", "low", "medium", "high", "critical", "blocker"]
            )

        try:
            params = {}
            if status_filter != "All":
                params["status"] = status_filter
            if severity_filter != "All":
                params["severity"] = severity_filter

            response = requests.get(f"{API_BASE_URL}/defects", params=params, timeout=10)
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a

            if response.status_code == 200:
                defects = response.json()

                if defects:
<<<<<<< HEAD
                    for defect in defects:
                        severity_color = {
                            'low': '🟢',
                            'medium': '🟡',
                            'high': '🟠',
                            'critical': '🔴',
                            'blocker': '🔴'
                        }.get(defect['severity'], '⚪')

                        with st.expander(f"{severity_color} {defect['title']} - {defect['status'].upper()}"):
                            col1, col2 = st.columns(2)

                            with col1:
                                st.write(f"**ID:** {defect['id']}")
                                st.write(f"**Severity:** {defect['severity']}")
                                st.write(f"**Priority:** {defect['priority']}")
                                st.write(f"**Status:** {defect['status']}")

                            with col2:
                                st.write(f"**Reported By:** {defect['reported_by']}")
                                st.write(f"**Created:** {defect['created_at']}")
                                if defect.get('assigned_to'):
                                    st.write(f"**Assigned To:** {defect['assigned_to']}")

                            st.write(f"**Description:** {defect['description']}")

                            # Update status
                            new_status = st.selectbox(
                                "Update Status",
                                ["new", "open", "in_progress", "resolved", "closed"],
                                key=f"status_{defect['id']}"
                            )

                            if st.button("Update", key=f"update_{defect['id']}"):
                                try:
                                    update_response = requests.patch(
                                        f"{API_BASE_URL}/defects/{defect['id']}/status?status={new_status}"
                                    )
                                    if update_response.status_code == 200:
                                        st.success("Status updated!")
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
=======
                    df = pd.DataFrame([
                        {
                            "ID": d["id"],
                            "Title": d["title"][:50],
                            "Severity": d["severity"].upper(),
                            "Priority": d["priority"].upper(),
                            "Status": d["status"].upper(),
                            "Created": d["created_at"][:10]
                        }
                        for d in defects
                    ])

                    st.dataframe(df, use_container_width=True)

>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a
                else:
                    st.info("No defects found")

            else:
                st.error("Failed to load defects")

        except Exception as e:
            st.error(f"Error: {str(e)}")

    with tab2:
<<<<<<< HEAD
        st.markdown("#### Report New Defect")

        with st.form("report_defect_form"):
            title = st.text_input("Title*")
            description = st.text_area("Description*")
            severity = st.selectbox("Severity*", ["low", "medium", "high", "critical", "blocker"])
            priority = st.selectbox("Priority", ["low", "medium", "high", "critical"])
            test_case_id = st.number_input("Test Case ID", min_value=0, value=0)
            environment = st.text_input("Environment")
            browser = st.text_input("Browser")
            os = st.text_input("Operating System")

            steps = st.text_area("Steps to Reproduce")
            expected = st.text_area("Expected Behavior")
            actual = st.text_area("Actual Behavior")

            submitted = st.form_submit_button("🐛 Report Defect")

            if submitted:
                if title and description:
                    try:
                        payload = {
                            "title": title,
                            "description": description,
                            "severity": severity,
                            "priority": priority,
                            "test_case_id": test_case_id if test_case_id > 0 else None,
                            "environment": environment,
                            "browser": browser,
                            "os": os,
                            "steps_to_reproduce": steps,
                            "expected_behavior": expected,
                            "actual_behavior": actual,
                            "reported_by": user_id
                        }

                        response = requests.post(f"{API_BASE_URL}/defects", json=payload)

                        if response.status_code == 200:
                            st.success("✅ Defect reported successfully!")
                            st.json(response.json())
                        else:
                            st.error(f"Error: {response.text}")

                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                else:
                    st.warning("Please fill in required fields")


def show_analytics():
    """Analytics dashboard"""
    st.markdown("### 📊 Test Analytics")

    days = st.slider("Time Range (days)", 1, 90, 30)

    try:
        response = requests.get(f"{API_BASE_URL}/analytics?days={days}")
=======
        with st.form("create_defect"):
            title = st.text_input("Title*")
            description = st.text_area("Description*")

            col1, col2 = st.columns(2)
            with col1:
                severity = st.selectbox("Severity*", ["low", "medium", "high", "critical", "blocker"])
                priority = st.selectbox("Priority*", ["low", "medium", "high", "critical"])

            with col2:
                component = st.text_input("Component")
                environment = st.text_input("Environment")

            steps_to_reproduce = st.text_area("Steps to Reproduce")
            expected_behavior = st.text_area("Expected Behavior")
            actual_behavior = st.text_area("Actual Behavior")

            submitted = st.form_submit_button("Create Defect")

            if submitted and title and description:
                try:
                    data = {
                        "title": title,
                        "description": description,
                        "severity": severity,
                        "priority": priority,
                        "component": component if component else None,
                        "environment": environment if environment else None,
                        "steps_to_reproduce": steps_to_reproduce if steps_to_reproduce else None,
                        "expected_behavior": expected_behavior if expected_behavior else None,
                        "actual_behavior": actual_behavior if actual_behavior else None
                    }

                    response = requests.post(f"{API_BASE_URL}/defects", json=data, timeout=10)

                    if response.status_code == 201:
                        st.success("✅ Defect created successfully!")
                        st.json(response.json())
                    else:
                        st.error(f"Error: {response.text}")

                except Exception as e:
                    st.error(f"Error: {str(e)}")


def analytics_page():
    """Analytics page"""
    st.title("📈 Test Analytics")

    try:
        response = requests.get(f"{API_BASE_URL}/analytics", timeout=10)
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a

        if response.status_code == 200:
            data = response.json()

<<<<<<< HEAD
            # Metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Test Cases", data['total_test_cases'])

            with col2:
                st.metric("Test Runs", data['total_test_runs'])

            with col3:
                st.metric("Pass Rate", f"{data['test_pass_rate']:.1f}%")

            with col4:
                st.metric("Defects", data['total_defects'])

            st.markdown("---")

            # Charts
            col1, col2 = st.columns(2)

            with col1:
                if data['tests_by_type']:
                    st.markdown("#### Tests by Type")
                    type_df = pd.DataFrame(list(data['tests_by_type'].items()), columns=['Type', 'Count'])
                    fig = px.pie(type_df, values='Count', names='Type')
                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                if data['defects_by_severity']:
                    st.markdown("#### Defects by Severity")
                    severity_df = pd.DataFrame(list(data['defects_by_severity'].items()), columns=['Severity', 'Count'])
                    fig = px.bar(severity_df, x='Severity', y='Count', color='Severity')
                    st.plotly_chart(fig, use_container_width=True)
=======
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Test Cases", data["total_test_cases"])
            with col2:
                st.metric("Total Test Runs", data["total_test_runs"])
            with col3:
                st.metric("Test Pass Rate", f"{data['test_pass_rate']:.2f}%")
            with col4:
                st.metric("Avg Duration", f"{data['average_test_duration']:.2f}s")

            # Visualizations
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📊 Tests by Type")
                if data["tests_by_type"]:
                    st.bar_chart(data["tests_by_type"])

            with col2:
                st.subheader("🐛 Defects by Severity")
                if data["defects_by_severity"]:
                    st.bar_chart(data["defects_by_severity"])

            # Top failing tests
            if data["top_failing_tests"]:
                st.subheader("🔴 Top Failing Tests")
                failing_df = pd.DataFrame(data["top_failing_tests"])
                st.dataframe(failing_df, use_container_width=True)
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a

        else:
            st.error("Failed to load analytics")

    except Exception as e:
        st.error(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
