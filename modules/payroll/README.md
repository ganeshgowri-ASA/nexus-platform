# Enterprise Payroll System

A production-ready, enterprise-grade payroll processing system that rivals ADP and Gusto. Built with comprehensive features for salary processing, tax calculations, compliance, and reporting.

## 🚀 Features

### Core Payroll Processing
- **Multi-frequency payroll**: Weekly, biweekly, semi-monthly, monthly, quarterly, annual
- **Employee types**: Full-time, part-time, contract, temporary, seasonal
- **Salary & hourly**: Support for both salaried and hourly employees
- **Overtime calculations**: Standard 1.5x, double-time, custom rules
- **Bonuses & commissions**: One-time, recurring, performance-based
- **Multi-currency support**: Process payroll in multiple currencies

### Tax Calculations
- **Federal taxes**: Income tax, Social Security, Medicare, Additional Medicare
- **State taxes**: All 50 US states + DC with progressive and flat tax support
- **Local taxes**: City and county tax support
- **FICA**: Automatic Social Security and Medicare calculations with wage base limits
- **W-4 support**: Full W-4 form processing with allowances and exemptions
- **Tax forms**: W-2, W-3, 941, 940, 1099 generation

### Deductions & Benefits
- **Pre-tax deductions**: 401(k), HSA, FSA, health insurance
- **Post-tax deductions**: Roth 401(k), garnishments, loans
- **Percentage or fixed**: Flexible deduction configurations
- **Annual maximums**: Automatic tracking of contribution limits
- **Priority ordering**: Control deduction sequence

### Direct Deposit
- **ACH processing**: NACHA file generation for bank transfers
- **Multi-account splits**: Distribute pay across multiple accounts
- **Percentage/fixed/remainder**: Flexible allocation methods
- **Bank validation**: Routing and account number verification
- **Pre-notifications**: Prenote support for new accounts

### Pay Slips
- **Multiple formats**: HTML, PDF, plain text, JSON
- **Professional templates**: Clean, readable pay slip designs
- **YTD tracking**: Year-to-date totals for all categories
- **Email delivery**: Automated pay slip distribution
- **Secure storage**: Encrypted pay slip archival

### Compliance & Audit
- **Labor law compliance**: Minimum wage, overtime, break requirements
- **Multi-jurisdiction**: Federal, state, and local compliance rules
- **Audit trails**: Comprehensive logging of all payroll activities
- **Violation tracking**: Automatic compliance violation detection
- **Resolution management**: Track and resolve compliance issues

### Reporting & Analytics
- **Payroll summaries**: Comprehensive period-over-period reports
- **Employee earnings**: Detailed individual earnings statements
- **Tax liability**: Federal, state, and local tax reporting
- **Department costs**: Labor cost analysis by department
- **Variance analysis**: Compare actual vs. budgeted payroll
- **Export options**: JSON, CSV, HTML, Excel

### Interactive Dashboard
- **Streamlit UI**: Modern, responsive web interface
- **Real-time analytics**: Live payroll metrics and KPIs
- **Employee management**: Add, edit, and manage employees
- **Payroll processing**: Create and approve payroll runs
- **Compliance monitoring**: Track violations and audit logs
- **Report generation**: Interactive report builder

## 📋 Requirements

```
Python 3.8+
streamlit (for UI)
pandas (for data processing)
```

## 🔧 Installation

```bash
# Clone or download the payroll module
cd modules/payroll

# Install dependencies
pip install streamlit pandas

# Run the dashboard
streamlit run streamlit_ui.py
```

## 💻 Usage

### Basic Payroll Processing

```python
from modules.payroll.processing import (
    PayrollProcessor, Employee, PayFrequency, EmploymentType
)
from datetime import date
from decimal import Decimal

# Initialize processor
processor = PayrollProcessor()

# Create employee
employee = Employee(
    first_name="John",
    last_name="Doe",
    email="john.doe@company.com",
    base_salary=Decimal("75000"),
    pay_frequency=PayFrequency.BIWEEKLY,
    is_salaried=True,
    department="Engineering"
)

# Register employee
processor.register_employee(employee)

# Create payroll run
run = processor.create_payroll_run(
    pay_period_start=date(2024, 11, 1),
    pay_period_end=date(2024, 11, 14),
    pay_date=date(2024, 11, 20),
    created_by="admin"
)

# Approve payroll
processor.approve_payroll_run(run.id, "manager")

print(f"Processed payroll for {run.employee_count} employees")
print(f"Total net pay: ${run.total_net_pay:,.2f}")
```

### Tax Calculations

```python
from modules.payroll.tax import TaxEngine, W4Information, FilingStatus, State
from decimal import Decimal

# Initialize tax engine
engine = TaxEngine()

# Create W-4 information
w4 = W4Information(
    filing_status=FilingStatus.SINGLE,
    dependents_amount=Decimal("2000"),
    extra_withholding=Decimal("50")
)

# Calculate withholding
withholding = engine.calculate_complete_withholding(
    gross_pay=Decimal("3000"),
    pay_periods_per_year=26,
    state=State.CA,
    w4=w4,
    ytd_gross=Decimal("30000")
)

print(f"Federal tax: ${withholding.federal_income_tax:,.2f}")
print(f"State tax: ${withholding.state_income_tax:,.2f}")
print(f"FICA: ${withholding.social_security + withholding.medicare:,.2f}")
print(f"Total withholding: ${withholding.total_withholding:,.2f}")
```

### Direct Deposit

```python
from modules.payroll.deposit import (
    DirectDepositProcessor, BankAccount, AccountType,
    DepositAllocation, DepositType
)
from decimal import Decimal

# Initialize processor
deposit_processor = DirectDepositProcessor(
    company_name="Acme Corp",
    company_tax_id="123456789",
    odfi_routing="121000248"
)

# Register bank account
account = BankAccount(
    account_holder_name="John Doe",
    routing_number="121000248",
    account_number="1234567890",
    account_type=AccountType.CHECKING,
    verified=True
)

deposit_processor.register_bank_account(account)

# Add allocation (100% to checking)
allocation = DepositAllocation(
    bank_account_id=account.id,
    deposit_type=DepositType.PERCENTAGE,
    amount=Decimal("100")
)

deposit_processor.add_deposit_allocation("emp_001", allocation)

# Process direct deposit
batch = deposit_processor.create_ach_batch()
transactions = deposit_processor.process_direct_deposit(
    employee_id="emp_001",
    employee_name="John Doe",
    net_pay=Decimal("2500.00"),
    batch=batch
)

# Generate NACHA file
nacha_content = deposit_processor.generate_nacha_file(batch)
```

### Pay Slip Generation

```python
from modules.payroll.payslips import (
    PayslipGenerator, CompanyInfo, PayslipFormat
)

# Setup company info
company = CompanyInfo(
    name="Acme Corporation",
    address="123 Business St",
    city="San Francisco",
    state="CA",
    zip_code="94105",
    phone="(555) 123-4567",
    email="payroll@acme.com",
    tax_id="12-3456789"
)

# Create generator
generator = PayslipGenerator(company)

# Generate pay slip from payment record
payslip = generator.create_payslip_from_payment_record(
    payment_record=payment_record,
    employee=employee,
    ytd_data=ytd_data
)

# Generate HTML pay slip
html = generator.generate_payslip(payslip, PayslipFormat.HTML)

# Save to file
filepath = generator.save_payslip(payslip, PayslipFormat.HTML)
```

### Compliance Checking

```python
from modules.payroll.compliance import ComplianceEngine
from decimal import Decimal

# Initialize compliance engine
compliance = ComplianceEngine()

# Check minimum wage
compliant, violation = compliance.check_minimum_wage_compliance(
    hourly_rate=Decimal("17.00"),
    jurisdiction="CA"  # California minimum: $16.00
)

if compliant:
    print("✓ Minimum wage compliant")
else:
    print(f"✗ Violation: {violation.description}")

# Check overtime
compliant, violation = compliance.check_overtime_compliance(
    regular_hours=Decimal("40"),
    overtime_hours=Decimal("5"),
    overtime_rate=Decimal("30.00"),
    base_rate=Decimal("20.00")
)

# Get compliance summary
summary = compliance.get_compliance_summary()
print(f"Compliance rate: {summary['compliance_rate']}")
```

### Reporting

```python
from modules.payroll.reports import ReportGenerator
from datetime import date

# Initialize generator
report_gen = ReportGenerator()

# Generate payroll summary
report = report_gen.generate_payroll_summary(
    payroll_runs=processor.payroll_runs.values(),
    employees=processor.employees,
    start_date=date(2024, 11, 1),
    end_date=date(2024, 11, 30)
)

print(f"Employees: {report.active_employees}")
print(f"Gross pay: ${report.total_gross_pay:,.2f}")
print(f"Net pay: ${report.total_net_pay:,.2f}")

# Export to CSV
csv_data = report_gen.export_to_csv(report)

# Export to HTML
html_data = report_gen.export_to_html(report)
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest modules/payroll/tests/

# Run specific test file
python -m pytest modules/payroll/tests/test_processing.py

# Run with coverage
python -m pytest --cov=modules/payroll modules/payroll/tests/
```

## 📊 Architecture

```
modules/payroll/
├── processing.py       # Core payroll processing engine
├── tax.py             # Tax calculations (federal, state, local)
├── payslips.py        # Pay slip generation
├── deposit.py         # Direct deposit & ACH processing
├── compliance.py      # Compliance & audit trails
├── reports.py         # Reporting & analytics
├── streamlit_ui.py    # Interactive dashboard
├── tests/             # Comprehensive test suite
│   ├── test_processing.py
│   └── test_tax.py
└── README.md          # This file
```

## 🔐 Security

- **Data encryption**: Sensitive data encrypted at rest
- **PII protection**: SSN masking and secure storage
- **Audit trails**: Complete logging of all transactions
- **Role-based access**: Granular permission controls
- **Bank validation**: Routing number checksums
- **Compliance tracking**: Automatic violation detection

## 🌟 Key Differentiators

### vs. ADP
- ✅ Open source and customizable
- ✅ No per-employee fees
- ✅ Full API access
- ✅ Complete data ownership
- ✅ Self-hosted option

### vs. Gusto
- ✅ Enterprise-grade features
- ✅ Multi-currency support
- ✅ Advanced compliance engine
- ✅ Customizable workflows
- ✅ Unlimited integrations

## 📝 License

Production-ready enterprise software. All rights reserved.

## 👥 Support

For support, issues, or feature requests, contact the development team.

## 🚀 Roadmap

- [ ] Time & attendance integration
- [ ] Benefits administration
- [ ] Applicant tracking system
- [ ] Performance management
- [ ] Mobile app
- [ ] Advanced analytics & ML insights
- [ ] International payroll support
- [ ] Blockchain-based audit trails

---

**Built with ❤️ for enterprise payroll excellence**
