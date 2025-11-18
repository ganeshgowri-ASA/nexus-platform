"""Metrics tracking service."""

from datetime import datetime
from typing import Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.ab_testing.models import Metric, MetricEvent, Variant
from modules.ab_testing.schemas.metric import MetricCreate, MetricEventCreate


class MetricsService:
    """Service for tracking and managing experiment metrics."""

    def __init__(self, db: AsyncSession):
        """
        Initialize metrics service.

        Args:
            db: Database session
        """
        self.db = db

    async def create_metric(self, data: MetricCreate) -> Metric:
        """
        Create a new metric for an experiment.

        Args:
            data: Metric creation data

        Returns:
            Metric: Created metric

        Example:
            >>> service = MetricsService(db)
            >>> data = MetricCreate(
            ...     experiment_id=1,
            ...     name="Conversion Rate",
            ...     type=MetricType.CONVERSION,
            ...     is_primary=True
            ... )
            >>> metric = await service.create_metric(data)
        """
        logger.info(f"Creating metric: {data.name}")

        metric = Metric(
            experiment_id=data.experiment_id,
            name=data.name,
            description=data.description,
            type=data.type,
            is_primary=data.is_primary,
            goal_value=data.goal_value,
            metadata=data.metadata,
        )

        self.db.add(metric)
        await self.db.commit()
        await self.db.refresh(metric)

        logger.info(f"Created metric {metric.id}: {metric.name}")
        return metric

    async def track_event(self, data: MetricEventCreate) -> MetricEvent:
        """
        Track a metric event for a participant.

        Args:
            data: Metric event data

        Returns:
            MetricEvent: Created metric event

        Example:
            >>> data = MetricEventCreate(
            ...     metric_id=1,
            ...     participant_id="user_123",
            ...     variant_id=2,
            ...     value=1.0,  # 1 for conversion
            ...     properties={"source": "email_campaign"}
            ... )
            >>> event = await service.track_event(data)
        """
        logger.info(
            f"Tracking event for metric {data.metric_id}, "
            f"participant {data.participant_id}"
        )

        # Verify variant exists
        result = await self.db.execute(
            select(Variant).where(Variant.id == data.variant_id)
        )
        variant = result.scalar_one_or_none()

        if not variant:
            raise ValueError(f"Variant {data.variant_id} not found")

        # Create event
        event = MetricEvent(
            metric_id=data.metric_id,
            participant_id=data.participant_id,
            variant_id=data.variant_id,
            value=data.value,
            properties=data.properties,
        )

        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)

        logger.info(f"Tracked event {event.id} with value {event.value}")
        return event

    async def get_metric_summary(
        self,
        metric_id: int,
        variant_id: Optional[int] = None,
    ) -> dict:
        """
        Get summary statistics for a metric.

        Args:
            metric_id: ID of metric
            variant_id: Optional variant ID to filter by

        Returns:
            dict: Summary statistics

        Example:
            >>> summary = await service.get_metric_summary(
            ...     metric_id=1,
            ...     variant_id=2
            ... )
            >>> print(f"Total events: {summary['total_events']}")
            >>> print(f"Average value: {summary['average_value']}")
        """
        logger.info(f"Getting summary for metric {metric_id}")

        query = select(MetricEvent).where(MetricEvent.metric_id == metric_id)

        if variant_id:
            query = query.where(MetricEvent.variant_id == variant_id)

        result = await self.db.execute(query)
        events = list(result.scalars().all())

        if not events:
            return {
                "total_events": 0,
                "total_value": 0.0,
                "average_value": 0.0,
                "min_value": 0.0,
                "max_value": 0.0,
            }

        values = [e.value for e in events]

        return {
            "total_events": len(events),
            "total_value": sum(values),
            "average_value": sum(values) / len(values),
            "min_value": min(values),
            "max_value": max(values),
        }
