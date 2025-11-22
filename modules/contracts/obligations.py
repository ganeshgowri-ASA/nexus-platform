"""Obligation management and tracking.

This module handles obligation extraction, deadline tracking,
responsibility assignment, and alerts.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

import structlog

from .contract_types import Obligation, ObligationStatus, ObligationType

logger = structlog.get_logger(__name__)


class ObligationManager:
    """Manages contractual obligations."""

    def __init__(self):
        """Initialize obligation manager."""
        self.obligations: Dict[UUID, Obligation] = {}

    def create_obligation(
        self,
        contract_id: UUID,
        title: str,
        description: str,
        obligation_type: ObligationType,
        responsible_party: UUID,
        due_date: Optional[datetime] = None,
        **kwargs
    ) -> Obligation:
        """Create a new obligation.

        Args:
            contract_id: Contract ID
            title: Obligation title
            description: Obligation description
            obligation_type: Type of obligation
            responsible_party: Responsible party ID
            due_date: Optional due date
            **kwargs: Additional obligation fields

        Returns:
            Created obligation
        """
        logger.info("Creating obligation", title=title, contract_id=contract_id)

        obligation = Obligation(
            contract_id=contract_id,
            title=title,
            description=description,
            obligation_type=obligation_type,
            responsible_party=responsible_party,
            due_date=due_date,
            **kwargs
        )

        self.obligations[obligation.id] = obligation
        return obligation

    def update_status(
        self,
        obligation_id: UUID,
        status: ObligationStatus,
    ) -> Obligation:
        """Update obligation status.

        Args:
            obligation_id: Obligation ID
            status: New status

        Returns:
            Updated obligation
        """
        logger.info("Updating obligation status", obligation_id=obligation_id, status=status)

        obligation = self.obligations[obligation_id]
        obligation.status = status
        obligation.updated_at = datetime.utcnow()

        if status == ObligationStatus.COMPLETED:
            obligation.completed_date = datetime.utcnow()

        return obligation

    def complete_obligation(
        self,
        obligation_id: UUID,
    ) -> Obligation:
        """Mark obligation as completed.

        Args:
            obligation_id: Obligation ID

        Returns:
            Completed obligation
        """
        return self.update_status(obligation_id, ObligationStatus.COMPLETED)

    def get_by_contract(
        self,
        contract_id: UUID,
        status: Optional[ObligationStatus] = None,
    ) -> List[Obligation]:
        """Get obligations for a contract.

        Args:
            contract_id: Contract ID
            status: Optional status filter

        Returns:
            List of obligations
        """
        obligations = [
            o for o in self.obligations.values()
            if o.contract_id == contract_id
        ]

        if status:
            obligations = [o for o in obligations if o.status == status]

        return sorted(obligations, key=lambda o: o.due_date or datetime.max)

    def get_by_party(
        self,
        party_id: UUID,
        status: Optional[ObligationStatus] = None,
    ) -> List[Obligation]:
        """Get obligations for a party.

        Args:
            party_id: Party ID
            status: Optional status filter

        Returns:
            List of obligations
        """
        obligations = [
            o for o in self.obligations.values()
            if o.responsible_party == party_id
        ]

        if status:
            obligations = [o for o in obligations if o.status == status]

        return sorted(obligations, key=lambda o: o.due_date or datetime.max)

    def get_overdue(
        self,
        contract_id: Optional[UUID] = None,
    ) -> List[Obligation]:
        """Get overdue obligations.

        Args:
            contract_id: Optional contract ID filter

        Returns:
            List of overdue obligations
        """
        now = datetime.utcnow()
        overdue = []

        for obligation in self.obligations.values():
            if contract_id and obligation.contract_id != contract_id:
                continue

            if not obligation.due_date:
                continue

            if obligation.status in [ObligationStatus.COMPLETED, ObligationStatus.WAIVED]:
                continue

            if obligation.due_date < now:
                obligation.status = ObligationStatus.OVERDUE
                overdue.append(obligation)

        return sorted(overdue, key=lambda o: o.due_date)

    def get_upcoming(
        self,
        days: int = 7,
        contract_id: Optional[UUID] = None,
    ) -> List[Obligation]:
        """Get upcoming obligations within specified days.

        Args:
            days: Number of days to look ahead
            contract_id: Optional contract ID filter

        Returns:
            List of upcoming obligations
        """
        now = datetime.utcnow()
        threshold = now + timedelta(days=days)
        upcoming = []

        for obligation in self.obligations.values():
            if contract_id and obligation.contract_id != contract_id:
                continue

            if not obligation.due_date:
                continue

            if obligation.status in [ObligationStatus.COMPLETED, ObligationStatus.WAIVED]:
                continue

            if now <= obligation.due_date <= threshold:
                upcoming.append(obligation)

        return sorted(upcoming, key=lambda o: o.due_date)

    def extract_obligations(
        self,
        contract_id: UUID,
        contract_text: str,
    ) -> List[Obligation]:
        """Extract obligations from contract text using AI.

        Args:
            contract_id: Contract ID
            contract_text: Contract text

        Returns:
            List of extracted obligations
        """
        logger.info("Extracting obligations from contract", contract_id=contract_id)

        # In production, would use AI/NLP to extract obligations
        # For now, return empty list
        extracted = []

        # Placeholder: could use patterns to detect obligations
        keywords = ["shall", "must", "will", "agrees to", "obligated to"]

        # This is a simplified example
        # Real implementation would use NLP/LLM

        return extracted

    def assign_to_party(
        self,
        obligation_id: UUID,
        party_id: UUID,
    ) -> Obligation:
        """Assign obligation to a party.

        Args:
            obligation_id: Obligation ID
            party_id: Party ID

        Returns:
            Updated obligation
        """
        logger.info("Assigning obligation", obligation_id=obligation_id, party_id=party_id)

        obligation = self.obligations[obligation_id]
        obligation.responsible_party = party_id
        obligation.updated_at = datetime.utcnow()

        return obligation

    def set_alert(
        self,
        obligation_id: UUID,
        days_before: int = 7,
        enabled: bool = True,
    ) -> Obligation:
        """Set alert for obligation.

        Args:
            obligation_id: Obligation ID
            days_before: Days before due date to alert
            enabled: Whether alert is enabled

        Returns:
            Updated obligation
        """
        logger.info("Setting obligation alert", obligation_id=obligation_id, days_before=days_before)

        obligation = self.obligations[obligation_id]
        obligation.alerts_enabled = enabled
        obligation.alert_days_before = days_before
        obligation.updated_at = datetime.utcnow()

        return obligation

    def check_dependencies(
        self,
        obligation_id: UUID,
    ) -> Dict[str, bool]:
        """Check if obligation dependencies are met.

        Args:
            obligation_id: Obligation ID

        Returns:
            Dictionary of dependency statuses
        """
        obligation = self.obligations[obligation_id]
        dependencies_met = {}

        for dep_id in obligation.dependencies:
            if dep_id in self.obligations:
                dep = self.obligations[dep_id]
                dependencies_met[str(dep_id)] = dep.status == ObligationStatus.COMPLETED
            else:
                dependencies_met[str(dep_id)] = False

        return dependencies_met

    def can_start(self, obligation_id: UUID) -> bool:
        """Check if obligation can be started (all dependencies met).

        Args:
            obligation_id: Obligation ID

        Returns:
            True if all dependencies are met
        """
        dependencies = self.check_dependencies(obligation_id)
        return all(dependencies.values()) if dependencies else True
