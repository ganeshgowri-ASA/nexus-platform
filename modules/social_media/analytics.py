"""
Social Media Module - Analytics and Metrics.

This module provides cross-platform analytics aggregation, engagement metrics,
audience insights, and ROI tracking.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from .platforms import BasePlatform
from .social_types import Analytics, PlatformType, Post

logger = logging.getLogger(__name__)


class AnalyticsError(Exception):
    """Base exception for analytics errors."""

    pass


class AnalyticsManager:
    """Cross-platform analytics and metrics manager."""

    def __init__(self):
        """Initialize analytics manager."""
        self._platforms: Dict[PlatformType, BasePlatform] = {}
        self._analytics_cache: Dict[UUID, Analytics] = {}

    def register_platform(
        self, platform_type: PlatformType, platform: BasePlatform
    ) -> None:
        """
        Register a platform for analytics tracking.

        Args:
            platform_type: Platform type
            platform: Platform instance
        """
        self._platforms[platform_type] = platform
        logger.info(f"Registered platform {platform_type.value} for analytics")

    async def fetch_post_analytics(
        self, post: Post, platform: PlatformType
    ) -> Analytics:
        """
        Fetch analytics for a specific post on a platform.

        Args:
            post: Post object
            platform: Platform to fetch from

        Returns:
            Analytics object

        Raises:
            AnalyticsError: If fetching fails
        """
        try:
            if platform not in self._platforms:
                raise AnalyticsError(f"Platform {platform.value} not registered")

            platform_instance = self._platforms[platform]
            platform_post_id = post.platform_post_ids.get(platform.value)

            if not platform_post_id:
                raise AnalyticsError(f"Post not published to {platform.value}")

            analytics = await platform_instance.get_post_analytics(platform_post_id)
            analytics.entity_id = post.id
            analytics.entity_type = "post"

            self._analytics_cache[analytics.id] = analytics
            logger.info(f"Fetched analytics for post {post.id} on {platform.value}")
            return analytics

        except Exception as e:
            logger.error(f"Failed to fetch post analytics: {e}")
            raise AnalyticsError(f"Analytics fetch failed: {e}")

    async def fetch_campaign_analytics(
        self,
        campaign_id: UUID,
        posts: List[Post],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Aggregate analytics for a campaign.

        Args:
            campaign_id: Campaign UUID
            posts: Posts in the campaign
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Aggregated analytics dictionary
        """
        total_impressions = 0
        total_reach = 0
        total_engagement = 0
        total_clicks = 0
        total_conversions = 0
        total_cost = 0.0
        total_revenue = 0.0

        platform_breakdown = {}
        post_performance = []

        for post in posts:
            # Apply date filters
            if start_date and post.published_at and post.published_at < start_date:
                continue
            if end_date and post.published_at and post.published_at > end_date:
                continue

            post_metrics = {
                "post_id": str(post.id),
                "title": post.title,
                "published_at": post.published_at.isoformat() if post.published_at else None,
                "platforms": {},
            }

            for platform in post.platforms:
                try:
                    analytics = await self.fetch_post_analytics(post, platform)

                    # Aggregate totals
                    total_impressions += analytics.impressions
                    total_reach += analytics.reach
                    total_engagement += analytics.engagement_count
                    total_clicks += analytics.clicks
                    total_conversions += analytics.conversion_count
                    total_cost += analytics.cost
                    total_revenue += analytics.revenue

                    # Platform breakdown
                    if platform.value not in platform_breakdown:
                        platform_breakdown[platform.value] = {
                            "impressions": 0,
                            "reach": 0,
                            "engagement": 0,
                            "clicks": 0,
                        }

                    platform_breakdown[platform.value]["impressions"] += analytics.impressions
                    platform_breakdown[platform.value]["reach"] += analytics.reach
                    platform_breakdown[platform.value]["engagement"] += analytics.engagement_count
                    platform_breakdown[platform.value]["clicks"] += analytics.clicks

                    # Post performance
                    post_metrics["platforms"][platform.value] = {
                        "impressions": analytics.impressions,
                        "engagement": analytics.engagement_count,
                        "engagement_rate": analytics.engagement_rate,
                    }

                except Exception as e:
                    logger.warning(
                        f"Failed to fetch analytics for post {post.id} on {platform.value}: {e}"
                    )

            post_performance.append(post_metrics)

        # Calculate aggregated metrics
        engagement_rate = (
            (total_engagement / total_reach * 100) if total_reach > 0 else 0.0
        )
        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0.0
        roi = (
            ((total_revenue - total_cost) / total_cost * 100) if total_cost > 0 else 0.0
        )

        return {
            "campaign_id": str(campaign_id),
            "total_posts": len(posts),
            "date_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
            "totals": {
                "impressions": total_impressions,
                "reach": total_reach,
                "engagement": total_engagement,
                "clicks": total_clicks,
                "conversions": total_conversions,
                "cost": total_cost,
                "revenue": total_revenue,
            },
            "rates": {
                "engagement_rate": round(engagement_rate, 2),
                "click_through_rate": round(ctr, 2),
                "roi": round(roi, 2),
            },
            "by_platform": platform_breakdown,
            "post_performance": post_performance,
        }

    def get_top_performing_posts(
        self,
        posts: List[Post],
        metric: str = "engagement_count",
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get top performing posts.

        Args:
            posts: List of posts to analyze
            metric: Metric to sort by (engagement_count, impressions, reach, etc.)
            limit: Number of top posts to return

        Returns:
            List of top performing post data
        """
        post_scores = []

        for post in posts:
            total_score = 0
            for platform_id, platform_metrics in post.performance_metrics.items():
                score = platform_metrics.get(metric, 0)
                total_score += score

            post_scores.append(
                {
                    "post_id": str(post.id),
                    "title": post.title,
                    "platforms": [p.value for p in post.platforms],
                    "published_at": post.published_at.isoformat() if post.published_at else None,
                    metric: total_score,
                }
            )

        # Sort by metric and return top N
        post_scores.sort(key=lambda x: x[metric], reverse=True)
        return post_scores[:limit]

    def get_engagement_trends(
        self,
        analytics_list: List[Analytics],
        period: str = "daily",
    ) -> Dict[str, Any]:
        """
        Analyze engagement trends over time.

        Args:
            analytics_list: List of analytics records
            period: Aggregation period (daily, weekly, monthly)

        Returns:
            Trend data dictionary
        """
        # Group by period
        trends = {}

        for analytics in analytics_list:
            date_key = self._get_period_key(analytics.date, period)

            if date_key not in trends:
                trends[date_key] = {
                    "date": date_key,
                    "impressions": 0,
                    "reach": 0,
                    "engagement": 0,
                    "likes": 0,
                    "comments": 0,
                    "shares": 0,
                }

            trends[date_key]["impressions"] += analytics.impressions
            trends[date_key]["reach"] += analytics.reach
            trends[date_key]["engagement"] += analytics.engagement_count
            trends[date_key]["likes"] += analytics.likes
            trends[date_key]["comments"] += analytics.comments
            trends[date_key]["shares"] += analytics.shares

        # Convert to list and sort by date
        trend_list = sorted(trends.values(), key=lambda x: x["date"])

        # Calculate growth rates
        for i in range(1, len(trend_list)):
            prev = trend_list[i - 1]
            curr = trend_list[i]

            for metric in ["impressions", "reach", "engagement"]:
                if prev[metric] > 0:
                    growth = ((curr[metric] - prev[metric]) / prev[metric]) * 100
                    curr[f"{metric}_growth"] = round(growth, 2)
                else:
                    curr[f"{metric}_growth"] = 0.0

        return {
            "period": period,
            "data_points": len(trend_list),
            "trends": trend_list,
        }

    def get_audience_insights(
        self, analytics_list: List[Analytics]
    ) -> Dict[str, Any]:
        """
        Aggregate audience demographic insights.

        Args:
            analytics_list: List of analytics records

        Returns:
            Audience insights dictionary
        """
        total_reach = 0
        age_distribution = {}
        gender_distribution = {}
        location_distribution = {}
        device_distribution = {}

        for analytics in analytics_list:
            total_reach += analytics.reach

            # Aggregate demographics
            demographics = analytics.audience_demographics

            # Age groups
            for age_group, count in demographics.get("age", {}).items():
                age_distribution[age_group] = age_distribution.get(age_group, 0) + count

            # Gender
            for gender, count in demographics.get("gender", {}).items():
                gender_distribution[gender] = gender_distribution.get(gender, 0) + count

            # Location
            for location, count in demographics.get("location", {}).items():
                location_distribution[location] = (
                    location_distribution.get(location, 0) + count
                )

            # Device
            for device, count in demographics.get("device", {}).items():
                device_distribution[device] = device_distribution.get(device, 0) + count

        # Convert counts to percentages
        def to_percentages(distribution, total):
            return {
                k: round((v / total * 100), 2) if total > 0 else 0
                for k, v in distribution.items()
            }

        return {
            "total_reach": total_reach,
            "age_groups": to_percentages(age_distribution, total_reach),
            "gender": to_percentages(gender_distribution, total_reach),
            "top_locations": sorted(
                [
                    {"location": k, "percentage": round((v / total_reach * 100), 2)}
                    for k, v in location_distribution.items()
                ],
                key=lambda x: x["percentage"],
                reverse=True,
            )[:10],
            "devices": to_percentages(device_distribution, total_reach),
        }

    def calculate_best_posting_times(
        self, analytics_list: List[Analytics]
    ) -> Dict[str, Any]:
        """
        Analyze best posting times based on historical performance.

        Args:
            analytics_list: List of analytics records

        Returns:
            Best posting times analysis
        """
        hour_performance = {i: {"posts": 0, "avg_engagement_rate": 0.0} for i in range(24)}
        day_performance = {i: {"posts": 0, "avg_engagement_rate": 0.0} for i in range(7)}

        for analytics in analytics_list:
            hour = analytics.date.hour
            day = analytics.date.weekday()

            # Hour performance
            hour_performance[hour]["posts"] += 1
            hour_performance[hour]["avg_engagement_rate"] += analytics.engagement_rate

            # Day performance
            day_performance[day]["posts"] += 1
            day_performance[day]["avg_engagement_rate"] += analytics.engagement_rate

        # Calculate averages
        for hour, data in hour_performance.items():
            if data["posts"] > 0:
                data["avg_engagement_rate"] = round(
                    data["avg_engagement_rate"] / data["posts"], 2
                )

        for day, data in day_performance.items():
            if data["posts"] > 0:
                data["avg_engagement_rate"] = round(
                    data["avg_engagement_rate"] / data["posts"], 2
                )

        # Get top hours and days
        top_hours = sorted(
            [
                {"hour": h, "engagement_rate": d["avg_engagement_rate"], "posts": d["posts"]}
                for h, d in hour_performance.items()
                if d["posts"] > 0
            ],
            key=lambda x: x["engagement_rate"],
            reverse=True,
        )[:5]

        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        top_days = sorted(
            [
                {
                    "day": day_names[d],
                    "engagement_rate": data["avg_engagement_rate"],
                    "posts": data["posts"],
                }
                for d, data in day_performance.items()
                if data["posts"] > 0
            ],
            key=lambda x: x["engagement_rate"],
            reverse=True,
        )[:3]

        return {
            "best_hours": top_hours,
            "best_days": top_days,
        }

    def _get_period_key(self, date: datetime, period: str) -> str:
        """Get period key for trend grouping."""
        if period == "daily":
            return date.strftime("%Y-%m-%d")
        elif period == "weekly":
            return date.strftime("%Y-W%U")
        elif period == "monthly":
            return date.strftime("%Y-%m")
        else:
            return date.strftime("%Y-%m-%d")

    def compare_platforms(
        self, analytics_list: List[Analytics]
    ) -> Dict[str, Any]:
        """
        Compare performance across platforms.

        Args:
            analytics_list: List of analytics records

        Returns:
            Platform comparison data
        """
        platform_metrics = {}

        for analytics in analytics_list:
            platform = analytics.platform.value

            if platform not in platform_metrics:
                platform_metrics[platform] = {
                    "posts": 0,
                    "total_impressions": 0,
                    "total_reach": 0,
                    "total_engagement": 0,
                    "total_clicks": 0,
                    "total_cost": 0.0,
                    "total_revenue": 0.0,
                }

            metrics = platform_metrics[platform]
            metrics["posts"] += 1
            metrics["total_impressions"] += analytics.impressions
            metrics["total_reach"] += analytics.reach
            metrics["total_engagement"] += analytics.engagement_count
            metrics["total_clicks"] += analytics.clicks
            metrics["total_cost"] += analytics.cost
            metrics["total_revenue"] += analytics.revenue

        # Calculate averages and rates
        comparison = []
        for platform, metrics in platform_metrics.items():
            avg_engagement_rate = (
                (metrics["total_engagement"] / metrics["total_reach"] * 100)
                if metrics["total_reach"] > 0
                else 0.0
            )
            avg_ctr = (
                (metrics["total_clicks"] / metrics["total_impressions"] * 100)
                if metrics["total_impressions"] > 0
                else 0.0
            )
            roi = (
                ((metrics["total_revenue"] - metrics["total_cost"]) / metrics["total_cost"] * 100)
                if metrics["total_cost"] > 0
                else 0.0
            )

            comparison.append(
                {
                    "platform": platform,
                    "posts": metrics["posts"],
                    "impressions": metrics["total_impressions"],
                    "reach": metrics["total_reach"],
                    "engagement": metrics["total_engagement"],
                    "clicks": metrics["total_clicks"],
                    "engagement_rate": round(avg_engagement_rate, 2),
                    "click_through_rate": round(avg_ctr, 2),
                    "roi": round(roi, 2),
                    "cost": metrics["total_cost"],
                    "revenue": metrics["total_revenue"],
                }
            )

        # Sort by engagement
        comparison.sort(key=lambda x: x["engagement"], reverse=True)

        return {"platforms": comparison}
