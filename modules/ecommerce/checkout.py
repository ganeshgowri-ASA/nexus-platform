"""
NEXUS E-commerce - Checkout Module
Handles checkout process, address validation, and order creation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum


class CheckoutStep(Enum):
    CART = "cart"
    SHIPPING = "shipping"
    PAYMENT = "payment"
    REVIEW = "review"
    COMPLETE = "complete"


@dataclass
class Address:
    """Shipping/Billing address"""
    first_name: str
    last_name: str
    address1: str
    address2: str = ""
    city: str = ""
    state: str = ""
    country: str = ""
    zip_code: str = ""
    phone: str = ""


@dataclass
class CheckoutSession:
    """Checkout session"""
    id: str
    cart_id: str
    customer_id: Optional[str] = None

    # Steps
    current_step: CheckoutStep = CheckoutStep.CART

    # Customer info
    email: str = ""
    shipping_address: Optional[Address] = None
    billing_address: Optional[Address] = None
    same_as_shipping: bool = True

    # Shipping
    shipping_method_id: Optional[str] = None
    shipping_rate: float = 0.0

    # Payment
    payment_method_id: Optional[str] = None

    # Totals
    subtotal: float = 0.0
    shipping_total: float = 0.0
    tax_total: float = 0.0
    discount_total: float = 0.0
    total: float = 0.0

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class CheckoutManager:
    """Manages checkout process"""

    def __init__(self):
        self.sessions: Dict[str, CheckoutSession] = {}

    def create_session(self, cart_id: str, customer_id: Optional[str] = None) -> CheckoutSession:
        """Create checkout session"""
        import uuid
        session = CheckoutSession(
            id=str(uuid.uuid4()),
            cart_id=cart_id,
            customer_id=customer_id
        )
        self.sessions[session.id] = session
        return session

    def set_shipping_address(self, session_id: str, address: Address) -> bool:
        """Set shipping address"""
        session = self.sessions.get(session_id)
        if not session:
            return False

        session.shipping_address = address
        session.current_step = CheckoutStep.SHIPPING
        session.updated_at = datetime.now()
        return True

    def set_shipping_method(self, session_id: str, method_id: str, rate: float) -> bool:
        """Set shipping method"""
        session = self.sessions.get(session_id)
        if not session:
            return False

        session.shipping_method_id = method_id
        session.shipping_rate = rate
        session.current_step = CheckoutStep.PAYMENT
        self._recalculate_totals(session)
        return True

    def set_payment_method(self, session_id: str, method_id: str) -> bool:
        """Set payment method"""
        session = self.sessions.get(session_id)
        if not session:
            return False

        session.payment_method_id = method_id
        session.current_step = CheckoutStep.REVIEW
        session.updated_at = datetime.now()
        return True

    def complete_checkout(self, session_id: str) -> Optional[str]:
        """Complete checkout and create order"""
        session = self.sessions.get(session_id)
        if not session:
            return None

        session.current_step = CheckoutStep.COMPLETE
        session.completed_at = datetime.now()

        # Return order ID (would create actual order)
        import uuid
        return str(uuid.uuid4())

    def _recalculate_totals(self, session: CheckoutSession) -> None:
        """Recalculate checkout totals"""
        session.shipping_total = session.shipping_rate
        session.tax_total = session.subtotal * 0.08  # 8% tax example
        session.total = session.subtotal + session.shipping_total + session.tax_total - session.discount_total
        session.updated_at = datetime.now()


if __name__ == "__main__":
    manager = CheckoutManager()

    session = manager.create_session("cart_001", "customer_001")

    address = Address(
        first_name="John",
        last_name="Doe",
        address1="123 Main St",
        city="New York",
        state="NY",
        country="USA",
        zip_code="10001",
        phone="555-1234"
    )

    manager.set_shipping_address(session.id, address)
    manager.set_shipping_method(session.id, "standard", 9.99)
    manager.set_payment_method(session.id, "stripe")

    order_id = manager.complete_checkout(session.id)
    print(f"Order created: {order_id}")
