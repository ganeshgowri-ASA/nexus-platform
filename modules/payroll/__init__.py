"""
Enterprise Payroll System
Production-ready payroll processing rivaling ADP and Gusto

Features:
- Comprehensive salary processing
- Federal, state, and local tax calculations
- Direct deposit and ACH processing
- Pay slip generation
- Compliance monitoring and audit trails
- Advanced reporting and analytics
- Interactive Streamlit dashboard
"""

__version__ = "1.0.0"
__author__ = "Nexus Platform"

# Core processing
from .processing import (
    PayrollProcessor,
    Employee,
    PayFrequency,
    EmploymentType,
    Deduction,
    DeductionType,
    Bonus,
    TimeEntry,
    OvertimeRule,
    Currency,
    PaymentRecord,
    PayrollRun,
    PaymentStatus,
)

# Tax calculations
from .tax import (
    TaxEngine,
    FederalTaxCalculator,
    StateTaxCalculator,
    W4Information,
    FilingStatus,
    State,
    TaxWithholding,
)

# Pay slips
from .payslips import (
    PayslipGenerator,
    CompanyInfo,
    Payslip,
    PayslipFormat,
    DeliveryMethod,
    PayslipDeliveryService,
)

# Direct deposit
from .deposit import (
    DirectDepositProcessor,
    BankAccount,
    AccountType,
    DepositAllocation,
    DepositType,
    ACHTransaction,
    ACHBatch,
    TransactionStatus,
)

# Compliance
from .compliance import (
    ComplianceEngine,
    ComplianceRule,
    ComplianceViolation,
    ComplianceStatus,
    LaborLawType,
    AuditLogEntry,
    AuditEventType,
    W2Form,
    Form941,
)

# Reporting
from .reports import (
    ReportGenerator,
    ReportType,
    ReportFormat,
    PayrollSummaryReport,
    EmployeeEarningsReport,
    TaxLiabilityReport,
    DepartmentCostReport,
)

__all__ = [
    # Processing
    "PayrollProcessor",
    "Employee",
    "PayFrequency",
    "EmploymentType",
    "Deduction",
    "DeductionType",
    "Bonus",
    "TimeEntry",
    "OvertimeRule",
    "Currency",
    "PaymentRecord",
    "PayrollRun",
    "PaymentStatus",

    # Tax
    "TaxEngine",
    "FederalTaxCalculator",
    "StateTaxCalculator",
    "W4Information",
    "FilingStatus",
    "State",
    "TaxWithholding",

    # Payslips
    "PayslipGenerator",
    "CompanyInfo",
    "Payslip",
    "PayslipFormat",
    "DeliveryMethod",
    "PayslipDeliveryService",

    # Deposit
    "DirectDepositProcessor",
    "BankAccount",
    "AccountType",
    "DepositAllocation",
    "DepositType",
    "ACHTransaction",
    "ACHBatch",
    "TransactionStatus",

    # Compliance
    "ComplianceEngine",
    "ComplianceRule",
    "ComplianceViolation",
    "ComplianceStatus",
    "LaborLawType",
    "AuditLogEntry",
    "AuditEventType",
    "W2Form",
    "Form941",

    # Reporting
    "ReportGenerator",
    "ReportType",
    "ReportFormat",
    "PayrollSummaryReport",
    "EmployeeEarningsReport",
    "TaxLiabilityReport",
    "DepartmentCostReport",
]
