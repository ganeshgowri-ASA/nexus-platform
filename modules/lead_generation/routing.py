"""Lead routing system for automatic assignment."""

from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from .models import Lead as LeadModel
from config.logging_config import get_logger

logger = get_logger(__name__)


class LeadRouter:
    """Lead routing service for automatic assignment to sales reps."""

    def __init__(self, db: Session):
        self.db = db
        self.current_round_robin_index = 0

    async def route_lead(
        self,
        lead_id: str,
        strategy: str = "round_robin",
        criteria: Optional[dict] = None,
    ) -> str:
        """Route lead to appropriate sales rep."""
        lead = self.db.query(LeadModel).filter(LeadModel.id == lead_id).first()
        if not lead:
            return None

        if strategy == "round_robin":
            assigned_to = await self._round_robin_routing()
        elif strategy == "territory":
            assigned_to = await self._territory_based_routing(lead, criteria or {})
        elif strategy == "skill":
            assigned_to = await self._skill_based_routing(lead, criteria or {})
        elif strategy == "load_balance":
            assigned_to = await self._load_balance_routing()
        else:
            assigned_to = await self._round_robin_routing()

        if assigned_to:
            lead.assigned_to = assigned_to
            self.db.commit()
            logger.info(f"Lead {lead.email} assigned to {assigned_to}")

        return assigned_to

    async def _round_robin_routing(self) -> str:
        """Simple round-robin assignment."""
        # In production, maintain list of available reps
        sales_reps = ["rep1", "rep2", "rep3", "rep4"]
        assigned = sales_reps[self.current_round_robin_index % len(sales_reps)]
        self.current_round_robin_index += 1
        return assigned

    async def _territory_based_routing(self, lead: LeadModel, criteria: dict) -> str:
        """Route based on geographic territory."""
        territory_map = criteria.get("territories", {})
        
        if lead.country in territory_map:
            return territory_map[lead.country]
        elif lead.state in territory_map:
            return territory_map[lead.state]
        
        return await self._round_robin_routing()

    async def _skill_based_routing(self, lead: LeadModel, criteria: dict) -> str:
        """Route based on required skills (industry, company size, etc.)."""
        skill_map = criteria.get("skills", {})
        
        if lead.industry in skill_map:
            return skill_map[lead.industry]
        
        return await self._round_robin_routing()

    async def _load_balance_routing(self) -> str:
        """Route to rep with lowest current lead count."""
        # Count leads per rep
        from sqlalchemy import func
        lead_counts = self.db.query(
            LeadModel.assigned_to,
            func.count(LeadModel.id).label("count")
        ).filter(
            LeadModel.status.in_(["new", "contacted"])
        ).group_by(LeadModel.assigned_to).all()

        if not lead_counts:
            return await self._round_robin_routing()

        # Find rep with minimum leads
        min_rep = min(lead_counts, key=lambda x: x.count)
        return min_rep.assigned_to
