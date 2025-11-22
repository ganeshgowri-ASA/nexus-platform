"""Budget management and pacing."""

from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from .models import Campaign, BudgetTracking
from shared.utils import generate_uuid
from config.logging_config import get_logger

logger = get_logger(__name__)


class BudgetManager:
    """Budget management service."""

    def __init__(self, db: Session):
        self.db = db

    async def create_budget_tracker(self, campaign_id: str) -> BudgetTracking:
        """Create budget tracker for campaign."""
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            return None

        tracker = BudgetTracking(
            id=generate_uuid(),
            campaign_id=campaign_id,
            daily_budget=campaign.daily_budget,
            total_budget=campaign.total_budget,
            remaining=campaign.total_budget or campaign.daily_budget * 30,
        )

        self.db.add(tracker)
        self.db.commit()
        self.db.refresh(tracker)

        return tracker

    async def update_spend(
        self,
        campaign_id: str,
        amount: float,
    ) -> Dict[str, Any]:
        """Update campaign spend."""
        tracker = self.db.query(BudgetTracking).filter(
            BudgetTracking.campaign_id == campaign_id
        ).first()

        if tracker:
            tracker.spent_today += amount
            tracker.spent_total += amount
            tracker.remaining = (tracker.total_budget or 0) - tracker.spent_total
            self.db.commit()

            # Check budget alerts
            if tracker.remaining < tracker.daily_budget:
                logger.warning(f"Budget alert: Campaign {campaign_id} running low")

            return {
                "spent_today": tracker.spent_today,
                "spent_total": tracker.spent_total,
                "remaining": tracker.remaining,
            }

        return {}

    async def check_budget_alerts(self) -> List[Dict[str, Any]]:
        """Check for budget alerts across all campaigns."""
        alerts = []
        trackers = self.db.query(BudgetTracking).all()

        for tracker in trackers:
            if tracker.remaining < tracker.daily_budget * 2:
                alerts.append({
                    "campaign_id": tracker.campaign_id,
                    "remaining": tracker.remaining,
                    "severity": "high" if tracker.remaining < tracker.daily_budget else "medium",
                })

        return alerts
