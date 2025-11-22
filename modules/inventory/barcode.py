"""
NEXUS Inventory - Barcode & Scanning Module
Barcode generation, scanning, and tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum


class BarcodeFormat(Enum):
    UPC_A = "upc_a"
    EAN_13 = "ean_13"
    CODE_128 = "code_128"
    QR_CODE = "qr_code"
    DATA_MATRIX = "data_matrix"


@dataclass
class Barcode:
    """Barcode record"""
    id: str
    code: str
    format: BarcodeFormat

    # Linked entity
    product_id: Optional[str] = None
    variant_id: Optional[str] = None
    location_id: Optional[str] = None

    # Image
    image_url: str = ""
    svg_data: str = ""

    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ScanEvent:
    """Barcode scan event"""
    id: str
    barcode_id: str
    barcode_value: str

    # Context
    scanned_by: str = ""
    location: str = ""
    device_id: str = ""
    scan_type: str = "manual"  # "manual", "auto", "batch"

    # Action
    action: str = ""  # "receive", "pick", "ship", "count", "lookup"

    # Metadata
    metadata: Dict[str, str] = field(default_factory=dict)

    created_at: datetime = field(default_factory=datetime.now)


class BarcodeManager:
    """Barcode management"""

    def __init__(self):
        self.barcodes: Dict[str, Barcode] = {}
        self.scan_events: List[ScanEvent] = []

    def generate_barcode(
        self,
        code: str,
        format: BarcodeFormat,
        product_id: Optional[str] = None,
        **kwargs
    ) -> Barcode:
        """Generate barcode"""
        import uuid

        barcode = Barcode(
            id=str(uuid.uuid4()),
            code=code,
            format=format,
            product_id=product_id,
            **kwargs
        )

        # Generate image URL (would use actual barcode library)
        barcode.image_url = f"https://api.nexus.com/barcode/{barcode.id}.png"

        self.barcodes[barcode.id] = barcode
        return barcode

    def scan_barcode(
        self,
        barcode_value: str,
        scanned_by: str,
        action: str,
        **kwargs
    ) -> Optional[ScanEvent]:
        """Record barcode scan"""
        # Find barcode
        barcode = None
        for b in self.barcodes.values():
            if b.code == barcode_value:
                barcode = b
                break

        if not barcode:
            return None

        import uuid
        event = ScanEvent(
            id=str(uuid.uuid4()),
            barcode_id=barcode.id,
            barcode_value=barcode_value,
            scanned_by=scanned_by,
            action=action,
            **kwargs
        )

        self.scan_events.append(event)
        return event

    def lookup_barcode(self, barcode_value: str) -> Optional[Barcode]:
        """Lookup barcode"""
        for barcode in self.barcodes.values():
            if barcode.code == barcode_value:
                return barcode
        return None

    def get_product_barcodes(self, product_id: str) -> List[Barcode]:
        """Get all barcodes for product"""
        return [b for b in self.barcodes.values() if b.product_id == product_id]

    def get_scan_history(
        self,
        barcode_id: str,
        limit: int = 100
    ) -> List[ScanEvent]:
        """Get scan history for barcode"""
        events = [e for e in self.scan_events if e.barcode_id == barcode_id]
        return sorted(events, key=lambda e: e.created_at, reverse=True)[:limit]


if __name__ == "__main__":
    manager = BarcodeManager()

    # Generate barcode
    barcode = manager.generate_barcode(
        "123456789012",
        BarcodeFormat.UPC_A,
        product_id="product_001"
    )

    # Scan barcode
    scan = manager.scan_barcode(
        "123456789012",
        scanned_by="user_001",
        action="receive",
        location="warehouse_001"
    )

    # Lookup
    found = manager.lookup_barcode("123456789012")

    print(f"Barcode: {barcode.code}")
    print(f"Format: {barcode.format.value}")
    print(f"Scans: {len(manager.get_scan_history(barcode.id))}")
