"""
Tests for e-commerce functionality
"""

import pytest
from modules.website.ecommerce import (
    EcommerceManager,
    ProductStatus,
    OrderStatus,
)


def test_create_product():
    """Test product creation"""
    manager = EcommerceManager()

    product = manager.create_product(
        name="Test Product",
        description="A test product",
        price=29.99,
        sku="TEST-001",
        inventory_count=100,
    )

    assert product.name == "Test Product"
    assert product.price == 29.99
    assert product.sku == "TEST-001"
    assert product.inventory_count == 100


def test_shopping_cart():
    """Test shopping cart functionality"""
    manager = EcommerceManager()

    # Create product
    product = manager.create_product(
        name="Test Product",
        description="A test product",
        price=29.99,
    )

    # Create cart
    cart = manager.create_cart()

    # Add to cart
    updated_cart = manager.add_to_cart(
        cart.cart_id,
        product.product_id,
        quantity=2,
    )

    assert len(updated_cart.items) == 1
    assert updated_cart.items[0].quantity == 2
    assert updated_cart.get_subtotal() == 59.98


def test_discount_code():
    """Test discount code application"""
    manager = EcommerceManager()

    # Create discount code
    discount = manager.create_discount_code(
        code="SAVE20",
        discount_type="percentage",
        discount_value=20.0,
    )

    assert discount.code == "SAVE20"
    assert discount.is_valid() is True

    # Test discount calculation
    discount_amount = discount.calculate_discount(100.0)
    assert discount_amount == 20.0


def test_create_order():
    """Test order creation"""
    manager = EcommerceManager()

    # Create product
    product = manager.create_product(
        name="Test Product",
        description="A test product",
        price=29.99,
        inventory_count=100,
    )

    # Create cart and add product
    cart = manager.create_cart()
    manager.add_to_cart(cart.cart_id, product.product_id, quantity=2)

    # Create order
    order = manager.create_order(
        cart_id=cart.cart_id,
        customer_email="test@example.com",
        payment_method="stripe",
        shipping_address={
            "street": "123 Main St",
            "city": "Test City",
            "state": "TS",
            "zip": "12345",
        },
    )

    assert order is not None
    assert order.customer_email == "test@example.com"
    assert order.status == OrderStatus.PENDING
    assert len(order.items) == 1


def test_inventory_update():
    """Test inventory management"""
    manager = EcommerceManager()

    product = manager.create_product(
        name="Test Product",
        description="A test product",
        price=29.99,
        inventory_count=100,
    )

    # Update inventory
    manager.update_inventory(product.product_id, 50)

    assert product.inventory_count == 50

    # Update to zero should change status
    manager.update_inventory(product.product_id, 0)

    assert product.inventory_count == 0
    assert product.status == ProductStatus.OUT_OF_STOCK


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
