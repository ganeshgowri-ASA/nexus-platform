"""
Comprehensive tests for payroll processing engine
"""

import unittest
from datetime import date, timedelta
from decimal import Decimal

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from processing import (
    PayrollProcessor, Employee, PayFrequency, EmploymentType,
    Deduction, DeductionType, Bonus, TimeEntry, OvertimeRule,
    Currency, PaymentStatus
)


class TestPayrollProcessor(unittest.TestCase):
    """Test PayrollProcessor class"""

    def setUp(self):
        """Set up test fixtures"""
        self.processor = PayrollProcessor()

    def test_register_employee(self):
        """Test employee registration"""
        employee = Employee(
            first_name="John",
            last_name="Doe",
            email="john.doe@company.com",
            base_salary=Decimal("75000"),
            pay_frequency=PayFrequency.BIWEEKLY,
            is_salaried=True
        )

        self.processor.register_employee(employee)

        self.assertEqual(len(self.processor.employees), 1)
        self.assertIn(employee.id, self.processor.employees)
        self.assertTrue(employee.employee_number.startswith("EMP"))

    def test_calculate_salaried_employee_pay(self):
        """Test salary calculation for salaried employee"""
        employee = Employee(
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@company.com",
            base_salary=Decimal("78000"),  # $78k annual
            pay_frequency=PayFrequency.BIWEEKLY,  # 26 pay periods
            is_salaried=True,
            department="Engineering"
        )

        self.processor.register_employee(employee)

        # Calculate pay for one period
        record = self.processor.calculate_employee_pay(
            employee,
            date(2024, 11, 1),
            date(2024, 11, 14),
        )

        # Expected: $78,000 / 26 = $3,000
        expected_pay = Decimal("3000.00")
        self.assertEqual(record.regular_pay, expected_pay)
        self.assertEqual(record.gross_pay, expected_pay)

    def test_calculate_hourly_employee_pay(self):
        """Test pay calculation for hourly employee"""
        employee = Employee(
            first_name="Bob",
            last_name="Johnson",
            email="bob.johnson@company.com",
            base_salary=Decimal("25"),  # $25/hour
            pay_frequency=PayFrequency.BIWEEKLY,
            is_salaried=False,
            overtime_eligible=True,
            overtime_rule=OvertimeRule()
        )

        self.processor.register_employee(employee)

        # Add time entries
        self.processor.add_time_entry(TimeEntry(
            employee_id=employee.id,
            date=date(2024, 11, 1),
            regular_hours=Decimal("45"),  # 5 hours OT
            approved=True
        ))

        # Calculate pay
        record = self.processor.calculate_employee_pay(
            employee,
            date(2024, 11, 1),
            date(2024, 11, 14),
        )

        # Expected: 40 hours * $25 + 5 hours * $37.50
        expected_regular = Decimal("40") * Decimal("25")
        expected_overtime = Decimal("5") * Decimal("25") * Decimal("1.5")
        expected_total = expected_regular + expected_overtime

        self.assertEqual(record.regular_pay, expected_regular)
        self.assertEqual(record.overtime_pay, expected_overtime)
        self.assertAlmostEqual(float(record.gross_pay), float(expected_total), places=2)

    def test_deductions(self):
        """Test deduction calculations"""
        employee = Employee(
            first_name="Alice",
            last_name="Williams",
            email="alice.williams@company.com",
            base_salary=Decimal("80000"),
            pay_frequency=PayFrequency.BIWEEKLY,
            is_salaried=True,
            deductions=[
                Deduction(
                    name="401(k)",
                    deduction_type=DeductionType.PRE_TAX,
                    percentage=Decimal("6"),  # 6% contribution
                ),
                Deduction(
                    name="Health Insurance",
                    deduction_type=DeductionType.BENEFIT,
                    amount=Decimal("200"),  # $200 per period
                )
            ]
        )

        self.processor.register_employee(employee)

        record = self.processor.calculate_employee_pay(
            employee,
            date(2024, 11, 1),
            date(2024, 11, 14),
        )

        # Gross pay: $80,000 / 26 = $3,076.92
        gross = Decimal("3076.92")

        # Pre-tax: 6% of $3,076.92 = $184.62
        expected_pretax = (gross * Decimal("0.06")).quantize(Decimal("0.01"))

        # Post-tax: $200
        expected_posttax = Decimal("200.00")

        self.assertAlmostEqual(float(record.pre_tax_deductions), float(expected_pretax), places=2)
        self.assertEqual(record.post_tax_deductions, expected_posttax)

    def test_create_payroll_run(self):
        """Test creating a complete payroll run"""
        # Add multiple employees
        employees = [
            Employee(
                first_name="Employee",
                last_name=f"#{i}",
                email=f"emp{i}@company.com",
                base_salary=Decimal("60000"),
                pay_frequency=PayFrequency.BIWEEKLY,
                is_salaried=True
            )
            for i in range(5)
        ]

        for emp in employees:
            self.processor.register_employee(emp)

        # Create payroll run
        run = self.processor.create_payroll_run(
            pay_period_start=date(2024, 11, 1),
            pay_period_end=date(2024, 11, 14),
            pay_date=date(2024, 11, 20),
            created_by="test_user"
        )

        self.assertEqual(run.employee_count, 5)
        self.assertEqual(len(run.payment_records), 5)
        self.assertEqual(run.status, PaymentStatus.PENDING_APPROVAL)

        # Each employee should get $60,000 / 26 = $2,307.69
        expected_per_employee = Decimal("2307.69")
        expected_total = expected_per_employee * 5

        self.assertAlmostEqual(
            float(run.total_gross_pay),
            float(expected_total),
            places=2
        )

    def test_approve_payroll_run(self):
        """Test payroll run approval"""
        employee = Employee(
            first_name="Test",
            last_name="User",
            email="test@company.com",
            base_salary=Decimal("50000"),
            pay_frequency=PayFrequency.BIWEEKLY,
            is_salaried=True
        )

        self.processor.register_employee(employee)

        run = self.processor.create_payroll_run(
            pay_period_start=date(2024, 11, 1),
            pay_period_end=date(2024, 11, 14),
            pay_date=date(2024, 11, 20),
            created_by="admin"
        )

        # Approve run
        success = self.processor.approve_payroll_run(run.id, "manager")

        self.assertTrue(success)
        self.assertEqual(run.status, PaymentStatus.APPROVED)
        self.assertEqual(run.approved_by, "manager")
        self.assertIsNotNone(run.approved_at)


class TestDeduction(unittest.TestCase):
    """Test Deduction class"""

    def test_percentage_deduction(self):
        """Test percentage-based deduction"""
        deduction = Deduction(
            name="401(k)",
            deduction_type=DeductionType.PRE_TAX,
            percentage=Decimal("5")
        )

        gross_pay = Decimal("3000")
        amount = deduction.calculate_amount(gross_pay)

        expected = Decimal("150.00")  # 5% of $3000
        self.assertEqual(amount, expected)

    def test_fixed_amount_deduction(self):
        """Test fixed amount deduction"""
        deduction = Deduction(
            name="Health Insurance",
            deduction_type=DeductionType.BENEFIT,
            amount=Decimal("250")
        )

        gross_pay = Decimal("3000")
        amount = deduction.calculate_amount(gross_pay)

        self.assertEqual(amount, Decimal("250.00"))

    def test_deduction_with_annual_max(self):
        """Test deduction with annual maximum"""
        deduction = Deduction(
            name="401(k)",
            deduction_type=DeductionType.PRE_TAX,
            percentage=Decimal("10"),
            annual_max=Decimal("22500")  # 2024 limit
        )

        gross_pay = Decimal("3000")
        ytd_amount = Decimal("22000")  # Already contributed $22k

        amount = deduction.calculate_amount(gross_pay, ytd_amount)

        # Should only deduct $500 to reach the $22,500 limit
        expected = Decimal("500.00")
        self.assertEqual(amount, expected)


class TestOvertimeCalculation(unittest.TestCase):
    """Test overtime calculations"""

    def test_standard_overtime(self):
        """Test standard 1.5x overtime calculation"""
        processor = PayrollProcessor()

        employee = Employee(
            first_name="Overtime",
            last_name="Worker",
            email="ot@company.com",
            base_salary=Decimal("20"),  # $20/hour
            pay_frequency=PayFrequency.BIWEEKLY,
            is_salaried=False,
            overtime_eligible=True,
            overtime_rule=OvertimeRule(
                threshold_hours=Decimal("40"),
                multiplier=Decimal("1.5")
            )
        )

        regular, overtime, double_time = processor.calculate_overtime(
            employee,
            Decimal("48"),  # 48 total hours
            employee.overtime_rule
        )

        self.assertEqual(regular, Decimal("40"))
        self.assertEqual(overtime, Decimal("8"))
        self.assertEqual(double_time, Decimal("0"))

    def test_double_time(self):
        """Test double-time calculation"""
        processor = PayrollProcessor()

        employee = Employee(
            first_name="Hard",
            last_name="Worker",
            email="hard@company.com",
            base_salary=Decimal("25"),
            pay_frequency=PayFrequency.BIWEEKLY,
            is_salaried=False,
            overtime_eligible=True,
            overtime_rule=OvertimeRule(
                threshold_hours=Decimal("40"),
                multiplier=Decimal("1.5"),
                double_time_threshold=Decimal("12"),
                double_time_multiplier=Decimal("2.0")
            )
        )

        regular, overtime, double_time = processor.calculate_overtime(
            employee,
            Decimal("60"),  # 60 total hours
            employee.overtime_rule
        )

        self.assertEqual(regular, Decimal("40"))
        self.assertEqual(overtime, Decimal("12"))
        self.assertEqual(double_time, Decimal("8"))


if __name__ == '__main__':
    unittest.main()
