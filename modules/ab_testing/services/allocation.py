"""Traffic allocation service for variant assignment."""

import hashlib
import random
from typing import Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.ab_testing.models import (
    Experiment,
    ExperimentStatus,
    Participant,
    ParticipantVariant,
    Variant,
)


class TrafficAllocator:
    """
    Traffic allocation service for assigning participants to variants.

    Uses deterministic hashing to ensure consistent variant assignment
    for the same participant across multiple visits.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize traffic allocator.

        Args:
            db: Database session
        """
        self.db = db

    async def assign_variant(
        self,
        experiment_id: int,
        participant_id: str,
        properties: Optional[dict] = None,
    ) -> Optional[Variant]:
        """
        Assign a participant to a variant in an experiment.

        Uses consistent hashing to ensure the same participant always
        gets the same variant.

        Args:
            experiment_id: ID of the experiment
            participant_id: Unique identifier for the participant
            properties: Optional participant properties for segment targeting

        Returns:
            Variant: Assigned variant or None if assignment failed

        Raises:
            ValueError: If experiment is not active or has no variants

        Example:
            >>> allocator = TrafficAllocator(db)
            >>> variant = await allocator.assign_variant(
            ...     experiment_id=1,
            ...     participant_id="user_123",
            ...     properties={"country": "US", "age": 25}
            ... )
            >>> print(f"Assigned to: {variant.name}")
        """
        logger.info(
            f"Assigning participant {participant_id} to experiment {experiment_id}"
        )

        # Check if participant already has an assignment
        result = await self.db.execute(
            select(ParticipantVariant)
            .where(ParticipantVariant.experiment_id == experiment_id)
            .where(ParticipantVariant.participant_id == participant_id)
        )
        existing_assignment = result.scalar_one_or_none()

        if existing_assignment:
            logger.info(
                f"Participant {participant_id} already assigned to variant "
                f"{existing_assignment.variant_id}"
            )
            result = await self.db.execute(
                select(Variant).where(Variant.id == existing_assignment.variant_id)
            )
            return result.scalar_one_or_none()

        # Get experiment
        result = await self.db.execute(
            select(Experiment).where(Experiment.id == experiment_id)
        )
        experiment = result.scalar_one_or_none()

        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        if experiment.status != ExperimentStatus.RUNNING:
            raise ValueError(f"Experiment {experiment_id} is not running")

        # Get variants
        result = await self.db.execute(
            select(Variant).where(Variant.experiment_id == experiment_id)
        )
        variants = list(result.scalars().all())

        if not variants:
            raise ValueError(f"Experiment {experiment_id} has no variants")

        # Check if participant should be included in experiment (traffic allocation)
        if not self._should_participate(
            participant_id, experiment_id, experiment.traffic_allocation
        ):
            logger.info(
                f"Participant {participant_id} excluded from experiment "
                f"due to traffic allocation"
            )
            return None

        # Check segment targeting
        if experiment.segments and properties:
            if not await self._matches_segments(experiment, properties):
                logger.info(
                    f"Participant {participant_id} does not match segment criteria"
                )
                return None

        # Select variant using weighted random selection with consistent hashing
        selected_variant = self._select_variant_deterministic(
            participant_id, experiment_id, variants
        )

        # Create or get participant
        result = await self.db.execute(
            select(Participant).where(
                Participant.participant_id == participant_id
            )
        )
        participant = result.scalar_one_or_none()

        if not participant:
            participant = Participant(
                participant_id=participant_id,
                properties=properties,
            )
            self.db.add(participant)
            await self.db.flush()

        # Create assignment
        assignment = ParticipantVariant(
            experiment_id=experiment_id,
            participant_id=participant_id,
            variant_id=selected_variant.id,
            metadata=properties,
        )
        self.db.add(assignment)
        await self.db.commit()

        logger.info(
            f"Assigned participant {participant_id} to variant "
            f"{selected_variant.id} ({selected_variant.name})"
        )

        return selected_variant

    def _should_participate(
        self,
        participant_id: str,
        experiment_id: int,
        traffic_allocation: float,
    ) -> bool:
        """
        Determine if participant should be included based on traffic allocation.

        Args:
            participant_id: Participant identifier
            experiment_id: Experiment ID
            traffic_allocation: Percentage of traffic to include (0.0-1.0)

        Returns:
            bool: True if participant should be included
        """
        if traffic_allocation >= 1.0:
            return True

        # Use consistent hashing to determine inclusion
        hash_input = f"{participant_id}:{experiment_id}:traffic"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        threshold = hash_value / (2**128)

        return threshold < traffic_allocation

    def _select_variant_deterministic(
        self,
        participant_id: str,
        experiment_id: int,
        variants: list[Variant],
    ) -> Variant:
        """
        Select variant using deterministic weighted random selection.

        Uses consistent hashing to ensure same participant always gets
        same variant.

        Args:
            participant_id: Participant identifier
            experiment_id: Experiment ID
            variants: List of available variants

        Returns:
            Variant: Selected variant
        """
        # Calculate total weight
        total_weight = sum(v.traffic_weight for v in variants)

        # Generate deterministic hash
        hash_input = f"{participant_id}:{experiment_id}:variant"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)

        # Convert hash to value in range [0, 1)
        random_value = (hash_value / (2**128)) * total_weight

        # Select variant based on cumulative weights
        cumulative_weight = 0.0
        for variant in variants:
            cumulative_weight += variant.traffic_weight
            if random_value < cumulative_weight:
                return variant

        # Fallback to last variant (should not happen)
        return variants[-1]

    async def _matches_segments(
        self,
        experiment: Experiment,
        properties: dict,
    ) -> bool:
        """
        Check if participant properties match experiment segment criteria.

        Args:
            experiment: Experiment with segments
            properties: Participant properties

        Returns:
            bool: True if participant matches all segments
        """
        if not experiment.segments:
            return True

        for segment in experiment.segments:
            # All conditions in a segment must be met (AND logic)
            for condition in segment.conditions:
                if not condition.evaluate(properties):
                    return False

        return True

    async def get_assignment(
        self,
        experiment_id: int,
        participant_id: str,
    ) -> Optional[Variant]:
        """
        Get existing variant assignment for a participant.

        Args:
            experiment_id: Experiment ID
            participant_id: Participant identifier

        Returns:
            Variant: Assigned variant or None if not assigned
        """
        result = await self.db.execute(
            select(ParticipantVariant)
            .where(ParticipantVariant.experiment_id == experiment_id)
            .where(ParticipantVariant.participant_id == participant_id)
        )
        assignment = result.scalar_one_or_none()

        if not assignment:
            return None

        result = await self.db.execute(
            select(Variant).where(Variant.id == assignment.variant_id)
        )
        return result.scalar_one_or_none()
