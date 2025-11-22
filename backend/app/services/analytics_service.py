"""
NEXUS Platform - Analytics Service for Channel ROI and Touchpoint Analysis
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, case

from backend.app.models.attribution import (
    Journey,
    Touchpoint,
    Conversion,
    Channel,
    AttributionResult,
    AttributionModel,
)
from backend.app.core.exceptions import NotFoundException, ValidationException


class AnalyticsService:
    """Service for channel ROI and touchpoint analysis."""

    def __init__(self, db: Session):
        """
        Initialize analytics service.

        Args:
            db: Database session
        """
        self.db = db

    def calculate_channel_roi(
        self,
        channel_ids: Optional[List[int]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        attribution_model_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Calculate ROI for channels.

        Args:
            channel_ids: Specific channels to analyze (None for all)
            start_date: Analysis start date
            end_date: Analysis end date
            attribution_model_id: Attribution model to use

        Returns:
            List of channel ROI data
        """
        # Build base query
        query = self.db.query(Channel)

        if channel_ids:
            query = query.filter(Channel.id.in_(channel_ids))

        channels = query.all()

        if not channels:
            return []

        # Get attribution results if model specified
        if attribution_model_id:
            return self._calculate_roi_from_attribution(
                channels, attribution_model_id, start_date, end_date
            )

        # Calculate ROI from raw data
        return self._calculate_roi_from_touchpoints(
            channels, start_date, end_date
        )

    def _calculate_roi_from_attribution(
        self,
        channels: List[Channel],
        model_id: int,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> List[Dict[str, Any]]:
        """Calculate ROI using attribution results."""
        channel_ids = [ch.id for ch in channels]

        # Build query for attribution results
        query = (
            self.db.query(
                AttributionResult.channel_id,
                func.sum(AttributionResult.attributed_revenue).label("total_revenue"),
                func.sum(AttributionResult.attributed_conversions).label(
                    "total_conversions"
                ),
                func.sum(AttributionResult.channel_cost).label("total_cost"),
                func.count(AttributionResult.id).label("touchpoint_count"),
            )
            .filter(
                and_(
                    AttributionResult.attribution_model_id == model_id,
                    AttributionResult.channel_id.in_(channel_ids),
                )
            )
        )

        if start_date:
            query = query.filter(AttributionResult.calculated_at >= start_date)

        if end_date:
            query = query.filter(AttributionResult.calculated_at <= end_date)

        results = query.group_by(AttributionResult.channel_id).all()

        # Format results
        channels_dict = {ch.id: ch for ch in channels}
        roi_data = []

        for result in results:
            channel = channels_dict[result.channel_id]

            # Calculate metrics
            roi = (
                ((result.total_revenue - result.total_cost) / result.total_cost) * 100
                if result.total_cost > 0
                else 0
            )
            roas = (
                result.total_revenue / result.total_cost
                if result.total_cost > 0
                else 0
            )
            avg_conversion_value = (
                result.total_revenue / result.total_conversions
                if result.total_conversions > 0
                else 0
            )
            cost_per_conversion = (
                result.total_cost / result.total_conversions
                if result.total_conversions > 0
                else 0
            )

            roi_data.append({
                "channel_id": channel.id,
                "channel_name": channel.name,
                "channel_type": channel.channel_type.value,
                "total_touchpoints": result.touchpoint_count,
                "total_conversions": float(result.total_conversions),
                "total_revenue": float(result.total_revenue),
                "total_cost": float(result.total_cost),
                "roi": float(roi),
                "roas": float(roas),
                "avg_conversion_value": float(avg_conversion_value),
                "cost_per_conversion": float(cost_per_conversion),
            })

        return roi_data

    def _calculate_roi_from_touchpoints(
        self,
        channels: List[Channel],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> List[Dict[str, Any]]:
        """Calculate ROI from raw touchpoint data."""
        channel_ids = [ch.id for ch in channels]

        # Get touchpoint data
        tp_query = (
            self.db.query(
                Touchpoint.channel_id,
                func.count(Touchpoint.id).label("touchpoint_count"),
                func.sum(Touchpoint.cost).label("total_cost"),
            )
            .filter(Touchpoint.channel_id.in_(channel_ids))
        )

        if start_date:
            tp_query = tp_query.filter(Touchpoint.timestamp >= start_date)

        if end_date:
            tp_query = tp_query.filter(Touchpoint.timestamp <= end_date)

        touchpoint_data = tp_query.group_by(Touchpoint.channel_id).all()

        # Get conversion data
        conv_query = (
            self.db.query(
                Touchpoint.channel_id,
                func.count(func.distinct(Conversion.id)).label("conversion_count"),
                func.sum(Conversion.revenue).label("total_revenue"),
            )
            .join(Journey, Touchpoint.journey_id == Journey.id)
            .join(Conversion, Journey.id == Conversion.journey_id)
            .filter(Touchpoint.channel_id.in_(channel_ids))
        )

        if start_date:
            conv_query = conv_query.filter(Journey.start_time >= start_date)

        if end_date:
            conv_query = conv_query.filter(Journey.start_time <= end_date)

        conversion_data = conv_query.group_by(Touchpoint.channel_id).all()

        # Combine data
        touchpoint_dict = {td.channel_id: td for td in touchpoint_data}
        conversion_dict = {cd.channel_id: cd for cd in conversion_data}
        channels_dict = {ch.id: ch for ch in channels}

        roi_data = []
        for channel_id in channel_ids:
            channel = channels_dict[channel_id]
            tp_data = touchpoint_dict.get(channel_id)
            conv_data = conversion_dict.get(channel_id)

            touchpoint_count = tp_data.touchpoint_count if tp_data else 0
            total_cost = float(tp_data.total_cost or 0) if tp_data else 0
            conversion_count = conv_data.conversion_count if conv_data else 0
            total_revenue = float(conv_data.total_revenue or 0) if conv_data else 0

            # Calculate metrics
            roi = (
                ((total_revenue - total_cost) / total_cost) * 100
                if total_cost > 0
                else 0
            )
            roas = total_revenue / total_cost if total_cost > 0 else 0
            avg_conversion_value = (
                total_revenue / conversion_count if conversion_count > 0 else 0
            )
            cost_per_conversion = (
                total_cost / conversion_count if conversion_count > 0 else 0
            )
            conversion_rate = (
                conversion_count / touchpoint_count if touchpoint_count > 0 else 0
            )

            roi_data.append({
                "channel_id": channel.id,
                "channel_name": channel.name,
                "channel_type": channel.channel_type.value,
                "total_touchpoints": touchpoint_count,
                "total_conversions": conversion_count,
                "total_revenue": total_revenue,
                "total_cost": total_cost,
                "roi": roi,
                "roas": roas,
                "avg_conversion_value": avg_conversion_value,
                "cost_per_conversion": cost_per_conversion,
                "conversion_rate": conversion_rate,
            })

        return roi_data

    def analyze_touchpoint_performance(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = "channel",
    ) -> List[Dict[str, Any]]:
        """
        Analyze touchpoint performance.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            group_by: Grouping dimension (channel, type, position)

        Returns:
            Touchpoint performance analysis
        """
        if group_by == "channel":
            return self._analyze_by_channel(start_date, end_date)
        elif group_by == "type":
            return self._analyze_by_type(start_date, end_date)
        elif group_by == "position":
            return self._analyze_by_position(start_date, end_date)
        else:
            raise ValidationException(f"Invalid group_by value: {group_by}")

    def _analyze_by_channel(
        self, start_date: Optional[datetime], end_date: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """Analyze touchpoints by channel."""
        query = (
            self.db.query(
                Channel.id,
                Channel.name,
                Channel.channel_type,
                func.count(Touchpoint.id).label("touchpoint_count"),
                func.avg(Touchpoint.engagement_score).label("avg_engagement"),
                func.avg(Touchpoint.time_spent_seconds).label("avg_time_spent"),
                func.avg(Touchpoint.pages_viewed).label("avg_pages_viewed"),
                func.sum(Touchpoint.cost).label("total_cost"),
            )
            .join(Touchpoint, Channel.id == Touchpoint.channel_id)
        )

        if start_date:
            query = query.filter(Touchpoint.timestamp >= start_date)

        if end_date:
            query = query.filter(Touchpoint.timestamp <= end_date)

        results = query.group_by(Channel.id, Channel.name, Channel.channel_type).all()

        return [
            {
                "channel_id": r.id,
                "channel_name": r.name,
                "channel_type": r.channel_type.value,
                "touchpoint_count": r.touchpoint_count,
                "avg_engagement": float(r.avg_engagement or 0),
                "avg_time_spent_seconds": float(r.avg_time_spent or 0),
                "avg_pages_viewed": float(r.avg_pages_viewed or 0),
                "total_cost": float(r.total_cost or 0),
            }
            for r in results
        ]

    def _analyze_by_type(
        self, start_date: Optional[datetime], end_date: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """Analyze touchpoints by type."""
        query = self.db.query(
            Touchpoint.touchpoint_type,
            func.count(Touchpoint.id).label("touchpoint_count"),
            func.avg(Touchpoint.engagement_score).label("avg_engagement"),
            func.avg(Touchpoint.time_spent_seconds).label("avg_time_spent"),
        )

        if start_date:
            query = query.filter(Touchpoint.timestamp >= start_date)

        if end_date:
            query = query.filter(Touchpoint.timestamp <= end_date)

        results = query.group_by(Touchpoint.touchpoint_type).all()

        return [
            {
                "touchpoint_type": r.touchpoint_type.value,
                "touchpoint_count": r.touchpoint_count,
                "avg_engagement": float(r.avg_engagement or 0),
                "avg_time_spent_seconds": float(r.avg_time_spent or 0),
            }
            for r in results
        ]

    def _analyze_by_position(
        self, start_date: Optional[datetime], end_date: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """Analyze touchpoints by position in journey."""
        # Categorize positions: first, middle, last
        query = (
            self.db.query(
                case(
                    (Touchpoint.position_in_journey == 1, "first"),
                    (Touchpoint.position_in_journey == Journey.total_touchpoints, "last"),
                    else_="middle",
                ).label("position_category"),
                func.count(Touchpoint.id).label("touchpoint_count"),
                func.avg(Touchpoint.engagement_score).label("avg_engagement"),
            )
            .join(Journey, Touchpoint.journey_id == Journey.id)
        )

        if start_date:
            query = query.filter(Journey.start_time >= start_date)

        if end_date:
            query = query.filter(Journey.start_time <= end_date)

        results = query.group_by("position_category").all()

        return [
            {
                "position_category": r.position_category,
                "touchpoint_count": r.touchpoint_count,
                "avg_engagement": float(r.avg_engagement or 0),
            }
            for r in results
        ]

    def get_channel_comparison(
        self,
        channel_ids: List[int],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        attribution_model_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Compare multiple channels across key metrics.

        Args:
            channel_ids: Channels to compare
            start_date: Start date
            end_date: End date
            attribution_model_id: Attribution model ID

        Returns:
            Channel comparison data
        """
        # Get ROI data
        roi_data = self.calculate_channel_roi(
            channel_ids, start_date, end_date, attribution_model_id
        )

        # Get performance data
        performance_data = self._analyze_by_channel(start_date, end_date)
        performance_dict = {p["channel_id"]: p for p in performance_data}

        # Combine data
        comparison = []
        for roi in roi_data:
            channel_id = roi["channel_id"]
            perf = performance_dict.get(channel_id, {})

            comparison.append({
                **roi,
                "avg_engagement": perf.get("avg_engagement", 0),
                "avg_time_spent_seconds": perf.get("avg_time_spent_seconds", 0),
                "avg_pages_viewed": perf.get("avg_pages_viewed", 0),
            })

        # Calculate rankings
        for metric in ["roi", "roas", "total_revenue", "avg_engagement"]:
            sorted_channels = sorted(
                comparison, key=lambda x: x.get(metric, 0), reverse=True
            )
            for rank, channel in enumerate(sorted_channels, 1):
                channel[f"{metric}_rank"] = rank

        return {
            "channels": comparison,
            "summary": {
                "total_channels": len(comparison),
                "total_revenue": sum(c["total_revenue"] for c in comparison),
                "total_cost": sum(c["total_cost"] for c in comparison),
                "avg_roi": (
                    sum(c["roi"] for c in comparison) / len(comparison)
                    if comparison
                    else 0
                ),
            },
        }

    def get_trend_analysis(
        self,
        metric: str,
        channel_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = "day",
    ) -> List[Dict[str, Any]]:
        """
        Get trend analysis for a metric over time.

        Args:
            metric: Metric to analyze (touchpoints, conversions, revenue, cost)
            channel_id: Optional channel filter
            start_date: Start date
            end_date: End date
            interval: Time interval (day, week, month)

        Returns:
            Time series data
        """
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Determine date truncation based on interval
        if interval == "day":
            date_trunc = func.date(Touchpoint.timestamp)
        elif interval == "week":
            date_trunc = func.date_trunc("week", Touchpoint.timestamp)
        elif interval == "month":
            date_trunc = func.date_trunc("month", Touchpoint.timestamp)
        else:
            raise ValidationException(f"Invalid interval: {interval}")

        # Build query based on metric
        if metric == "touchpoints":
            query = (
                self.db.query(
                    date_trunc.label("date"),
                    func.count(Touchpoint.id).label("value"),
                )
                .filter(Touchpoint.timestamp.between(start_date, end_date))
            )

            if channel_id:
                query = query.filter(Touchpoint.channel_id == channel_id)

            results = query.group_by("date").order_by("date").all()

        elif metric == "cost":
            query = (
                self.db.query(
                    date_trunc.label("date"),
                    func.sum(Touchpoint.cost).label("value"),
                )
                .filter(Touchpoint.timestamp.between(start_date, end_date))
            )

            if channel_id:
                query = query.filter(Touchpoint.channel_id == channel_id)

            results = query.group_by("date").order_by("date").all()

        else:
            raise ValidationException(f"Invalid metric: {metric}")

        return [
            {"date": r.date.isoformat() if hasattr(r.date, 'isoformat') else str(r.date), "value": float(r.value or 0)}
            for r in results
        ]
