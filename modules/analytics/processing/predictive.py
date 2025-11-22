"""
Predictive Analytics

ML-based predictive analytics for user behavior.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import numpy as np
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from modules.analytics.storage.database import Database
from modules.analytics.storage.models import EventORM, SessionORM, UserORM
from shared.utils import get_utc_now

logger = logging.getLogger(__name__)


class PredictiveEngine:
    """Predictive analytics engine."""

    def __init__(self, db: Database):
        """Initialize predictive engine."""
        self.db = db
        logger.info("Predictive engine initialized")

    def predict_churn(self, user_id: str) -> float:
        """
        Predict churn probability for a user.

        Args:
            user_id: User ID

        Returns:
            Churn probability (0-1)
        """
        try:
            with self.db.session() as session:
                user = session.query(UserORM).filter(UserORM.id == user_id).first()
                if not user:
                    return 0.0

                # Get user metrics
                days_since_last_seen = (get_utc_now() - user.last_seen_at).days
                avg_session_duration = self._get_avg_session_duration(session, user_id)
                session_frequency = self._get_session_frequency(session, user_id)
                engagement_trend = self._get_engagement_trend(session, user_id)

                # Simple scoring model (replace with trained ML model)
                churn_score = 0.0

                # Days inactive
                if days_since_last_seen > 30:
                    churn_score += 0.4
                elif days_since_last_seen > 14:
                    churn_score += 0.2
                elif days_since_last_seen > 7:
                    churn_score += 0.1

                # Session duration
                if avg_session_duration < 60:
                    churn_score += 0.2

                # Session frequency
                if session_frequency < 1:
                    churn_score += 0.2

                # Engagement trend
                if engagement_trend < -0.5:
                    churn_score += 0.2

                return min(churn_score, 1.0)

        except Exception as e:
            logger.error(f"Error predicting churn: {e}", exc_info=True)
            return 0.0

    def predict_ltv(self, user_id: str, months: int = 12) -> float:
        """
        Predict customer lifetime value.

        Args:
            user_id: User ID
            months: Prediction period in months

        Returns:
            Predicted LTV
        """
        try:
            with self.db.session() as session:
                user = session.query(UserORM).filter(UserORM.id == user_id).first()
                if not user:
                    return 0.0

                # Calculate average monthly value
                user_age_days = (get_utc_now() - user.first_seen_at).days
                if user_age_days == 0:
                    return 0.0

                avg_monthly_value = (user.lifetime_value / user_age_days) * 30

                # Apply growth/decay factor based on engagement
                engagement_trend = self._get_engagement_trend(session, user_id)
                growth_factor = 1 + (engagement_trend * 0.1)

                # Predict LTV
                predicted_ltv = avg_monthly_value * months * growth_factor

                return max(predicted_ltv, 0.0)

        except Exception as e:
            logger.error(f"Error predicting LTV: {e}", exc_info=True)
            return 0.0

    def calculate_engagement_score(self, user_id: str) -> float:
        """
        Calculate user engagement score (0-100).

        Args:
            user_id: User ID

        Returns:
            Engagement score
        """
        try:
            with self.db.session() as session:
                user = session.query(UserORM).filter(UserORM.id == user_id).first()
                if not user:
                    return 0.0

                # Get metrics
                recency = self._get_recency_score(user)
                frequency = self._get_frequency_score(session, user_id)
                duration = self._get_duration_score(session, user_id)
                diversity = self._get_diversity_score(session, user_id)

                # Weighted score
                engagement_score = (
                    recency * 0.3 +
                    frequency * 0.3 +
                    duration * 0.2 +
                    diversity * 0.2
                ) * 100

                return min(engagement_score, 100.0)

        except Exception as e:
            logger.error(f"Error calculating engagement score: {e}", exc_info=True)
            return 0.0

    def _get_avg_session_duration(self, session: Session, user_id: str) -> float:
        """Get average session duration for user."""
        avg_duration = session.query(
            func.avg(SessionORM.duration_seconds)
        ).filter(
            SessionORM.user_id == user_id
        ).scalar()

        return float(avg_duration or 0)

    def _get_session_frequency(self, session: Session, user_id: str) -> float:
        """Get session frequency (sessions per week)."""
        user = session.query(UserORM).filter(UserORM.id == user_id).first()
        if not user:
            return 0.0

        user_age_days = (get_utc_now() - user.first_seen_at).days
        if user_age_days == 0:
            return 0.0

        sessions_per_week = (user.total_sessions / user_age_days) * 7
        return sessions_per_week

    def _get_engagement_trend(self, session: Session, user_id: str) -> float:
        """Get engagement trend (-1 to 1)."""
        # Compare last 7 days to previous 7 days
        now = get_utc_now()
        recent_start = now - timedelta(days=7)
        previous_start = now - timedelta(days=14)

        recent_sessions = session.query(func.count(SessionORM.id)).filter(
            and_(
                SessionORM.user_id == user_id,
                SessionORM.started_at >= recent_start
            )
        ).scalar()

        previous_sessions = session.query(func.count(SessionORM.id)).filter(
            and_(
                SessionORM.user_id == user_id,
                SessionORM.started_at >= previous_start,
                SessionORM.started_at < recent_start
            )
        ).scalar()

        if previous_sessions == 0:
            return 0.0

        trend = (recent_sessions - previous_sessions) / previous_sessions
        return max(min(trend, 1.0), -1.0)

    def _get_recency_score(self, user: UserORM) -> float:
        """Get recency score (0-1)."""
        days_since_last_seen = (get_utc_now() - user.last_seen_at).days

        if days_since_last_seen == 0:
            return 1.0
        elif days_since_last_seen <= 1:
            return 0.9
        elif days_since_last_seen <= 7:
            return 0.7
        elif days_since_last_seen <= 14:
            return 0.5
        elif days_since_last_seen <= 30:
            return 0.3
        else:
            return 0.1

    def _get_frequency_score(self, session: Session, user_id: str) -> float:
        """Get frequency score (0-1)."""
        frequency = self._get_session_frequency(session, user_id)

        if frequency >= 7:
            return 1.0
        elif frequency >= 3:
            return 0.7
        elif frequency >= 1:
            return 0.5
        elif frequency > 0:
            return 0.3
        else:
            return 0.1

    def _get_duration_score(self, session: Session, user_id: str) -> float:
        """Get duration score (0-1)."""
        avg_duration = self._get_avg_session_duration(session, user_id)

        if avg_duration >= 600:  # 10 minutes
            return 1.0
        elif avg_duration >= 300:  # 5 minutes
            return 0.7
        elif avg_duration >= 120:  # 2 minutes
            return 0.5
        elif avg_duration > 0:
            return 0.3
        else:
            return 0.1

    def _get_diversity_score(self, session: Session, user_id: str) -> float:
        """Get diversity score based on module usage (0-1)."""
        # Count distinct modules used
        distinct_modules = session.query(
            func.count(func.distinct(EventORM.module))
        ).filter(
            and_(
                EventORM.user_id == user_id,
                EventORM.module.isnot(None)
            )
        ).scalar()

        modules_count = distinct_modules or 0

        if modules_count >= 10:
            return 1.0
        elif modules_count >= 5:
            return 0.7
        elif modules_count >= 3:
            return 0.5
        elif modules_count > 0:
            return 0.3
        else:
            return 0.1
