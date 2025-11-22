"""
NEXUS E-commerce - Shipping Module
Handles shipping rates, zones, carriers, and label generation.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum


class ShippingCarrier(Enum):
    UPS = "ups"
    FEDEX = "fedex"
    USPS = "usps"
    DHL = "dhl"


@dataclass
class ShippingZone:
    """Shipping zone"""
    id: str
    name: str
    countries: List[str] = field(default_factory=list)
    states: List[str] = field(default_factory=list)


@dataclass
class ShippingRate:
    """Shipping rate"""
    id: str
    name: str
    carrier: ShippingCarrier
    zone_id: str

    # Pricing
    base_rate: float = 0.0
    per_kg_rate: float = 0.0
    min_order_free_shipping: Optional[float] = None

    # Delivery
    min_days: int = 3
    max_days: int = 7

    is_active: bool = True


@dataclass
class Shipment:
    """Shipment record"""
    id: str
    order_id: str
    carrier: ShippingCarrier

    # Tracking
    tracking_number: str = ""
    tracking_url: str = ""

    # Package
    weight_kg: float = 0.0
    dimensions: Dict[str, float] = field(default_factory=dict)

    # Status
    status: str = "pending"
    shipped_at: Optional[datetime] = None
    estimated_delivery: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

    created_at: datetime = field(default_factory=datetime.now)


class ShippingManager:
    """Shipping management"""

    def __init__(self):
        self.zones: Dict[str, ShippingZone] = {}
        self.rates: Dict[str, ShippingRate] = {}
        self.shipments: Dict[str, Shipment] = {}

    def create_zone(self, name: str, countries: List[str], **kwargs) -> ShippingZone:
        """Create shipping zone"""
        import uuid
        zone = ShippingZone(
            id=str(uuid.uuid4()),
            name=name,
            countries=countries,
            **kwargs
        )
        self.zones[zone.id] = zone
        return zone

    def create_rate(
        self,
        name: str,
        carrier: ShippingCarrier,
        zone_id: str,
        base_rate: float,
        **kwargs
    ) -> ShippingRate:
        """Create shipping rate"""
        import uuid
        rate = ShippingRate(
            id=str(uuid.uuid4()),
            name=name,
            carrier=carrier,
            zone_id=zone_id,
            base_rate=base_rate,
            **kwargs
        )
        self.rates[rate.id] = rate
        return rate

    def calculate_rate(
        self,
        zone_id: str,
        weight_kg: float,
        order_total: float
    ) -> List[Dict]:
        """Calculate shipping rates"""
        available_rates = []

        for rate in self.rates.values():
            if rate.zone_id == zone_id and rate.is_active:
                # Check for free shipping
                if rate.min_order_free_shipping and order_total >= rate.min_order_free_shipping:
                    cost = 0.0
                else:
                    cost = rate.base_rate + (weight_kg * rate.per_kg_rate)

                available_rates.append({
                    "id": rate.id,
                    "name": rate.name,
                    "carrier": rate.carrier.value,
                    "cost": cost,
                    "delivery_days": f"{rate.min_days}-{rate.max_days}"
                })

        return available_rates

    def create_shipment(
        self,
        order_id: str,
        carrier: ShippingCarrier,
        weight_kg: float,
        **kwargs
    ) -> Shipment:
        """Create shipment"""
        import uuid
        import random

        shipment = Shipment(
            id=str(uuid.uuid4()),
            order_id=order_id,
            carrier=carrier,
            weight_kg=weight_kg,
            tracking_number=f"{carrier.value.upper()}{random.randint(100000, 999999)}",
            **kwargs
        )

        shipment.tracking_url = f"https://track.{carrier.value}.com/{shipment.tracking_number}"
        shipment.estimated_delivery = datetime.now() + timedelta(days=5)

        self.shipments[shipment.id] = shipment
        return shipment

    def ship(self, shipment_id: str) -> bool:
        """Mark shipment as shipped"""
        shipment = self.shipments.get(shipment_id)
        if not shipment:
            return False

        shipment.status = "shipped"
        shipment.shipped_at = datetime.now()
        return True


if __name__ == "__main__":
    manager = ShippingManager()

    zone = manager.create_zone("USA", ["US"])

    rate = manager.create_rate(
        "Standard Shipping",
        ShippingCarrier.USPS,
        zone.id,
        base_rate=5.99,
        per_kg_rate=1.50,
        min_order_free_shipping=50.0
    )

    rates = manager.calculate_rate(zone.id, weight_kg=2.5, order_total=100.0)
    print(f"Shipping options: {len(rates)}")

    shipment = manager.create_shipment("order_001", ShippingCarrier.USPS, 2.5)
    manager.ship(shipment.id)
    print(f"Tracking: {shipment.tracking_number}")
