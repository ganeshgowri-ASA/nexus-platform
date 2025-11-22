"""
NEXUS E-commerce - Payments Module
Handles payment processing with Stripe and PayPal integration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum


class PaymentMethod(Enum):
    STRIPE = "stripe"
    PAYPAL = "paypal"
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"


class PaymentStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    CANCELLED = "cancelled"


@dataclass
class Payment:
    """Payment transaction"""
    id: str
    order_id: str
    customer_id: str
    amount: float
    currency: str = "USD"

    payment_method: PaymentMethod = PaymentMethod.STRIPE
    status: PaymentStatus = PaymentStatus.PENDING

    # Payment details
    transaction_id: Optional[str] = None
    payment_intent_id: Optional[str] = None

    # Metadata
    metadata: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None

    # Refund
    refund_amount: float = 0.0
    refund_reason: str = ""


class PaymentProcessor:
    """Payment processing"""

    def __init__(self):
        self.payments: Dict[str, Payment] = {}

    def create_payment(
        self,
        order_id: str,
        customer_id: str,
        amount: float,
        payment_method: PaymentMethod,
        **kwargs
    ) -> Payment:
        """Create payment"""
        import uuid
        payment = Payment(
            id=str(uuid.uuid4()),
            order_id=order_id,
            customer_id=customer_id,
            amount=amount,
            payment_method=payment_method,
            **kwargs
        )
        self.payments[payment.id] = payment
        return payment

    def process_payment(self, payment_id: str) -> bool:
        """Process payment"""
        payment = self.payments.get(payment_id)
        if not payment:
            return False

        payment.status = PaymentStatus.PROCESSING

        # Simulate payment processing
        try:
            if payment.payment_method == PaymentMethod.STRIPE:
                payment.transaction_id = f"stripe_{payment.id}"
            elif payment.payment_method == PaymentMethod.PAYPAL:
                payment.transaction_id = f"paypal_{payment.id}"

            payment.status = PaymentStatus.SUCCEEDED
            payment.processed_at = datetime.now()
            return True

        except Exception as e:
            payment.status = PaymentStatus.FAILED
            payment.metadata["error"] = str(e)
            return False

    def refund_payment(self, payment_id: str, amount: float, reason: str = "") -> bool:
        """Refund payment"""
        payment = self.payments.get(payment_id)
        if not payment or payment.status != PaymentStatus.SUCCEEDED:
            return False

        if amount > payment.amount:
            return False

        payment.refund_amount += amount
        payment.refund_reason = reason
        payment.refunded_at = datetime.now()

        if payment.refund_amount >= payment.amount:
            payment.status = PaymentStatus.REFUNDED
        else:
            payment.status = PaymentStatus.PARTIALLY_REFUNDED

        return True


if __name__ == "__main__":
    processor = PaymentProcessor()

    payment = processor.create_payment(
        "order_001",
        "customer_001",
        299.99,
        PaymentMethod.STRIPE
    )

    success = processor.process_payment(payment.id)
    print(f"Payment: {payment.status.value}, Amount: ${payment.amount}")
