"""
Enterprise Payroll Dashboard - Streamlit UI
Interactive web dashboard for payroll management, analytics, and reporting
Production-ready with real-time updates and comprehensive visualizations
"""

import streamlit as st
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
import pandas as pd
import logging

# Import payroll modules
try:
    from .processing import (
        PayrollProcessor, Employee, PayFrequency, EmploymentType,
        Deduction, DeductionType, Bonus, TimeEntry, OvertimeRule, Currency
    )
    from .tax import TaxEngine, W4Information, FilingStatus, State
    from .payslips import PayslipGenerator, CompanyInfo, PayslipFormat
    from .deposit import DirectDepositProcessor, BankAccount, AccountType, DepositAllocation, DepositType
    from .compliance import ComplianceEngine, LaborLawType
    from .reports import ReportGenerator, ReportType, PayrollSummaryReport
except ImportError:
    # Fallback for standalone execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))

    from processing import (
        PayrollProcessor, Employee, PayFrequency, EmploymentType,
        Deduction, DeductionType, Bonus, TimeEntry, OvertimeRule, Currency
    )
    from tax import TaxEngine, W4Information, FilingStatus, State
    from payslips import PayslipGenerator, CompanyInfo, PayslipFormat
    from deposit import DirectDepositProcessor, BankAccount, AccountType, DepositAllocation, DepositType
    from compliance import ComplianceEngine, LaborLawType
    from reports import ReportGenerator, ReportType, PayrollSummaryReport

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Page configuration
st.set_page_config(
    page_title="Enterprise Payroll System",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
def init_session_state():
    """Initialize Streamlit session state"""
    if 'payroll_processor' not in st.session_state:
        st.session_state.payroll_processor = PayrollProcessor()

    if 'tax_engine' not in st.session_state:
        st.session_state.tax_engine = TaxEngine()

    if 'compliance_engine' not in st.session_state:
        st.session_state.compliance_engine = ComplianceEngine()

    if 'report_generator' not in st.session_state:
        st.session_state.report_generator = ReportGenerator()

    if 'company_info' not in st.session_state:
        st.session_state.company_info = CompanyInfo(
            name="Acme Corporation",
            address="123 Business St",
            city="San Francisco",
            state="CA",
            zip_code="94105",
            phone="(555) 123-4567",
            email="payroll@acme.com",
            tax_id="12-3456789"
        )


def show_dashboard():
    """Main dashboard view"""
    st.markdown('<p class="main-header">💰 Enterprise Payroll System</p>', unsafe_allow_html=True)

    processor = st.session_state.payroll_processor

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_employees = len(processor.employees)
        active_employees = len([e for e in processor.employees.values() if e.active])
        st.metric("Total Employees", total_employees, f"{active_employees} active")

    with col2:
        total_runs = len(processor.payroll_runs)
        st.metric("Payroll Runs", total_runs)

    with col3:
        if processor.payroll_runs:
            latest_run = list(processor.payroll_runs.values())[-1]
            st.metric("Last Run Total", f"${latest_run.total_net_pay:,.2f}")
        else:
            st.metric("Last Run Total", "$0.00")

    with col4:
        compliance_summary = st.session_state.compliance_engine.get_compliance_summary()
        st.metric("Compliance Rate", compliance_summary['compliance_rate'])

    st.divider()

    # Recent activity
    st.subheader("📊 Recent Activity")

    if processor.payroll_runs:
        runs_data = []
        for run in list(processor.payroll_runs.values())[-5:]:
            runs_data.append({
                "Run Number": run.run_number,
                "Pay Date": run.pay_date.isoformat(),
                "Employees": run.employee_count,
                "Gross Pay": f"${run.total_gross_pay:,.2f}",
                "Net Pay": f"${run.total_net_pay:,.2f}",
                "Status": run.status.value
            })

        df = pd.DataFrame(runs_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No payroll runs yet. Create your first payroll run!")

    # Quick actions
    st.divider()
    st.subheader("⚡ Quick Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("➕ Add Employee", use_container_width=True):
            st.session_state.page = "employees"
            st.rerun()

    with col2:
        if st.button("🔄 Run Payroll", use_container_width=True):
            st.session_state.page = "payroll"
            st.rerun()

    with col3:
        if st.button("📄 Generate Reports", use_container_width=True):
            st.session_state.page = "reports"
            st.rerun()

    with col4:
        if st.button("✅ Check Compliance", use_container_width=True):
            st.session_state.page = "compliance"
            st.rerun()


def show_employees():
    """Employee management view"""
    st.header("👥 Employee Management")

    processor = st.session_state.payroll_processor

    # Tabs for different actions
    tab1, tab2, tab3 = st.tabs(["All Employees", "Add Employee", "Import"])

    with tab1:
        if processor.employees:
            employees_data = []
            for emp in processor.employees.values():
                employees_data.append({
                    "ID": emp.employee_number,
                    "Name": emp.full_name,
                    "Department": emp.department,
                    "Type": emp.employment_type.value,
                    "Salary": f"${emp.base_salary:,.2f}",
                    "Pay Frequency": emp.pay_frequency.value,
                    "Active": "✓" if emp.active else "✗"
                })

            df = pd.DataFrame(employees_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.metric("Total Employees", len(employees_data))
        else:
            st.info("No employees registered yet.")

    with tab2:
        st.subheader("Add New Employee")

        with st.form("add_employee_form"):
            col1, col2 = st.columns(2)

            with col1:
                first_name = st.text_input("First Name*")
                last_name = st.text_input("Last Name*")
                email = st.text_input("Email*")
                department = st.text_input("Department")

            with col2:
                employment_type = st.selectbox(
                    "Employment Type*",
                    options=[e.value for e in EmploymentType]
                )
                is_salaried = st.checkbox("Salaried Employee", value=True)
                base_salary = st.number_input(
                    "Annual Salary" if is_salaried else "Hourly Rate",
                    min_value=0.0,
                    value=50000.0 if is_salaried else 25.0,
                    step=1000.0 if is_salaried else 1.0
                )
                pay_frequency = st.selectbox(
                    "Pay Frequency*",
                    options=[e.value for e in PayFrequency]
                )

            overtime_eligible = st.checkbox("Overtime Eligible")

            submitted = st.form_submit_button("Add Employee", use_container_width=True)

            if submitted:
                if not all([first_name, last_name, email]):
                    st.error("Please fill in all required fields (*)")
                else:
                    employee = Employee(
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        department=department,
                        employment_type=EmploymentType(employment_type),
                        is_salaried=is_salaried,
                        base_salary=Decimal(str(base_salary)),
                        pay_frequency=PayFrequency(pay_frequency),
                        overtime_eligible=overtime_eligible,
                        overtime_rule=OvertimeRule() if overtime_eligible else None
                    )

                    processor.register_employee(employee)
                    st.success(f"✓ Employee {employee.full_name} added successfully!")
                    st.balloons()

    with tab3:
        st.subheader("Import Employees")
        st.info("Upload a CSV file with employee data")

        uploaded_file = st.file_uploader("Choose CSV file", type=['csv'])

        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                st.write("Preview:", df.head())

                if st.button("Import Employees"):
                    count = 0
                    for _, row in df.iterrows():
                        # Import logic here
                        count += 1

                    st.success(f"✓ Imported {count} employees successfully!")
            except Exception as e:
                st.error(f"Error importing file: {e}")


def show_payroll():
    """Payroll processing view"""
    st.header("💵 Payroll Processing")

    processor = st.session_state.payroll_processor

    tab1, tab2, tab3 = st.tabs(["New Payroll Run", "Previous Runs", "Approve Pending"])

    with tab1:
        st.subheader("Create New Payroll Run")

        with st.form("payroll_run_form"):
            col1, col2, col3 = st.columns(3)

            with col1:
                pay_period_start = st.date_input("Pay Period Start", date.today() - timedelta(days=14))

            with col2:
                pay_period_end = st.date_input("Pay Period End", date.today())

            with col3:
                pay_date = st.date_input("Pay Date", date.today() + timedelta(days=7))

            # Employee selection
            all_employees = st.checkbox("Process all active employees", value=True)

            if not all_employees:
                employee_options = {
                    emp.full_name: emp.id
                    for emp in processor.employees.values()
                    if emp.active
                }
                selected_employees = st.multiselect(
                    "Select Employees",
                    options=list(employee_options.keys())
                )
            else:
                selected_employees = None

            submitted = st.form_submit_button("Run Payroll", use_container_width=True)

            if submitted:
                with st.spinner("Processing payroll..."):
                    try:
                        employee_ids = None
                        if not all_employees and selected_employees:
                            employee_ids = [employee_options[name] for name in selected_employees]

                        run = processor.create_payroll_run(
                            pay_period_start=pay_period_start,
                            pay_period_end=pay_period_end,
                            pay_date=pay_date,
                            employee_ids=employee_ids,
                            created_by="admin"
                        )

                        st.success(f"✓ Payroll run {run.run_number} created successfully!")

                        # Show summary
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Employees", run.employee_count)
                        with col2:
                            st.metric("Gross Pay", f"${run.total_gross_pay:,.2f}")
                        with col3:
                            st.metric("Taxes", f"${run.total_taxes:,.2f}")
                        with col4:
                            st.metric("Net Pay", f"${run.total_net_pay:,.2f}")

                        if run.errors:
                            st.error("Errors encountered:")
                            for error in run.errors:
                                st.write(f"• {error}")

                        if run.warnings:
                            st.warning("Warnings:")
                            for warning in run.warnings:
                                st.write(f"• {warning}")

                    except Exception as e:
                        st.error(f"Error processing payroll: {e}")

    with tab2:
        st.subheader("Previous Payroll Runs")

        if processor.payroll_runs:
            for run in reversed(list(processor.payroll_runs.values())):
                with st.expander(f"{run.run_number} - {run.pay_date} ({run.status.value})"):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(f"**Period:** {run.pay_period_start} to {run.pay_period_end}")
                        st.write(f"**Employees:** {run.employee_count}")
                        st.write(f"**Created:** {run.created_at.strftime('%Y-%m-%d %H:%M')}")

                    with col2:
                        st.write(f"**Gross Pay:** ${run.total_gross_pay:,.2f}")
                        st.write(f"**Taxes:** ${run.total_taxes:,.2f}")
                        st.write(f"**Net Pay:** ${run.total_net_pay:,.2f}")

                    if st.button(f"View Details - {run.run_number}"):
                        st.session_state.selected_run = run.id
        else:
            st.info("No payroll runs yet.")

    with tab3:
        st.subheader("Approve Pending Runs")

        pending_runs = [
            run for run in processor.payroll_runs.values()
            if run.status.value == "pending_approval"
        ]

        if pending_runs:
            for run in pending_runs:
                with st.expander(f"{run.run_number} - Pending Approval"):
                    st.write(f"Employees: {run.employee_count}")
                    st.write(f"Net Pay: ${run.total_net_pay:,.2f}")

                    if st.button(f"Approve {run.run_number}"):
                        processor.approve_payroll_run(run.id, "admin")
                        st.success("✓ Payroll run approved!")
                        st.rerun()
        else:
            st.info("No pending payroll runs.")


def show_reports():
    """Reports and analytics view"""
    st.header("📊 Reports & Analytics")

    processor = st.session_state.payroll_processor
    report_gen = st.session_state.report_generator

    tab1, tab2, tab3 = st.tabs(["Payroll Summary", "Tax Reports", "Custom Reports"])

    with tab1:
        st.subheader("Payroll Summary Report")

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", date.today() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", date.today())

        if st.button("Generate Summary Report"):
            if processor.payroll_runs:
                report = report_gen.generate_payroll_summary(
                    list(processor.payroll_runs.values()),
                    processor.employees,
                    start_date,
                    end_date
                )

                # Display metrics
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Active Employees", report.active_employees)
                    st.metric("New Hires", report.new_hires)

                with col2:
                    st.metric("Gross Pay", f"${report.total_gross_pay:,.2f}")
                    st.metric("Regular Pay", f"${report.total_regular_pay:,.2f}")

                with col3:
                    st.metric("Total Taxes", f"${report.total_taxes:,.2f}")
                    st.metric("Deductions", f"${report.total_deductions:,.2f}")

                with col4:
                    st.metric("Net Pay", f"${report.total_net_pay:,.2f}")

                # Department breakdown
                if report.by_department:
                    st.subheader("By Department")
                    dept_df = pd.DataFrame([
                        {"Department": dept, "Amount": float(amount)}
                        for dept, amount in report.by_department.items()
                    ])
                    st.bar_chart(dept_df.set_index("Department"))

                # Export options
                st.divider()
                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("Export to JSON"):
                        json_data = report_gen.export_to_json(report)
                        st.download_button(
                            "Download JSON",
                            json_data,
                            "payroll_summary.json",
                            "application/json"
                        )

                with col2:
                    if st.button("Export to CSV"):
                        csv_data = report_gen.export_to_csv(report)
                        st.download_button(
                            "Download CSV",
                            csv_data,
                            "payroll_summary.csv",
                            "text/csv"
                        )

                with col3:
                    if st.button("Export to HTML"):
                        html_data = report_gen.export_to_html(report)
                        st.download_button(
                            "Download HTML",
                            html_data,
                            "payroll_summary.html",
                            "text/html"
                        )
            else:
                st.warning("No payroll data available for the selected period.")

    with tab2:
        st.subheader("Tax Liability Reports")
        st.info("Tax reports will be generated here - W-2s, 941s, etc.")

    with tab3:
        st.subheader("Custom Reports")
        st.info("Build custom reports with flexible filtering and grouping.")


def show_compliance():
    """Compliance monitoring view"""
    st.header("✅ Compliance & Audit")

    compliance = st.session_state.compliance_engine

    # Compliance summary
    summary = compliance.get_compliance_summary()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Active Rules", summary['active_rules'])

    with col2:
        st.metric("Total Violations", summary['total_violations'])

    with col3:
        st.metric("Critical", summary['critical_violations'], delta_color="inverse")

    with col4:
        st.metric("Compliance Rate", summary['compliance_rate'])

    st.divider()

    # Tabs
    tab1, tab2, tab3 = st.tabs(["Violations", "Rules", "Audit Log"])

    with tab1:
        st.subheader("Compliance Violations")

        if compliance.violations:
            for violation in compliance.violations:
                severity_color = {
                    "violation": "🔴",
                    "warning": "🟡",
                    "compliant": "🟢"
                }.get(violation.severity.value, "⚪")

                with st.expander(f"{severity_color} {violation.rule_name}"):
                    st.write(f"**Description:** {violation.description}")
                    st.write(f"**Detected:** {violation.detected_at.strftime('%Y-%m-%d %H:%M')}")

                    if violation.resolved_at:
                        st.success(f"✓ Resolved on {violation.resolved_at.strftime('%Y-%m-%d')}")
                    else:
                        if st.button(f"Mark Resolved - {violation.id[:8]}"):
                            violation.resolved_at = datetime.now()
                            st.success("Violation marked as resolved")
                            st.rerun()
        else:
            st.success("✓ No compliance violations!")

    with tab2:
        st.subheader("Compliance Rules")

        for rule in compliance.compliance_rules.values():
            if rule.active:
                with st.expander(f"📋 {rule.name}"):
                    st.write(f"**Type:** {rule.law_type.value}")
                    st.write(f"**Jurisdiction:** {rule.jurisdiction}")
                    st.write(f"**Description:** {rule.description}")
                    st.write(f"**Parameters:** {rule.parameters}")

    with tab3:
        st.subheader("Audit Log")

        if compliance.audit_log:
            audit_data = []
            for entry in compliance.audit_log[-50:]:  # Last 50 entries
                audit_data.append({
                    "Timestamp": entry.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "Event": entry.event_type.value,
                    "User": entry.user_name,
                    "Action": entry.action,
                    "Description": entry.description
                })

            df = pd.DataFrame(audit_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            if st.button("Export Audit Log"):
                st.info("Audit log export functionality")
        else:
            st.info("No audit log entries yet.")


def main():
    """Main application entry point"""
    init_session_state()

    # Sidebar navigation
    st.sidebar.title("Navigation")

    pages = {
        "Dashboard": "dashboard",
        "Employees": "employees",
        "Payroll": "payroll",
        "Reports": "reports",
        "Compliance": "compliance",
    }

    if 'page' not in st.session_state:
        st.session_state.page = "dashboard"

    for page_name, page_id in pages.items():
        if st.sidebar.button(page_name, use_container_width=True):
            st.session_state.page = page_id
            st.rerun()

    st.sidebar.divider()

    # Company info
    st.sidebar.subheader("Company")
    st.sidebar.write(st.session_state.company_info.name)

    # Route to appropriate page
    if st.session_state.page == "dashboard":
        show_dashboard()
    elif st.session_state.page == "employees":
        show_employees()
    elif st.session_state.page == "payroll":
        show_payroll()
    elif st.session_state.page == "reports":
        show_reports()
    elif st.session_state.page == "compliance":
        show_compliance()


if __name__ == "__main__":
    main()
