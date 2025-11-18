"""
NEXUS Platform - Journey Mapping and Visualization Service
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from backend.app.models.attribution import (
    Journey,
    Touchpoint,
    Conversion,
    Channel,
    AttributionResult,
)
from backend.app.core.exceptions import NotFoundException, AttributionException
from backend.app.services.attribution_service import AttributionService


class JourneyVisualizationService:
    """Service for journey mapping and visualization."""

    def __init__(self, db: Session):
        """
        Initialize journey visualization service.

        Args:
            db: Database session
        """
        self.db = db
        self.attribution_service = AttributionService(db)

    def get_journey_visualization(
        self,
        journey_id: int,
        attribution_model_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get complete journey visualization data.

        Args:
            journey_id: Journey ID
            attribution_model_id: Optional attribution model ID for credit display

        Returns:
            Journey visualization data
        """
        # Get journey
        journey = self.attribution_service.get_journey(journey_id)

        # Get touchpoints
        touchpoints = (
            self.db.query(Touchpoint)
            .filter(Touchpoint.journey_id == journey_id)
            .order_by(Touchpoint.position_in_journey)
            .all()
        )

        # Get conversions
        conversions = (
            self.db.query(Conversion)
            .filter(Conversion.journey_id == journey_id)
            .order_by(Conversion.timestamp)
            .all()
        )

        # Get channels
        channel_ids = list(set(tp.channel_id for tp in touchpoints))
        channels = (
            self.db.query(Channel)
            .filter(Channel.id.in_(channel_ids))
            .all()
        )
        channels_dict = {ch.id: ch for ch in channels}

        # Get attribution credits if model specified
        attribution_credits = {}
        if attribution_model_id:
            try:
                # Try to get existing results
                results = (
                    self.db.query(AttributionResult)
                    .filter(
                        and_(
                            AttributionResult.journey_id == journey_id,
                            AttributionResult.attribution_model_id == attribution_model_id,
                        )
                    )
                    .all()
                )

                if not results:
                    # Calculate attribution
                    results = self.attribution_service.calculate_attribution(
                        journey_id, attribution_model_id
                    )

                # Map channel to credit
                for result in results:
                    attribution_credits[result.channel_id] = result.credit

            except Exception as e:
                print(f"Error getting attribution credits: {e}")

        # Format touchpoint data
        touchpoint_data = []
        for tp in touchpoints:
            channel = channels_dict.get(tp.channel_id)
            touchpoint_data.append({
                "id": tp.id,
                "position": tp.position_in_journey,
                "channel_id": tp.channel_id,
                "channel_name": channel.name if channel else "Unknown",
                "channel_type": channel.channel_type.value if channel else "unknown",
                "touchpoint_type": tp.touchpoint_type.value,
                "timestamp": tp.timestamp,
                "time_spent_seconds": tp.time_spent_seconds,
                "pages_viewed": tp.pages_viewed,
                "engagement_score": tp.engagement_score,
                "cost": tp.cost,
                "attribution_credit": attribution_credits.get(tp.channel_id),
                "campaign_name": tp.campaign_name,
                "page_url": tp.page_url,
                "device_type": tp.device_type,
                "location": tp.location,
            })

        # Format conversion data
        conversion_data = [
            {
                "id": conv.id,
                "type": conv.conversion_type.value,
                "timestamp": conv.timestamp,
                "revenue": conv.revenue,
                "quantity": conv.quantity,
                "product_name": conv.product_name,
            }
            for conv in conversions
        ]

        return {
            "journey_id": journey.id,
            "user_id": journey.user_id,
            "session_id": journey.session_id,
            "start_time": journey.start_time,
            "end_time": journey.end_time,
            "total_touchpoints": journey.total_touchpoints,
            "has_conversion": journey.has_conversion,
            "conversion_value": journey.conversion_value,
            "journey_duration_minutes": journey.journey_duration_minutes,
            "touchpoints": touchpoint_data,
            "conversions": conversion_data,
            "total_cost": sum(tp.cost for tp in touchpoints),
            "unique_channels": len(set(tp.channel_id for tp in touchpoints)),
        }

    def get_conversion_paths(
        self,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_touchpoints: int = 1,
        converted_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get common conversion paths.

        Args:
            limit: Maximum number of paths to return
            start_date: Filter journeys after this date
            end_date: Filter journeys before this date
            min_touchpoints: Minimum touchpoints required
            converted_only: Only include converted journeys

        Returns:
            List of conversion path patterns
        """
        # Build query
        query = self.db.query(Journey)

        if converted_only:
            query = query.filter(Journey.has_conversion == True)

        if start_date:
            query = query.filter(Journey.start_time >= start_date)

        if end_date:
            query = query.filter(Journey.start_time <= end_date)

        if min_touchpoints > 1:
            query = query.filter(Journey.total_touchpoints >= min_touchpoints)

        # Get journeys
        journeys = query.limit(limit).all()

        # Extract paths
        paths = []
        for journey in journeys:
            # Get touchpoints
            touchpoints = (
                self.db.query(Touchpoint, Channel)
                .join(Channel, Touchpoint.channel_id == Channel.id)
                .filter(Touchpoint.journey_id == journey.id)
                .order_by(Touchpoint.position_in_journey)
                .all()
            )

            # Create path string
            path = " → ".join(
                [f"{ch.name} ({ch.channel_type.value})" for tp, ch in touchpoints]
            )

            paths.append({
                "journey_id": journey.id,
                "path": path,
                "touchpoint_count": len(touchpoints),
                "conversion_value": journey.conversion_value,
                "duration_minutes": journey.journey_duration_minutes,
                "channels": [ch.name for tp, ch in touchpoints],
            })

        return paths

    def analyze_touchpoint_patterns(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Analyze touchpoint patterns and sequences.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            Touchpoint pattern analysis
        """
        # Build query
        query = self.db.query(Journey)

        if start_date:
            query = query.filter(Journey.start_time >= start_date)

        if end_date:
            query = query.filter(Journey.start_time <= end_date)

        journeys = query.all()

        # Analyze patterns
        total_journeys = len(journeys)
        converted_journeys = sum(1 for j in journeys if j.has_conversion)

        # Touchpoint position analysis
        first_touchpoints: Dict[str, int] = {}
        last_touchpoints: Dict[str, int] = {}
        all_touchpoints: Dict[str, int] = {}

        for journey in journeys:
            touchpoints = (
                self.db.query(Touchpoint, Channel)
                .join(Channel, Touchpoint.channel_id == Channel.id)
                .filter(Touchpoint.journey_id == journey.id)
                .order_by(Touchpoint.position_in_journey)
                .all()
            )

            if not touchpoints:
                continue

            # First touchpoint
            first_channel = touchpoints[0][1].name
            first_touchpoints[first_channel] = (
                first_touchpoints.get(first_channel, 0) + 1
            )

            # Last touchpoint
            last_channel = touchpoints[-1][1].name
            last_touchpoints[last_channel] = (
                last_touchpoints.get(last_channel, 0) + 1
            )

            # All touchpoints
            for tp, ch in touchpoints:
                all_touchpoints[ch.name] = all_touchpoints.get(ch.name, 0) + 1

        return {
            "total_journeys": total_journeys,
            "converted_journeys": converted_journeys,
            "conversion_rate": converted_journeys / total_journeys if total_journeys > 0 else 0,
            "first_touchpoints": sorted(
                first_touchpoints.items(), key=lambda x: x[1], reverse=True
            ),
            "last_touchpoints": sorted(
                last_touchpoints.items(), key=lambda x: x[1], reverse=True
            ),
            "all_touchpoints": sorted(
                all_touchpoints.items(), key=lambda x: x[1], reverse=True
            ),
        }

    def get_journey_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get aggregated journey metrics.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            Journey metrics
        """
        # Build query
        query = self.db.query(Journey)

        if start_date:
            query = query.filter(Journey.start_time >= start_date)

        if end_date:
            query = query.filter(Journey.start_time <= end_date)

        # Get aggregated metrics
        metrics = query.with_entities(
            func.count(Journey.id).label("total_journeys"),
            func.sum(func.cast(Journey.has_conversion, func.Integer)).label(
                "total_conversions"
            ),
            func.sum(Journey.conversion_value).label("total_revenue"),
            func.avg(Journey.total_touchpoints).label("avg_touchpoints"),
            func.avg(Journey.journey_duration_minutes).label("avg_duration"),
            func.avg(Journey.conversion_value).label("avg_conversion_value"),
        ).first()

        if not metrics.total_journeys:
            return {
                "total_journeys": 0,
                "total_conversions": 0,
                "conversion_rate": 0,
                "total_revenue": 0,
                "avg_touchpoints": 0,
                "avg_duration_minutes": 0,
                "avg_conversion_value": 0,
            }

        return {
            "total_journeys": metrics.total_journeys,
            "total_conversions": metrics.total_conversions or 0,
            "conversion_rate": (
                (metrics.total_conversions or 0) / metrics.total_journeys
                if metrics.total_journeys > 0
                else 0
            ),
            "total_revenue": float(metrics.total_revenue or 0),
            "avg_touchpoints": float(metrics.avg_touchpoints or 0),
            "avg_duration_minutes": float(metrics.avg_duration or 0),
            "avg_conversion_value": float(metrics.avg_conversion_value or 0),
        }

    def find_similar_journeys(
        self, journey_id: int, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find journeys similar to the given journey.

        Similarity is based on:
        - Channel sequence
        - Number of touchpoints
        - Journey duration

        Args:
            journey_id: Reference journey ID
            limit: Maximum number of similar journeys

        Returns:
            List of similar journeys
        """
        # Get reference journey
        reference_journey = self.attribution_service.get_journey(journey_id)

        # Get reference touchpoints
        ref_touchpoints = (
            self.db.query(Touchpoint)
            .filter(Touchpoint.journey_id == journey_id)
            .order_by(Touchpoint.position_in_journey)
            .all()
        )

        ref_channel_sequence = [tp.channel_id for tp in ref_touchpoints]

        # Find similar journeys
        # This is a simplified similarity - in production, use more sophisticated matching
        similar_query = (
            self.db.query(Journey)
            .filter(
                and_(
                    Journey.id != journey_id,
                    Journey.total_touchpoints.between(
                        max(1, reference_journey.total_touchpoints - 2),
                        reference_journey.total_touchpoints + 2,
                    ),
                )
            )
            .limit(limit * 2)  # Get more candidates for filtering
        )

        similar_journeys = []
        for journey in similar_query:
            touchpoints = (
                self.db.query(Touchpoint)
                .filter(Touchpoint.journey_id == journey.id)
                .order_by(Touchpoint.position_in_journey)
                .all()
            )

            channel_sequence = [tp.channel_id for tp in touchpoints]

            # Calculate similarity score (simple overlap)
            overlap = len(set(ref_channel_sequence) & set(channel_sequence))
            similarity_score = overlap / len(set(ref_channel_sequence + channel_sequence))

            if similarity_score > 0.3:  # Threshold
                similar_journeys.append({
                    "journey_id": journey.id,
                    "user_id": journey.user_id,
                    "similarity_score": similarity_score,
                    "total_touchpoints": journey.total_touchpoints,
                    "has_conversion": journey.has_conversion,
                    "conversion_value": journey.conversion_value,
                    "channel_sequence": channel_sequence,
                })

        # Sort by similarity and limit
        similar_journeys.sort(key=lambda x: x["similarity_score"], reverse=True)

        return similar_journeys[:limit]
