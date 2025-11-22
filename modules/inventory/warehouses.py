"""
NEXUS Inventory - Warehouses Module
Multi-warehouse management with zones and bin locations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional


@dataclass
class Warehouse:
    """Warehouse facility"""
    id: str
    name: str
    code: str

    # Location
    address: str = ""
    city: str = ""
    state: str = ""
    country: str = ""
    zip_code: str = ""

    # Contact
    phone: str = ""
    email: str = ""
    manager_id: Optional[str] = None

    # Capacity
    total_capacity: float = 0.0  # square meters
    used_capacity: float = 0.0

    # Status
    is_active: bool = True

    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class WarehouseZone:
    """Zone within warehouse"""
    id: str
    warehouse_id: str
    name: str
    zone_type: str  # "receiving", "storage", "shipping", "returns"

    capacity: float = 0.0
    temperature_controlled: bool = False
    security_level: str = "standard"


@dataclass
class BinLocation:
    """Bin location within zone"""
    id: str
    warehouse_id: str
    zone_id: str
    code: str  # e.g., "A-01-05"

    # Dimensions
    width: float = 0.0
    height: float = 0.0
    depth: float = 0.0

    # Status
    is_occupied: bool = False
    current_product_id: Optional[str] = None


class WarehouseManager:
    """Warehouse management"""

    def __init__(self):
        self.warehouses: Dict[str, Warehouse] = {}
        self.zones: Dict[str, WarehouseZone] = {}
        self.bins: Dict[str, BinLocation] = {}

    def create_warehouse(
        self,
        name: str,
        code: str,
        address: str,
        **kwargs
    ) -> Warehouse:
        """Create warehouse"""
        import uuid
        warehouse = Warehouse(
            id=str(uuid.uuid4()),
            name=name,
            code=code,
            address=address,
            **kwargs
        )
        self.warehouses[warehouse.id] = warehouse
        return warehouse

    def create_zone(
        self,
        warehouse_id: str,
        name: str,
        zone_type: str,
        **kwargs
    ) -> Optional[WarehouseZone]:
        """Create warehouse zone"""
        if warehouse_id not in self.warehouses:
            return None

        import uuid
        zone = WarehouseZone(
            id=str(uuid.uuid4()),
            warehouse_id=warehouse_id,
            name=name,
            zone_type=zone_type,
            **kwargs
        )
        self.zones[zone.id] = zone
        return zone

    def create_bin(
        self,
        warehouse_id: str,
        zone_id: str,
        code: str,
        **kwargs
    ) -> Optional[BinLocation]:
        """Create bin location"""
        if warehouse_id not in self.warehouses or zone_id not in self.zones:
            return None

        import uuid
        bin_loc = BinLocation(
            id=str(uuid.uuid4()),
            warehouse_id=warehouse_id,
            zone_id=zone_id,
            code=code,
            **kwargs
        )
        self.bins[bin_loc.id] = bin_loc
        return bin_loc

    def assign_product_to_bin(self, bin_id: str, product_id: str) -> bool:
        """Assign product to bin"""
        bin_loc = self.bins.get(bin_id)
        if not bin_loc or bin_loc.is_occupied:
            return False

        bin_loc.is_occupied = True
        bin_loc.current_product_id = product_id
        return True

    def get_warehouse_zones(self, warehouse_id: str) -> List[WarehouseZone]:
        """Get all zones in warehouse"""
        return [z for z in self.zones.values() if z.warehouse_id == warehouse_id]


if __name__ == "__main__":
    manager = WarehouseManager()

    wh = manager.create_warehouse(
        "Main Warehouse",
        "WH-001",
        "123 Storage Ln",
        city="Chicago",
        total_capacity=10000.0
    )

    zone = manager.create_zone(wh.id, "Storage A", "storage", capacity=2500.0)

    bin_loc = manager.create_bin(wh.id, zone.id, "A-01-01", width=1.0, height=2.0, depth=1.0)

    manager.assign_product_to_bin(bin_loc.id, "product_001")

    print(f"Warehouse: {wh.name}")
    print(f"Zones: {len(manager.get_warehouse_zones(wh.id))}")
