"""
Funnel Analysis Engine

Funnel analysis and conversion tracking.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from modules.analytics.models.funnel import FunnelAnalysis, FunnelStepStats
from modules.analytics.storage.database import Database
from modules.analytics.storage.models import EventORM, FunnelORM, FunnelStepORM
from modules.analytics.storage.repositories import FunnelRepository
from shared.utils import safe_divide

logger = logging.getLogger(__name__)


class FunnelEngine:
    """Funnel analysis engine."""

    def __init__(self, db: Database):
        """Initialize funnel engine."""
        self.db = db
        self.repository = FunnelRepository()
        logger.info("Funnel engine initialized")

    def analyze_funnel(
        self,
        funnel_id: str,
        start_date: datetime,
        end_date: datetime,
        user_segment: Optional[str] = None,
    ) -> Optional[FunnelAnalysis]:
        """
        Analyze funnel conversion rates.

        Args:
            funnel_id: Funnel ID
            start_date: Analysis start date
            end_date: Analysis end date
            user_segment: Optional user segment filter

        Returns:
            Funnel analysis results
        """
        try:
            with self.db.session() as session:
                funnel = self.repository.get_by_id(session, funnel_id)
                if not funnel or not funnel.steps:
                    logger.error(f"Funnel not found: {funnel_id}")
                    return None

                # Sort steps by order
                sorted_steps = sorted(funnel.steps, key=lambda s: s.order)

                # Get users who entered the funnel
                first_step = sorted_steps[0]
                entered_users = self._get_step_users(
                    session,
                    first_step.event_type,
                    start_date,
                    end_date
                )

                total_entered = len(entered_users)
                if total_entered == 0:
                    return FunnelAnalysis(
                        funnel_id=funnel_id,
                        funnel_name=funnel.name,
                        start_date=start_date,
                        end_date=end_date,
                        total_entered=0,
                        total_completed=0,
                        overall_conversion_rate=0.0,
                        steps=[]
                    )

                # Analyze each step
                step_stats = []
                current_users = entered_users

                for step in sorted_steps:
                    step_data = self._analyze_step(
                        session,
                        step,
                        current_users,
                        start_date,
                        end_date
                    )
                    step_stats.append(step_data)

                    # Update current users for next step
                    current_users = self._get_step_completers(
                        session,
                        step.event_type,
                        current_users,
                        start_date,
                        end_date
                    )

                # Calculate overall conversion
                final_completers = len(current_users)
                conversion_rate = safe_divide(final_completers, total_entered) * 100

                return FunnelAnalysis(
                    funnel_id=funnel_id,
                    funnel_name=funnel.name,
                    start_date=start_date,
                    end_date=end_date,
                    total_entered=total_entered,
                    total_completed=final_completers,
                    overall_conversion_rate=round(conversion_rate, 2),
                    steps=step_stats
                )

        except Exception as e:
            logger.error(f"Error analyzing funnel: {e}", exc_info=True)
            return None

    def _get_step_users(
        self,
        session: Session,
        event_type: str,
        start_date: datetime,
        end_date: datetime
    ) -> set:
        """Get unique users for a funnel step."""
        users = session.query(EventORM.user_id).filter(
            and_(
                EventORM.event_type == event_type,
                EventORM.timestamp >= start_date,
                EventORM.timestamp <= end_date,
                EventORM.user_id.isnot(None)
            )
        ).distinct().all()

        return {u.user_id for u in users}

    def _get_step_completers(
        self,
        session: Session,
        event_type: str,
        users: set,
        start_date: datetime,
        end_date: datetime
    ) -> set:
        """Get users who completed a step."""
        if not users:
            return set()

        completers = session.query(EventORM.user_id).filter(
            and_(
                EventORM.event_type == event_type,
                EventORM.user_id.in_(users),
                EventORM.timestamp >= start_date,
                EventORM.timestamp <= end_date
            )
        ).distinct().all()

        return {u.user_id for u in completers}

    def _analyze_step(
        self,
        session: Session,
        step: FunnelStepORM,
        entered_users: set,
        start_date: datetime,
        end_date: datetime
    ) -> FunnelStepStats:
        """Analyze a single funnel step."""
        entered = len(entered_users)

        # Get completers
        completers = self._get_step_completers(
            session,
            step.event_type,
            entered_users,
            start_date,
            end_date
        )
        completed = len(completers)
        dropped = entered - completed

        # Calculate rates
        completion_rate = safe_divide(completed, entered) * 100
        drop_off_rate = safe_divide(dropped, entered) * 100

        return FunnelStepStats(
            step_id=step.id,
            step_name=step.name,
            order=step.order,
            entered=entered,
            completed=completed,
            dropped=dropped,
            completion_rate=round(completion_rate, 2),
            drop_off_rate=round(drop_off_rate, 2)
        )
