"""
Enterprise Payroll Reporting and Analytics System
Comprehensive reporting, analytics, dashboards, and data visualization
Production-ready with export capabilities and customizable reports
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import logging
import json
from collections import defaultdict
from uuid import uuid4

logger = logging.getLogger(__name__)


class ReportType(Enum):
    """Types of payroll reports"""
    PAYROLL_SUMMARY = "payroll_summary"
    EMPLOYEE_EARNINGS = "employee_earnings"
    TAX_LIABILITY = "tax_liability"
    DEDUCTION_SUMMARY = "deduction_summary"
    DEPARTMENT_COSTS = "department_costs"
    YTD_SUMMARY = "ytd_summary"
    VARIANCE_ANALYSIS = "variance_analysis"
    LABOR_DISTRIBUTION = "labor_distribution"
    BENEFIT_COSTS = "benefit_costs"
    COMPLIANCE_REPORT = "compliance_report"
    CUSTOM = "custom"


class ReportFormat(Enum):
    """Report output formats"""
    JSON = "json"
    CSV = "csv"
    HTML = "html"
    PDF = "pdf"
    EXCEL = "excel"


class TimePeriod(Enum):
    """Reporting time periods"""
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


@dataclass
class ReportFilter:
    """Report filtering criteria"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    employee_ids: Optional[List[str]] = None
    department: Optional[str] = None
    cost_center: Optional[str] = None
    employment_type: Optional[str] = None
    pay_frequency: Optional[str] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None


@dataclass
class PayrollSummaryReport:
    """Payroll summary report data"""
    id: str = field(default_factory=lambda: str(uuid4()))
    report_date: date = field(default_factory=date.today)
    period_start: date = field(default_factory=date.today)
    period_end: date = field(default_factory=date.today)

    # Employee counts
    total_employees: int = 0
    active_employees: int = 0
    new_hires: int = 0
    terminations: int = 0

    # Compensation
    total_gross_pay: Decimal = Decimal("0")
    total_regular_pay: Decimal = Decimal("0")
    total_overtime_pay: Decimal = Decimal("0")
    total_bonus_pay: Decimal = Decimal("0")

    # Deductions
    total_pre_tax_deductions: Decimal = Decimal("0")
    total_post_tax_deductions: Decimal = Decimal("0")
    total_deductions: Decimal = Decimal("0")

    # Taxes
    total_federal_tax: Decimal = Decimal("0")
    total_state_tax: Decimal = Decimal("0")
    total_local_tax: Decimal = Decimal("0")
    total_fica: Decimal = Decimal("0")
    total_taxes: Decimal = Decimal("0")

    # Net pay
    total_net_pay: Decimal = Decimal("0")

    # Hours
    total_regular_hours: Decimal = Decimal("0")
    total_overtime_hours: Decimal = Decimal("0")
    total_pto_hours: Decimal = Decimal("0")

    # Breakdown by category
    by_department: Dict[str, Decimal] = field(default_factory=dict)
    by_employment_type: Dict[str, Decimal] = field(default_factory=dict)
    by_pay_frequency: Dict[str, Decimal] = field(default_factory=dict)

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EmployeeEarningsReport:
    """Employee earnings detail report"""
    employee_id: str
    employee_name: str
    employee_number: str
    department: str
    hire_date: date

    # Current period
    period_start: date
    period_end: date
    gross_pay: Decimal = Decimal("0")
    net_pay: Decimal = Decimal("0")
    hours_worked: Decimal = Decimal("0")

    # YTD
    ytd_gross: Decimal = Decimal("0")
    ytd_net: Decimal = Decimal("0")
    ytd_taxes: Decimal = Decimal("0")
    ytd_deductions: Decimal = Decimal("0")

    # Breakdown
    earnings_breakdown: List[Tuple[str, Decimal]] = field(default_factory=list)
    deductions_breakdown: List[Tuple[str, Decimal]] = field(default_factory=list)
    taxes_breakdown: List[Tuple[str, Decimal]] = field(default_factory=list)


@dataclass
class TaxLiabilityReport:
    """Tax liability report"""
    id: str = field(default_factory=lambda: str(uuid4()))
    period_start: date = field(default_factory=date.today)
    period_end: date = field(default_factory=date.today)
    generated_at: datetime = field(default_factory=datetime.now)

    # Federal taxes
    federal_income_tax: Decimal = Decimal("0")
    social_security_employee: Decimal = Decimal("0")
    social_security_employer: Decimal = Decimal("0")
    medicare_employee: Decimal = Decimal("0")
    medicare_employer: Decimal = Decimal("0")
    futa: Decimal = Decimal("0")  # Federal Unemployment Tax

    # State taxes
    state_income_tax: Decimal = Decimal("0")
    state_unemployment_tax: Decimal = Decimal("0")
    state_disability: Decimal = Decimal("0")

    # Local taxes
    local_income_tax: Decimal = Decimal("0")

    # Totals
    total_employee_taxes: Decimal = Decimal("0")
    total_employer_taxes: Decimal = Decimal("0")
    total_tax_liability: Decimal = Decimal("0")

    # Breakdown by employee
    employee_details: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class DepartmentCostReport:
    """Department labor cost analysis"""
    department: str
    cost_center: str
    period_start: date
    period_end: date

    employee_count: int = 0
    total_compensation: Decimal = Decimal("0")
    total_benefits: Decimal = Decimal("0")
    total_taxes: Decimal = Decimal("0")
    total_cost: Decimal = Decimal("0")

    # Cost per employee
    avg_compensation_per_employee: Decimal = Decimal("0")
    avg_total_cost_per_employee: Decimal = Decimal("0")

    # Hours
    total_hours: Decimal = Decimal("0")
    cost_per_hour: Decimal = Decimal("0")

    # Breakdown
    by_employee_type: Dict[str, Decimal] = field(default_factory=dict)
    top_earners: List[Tuple[str, Decimal]] = field(default_factory=list)


class ReportGenerator:
    """
    Payroll reporting and analytics engine
    Generates comprehensive reports and analytics
    """

    def __init__(self):
        self.reports: Dict[str, Any] = {}

    def generate_payroll_summary(
        self,
        payroll_runs: List[Any],
        employees: Dict[str, Any],
        start_date: date,
        end_date: date
    ) -> PayrollSummaryReport:
        """Generate comprehensive payroll summary report"""
        report = PayrollSummaryReport(
            period_start=start_date,
            period_end=end_date
        )

        # Filter payroll runs within date range
        period_runs = [
            run for run in payroll_runs
            if start_date <= run.pay_date <= end_date
        ]

        # Initialize counters
        by_dept = defaultdict(Decimal)
        by_emp_type = defaultdict(Decimal)
        by_pay_freq = defaultdict(Decimal)

        # Aggregate data from payroll runs
        for run in period_runs:
            report.total_gross_pay += run.total_gross_pay
            report.total_deductions += run.total_deductions
            report.total_taxes += run.total_taxes
            report.total_net_pay += run.total_net_pay

            # Process each payment record
            for record in run.payment_records:
                report.total_regular_pay += record.regular_pay
                report.total_overtime_pay += record.overtime_pay
                report.total_bonus_pay += record.bonus_total

                report.total_pre_tax_deductions += record.pre_tax_deductions
                report.total_post_tax_deductions += record.post_tax_deductions

                report.total_federal_tax += record.federal_tax
                report.total_state_tax += record.state_tax
                report.total_local_tax += record.local_tax
                report.total_fica += (record.social_security + record.medicare)

                report.total_regular_hours += record.regular_hours
                report.total_overtime_hours += record.overtime_hours

                # Get employee info
                emp = employees.get(record.employee_id)
                if emp:
                    dept = emp.department or "Unassigned"
                    by_dept[dept] += record.gross_pay

                    emp_type = emp.employment_type.value if hasattr(emp.employment_type, 'value') else str(emp.employment_type)
                    by_emp_type[emp_type] += record.gross_pay

                    pay_freq = emp.pay_frequency.value if hasattr(emp.pay_frequency, 'value') else str(emp.pay_frequency)
                    by_pay_freq[pay_freq] += record.gross_pay

        # Calculate employee counts
        active_employees = [emp for emp in employees.values() if emp.active]
        report.total_employees = len(employees)
        report.active_employees = len(active_employees)

        # New hires and terminations in period
        report.new_hires = len([
            emp for emp in employees.values()
            if start_date <= emp.hire_date <= end_date
        ])

        report.terminations = len([
            emp for emp in employees.values()
            if emp.termination_date and start_date <= emp.termination_date <= end_date
        ])

        # Convert defaultdicts to regular dicts
        report.by_department = dict(by_dept)
        report.by_employment_type = dict(by_emp_type)
        report.by_pay_frequency = dict(by_pay_freq)

        # Store report
        self.reports[report.id] = report

        logger.info(
            f"Generated payroll summary: {report.active_employees} employees, "
            f"${report.total_gross_pay} gross, ${report.total_net_pay} net"
        )

        return report

    def generate_employee_earnings_report(
        self,
        employee: Any,
        payment_records: List[Any],
        start_date: date,
        end_date: date,
        ytd_data: Optional[Dict[str, Decimal]] = None
    ) -> EmployeeEarningsReport:
        """Generate detailed earnings report for employee"""
        if ytd_data is None:
            ytd_data = {}

        report = EmployeeEarningsReport(
            employee_id=employee.id,
            employee_name=employee.full_name,
            employee_number=employee.employee_number,
            department=employee.department,
            hire_date=employee.hire_date,
            period_start=start_date,
            period_end=end_date
        )

        # Filter records for period
        period_records = [
            r for r in payment_records
            if start_date <= r.pay_date <= end_date
        ]

        # Aggregate period data
        for record in period_records:
            report.gross_pay += record.gross_pay
            report.net_pay += record.net_pay
            report.hours_worked += record.regular_hours + record.overtime_hours

            # Earnings breakdown
            if record.regular_pay > 0:
                report.earnings_breakdown.append(("Regular Pay", record.regular_pay))
            if record.overtime_pay > 0:
                report.earnings_breakdown.append(("Overtime Pay", record.overtime_pay))
            if record.bonus_total > 0:
                report.earnings_breakdown.append(("Bonuses", record.bonus_total))

            # Deductions
            for deduction_name, amount in record.deduction_details:
                report.deductions_breakdown.append((deduction_name, amount))

            # Taxes
            if record.federal_tax > 0:
                report.taxes_breakdown.append(("Federal Tax", record.federal_tax))
            if record.state_tax > 0:
                report.taxes_breakdown.append(("State Tax", record.state_tax))
            if record.social_security > 0:
                report.taxes_breakdown.append(("Social Security", record.social_security))
            if record.medicare > 0:
                report.taxes_breakdown.append(("Medicare", record.medicare))

        # YTD data
        report.ytd_gross = ytd_data.get("gross", Decimal("0"))
        report.ytd_net = ytd_data.get("net", Decimal("0"))
        report.ytd_taxes = ytd_data.get("taxes", Decimal("0"))
        report.ytd_deductions = ytd_data.get("deductions", Decimal("0"))

        logger.info(f"Generated earnings report for {employee.full_name}")
        return report

    def generate_tax_liability_report(
        self,
        payroll_runs: List[Any],
        start_date: date,
        end_date: date
    ) -> TaxLiabilityReport:
        """Generate tax liability report"""
        report = TaxLiabilityReport(
            period_start=start_date,
            period_end=end_date
        )

        # Filter runs
        period_runs = [
            run for run in payroll_runs
            if start_date <= run.pay_date <= end_date
        ]

        # Aggregate tax data
        for run in period_runs:
            for record in run.payment_records:
                # Employee taxes (withheld)
                report.federal_income_tax += record.federal_tax
                report.state_income_tax += record.state_tax
                report.local_income_tax += record.local_tax
                report.social_security_employee += record.social_security
                report.medicare_employee += record.medicare

                # Employer matching (FICA)
                report.social_security_employer += record.social_security
                report.medicare_employer += record.medicare

                # Employee detail
                report.employee_details.append({
                    "employee_id": record.employee_id,
                    "employee_name": record.employee_name,
                    "federal_tax": float(record.federal_tax),
                    "state_tax": float(record.state_tax),
                    "fica": float(record.social_security + record.medicare),
                    "total": float(record.total_taxes),
                })

        # Calculate totals
        report.total_employee_taxes = (
            report.federal_income_tax +
            report.state_income_tax +
            report.local_income_tax +
            report.social_security_employee +
            report.medicare_employee +
            report.state_disability
        )

        report.total_employer_taxes = (
            report.social_security_employer +
            report.medicare_employer +
            report.futa +
            report.state_unemployment_tax
        )

        report.total_tax_liability = (
            report.total_employee_taxes + report.total_employer_taxes
        )

        logger.info(
            f"Generated tax liability report: "
            f"${report.total_tax_liability} total liability"
        )

        return report

    def generate_department_cost_report(
        self,
        department: str,
        employees: List[Any],
        payment_records: List[Any],
        start_date: date,
        end_date: date
    ) -> DepartmentCostReport:
        """Generate department labor cost analysis"""
        dept_employees = [emp for emp in employees if emp.department == department]

        report = DepartmentCostReport(
            department=department,
            cost_center=dept_employees[0].cost_center if dept_employees else "",
            period_start=start_date,
            period_end=end_date,
            employee_count=len(dept_employees)
        )

        # Get employee IDs
        emp_ids = {emp.id for emp in dept_employees}

        # Aggregate costs
        employee_totals = defaultdict(Decimal)
        emp_type_costs = defaultdict(Decimal)

        for record in payment_records:
            if record.employee_id not in emp_ids:
                continue

            if not (start_date <= record.pay_date <= end_date):
                continue

            # Compensation
            report.total_compensation += record.gross_pay

            # Benefits (deductions)
            report.total_benefits += (record.pre_tax_deductions + record.post_tax_deductions)

            # Taxes
            report.total_taxes += record.total_taxes

            # Hours
            report.total_hours += (record.regular_hours + record.overtime_hours)

            # Per employee
            employee_totals[record.employee_name] += record.gross_pay

            # By type
            emp = next((e for e in dept_employees if e.id == record.employee_id), None)
            if emp:
                emp_type = emp.employment_type.value if hasattr(emp.employment_type, 'value') else str(emp.employment_type)
                emp_type_costs[emp_type] += record.gross_pay

        # Calculate totals
        report.total_cost = (
            report.total_compensation +
            report.total_benefits +
            report.total_taxes
        )

        # Averages
        if report.employee_count > 0:
            report.avg_compensation_per_employee = report.total_compensation / Decimal(report.employee_count)
            report.avg_total_cost_per_employee = report.total_cost / Decimal(report.employee_count)

        if report.total_hours > 0:
            report.cost_per_hour = report.total_cost / report.total_hours

        # Top earners
        report.top_earners = sorted(
            employee_totals.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        report.by_employee_type = dict(emp_type_costs)

        logger.info(f"Generated department cost report for {department}")
        return report

    def export_to_json(self, report: Any) -> str:
        """Export report to JSON"""
        def decimal_default(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            if isinstance(obj, (date, datetime)):
                return obj.isoformat()
            raise TypeError

        return json.dumps(report.__dict__, default=decimal_default, indent=2)

    def export_to_csv(self, report: PayrollSummaryReport) -> str:
        """Export payroll summary to CSV"""
        lines = []

        # Header
        lines.append("Payroll Summary Report")
        lines.append(f"Period: {report.period_start} to {report.period_end}")
        lines.append("")

        # Employee summary
        lines.append("Employee Summary")
        lines.append("Metric,Value")
        lines.append(f"Total Employees,{report.total_employees}")
        lines.append(f"Active Employees,{report.active_employees}")
        lines.append(f"New Hires,{report.new_hires}")
        lines.append(f"Terminations,{report.terminations}")
        lines.append("")

        # Compensation
        lines.append("Compensation Summary")
        lines.append("Category,Amount")
        lines.append(f"Gross Pay,${float(report.total_gross_pay):,.2f}")
        lines.append(f"Regular Pay,${float(report.total_regular_pay):,.2f}")
        lines.append(f"Overtime Pay,${float(report.total_overtime_pay):,.2f}")
        lines.append(f"Bonus Pay,${float(report.total_bonus_pay):,.2f}")
        lines.append("")

        # Deductions and taxes
        lines.append("Deductions,${0:,.2f}".format(float(report.total_deductions)))
        lines.append("Taxes,${0:,.2f}".format(float(report.total_taxes)))
        lines.append("Net Pay,${0:,.2f}".format(float(report.total_net_pay)))
        lines.append("")

        # By department
        if report.by_department:
            lines.append("By Department")
            lines.append("Department,Gross Pay")
            for dept, amount in sorted(report.by_department.items()):
                lines.append(f"{dept},${float(amount):,.2f}")

        return "\n".join(lines)

    def export_to_html(self, report: PayrollSummaryReport) -> str:
        """Export payroll summary to HTML"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Payroll Summary Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th {{ background: #007bff; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        .amount {{ text-align: right; font-family: monospace; }}
        .section {{ margin: 30px 0; }}
    </style>
</head>
<body>
    <h1>Payroll Summary Report</h1>
    <p>Period: {report.period_start} to {report.period_end}</p>

    <div class="section">
        <h2>Employee Summary</h2>
        <table>
            <tr><td>Total Employees</td><td class="amount">{report.total_employees}</td></tr>
            <tr><td>Active Employees</td><td class="amount">{report.active_employees}</td></tr>
            <tr><td>New Hires</td><td class="amount">{report.new_hires}</td></tr>
            <tr><td>Terminations</td><td class="amount">{report.terminations}</td></tr>
        </table>
    </div>

    <div class="section">
        <h2>Compensation</h2>
        <table>
            <tr><td>Gross Pay</td><td class="amount">${float(report.total_gross_pay):,.2f}</td></tr>
            <tr><td>Regular Pay</td><td class="amount">${float(report.total_regular_pay):,.2f}</td></tr>
            <tr><td>Overtime Pay</td><td class="amount">${float(report.total_overtime_pay):,.2f}</td></tr>
            <tr><td>Bonus Pay</td><td class="amount">${float(report.total_bonus_pay):,.2f}</td></tr>
        </table>
    </div>

    <div class="section">
        <h2>Deductions & Taxes</h2>
        <table>
            <tr><td>Total Deductions</td><td class="amount">${float(report.total_deductions):,.2f}</td></tr>
            <tr><td>Total Taxes</td><td class="amount">${float(report.total_taxes):,.2f}</td></tr>
            <tr><td><strong>Net Pay</strong></td><td class="amount"><strong>${float(report.total_net_pay):,.2f}</strong></td></tr>
        </table>
    </div>
</body>
</html>
"""
        return html


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    generator = ReportGenerator()

    # Create sample report
    report = PayrollSummaryReport(
        period_start=date(2024, 11, 1),
        period_end=date(2024, 11, 30),
        total_employees=50,
        active_employees=48,
        new_hires=3,
        terminations=2,
        total_gross_pay=Decimal("250000.00"),
        total_net_pay=Decimal("185000.00"),
        total_taxes=Decimal("45000.00"),
        total_deductions=Decimal("20000.00")
    )

    report.by_department = {
        "Engineering": Decimal("120000.00"),
        "Sales": Decimal("80000.00"),
        "Operations": Decimal("50000.00"),
    }

    # Export to different formats
    json_export = generator.export_to_json(report)
    print("JSON Export:")
    print(json_export[:500])

    csv_export = generator.export_to_csv(report)
    print("\nCSV Export:")
    print(csv_export)
