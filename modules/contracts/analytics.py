"""Contract analytics and reporting.

This module provides analytics for cycle time, bottleneck detection,
approval metrics, value analysis, and risk metrics.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID
import structlog

from .contract_types import Contract, ContractStatus

logger = structlog.get_logger(__name__)


class ContractAnalytics:
    """Analytics engine for contracts."""

    def __init__(self):
        """Initialize analytics engine."""
        self.contracts: Dict[UUID, Contract] = {}

    def add_contract(self, contract: Contract) -> None:
        """Add contract to analytics."""
        self.contracts[contract.id] = contract

    def calculate_cycle_time(
        self,
        contract_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict:
        """Calculate average contract cycle time.

        Args:
            contract_id: Optional specific contract
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Cycle time statistics
        """
        logger.info("Calculating cycle time")

        contracts = list(self.contracts.values())
        if contract_id:
            contracts = [c for c in contracts if c.id == contract_id]
        if start_date:
            contracts = [c for c in contracts if c.created_at >= start_date]
        if end_date:
            contracts = [c for c in contracts if c.created_at <= end_date]

        cycle_times = []
        for contract in contracts:
            if contract.execution_date:
                cycle_time = (contract.execution_date - contract.created_at).days
                cycle_times.append(cycle_time)

        if not cycle_times:
            return {"average_days": 0, "min_days": 0, "max_days": 0}

        return {
            "average_days": sum(cycle_times) / len(cycle_times),
            "min_days": min(cycle_times),
            "max_days": max(cycle_times),
            "total_contracts": len(cycle_times),
        }

    def get_value_analysis(self) -> Dict:
        """Get contract value analysis.

        Returns:
            Value analysis statistics
        """
        logger.info("Generating value analysis")

        total_value = sum(
            c.total_value or 0 for c in self.contracts.values()
        )

        active_value = sum(
            c.total_value or 0 for c in self.contracts.values()
            if c.status == ContractStatus.ACTIVE
        )

        return {
            "total_value": total_value,
            "active_value": active_value,
            "total_contracts": len(self.contracts),
            "active_contracts": sum(1 for c in self.contracts.values() if c.status == ContractStatus.ACTIVE),
        }

    def get_risk_distribution(self) -> Dict:
        """Get risk level distribution.

        Returns:
            Risk distribution statistics
        """
        logger.info("Generating risk distribution")

        distribution = {
            "low": 0,
            "medium": 0,
            "high": 0,
            "critical": 0,
        }

        for contract in self.contracts.values():
            risk_level = contract.risk_level.value
            distribution[risk_level] += 1

        return distribution

    def get_status_breakdown(self) -> Dict[str, int]:
        """Get contract status breakdown.

        Returns:
            Dictionary of status counts
        """
        breakdown = {}
        for contract in self.contracts.values():
            status = contract.status.value
            breakdown[status] = breakdown.get(status, 0) + 1
        return breakdown
