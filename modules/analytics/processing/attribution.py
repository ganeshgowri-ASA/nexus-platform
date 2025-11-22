"""
Attribution Modeling

Multi-channel attribution for conversions.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from modules.analytics.storage.database import Database
from modules.analytics.storage.models import EventORM, GoalConversionORM, SessionORM
from shared.constants import AttributionModel
from shared.utils import safe_divide

logger = logging.getLogger(__name__)


class AttributionEngine:
    """Multi-channel attribution engine."""

    def __init__(self, db: Database):
        """Initialize attribution engine."""
        self.db = db
        logger.info("Attribution engine initialized")

    def calculate_attribution(
        self,
        conversion_id: str,
        model: AttributionModel = AttributionModel.LINEAR
    ) -> Dict[str, float]:
        """
        Calculate attribution for a conversion.

        Args:
            conversion_id: Goal conversion ID
            model: Attribution model to use

        Returns:
            Dictionary of touchpoint credits
        """
        try:
            with self.db.session() as session:
                # Get conversion
                conversion = session.query(GoalConversionORM).filter(
                    GoalConversionORM.id == conversion_id
                ).first()

                if not conversion:
                    return {}

                # Get touchpoints (events leading to conversion)
                touchpoints = self._get_touchpoints(
                    session,
                    conversion.user_id,
                    conversion.converted_at
                )

                if not touchpoints:
                    return {}

                # Calculate attribution based on model
                if model == AttributionModel.FIRST_TOUCH:
                    return self._first_touch_attribution(touchpoints)
                elif model == AttributionModel.LAST_TOUCH:
                    return self._last_touch_attribution(touchpoints)
                elif model == AttributionModel.LINEAR:
                    return self._linear_attribution(touchpoints)
                elif model == AttributionModel.TIME_DECAY:
                    return self._time_decay_attribution(touchpoints, conversion.converted_at)
                elif model == AttributionModel.POSITION_BASED:
                    return self._position_based_attribution(touchpoints)
                else:
                    return {}

        except Exception as e:
            logger.error(f"Error calculating attribution: {e}", exc_info=True)
            return {}

    def _get_touchpoints(
        self,
        session: Session,
        user_id: str,
        conversion_date: datetime,
        lookback_days: int = 30
    ) -> List[EventORM]:
        """Get user touchpoints before conversion."""
        from datetime import timedelta

        lookback_start = conversion_date - timedelta(days=lookback_days)

        touchpoints = session.query(EventORM).filter(
            and_(
                EventORM.user_id == user_id,
                EventORM.timestamp >= lookback_start,
                EventORM.timestamp <= conversion_date,
                EventORM.event_type.in_([
                    'page_view', 'button_click', 'link_click',
                    'search_query', 'module_open'
                ])
            )
        ).order_by(EventORM.timestamp).all()

        return touchpoints

    def _first_touch_attribution(self, touchpoints: List[EventORM]) -> Dict[str, float]:
        """First touch attribution - 100% to first interaction."""
        if not touchpoints:
            return {}

        first_touchpoint = touchpoints[0]
        channel = first_touchpoint.utm_source or first_touchpoint.referrer or "direct"

        return {channel: 1.0}

    def _last_touch_attribution(self, touchpoints: List[EventORM]) -> Dict[str, float]:
        """Last touch attribution - 100% to last interaction."""
        if not touchpoints:
            return {}

        last_touchpoint = touchpoints[-1]
        channel = last_touchpoint.utm_source or last_touchpoint.referrer or "direct"

        return {channel: 1.0}

    def _linear_attribution(self, touchpoints: List[EventORM]) -> Dict[str, float]:
        """Linear attribution - equal credit to all touchpoints."""
        if not touchpoints:
            return {}

        credit_per_touchpoint = 1.0 / len(touchpoints)
        attribution = {}

        for touchpoint in touchpoints:
            channel = touchpoint.utm_source or touchpoint.referrer or "direct"
            attribution[channel] = attribution.get(channel, 0.0) + credit_per_touchpoint

        return attribution

    def _time_decay_attribution(
        self,
        touchpoints: List[EventORM],
        conversion_date: datetime
    ) -> Dict[str, float]:
        """Time decay attribution - more credit to recent touchpoints."""
        if not touchpoints:
            return {}

        import math

        # Calculate time-based weights (exponential decay)
        weights = []
        total_weight = 0

        for touchpoint in touchpoints:
            days_ago = (conversion_date - touchpoint.timestamp).days
            weight = math.exp(-days_ago / 7)  # 7-day half-life
            weights.append(weight)
            total_weight += weight

        # Normalize and assign credits
        attribution = {}

        for touchpoint, weight in zip(touchpoints, weights):
            channel = touchpoint.utm_source or touchpoint.referrer or "direct"
            credit = weight / total_weight
            attribution[channel] = attribution.get(channel, 0.0) + credit

        return attribution

    def _position_based_attribution(self, touchpoints: List[EventORM]) -> Dict[str, float]:
        """Position-based attribution - 40% first, 40% last, 20% middle."""
        if not touchpoints:
            return {}

        attribution = {}

        if len(touchpoints) == 1:
            # Single touchpoint gets 100%
            channel = touchpoints[0].utm_source or touchpoints[0].referrer or "direct"
            attribution[channel] = 1.0
        elif len(touchpoints) == 2:
            # First and last get 50% each
            first_channel = touchpoints[0].utm_source or touchpoints[0].referrer or "direct"
            last_channel = touchpoints[-1].utm_source or touchpoints[-1].referrer or "direct"
            attribution[first_channel] = attribution.get(first_channel, 0.0) + 0.5
            attribution[last_channel] = attribution.get(last_channel, 0.0) + 0.5
        else:
            # First gets 40%
            first_channel = touchpoints[0].utm_source or touchpoints[0].referrer or "direct"
            attribution[first_channel] = attribution.get(first_channel, 0.0) + 0.4

            # Last gets 40%
            last_channel = touchpoints[-1].utm_source or touchpoints[-1].referrer or "direct"
            attribution[last_channel] = attribution.get(last_channel, 0.0) + 0.4

            # Middle touchpoints share 20%
            middle_touchpoints = touchpoints[1:-1]
            credit_per_middle = 0.2 / len(middle_touchpoints)

            for touchpoint in middle_touchpoints:
                channel = touchpoint.utm_source or touchpoint.referrer or "direct"
                attribution[channel] = attribution.get(channel, 0.0) + credit_per_middle

        return attribution
