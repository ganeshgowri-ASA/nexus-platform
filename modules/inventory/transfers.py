"""
NEXUS Inventory - Stock Transfers Module
Inter-warehouse transfers and movements.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum


class TransferStatus(Enum):
    DRAFT = "draft"
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class TransferItem:
    """Item being transferred"""
    product_id: str
    variant_id: Optional[str] = None
    quantity: int = 1
    sku: str = ""
    name: str = ""


@dataclass
class StockTransfer:
    """Stock transfer between warehouses"""
    id: str
    transfer_number: str

    # Locations
    from_warehouse_id: str
    to_warehouse_id: str

    # Items
    items: List[TransferItem] = field(default_factory=list)

    # Status
    status: TransferStatus = TransferStatus.DRAFT

    # Tracking
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None

    # People
    requested_by: str = ""
    approved_by: Optional[str] = None

    # Notes
    notes: str = ""
    reason: str = ""

    # Dates
    created_at: datetime = field(default_factory=datetime.now)
    shipped_at: Optional[datetime] = None
    received_at: Optional[datetime] = None


class TransferManager:
    """Transfer management"""

    def __init__(self):
        self.transfers: Dict[str, StockTransfer] = {}
        self.transfer_counter = 1000

    def create_transfer(
        self,
        from_warehouse_id: str,
        to_warehouse_id: str,
        items: List[TransferItem],
        requested_by: str,
        **kwargs
    ) -> StockTransfer:
        """Create stock transfer"""
        import uuid
        transfer_number = f"TRF-{self.transfer_counter}"
        self.transfer_counter += 1

        transfer = StockTransfer(
            id=str(uuid.uuid4()),
            transfer_number=transfer_number,
            from_warehouse_id=from_warehouse_id,
            to_warehouse_id=to_warehouse_id,
            items=items,
            requested_by=requested_by,
            **kwargs
        )

        self.transfers[transfer.id] = transfer
        return transfer

    def approve_transfer(self, transfer_id: str, approved_by: str) -> bool:
        """Approve transfer"""
        transfer = self.transfers.get(transfer_id)
        if not transfer or transfer.status != TransferStatus.DRAFT:
            return False

        transfer.status = TransferStatus.PENDING
        transfer.approved_by = approved_by
        return True

    def ship_transfer(self, transfer_id: str, tracking: str, carrier: str) -> bool:
        """Mark transfer as shipped"""
        transfer = self.transfers.get(transfer_id)
        if not transfer or transfer.status != TransferStatus.PENDING:
            return False

        transfer.status = TransferStatus.IN_TRANSIT
        transfer.tracking_number = tracking
        transfer.carrier = carrier
        transfer.shipped_at = datetime.now()
        return True

    def receive_transfer(self, transfer_id: str) -> bool:
        """Mark transfer as received"""
        transfer = self.transfers.get(transfer_id)
        if not transfer or transfer.status != TransferStatus.IN_TRANSIT:
            return False

        transfer.status = TransferStatus.COMPLETED
        transfer.received_at = datetime.now()
        return True

    def get_warehouse_transfers(
        self,
        warehouse_id: str,
        direction: str = "both"  # "incoming", "outgoing", "both"
    ) -> List[StockTransfer]:
        """Get transfers for warehouse"""
        transfers = []

        for t in self.transfers.values():
            if direction in ["incoming", "both"] and t.to_warehouse_id == warehouse_id:
                transfers.append(t)
            elif direction in ["outgoing", "both"] and t.from_warehouse_id == warehouse_id:
                transfers.append(t)

        return transfers


if __name__ == "__main__":
    manager = TransferManager()

    items = [
        TransferItem(
            product_id="prod_001",
            quantity=10,
            sku="SKU-001",
            name="Widget A"
        )
    ]

    transfer = manager.create_transfer(
        "warehouse_001",
        "warehouse_002",
        items,
        "user_001",
        reason="Stock balancing"
    )

    manager.approve_transfer(transfer.id, "manager_001")
    manager.ship_transfer(transfer.id, "TRACK123", "UPS")
    manager.receive_transfer(transfer.id)

    print(f"Transfer: {transfer.transfer_number}")
    print(f"Status: {transfer.status.value}")
