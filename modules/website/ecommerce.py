"""
E-commerce Manager - Product management, cart, checkout, and payment integration
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
import uuid


class PaymentProvider(Enum):
    """Payment providers"""
    STRIPE = "stripe"
    PAYPAL = "paypal"
    SQUARE = "square"
    RAZORPAY = "razorpay"
    BRAINTREE = "braintree"


class OrderStatus(Enum):
    """Order status"""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class ProductStatus(Enum):
    """Product status"""
    ACTIVE = "active"
    DRAFT = "draft"
    ARCHIVED = "archived"
    OUT_OF_STOCK = "out_of_stock"


@dataclass
class Product:
    """Product definition"""
    product_id: str
    name: str
    description: str
    price: float
    currency: str = "USD"
    status: ProductStatus = ProductStatus.ACTIVE
    sku: Optional[str] = None
    images: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    inventory_count: int = 0
    weight: Optional[float] = None
    dimensions: Optional[Dict[str, float]] = None
    variants: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "product_id": self.product_id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "currency": self.currency,
            "status": self.status.value,
            "sku": self.sku,
            "images": self.images,
            "categories": self.categories,
            "tags": self.tags,
            "inventory_count": self.inventory_count,
            "weight": self.weight,
            "dimensions": self.dimensions,
            "variants": self.variants,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class CartItem:
    """Shopping cart item"""
    product_id: str
    product_name: str
    quantity: int
    price: float
    variant_id: Optional[str] = None
    variant_name: Optional[str] = None

    def get_subtotal(self) -> float:
        """Get subtotal for this item"""
        return self.price * self.quantity

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "quantity": self.quantity,
            "price": self.price,
            "variant_id": self.variant_id,
            "variant_name": self.variant_name,
            "subtotal": self.get_subtotal(),
        }


@dataclass
class Cart:
    """Shopping cart"""
    cart_id: str
    items: List[CartItem] = field(default_factory=list)
    discount_code: Optional[str] = None
    discount_amount: float = 0.0
    tax_rate: float = 0.0
    shipping_cost: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def get_subtotal(self) -> float:
        """Get cart subtotal"""
        return sum(item.get_subtotal() for item in self.items)

    def get_tax(self) -> float:
        """Get tax amount"""
        return self.get_subtotal() * self.tax_rate

    def get_total(self) -> float:
        """Get cart total"""
        return self.get_subtotal() - self.discount_amount + self.get_tax() + self.shipping_cost

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "cart_id": self.cart_id,
            "items": [item.to_dict() for item in self.items],
            "discount_code": self.discount_code,
            "discount_amount": self.discount_amount,
            "tax_rate": self.tax_rate,
            "shipping_cost": self.shipping_cost,
            "subtotal": self.get_subtotal(),
            "tax": self.get_tax(),
            "total": self.get_total(),
            "items_count": len(self.items),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class Order:
    """Customer order"""
    order_id: str
    customer_email: str
    items: List[CartItem]
    subtotal: float
    tax: float
    shipping_cost: float
    discount_amount: float
    total: float
    status: OrderStatus
    payment_method: str
    shipping_address: Dict[str, str]
    billing_address: Dict[str, str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tracking_number: Optional[str] = None
    notes: str = ""

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "order_id": self.order_id,
            "customer_email": self.customer_email,
            "items": [item.to_dict() for item in self.items],
            "subtotal": self.subtotal,
            "tax": self.tax,
            "shipping_cost": self.shipping_cost,
            "discount_amount": self.discount_amount,
            "total": self.total,
            "status": self.status.value,
            "payment_method": self.payment_method,
            "shipping_address": self.shipping_address,
            "billing_address": self.billing_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "tracking_number": self.tracking_number,
            "notes": self.notes,
        }


@dataclass
class DiscountCode:
    """Discount/coupon code"""
    code_id: str
    code: str
    discount_type: str  # percentage, fixed
    discount_value: float
    min_purchase: float = 0.0
    max_uses: Optional[int] = None
    uses_count: int = 0
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    active: bool = True

    def is_valid(self) -> bool:
        """Check if discount code is valid"""
        now = datetime.now()

        if not self.active:
            return False

        if self.valid_from and now < self.valid_from:
            return False

        if self.valid_until and now > self.valid_until:
            return False

        if self.max_uses and self.uses_count >= self.max_uses:
            return False

        return True

    def calculate_discount(self, subtotal: float) -> float:
        """Calculate discount amount"""
        if not self.is_valid() or subtotal < self.min_purchase:
            return 0.0

        if self.discount_type == "percentage":
            return subtotal * (self.discount_value / 100)
        else:  # fixed
            return min(self.discount_value, subtotal)


class EcommerceManager:
    """Manager for e-commerce functionality"""

    def __init__(self):
        self.products: Dict[str, Product] = {}
        self.carts: Dict[str, Cart] = {}
        self.orders: Dict[str, Order] = {}
        self.discount_codes: Dict[str, DiscountCode] = {}
        self.payment_providers: Dict[str, Dict[str, Any]] = {}

    # Product Management

    def create_product(
        self,
        name: str,
        description: str,
        price: float,
        **kwargs
    ) -> Product:
        """Create a new product"""
        product_id = str(uuid.uuid4())

        product = Product(
            product_id=product_id,
            name=name,
            description=description,
            price=price,
            **kwargs
        )

        self.products[product_id] = product
        return product

    def update_product(
        self,
        product_id: str,
        **updates
    ) -> Optional[Product]:
        """Update product"""
        product = self.products.get(product_id)
        if not product:
            return None

        for key, value in updates.items():
            if hasattr(product, key):
                setattr(product, key, value)

        product.updated_at = datetime.now()
        return product

    def delete_product(self, product_id: str) -> bool:
        """Delete product"""
        if product_id in self.products:
            del self.products[product_id]
            return True
        return False

    def get_product(self, product_id: str) -> Optional[Product]:
        """Get product by ID"""
        return self.products.get(product_id)

    def get_all_products(
        self,
        status: Optional[ProductStatus] = None,
        category: Optional[str] = None,
    ) -> List[Product]:
        """Get all products with optional filters"""
        products = list(self.products.values())

        if status:
            products = [p for p in products if p.status == status]

        if category:
            products = [p for p in products if category in p.categories]

        return products

    def search_products(self, query: str) -> List[Product]:
        """Search products"""
        query = query.lower()
        return [
            p for p in self.products.values()
            if query in p.name.lower()
            or query in p.description.lower()
            or any(query in tag.lower() for tag in p.tags)
        ]

    def update_inventory(self, product_id: str, quantity: int) -> bool:
        """Update product inventory"""
        product = self.products.get(product_id)
        if not product:
            return False

        product.inventory_count = quantity
        if quantity == 0:
            product.status = ProductStatus.OUT_OF_STOCK
        elif product.status == ProductStatus.OUT_OF_STOCK:
            product.status = ProductStatus.ACTIVE

        return True

    # Shopping Cart

    def create_cart(self) -> Cart:
        """Create a new shopping cart"""
        cart_id = str(uuid.uuid4())
        cart = Cart(cart_id=cart_id)
        self.carts[cart_id] = cart
        return cart

    def get_cart(self, cart_id: str) -> Optional[Cart]:
        """Get cart by ID"""
        return self.carts.get(cart_id)

    def add_to_cart(
        self,
        cart_id: str,
        product_id: str,
        quantity: int = 1,
        variant_id: Optional[str] = None,
    ) -> Optional[Cart]:
        """Add item to cart"""
        cart = self.carts.get(cart_id)
        product = self.products.get(product_id)

        if not cart or not product:
            return None

        # Check if item already in cart
        for item in cart.items:
            if item.product_id == product_id and item.variant_id == variant_id:
                item.quantity += quantity
                cart.updated_at = datetime.now()
                return cart

        # Add new item
        cart_item = CartItem(
            product_id=product_id,
            product_name=product.name,
            quantity=quantity,
            price=product.price,
            variant_id=variant_id,
        )

        cart.items.append(cart_item)
        cart.updated_at = datetime.now()
        return cart

    def remove_from_cart(
        self,
        cart_id: str,
        product_id: str,
        variant_id: Optional[str] = None,
    ) -> Optional[Cart]:
        """Remove item from cart"""
        cart = self.carts.get(cart_id)
        if not cart:
            return None

        cart.items = [
            item for item in cart.items
            if not (item.product_id == product_id and item.variant_id == variant_id)
        ]

        cart.updated_at = datetime.now()
        return cart

    def update_cart_item_quantity(
        self,
        cart_id: str,
        product_id: str,
        quantity: int,
        variant_id: Optional[str] = None,
    ) -> Optional[Cart]:
        """Update item quantity in cart"""
        cart = self.carts.get(cart_id)
        if not cart:
            return None

        for item in cart.items:
            if item.product_id == product_id and item.variant_id == variant_id:
                if quantity <= 0:
                    cart.items.remove(item)
                else:
                    item.quantity = quantity
                cart.updated_at = datetime.now()
                return cart

        return None

    def apply_discount_code(self, cart_id: str, code: str) -> Optional[Cart]:
        """Apply discount code to cart"""
        cart = self.carts.get(cart_id)
        discount = None

        # Find discount code
        for dc in self.discount_codes.values():
            if dc.code.upper() == code.upper():
                discount = dc
                break

        if not cart or not discount or not discount.is_valid():
            return None

        discount_amount = discount.calculate_discount(cart.get_subtotal())
        cart.discount_code = code
        cart.discount_amount = discount_amount
        cart.updated_at = datetime.now()

        return cart

    def clear_cart(self, cart_id: str) -> bool:
        """Clear cart"""
        cart = self.carts.get(cart_id)
        if not cart:
            return False

        cart.items = []
        cart.discount_code = None
        cart.discount_amount = 0.0
        cart.updated_at = datetime.now()
        return True

    # Order Management

    def create_order(
        self,
        cart_id: str,
        customer_email: str,
        payment_method: str,
        shipping_address: Dict[str, str],
        billing_address: Optional[Dict[str, str]] = None,
    ) -> Optional[Order]:
        """Create order from cart"""
        cart = self.carts.get(cart_id)
        if not cart or not cart.items:
            return None

        order_id = str(uuid.uuid4())

        order = Order(
            order_id=order_id,
            customer_email=customer_email,
            items=cart.items.copy(),
            subtotal=cart.get_subtotal(),
            tax=cart.get_tax(),
            shipping_cost=cart.shipping_cost,
            discount_amount=cart.discount_amount,
            total=cart.get_total(),
            status=OrderStatus.PENDING,
            payment_method=payment_method,
            shipping_address=shipping_address,
            billing_address=billing_address or shipping_address,
        )

        self.orders[order_id] = order

        # Update inventory
        for item in cart.items:
            product = self.products.get(item.product_id)
            if product:
                product.inventory_count -= item.quantity

        # Clear cart
        self.clear_cart(cart_id)

        return order

    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        return self.orders.get(order_id)

    def update_order_status(
        self,
        order_id: str,
        status: OrderStatus,
        tracking_number: Optional[str] = None,
    ) -> Optional[Order]:
        """Update order status"""
        order = self.orders.get(order_id)
        if not order:
            return None

        order.status = status
        if tracking_number:
            order.tracking_number = tracking_number
        order.updated_at = datetime.now()

        return order

    def get_orders_by_customer(self, customer_email: str) -> List[Order]:
        """Get all orders for a customer"""
        return [
            order for order in self.orders.values()
            if order.customer_email == customer_email
        ]

    def get_all_orders(
        self,
        status: Optional[OrderStatus] = None,
    ) -> List[Order]:
        """Get all orders with optional filter"""
        orders = list(self.orders.values())

        if status:
            orders = [o for o in orders if o.status == status]

        return sorted(orders, key=lambda o: o.created_at or datetime.now(), reverse=True)

    # Discount Codes

    def create_discount_code(
        self,
        code: str,
        discount_type: str,
        discount_value: float,
        **kwargs
    ) -> DiscountCode:
        """Create discount code"""
        code_id = str(uuid.uuid4())

        discount = DiscountCode(
            code_id=code_id,
            code=code.upper(),
            discount_type=discount_type,
            discount_value=discount_value,
            **kwargs
        )

        self.discount_codes[code_id] = discount
        return discount

    def get_discount_code(self, code: str) -> Optional[DiscountCode]:
        """Get discount code by code"""
        for discount in self.discount_codes.values():
            if discount.code.upper() == code.upper():
                return discount
        return None

    def deactivate_discount_code(self, code_id: str) -> bool:
        """Deactivate discount code"""
        discount = self.discount_codes.get(code_id)
        if discount:
            discount.active = False
            return True
        return False

    # Payment Integration

    def setup_payment_provider(
        self,
        provider: PaymentProvider,
        api_key: str,
        **config
    ) -> Dict[str, Any]:
        """Setup payment provider"""
        self.payment_providers[provider.value] = {
            "provider": provider,
            "api_key": api_key,
            "config": config,
            "enabled": True,
        }

        return self.payment_providers[provider.value]

    def process_payment(
        self,
        order_id: str,
        payment_method: str,
        payment_token: str,
    ) -> Dict[str, Any]:
        """Process payment (placeholder)"""
        order = self.orders.get(order_id)
        if not order:
            return {"success": False, "error": "Order not found"}

        # In real implementation, this would integrate with payment provider
        # For now, simulate successful payment
        order.status = OrderStatus.PROCESSING

        return {
            "success": True,
            "transaction_id": str(uuid.uuid4()),
            "amount": order.total,
            "currency": "USD",
        }

    # Analytics & Reports

    def get_sales_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get sales report"""
        from datetime import timedelta

        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()

        orders = [
            o for o in self.orders.values()
            if o.created_at and start_date <= o.created_at <= end_date
        ]

        total_revenue = sum(o.total for o in orders)
        total_orders = len(orders)

        return {
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "average_order_value": total_revenue / total_orders if total_orders > 0 else 0,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
        }

    def get_top_products(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top selling products"""
        product_sales: Dict[str, int] = {}

        for order in self.orders.values():
            for item in order.items:
                product_sales[item.product_id] = product_sales.get(item.product_id, 0) + item.quantity

        top_products = sorted(
            product_sales.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]

        return [
            {
                "product_id": product_id,
                "product": self.products.get(product_id),
                "units_sold": units,
            }
            for product_id, units in top_products
        ]

    def get_ecommerce_stats(self) -> Dict[str, Any]:
        """Get e-commerce statistics"""
        return {
            "total_products": len(self.products),
            "active_products": len([p for p in self.products.values() if p.status == ProductStatus.ACTIVE]),
            "total_orders": len(self.orders),
            "pending_orders": len([o for o in self.orders.values() if o.status == OrderStatus.PENDING]),
            "total_revenue": sum(o.total for o in self.orders.values()),
            "active_carts": len(self.carts),
            "active_discount_codes": len([d for d in self.discount_codes.values() if d.active]),
        }
