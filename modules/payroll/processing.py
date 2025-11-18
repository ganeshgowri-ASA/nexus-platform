"""
Enterprise Payroll Processing Engine
Handles salary calculations, deductions, bonuses, overtime, and multi-currency processing
Production-ready, type-safe implementation rivaling ADP/Gusto
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Callable
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)


class PayFrequency(Enum):
    """Pay period frequencies"""
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    SEMIMONTHLY = "semimonthly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class EmploymentType(Enum):
    """Employment types"""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    TEMPORARY = "temporary"
    SEASONAL = "seasonal"


class DeductionType(Enum):
    """Types of payroll deductions"""
    PRE_TAX = "pre_tax"  # 401k, HSA, etc.
    POST_TAX = "post_tax"  # Roth 401k, garnishments
    BENEFIT = "benefit"  # Health insurance, life insurance
    LOAN = "loan"  # Employee loans, advances
    GARNISHMENT = "garnishment"  # Court-ordered deductions


class PaymentStatus(Enum):
    """Payroll processing status"""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Currency:
    """Multi-currency support"""
    code: str  # ISO 4217 code (USD, EUR, GBP, etc.)
    symbol: str
    decimal_places: int = 2
    exchange_rate: Decimal = Decimal("1.0")  # Rate to base currency

    def convert_to_base(self, amount: Decimal) -> Decimal:
        """Convert amount to base currency"""
        return amount * self.exchange_rate

    def convert_from_base(self, amount: Decimal) -> Decimal:
        """Convert amount from base currency"""
        return amount / self.exchange_rate


@dataclass
class Deduction:
    """Payroll deduction configuration"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    deduction_type: DeductionType = DeductionType.POST_TAX
    amount: Decimal = Decimal("0")
    percentage: Optional[Decimal] = None  # If percentage-based
    max_amount: Optional[Decimal] = None  # Maximum deduction per period
    annual_max: Optional[Decimal] = None  # Annual maximum
    priority: int = 0  # Deduction order (lower = higher priority)
    active: bool = True
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def calculate_amount(self, gross_pay: Decimal, ytd_amount: Decimal = Decimal("0")) -> Decimal:
        """Calculate deduction amount for this period"""
        if not self.active:
            return Decimal("0")

        # Calculate based on percentage or fixed amount
        if self.percentage:
            calculated = gross_pay * (self.percentage / Decimal("100"))
        else:
            calculated = self.amount

        # Apply maximum constraints
        if self.max_amount and calculated > self.max_amount:
            calculated = self.max_amount

        if self.annual_max:
            remaining = self.annual_max - ytd_amount
            if remaining <= 0:
                return Decimal("0")
            calculated = min(calculated, remaining)

        return calculated.quantize(Decimal("0.01"))


@dataclass
class Bonus:
    """Bonus/commission structure"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    amount: Decimal = Decimal("0")
    bonus_type: str = "one_time"  # one_time, recurring, commission, performance
    taxable: bool = True
    pay_date: Optional[date] = None
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OvertimeRule:
    """Overtime calculation rules"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = "Standard Overtime"
    threshold_hours: Decimal = Decimal("40")  # Hours per week before OT
    multiplier: Decimal = Decimal("1.5")  # Pay multiplier (1.5x, 2x, etc.)
    daily_threshold: Optional[Decimal] = None  # Daily OT threshold
    double_time_threshold: Optional[Decimal] = None  # Double-time threshold
    double_time_multiplier: Decimal = Decimal("2.0")


@dataclass
class Employee:
    """Employee payroll information"""
    id: str = field(default_factory=lambda: str(uuid4()))
    employee_number: str = ""
    first_name: str = ""
    last_name: str = ""
    email: str = ""

    # Employment details
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    hire_date: date = field(default_factory=date.today)
    termination_date: Optional[date] = None

    # Compensation
    base_salary: Decimal = Decimal("0")  # Annual for salaried, hourly rate for hourly
    pay_frequency: PayFrequency = PayFrequency.BIWEEKLY
    currency: Currency = field(default_factory=lambda: Currency("USD", "$"))
    is_salaried: bool = True

    # Deductions and benefits
    deductions: List[Deduction] = field(default_factory=list)
    recurring_bonuses: List[Bonus] = field(default_factory=list)

    # Overtime
    overtime_eligible: bool = False
    overtime_rule: Optional[OvertimeRule] = None

    # Tax and compliance
    tax_exempt: bool = False
    tax_jurisdiction: str = "US"

    # Banking
    bank_account: Optional[str] = None
    routing_number: Optional[str] = None

    # Metadata
    department: str = ""
    cost_center: str = ""
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def full_name(self) -> str:
        """Get employee full name"""
        return f"{self.first_name} {self.last_name}"

    def get_pay_period_salary(self) -> Decimal:
        """Calculate base pay for one period"""
        if not self.is_salaried:
            return Decimal("0")  # Hourly employees don't have period salary

        periods_per_year = {
            PayFrequency.WEEKLY: 52,
            PayFrequency.BIWEEKLY: 26,
            PayFrequency.SEMIMONTHLY: 24,
            PayFrequency.MONTHLY: 12,
            PayFrequency.QUARTERLY: 4,
            PayFrequency.ANNUAL: 1,
        }

        periods = periods_per_year.get(self.pay_frequency, 26)
        return (self.base_salary / Decimal(periods)).quantize(Decimal("0.01"))


@dataclass
class TimeEntry:
    """Time tracking entry for hourly employees"""
    id: str = field(default_factory=lambda: str(uuid4()))
    employee_id: str = ""
    date: date = field(default_factory=date.today)
    regular_hours: Decimal = Decimal("0")
    overtime_hours: Decimal = Decimal("0")
    double_time_hours: Decimal = Decimal("0")
    pto_hours: Decimal = Decimal("0")
    sick_hours: Decimal = Decimal("0")
    holiday_hours: Decimal = Decimal("0")
    approved: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    notes: str = ""


@dataclass
class PayrollRun:
    """A complete payroll processing run"""
    id: str = field(default_factory=lambda: str(uuid4()))
    run_number: str = ""
    pay_period_start: date = field(default_factory=date.today)
    pay_period_end: date = field(default_factory=date.today)
    pay_date: date = field(default_factory=date.today)
    status: PaymentStatus = PaymentStatus.DRAFT

    # Processing metadata
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    processed_at: Optional[datetime] = None

    # Totals
    total_gross_pay: Decimal = Decimal("0")
    total_deductions: Decimal = Decimal("0")
    total_taxes: Decimal = Decimal("0")
    total_net_pay: Decimal = Decimal("0")
    employee_count: int = 0

    # Records
    payment_records: List['PaymentRecord'] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PaymentRecord:
    """Individual employee payment record"""
    id: str = field(default_factory=lambda: str(uuid4()))
    payroll_run_id: str = ""
    employee_id: str = ""
    employee_name: str = ""

    # Pay period
    pay_period_start: date = field(default_factory=date.today)
    pay_period_end: date = field(default_factory=date.today)
    pay_date: date = field(default_factory=date.today)

    # Earnings
    regular_hours: Decimal = Decimal("0")
    overtime_hours: Decimal = Decimal("0")
    double_time_hours: Decimal = Decimal("0")
    regular_pay: Decimal = Decimal("0")
    overtime_pay: Decimal = Decimal("0")
    double_time_pay: Decimal = Decimal("0")
    bonuses: List[Bonus] = field(default_factory=list)
    bonus_total: Decimal = Decimal("0")
    gross_pay: Decimal = Decimal("0")

    # Deductions
    pre_tax_deductions: Decimal = Decimal("0")
    post_tax_deductions: Decimal = Decimal("0")
    deduction_details: List[Tuple[str, Decimal]] = field(default_factory=list)

    # Taxes
    federal_tax: Decimal = Decimal("0")
    state_tax: Decimal = Decimal("0")
    local_tax: Decimal = Decimal("0")
    social_security: Decimal = Decimal("0")
    medicare: Decimal = Decimal("0")
    total_taxes: Decimal = Decimal("0")

    # Net pay
    net_pay: Decimal = Decimal("0")

    # Currency
    currency: Currency = field(default_factory=lambda: Currency("USD", "$"))

    # YTD totals
    ytd_gross: Decimal = Decimal("0")
    ytd_taxes: Decimal = Decimal("0")
    ytd_net: Decimal = Decimal("0")

    # Status
    status: PaymentStatus = PaymentStatus.DRAFT
    errors: List[str] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)


class PayrollProcessor:
    """
    Enterprise payroll processing engine
    Handles complete payroll lifecycle with integrations
    """

    def __init__(self):
        self.employees: Dict[str, Employee] = {}
        self.payroll_runs: Dict[str, PayrollRun] = {}
        self.time_entries: Dict[str, List[TimeEntry]] = {}
        self.currency_rates: Dict[str, Currency] = {
            "USD": Currency("USD", "$", 2, Decimal("1.0")),
            "EUR": Currency("EUR", "€", 2, Decimal("1.1")),
            "GBP": Currency("GBP", "£", 2, Decimal("1.27")),
            "CAD": Currency("CAD", "C$", 2, Decimal("0.74")),
        }
        self.tax_calculator: Optional[Callable] = None
        self.pre_process_hooks: List[Callable] = []
        self.post_process_hooks: List[Callable] = []

    def register_employee(self, employee: Employee) -> None:
        """Register an employee in the payroll system"""
        if not employee.employee_number:
            employee.employee_number = f"EMP{len(self.employees) + 1:06d}"

        self.employees[employee.id] = employee
        logger.info(f"Registered employee: {employee.full_name} ({employee.employee_number})")

    def add_time_entry(self, entry: TimeEntry) -> None:
        """Add time entry for hourly employee"""
        if entry.employee_id not in self.employees:
            raise ValueError(f"Employee {entry.employee_id} not found")

        if entry.employee_id not in self.time_entries:
            self.time_entries[entry.employee_id] = []

        self.time_entries[entry.employee_id].append(entry)
        logger.info(f"Added time entry for employee {entry.employee_id}: {entry.regular_hours}h")

    def calculate_overtime(
        self,
        employee: Employee,
        hours: Decimal,
        rule: OvertimeRule
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Calculate regular, overtime, and double-time hours
        Returns: (regular_hours, overtime_hours, double_time_hours)
        """
        regular_hours = Decimal("0")
        overtime_hours = Decimal("0")
        double_time_hours = Decimal("0")

        if hours <= rule.threshold_hours:
            regular_hours = hours
        else:
            regular_hours = rule.threshold_hours
            excess_hours = hours - rule.threshold_hours

            if rule.double_time_threshold and excess_hours > rule.double_time_threshold:
                overtime_hours = rule.double_time_threshold
                double_time_hours = excess_hours - rule.double_time_threshold
            else:
                overtime_hours = excess_hours

        return regular_hours, overtime_hours, double_time_hours

    def calculate_employee_pay(
        self,
        employee: Employee,
        pay_period_start: date,
        pay_period_end: date,
        bonuses: Optional[List[Bonus]] = None,
        ytd_deductions: Optional[Dict[str, Decimal]] = None
    ) -> PaymentRecord:
        """
        Calculate complete pay for an employee for a pay period
        This is the core processing engine
        """
        record = PaymentRecord(
            employee_id=employee.id,
            employee_name=employee.full_name,
            pay_period_start=pay_period_start,
            pay_period_end=pay_period_end,
            currency=employee.currency
        )

        if ytd_deductions is None:
            ytd_deductions = {}

        try:
            # Calculate base pay
            if employee.is_salaried:
                # Salaried employee
                record.regular_pay = employee.get_pay_period_salary()
                record.regular_hours = Decimal("0")  # Not applicable for salaried
            else:
                # Hourly employee - aggregate time entries
                entries = self.time_entries.get(employee.id, [])
                period_entries = [
                    e for e in entries
                    if pay_period_start <= e.date <= pay_period_end and e.approved
                ]

                total_regular = sum(e.regular_hours for e in period_entries)
                total_overtime = sum(e.overtime_hours for e in period_entries)
                total_double = sum(e.double_time_hours for e in period_entries)

                # Apply overtime rules if needed
                if employee.overtime_eligible and employee.overtime_rule:
                    regular, ot, dt = self.calculate_overtime(
                        employee,
                        total_regular + total_overtime + total_double,
                        employee.overtime_rule
                    )
                    record.regular_hours = regular
                    record.overtime_hours = ot
                    record.double_time_hours = dt
                else:
                    record.regular_hours = total_regular
                    record.overtime_hours = Decimal("0")
                    record.double_time_hours = Decimal("0")

                # Calculate pay
                hourly_rate = employee.base_salary
                record.regular_pay = record.regular_hours * hourly_rate

                if employee.overtime_rule:
                    record.overtime_pay = (
                        record.overtime_hours * hourly_rate * employee.overtime_rule.multiplier
                    )
                    record.double_time_pay = (
                        record.double_time_hours * hourly_rate * employee.overtime_rule.double_time_multiplier
                    )

            # Add bonuses
            if bonuses:
                record.bonuses = bonuses
                record.bonus_total = sum(b.amount for b in bonuses if b.taxable)

            # Calculate gross pay
            record.gross_pay = (
                record.regular_pay +
                record.overtime_pay +
                record.double_time_pay +
                record.bonus_total
            )

            # Calculate pre-tax deductions
            pre_tax_total = Decimal("0")
            for deduction in employee.deductions:
                if deduction.deduction_type == DeductionType.PRE_TAX and deduction.active:
                    ytd = ytd_deductions.get(deduction.id, Decimal("0"))
                    amount = deduction.calculate_amount(record.gross_pay, ytd)
                    if amount > 0:
                        pre_tax_total += amount
                        record.deduction_details.append((deduction.name, amount))

            record.pre_tax_deductions = pre_tax_total

            # Calculate taxable income
            taxable_income = record.gross_pay - record.pre_tax_deductions

            # Calculate taxes (use injected calculator if available)
            if self.tax_calculator and not employee.tax_exempt:
                tax_details = self.tax_calculator(employee, taxable_income, pay_period_start)
                record.federal_tax = tax_details.get("federal", Decimal("0"))
                record.state_tax = tax_details.get("state", Decimal("0"))
                record.local_tax = tax_details.get("local", Decimal("0"))
                record.social_security = tax_details.get("social_security", Decimal("0"))
                record.medicare = tax_details.get("medicare", Decimal("0"))

            record.total_taxes = (
                record.federal_tax +
                record.state_tax +
                record.local_tax +
                record.social_security +
                record.medicare
            )

            # Calculate post-tax deductions
            post_tax_total = Decimal("0")
            for deduction in employee.deductions:
                if deduction.deduction_type != DeductionType.PRE_TAX and deduction.active:
                    ytd = ytd_deductions.get(deduction.id, Decimal("0"))
                    amount = deduction.calculate_amount(record.gross_pay, ytd)
                    if amount > 0:
                        post_tax_total += amount
                        record.deduction_details.append((deduction.name, amount))

            record.post_tax_deductions = post_tax_total

            # Calculate net pay
            record.net_pay = (
                record.gross_pay -
                record.pre_tax_deductions -
                record.total_taxes -
                record.post_tax_deductions
            )

            # Round to currency decimal places
            dp = Decimal("0.01")
            record.gross_pay = record.gross_pay.quantize(dp)
            record.net_pay = record.net_pay.quantize(dp)
            record.total_taxes = record.total_taxes.quantize(dp)

            record.status = PaymentStatus.PENDING_APPROVAL

        except Exception as e:
            logger.error(f"Error calculating pay for {employee.full_name}: {e}")
            record.status = PaymentStatus.FAILED
            record.errors.append(str(e))

        return record

    def create_payroll_run(
        self,
        pay_period_start: date,
        pay_period_end: date,
        pay_date: date,
        employee_ids: Optional[List[str]] = None,
        created_by: str = "system"
    ) -> PayrollRun:
        """
        Create and process a complete payroll run
        """
        run = PayrollRun(
            run_number=f"PR{datetime.now().strftime('%Y%m%d%H%M%S')}",
            pay_period_start=pay_period_start,
            pay_period_end=pay_period_end,
            pay_date=pay_date,
            created_by=created_by,
            status=PaymentStatus.PROCESSING
        )

        logger.info(f"Creating payroll run {run.run_number} for period {pay_period_start} to {pay_period_end}")

        # Execute pre-process hooks
        for hook in self.pre_process_hooks:
            try:
                hook(run)
            except Exception as e:
                logger.error(f"Pre-process hook failed: {e}")
                run.warnings.append(f"Pre-process hook error: {e}")

        # Determine which employees to process
        if employee_ids:
            employees_to_process = [
                self.employees[eid] for eid in employee_ids
                if eid in self.employees
            ]
        else:
            employees_to_process = [
                emp for emp in self.employees.values()
                if emp.active and (not emp.termination_date or emp.termination_date >= pay_period_end)
            ]

        # Process each employee
        for employee in employees_to_process:
            try:
                # Get any one-time bonuses for this period
                bonuses = [
                    b for b in employee.recurring_bonuses
                    if not b.pay_date or (pay_period_start <= b.pay_date <= pay_period_end)
                ]

                # Calculate YTD deductions (simplified - in production, query from database)
                ytd_deductions: Dict[str, Decimal] = {}

                # Process employee payment
                record = self.calculate_employee_pay(
                    employee,
                    pay_period_start,
                    pay_period_end,
                    bonuses,
                    ytd_deductions
                )

                record.payroll_run_id = run.id
                run.payment_records.append(record)

                # Update run totals
                if record.status != PaymentStatus.FAILED:
                    run.total_gross_pay += record.gross_pay
                    run.total_deductions += (record.pre_tax_deductions + record.post_tax_deductions)
                    run.total_taxes += record.total_taxes
                    run.total_net_pay += record.net_pay
                    run.employee_count += 1
                else:
                    run.errors.extend(record.errors)

            except Exception as e:
                error_msg = f"Failed to process employee {employee.full_name}: {e}"
                logger.error(error_msg)
                run.errors.append(error_msg)

        # Finalize run
        run.processed_at = datetime.now()
        run.status = PaymentStatus.PENDING_APPROVAL if not run.errors else PaymentStatus.FAILED

        # Execute post-process hooks
        for hook in self.post_process_hooks:
            try:
                hook(run)
            except Exception as e:
                logger.error(f"Post-process hook failed: {e}")
                run.warnings.append(f"Post-process hook error: {e}")

        # Store run
        self.payroll_runs[run.id] = run

        logger.info(
            f"Payroll run {run.run_number} completed: "
            f"{run.employee_count} employees, "
            f"${run.total_net_pay} total net pay"
        )

        return run

    def approve_payroll_run(self, run_id: str, approved_by: str) -> bool:
        """Approve a payroll run for processing"""
        if run_id not in self.payroll_runs:
            raise ValueError(f"Payroll run {run_id} not found")

        run = self.payroll_runs[run_id]

        if run.status != PaymentStatus.PENDING_APPROVAL:
            raise ValueError(f"Payroll run is in {run.status.value} status, cannot approve")

        run.status = PaymentStatus.APPROVED
        run.approved_by = approved_by
        run.approved_at = datetime.now()

        # Update all payment records
        for record in run.payment_records:
            if record.status == PaymentStatus.PENDING_APPROVAL:
                record.status = PaymentStatus.APPROVED

        logger.info(f"Payroll run {run.run_number} approved by {approved_by}")
        return True

    def get_payroll_summary(self, run_id: str) -> Dict[str, Any]:
        """Get detailed summary of a payroll run"""
        if run_id not in self.payroll_runs:
            raise ValueError(f"Payroll run {run_id} not found")

        run = self.payroll_runs[run_id]

        return {
            "run_number": run.run_number,
            "pay_period": f"{run.pay_period_start} to {run.pay_period_end}",
            "pay_date": run.pay_date.isoformat(),
            "status": run.status.value,
            "employee_count": run.employee_count,
            "total_gross_pay": float(run.total_gross_pay),
            "total_deductions": float(run.total_deductions),
            "total_taxes": float(run.total_taxes),
            "total_net_pay": float(run.total_net_pay),
            "errors": run.errors,
            "warnings": run.warnings,
            "created_by": run.created_by,
            "created_at": run.created_at.isoformat(),
            "approved_by": run.approved_by,
            "approved_at": run.approved_at.isoformat() if run.approved_at else None,
        }

    def register_tax_calculator(self, calculator: Callable) -> None:
        """Register external tax calculation function"""
        self.tax_calculator = calculator
        logger.info("Tax calculator registered")

    def add_pre_process_hook(self, hook: Callable) -> None:
        """Add pre-processing hook"""
        self.pre_process_hooks.append(hook)

    def add_post_process_hook(self, hook: Callable) -> None:
        """Add post-processing hook"""
        self.post_process_hooks.append(hook)


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Initialize processor
    processor = PayrollProcessor()

    # Create sample employees
    emp1 = Employee(
        employee_number="EMP001",
        first_name="John",
        last_name="Doe",
        email="john.doe@company.com",
        base_salary=Decimal("75000"),
        pay_frequency=PayFrequency.BIWEEKLY,
        is_salaried=True,
        department="Engineering",
        deductions=[
            Deduction(
                name="401(k)",
                deduction_type=DeductionType.PRE_TAX,
                percentage=Decimal("6"),
                annual_max=Decimal("22500")
            ),
            Deduction(
                name="Health Insurance",
                deduction_type=DeductionType.BENEFIT,
                amount=Decimal("150")
            )
        ]
    )

    emp2 = Employee(
        employee_number="EMP002",
        first_name="Jane",
        last_name="Smith",
        email="jane.smith@company.com",
        base_salary=Decimal("35"),  # $35/hour
        pay_frequency=PayFrequency.BIWEEKLY,
        is_salaried=False,
        overtime_eligible=True,
        overtime_rule=OvertimeRule(),
        department="Operations"
    )

    # Register employees
    processor.register_employee(emp1)
    processor.register_employee(emp2)

    # Add time entries for hourly employee
    processor.add_time_entry(TimeEntry(
        employee_id=emp2.id,
        date=date(2024, 11, 1),
        regular_hours=Decimal("45"),
        approved=True
    ))

    # Create payroll run
    run = processor.create_payroll_run(
        pay_period_start=date(2024, 11, 1),
        pay_period_end=date(2024, 11, 14),
        pay_date=date(2024, 11, 20),
        created_by="admin"
    )

    # Print summary
    summary = processor.get_payroll_summary(run.id)
    print(f"\nPayroll Run Summary:")
    print(f"  Employees: {summary['employee_count']}")
    print(f"  Gross Pay: ${summary['total_gross_pay']:,.2f}")
    print(f"  Net Pay: ${summary['total_net_pay']:,.2f}")
    print(f"  Status: {summary['status']}")
