"""
NEXUS Inventory - Stock Management Module
Handles stock levels, tracking, adjustments, and reorder points.
Rival to Cin7 inventory management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum


class StockStatus(Enum):
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"


class AdjustmentReason(Enum):
    RECEIVED = "received"
    SOLD = "sold"
    DAMAGED = "damaged"
    RETURNED = "returned"
    RECOUNT = "recount"
    THEFT = "theft"
    EXPIRED = "expired"


@dataclass
class StockItem:
    """Stock item tracking"""
    id: str
    product_id: str
    variant_id: Optional[str] = None
    sku: str = ""
    name: str = ""

    # Quantities
    quantity_on_hand: int = 0
    quantity_available: int = 0
    quantity_reserved: int = 0
    quantity_incoming: int = 0

    # Reorder settings
    reorder_point: int = 10
    reorder_quantity: int = 50
    max_stock_level: int = 100

    # Location
    warehouse_id: str = ""
    bin_location: str = ""

    # Status
    status: StockStatus = StockStatus.IN_STOCK

    # Metadata
    last_counted: Optional[datetime] = None
    last_received: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class StockAdjustment:
    """Stock adjustment record"""
    id: str
    stock_item_id: str
    adjustment_type: AdjustmentReason
    quantity_change: int  # positive or negative
    previous_quantity: int
    new_quantity: int

    reason: str = ""
    notes: str = ""
    user_id: str = ""

    created_at: datetime = field(default_factory=datetime.now)


class StockManager:
    """Stock management"""

    def __init__(self):
        self.stock_items: Dict[str, StockItem] = {}
        self.adjustments: List[StockAdjustment] = []

    def create_stock_item(
        self,
        product_id: str,
        sku: str,
        name: str,
        warehouse_id: str,
        **kwargs
    ) -> StockItem:
        """Create stock item"""
        import uuid
        item = StockItem(
            id=str(uuid.uuid4()),
            product_id=product_id,
            sku=sku,
            name=name,
            warehouse_id=warehouse_id,
            **kwargs
        )

        item.quantity_available = item.quantity_on_hand - item.quantity_reserved
        self._update_status(item)

        self.stock_items[item.id] = item
        return item

    def adjust_stock(
        self,
        stock_item_id: str,
        quantity_change: int,
        adjustment_type: AdjustmentReason,
        reason: str = "",
        user_id: str = ""
    ) -> Optional[StockAdjustment]:
        """Adjust stock level"""
        item = self.stock_items.get(stock_item_id)
        if not item:
            return None

        previous_qty = item.quantity_on_hand

        import uuid
        adjustment = StockAdjustment(
            id=str(uuid.uuid4()),
            stock_item_id=stock_item_id,
            adjustment_type=adjustment_type,
            quantity_change=quantity_change,
            previous_quantity=previous_qty,
            new_quantity=previous_qty + quantity_change,
            reason=reason,
            user_id=user_id
        )

        item.quantity_on_hand += quantity_change
        item.quantity_available = item.quantity_on_hand - item.quantity_reserved
        item.updated_at = datetime.now()

        self._update_status(item)
        self.adjustments.append(adjustment)

        return adjustment

    def reserve_stock(self, stock_item_id: str, quantity: int) -> bool:
        """Reserve stock for order"""
        item = self.stock_items.get(stock_item_id)
        if not item or item.quantity_available < quantity:
            return False

        item.quantity_reserved += quantity
        item.quantity_available -= quantity
        item.updated_at = datetime.now()
        return True

    def release_stock(self, stock_item_id: str, quantity: int) -> bool:
        """Release reserved stock"""
        item = self.stock_items.get(stock_item_id)
        if not item or item.quantity_reserved < quantity:
            return False

        item.quantity_reserved -= quantity
        item.quantity_available += quantity
        item.updated_at = datetime.now()
        return True

    def _update_status(self, item: StockItem) -> None:
        """Update stock status"""
        if item.quantity_on_hand <= 0:
            item.status = StockStatus.OUT_OF_STOCK
        elif item.quantity_on_hand <= item.reorder_point:
            item.status = StockStatus.LOW_STOCK
        else:
            item.status = StockStatus.IN_STOCK

    def get_low_stock_items(self) -> List[StockItem]:
        """Get items below reorder point"""
        return [
            item for item in self.stock_items.values()
            if item.quantity_on_hand <= item.reorder_point
        ]

    def get_stock_value(self, cost_per_unit: float) -> float:
        """Calculate total inventory value"""
        total = sum(item.quantity_on_hand for item in self.stock_items.values())
        return total * cost_per_unit


if __name__ == "__main__":
    manager = StockManager()

    item = manager.create_stock_item(
        "product_001",
        "SKU-001",
        "Widget A",
        "warehouse_001",
        quantity_on_hand=100,
        reorder_point=20
    )

    manager.adjust_stock(item.id, -10, AdjustmentReason.SOLD, "Customer order")
    manager.reserve_stock(item.id, 5)

    print(f"Stock: {item.name}")
    print(f"Available: {item.quantity_available}")
    print(f"Status: {item.status.value}")
