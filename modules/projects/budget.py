"""
NEXUS Budget Management Module
Budget tracking, expense management, and cost reporting.
"""

from typing import Dict, List, Optional, Any
from datetime import date, datetime
from enum import Enum
import uuid


class ExpenseCategory(Enum):
    """Expense categories."""
    LABOR = "labor"
    MATERIALS = "materials"
    SOFTWARE = "software"
    HARDWARE = "hardware"
    TRAVEL = "travel"
    CONSULTING = "consulting"
    OTHER = "other"


class ExpenseStatus(Enum):
    """Expense status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class Expense:
    """
    Represents a project expense.

    Attributes:
        id: Unique expense identifier
        project_id: Associated project ID
        category: Expense category
        amount: Expense amount
        currency: Currency code
        description: Expense description
        date: Expense date
        vendor: Vendor/supplier name
        status: Expense status
        approved_by: User who approved expense
        receipt_url: URL to receipt/invoice
        metadata: Additional metadata
        created_at: Creation timestamp
    """

    def __init__(
        self,
        project_id: str,
        category: ExpenseCategory,
        amount: float,
        description: str = "",
        currency: str = "USD",
        date: Optional[date] = None,
        vendor: str = "",
        status: ExpenseStatus = ExpenseStatus.PENDING,
        receipt_url: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        expense_id: Optional[str] = None
    ):
        """Initialize an expense."""
        self.id: str = expense_id or str(uuid.uuid4())
        self.project_id: str = project_id
        self.category: ExpenseCategory = category
        self.amount: float = amount
        self.currency: str = currency
        self.description: str = description
        self.date: date = date or date.today()
        self.vendor: str = vendor
        self.status: ExpenseStatus = status
        self.approved_by: Optional[str] = None
        self.receipt_url: str = receipt_url
        self.metadata: Dict[str, Any] = metadata or {}
        self.created_at: datetime = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert expense to dictionary."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "category": self.category.value,
            "amount": self.amount,
            "currency": self.currency,
            "description": self.description,
            "date": self.date.isoformat(),
            "vendor": self.vendor,
            "status": self.status.value,
            "approved_by": self.approved_by,
            "receipt_url": self.receipt_url,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


class Budget:
    """
    Represents a project budget.

    Attributes:
        id: Budget identifier
        project_id: Associated project ID
        total_budget: Total budget amount
        currency: Currency code
        labor_budget: Labor cost budget
        materials_budget: Materials cost budget
        other_budget: Other costs budget
        contingency_percentage: Contingency reserve (%)
        start_date: Budget period start
        end_date: Budget period end
        metadata: Additional metadata
    """

    def __init__(
        self,
        project_id: str,
        total_budget: float,
        currency: str = "USD",
        labor_budget: float = 0.0,
        materials_budget: float = 0.0,
        other_budget: float = 0.0,
        contingency_percentage: float = 10.0,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        metadata: Optional[Dict[str, Any]] = None,
        budget_id: Optional[str] = None
    ):
        """Initialize a budget."""
        self.id: str = budget_id or str(uuid.uuid4())
        self.project_id: str = project_id
        self.total_budget: float = total_budget
        self.currency: str = currency
        self.labor_budget: float = labor_budget
        self.materials_budget: float = materials_budget
        self.other_budget: float = other_budget
        self.contingency_percentage: float = contingency_percentage
        self.start_date: Optional[date] = start_date
        self.end_date: Optional[date] = end_date
        self.metadata: Dict[str, Any] = metadata or {}
        self.created_at: datetime = datetime.now()

    @property
    def contingency_amount(self) -> float:
        """Calculate contingency reserve amount."""
        return self.total_budget * (self.contingency_percentage / 100)

    def to_dict(self) -> Dict[str, Any]:
        """Convert budget to dictionary."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "total_budget": self.total_budget,
            "currency": self.currency,
            "labor_budget": self.labor_budget,
            "materials_budget": self.materials_budget,
            "other_budget": self.other_budget,
            "contingency_percentage": self.contingency_percentage,
            "contingency_amount": self.contingency_amount,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


class BudgetManager:
    """
    Budget and expense management engine.
    Handles budget creation, expense tracking, and cost reporting.
    """

    def __init__(self, resource_manager=None):
        """
        Initialize the budget manager.

        Args:
            resource_manager: Resource manager instance (optional)
        """
        self.resource_manager = resource_manager
        self.budgets: Dict[str, Budget] = {}
        self.expenses: Dict[str, Expense] = {}

    def create_budget(
        self,
        project_id: str,
        total_budget: float,
        **kwargs
    ) -> Budget:
        """
        Create a budget for a project.

        Args:
            project_id: Project identifier
            total_budget: Total budget amount
            **kwargs: Additional budget attributes

        Returns:
            Created budget
        """
        budget = Budget(project_id=project_id, total_budget=total_budget, **kwargs)
        self.budgets[budget.id] = budget
        return budget

    def get_budget(self, budget_id: str) -> Optional[Budget]:
        """Get a budget by ID."""
        return self.budgets.get(budget_id)

    def get_project_budget(self, project_id: str) -> Optional[Budget]:
        """Get the budget for a project."""
        for budget in self.budgets.values():
            if budget.project_id == project_id:
                return budget
        return None

    def update_budget(self, budget_id: str, **kwargs) -> Optional[Budget]:
        """Update a budget."""
        budget = self.get_budget(budget_id)
        if not budget:
            return None

        for key, value in kwargs.items():
            if hasattr(budget, key):
                setattr(budget, key, value)

        return budget

    def add_expense(
        self,
        project_id: str,
        category: ExpenseCategory,
        amount: float,
        description: str = "",
        **kwargs
    ) -> Expense:
        """
        Add an expense to a project.

        Args:
            project_id: Project identifier
            category: Expense category
            amount: Expense amount
            description: Expense description
            **kwargs: Additional expense attributes

        Returns:
            Created expense
        """
        expense = Expense(
            project_id=project_id,
            category=category,
            amount=amount,
            description=description,
            **kwargs
        )

        self.expenses[expense.id] = expense
        return expense

    def get_expense(self, expense_id: str) -> Optional[Expense]:
        """Get an expense by ID."""
        return self.expenses.get(expense_id)

    def update_expense(self, expense_id: str, **kwargs) -> Optional[Expense]:
        """Update an expense."""
        expense = self.get_expense(expense_id)
        if not expense:
            return None

        for key, value in kwargs.items():
            if hasattr(expense, key):
                setattr(expense, key, value)

        return expense

    def delete_expense(self, expense_id: str) -> bool:
        """Delete an expense."""
        if expense_id in self.expenses:
            del self.expenses[expense_id]
            return True
        return False

    def get_project_expenses(
        self,
        project_id: str,
        status: Optional[ExpenseStatus] = None,
        category: Optional[ExpenseCategory] = None
    ) -> List[Expense]:
        """
        Get expenses for a project.

        Args:
            project_id: Project identifier
            status: Filter by status
            category: Filter by category

        Returns:
            List of expenses
        """
        expenses = [e for e in self.expenses.values() if e.project_id == project_id]

        if status:
            expenses = [e for e in expenses if e.status == status]

        if category:
            expenses = [e for e in expenses if e.category == category]

        return expenses

    def approve_expense(self, expense_id: str, approver_id: str) -> bool:
        """Approve an expense."""
        expense = self.get_expense(expense_id)
        if not expense:
            return False

        expense.status = ExpenseStatus.APPROVED
        expense.approved_by = approver_id
        return True

    def reject_expense(self, expense_id: str) -> bool:
        """Reject an expense."""
        expense = self.get_expense(expense_id)
        if not expense:
            return False

        expense.status = ExpenseStatus.REJECTED
        return True

    def calculate_total_expenses(
        self,
        project_id: str,
        include_pending: bool = False
    ) -> float:
        """
        Calculate total expenses for a project.

        Args:
            project_id: Project identifier
            include_pending: Include pending expenses

        Returns:
            Total expense amount
        """
        expenses = self.get_project_expenses(project_id)

        if not include_pending:
            expenses = [e for e in expenses if e.status != ExpenseStatus.PENDING]

        return sum(e.amount for e in expenses)

    def get_budget_utilization(self, project_id: str) -> Dict[str, Any]:
        """
        Calculate budget utilization for a project.

        Args:
            project_id: Project identifier

        Returns:
            Budget utilization dictionary
        """
        budget = self.get_project_budget(project_id)
        if not budget:
            return {
                "error": "No budget found for project"
            }

        # Calculate actual expenses
        total_expenses = self.calculate_total_expenses(project_id)
        pending_expenses = self.calculate_total_expenses(project_id, include_pending=True) - total_expenses

        # Calculate labor costs from resource manager
        labor_costs = 0.0
        if self.resource_manager:
            cost_data = self.resource_manager.calculate_project_cost(project_id)
            labor_costs = cost_data.get("total_cost", 0.0)

        # Calculate totals
        total_actual = total_expenses + labor_costs
        total_committed = total_actual + pending_expenses

        # Calculate by category
        expenses_by_category = {}
        for expense in self.get_project_expenses(project_id):
            category = expense.category.value
            if category not in expenses_by_category:
                expenses_by_category[category] = 0.0
            if expense.status != ExpenseStatus.PENDING:
                expenses_by_category[category] += expense.amount

        expenses_by_category["labor"] = labor_costs

        return {
            "budget": {
                "total": budget.total_budget,
                "labor": budget.labor_budget,
                "materials": budget.materials_budget,
                "other": budget.other_budget,
                "contingency": budget.contingency_amount
            },
            "actual": {
                "total": total_actual,
                "by_category": expenses_by_category
            },
            "committed": {
                "total": total_committed,
                "pending": pending_expenses
            },
            "remaining": budget.total_budget - total_committed,
            "utilization_percentage": (total_committed / budget.total_budget * 100) if budget.total_budget > 0 else 0,
            "is_over_budget": total_committed > budget.total_budget,
            "variance": budget.total_budget - total_actual,
            "currency": budget.currency
        }

    def forecast_final_cost(
        self,
        project_id: str,
        completion_percentage: float
    ) -> Dict[str, Any]:
        """
        Forecast final project cost based on current progress.

        Args:
            project_id: Project identifier
            completion_percentage: Project completion percentage (0-100)

        Returns:
            Cost forecast dictionary
        """
        if completion_percentage <= 0:
            return {"error": "Invalid completion percentage"}

        budget = self.get_project_budget(project_id)
        utilization = self.get_budget_utilization(project_id)

        if not budget or "error" in utilization:
            return {"error": "Cannot calculate forecast"}

        actual_cost = utilization["actual"]["total"]

        # Calculate Estimate at Completion (EAC)
        # Using the formula: EAC = Actual Cost / (Completion % / 100)
        if completion_percentage > 0:
            eac = actual_cost / (completion_percentage / 100)
        else:
            eac = budget.total_budget

        # Calculate Variance at Completion (VAC)
        vac = budget.total_budget - eac

        # Calculate To-Complete Performance Index (TCPI)
        remaining_work = 100 - completion_percentage
        remaining_budget = budget.total_budget - actual_cost

        if remaining_work > 0 and remaining_budget > 0:
            tcpi = (budget.total_budget - actual_cost) / (budget.total_budget * (remaining_work / 100))
        else:
            tcpi = 0.0

        return {
            "project_id": project_id,
            "completion_percentage": completion_percentage,
            "budget": budget.total_budget,
            "actual_cost": actual_cost,
            "estimate_at_completion": eac,
            "variance_at_completion": vac,
            "cost_performance_index": (budget.total_budget * (completion_percentage / 100)) / actual_cost if actual_cost > 0 else 0,
            "to_complete_performance_index": tcpi,
            "forecast_overrun": max(0, eac - budget.total_budget),
            "currency": budget.currency
        }

    def generate_cost_report(
        self,
        project_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive cost report.

        Args:
            project_id: Project identifier
            start_date: Report start date
            end_date: Report end date

        Returns:
            Cost report dictionary
        """
        budget = self.get_project_budget(project_id)
        expenses = self.get_project_expenses(project_id)

        # Filter by date
        if start_date or end_date:
            filtered = []
            for expense in expenses:
                if start_date and expense.date < start_date:
                    continue
                if end_date and expense.date > end_date:
                    continue
                filtered.append(expense)
            expenses = filtered

        # Group by category
        by_category: Dict[str, float] = {}
        for expense in expenses:
            if expense.status != ExpenseStatus.REJECTED:
                category = expense.category.value
                if category not in by_category:
                    by_category[category] = 0.0
                by_category[category] += expense.amount

        # Group by status
        by_status: Dict[str, float] = {}
        for expense in expenses:
            status = expense.status.value
            if status not in by_status:
                by_status[status] = 0.0
            by_status[status] += expense.amount

        return {
            "project_id": project_id,
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            },
            "budget": budget.to_dict() if budget else None,
            "expenses": {
                "total": sum(by_category.values()),
                "by_category": by_category,
                "by_status": by_status,
                "count": len(expenses)
            },
            "utilization": self.get_budget_utilization(project_id) if budget else None
        }
