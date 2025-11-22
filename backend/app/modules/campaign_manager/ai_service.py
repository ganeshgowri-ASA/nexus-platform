"""
AI Service for campaign optimization using Claude.

This module provides AI-powered insights and recommendations for campaigns.
"""

from typing import Dict, Any, List, Optional
import json
from anthropic import Anthropic

from app.config import settings
from app.models.campaign import Campaign


class AIService:
    """AI service for campaign intelligence."""

    def __init__(self):
        """Initialize Anthropic client."""
        self.client = None
        if settings.ANTHROPIC_API_KEY:
            self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def generate_campaign_insights(
        self,
        campaign: Campaign,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate AI insights for campaign performance.

        Args:
            campaign: Campaign instance
            metrics: Performance metrics

        Returns:
            dict: AI-generated insights
        """
        if not self.client:
            return self._fallback_insights(campaign, metrics)

        try:
            prompt = self._build_insights_prompt(campaign, metrics)

            message = self.client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=settings.CLAUDE_MAX_TOKENS,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Parse response
            response_text = message.content[0].text
            insights = json.loads(response_text)

            return insights

        except Exception as e:
            return {
                "error": str(e),
                **self._fallback_insights(campaign, metrics)
            }

    def generate_recommendations(
        self,
        campaign: Campaign,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate AI recommendations for campaign optimization.

        Args:
            campaign: Campaign instance
            metrics: Performance metrics

        Returns:
            dict: AI-generated recommendations
        """
        if not self.client:
            return self._fallback_recommendations(campaign, metrics)

        try:
            prompt = self._build_recommendations_prompt(campaign, metrics)

            message = self.client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=settings.CLAUDE_MAX_TOKENS,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            response_text = message.content[0].text
            recommendations = json.loads(response_text)

            return recommendations

        except Exception as e:
            return {
                "error": str(e),
                **self._fallback_recommendations(campaign, metrics)
            }

    def optimize_budget_allocation(
        self,
        campaign: Campaign,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Optimize budget allocation across channels using AI.

        Args:
            campaign: Campaign instance
            metrics: Performance metrics

        Returns:
            dict: Budget optimization suggestions
        """
        if not self.client:
            return self._fallback_budget_optimization(campaign, metrics)

        try:
            # Build channel performance data
            channel_data = []
            for channel in campaign.channels:
                channel_data.append({
                    "id": channel.id,
                    "name": channel.channel_name,
                    "type": channel.channel_type.value,
                    "allocated_budget": channel.allocated_budget,
                    "spent_budget": channel.spent_budget,
                    "roi": channel.roi,
                    "conversions": channel.conversions,
                    "ctr": channel.ctr,
                })

            prompt = f"""Analyze this campaign's channel performance and recommend optimal budget allocation:

Campaign: {campaign.name}
Type: {campaign.campaign_type.value}
Total Budget: ${campaign.total_budget}
Remaining Budget: ${campaign.remaining_budget}

Channel Performance:
{json.dumps(channel_data, indent=2)}

Overall Metrics:
{json.dumps(metrics, indent=2)}

Provide budget reallocation recommendations in JSON format:
{{
    "summary": "Brief explanation of recommendations",
    "reallocations": [
        {{
            "channel_id": 1,
            "channel_name": "Channel Name",
            "current_allocation": 1000,
            "recommended_allocation": 1500,
            "reason": "Why this change is recommended",
            "expected_impact": "Expected improvement"
        }}
    ],
    "priority": "high/medium/low",
    "estimated_roi_improvement": 15.5
}}"""

            message = self.client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=settings.CLAUDE_MAX_TOKENS,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            response_text = message.content[0].text
            optimization = json.loads(response_text)

            return optimization

        except Exception as e:
            return {
                "error": str(e),
                **self._fallback_budget_optimization(campaign, metrics)
            }

    def generate_campaign_content(
        self,
        campaign_type: str,
        target_audience: Dict[str, Any],
        goals: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        Generate campaign content ideas using AI.

        Args:
            campaign_type: Type of campaign
            target_audience: Target audience details
            goals: Campaign goals

        Returns:
            dict: Content suggestions
        """
        if not self.client:
            return {"ideas": [], "error": "AI service not configured"}

        try:
            prompt = f"""Generate creative campaign content ideas:

Campaign Type: {campaign_type}
Target Audience: {json.dumps(target_audience, indent=2)}
Goals: {json.dumps(goals, indent=2)}

Provide 5-10 campaign content ideas in JSON format:
{{
    "ideas": [
        {{
            "title": "Content idea title",
            "description": "Detailed description",
            "channels": ["email", "social_media"],
            "estimated_reach": "Expected reach",
            "creative_approach": "How to execute"
        }}
    ]
}}"""

            message = self.client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=settings.CLAUDE_MAX_TOKENS,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            response_text = message.content[0].text
            content = json.loads(response_text)

            return content

        except Exception as e:
            return {"ideas": [], "error": str(e)}

    def _build_insights_prompt(
        self,
        campaign: Campaign,
        metrics: Dict[str, Any]
    ) -> str:
        """Build prompt for insights generation."""
        return f"""Analyze this marketing campaign and provide insights:

Campaign: {campaign.name}
Type: {campaign.campaign_type.value}
Status: {campaign.status.value}
Duration: {campaign.start_date} to {campaign.end_date}
Budget: ${campaign.total_budget} (${metrics.get('total_cost', 0)} spent)

Performance Metrics:
- ROI: {metrics.get('roi', 0):.2f}%
- Impressions: {metrics.get('total_impressions', 0):,}
- Clicks: {metrics.get('total_clicks', 0):,}
- Conversions: {metrics.get('total_conversions', 0):,}
- CTR: {metrics.get('ctr', 0):.2f}%
- Conversion Rate: {metrics.get('conversion_rate', 0):.2f}%

Provide analysis in JSON format:
{{
    "summary": "Overall performance summary",
    "strengths": ["Key strength 1", "Key strength 2"],
    "weaknesses": ["Area for improvement 1", "Area for improvement 2"],
    "opportunities": ["Opportunity 1", "Opportunity 2"],
    "threats": ["Risk 1", "Risk 2"],
    "key_metrics_analysis": {{
        "roi_assessment": "ROI analysis",
        "engagement_assessment": "Engagement analysis",
        "conversion_assessment": "Conversion analysis"
    }}
}}"""

    def _build_recommendations_prompt(
        self,
        campaign: Campaign,
        metrics: Dict[str, Any]
    ) -> str:
        """Build prompt for recommendations generation."""
        return f"""Based on this campaign's performance, provide actionable recommendations:

Campaign: {campaign.name}
Current Performance:
{json.dumps(metrics, indent=2)}

Goals:
{json.dumps(campaign.goals or {}, indent=2)}

Provide recommendations in JSON format:
{{
    "immediate_actions": [
        {{
            "action": "Specific action to take",
            "priority": "high/medium/low",
            "expected_impact": "Expected outcome",
            "timeline": "When to implement"
        }}
    ],
    "strategic_recommendations": [
        {{
            "recommendation": "Strategic change",
            "rationale": "Why this is recommended",
            "implementation_steps": ["Step 1", "Step 2"]
        }}
    ],
    "content_suggestions": ["Content idea 1", "Content idea 2"],
    "channel_recommendations": ["Channel strategy 1", "Channel strategy 2"]
}}"""

    def _fallback_insights(
        self,
        campaign: Campaign,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback insights when AI is unavailable."""
        roi = metrics.get("roi", 0)
        ctr = metrics.get("ctr", 0)

        strengths = []
        weaknesses = []

        if roi > 100:
            strengths.append("Strong positive ROI")
        elif roi < 0:
            weaknesses.append("Negative ROI needs attention")

        if ctr > 2.0:
            strengths.append("Above-average click-through rate")
        elif ctr < 1.0:
            weaknesses.append("Low click-through rate")

        return {
            "summary": f"Campaign is {campaign.status.value} with {roi:.1f}% ROI",
            "strengths": strengths or ["Campaign is tracking"],
            "weaknesses": weaknesses or ["No major issues detected"],
            "opportunities": ["Optimize channel mix", "Test new creatives"],
            "threats": ["Budget constraints", "Market competition"],
        }

    def _fallback_recommendations(
        self,
        campaign: Campaign,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback recommendations when AI is unavailable."""
        recommendations = []

        if metrics.get("roi", 0) < 50:
            recommendations.append({
                "action": "Review and optimize budget allocation",
                "priority": "high",
                "expected_impact": "Improved ROI",
                "timeline": "Immediate"
            })

        if metrics.get("ctr", 0) < 1.5:
            recommendations.append({
                "action": "Test new ad creatives and messaging",
                "priority": "medium",
                "expected_impact": "Higher engagement",
                "timeline": "Within 1 week"
            })

        return {
            "immediate_actions": recommendations,
            "strategic_recommendations": [],
            "content_suggestions": ["Test A/B variants", "Refresh creative assets"],
            "channel_recommendations": ["Focus on high-performing channels"]
        }

    def _fallback_budget_optimization(
        self,
        campaign: Campaign,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback budget optimization when AI is unavailable."""
        return {
            "summary": "Maintain current allocation pending more data",
            "reallocations": [],
            "priority": "low",
            "estimated_roi_improvement": 0.0
        }
