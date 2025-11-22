"""
NEXUS Accounting - Financial Reports Module
P&L, balance sheet, cash flow, tax reports.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from decimal import Decimal
from enum import Enum


class ReportType(Enum):
    PROFIT_LOSS = "profit_loss"
    BALANCE_SHEET = "balance_sheet"
    CASH_FLOW = "cash_flow"
    TRIAL_BALANCE = "trial_balance"
    TAX_SUMMARY = "tax_summary"


@dataclass
class FinancialReport:
    """Financial report"""
    id: str
    report_type: ReportType
    title: str

    # Period
    start_date: datetime
    end_date: datetime

    # Data
    data: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    generated_at: datetime = field(default_factory=datetime.now)
    generated_by: str = ""


class FinancialReportManager:
    """Financial reporting"""

    def __init__(self):
        self.reports: Dict[str, FinancialReport] = {}

    def generate_profit_loss(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> FinancialReport:
        """Generate P&L statement"""
        import uuid

        # Mock data - would query actual ledger
        data = {
            "revenue": {
                "sales": Decimal("100000.00"),
                "service_revenue": Decimal("50000.00"),
                "total_revenue": Decimal("150000.00")
            },
            "cost_of_goods_sold": {
                "cogs": Decimal("60000.00")
            },
            "gross_profit": Decimal("90000.00"),
            "operating_expenses": {
                "salaries": Decimal("30000.00"),
                "rent": Decimal("10000.00"),
                "utilities": Decimal("2000.00"),
                "marketing": Decimal("5000.00"),
                "total_expenses": Decimal("47000.00")
            },
            "operating_income": Decimal("43000.00"),
            "other_income": Decimal("1000.00"),
            "other_expenses": Decimal("500.00"),
            "net_income": Decimal("43500.00")
        }

        report = FinancialReport(
            id=str(uuid.uuid4()),
            report_type=ReportType.PROFIT_LOSS,
            title=f"Profit & Loss Statement ({start_date.date()} - {end_date.date()})",
            start_date=start_date,
            end_date=end_date,
            data=data
        )

        self.reports[report.id] = report
        return report

    def generate_balance_sheet(self, as_of_date: datetime) -> FinancialReport:
        """Generate balance sheet"""
        import uuid

        data = {
            "assets": {
                "current_assets": {
                    "cash": Decimal("50000.00"),
                    "accounts_receivable": Decimal("30000.00"),
                    "inventory": Decimal("20000.00"),
                    "total_current": Decimal("100000.00")
                },
                "fixed_assets": {
                    "equipment": Decimal("50000.00"),
                    "accumulated_depreciation": Decimal("-10000.00"),
                    "total_fixed": Decimal("40000.00")
                },
                "total_assets": Decimal("140000.00")
            },
            "liabilities": {
                "current_liabilities": {
                    "accounts_payable": Decimal("20000.00"),
                    "short_term_loans": Decimal("10000.00"),
                    "total_current": Decimal("30000.00")
                },
                "long_term_liabilities": {
                    "long_term_loans": Decimal("30000.00"),
                    "total_long_term": Decimal("30000.00")
                },
                "total_liabilities": Decimal("60000.00")
            },
            "equity": {
                "owners_equity": Decimal("50000.00"),
                "retained_earnings": Decimal("30000.00"),
                "total_equity": Decimal("80000.00")
            },
            "total_liabilities_equity": Decimal("140000.00")
        }

        report = FinancialReport(
            id=str(uuid.uuid4()),
            report_type=ReportType.BALANCE_SHEET,
            title=f"Balance Sheet as of {as_of_date.date()}",
            start_date=as_of_date,
            end_date=as_of_date,
            data=data
        )

        self.reports[report.id] = report
        return report

    def generate_cash_flow(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> FinancialReport:
        """Generate cash flow statement"""
        import uuid

        data = {
            "operating_activities": {
                "net_income": Decimal("43500.00"),
                "depreciation": Decimal("5000.00"),
                "accounts_receivable_change": Decimal("-5000.00"),
                "accounts_payable_change": Decimal("3000.00"),
                "net_cash_operating": Decimal("46500.00")
            },
            "investing_activities": {
                "equipment_purchase": Decimal("-10000.00"),
                "net_cash_investing": Decimal("-10000.00")
            },
            "financing_activities": {
                "loan_proceeds": Decimal("20000.00"),
                "loan_payments": Decimal("-5000.00"),
                "net_cash_financing": Decimal("15000.00")
            },
            "net_change_cash": Decimal("51500.00"),
            "beginning_cash": Decimal("10000.00"),
            "ending_cash": Decimal("61500.00")
        }

        report = FinancialReport(
            id=str(uuid.uuid4()),
            report_type=ReportType.CASH_FLOW,
            title=f"Cash Flow Statement ({start_date.date()} - {end_date.date()})",
            start_date=start_date,
            end_date=end_date,
            data=data
        )

        self.reports[report.id] = report
        return report

    def generate_tax_summary(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> FinancialReport:
        """Generate tax summary report"""
        import uuid

        data = {
            "income": {
                "gross_revenue": Decimal("150000.00"),
                "taxable_income": Decimal("43500.00")
            },
            "deductions": {
                "business_expenses": Decimal("47000.00"),
                "depreciation": Decimal("5000.00"),
                "total_deductions": Decimal("52000.00")
            },
            "sales_tax": {
                "collected": Decimal("12000.00"),
                "paid": Decimal("11500.00"),
                "net_due": Decimal("500.00")
            }
        }

        report = FinancialReport(
            id=str(uuid.uuid4()),
            report_type=ReportType.TAX_SUMMARY,
            title=f"Tax Summary ({start_date.date()} - {end_date.date()})",
            start_date=start_date,
            end_date=end_date,
            data=data
        )

        self.reports[report.id] = report
        return report


if __name__ == "__main__":
    manager = FinancialReportManager()

    from datetime import timedelta

    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    pl = manager.generate_profit_loss(start_date, end_date)
    bs = manager.generate_balance_sheet(end_date)
    cf = manager.generate_cash_flow(start_date, end_date)

    print(f"P&L Net Income: ${pl.data['net_income']}")
    print(f"Total Assets: ${bs.data['assets']['total_assets']}")
    print(f"Cash Flow: ${cf.data['net_change_cash']}")
