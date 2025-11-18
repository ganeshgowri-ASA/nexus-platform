"""
NEXUS Accounting - Expenses Module
Expense tracking, categorization, reimbursements, receipts.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum
from decimal import Decimal


class ExpenseStatus(Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    REIMBURSED = "reimbursed"


class ExpenseCategory(Enum):
    TRAVEL = "travel"
    MEALS = "meals"
    OFFICE = "office_supplies"
    SOFTWARE = "software"
    MARKETING = "marketing"
    UTILITIES = "utilities"
    RENT = "rent"
    INSURANCE = "insurance"
    OTHER = "other"


@dataclass
class Expense:
    """Expense record"""
    id: str
    expense_number: str
    employee_id: str
    employee_name: str

    # Details
    category: ExpenseCategory
    description: str
    amount: Decimal
    currency: str = "USD"

    # Date
    expense_date: datetime = field(default_factory=datetime.now)

    # Reimbursement
    is_reimbursable: bool = True
    reimbursed_amount: Decimal = Decimal("0.00")

    # Attachments
    receipt_urls: List[str] = field(default_factory=list)

    # Approval
    status: ExpenseStatus = ExpenseStatus.DRAFT
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    # GL account
    account_id: Optional[str] = None

    # Metadata
    notes: str = ""
    project_id: Optional[str] = None
    vendor: str = ""

    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ExpenseReport:
    """Expense report (group of expenses)"""
    id: str
    report_number: str
    employee_id: str
    employee_name: str

    # Expenses
    expense_ids: List[str] = field(default_factory=list)

    # Totals
    total_amount: Decimal = Decimal("0.00")
    reimbursable_amount: Decimal = Decimal("0.00")

    # Status
    status: ExpenseStatus = ExpenseStatus.DRAFT

    # Approval
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None

    created_at: datetime = field(default_factory=datetime.now)


class ExpenseManager:
    """Expense management"""

    def __init__(self):
        self.expenses: Dict[str, Expense] = {}
        self.reports: Dict[str, ExpenseReport] = {}
        self.expense_counter = 1000
        self.report_counter = 1000

    def create_expense(
        self,
        employee_id: str,
        employee_name: str,
        category: ExpenseCategory,
        description: str,
        amount: Decimal,
        **kwargs
    ) -> Expense:
        """Create expense"""
        import uuid
        expense_number = f"EXP-{self.expense_counter}"
        self.expense_counter += 1

        expense = Expense(
            id=str(uuid.uuid4()),
            expense_number=expense_number,
            employee_id=employee_id,
            employee_name=employee_name,
            category=category,
            description=description,
            amount=amount,
            **kwargs
        )

        self.expenses[expense.id] = expense
        return expense

    def create_expense_report(
        self,
        employee_id: str,
        employee_name: str,
        expense_ids: List[str]
    ) -> ExpenseReport:
        """Create expense report"""
        import uuid
        report_number = f"ER-{self.report_counter}"
        self.report_counter += 1

        # Calculate totals
        total = Decimal("0.00")
        reimbursable = Decimal("0.00")

        for exp_id in expense_ids:
            expense = self.expenses.get(exp_id)
            if expense:
                total += expense.amount
                if expense.is_reimbursable:
                    reimbursable += expense.amount

        report = ExpenseReport(
            id=str(uuid.uuid4()),
            report_number=report_number,
            employee_id=employee_id,
            employee_name=employee_name,
            expense_ids=expense_ids,
            total_amount=total,
            reimbursable_amount=reimbursable
        )

        self.reports[report.id] = report
        return report

    def approve_expense(self, expense_id: str, approved_by: str) -> bool:
        """Approve expense"""
        expense = self.expenses.get(expense_id)
        if not expense or expense.status != ExpenseStatus.SUBMITTED:
            return False

        expense.status = ExpenseStatus.APPROVED
        expense.approved_by = approved_by
        expense.approved_at = datetime.now()
        return True

    def reimburse_expense(self, expense_id: str, amount: Decimal) -> bool:
        """Reimburse expense"""
        expense = self.expenses.get(expense_id)
        if not expense or expense.status != ExpenseStatus.APPROVED:
            return False

        expense.reimbursed_amount = amount
        expense.status = ExpenseStatus.REIMBURSED
        return True

    def get_employee_expenses(
        self,
        employee_id: str,
        status: Optional[ExpenseStatus] = None
    ) -> List[Expense]:
        """Get expenses for employee"""
        expenses = [e for e in self.expenses.values() if e.employee_id == employee_id]

        if status:
            expenses = [e for e in expenses if e.status == status]

        return expenses

    def get_expenses_by_category(self, category: ExpenseCategory) -> List[Expense]:
        """Get expenses by category"""
        return [e for e in self.expenses.values() if e.category == category]


if __name__ == "__main__":
    manager = ExpenseManager()

    expense = manager.create_expense(
        "emp_001",
        "John Doe",
        ExpenseCategory.TRAVEL,
        "Flight to NYC",
        Decimal("450.00"),
        vendor="Delta Airlines"
    )

    expense.status = ExpenseStatus.SUBMITTED
    manager.approve_expense(expense.id, "manager_001")
    manager.reimburse_expense(expense.id, Decimal("450.00"))

    print(f"Expense: {expense.expense_number}")
    print(f"Status: {expense.status.value}")
