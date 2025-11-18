"""
NEXUS Accounting - Invoicing Module
Invoice creation, recurring invoices, payment processing.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum
from decimal import Decimal


class InvoiceStatus(Enum):
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


@dataclass
class InvoiceLineItem:
    """Invoice line item"""
    id: str
    description: str
    quantity: Decimal = Decimal("1.00")
    rate: Decimal = Decimal("0.00")
    amount: Decimal = field(init=False)
    tax_rate: Decimal = Decimal("0.00")

    def __post_init__(self):
        self.amount = self.quantity * self.rate


@dataclass
class Invoice:
    """Customer invoice"""
    id: str
    invoice_number: str
    customer_id: str
    customer_name: str

    # Line items
    items: List[InvoiceLineItem] = field(default_factory=list)

    # Amounts
    subtotal: Decimal = Decimal("0.00")
    tax: Decimal = Decimal("0.00")
    total: Decimal = Decimal("0.00")
    amount_paid: Decimal = Decimal("0.00")
    balance_due: Decimal = field(init=False)

    # Dates
    invoice_date: datetime = field(default_factory=datetime.now)
    due_date: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=30))

    # Status
    status: InvoiceStatus = InvoiceStatus.DRAFT

    # Metadata
    notes: str = ""
    terms: str = "Net 30"
    po_number: str = ""

    created_at: datetime = field(default_factory=datetime.now)
    sent_at: Optional[datetime] = None

    def __post_init__(self):
        self._calculate_totals()
        self.balance_due = self.total - self.amount_paid

    def _calculate_totals(self):
        self.subtotal = sum(item.amount for item in self.items)
        self.tax = sum(item.amount * item.tax_rate for item in self.items)
        self.total = self.subtotal + self.tax


class InvoiceManager:
    """Invoice management"""

    def __init__(self):
        self.invoices: Dict[str, Invoice] = {}
        self.invoice_counter = 1000

    def create_invoice(
        self,
        customer_id: str,
        customer_name: str,
        items: List[Dict],
        **kwargs
    ) -> Invoice:
        """Create invoice"""
        import uuid
        invoice_number = f"INV-{self.invoice_counter}"
        self.invoice_counter += 1

        line_items = []
        for item_data in items:
            line_item = InvoiceLineItem(
                id=str(uuid.uuid4()),
                description=item_data['description'],
                quantity=Decimal(str(item_data.get('quantity', 1))),
                rate=Decimal(str(item_data['rate'])),
                tax_rate=Decimal(str(item_data.get('tax_rate', 0)))
            )
            line_items.append(line_item)

        invoice = Invoice(
            id=str(uuid.uuid4()),
            invoice_number=invoice_number,
            customer_id=customer_id,
            customer_name=customer_name,
            items=line_items,
            **kwargs
        )

        self.invoices[invoice.id] = invoice
        return invoice

    def send_invoice(self, invoice_id: str) -> bool:
        """Send invoice to customer"""
        invoice = self.invoices.get(invoice_id)
        if not invoice or invoice.status == InvoiceStatus.CANCELLED:
            return False

        invoice.status = InvoiceStatus.SENT
        invoice.sent_at = datetime.now()
        return True

    def record_payment(
        self,
        invoice_id: str,
        amount: Decimal,
        payment_date: datetime = None
    ) -> bool:
        """Record payment on invoice"""
        invoice = self.invoices.get(invoice_id)
        if not invoice:
            return False

        invoice.amount_paid += amount
        invoice.balance_due = invoice.total - invoice.amount_paid

        if invoice.balance_due <= 0:
            invoice.status = InvoiceStatus.PAID
        elif invoice.amount_paid > 0:
            invoice.status = InvoiceStatus.PARTIAL

        return True

    def get_overdue_invoices(self) -> List[Invoice]:
        """Get overdue invoices"""
        now = datetime.now()
        return [
            inv for inv in self.invoices.values()
            if inv.status not in [InvoiceStatus.PAID, InvoiceStatus.CANCELLED]
            and inv.due_date < now
        ]


if __name__ == "__main__":
    manager = InvoiceManager()

    invoice = manager.create_invoice(
        "customer_001",
        "Acme Corp",
        items=[
            {"description": "Consulting Services", "quantity": 10, "rate": 150.00, "tax_rate": 0.08},
            {"description": "Software License", "quantity": 1, "rate": 500.00, "tax_rate": 0.08}
        ],
        terms="Net 30"
    )

    manager.send_invoice(invoice.id)
    manager.record_payment(invoice.id, Decimal("500.00"))

    print(f"Invoice: {invoice.invoice_number}")
    print(f"Total: ${invoice.total}")
    print(f"Balance: ${invoice.balance_due}")
