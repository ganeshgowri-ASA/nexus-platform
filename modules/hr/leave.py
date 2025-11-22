"""
NEXUS HR - Leave Management Module
PTO, vacation, sick leave, leave requests, and approvals.
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from enum import Enum
from decimal import Decimal


class LeaveType(Enum):
    VACATION = "vacation"
    SICK = "sick"
    PERSONAL = "personal"
    PARENTAL = "parental"
    BEREAVEMENT = "bereavement"
    UNPAID = "unpaid"


class LeaveStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


@dataclass
class LeaveBalance:
    """Employee leave balance"""
    id: str
    employee_id: str
    leave_type: LeaveType
    year: int

    # Balances (in days)
    accrued: Decimal = Decimal("0.0")
    used: Decimal = Decimal("0.0")
    pending: Decimal = Decimal("0.0")
    available: Decimal = field(init=False)

    # Policy
    annual_allowance: Decimal = Decimal("20.0")
    carryover_allowed: bool = True
    max_carryover: Decimal = Decimal("5.0")

    def __post_init__(self):
        self.available = self.accrued - self.used - self.pending


@dataclass
class LeaveRequest:
    """Leave request"""
    id: str
    request_number: str
    employee_id: str
    employee_name: str

    # Leave details
    leave_type: LeaveType
    start_date: date
    end_date: date
    total_days: Decimal = field(init=False)
    half_day: bool = False

    # Request
    reason: str = ""
    notes: str = ""

    # Approval
    status: LeaveStatus = LeaveStatus.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: str = ""

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        days = (self.end_date - self.start_date).days + 1
        self.total_days = Decimal(str(days)) if not self.half_day else Decimal("0.5")


class LeaveManager:
    """Leave management"""

    def __init__(self):
        self.leave_balances: Dict[str, Dict[LeaveType, LeaveBalance]] = {}  # employee_id -> balances
        self.leave_requests: Dict[str, LeaveRequest] = {}
        self.request_counter = 1000

    def create_leave_balance(
        self,
        employee_id: str,
        leave_type: LeaveType,
        year: int,
        **kwargs
    ) -> LeaveBalance:
        """Create leave balance"""
        import uuid
        balance = LeaveBalance(
            id=str(uuid.uuid4()),
            employee_id=employee_id,
            leave_type=leave_type,
            year=year,
            **kwargs
        )

        if employee_id not in self.leave_balances:
            self.leave_balances[employee_id] = {}

        self.leave_balances[employee_id][leave_type] = balance
        return balance

    def accrue_leave(
        self,
        employee_id: str,
        leave_type: LeaveType,
        days: Decimal
    ) -> bool:
        """Accrue leave"""
        if employee_id not in self.leave_balances:
            return False

        balance = self.leave_balances[employee_id].get(leave_type)
        if not balance:
            return False

        balance.accrued += days
        balance.available = balance.accrued - balance.used - balance.pending
        return True

    def create_leave_request(
        self,
        employee_id: str,
        employee_name: str,
        leave_type: LeaveType,
        start_date: date,
        end_date: date,
        **kwargs
    ) -> Optional[LeaveRequest]:
        """Create leave request"""
        # Check balance
        if employee_id not in self.leave_balances:
            return None

        balance = self.leave_balances[employee_id].get(leave_type)
        if not balance:
            return None

        import uuid
        request_number = f"LVE-{self.request_counter}"
        self.request_counter += 1

        request = LeaveRequest(
            id=str(uuid.uuid4()),
            request_number=request_number,
            employee_id=employee_id,
            employee_name=employee_name,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            **kwargs
        )

        # Check if sufficient balance
        if balance.available < request.total_days:
            return None

        # Reserve the days
        balance.pending += request.total_days
        balance.available = balance.accrued - balance.used - balance.pending

        self.leave_requests[request.id] = request
        return request

    def approve_leave(self, request_id: str, approved_by: str) -> bool:
        """Approve leave request"""
        request = self.leave_requests.get(request_id)
        if not request or request.status != LeaveStatus.PENDING:
            return False

        request.status = LeaveStatus.APPROVED
        request.approved_by = approved_by
        request.approved_at = datetime.now()

        # Update balance
        balance = self.leave_balances[request.employee_id][request.leave_type]
        balance.pending -= request.total_days
        balance.used += request.total_days
        balance.available = balance.accrued - balance.used - balance.pending

        return True

    def reject_leave(self, request_id: str, reason: str = "") -> bool:
        """Reject leave request"""
        request = self.leave_requests.get(request_id)
        if not request or request.status != LeaveStatus.PENDING:
            return False

        request.status = LeaveStatus.REJECTED
        request.rejection_reason = reason

        # Release reserved days
        balance = self.leave_balances[request.employee_id][request.leave_type]
        balance.pending -= request.total_days
        balance.available = balance.accrued - balance.used - balance.pending

        return True

    def get_employee_balance(
        self,
        employee_id: str,
        leave_type: LeaveType
    ) -> Optional[LeaveBalance]:
        """Get leave balance"""
        if employee_id not in self.leave_balances:
            return None
        return self.leave_balances[employee_id].get(leave_type)

    def get_pending_requests(self) -> List[LeaveRequest]:
        """Get all pending requests"""
        return [
            req for req in self.leave_requests.values()
            if req.status == LeaveStatus.PENDING
        ]

    def get_employee_requests(
        self,
        employee_id: str,
        year: Optional[int] = None
    ) -> List[LeaveRequest]:
        """Get leave requests for employee"""
        requests = [
            req for req in self.leave_requests.values()
            if req.employee_id == employee_id
        ]

        if year:
            requests = [
                req for req in requests
                if req.start_date.year == year
            ]

        return sorted(requests, key=lambda r: r.start_date, reverse=True)


if __name__ == "__main__":
    manager = LeaveManager()

    # Create balance
    balance = manager.create_leave_balance(
        "employee_001",
        LeaveType.VACATION,
        2024,
        annual_allowance=Decimal("20.0")
    )

    # Accrue leave
    manager.accrue_leave("employee_001", LeaveType.VACATION, Decimal("20.0"))

    # Request leave
    request = manager.create_leave_request(
        "employee_001",
        "John Doe",
        LeaveType.VACATION,
        date(2024, 7, 1),
        date(2024, 7, 5),
        reason="Family vacation"
    )

    # Approve
    if request:
        manager.approve_leave(request.id, "manager_001")

        updated_balance = manager.get_employee_balance("employee_001", LeaveType.VACATION)
        print(f"Leave Request: {request.request_number}")
        print(f"Status: {request.status.value}")
        print(f"Remaining balance: {updated_balance.available} days")
