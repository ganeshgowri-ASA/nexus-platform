"""
NEXUS E-commerce - Shopping Cart Module
Handles cart operations, line items, discounts, and cart persistence.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum


@dataclass
class CartItem:
    """Item in shopping cart"""
    product_id: str
    variant_id: Optional[str] = None
    quantity: int = 1

    # Product details (cached for performance)
    name: str = ""
    price: float = 0.0
    image_url: str = ""
    sku: str = ""

    # Customization
    attributes: Dict[str, str] = field(default_factory=dict)
    custom_note: str = ""

    # Pricing
    line_price: float = 0.0  # price * quantity
    discount_amount: float = 0.0
    final_price: float = 0.0

    added_at: datetime = field(default_factory=datetime.now)


@dataclass
class ShoppingCart:
    """Shopping cart"""
    id: str
    customer_id: Optional[str] = None
    session_id: Optional[str] = None

    # Items
    items: List[CartItem] = field(default_factory=list)

    # Pricing
    subtotal: float = 0.0
    discount_total: float = 0.0
    tax_total: float = 0.0
    shipping_total: float = 0.0
    total: float = 0.0

    # Discounts
    coupon_code: Optional[str] = None
    discount_codes: List[str] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=30))

    # Status
    is_active: bool = True
    converted_to_order: bool = False


class CartManager:
    """Manages shopping carts"""

    def __init__(self):
        self.carts: Dict[str, ShoppingCart] = {}

    def create_cart(self, customer_id: Optional[str] = None, session_id: Optional[str] = None) -> ShoppingCart:
        """Create a new cart"""
        import uuid
        cart_id = str(uuid.uuid4())

        cart = ShoppingCart(
            id=cart_id,
            customer_id=customer_id,
            session_id=session_id
        )

        self.carts[cart_id] = cart
        return cart

    def get_cart(self, cart_id: str) -> Optional[ShoppingCart]:
        """Get cart by ID"""
        return self.carts.get(cart_id)

    def get_customer_cart(self, customer_id: str) -> Optional[ShoppingCart]:
        """Get active cart for customer"""
        for cart in self.carts.values():
            if cart.customer_id == customer_id and cart.is_active and not cart.converted_to_order:
                return cart
        return None

    def add_item(
        self,
        cart_id: str,
        product_id: str,
        quantity: int = 1,
        variant_id: Optional[str] = None,
        **kwargs
    ) -> Optional[CartItem]:
        """Add item to cart"""
        cart = self.get_cart(cart_id)
        if not cart:
            return None

        # Check if item already in cart
        for item in cart.items:
            if item.product_id == product_id and item.variant_id == variant_id:
                item.quantity += quantity
                self._recalculate_cart(cart)
                return item

        # Add new item
        item = CartItem(
            product_id=product_id,
            variant_id=variant_id,
            quantity=quantity,
            **kwargs
        )
        item.line_price = item.price * quantity
        item.final_price = item.line_price

        cart.items.append(item)
        self._recalculate_cart(cart)

        return item

    def update_quantity(self, cart_id: str, product_id: str, quantity: int) -> bool:
        """Update item quantity"""
        cart = self.get_cart(cart_id)
        if not cart:
            return False

        for item in cart.items:
            if item.product_id == product_id:
                if quantity <= 0:
                    cart.items.remove(item)
                else:
                    item.quantity = quantity
                self._recalculate_cart(cart)
                return True

        return False

    def remove_item(self, cart_id: str, product_id: str) -> bool:
        """Remove item from cart"""
        return self.update_quantity(cart_id, product_id, 0)

    def apply_coupon(self, cart_id: str, coupon_code: str) -> bool:
        """Apply coupon code"""
        cart = self.get_cart(cart_id)
        if not cart:
            return False

        cart.coupon_code = coupon_code
        if coupon_code not in cart.discount_codes:
            cart.discount_codes.append(coupon_code)

        self._recalculate_cart(cart)
        return True

    def _recalculate_cart(self, cart: ShoppingCart) -> None:
        """Recalculate cart totals"""
        cart.subtotal = sum(item.price * item.quantity for item in cart.items)
        cart.discount_total = sum(item.discount_amount for item in cart.items)
        cart.total = cart.subtotal - cart.discount_total + cart.tax_total + cart.shipping_total
        cart.updated_at = datetime.now()

    def clear_cart(self, cart_id: str) -> bool:
        """Clear all items from cart"""
        cart = self.get_cart(cart_id)
        if not cart:
            return False

        cart.items = []
        self._recalculate_cart(cart)
        return True

    def get_item_count(self, cart_id: str) -> int:
        """Get total number of items in cart"""
        cart = self.get_cart(cart_id)
        if not cart:
            return 0

        return sum(item.quantity for item in cart.items)


# Example usage
if __name__ == "__main__":
    manager = CartManager()

    cart = manager.create_cart(customer_id="customer_001")

    manager.add_item(
        cart.id,
        "product_001",
        quantity=2,
        name="Wireless Headphones",
        price=299.99,
        sku="WH-001"
    )

    manager.apply_coupon(cart.id, "SAVE10")

    print(f"Cart total: ${cart.total:.2f}")
    print(f"Items: {manager.get_item_count(cart.id)}")
