"""Contract reporting."""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID
import structlog

logger = structlog.get_logger(__name__)


class ReportGenerator:
    """Generates contract reports."""

    def __init__(self):
        """Initialize report generator."""
        pass

    def generate_contract_register(self, contracts: List) -> Dict:
        """Generate contract register report."""
        logger.info("Generating contract register", count=len(contracts))

        return {
            "title": "Contract Register",
            "generated_at": datetime.utcnow().isoformat(),
            "total_contracts": len(contracts),
            "contracts": [
                {
                    "id": str(c.id),
                    "title": c.title,
                    "type": c.contract_type.value,
                    "status": c.status.value,
                    "start_date": c.start_date.isoformat() if c.start_date else None,
                    "end_date": c.end_date.isoformat() if c.end_date else None,
                    "value": float(c.total_value) if c.total_value else 0,
                }
                for c in contracts
            ],
        }

    def generate_obligation_report(self, obligations: List) -> Dict:
        """Generate obligations report."""
        logger.info("Generating obligations report", count=len(obligations))

        return {
            "title": "Obligations Report",
            "generated_at": datetime.utcnow().isoformat(),
            "total_obligations": len(obligations),
            "pending": sum(1 for o in obligations if o.status.value == "pending"),
            "completed": sum(1 for o in obligations if o.status.value == "completed"),
            "overdue": sum(1 for o in obligations if o.status.value == "overdue"),
        }

    def generate_value_report(self, contracts: List) -> Dict:
        """Generate contract value report."""
        logger.info("Generating value report")

        total_value = sum(float(c.total_value or 0) for c in contracts)

        by_type = {}
        for contract in contracts:
            contract_type = contract.contract_type.value
            value = float(contract.total_value or 0)
            by_type[contract_type] = by_type.get(contract_type, 0) + value

        return {
            "title": "Contract Value Report",
            "generated_at": datetime.utcnow().isoformat(),
            "total_value": total_value,
            "value_by_type": by_type,
        }
