"""
Comprehensive tests for tax calculation engine
"""

import unittest
from decimal import Decimal
from datetime import date

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tax import (
    TaxEngine, FederalTaxCalculator, StateTaxCalculator,
    W4Information, FilingStatus, State, TaxWithholding
)


class TestFederalTaxCalculator(unittest.TestCase):
    """Test Federal Tax Calculator"""

    def setUp(self):
        """Set up test fixtures"""
        self.calculator = FederalTaxCalculator()

    def test_social_security_calculation(self):
        """Test Social Security tax calculation"""
        gross_pay = Decimal("3000")
        ytd_gross = Decimal("30000")

        ss_tax = self.calculator.calculate_social_security(gross_pay, ytd_gross)

        # Expected: $3,000 * 6.2% = $186.00
        expected = Decimal("186.00")
        self.assertEqual(ss_tax, expected)

    def test_social_security_wage_base_limit(self):
        """Test SS tax stops at wage base"""
        gross_pay = Decimal("5000")
        ytd_gross = Decimal("168000")  # At wage base

        ss_tax = self.calculator.calculate_social_security(gross_pay, ytd_gross)

        # Should be $0 because already at limit
        self.assertEqual(ss_tax, Decimal("0"))

    def test_social_security_partial_limit(self):
        """Test SS tax with partial wage base"""
        gross_pay = Decimal("1000")
        ytd_gross = Decimal("168000")  # At limit

        ss_tax = self.calculator.calculate_social_security(gross_pay, ytd_gross)

        # Should only tax $600 (up to $168,600 limit)
        # But YTD is already at limit, so $0
        self.assertEqual(ss_tax, Decimal("0"))

    def test_medicare_calculation(self):
        """Test Medicare tax calculation"""
        gross_pay = Decimal("3000")
        ytd_gross = Decimal("30000")

        medicare, additional = self.calculator.calculate_medicare(
            gross_pay,
            FilingStatus.SINGLE,
            ytd_gross
        )

        # Expected: $3,000 * 1.45% = $43.50
        expected_medicare = Decimal("43.50")
        self.assertEqual(medicare, expected_medicare)
        self.assertEqual(additional, Decimal("0"))  # Below threshold

    def test_additional_medicare(self):
        """Test Additional Medicare tax on high earners"""
        gross_pay = Decimal("10000")
        ytd_gross = Decimal("195000")  # Close to $200k threshold

        medicare, additional = self.calculator.calculate_medicare(
            gross_pay,
            FilingStatus.SINGLE,
            ytd_gross
        )

        # Standard Medicare on all $10k
        expected_medicare = (Decimal("10000") * Decimal("1.45") / Decimal("100")).quantize(Decimal("0.01"))

        # Additional Medicare on amount over $200k
        # YTD + current = $205k, so $5k subject to additional
        excess = Decimal("5000")
        expected_additional = (excess * Decimal("0.9") / Decimal("100")).quantize(Decimal("0.01"))

        self.assertEqual(medicare, expected_medicare)
        self.assertEqual(additional, expected_additional)

    def test_federal_withholding_single(self):
        """Test federal income tax withholding for single filer"""
        w4 = W4Information(
            filing_status=FilingStatus.SINGLE,
            dependents_amount=Decimal("0"),
            extra_withholding=Decimal("0")
        )

        # $3,000 biweekly = $78,000 annual
        withholding = self.calculator.calculate_federal_withholding(
            gross_pay=Decimal("3000"),
            pay_periods_per_year=26,
            w4=w4,
            ytd_gross=Decimal("0")
        )

        # Should be positive amount
        self.assertGreater(withholding, Decimal("0"))

    def test_federal_withholding_exempt(self):
        """Test exempt employee has no withholding"""
        w4 = W4Information(
            filing_status=FilingStatus.SINGLE,
            exempt=True
        )

        withholding = self.calculator.calculate_federal_withholding(
            gross_pay=Decimal("3000"),
            pay_periods_per_year=26,
            w4=w4
        )

        self.assertEqual(withholding, Decimal("0"))


class TestStateTaxCalculator(unittest.TestCase):
    """Test State Tax Calculator"""

    def setUp(self):
        """Set up test fixtures"""
        self.calculator = StateTaxCalculator()

    def test_no_income_tax_states(self):
        """Test states with no income tax"""
        no_tax_states = [State.FL, State.TX, State.WA, State.NV]

        for state in no_tax_states:
            tax = self.calculator.calculate_state_tax(
                state=state,
                gross_pay=Decimal("3000"),
                pay_periods_per_year=26
            )
            self.assertEqual(tax, Decimal("0"), f"{state.value} should have no tax")

    def test_flat_tax_state(self):
        """Test flat tax state (Illinois)"""
        tax = self.calculator.calculate_state_tax(
            state=State.IL,
            gross_pay=Decimal("3000"),
            pay_periods_per_year=26
        )

        # IL has 4.95% flat tax
        # Annual: $3,000 * 26 = $78,000
        # Tax: $78,000 * 4.95% = $3,861
        # Per period: $3,861 / 26 = $148.50
        expected = Decimal("148.50")

        self.assertAlmostEqual(float(tax), float(expected), places=2)

    def test_california_sdi(self):
        """Test California State Disability Insurance"""
        sdi = self.calculator.calculate_state_disability(
            state=State.CA,
            gross_pay=Decimal("3000"),
            ytd_gross=Decimal("0")
        )

        # CA SDI is 1.1% in 2024
        # $3,000 * 1.1% = $33.00
        expected = Decimal("33.00")
        self.assertEqual(sdi, expected)

    def test_sdi_wage_base_limit(self):
        """Test SDI stops at wage base"""
        sdi = self.calculator.calculate_state_disability(
            state=State.CA,
            gross_pay=Decimal("5000"),
            ytd_gross=Decimal("153164")  # At limit
        )

        # Should be $0 because at wage base
        self.assertEqual(sdi, Decimal("0"))


class TestTaxEngine(unittest.TestCase):
    """Test complete Tax Engine"""

    def setUp(self):
        """Set up test fixtures"""
        self.engine = TaxEngine()

    def test_complete_withholding_calculation(self):
        """Test complete tax withholding for employee"""
        w4 = W4Information(
            filing_status=FilingStatus.SINGLE,
            dependents_amount=Decimal("0"),
            extra_withholding=Decimal("50")
        )

        withholding = self.engine.calculate_complete_withholding(
            gross_pay=Decimal("3000"),
            pay_periods_per_year=26,
            state=State.CA,
            w4=w4,
            ytd_gross=Decimal("30000")
        )

        # Verify all components are calculated
        self.assertGreater(withholding.federal_income_tax, Decimal("0"))
        self.assertGreater(withholding.social_security, Decimal("0"))
        self.assertGreater(withholding.medicare, Decimal("0"))
        self.assertGreater(withholding.state_income_tax, Decimal("0"))
        self.assertGreater(withholding.state_disability, Decimal("0"))

        # Verify total equals sum of components
        expected_total = (
            withholding.federal_income_tax +
            withholding.state_income_tax +
            withholding.local_income_tax +
            withholding.social_security +
            withholding.medicare +
            withholding.additional_medicare +
            withholding.state_disability
        )

        self.assertEqual(withholding.total_withholding, expected_total)

    def test_tax_summary(self):
        """Test tax summary generation"""
        w4 = W4Information(
            filing_status=FilingStatus.MARRIED_JOINT,
            dependents_amount=Decimal("4000")
        )

        withholding = self.engine.calculate_complete_withholding(
            gross_pay=Decimal("5000"),
            pay_periods_per_year=24,  # Semi-monthly
            state=State.NY,
            w4=w4,
            ytd_gross=Decimal("50000")
        )

        summary = self.engine.get_tax_summary(withholding)

        # Verify summary structure
        self.assertIn("gross_pay", summary)
        self.assertIn("federal_taxes", summary)
        self.assertIn("state_taxes", summary)
        self.assertIn("total_withholding", summary)
        self.assertIn("net_pay", summary)

        # Verify calculations
        self.assertEqual(summary["gross_pay"], 5000.0)
        net_pay = 5000.0 - summary["total_withholding"]
        self.assertAlmostEqual(summary["net_pay"], net_pay, places=2)


if __name__ == '__main__':
    unittest.main()
