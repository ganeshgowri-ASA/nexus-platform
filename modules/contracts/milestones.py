"""Milestone tracking and management.

This module handles milestone definition, progress tracking,
payment triggers, and deliverable verification.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

import structlog

from .contract_types import Milestone, MilestoneStatus

logger = structlog.get_logger(__name__)


class MilestoneManager:
    """Manages contract milestones."""

    def __init__(self):
        """Initialize milestone manager."""
        self.milestones: dict[UUID, Milestone] = {}

    def create_milestone(
        self,
        contract_id: UUID,
        title: str,
        due_date: Optional[datetime] = None,
        payment_trigger: bool = False,
        **kwargs
    ) -> Milestone:
        """Create a new milestone.

        Args:
            contract_id: Contract ID
            title: Milestone title
            due_date: Optional due date
            payment_trigger: Whether milestone triggers payment
            **kwargs: Additional milestone fields

        Returns:
            Created milestone
        """
        logger.info("Creating milestone", title=title, contract_id=contract_id)

        milestone = Milestone(
            contract_id=contract_id,
            title=title,
            due_date=due_date,
            payment_trigger=payment_trigger,
            **kwargs
        )

        self.milestones[milestone.id] = milestone
        return milestone

    def update_progress(
        self,
        milestone_id: UUID,
        progress_percentage: int,
    ) -> Milestone:
        """Update milestone progress.

        Args:
            milestone_id: Milestone ID
            progress_percentage: Progress percentage (0-100)

        Returns:
            Updated milestone
        """
        logger.info("Updating milestone progress", milestone_id=milestone_id, progress=progress_percentage)

        milestone = self.milestones[milestone_id]
        milestone.progress_percentage = max(0, min(100, progress_percentage))
        milestone.updated_at = datetime.utcnow()

        if milestone.progress_percentage == 100 and milestone.status != MilestoneStatus.COMPLETED:
            milestone.status = MilestoneStatus.COMPLETED
            milestone.completed_date = datetime.utcnow()

        return milestone

    def complete_milestone(
        self,
        milestone_id: UUID,
    ) -> Milestone:
        """Mark milestone as completed.

        Args:
            milestone_id: Milestone ID

        Returns:
            Completed milestone
        """
        logger.info("Completing milestone", milestone_id=milestone_id)

        milestone = self.milestones[milestone_id]
        milestone.status = MilestoneStatus.COMPLETED
        milestone.progress_percentage = 100
        milestone.completed_date = datetime.utcnow()
        milestone.updated_at = datetime.utcnow()

        return milestone

    def get_by_contract(
        self,
        contract_id: UUID,
        status: Optional[MilestoneStatus] = None,
    ) -> List[Milestone]:
        """Get milestones for a contract.

        Args:
            contract_id: Contract ID
            status: Optional status filter

        Returns:
            List of milestones
        """
        milestones = [
            m for m in self.milestones.values()
            if m.contract_id == contract_id
        ]

        if status:
            milestones = [m for m in milestones if m.status == status]

        return sorted(milestones, key=lambda m: m.due_date or datetime.max)

    def get_payment_milestones(
        self,
        contract_id: UUID,
        completed_only: bool = True,
    ) -> List[Milestone]:
        """Get payment-triggering milestones.

        Args:
            contract_id: Contract ID
            completed_only: Only return completed milestones

        Returns:
            List of payment milestones
        """
        milestones = [
            m for m in self.milestones.values()
            if m.contract_id == contract_id and m.payment_trigger
        ]

        if completed_only:
            milestones = [m for m in milestones if m.status == MilestoneStatus.COMPLETED]

        return sorted(milestones, key=lambda m: m.completed_date or datetime.max)
