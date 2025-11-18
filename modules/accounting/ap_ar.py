"""
NEXUS Accounting - Accounts Payable/Receivable Module
AP/AR management, aging reports, payment tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum
from decimal import Decimal


class PaymentStatus(Enum):
    OPEN = "open"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    WRITTEN_OFF = "written_off"


@dataclass
class AccountsReceivable:
    """AR record"""
    id: str
    invoice_id: str
    customer_id: str
    customer_name: str

    # Amounts
    amount: Decimal
    amount_paid: Decimal = Decimal("0.00")
    amount_due: Decimal = field(init=False)

    # Dates
    invoice_date: datetime = field(default_factory=datetime.now)
    due_date: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=30))

    # Status
    status: PaymentStatus = PaymentStatus.OPEN

    # Payments
    payments: List[Dict] = field(default_factory=list)

    def __post_init__(self):
        self.amount_due = self.amount - self.amount_paid


@dataclass
class AccountsPayable:
    """AP record"""
    id: str
    bill_id: str
    vendor_id: str
    vendor_name: str

    # Amounts
    amount: Decimal
    amount_paid: Decimal = Decimal("0.00")
    amount_due: Decimal = field(init=False)

    # Dates
    bill_date: datetime = field(default_factory=datetime.now)
    due_date: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=30))

    # Status
    status: PaymentStatus = PaymentStatus.OPEN

    # Payments
    payments: List[Dict] = field(default_factory=list)

    def __post_init__(self):
        self.amount_due = self.amount - self.amount_paid


class APARManager:
    """AP/AR management"""

    def __init__(self):
        self.receivables: Dict[str, AccountsReceivable] = {}
        self.payables: Dict[str, AccountsPayable] = {}

    def create_receivable(
        self,
        invoice_id: str,
        customer_id: str,
        customer_name: str,
        amount: Decimal,
        **kwargs
    ) -> AccountsReceivable:
        """Create AR entry"""
        import uuid
        ar = AccountsReceivable(
            id=str(uuid.uuid4()),
            invoice_id=invoice_id,
            customer_id=customer_id,
            customer_name=customer_name,
            amount=amount,
            **kwargs
        )
        self.receivables[ar.id] = ar
        return ar

    def record_ar_payment(
        self,
        ar_id: str,
        amount: Decimal,
        payment_date: datetime,
        payment_method: str = "check"
    ) -> bool:
        """Record payment on AR"""
        ar = self.receivables.get(ar_id)
        if not ar:
            return False

        ar.amount_paid += amount
        ar.amount_due = ar.amount - ar.amount_paid

        ar.payments.append({
            "amount": float(amount),
            "date": payment_date,
            "method": payment_method
        })

        if ar.amount_due <= 0:
            ar.status = PaymentStatus.PAID
        elif ar.amount_paid > 0:
            ar.status = PaymentStatus.PARTIAL

        return True

    def create_payable(
        self,
        bill_id: str,
        vendor_id: str,
        vendor_name: str,
        amount: Decimal,
        **kwargs
    ) -> AccountsPayable:
        """Create AP entry"""
        import uuid
        ap = AccountsPayable(
            id=str(uuid.uuid4()),
            bill_id=bill_id,
            vendor_id=vendor_id,
            vendor_name=vendor_name,
            amount=amount,
            **kwargs
        )
        self.payables[ap.id] = ap
        return ap

    def record_ap_payment(
        self,
        ap_id: str,
        amount: Decimal,
        payment_date: datetime,
        payment_method: str = "check"
    ) -> bool:
        """Record payment on AP"""
        ap = self.payables.get(ap_id)
        if not ap:
            return False

        ap.amount_paid += amount
        ap.amount_due = ap.amount - ap.amount_paid

        ap.payments.append({
            "amount": float(amount),
            "date": payment_date,
            "method": payment_method
        })

        if ap.amount_due <= 0:
            ap.status = PaymentStatus.PAID
        elif ap.amount_paid > 0:
            ap.status = PaymentStatus.PARTIAL

        return True

    def get_aging_report(self, as_of_date: datetime = None) -> Dict:
        """AR aging report"""
        if not as_of_date:
            as_of_date = datetime.now()

        current = []
        days_30 = []
        days_60 = []
        days_90 = []
        over_90 = []

        for ar in self.receivables.values():
            if ar.status == PaymentStatus.PAID:
                continue

            days_overdue = (as_of_date - ar.due_date).days

            if days_overdue < 0:
                current.append(ar)
            elif days_overdue <= 30:
                days_30.append(ar)
            elif days_overdue <= 60:
                days_60.append(ar)
            elif days_overdue <= 90:
                days_90.append(ar)
            else:
                over_90.append(ar)

        return {
            "current": {"count": len(current), "total": sum(ar.amount_due for ar in current)},
            "1-30": {"count": len(days_30), "total": sum(ar.amount_due for ar in days_30)},
            "31-60": {"count": len(days_60), "total": sum(ar.amount_due for ar in days_60)},
            "61-90": {"count": len(days_90), "total": sum(ar.amount_due for ar in days_90)},
            "90+": {"count": len(over_90), "total": sum(ar.amount_due for ar in over_90)}
        }


if __name__ == "__main__":
    manager = APARManager()

    ar = manager.create_receivable(
        "INV-001",
        "customer_001",
        "Acme Corp",
        Decimal("1500.00"),
        due_date=datetime.now() + timedelta(days=30)
    )

    manager.record_ar_payment(ar.id, Decimal("500.00"), datetime.now())

    print(f"AR: ${ar.amount_due} due")
    print(f"Status: {ar.status.value}")
