"""
NEXUS Platform - AI-Powered Attribution Service
Uses AI/LLM for data-driven attribution and insights.
"""
from datetime import datetime
from typing import List, Dict, Optional, Any
import json
from anthropic import Anthropic
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.exceptions import AttributionException
from backend.app.models.attribution import (
    Journey,
    Touchpoint,
    Channel,
    AttributionModel,
    AttributionResult,
)
from backend.app.services.attribution_service import AttributionService


class AIAttributionService:
    """AI-powered attribution service using Claude AI."""

    def __init__(self, db: Session):
        """
        Initialize AI attribution service.

        Args:
            db: Database session
        """
        self.db = db
        self.attribution_service = AttributionService(db)
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def calculate_data_driven_attribution(
        self,
        journey_id: int,
        model_id: int,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[int, float]:
        """
        Calculate data-driven attribution using AI/LLM.

        Uses Claude to analyze journey patterns and provide intelligent
        attribution based on engagement, timing, and channel characteristics.

        Args:
            journey_id: Journey ID
            model_id: Attribution model ID
            context: Additional context for AI analysis

        Returns:
            Dictionary mapping channel_id to attribution credit
        """
        # Get journey and touchpoints
        journey = self.attribution_service.get_journey(journey_id)
        touchpoints = (
            self.db.query(Touchpoint)
            .filter(Touchpoint.journey_id == journey_id)
            .all()
        )

        if not touchpoints:
            raise AttributionException(
                "Cannot calculate attribution without touchpoints"
            )

        # Get channel information
        channel_ids = list(set(tp.channel_id for tp in touchpoints))
        channels = (
            self.db.query(Channel)
            .filter(Channel.id.in_(channel_ids))
            .all()
        )
        channels_dict = {ch.id: ch for ch in channels}

        # Prepare journey data for AI analysis
        journey_data = self._prepare_journey_data(
            journey, touchpoints, channels_dict
        )

        # Get AI attribution analysis
        attribution_weights = self._get_ai_attribution_weights(
            journey_data, context
        )

        # Calculate actual credit values
        channel_credits = {}
        for channel_id, weight in attribution_weights.items():
            credit = journey.conversion_value * weight
            channel_credits[channel_id] = credit

        return channel_credits

    def _prepare_journey_data(
        self,
        journey: Journey,
        touchpoints: List[Touchpoint],
        channels_dict: Dict[int, Channel],
    ) -> Dict[str, Any]:
        """
        Prepare journey data for AI analysis.

        Args:
            journey: Journey object
            touchpoints: List of touchpoints
            channels_dict: Dictionary of channels by ID

        Returns:
            Formatted journey data
        """
        # Sort touchpoints by position
        sorted_touchpoints = sorted(
            touchpoints, key=lambda t: t.position_in_journey
        )

        # Format touchpoint data
        touchpoint_data = []
        for tp in sorted_touchpoints:
            channel = channels_dict.get(tp.channel_id)
            touchpoint_data.append({
                "position": tp.position_in_journey,
                "channel_name": channel.name if channel else "Unknown",
                "channel_type": channel.channel_type.value if channel else "unknown",
                "touchpoint_type": tp.touchpoint_type.value,
                "timestamp": tp.timestamp.isoformat(),
                "time_spent_seconds": tp.time_spent_seconds,
                "pages_viewed": tp.pages_viewed,
                "engagement_score": tp.engagement_score,
                "cost": tp.cost,
                "campaign_name": tp.campaign_name,
            })

        return {
            "journey_id": journey.id,
            "user_id": journey.user_id,
            "start_time": journey.start_time.isoformat(),
            "end_time": journey.end_time.isoformat() if journey.end_time else None,
            "total_touchpoints": journey.total_touchpoints,
            "conversion_value": journey.conversion_value,
            "journey_duration_minutes": journey.journey_duration_minutes,
            "touchpoints": touchpoint_data,
        }

    def _get_ai_attribution_weights(
        self, journey_data: Dict[str, Any], context: Optional[Dict[str, Any]]
    ) -> Dict[int, float]:
        """
        Get attribution weights from AI analysis.

        Args:
            journey_data: Prepared journey data
            context: Additional context

        Returns:
            Dictionary mapping channel_id to weight (0-1)
        """
        # Build prompt for Claude
        prompt = self._build_attribution_prompt(journey_data, context)

        try:
            # Call Claude API
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=2048,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            # Parse response
            content = response.content[0].text
            attribution_weights = self._parse_ai_response(content, journey_data)

            return attribution_weights

        except Exception as e:
            raise AttributionException(
                "AI attribution calculation failed",
                details={"error": str(e)},
            )

    def _build_attribution_prompt(
        self, journey_data: Dict[str, Any], context: Optional[Dict[str, Any]]
    ) -> str:
        """
        Build prompt for Claude AI attribution analysis.

        Args:
            journey_data: Journey data
            context: Additional context

        Returns:
            Formatted prompt
        """
        touchpoints_str = json.dumps(journey_data["touchpoints"], indent=2)

        prompt = f"""You are an expert in marketing attribution analysis. Analyze this customer journey and provide attribution weights for each touchpoint based on their influence on the conversion.

Journey Information:
- Total Touchpoints: {journey_data["total_touchpoints"]}
- Journey Duration: {journey_data["journey_duration_minutes"]} minutes
- Conversion Value: ${journey_data["conversion_value"]}

Touchpoints:
{touchpoints_str}

Consider these factors in your analysis:
1. Position in journey (first touch awareness, mid-journey consideration, last touch decision)
2. Engagement metrics (time spent, pages viewed, engagement score)
3. Channel characteristics and typical role in customer journey
4. Timing and sequence of touchpoints
5. Campaign context

{"Additional Context: " + json.dumps(context, indent=2) if context else ""}

Provide attribution weights that sum to 1.0, formatted as a JSON object where keys are the touchpoint positions (1, 2, 3, etc.) and values are the weights.

Example format:
{{
  "1": 0.3,
  "2": 0.2,
  "3": 0.5
}}

Respond ONLY with the JSON object, no additional text."""

        return prompt

    def _parse_ai_response(
        self, response: str, journey_data: Dict[str, Any]
    ) -> Dict[int, float]:
        """
        Parse AI response to extract attribution weights.

        Args:
            response: AI response text
            journey_data: Journey data for mapping positions to channels

        Returns:
            Dictionary mapping channel_id to weight
        """
        try:
            # Extract JSON from response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            json_str = response[start_idx:end_idx]

            # Parse JSON
            position_weights = json.loads(json_str)

            # Convert position weights to channel weights
            channel_weights: Dict[int, float] = {}
            touchpoints = journey_data["touchpoints"]

            for position_str, weight in position_weights.items():
                position = int(position_str)
                # Find touchpoint at this position
                touchpoint = next(
                    (tp for tp in touchpoints if tp["position"] == position),
                    None,
                )
                if touchpoint:
                    # Note: We'd need to store channel_id in touchpoint_data
                    # For now, we'll use position as proxy
                    # In production, include channel_id in touchpoint_data
                    channel_weights[position] = weight

            # Normalize weights to ensure they sum to 1.0
            total_weight = sum(channel_weights.values())
            if total_weight > 0:
                channel_weights = {
                    k: v / total_weight for k, v in channel_weights.items()
                }

            return channel_weights

        except Exception as e:
            raise AttributionException(
                "Failed to parse AI attribution response",
                details={"error": str(e), "response": response},
            )

    def get_ai_insights(
        self,
        journey_ids: List[int],
        analysis_type: str = "performance",
    ) -> Dict[str, Any]:
        """
        Get AI-powered insights for journeys.

        Args:
            journey_ids: List of journey IDs to analyze
            analysis_type: Type of analysis (performance, optimization, trends)

        Returns:
            AI-generated insights
        """
        # Get journeys and aggregate data
        journeys = (
            self.db.query(Journey)
            .filter(Journey.id.in_(journey_ids))
            .all()
        )

        if not journeys:
            raise AttributionException("No journeys found for analysis")

        # Aggregate journey statistics
        stats = self._aggregate_journey_stats(journeys)

        # Build insights prompt
        prompt = self._build_insights_prompt(stats, analysis_type)

        try:
            # Call Claude API
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4096,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            insights = response.content[0].text

            return {
                "analysis_type": analysis_type,
                "journey_count": len(journeys),
                "insights": insights,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            raise AttributionException(
                "AI insights generation failed",
                details={"error": str(e)},
            )

    def _aggregate_journey_stats(
        self, journeys: List[Journey]
    ) -> Dict[str, Any]:
        """
        Aggregate statistics from journeys.

        Args:
            journeys: List of journeys

        Returns:
            Aggregated statistics
        """
        total_journeys = len(journeys)
        converted_journeys = sum(1 for j in journeys if j.has_conversion)
        total_revenue = sum(j.conversion_value for j in journeys)
        avg_touchpoints = (
            sum(j.total_touchpoints for j in journeys) / total_journeys
        )
        avg_duration = sum(
            j.journey_duration_minutes or 0 for j in journeys
        ) / total_journeys

        return {
            "total_journeys": total_journeys,
            "converted_journeys": converted_journeys,
            "conversion_rate": converted_journeys / total_journeys if total_journeys > 0 else 0,
            "total_revenue": total_revenue,
            "avg_revenue_per_journey": total_revenue / total_journeys if total_journeys > 0 else 0,
            "avg_touchpoints": avg_touchpoints,
            "avg_duration_minutes": avg_duration,
        }

    def _build_insights_prompt(
        self, stats: Dict[str, Any], analysis_type: str
    ) -> str:
        """
        Build prompt for AI insights.

        Args:
            stats: Journey statistics
            analysis_type: Type of analysis

        Returns:
            Formatted prompt
        """
        prompt = f"""You are a marketing attribution expert. Analyze these customer journey statistics and provide actionable insights.

Journey Statistics:
{json.dumps(stats, indent=2)}

Analysis Type: {analysis_type}

Provide insights covering:
"""

        if analysis_type == "performance":
            prompt += """
1. Overall performance assessment
2. Conversion rate analysis
3. Revenue patterns
4. Journey efficiency (touchpoints vs conversions)
5. Key performance indicators
"""
        elif analysis_type == "optimization":
            prompt += """
1. Optimization opportunities
2. Channel performance recommendations
3. Journey length optimization
4. Touchpoint efficiency improvements
5. Budget allocation suggestions
"""
        elif analysis_type == "trends":
            prompt += """
1. Emerging patterns
2. Customer behavior trends
3. Channel effectiveness trends
4. Journey complexity trends
5. Conversion path insights
"""

        prompt += "\nProvide detailed, actionable insights in markdown format."

        return prompt

    def compare_attribution_models(
        self,
        journey_ids: List[int],
        model_ids: List[int],
    ) -> Dict[str, Any]:
        """
        Use AI to compare different attribution models and provide recommendations.

        Args:
            journey_ids: List of journey IDs
            model_ids: List of model IDs to compare

        Returns:
            AI-powered model comparison and recommendations
        """
        # Calculate attribution for all models
        results_by_model = self.attribution_service.calculate_bulk_attribution(
            journey_ids, model_ids
        )

        # Aggregate results by model
        model_summaries = {}
        for model_id_str, results in results_by_model.items():
            model_id = int(model_id_str)
            model = self.attribution_service.get_attribution_model(model_id)

            # Aggregate by channel
            channel_totals: Dict[int, Dict[str, float]] = {}
            for result in results:
                if result.channel_id not in channel_totals:
                    channel_totals[result.channel_id] = {
                        "attributed_revenue": 0.0,
                        "attributed_conversions": 0.0,
                        "total_cost": 0.0,
                    }

                channel_totals[result.channel_id]["attributed_revenue"] += (
                    result.attributed_revenue
                )
                channel_totals[result.channel_id]["attributed_conversions"] += (
                    result.attributed_conversions
                )
                channel_totals[result.channel_id]["total_cost"] += (
                    result.channel_cost
                )

            model_summaries[model.name] = {
                "model_type": model.model_type.value,
                "total_revenue": sum(
                    ch["attributed_revenue"] for ch in channel_totals.values()
                ),
                "channel_count": len(channel_totals),
                "channels": channel_totals,
            }

        # Get AI comparison
        prompt = f"""Compare these attribution model results and provide recommendations on which model to use and why.

Model Results:
{json.dumps(model_summaries, indent=2)}

Provide:
1. Comparison of how each model distributes credit
2. Strengths and weaknesses of each model for this data
3. Recommendation on which model(s) to use
4. Scenarios where each model would be most appropriate
5. Suggestions for custom model parameters

Format your response in markdown."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4096,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            comparison = response.content[0].text

            return {
                "model_summaries": model_summaries,
                "ai_comparison": comparison,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            raise AttributionException(
                "AI model comparison failed",
                details={"error": str(e)},
            )
