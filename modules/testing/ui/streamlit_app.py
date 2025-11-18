"""
Streamlit UI for Testing & QA Module
"""
import streamlit as st
import requests
import pandas as pd
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

                else:
                    st.info("No test cases found")

            else:
                st.error("Failed to load test cases")

        except Exception as e:
            st.error(f"Error: {str(e)}")

    with tab2:
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

                else:
                    st.info("No test runs found")

            else:
                st.error("Failed to load test runs")

        except Exception as e:
            st.error(f"Error: {str(e)}")

    with tab2:
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

            if response.status_code == 200:
                defects = response.json()

                if defects:
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

                else:
                    st.info("No defects found")

            else:
                st.error("Failed to load defects")

        except Exception as e:
            st.error(f"Error: {str(e)}")

    with tab2:
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

        if response.status_code == 200:
            data = response.json()

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

        else:
            st.error("Failed to load analytics")

    except Exception as e:
        st.error(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
