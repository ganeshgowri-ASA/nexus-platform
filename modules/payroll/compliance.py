"""
Enterprise Payroll Compliance System
Handles tax forms (W-2, 1099, W-4), labor law compliance, audit trails, and regulatory reporting
Production-ready with automated compliance checks and reporting
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Tuple
import logging
import json
from uuid import uuid4

logger = logging.getLogger(__name__)


class TaxFormType(Enum):
    """Federal tax form types"""
    W2 = "w2"  # Wage and Tax Statement
    W3 = "w3"  # Transmittal of Wage and Tax Statements
    W4 = "w4"  # Employee's Withholding Certificate
    FORM_1099_MISC = "1099_misc"  # Miscellaneous Income
    FORM_1099_NEC = "1099_nec"  # Nonemployee Compensation
    FORM_940 = "940"  # Employer's Annual Federal Unemployment Tax Return
    FORM_941 = "941"  # Employer's Quarterly Federal Tax Return
    FORM_944 = "944"  # Employer's Annual Federal Tax Return


class ComplianceStatus(Enum):
    """Compliance check status"""
    COMPLIANT = "compliant"
    WARNING = "warning"
    VIOLATION = "violation"
    PENDING_REVIEW = "pending_review"


class LaborLawType(Enum):
    """Labor law categories"""
    MINIMUM_WAGE = "minimum_wage"
    OVERTIME = "overtime"
    CHILD_LABOR = "child_labor"
    BREAK_REQUIREMENTS = "break_requirements"
    PAID_SICK_LEAVE = "paid_sick_leave"
    FAMILY_LEAVE = "family_leave"
    EQUAL_PAY = "equal_pay"
    WORKPLACE_SAFETY = "workplace_safety"


class AuditEventType(Enum):
    """Audit trail event types"""
    PAYROLL_RUN = "payroll_run"
    PAYMENT_PROCESSED = "payment_processed"
    TAX_CALCULATED = "tax_calculated"
    EMPLOYEE_CREATED = "employee_created"
    EMPLOYEE_UPDATED = "employee_updated"
    EMPLOYEE_TERMINATED = "employee_terminated"
    BANK_ACCOUNT_ADDED = "bank_account_added"
    DEDUCTION_CHANGED = "deduction_changed"
    SALARY_CHANGED = "salary_changed"
    TAX_FORM_GENERATED = "tax_form_generated"
    COMPLIANCE_CHECK = "compliance_check"
    REPORT_GENERATED = "report_generated"


@dataclass
class W2Form:
    """W-2 Wage and Tax Statement"""
    id: str = field(default_factory=lambda: str(uuid4()))
    tax_year: int = 2024

    # Employer information
    employer_ein: str = ""
    employer_name: str = ""
    employer_address: str = ""
    employer_city: str = ""
    employer_state: str = ""
    employer_zip: str = ""

    # Employee information
    employee_ssn: str = ""
    employee_first_name: str = ""
    employee_last_name: str = ""
    employee_address: str = ""
    employee_city: str = ""
    employee_state: str = ""
    employee_zip: str = ""

    # Box 1: Wages, tips, other compensation
    wages_tips_compensation: Decimal = Decimal("0")

    # Box 2: Federal income tax withheld
    federal_tax_withheld: Decimal = Decimal("0")

    # Box 3: Social Security wages
    social_security_wages: Decimal = Decimal("0")

    # Box 4: Social Security tax withheld
    social_security_tax: Decimal = Decimal("0")

    # Box 5: Medicare wages and tips
    medicare_wages: Decimal = Decimal("0")

    # Box 6: Medicare tax withheld
    medicare_tax: Decimal = Decimal("0")

    # Box 7: Social Security tips
    social_security_tips: Decimal = Decimal("0")

    # Box 8: Allocated tips
    allocated_tips: Decimal = Decimal("0")

    # Box 10: Dependent care benefits
    dependent_care_benefits: Decimal = Decimal("0")

    # Box 11: Nonqualified plans
    nonqualified_plans: Decimal = Decimal("0")

    # Box 12: Codes and amounts
    box_12_codes: List[Tuple[str, Decimal]] = field(default_factory=list)

    # Box 13: Checkboxes
    statutory_employee: bool = False
    retirement_plan: bool = False
    third_party_sick_pay: bool = False

    # Box 14: Other
    other_deductions: List[Tuple[str, Decimal]] = field(default_factory=list)

    # State and local information
    state_wages: Dict[str, Decimal] = field(default_factory=dict)
    state_tax: Dict[str, Decimal] = field(default_factory=dict)
    local_wages: Dict[str, Decimal] = field(default_factory=dict)
    local_tax: Dict[str, Decimal] = field(default_factory=dict)

    # Metadata
    generated_at: datetime = field(default_factory=datetime.now)
    corrected: bool = False
    void: bool = False


@dataclass
class Form941:
    """Employer's Quarterly Federal Tax Return"""
    id: str = field(default_factory=lambda: str(uuid4()))
    year: int = 2024
    quarter: int = 1  # 1-4

    # Employer information
    employer_ein: str = ""
    employer_name: str = ""
    employer_address: str = ""

    # Line 1: Number of employees who received wages
    number_of_employees: int = 0

    # Line 2: Total wages, tips, and other compensation
    total_wages: Decimal = Decimal("0")

    # Line 3: Federal income tax withheld
    federal_tax_withheld: Decimal = Decimal("0")

    # Line 5: Taxable Social Security wages/tips
    ss_wages: Decimal = Decimal("0")
    ss_tax: Decimal = Decimal("0")

    # Line 5c: Taxable Medicare wages/tips
    medicare_wages: Decimal = Decimal("0")
    medicare_tax: Decimal = Decimal("0")

    # Total taxes
    total_taxes: Decimal = Decimal("0")

    # Deposits
    total_deposits: Decimal = Decimal("0")

    # Balance
    balance_due: Decimal = Decimal("0")
    overpayment: Decimal = Decimal("0")

    # Monthly tax liability
    month1_liability: Decimal = Decimal("0")
    month2_liability: Decimal = Decimal("0")
    month3_liability: Decimal = Decimal("0")

    # Metadata
    generated_at: datetime = field(default_factory=datetime.now)
    filed_at: Optional[datetime] = None


@dataclass
class ComplianceRule:
    """Compliance rule definition"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    law_type: LaborLawType = LaborLawType.MINIMUM_WAGE
    jurisdiction: str = "US"  # US, state code, or locality
    effective_date: date = field(default_factory=date.today)
    expiration_date: Optional[date] = None

    # Rule parameters (flexible for different rule types)
    parameters: Dict[str, Any] = field(default_factory=dict)

    active: bool = True


@dataclass
class ComplianceViolation:
    """Compliance violation record"""
    id: str = field(default_factory=lambda: str(uuid4()))
    rule_id: str = ""
    rule_name: str = ""
    severity: ComplianceStatus = ComplianceStatus.WARNING

    # What was violated
    employee_id: Optional[str] = None
    payroll_run_id: Optional[str] = None

    # Violation details
    description: str = ""
    detected_value: Any = None
    expected_value: Any = None

    # Resolution
    detected_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: str = ""

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditLogEntry:
    """Audit trail entry"""
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    event_type: AuditEventType = AuditEventType.PAYROLL_RUN

    # Who performed the action
    user_id: str = ""
    user_name: str = ""
    ip_address: Optional[str] = None

    # What was affected
    entity_type: str = ""  # employee, payroll_run, etc.
    entity_id: str = ""

    # What changed
    action: str = ""  # created, updated, deleted, processed
    old_values: Dict[str, Any] = field(default_factory=dict)
    new_values: Dict[str, Any] = field(default_factory=dict)

    # Additional context
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class ComplianceEngine:
    """
    Payroll compliance engine
    Handles regulatory compliance, audit trails, and reporting
    """

    def __init__(self):
        self.compliance_rules: Dict[str, ComplianceRule] = {}
        self.violations: List[ComplianceViolation] = []
        self.audit_log: List[AuditLogEntry] = []
        self.w2_forms: Dict[str, W2Form] = {}
        self.form_941s: Dict[str, Form941] = {}

        # Initialize default compliance rules
        self._initialize_default_rules()

    def _initialize_default_rules(self):
        """Initialize default compliance rules"""
        # Federal minimum wage
        self.add_compliance_rule(ComplianceRule(
            name="Federal Minimum Wage",
            description="Federal minimum wage must be at least $7.25/hour",
            law_type=LaborLawType.MINIMUM_WAGE,
            jurisdiction="US",
            parameters={
                "minimum_hourly_rate": Decimal("7.25")
            }
        ))

        # FLSA Overtime
        self.add_compliance_rule(ComplianceRule(
            name="FLSA Overtime",
            description="Non-exempt employees must receive 1.5x pay for hours over 40/week",
            law_type=LaborLawType.OVERTIME,
            jurisdiction="US",
            parameters={
                "threshold_hours": 40,
                "multiplier": Decimal("1.5")
            }
        ))

        # Social Security wage base
        self.add_compliance_rule(ComplianceRule(
            name="Social Security Wage Base 2024",
            description="Social Security tax applies up to $168,600 in 2024",
            law_type=LaborLawType.MINIMUM_WAGE,  # Using as placeholder
            jurisdiction="US",
            parameters={
                "wage_base": Decimal("168600")
            }
        ))

        # California minimum wage
        self.add_compliance_rule(ComplianceRule(
            name="California Minimum Wage",
            description="California minimum wage is $16.00/hour",
            law_type=LaborLawType.MINIMUM_WAGE,
            jurisdiction="CA",
            parameters={
                "minimum_hourly_rate": Decimal("16.00")
            }
        ))

        # New York minimum wage
        self.add_compliance_rule(ComplianceRule(
            name="New York Minimum Wage",
            description="New York minimum wage is $15.00/hour",
            law_type=LaborLawType.MINIMUM_WAGE,
            jurisdiction="NY",
            parameters={
                "minimum_hourly_rate": Decimal("15.00")
            }
        ))

    def add_compliance_rule(self, rule: ComplianceRule) -> None:
        """Add compliance rule"""
        self.compliance_rules[rule.id] = rule
        logger.info(f"Added compliance rule: {rule.name}")

    def check_minimum_wage_compliance(
        self,
        hourly_rate: Decimal,
        jurisdiction: str = "US"
    ) -> Tuple[bool, Optional[ComplianceViolation]]:
        """Check minimum wage compliance"""
        # Find applicable minimum wage rule
        applicable_rules = [
            rule for rule in self.compliance_rules.values()
            if rule.law_type == LaborLawType.MINIMUM_WAGE
            and rule.jurisdiction == jurisdiction
            and rule.active
        ]

        for rule in applicable_rules:
            min_wage = rule.parameters.get("minimum_hourly_rate", Decimal("0"))

            if hourly_rate < min_wage:
                violation = ComplianceViolation(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=ComplianceStatus.VIOLATION,
                    description=f"Hourly rate ${hourly_rate} is below minimum wage ${min_wage}",
                    detected_value=float(hourly_rate),
                    expected_value=float(min_wage)
                )
                self.violations.append(violation)
                logger.warning(f"Minimum wage violation: {violation.description}")
                return False, violation

        return True, None

    def check_overtime_compliance(
        self,
        regular_hours: Decimal,
        overtime_hours: Decimal,
        overtime_rate: Decimal,
        base_rate: Decimal,
        jurisdiction: str = "US"
    ) -> Tuple[bool, Optional[ComplianceViolation]]:
        """Check overtime compliance"""
        # Find applicable overtime rules
        applicable_rules = [
            rule for rule in self.compliance_rules.values()
            if rule.law_type == LaborLawType.OVERTIME
            and rule.jurisdiction == jurisdiction
            and rule.active
        ]

        for rule in applicable_rules:
            required_multiplier = rule.parameters.get("multiplier", Decimal("1.5"))
            expected_rate = base_rate * required_multiplier

            # Allow small rounding differences
            tolerance = Decimal("0.01")

            if overtime_hours > 0 and abs(overtime_rate - expected_rate) > tolerance:
                violation = ComplianceViolation(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=ComplianceStatus.VIOLATION,
                    description=f"Overtime rate ${overtime_rate} does not match required {required_multiplier}x rate ${expected_rate}",
                    detected_value=float(overtime_rate),
                    expected_value=float(expected_rate)
                )
                self.violations.append(violation)
                logger.warning(f"Overtime violation: {violation.description}")
                return False, violation

        return True, None

    def audit_payroll_run(
        self,
        payroll_run: Any,
        user_id: str,
        user_name: str
    ) -> None:
        """Create audit log entry for payroll run"""
        entry = AuditLogEntry(
            event_type=AuditEventType.PAYROLL_RUN,
            user_id=user_id,
            user_name=user_name,
            entity_type="payroll_run",
            entity_id=payroll_run.id,
            action="processed",
            description=f"Payroll run {payroll_run.run_number} processed",
            new_values={
                "run_number": payroll_run.run_number,
                "employee_count": payroll_run.employee_count,
                "total_gross": float(payroll_run.total_gross_pay),
                "total_net": float(payroll_run.total_net_pay),
                "pay_date": payroll_run.pay_date.isoformat(),
            }
        )

        self.audit_log.append(entry)
        logger.info(f"Audit log: Payroll run {payroll_run.run_number}")

    def audit_employee_change(
        self,
        employee_id: str,
        change_type: str,
        old_values: Dict[str, Any],
        new_values: Dict[str, Any],
        user_id: str,
        user_name: str
    ) -> None:
        """Create audit log entry for employee changes"""
        event_type_map = {
            "created": AuditEventType.EMPLOYEE_CREATED,
            "updated": AuditEventType.EMPLOYEE_UPDATED,
            "terminated": AuditEventType.EMPLOYEE_TERMINATED,
            "salary_changed": AuditEventType.SALARY_CHANGED,
        }

        entry = AuditLogEntry(
            event_type=event_type_map.get(change_type, AuditEventType.EMPLOYEE_UPDATED),
            user_id=user_id,
            user_name=user_name,
            entity_type="employee",
            entity_id=employee_id,
            action=change_type,
            old_values=old_values,
            new_values=new_values,
            description=f"Employee {employee_id} {change_type}"
        )

        self.audit_log.append(entry)
        logger.info(f"Audit log: Employee {employee_id} {change_type}")

    def generate_w2(
        self,
        employee: Any,
        ytd_data: Dict[str, Decimal],
        employer_info: Dict[str, str],
        tax_year: int = 2024
    ) -> W2Form:
        """Generate W-2 form for employee"""
        w2 = W2Form(
            tax_year=tax_year,

            # Employer
            employer_ein=employer_info.get("ein", ""),
            employer_name=employer_info.get("name", ""),
            employer_address=employer_info.get("address", ""),
            employer_city=employer_info.get("city", ""),
            employer_state=employer_info.get("state", ""),
            employer_zip=employer_info.get("zip", ""),

            # Employee
            employee_ssn=employee.metadata.get("ssn", ""),
            employee_first_name=employee.first_name,
            employee_last_name=employee.last_name,
            employee_address=employee.metadata.get("address", ""),
            employee_city=employee.metadata.get("city", ""),
            employee_state=employee.metadata.get("state", ""),
            employee_zip=employee.metadata.get("zip", ""),

            # Wages and withholdings
            wages_tips_compensation=ytd_data.get("gross_wages", Decimal("0")),
            federal_tax_withheld=ytd_data.get("federal_tax", Decimal("0")),
            social_security_wages=ytd_data.get("ss_wages", Decimal("0")),
            social_security_tax=ytd_data.get("ss_tax", Decimal("0")),
            medicare_wages=ytd_data.get("medicare_wages", Decimal("0")),
            medicare_tax=ytd_data.get("medicare_tax", Decimal("0")),
        )

        # Add to storage
        self.w2_forms[w2.id] = w2

        # Audit log
        self.audit_log.append(AuditLogEntry(
            event_type=AuditEventType.TAX_FORM_GENERATED,
            user_id="system",
            user_name="System",
            entity_type="w2_form",
            entity_id=w2.id,
            action="generated",
            description=f"W-2 generated for {employee.full_name} for {tax_year}",
            new_values={
                "employee_id": employee.id,
                "tax_year": tax_year,
                "total_wages": float(w2.wages_tips_compensation)
            }
        ))

        logger.info(f"Generated W-2 for {employee.full_name} - {tax_year}")
        return w2

    def generate_941(
        self,
        year: int,
        quarter: int,
        employer_info: Dict[str, str],
        quarterly_data: Dict[str, Any]
    ) -> Form941:
        """Generate Form 941 for quarter"""
        form = Form941(
            year=year,
            quarter=quarter,
            employer_ein=employer_info.get("ein", ""),
            employer_name=employer_info.get("name", ""),
            employer_address=employer_info.get("address", ""),

            number_of_employees=quarterly_data.get("employee_count", 0),
            total_wages=quarterly_data.get("total_wages", Decimal("0")),
            federal_tax_withheld=quarterly_data.get("federal_tax", Decimal("0")),
            ss_wages=quarterly_data.get("ss_wages", Decimal("0")),
            ss_tax=quarterly_data.get("ss_tax", Decimal("0")),
            medicare_wages=quarterly_data.get("medicare_wages", Decimal("0")),
            medicare_tax=quarterly_data.get("medicare_tax", Decimal("0")),
        )

        # Calculate total taxes
        form.total_taxes = (
            form.federal_tax_withheld +
            form.ss_tax +
            form.medicare_tax
        )

        # Add to storage
        self.form_941s[form.id] = form

        logger.info(f"Generated Form 941 for Q{quarter} {year}")
        return form

    def get_compliance_summary(self) -> Dict[str, Any]:
        """Get compliance summary"""
        total_violations = len(self.violations)
        critical_violations = len([v for v in self.violations if v.severity == ComplianceStatus.VIOLATION])
        warnings = len([v for v in self.violations if v.severity == ComplianceStatus.WARNING])
        resolved = len([v for v in self.violations if v.resolved_at is not None])

        return {
            "total_violations": total_violations,
            "critical_violations": critical_violations,
            "warnings": warnings,
            "resolved": resolved,
            "unresolved": total_violations - resolved,
            "compliance_rate": f"{((1 - critical_violations / max(1, total_violations)) * 100):.1f}%",
            "active_rules": len([r for r in self.compliance_rules.values() if r.active]),
        }

    def get_audit_trail(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_type: Optional[AuditEventType] = None,
        entity_id: Optional[str] = None
    ) -> List[AuditLogEntry]:
        """Get filtered audit trail"""
        filtered = self.audit_log

        if start_date:
            filtered = [e for e in filtered if e.timestamp >= start_date]

        if end_date:
            filtered = [e for e in filtered if e.timestamp <= end_date]

        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]

        if entity_id:
            filtered = [e for e in filtered if e.entity_id == entity_id]

        return sorted(filtered, key=lambda e: e.timestamp, reverse=True)

    def export_audit_log(self, filepath: str) -> bool:
        """Export audit log to JSON file"""
        try:
            data = []
            for entry in self.audit_log:
                data.append({
                    "timestamp": entry.timestamp.isoformat(),
                    "event_type": entry.event_type.value,
                    "user": entry.user_name,
                    "entity_type": entry.entity_type,
                    "entity_id": entry.entity_id,
                    "action": entry.action,
                    "description": entry.description,
                    "old_values": entry.old_values,
                    "new_values": entry.new_values,
                })

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Audit log exported to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to export audit log: {e}")
            return False


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    engine = ComplianceEngine()

    # Check minimum wage compliance
    compliant, violation = engine.check_minimum_wage_compliance(
        Decimal("15.00"),
        jurisdiction="CA"
    )
    print(f"California minimum wage check: {'✓ Compliant' if compliant else '✗ Violation'}")

    # Check overtime compliance
    compliant, violation = engine.check_overtime_compliance(
        regular_hours=Decimal("40"),
        overtime_hours=Decimal("5"),
        overtime_rate=Decimal("30.00"),
        base_rate=Decimal("20.00"),
        jurisdiction="US"
    )
    print(f"Overtime compliance check: {'✓ Compliant' if compliant else '✗ Violation'}")

    # Get compliance summary
    summary = engine.get_compliance_summary()
    print(f"\nCompliance Summary:")
    print(f"  Total Violations: {summary['total_violations']}")
    print(f"  Critical: {summary['critical_violations']}")
    print(f"  Warnings: {summary['warnings']}")
    print(f"  Active Rules: {summary['active_rules']}")
