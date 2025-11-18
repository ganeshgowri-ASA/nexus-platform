"""
Data Aggregator

Data aggregation engine with time-series support.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from modules.analytics.storage.database import Database
from modules.analytics.storage.models import EventORM, MetricORM, SessionORM
from modules.analytics.storage.repositories import MetricRepository
from shared.constants import AggregationPeriod, MetricType
from shared.utils import generate_uuid, get_utc_now, safe_divide

logger = logging.getLogger(__name__)


class DataAggregator:
    """
    Data aggregation engine for analytics metrics.

    Features:
    - Time-series aggregation
    - Multiple aggregation periods
    - Metric calculations
    - Incremental updates
    """

    def __init__(self, db: Database):
        """
        Initialize data aggregator.

        Args:
            db: Database instance
        """
        self.db = db
        self.metric_repository = MetricRepository()

        logger.info("Data aggregator initialized")

    def aggregate_events(
        self,
        session: Session,
        start_date: datetime,
        end_date: datetime,
        period: AggregationPeriod = AggregationPeriod.DAY,
        event_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Aggregate events by time period.

        Args:
            session: Database session
            start_date: Start date
            end_date: End date
            period: Aggregation period
            event_types: Optional event types filter

        Returns:
            List of aggregated data
        """
        try:
            # Build query
            query = session.query(
                func.date_trunc(period.value, EventORM.timestamp).label("period"),
                EventORM.event_type,
                func.count(EventORM.id).label("count"),
                func.count(func.distinct(EventORM.user_id)).label("unique_users"),
                func.count(func.distinct(EventORM.session_id)).label("unique_sessions"),
            ).filter(
                and_(
                    EventORM.timestamp >= start_date,
                    EventORM.timestamp <= end_date,
                )
            )

            if event_types:
                query = query.filter(EventORM.event_type.in_(event_types))

            query = query.group_by("period", EventORM.event_type).order_by("period")

            results = query.all()

            aggregated = [
                {
                    "period": row.period,
                    "event_type": row.event_type,
                    "count": row.count,
                    "unique_users": row.unique_users,
                    "unique_sessions": row.unique_sessions,
                }
                for row in results
            ]

            logger.info(f"Aggregated {len(aggregated)} event periods")
            return aggregated

        except Exception as e:
            logger.error(f"Error aggregating events: {e}", exc_info=True)
            return []

    def calculate_session_metrics(
        self,
        session: Session,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """
        Calculate session-based metrics.

        Args:
            session: Database session
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary of session metrics
        """
        try:
            # Query sessions
            query = session.query(
                func.count(SessionORM.id).label("total_sessions"),
                func.count(func.distinct(SessionORM.user_id)).label("unique_users"),
                func.avg(SessionORM.duration_seconds).label("avg_duration"),
                func.avg(SessionORM.page_views).label("avg_page_views"),
                func.sum(func.cast(SessionORM.is_bounce, func.Integer)).label("bounces"),
                func.sum(func.cast(SessionORM.converted, func.Integer)).label("conversions"),
                func.sum(SessionORM.conversion_value).label("total_value"),
            ).filter(
                and_(
                    SessionORM.started_at >= start_date,
                    SessionORM.started_at <= end_date,
                )
            )

            result = query.first()

            total_sessions = result.total_sessions or 0
            bounces = result.bounces or 0
            conversions = result.conversions or 0

            metrics = {
                "total_sessions": total_sessions,
                "unique_users": result.unique_users or 0,
                "avg_duration_seconds": round(result.avg_duration or 0, 2),
                "avg_page_views": round(result.avg_page_views or 0, 2),
                "bounce_rate": safe_divide(bounces, total_sessions) * 100,
                "conversion_rate": safe_divide(conversions, total_sessions) * 100,
                "total_conversions": conversions,
                "total_conversion_value": float(result.total_value or 0),
            }

            logger.info("Calculated session metrics")
            return metrics

        except Exception as e:
            logger.error(f"Error calculating session metrics: {e}", exc_info=True)
            return {}

    def generate_time_series(
        self,
        session: Session,
        metric_name: str,
        start_date: datetime,
        end_date: datetime,
        period: AggregationPeriod = AggregationPeriod.DAY,
    ) -> List[Tuple[datetime, float]]:
        """
        Generate time series for a metric.

        Args:
            session: Database session
            metric_name: Metric name
            start_date: Start date
            end_date: End date
            period: Aggregation period

        Returns:
            List of (timestamp, value) tuples
        """
        try:
            metrics = self.metric_repository.get_time_series(
                session, metric_name, start_date, end_date, period.value
            )

            time_series = [(m.timestamp, m.value) for m in metrics]

            logger.info(f"Generated time series for {metric_name}: {len(time_series)} points")
            return time_series

        except Exception as e:
            logger.error(f"Error generating time series: {e}", exc_info=True)
            return []

    def save_metric(
        self,
        session: Session,
        name: str,
        metric_type: MetricType,
        value: float,
        period: Optional[AggregationPeriod] = None,
        dimensions: Optional[Dict[str, Any]] = None,
        module: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """
        Save a calculated metric.

        Args:
            session: Database session
            name: Metric name
            metric_type: Metric type
            value: Metric value
            period: Aggregation period
            dimensions: Metric dimensions
            module: Module name
            timestamp: Metric timestamp

        Returns:
            True if successful
        """
        try:
            metric_data = {
                "id": generate_uuid(),
                "name": name,
                "metric_type": metric_type.value,
                "value": value,
                "period": period.value if period else None,
                "dimensions": dimensions or {},
                "module": module,
                "timestamp": timestamp or get_utc_now(),
            }

            self.metric_repository.create(session, **metric_data)
            logger.debug(f"Saved metric: {name} = {value}")
            return True

        except Exception as e:
            logger.error(f"Error saving metric: {e}", exc_info=True)
            return False

    def aggregate_by_dimension(
        self,
        session: Session,
        dimension: str,
        start_date: datetime,
        end_date: datetime,
        event_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Aggregate events by a dimension.

        Args:
            session: Database session
            dimension: Dimension field name
            start_date: Start date
            end_date: End date
            event_types: Optional event types filter

        Returns:
            List of aggregated data by dimension
        """
        try:
            # Map dimension to ORM field
            dimension_field = getattr(EventORM, dimension, None)
            if dimension_field is None:
                logger.error(f"Invalid dimension: {dimension}")
                return []

            query = session.query(
                dimension_field.label("dimension_value"),
                func.count(EventORM.id).label("count"),
                func.count(func.distinct(EventORM.user_id)).label("unique_users"),
            ).filter(
                and_(
                    EventORM.timestamp >= start_date,
                    EventORM.timestamp <= end_date,
                    dimension_field.isnot(None),
                )
            )

            if event_types:
                query = query.filter(EventORM.event_type.in_(event_types))

            query = query.group_by("dimension_value").order_by(func.count(EventORM.id).desc())

            results = query.all()

            aggregated = [
                {
                    "dimension": dimension,
                    "value": row.dimension_value,
                    "count": row.count,
                    "unique_users": row.unique_users,
                }
                for row in results
            ]

            logger.info(f"Aggregated by {dimension}: {len(aggregated)} values")
            return aggregated

        except Exception as e:
            logger.error(f"Error aggregating by dimension: {e}", exc_info=True)
            return []

    def calculate_retention(
        self,
        session: Session,
        cohort_date: datetime,
        periods: int = 12,
    ) -> List[Dict[str, Any]]:
        """
        Calculate retention rates for a cohort.

        Args:
            session: Database session
            cohort_date: Cohort date
            periods: Number of periods to calculate

        Returns:
            List of retention data per period
        """
        try:
            # Get users from cohort
            cohort_start = cohort_date.replace(hour=0, minute=0, second=0, microsecond=0)
            cohort_end = cohort_start + timedelta(days=1)

            cohort_users = session.query(SessionORM.user_id).filter(
                and_(
                    SessionORM.started_at >= cohort_start,
                    SessionORM.started_at < cohort_end,
                )
            ).distinct().all()

            cohort_user_ids = [u.user_id for u in cohort_users]
            initial_count = len(cohort_user_ids)

            if initial_count == 0:
                return []

            retention_data = []

            for period in range(periods):
                period_start = cohort_start + timedelta(days=period * 7)
                period_end = period_start + timedelta(days=7)

                active_users = session.query(
                    func.count(func.distinct(SessionORM.user_id))
                ).filter(
                    and_(
                        SessionORM.user_id.in_(cohort_user_ids),
                        SessionORM.started_at >= period_start,
                        SessionORM.started_at < period_end,
                    )
                ).scalar()

                retention_rate = safe_divide(active_users, initial_count) * 100

                retention_data.append({
                    "period": period,
                    "period_start": period_start,
                    "active_users": active_users,
                    "retention_rate": round(retention_rate, 2),
                })

            logger.info(f"Calculated retention for cohort: {len(retention_data)} periods")
            return retention_data

        except Exception as e:
            logger.error(f"Error calculating retention: {e}", exc_info=True)
            return []
