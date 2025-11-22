"""
NEXUS Platform - Attribution Service
Implements multi-touch attribution models and analysis.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import math
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from backend.app.models.attribution import (
    Journey,
    Touchpoint,
    Conversion,
    Channel,
    AttributionModel,
    AttributionResult,
    AttributionModelType,
)
from backend.app.core.exceptions import (
    AttributionException,
    NotFoundException,
    ValidationException,
)


class AttributionCalculator:
    """Core attribution calculation engine."""

    def __init__(self, db: Session):
        """
        Initialize attribution calculator.

        Args:
            db: Database session
        """
        self.db = db

    def calculate_first_touch(
        self, touchpoints: List[Touchpoint], conversion_value: float
    ) -> Dict[int, float]:
        """
        First-touch attribution: 100% credit to first touchpoint.

        Args:
            touchpoints: List of touchpoints in journey
            conversion_value: Value of conversion

        Returns:
            Dictionary mapping channel_id to attribution credit
        """
        if not touchpoints:
            return {}

        # Sort by position to ensure we get the first touchpoint
        sorted_touchpoints = sorted(touchpoints, key=lambda t: t.position_in_journey)
        first_touchpoint = sorted_touchpoints[0]

        return {first_touchpoint.channel_id: conversion_value}

    def calculate_last_touch(
        self, touchpoints: List[Touchpoint], conversion_value: float
    ) -> Dict[int, float]:
        """
        Last-touch attribution: 100% credit to last touchpoint.

        Args:
            touchpoints: List of touchpoints in journey
            conversion_value: Value of conversion

        Returns:
            Dictionary mapping channel_id to attribution credit
        """
        if not touchpoints:
            return {}

        # Sort by position to ensure we get the last touchpoint
        sorted_touchpoints = sorted(touchpoints, key=lambda t: t.position_in_journey)
        last_touchpoint = sorted_touchpoints[-1]

        return {last_touchpoint.channel_id: conversion_value}

    def calculate_linear(
        self, touchpoints: List[Touchpoint], conversion_value: float
    ) -> Dict[int, float]:
        """
        Linear attribution: Equal credit to all touchpoints.

        Args:
            touchpoints: List of touchpoints in journey
            conversion_value: Value of conversion

        Returns:
            Dictionary mapping channel_id to attribution credit
        """
        if not touchpoints:
            return {}

        # Calculate equal credit for each touchpoint
        credit_per_touchpoint = conversion_value / len(touchpoints)

        # Aggregate credit by channel
        channel_credits: Dict[int, float] = {}
        for touchpoint in touchpoints:
            channel_id = touchpoint.channel_id
            channel_credits[channel_id] = (
                channel_credits.get(channel_id, 0.0) + credit_per_touchpoint
            )

        return channel_credits

    def calculate_time_decay(
        self,
        touchpoints: List[Touchpoint],
        conversion_value: float,
        halflife_days: float = 7.0,
    ) -> Dict[int, float]:
        """
        Time-decay attribution: More recent touchpoints get more credit.

        Uses exponential decay: credit = exp(-lambda * time_difference)
        where lambda = ln(2) / halflife

        Args:
            touchpoints: List of touchpoints in journey
            conversion_value: Value of conversion
            halflife_days: Half-life period in days

        Returns:
            Dictionary mapping channel_id to attribution credit
        """
        if not touchpoints:
            return {}

        # Sort by timestamp
        sorted_touchpoints = sorted(touchpoints, key=lambda t: t.timestamp)

        # Get conversion time (time of last touchpoint)
        conversion_time = sorted_touchpoints[-1].timestamp

        # Calculate decay rate
        decay_rate = math.log(2) / halflife_days

        # Calculate weights using exponential decay
        weights: List[float] = []
        for touchpoint in sorted_touchpoints:
            time_diff_days = (conversion_time - touchpoint.timestamp).total_seconds() / 86400
            weight = math.exp(-decay_rate * time_diff_days)
            weights.append(weight)

        # Normalize weights to sum to 1
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]

        # Calculate attribution credit by channel
        channel_credits: Dict[int, float] = {}
        for touchpoint, weight in zip(sorted_touchpoints, normalized_weights):
            channel_id = touchpoint.channel_id
            credit = conversion_value * weight
            channel_credits[channel_id] = channel_credits.get(channel_id, 0.0) + credit

        return channel_credits

    def calculate_position_based(
        self,
        touchpoints: List[Touchpoint],
        conversion_value: float,
        weights: Optional[Dict[str, float]] = None,
    ) -> Dict[int, float]:
        """
        Position-based attribution (U-shaped): More credit to first and last touchpoints.

        Default: 40% first, 40% last, 20% distributed among middle touchpoints.

        Args:
            touchpoints: List of touchpoints in journey
            conversion_value: Value of conversion
            weights: Custom weights dict with keys: first, middle, last

        Returns:
            Dictionary mapping channel_id to attribution credit
        """
        if not touchpoints:
            return {}

        # Default weights (40-20-40 model)
        if weights is None:
            weights = {"first": 0.4, "middle": 0.2, "last": 0.4}

        # Sort by position
        sorted_touchpoints = sorted(touchpoints, key=lambda t: t.position_in_journey)

        if len(sorted_touchpoints) == 1:
            # Only one touchpoint gets 100%
            return {sorted_touchpoints[0].channel_id: conversion_value}

        if len(sorted_touchpoints) == 2:
            # First and last split the credit
            first_credit = conversion_value * weights["first"]
            last_credit = conversion_value * weights["last"]
            return {
                sorted_touchpoints[0].channel_id: first_credit,
                sorted_touchpoints[1].channel_id: last_credit,
            }

        # More than 2 touchpoints
        first_credit = conversion_value * weights["first"]
        last_credit = conversion_value * weights["last"]
        middle_total_credit = conversion_value * weights["middle"]

        # Distribute middle credit equally among middle touchpoints
        middle_touchpoints = sorted_touchpoints[1:-1]
        middle_credit_each = middle_total_credit / len(middle_touchpoints)

        # Aggregate credit by channel
        channel_credits: Dict[int, float] = {}

        # First touchpoint
        first_channel = sorted_touchpoints[0].channel_id
        channel_credits[first_channel] = (
            channel_credits.get(first_channel, 0.0) + first_credit
        )

        # Middle touchpoints
        for touchpoint in middle_touchpoints:
            channel_id = touchpoint.channel_id
            channel_credits[channel_id] = (
                channel_credits.get(channel_id, 0.0) + middle_credit_each
            )

        # Last touchpoint
        last_channel = sorted_touchpoints[-1].channel_id
        channel_credits[last_channel] = (
            channel_credits.get(last_channel, 0.0) + last_credit
        )

        return channel_credits


class AttributionService:
    """Service for attribution analysis and management."""

    def __init__(self, db: Session):
        """
        Initialize attribution service.

        Args:
            db: Database session
        """
        self.db = db
        self.calculator = AttributionCalculator(db)

    # ========================================================================
    # Journey Management
    # ========================================================================

    def create_journey(
        self, user_id: str, session_id: Optional[str] = None, **kwargs
    ) -> Journey:
        """
        Create a new customer journey.

        Args:
            user_id: User identifier
            session_id: Session identifier
            **kwargs: Additional journey attributes

        Returns:
            Created journey
        """
        journey = Journey(
            user_id=user_id,
            session_id=session_id,
            start_time=kwargs.get("start_time", datetime.utcnow()),
            **kwargs,
        )
        self.db.add(journey)
        self.db.commit()
        self.db.refresh(journey)
        return journey

    def get_journey(self, journey_id: int) -> Journey:
        """
        Get journey by ID.

        Args:
            journey_id: Journey ID

        Returns:
            Journey object

        Raises:
            NotFoundException: If journey not found
        """
        journey = self.db.query(Journey).filter(Journey.id == journey_id).first()
        if not journey:
            raise NotFoundException(f"Journey {journey_id} not found")
        return journey

    def add_touchpoint(
        self,
        journey_id: int,
        channel_id: int,
        touchpoint_type: str,
        **kwargs,
    ) -> Touchpoint:
        """
        Add touchpoint to journey.

        Args:
            journey_id: Journey ID
            channel_id: Channel ID
            touchpoint_type: Type of touchpoint
            **kwargs: Additional touchpoint attributes

        Returns:
            Created touchpoint
        """
        # Get journey to calculate position
        journey = self.get_journey(journey_id)

        # Calculate position
        position = journey.total_touchpoints + 1

        touchpoint = Touchpoint(
            journey_id=journey_id,
            channel_id=channel_id,
            touchpoint_type=touchpoint_type,
            position_in_journey=position,
            timestamp=kwargs.get("timestamp", datetime.utcnow()),
            **kwargs,
        )

        # Update journey touchpoint count
        journey.total_touchpoints = position

        self.db.add(touchpoint)
        self.db.commit()
        self.db.refresh(touchpoint)

        return touchpoint

    def add_conversion(
        self, journey_id: int, conversion_type: str, revenue: float, **kwargs
    ) -> Conversion:
        """
        Add conversion to journey.

        Args:
            journey_id: Journey ID
            conversion_type: Type of conversion
            revenue: Revenue amount
            **kwargs: Additional conversion attributes

        Returns:
            Created conversion
        """
        journey = self.get_journey(journey_id)

        conversion = Conversion(
            journey_id=journey_id,
            conversion_type=conversion_type,
            revenue=revenue,
            timestamp=kwargs.get("timestamp", datetime.utcnow()),
            **kwargs,
        )

        # Update journey conversion status
        journey.has_conversion = True
        journey.conversion_value += revenue
        if not journey.end_time:
            journey.end_time = conversion.timestamp

        # Calculate journey duration
        if journey.end_time and journey.start_time:
            duration = journey.end_time - journey.start_time
            journey.journey_duration_minutes = int(duration.total_seconds() / 60)

        self.db.add(conversion)
        self.db.commit()
        self.db.refresh(conversion)

        return conversion

    # ========================================================================
    # Attribution Calculation
    # ========================================================================

    def calculate_attribution(
        self, journey_id: int, model_id: int
    ) -> List[AttributionResult]:
        """
        Calculate attribution for a journey using specified model.

        Args:
            journey_id: Journey ID
            model_id: Attribution model ID

        Returns:
            List of attribution results

        Raises:
            NotFoundException: If journey or model not found
            AttributionException: If calculation fails
        """
        # Get journey
        journey = self.get_journey(journey_id)

        # Check if journey has conversion
        if not journey.has_conversion or journey.conversion_value == 0:
            raise AttributionException(
                "Cannot calculate attribution for journey without conversion",
                details={"journey_id": journey_id},
            )

        # Get attribution model
        model = (
            self.db.query(AttributionModel)
            .filter(AttributionModel.id == model_id)
            .first()
        )
        if not model:
            raise NotFoundException(f"Attribution model {model_id} not found")

        # Get touchpoints
        touchpoints = (
            self.db.query(Touchpoint)
            .filter(Touchpoint.journey_id == journey_id)
            .all()
        )

        if not touchpoints:
            raise AttributionException(
                "Cannot calculate attribution for journey without touchpoints",
                details={"journey_id": journey_id},
            )

        # Calculate attribution based on model type
        channel_credits = self._calculate_by_model_type(
            model, touchpoints, journey.conversion_value
        )

        # Create attribution results
        results = []
        for channel_id, credit in channel_credits.items():
            # Get channel cost
            channel_cost = sum(
                tp.cost for tp in touchpoints if tp.channel_id == channel_id
            )

            # Calculate ROI and ROAS
            roi = None
            roas = None
            if channel_cost > 0:
                roi = ((credit - channel_cost) / channel_cost) * 100
                roas = credit / channel_cost

            result = AttributionResult(
                journey_id=journey_id,
                attribution_model_id=model_id,
                channel_id=channel_id,
                credit=credit / journey.conversion_value,  # Normalized credit (0-1)
                attributed_revenue=credit,
                attributed_conversions=1.0,  # Each journey has 1 conversion
                channel_cost=channel_cost,
                roi=roi,
                roas=roas,
                calculated_at=datetime.utcnow(),
            )
            results.append(result)

        # Save results
        self.db.add_all(results)
        self.db.commit()

        return results

    def _calculate_by_model_type(
        self,
        model: AttributionModel,
        touchpoints: List[Touchpoint],
        conversion_value: float,
    ) -> Dict[int, float]:
        """
        Calculate attribution based on model type.

        Args:
            model: Attribution model
            touchpoints: List of touchpoints
            conversion_value: Conversion value

        Returns:
            Dictionary mapping channel_id to credit
        """
        if model.model_type == AttributionModelType.FIRST_TOUCH:
            return self.calculator.calculate_first_touch(touchpoints, conversion_value)

        elif model.model_type == AttributionModelType.LAST_TOUCH:
            return self.calculator.calculate_last_touch(touchpoints, conversion_value)

        elif model.model_type == AttributionModelType.LINEAR:
            return self.calculator.calculate_linear(touchpoints, conversion_value)

        elif model.model_type == AttributionModelType.TIME_DECAY:
            halflife = model.time_decay_halflife_days or 7.0
            return self.calculator.calculate_time_decay(
                touchpoints, conversion_value, halflife
            )

        elif model.model_type == AttributionModelType.POSITION_BASED:
            return self.calculator.calculate_position_based(
                touchpoints, conversion_value, model.position_weights
            )

        else:
            raise AttributionException(
                f"Unsupported attribution model type: {model.model_type}"
            )

    def calculate_bulk_attribution(
        self, journey_ids: List[int], model_ids: List[int]
    ) -> Dict[str, List[AttributionResult]]:
        """
        Calculate attribution for multiple journeys and models.

        Args:
            journey_ids: List of journey IDs
            model_ids: List of model IDs

        Returns:
            Dictionary with results organized by model
        """
        results_by_model: Dict[str, List[AttributionResult]] = {}

        for model_id in model_ids:
            model_results = []
            for journey_id in journey_ids:
                try:
                    results = self.calculate_attribution(journey_id, model_id)
                    model_results.extend(results)
                except (NotFoundException, AttributionException) as e:
                    # Log error but continue with other journeys
                    print(f"Error calculating attribution: {e}")
                    continue

            results_by_model[str(model_id)] = model_results

        return results_by_model

    # ========================================================================
    # Channel Management
    # ========================================================================

    def create_channel(self, name: str, channel_type: str, **kwargs) -> Channel:
        """Create a new marketing channel."""
        channel = Channel(name=name, channel_type=channel_type, **kwargs)
        self.db.add(channel)
        self.db.commit()
        self.db.refresh(channel)
        return channel

    def get_channel(self, channel_id: int) -> Channel:
        """Get channel by ID."""
        channel = self.db.query(Channel).filter(Channel.id == channel_id).first()
        if not channel:
            raise NotFoundException(f"Channel {channel_id} not found")
        return channel

    def list_channels(
        self, active_only: bool = True, skip: int = 0, limit: int = 100
    ) -> List[Channel]:
        """List all channels."""
        query = self.db.query(Channel)
        if active_only:
            query = query.filter(Channel.is_active == True)
        return query.offset(skip).limit(limit).all()

    # ========================================================================
    # Attribution Model Management
    # ========================================================================

    def create_attribution_model(
        self, name: str, model_type: str, **kwargs
    ) -> AttributionModel:
        """Create a new attribution model."""
        model = AttributionModel(name=name, model_type=model_type, **kwargs)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def get_attribution_model(self, model_id: int) -> AttributionModel:
        """Get attribution model by ID."""
        model = (
            self.db.query(AttributionModel)
            .filter(AttributionModel.id == model_id)
            .first()
        )
        if not model:
            raise NotFoundException(f"Attribution model {model_id} not found")
        return model

    def list_attribution_models(
        self, active_only: bool = True, skip: int = 0, limit: int = 100
    ) -> List[AttributionModel]:
        """List all attribution models."""
        query = self.db.query(AttributionModel)
        if active_only:
            query = query.filter(AttributionModel.is_active == True)
        return query.offset(skip).limit(limit).all()
