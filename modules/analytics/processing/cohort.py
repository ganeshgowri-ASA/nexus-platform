"""
Cohort Analysis System

Cohort analysis and retention tracking.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from modules.analytics.models.cohort import CohortAnalysis, CohortRetention
from modules.analytics.storage.database import Database
from modules.analytics.storage.models import SessionORM, UserORM
from modules.analytics.storage.repositories import CohortRepository
from shared.constants import AggregationPeriod, CohortType
from shared.utils import safe_divide

logger = logging.getLogger(__name__)


class CohortEngine:
    """Cohort analysis engine."""

    def __init__(self, db: Database):
        """Initialize cohort engine."""
        self.db = db
        self.repository = CohortRepository()
        logger.info("Cohort engine initialized")

    def analyze_retention_cohort(
        self,
        cohort_date: datetime,
        periods: int = 12,
        period_type: AggregationPeriod = AggregationPeriod.WEEK
    ) -> Optional[CohortAnalysis]:
        """
        Analyze retention for a date-based cohort.

        Args:
            cohort_date: Cohort starting date
            periods: Number of periods to analyze
            period_type: Period type (day, week, month)

        Returns:
            Cohort analysis results
        """
        try:
            with self.db.session() as session:
                # Get cohort users
                cohort_users = self._get_cohort_users(
                    session,
                    cohort_date,
                    period_type
                )

                if not cohort_users:
                    return None

                initial_count = len(cohort_users)

                # Calculate retention for each period
                retention_data = []

                for period in range(periods):
                    period_start, period_end = self._get_period_range(
                        cohort_date,
                        period,
                        period_type
                    )

                    active_users = self._get_active_users(
                        session,
                        cohort_users,
                        period_start,
                        period_end
                    )

                    retention_rate = safe_divide(active_users, initial_count) * 100

                    # Calculate cumulative retention
                    if period == 0:
                        cumulative_retention = 100.0
                    else:
                        cumulative_retention = retention_rate

                    retention_data.append(
                        CohortRetention(
                            period=period,
                            users_active=active_users,
                            retention_rate=round(retention_rate, 2),
                            cumulative_retention=round(cumulative_retention, 2)
                        )
                    )

                # Calculate average retention
                avg_retention = sum(r.retention_rate for r in retention_data) / len(retention_data)
                churn_rate = 100 - avg_retention

                return CohortAnalysis(
                    cohort_id="",
                    cohort_name=f"Cohort {cohort_date.date()}",
                    cohort_date=cohort_date,
                    initial_users=initial_count,
                    retention_data=retention_data,
                    avg_retention_rate=round(avg_retention, 2),
                    churn_rate=round(churn_rate, 2)
                )

        except Exception as e:
            logger.error(f"Error analyzing retention cohort: {e}", exc_info=True)
            return None

    def _get_cohort_users(
        self,
        session: Session,
        cohort_date: datetime,
        period_type: AggregationPeriod
    ) -> set:
        """Get users in cohort."""
        period_start, period_end = self._get_period_range(
            cohort_date,
            0,
            period_type
        )

        users = session.query(UserORM.id).filter(
            and_(
                UserORM.first_seen_at >= period_start,
                UserORM.first_seen_at < period_end
            )
        ).all()

        return {u.id for u in users}

    def _get_active_users(
        self,
        session: Session,
        cohort_users: set,
        period_start: datetime,
        period_end: datetime
    ) -> int:
        """Get number of active users in period."""
        if not cohort_users:
            return 0

        count = session.query(
            func.count(func.distinct(SessionORM.user_id))
        ).filter(
            and_(
                SessionORM.user_id.in_(cohort_users),
                SessionORM.started_at >= period_start,
                SessionORM.started_at < period_end
            )
        ).scalar()

        return count or 0

    def _get_period_range(
        self,
        cohort_date: datetime,
        period: int,
        period_type: AggregationPeriod
    ) -> tuple:
        """Get start and end dates for a period."""
        if period_type == AggregationPeriod.DAY:
            delta = timedelta(days=1)
        elif period_type == AggregationPeriod.WEEK:
            delta = timedelta(weeks=1)
        elif period_type == AggregationPeriod.MONTH:
            delta = timedelta(days=30)
        else:
            delta = timedelta(days=1)

        period_start = cohort_date + (delta * period)
        period_end = period_start + delta

        return period_start, period_end
