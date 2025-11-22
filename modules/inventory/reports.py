"""
NEXUS Inventory - Reports Module
Inventory reports, analytics, and insights.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum


class ReportType(Enum):
    STOCK_LEVELS = "stock_levels"
    LOW_STOCK = "low_stock"
    STOCK_MOVEMENT = "stock_movement"
    VALUATION = "valuation"
    DEAD_STOCK = "dead_stock"
    ABC_ANALYSIS = "abc_analysis"
    REORDER_REPORT = "reorder_report"


@dataclass
class InventoryReport:
    """Inventory report"""
    id: str
    report_type: ReportType
    title: str

    # Data
    data: List[Dict[str, Any]] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    # Filters
    warehouse_id: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

    # Metadata
    generated_at: datetime = field(default_factory=datetime.now)
    generated_by: str = ""


@dataclass
class StockMovementRecord:
    """Stock movement for reporting"""
    product_id: str
    sku: str
    name: str
    opening_stock: int
    received: int
    sold: int
    adjusted: int
    transferred: int
    closing_stock: int
    variance: int


class ReportManager:
    """Report generation"""

    def __init__(self):
        self.reports: Dict[str, InventoryReport] = {}

    def generate_stock_levels_report(
        self,
        warehouse_id: Optional[str] = None
    ) -> InventoryReport:
        """Generate current stock levels report"""
        import uuid

        # Mock data - would query actual stock items
        data = [
            {
                "sku": "SKU-001",
                "name": "Product A",
                "warehouse": "WH-001",
                "quantity": 150,
                "reserved": 20,
                "available": 130,
                "reorder_point": 50,
                "status": "in_stock"
            }
        ]

        summary = {
            "total_products": len(data),
            "total_quantity": sum(item["quantity"] for item in data),
            "low_stock_count": 0
        }

        report = InventoryReport(
            id=str(uuid.uuid4()),
            report_type=ReportType.STOCK_LEVELS,
            title="Stock Levels Report",
            data=data,
            summary=summary,
            warehouse_id=warehouse_id
        )

        self.reports[report.id] = report
        return report

    def generate_low_stock_report(self) -> InventoryReport:
        """Generate low stock report"""
        import uuid

        data = [
            {
                "sku": "SKU-002",
                "name": "Product B",
                "current_stock": 15,
                "reorder_point": 50,
                "suggested_order": 100
            }
        ]

        summary = {
            "items_below_reorder": len(data),
            "total_value_at_risk": 0.0
        }

        report = InventoryReport(
            id=str(uuid.uuid4()),
            report_type=ReportType.LOW_STOCK,
            title="Low Stock Alert Report",
            data=data,
            summary=summary
        )

        self.reports[report.id] = report
        return report

    def generate_movement_report(
        self,
        date_from: datetime,
        date_to: datetime
    ) -> InventoryReport:
        """Generate stock movement report"""
        import uuid

        movements = [
            StockMovementRecord(
                product_id="prod_001",
                sku="SKU-001",
                name="Product A",
                opening_stock=100,
                received=50,
                sold=30,
                adjusted=-5,
                transferred=10,
                closing_stock=105,
                variance=5
            )
        ]

        data = [
            {
                "sku": m.sku,
                "name": m.name,
                "opening": m.opening_stock,
                "received": m.received,
                "sold": m.sold,
                "adjusted": m.adjusted,
                "transferred": m.transferred,
                "closing": m.closing_stock,
                "variance": m.variance
            }
            for m in movements
        ]

        summary = {
            "total_received": sum(m.received for m in movements),
            "total_sold": sum(m.sold for m in movements),
            "net_change": sum(m.variance for m in movements)
        }

        report = InventoryReport(
            id=str(uuid.uuid4()),
            report_type=ReportType.STOCK_MOVEMENT,
            title=f"Stock Movement Report ({date_from.date()} to {date_to.date()})",
            data=data,
            summary=summary,
            date_from=date_from,
            date_to=date_to
        )

        self.reports[report.id] = report
        return report

    def generate_valuation_report(
        self,
        cost_data: Dict[str, float]
    ) -> InventoryReport:
        """Generate inventory valuation report"""
        import uuid

        data = [
            {
                "sku": "SKU-001",
                "name": "Product A",
                "quantity": 150,
                "cost_per_unit": cost_data.get("SKU-001", 0.0),
                "total_value": 150 * cost_data.get("SKU-001", 0.0)
            }
        ]

        summary = {
            "total_units": sum(item["quantity"] for item in data),
            "total_value": sum(item["total_value"] for item in data)
        }

        report = InventoryReport(
            id=str(uuid.uuid4()),
            report_type=ReportType.VALUATION,
            title="Inventory Valuation Report",
            data=data,
            summary=summary
        )

        self.reports[report.id] = report
        return report

    def generate_abc_analysis(self) -> InventoryReport:
        """Generate ABC analysis (Pareto) report"""
        import uuid

        data = [
            {
                "sku": "SKU-001",
                "name": "Product A",
                "revenue": 50000,
                "percentage_of_total": 45.0,
                "category": "A"
            },
            {
                "sku": "SKU-002",
                "name": "Product B",
                "revenue": 30000,
                "percentage_of_total": 27.0,
                "category": "B"
            },
            {
                "sku": "SKU-003",
                "name": "Product C",
                "revenue": 10000,
                "percentage_of_total": 9.0,
                "category": "C"
            }
        ]

        summary = {
            "a_items": 1,
            "b_items": 1,
            "c_items": 1,
            "total_revenue": 90000
        }

        report = InventoryReport(
            id=str(uuid.uuid4()),
            report_type=ReportType.ABC_ANALYSIS,
            title="ABC Analysis Report",
            data=data,
            summary=summary
        )

        self.reports[report.id] = report
        return report

    def export_report(self, report_id: str, format: str = "csv") -> str:
        """Export report to file"""
        report = self.reports.get(report_id)
        if not report:
            return ""

        # Would generate actual file
        return f"/reports/{report_id}.{format}"


if __name__ == "__main__":
    manager = ReportManager()

    # Generate reports
    stock_report = manager.generate_stock_levels_report()
    low_stock = manager.generate_low_stock_report()
    movement = manager.generate_movement_report(
        datetime.now() - timedelta(days=30),
        datetime.now()
    )
    valuation = manager.generate_valuation_report({"SKU-001": 25.50})
    abc = manager.generate_abc_analysis()

    print(f"Stock Levels Report: {len(stock_report.data)} items")
    print(f"Low Stock Alerts: {len(low_stock.data)} items")
    print(f"Total Value: ${valuation.summary['total_value']:.2f}")
