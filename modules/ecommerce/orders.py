"""
NEXUS E-commerce - Orders Module
Handles order management, fulfillment, and tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum


class OrderStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class FulfillmentStatus(Enum):
    UNFULFILLED = "unfulfilled"
    PARTIALLY_FULFILLED = "partially_fulfilled"
    FULFILLED = "fulfilled"


@dataclass
class OrderItem:
    """Order line item"""
    product_id: str
    variant_id: Optional[str] = None
    quantity: int = 1
    price: float = 0.0
    name: str = ""
    sku: str = ""
    total: float = 0.0


@dataclass
class Order:
    """Customer order"""
    id: str
    order_number: str
    customer_id: str
    email: str

    # Items
    items: List[OrderItem] = field(default_factory=list)

    # Status
    order_status: OrderStatus = OrderStatus.PENDING
    fulfillment_status: FulfillmentStatus = FulfillmentStatus.UNFULFILLED
    payment_status: str = "pending"

    # Pricing
    subtotal: float = 0.0
    shipping_total: float = 0.0
    tax_total: float = 0.0
    discount_total: float = 0.0
    total: float = 0.0

    # Shipping
    shipping_address: Optional[Dict] = None
    billing_address: Optional[Dict] = None
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None

    # Dates
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None


class OrderManager:
    """Order management"""

    def __init__(self):
        self.orders: Dict[str, Order] = {}
        self.order_counter = 1000

    def create_order(
        self,
        customer_id: str,
        email: str,
        items: List[OrderItem],
        **kwargs
    ) -> Order:
        """Create new order"""
        import uuid
        order_number = f"ORD-{self.order_counter}"
        self.order_counter += 1

        order = Order(
            id=str(uuid.uuid4()),
            order_number=order_number,
            customer_id=customer_id,
            email=email,
            items=items,
            **kwargs
        )

        order.subtotal = sum(item.total for item in items)
        order.total = order.subtotal + order.shipping_total + order.tax_total - order.discount_total

        self.orders[order.id] = order
        return order

    def update_status(self, order_id: str, status: OrderStatus) -> bool:
        """Update order status"""
        order = self.orders.get(order_id)
        if not order:
            return False

        order.order_status = status
        order.updated_at = datetime.now()

        if status == OrderStatus.SHIPPED:
            order.shipped_at = datetime.now()
        elif status == OrderStatus.DELIVERED:
            order.delivered_at = datetime.now()

        return True

    def add_tracking(self, order_id: str, tracking_number: str, carrier: str) -> bool:
        """Add tracking info"""
        order = self.orders.get(order_id)
        if not order:
            return False

        order.tracking_number = tracking_number
        order.carrier = carrier
        order.updated_at = datetime.now()
        return True

    def get_customer_orders(self, customer_id: str) -> List[Order]:
        """Get all orders for customer"""
        return [o for o in self.orders.values() if o.customer_id == customer_id]


if __name__ == "__main__":
    manager = OrderManager()

    items = [
        OrderItem(
            product_id="prod_001",
            quantity=2,
            price=299.99,
            name="Headphones",
            sku="WH-001",
            total=599.98
        )
    ]

    order = manager.create_order(
        "customer_001",
        "customer@email.com",
        items,
        shipping_total=9.99,
        tax_total=48.80
    )

    manager.update_status(order.id, OrderStatus.PROCESSING)
    manager.add_tracking(order.id, "1Z999AA10123456784", "UPS")

    print(f"Order: {order.order_number}, Total: ${order.total:.2f}")
