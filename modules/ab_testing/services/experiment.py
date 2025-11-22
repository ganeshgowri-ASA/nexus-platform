"""Experiment service for managing A/B tests."""

from datetime import datetime
from typing import Optional

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from modules.ab_testing.core.statistics import StatisticalAnalyzer, VariantData
from modules.ab_testing.models import (
    Experiment,
    ExperimentStatus,
    Metric,
    MetricEvent,
    ParticipantVariant,
    Variant,
)
from modules.ab_testing.schemas.experiment import (
    ExperimentCreate,
    ExperimentStats,
    ExperimentUpdate,
)


class ExperimentService:
    """Service for managing experiments and analyzing results."""

    def __init__(self, db: AsyncSession):
        """
        Initialize experiment service.

        Args:
            db: Database session
        """
        self.db = db
        self.analyzer = StatisticalAnalyzer()

    async def create_experiment(
        self,
        data: ExperimentCreate,
    ) -> Experiment:
        """
        Create a new experiment.

        Args:
            data: Experiment creation data

        Returns:
            Experiment: Created experiment

        Example:
            >>> service = ExperimentService(db)
            >>> data = ExperimentCreate(
            ...     name="Homepage CTA Test",
            ...     description="Testing different CTA button colors",
            ...     hypothesis="Red button will increase conversions by 10%"
            ... )
            >>> experiment = await service.create_experiment(data)
        """
        logger.info(f"Creating experiment: {data.name}")

        experiment = Experiment(
            name=data.name,
            description=data.description,
            hypothesis=data.hypothesis,
            type=data.type,
            target_sample_size=data.target_sample_size,
            confidence_level=data.confidence_level,
            traffic_allocation=data.traffic_allocation,
            auto_winner_enabled=data.auto_winner_enabled,
            metadata=data.metadata,
        )

        self.db.add(experiment)
        await self.db.commit()
        await self.db.refresh(experiment)

        logger.info(f"Created experiment {experiment.id}: {experiment.name}")
        return experiment

    async def update_experiment(
        self,
        experiment_id: int,
        data: ExperimentUpdate,
    ) -> Optional[Experiment]:
        """
        Update an existing experiment.

        Args:
            experiment_id: ID of experiment to update
            data: Update data

        Returns:
            Experiment: Updated experiment or None if not found
        """
        logger.info(f"Updating experiment {experiment_id}")

        result = await self.db.execute(
            select(Experiment).where(Experiment.id == experiment_id)
        )
        experiment = result.scalar_one_or_none()

        if not experiment:
            logger.warning(f"Experiment {experiment_id} not found")
            return None

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(experiment, field, value)

        await self.db.commit()
        await self.db.refresh(experiment)

        logger.info(f"Updated experiment {experiment_id}")
        return experiment

    async def start_experiment(self, experiment_id: int) -> Optional[Experiment]:
        """
        Start an experiment.

        Args:
            experiment_id: ID of experiment to start

        Returns:
            Experiment: Started experiment or None if not found

        Raises:
            ValueError: If experiment cannot be started
        """
        logger.info(f"Starting experiment {experiment_id}")

        result = await self.db.execute(
            select(Experiment)
            .options(selectinload(Experiment.variants))
            .where(Experiment.id == experiment_id)
        )
        experiment = result.scalar_one_or_none()

        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        if experiment.status != ExperimentStatus.DRAFT:
            raise ValueError(
                f"Cannot start experiment in status {experiment.status}"
            )

        if not experiment.variants or len(experiment.variants) < 2:
            raise ValueError("Experiment must have at least 2 variants")

        experiment.status = ExperimentStatus.RUNNING
        experiment.start_date = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(experiment)

        logger.info(f"Started experiment {experiment_id}")
        return experiment

    async def pause_experiment(self, experiment_id: int) -> Optional[Experiment]:
        """
        Pause a running experiment.

        Args:
            experiment_id: ID of experiment to pause

        Returns:
            Experiment: Paused experiment or None if not found
        """
        logger.info(f"Pausing experiment {experiment_id}")

        result = await self.db.execute(
            select(Experiment).where(Experiment.id == experiment_id)
        )
        experiment = result.scalar_one_or_none()

        if not experiment:
            return None

        if experiment.status != ExperimentStatus.RUNNING:
            raise ValueError(
                f"Cannot pause experiment in status {experiment.status}"
            )

        experiment.status = ExperimentStatus.PAUSED

        await self.db.commit()
        await self.db.refresh(experiment)

        logger.info(f"Paused experiment {experiment_id}")
        return experiment

    async def complete_experiment(self, experiment_id: int) -> Optional[Experiment]:
        """
        Complete an experiment.

        Args:
            experiment_id: ID of experiment to complete

        Returns:
            Experiment: Completed experiment or None if not found
        """
        logger.info(f"Completing experiment {experiment_id}")

        result = await self.db.execute(
            select(Experiment).where(Experiment.id == experiment_id)
        )
        experiment = result.scalar_one_or_none()

        if not experiment:
            return None

        experiment.status = ExperimentStatus.COMPLETED
        experiment.end_date = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(experiment)

        logger.info(f"Completed experiment {experiment_id}")
        return experiment

    async def get_experiment_stats(
        self,
        experiment_id: int,
    ) -> Optional[ExperimentStats]:
        """
        Get statistical analysis for an experiment.

        Args:
            experiment_id: ID of experiment

        Returns:
            ExperimentStats: Statistical analysis results

        Example:
            >>> stats = await service.get_experiment_stats(1)
            >>> print(f"Total participants: {stats.total_participants}")
            >>> print(f"Statistical significance: {stats.statistical_significance}")
        """
        logger.info(f"Calculating stats for experiment {experiment_id}")

        # Get experiment with relationships
        result = await self.db.execute(
            select(Experiment)
            .options(
                selectinload(Experiment.variants),
                selectinload(Experiment.metrics).selectinload(Metric.events),
            )
            .where(Experiment.id == experiment_id)
        )
        experiment = result.scalar_one_or_none()

        if not experiment:
            return None

        # Get total participants
        result = await self.db.execute(
            select(func.count(ParticipantVariant.id)).where(
                ParticipantVariant.experiment_id == experiment_id
            )
        )
        total_participants = result.scalar()

        # Calculate stats for each variant
        variant_stats = {}
        for variant in experiment.variants:
            result = await self.db.execute(
                select(func.count(ParticipantVariant.id)).where(
                    ParticipantVariant.variant_id == variant.id
                )
            )
            participant_count = result.scalar()

            variant_stats[variant.name] = {
                "id": variant.id,
                "participants": participant_count,
                "is_control": variant.is_control,
            }

        # Analyze primary metric if available
        primary_metric_results = None
        statistical_significance = None
        confidence_interval = None
        recommended_action = None

        primary_metric = next(
            (m for m in experiment.metrics if m.is_primary), None
        )

        if primary_metric and len(experiment.variants) >= 2:
            # Get conversion data for each variant
            variant_data_map = {}
            for variant in experiment.variants:
                result = await self.db.execute(
                    select(func.count(MetricEvent.id))
                    .where(MetricEvent.metric_id == primary_metric.id)
                    .where(MetricEvent.variant_id == variant.id)
                )
                conversions = result.scalar()

                result = await self.db.execute(
                    select(func.count(ParticipantVariant.id)).where(
                        ParticipantVariant.variant_id == variant.id
                    )
                )
                total = result.scalar()

                variant_data_map[variant.name] = VariantData(
                    name=variant.name,
                    conversions=conversions,
                    total=total,
                )

            # Perform statistical test between control and first treatment
            control = next(
                (v for v in variant_data_map.values() if v.name == "Control"),
                None,
            )
            treatment = next(
                (
                    v
                    for v in variant_data_map.values()
                    if v.name != "Control"
                ),
                None,
            )

            if control and treatment and control.total > 0 and treatment.total > 0:
                test_result = self.analyzer.z_test(
                    control,
                    treatment,
                    confidence_level=experiment.confidence_level,
                )

                primary_metric_results = {
                    "control_conversion_rate": control.conversion_rate,
                    "treatment_conversion_rate": treatment.conversion_rate,
                    "p_value": test_result.p_value,
                    "is_significant": test_result.is_significant,
                    "effect_size": test_result.effect_size,
                    "winner": test_result.winner,
                    "relative_improvement": test_result.relative_improvement,
                }

                statistical_significance = (
                    1 - test_result.p_value if test_result.is_significant else None
                )
                confidence_interval = {
                    "lower": test_result.confidence_interval[0],
                    "upper": test_result.confidence_interval[1],
                }

                # Provide recommendation
                if test_result.is_significant:
                    if test_result.winner:
                        recommended_action = (
                            f"Deploy {test_result.winner} variant - "
                            f"statistically significant improvement detected"
                        )
                    else:
                        recommended_action = "No significant difference - keep current implementation"
                else:
                    min_sample = experiment.target_sample_size
                    if control.total < min_sample or treatment.total < min_sample:
                        recommended_action = (
                            f"Continue test - need {min_sample} participants per variant"
                        )
                    else:
                        recommended_action = "No significant difference detected - consider ending test"

        return ExperimentStats(
            experiment_id=experiment_id,
            total_participants=total_participants,
            variant_stats=variant_stats,
            primary_metric_results=primary_metric_results,
            statistical_significance=statistical_significance,
            confidence_interval=confidence_interval,
            recommended_action=recommended_action,
        )

    async def check_auto_winner(self, experiment_id: int) -> Optional[Variant]:
        """
        Check if a winner can be automatically determined.

        Args:
            experiment_id: ID of experiment

        Returns:
            Variant: Winning variant or None if no winner yet
        """
        logger.info(f"Checking for auto winner in experiment {experiment_id}")

        result = await self.db.execute(
            select(Experiment)
            .options(selectinload(Experiment.variants))
            .where(Experiment.id == experiment_id)
        )
        experiment = result.scalar_one_or_none()

        if not experiment or not experiment.auto_winner_enabled:
            return None

        if experiment.winner_variant_id:
            logger.info(f"Winner already determined: {experiment.winner_variant_id}")
            result = await self.db.execute(
                select(Variant).where(Variant.id == experiment.winner_variant_id)
            )
            return result.scalar_one_or_none()

        # Get experiment stats
        stats = await self.get_experiment_stats(experiment_id)

        if not stats or not stats.primary_metric_results:
            return None

        # Check if we have a significant winner
        if (
            stats.primary_metric_results.get("is_significant")
            and stats.primary_metric_results.get("winner")
        ):
            # Find winning variant
            winner_name = stats.primary_metric_results["winner"]
            winning_variant = next(
                (v for v in experiment.variants if v.name == winner_name),
                None,
            )

            if winning_variant:
                experiment.winner_variant_id = winning_variant.id
                await self.db.commit()
                logger.info(
                    f"Auto-selected winner: {winning_variant.id} ({winner_name})"
                )
                return winning_variant

        return None
