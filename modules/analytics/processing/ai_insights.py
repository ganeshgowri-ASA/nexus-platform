"""
AI-Powered Analytics Insights

Claude AI integration for predictive insights, anomaly detection,
and automated analysis recommendations.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from anthropic import AsyncAnthropic

from shared.config import get_settings
from shared.logger import get_logger
from shared.utils import get_utc_now

logger = get_logger(__name__)
settings = get_settings()


class AIInsightsEngine:
    """
    AI-powered insights engine using Claude.

    Provides intelligent analysis of analytics data including:
    - Anomaly detection
    - Trend analysis
    - Predictive insights
    - Automated recommendations
    - Natural language explanations
    """

    def __init__(self) -> None:
        """Initialize AI insights engine."""
        self.client: Optional[AsyncAnthropic] = None
        if settings.ai.claude_api_key:
            self.client = AsyncAnthropic(api_key=settings.ai.claude_api_key)
        else:
            logger.warning("Claude API key not configured")

    async def detect_anomalies(
        self,
        metric_data: List[Dict[str, Any]],
        metric_name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Detect anomalies in metric data using AI.

        Args:
            metric_data: Time series metric data
            metric_name: Name of the metric
            context: Additional context information

        Returns:
            Dict containing anomalies and explanations

        Example:
            >>> engine = AIInsightsEngine()
            >>> data = [{"timestamp": "2024-01-15", "value": 1000}, ...]
            >>> result = await engine.detect_anomalies(data, "page_views")
        """
        if not self.client:
            return {"error": "AI insights not configured"}

        try:
            # Prepare data summary
            data_summary = self._prepare_data_summary(metric_data, metric_name)

            prompt = f"""Analyze this analytics metric data and detect any anomalies:

Metric: {metric_name}
Time Period: {data_summary['start_date']} to {data_summary['end_date']}
Data Points: {len(metric_data)}
Average Value: {data_summary['avg_value']:.2f}
Min Value: {data_summary['min_value']:.2f}
Max Value: {data_summary['max_value']:.2f}
Standard Deviation: {data_summary['std_dev']:.2f}

Recent Data Points:
{self._format_recent_data(metric_data[-20:])}

Additional Context:
{context or 'None provided'}

Please analyze this data and provide:
1. Any detected anomalies (unusual spikes, drops, or patterns)
2. Potential causes for each anomaly
3. Severity level (low, medium, high, critical)
4. Recommended actions
5. Overall data health assessment

Format your response as a structured analysis."""

            response = await self.client.messages.create(
                model=settings.ai.model,
                max_tokens=settings.ai.max_tokens,
                temperature=settings.ai.temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            analysis_text = response.content[0].text

            return {
                "metric_name": metric_name,
                "analysis": analysis_text,
                "data_summary": data_summary,
                "analyzed_at": get_utc_now().isoformat(),
                "model": settings.ai.model,
            }

        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}", exc_info=True)
            return {"error": str(e)}

    async def analyze_trends(
        self,
        metric_data: List[Dict[str, Any]],
        metric_name: str,
        period: str = "30d",
    ) -> Dict[str, Any]:
        """
        Analyze trends in metric data.

        Args:
            metric_data: Time series metric data
            metric_name: Name of the metric
            period: Analysis period

        Returns:
            Dict containing trend analysis and insights
        """
        if not self.client:
            return {"error": "AI insights not configured"}

        try:
            data_summary = self._prepare_data_summary(metric_data, metric_name)

            prompt = f"""Analyze the trend in this analytics metric:

Metric: {metric_name}
Period: {period}
Total Data Points: {len(metric_data)}

Summary Statistics:
- Average: {data_summary['avg_value']:.2f}
- Trend: {data_summary['trend']}
- Growth Rate: {data_summary.get('growth_rate', 0):.2f}%
- Volatility: {data_summary.get('volatility', 'unknown')}

Recent Trend Data:
{self._format_recent_data(metric_data[-30:])}

Please provide:
1. Overall trend direction and strength
2. Key inflection points
3. Seasonal patterns (if any)
4. Predicted next period values
5. Business insights and recommendations

Be concise but insightful."""

            response = await self.client.messages.create(
                model=settings.ai.model,
                max_tokens=settings.ai.max_tokens,
                temperature=settings.ai.temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            return {
                "metric_name": metric_name,
                "period": period,
                "trend_analysis": response.content[0].text,
                "data_summary": data_summary,
                "analyzed_at": get_utc_now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error analyzing trends: {e}", exc_info=True)
            return {"error": str(e)}

    async def generate_insights(
        self,
        analytics_data: Dict[str, Any],
        focus_areas: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive analytics insights.

        Args:
            analytics_data: Complete analytics data snapshot
            focus_areas: Specific areas to focus on

        Returns:
            Dict containing insights and recommendations
        """
        if not self.client:
            return {"error": "AI insights not configured"}

        try:
            prompt = f"""Analyze this analytics data and provide actionable insights:

Analytics Summary:
{self._format_analytics_summary(analytics_data)}

Focus Areas: {', '.join(focus_areas) if focus_areas else 'All areas'}

Please provide:
1. Key performance highlights
2. Areas of concern
3. Growth opportunities
4. User behavior insights
5. Specific action recommendations
6. Priority ranking for recommendations

Keep insights actionable and business-focused."""

            response = await self.client.messages.create(
                model=settings.ai.model,
                max_tokens=settings.ai.max_tokens,
                temperature=settings.ai.temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            return {
                "insights": response.content[0].text,
                "focus_areas": focus_areas,
                "generated_at": get_utc_now().isoformat(),
                "model": settings.ai.model,
            }

        except Exception as e:
            logger.error(f"Error generating insights: {e}", exc_info=True)
            return {"error": str(e)}

    async def explain_metric_change(
        self,
        metric_name: str,
        current_value: float,
        previous_value: float,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Explain why a metric changed.

        Args:
            metric_name: Name of the metric
            current_value: Current metric value
            previous_value: Previous metric value
            context: Additional context data

        Returns:
            Dict containing explanation and analysis
        """
        if not self.client:
            return {"error": "AI insights not configured"}

        try:
            change = current_value - previous_value
            change_pct = ((change / previous_value) * 100) if previous_value else 0

            prompt = f"""Explain this metric change:

Metric: {metric_name}
Previous Value: {previous_value:,.2f}
Current Value: {current_value:,.2f}
Change: {change:+,.2f} ({change_pct:+.1f}%)

Context:
{self._format_context(context)}

Please explain:
1. What this change means
2. Possible reasons for the change
3. Whether this is positive, negative, or neutral
4. What actions should be taken (if any)
5. What to monitor next

Be specific and actionable."""

            response = await self.client.messages.create(
                model=settings.ai.model,
                max_tokens=1024,
                temperature=settings.ai.temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            return {
                "metric_name": metric_name,
                "change": change,
                "change_percentage": change_pct,
                "explanation": response.content[0].text,
                "explained_at": get_utc_now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error explaining metric change: {e}", exc_info=True)
            return {"error": str(e)}

    async def recommend_optimizations(
        self,
        funnel_data: Dict[str, Any],
        goal_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Recommend optimization strategies.

        Args:
            funnel_data: Funnel performance data
            goal_data: Goal conversion data

        Returns:
            Dict containing optimization recommendations
        """
        if not self.client:
            return {"error": "AI insights not configured"}

        try:
            prompt = f"""Analyze this conversion data and recommend optimizations:

Funnel Performance:
{self._format_funnel_data(funnel_data)}

Goal Conversions:
{self._format_goal_data(goal_data)}

Please provide:
1. Biggest conversion bottlenecks
2. Quick wins for improvement
3. Long-term optimization strategies
4. A/B test ideas
5. Expected impact of each recommendation

Prioritize by potential impact and ease of implementation."""

            response = await self.client.messages.create(
                model=settings.ai.model,
                max_tokens=settings.ai.max_tokens,
                temperature=settings.ai.temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            return {
                "recommendations": response.content[0].text,
                "generated_at": get_utc_now().isoformat(),
                "model": settings.ai.model,
            }

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}", exc_info=True)
            return {"error": str(e)}

    def _prepare_data_summary(
        self, data: List[Dict[str, Any]], metric_name: str
    ) -> Dict[str, Any]:
        """Prepare statistical summary of data."""
        if not data:
            return {}

        values = [d.get("value", 0) for d in data]

        import statistics

        return {
            "metric_name": metric_name,
            "data_points": len(data),
            "avg_value": statistics.mean(values),
            "min_value": min(values),
            "max_value": max(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
            "trend": "increasing" if values[-1] > values[0] else "decreasing",
            "start_date": data[0].get("timestamp", "unknown"),
            "end_date": data[-1].get("timestamp", "unknown"),
        }

    def _format_recent_data(self, data: List[Dict[str, Any]]) -> str:
        """Format recent data points for prompt."""
        lines = []
        for d in data[-10:]:
            timestamp = d.get("timestamp", "unknown")
            value = d.get("value", 0)
            lines.append(f"  {timestamp}: {value:,.2f}")
        return "\n".join(lines)

    def _format_analytics_summary(self, data: Dict[str, Any]) -> str:
        """Format analytics data summary."""
        lines = []
        for key, value in data.items():
            if isinstance(value, (int, float)):
                lines.append(f"- {key}: {value:,.2f}")
            else:
                lines.append(f"- {key}: {value}")
        return "\n".join(lines)

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context data."""
        lines = []
        for key, value in context.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)

    def _format_funnel_data(self, data: Dict[str, Any]) -> str:
        """Format funnel data."""
        lines = []
        for key, value in data.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)

    def _format_goal_data(self, data: Dict[str, Any]) -> str:
        """Format goal data."""
        lines = []
        for key, value in data.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)


# Singleton instance
_ai_insights_engine: Optional[AIInsightsEngine] = None


def get_ai_insights_engine() -> AIInsightsEngine:
    """
    Get or create AI insights engine instance.

    Returns:
        AIInsightsEngine: Singleton instance
    """
    global _ai_insights_engine
    if _ai_insights_engine is None:
        _ai_insights_engine = AIInsightsEngine()
    return _ai_insights_engine
