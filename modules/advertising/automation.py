"""Automated rules and optimization."""

from typing import Dict, Any, List
from sqlalchemy.orm import Session

from .models import Campaign
from .optimization import CampaignOptimizer
from config.logging_config import get_logger

logger = get_logger(__name__)


class AutomationRules:
    """Automated rules engine."""

    def __init__(self, db: Session):
        self.db = db
        self.optimizer = CampaignOptimizer(db)

    async def apply_rules(self) -> List[Dict[str, Any]]:
        """Apply all automated rules."""
        results = []

        # Rule: Auto-pause high CPA campaigns
        paused = await self.optimizer.auto_pause_underperforming(threshold_cpa=100.0)
        if paused:
            results.append({
                "rule": "auto_pause_high_cpa",
                "campaigns_affected": len(paused),
                "campaign_ids": paused,
            })

        # Rule: Alert low budget campaigns
        from .budgets import BudgetManager
        budget_mgr = BudgetManager(self.db)
        alerts = await budget_mgr.check_budget_alerts()
        if alerts:
            results.append({
                "rule": "budget_alerts",
                "alerts": alerts,
            })

        return results

    async def schedule_optimization(self) -> bool:
        """Schedule automated optimization tasks."""
        logger.info("Running scheduled optimization")
        results = await self.apply_rules()
        logger.info(f"Automation results: {results}")
        return True
