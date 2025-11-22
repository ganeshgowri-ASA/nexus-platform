"""
Analytics module for performance tracking and ROI analysis.

This module provides:
- Performance tracking
- Engagement metrics
- Content ROI calculation
- Analytics reports
- Insights and recommendations
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from loguru import logger
import pandas as pd

from database import ContentItem, Analytics, Campaign, Channel
from .calendar_types import (
    AnalyticsMetric,
    PerformanceReport,
)


class AnalyticsManager:
    """Analytics manager for performance tracking and insights."""

    def __init__(self, db: Session):
        """
        Initialize analytics manager.

        Args:
            db: Database session
        """
        self.db = db
        logger.info("AnalyticsManager initialized")

    def track_metric(
        self,
        content_id: int,
        channel: str,
        metric_name: str,
        metric_value: float,
        metadata: Optional[dict] = None,
    ) -> AnalyticsMetric:
        """
        Track a single metric for content.

        Args:
            content_id: Content ID
            channel: Publishing channel
            metric_name: Metric name (views, likes, shares, etc.)
            metric_value: Metric value
            metadata: Additional metadata

        Returns:
            Tracked metric
        """
        try:
            # Map channel string to enum
            channel_enum = self._map_channel(channel)

            analytics = Analytics(
                content_item_id=content_id,
                channel=channel_enum,
                metric_name=metric_name,
                metric_value=metric_value,
                metadata=metadata or {},
            )

            self.db.add(analytics)
            self.db.commit()
            self.db.refresh(analytics)

            # Update content item aggregates
            self._update_content_aggregates(content_id)

            metric = AnalyticsMetric(
                metric_name=metric_name,
                metric_value=metric_value,
                channel=channel,
                timestamp=analytics.recorded_at,
            )

            logger.info(f"Tracked metric {metric_name}={metric_value} for content {content_id}")
            return metric

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error tracking metric: {e}")
            raise

    def get_content_performance(
        self,
        content_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> PerformanceReport:
        """
        Get performance report for content.

        Args:
            content_id: Content ID
            start_date: Report start date
            end_date: Report end date

        Returns:
            Performance report
        """
        try:
            # Set default date range
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)

            # Query analytics
            analytics = (
                self.db.query(Analytics)
                .filter(
                    and_(
                        Analytics.content_item_id == content_id,
                        Analytics.recorded_at >= start_date,
                        Analytics.recorded_at <= end_date,
                    )
                )
                .all()
            )

            # Build metrics list
            metrics = [
                AnalyticsMetric(
                    metric_name=a.metric_name,
                    metric_value=a.metric_value,
                    channel=a.channel.value,
                    timestamp=a.recorded_at,
                )
                for a in analytics
            ]

            # Calculate aggregates
            total_views = sum(
                m.metric_value for m in metrics if m.metric_name == "views"
            )
            total_likes = sum(
                m.metric_value for m in metrics if m.metric_name == "likes"
            )
            total_shares = sum(
                m.metric_value for m in metrics if m.metric_name == "shares"
            )
            total_comments = sum(
                m.metric_value for m in metrics if m.metric_name == "comments"
            )

            # Calculate engagement rate
            engagement_rate = 0.0
            if total_views > 0:
                total_engagements = total_likes + total_shares + total_comments
                engagement_rate = (total_engagements / total_views) * 100

            # Get content for ROI calculation
            content_item = (
                self.db.query(ContentItem)
                .filter(ContentItem.id == content_id)
                .first()
            )

            roi = None
            if content_item and content_item.campaign_id:
                roi = self._calculate_content_roi(content_id, content_item.campaign_id)

            report = PerformanceReport(
                content_id=content_id,
                period_start=start_date,
                period_end=end_date,
                metrics=metrics,
                total_views=int(total_views),
                total_likes=int(total_likes),
                total_shares=int(total_shares),
                total_comments=int(total_comments),
                engagement_rate=engagement_rate,
                roi=roi,
            )

            logger.info(f"Generated performance report for content {content_id}")
            return report

        except Exception as e:
            logger.error(f"Error getting content performance: {e}")
            raise

    def get_campaign_performance(
        self,
        campaign_id: int,
    ) -> dict:
        """
        Get performance metrics for entire campaign.

        Args:
            campaign_id: Campaign ID

        Returns:
            Campaign performance data
        """
        try:
            campaign = (
                self.db.query(Campaign)
                .filter(Campaign.id == campaign_id)
                .first()
            )

            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")

            # Get all content in campaign
            content_items = (
                self.db.query(ContentItem)
                .filter(ContentItem.campaign_id == campaign_id)
                .all()
            )

            # Aggregate metrics
            total_views = sum(item.views for item in content_items)
            total_likes = sum(item.likes for item in content_items)
            total_shares = sum(item.shares for item in content_items)
            total_comments = sum(item.comments_count for item in content_items)

            avg_engagement = 0.0
            if content_items:
                avg_engagement = sum(
                    item.engagement_rate for item in content_items
                ) / len(content_items)

            # Calculate ROI
            roi = None
            if campaign.budget and campaign.budget > 0:
                # Simplified ROI calculation
                # In production, this would use actual revenue data
                estimated_value = total_views * 0.01 + total_likes * 0.05 + total_shares * 0.10
                roi = ((estimated_value - campaign.budget) / campaign.budget) * 100

            return {
                "campaign_id": campaign_id,
                "campaign_name": campaign.name,
                "start_date": campaign.start_date,
                "end_date": campaign.end_date,
                "content_count": len(content_items),
                "total_views": total_views,
                "total_likes": total_likes,
                "total_shares": total_shares,
                "total_comments": total_comments,
                "average_engagement_rate": avg_engagement,
                "budget": campaign.budget,
                "roi": roi,
            }

        except Exception as e:
            logger.error(f"Error getting campaign performance: {e}")
            raise

    def get_channel_performance(
        self,
        channel: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """
        Get performance metrics for channel.

        Args:
            channel: Channel name
            start_date: Report start date
            end_date: Report end date

        Returns:
            Channel performance data
        """
        try:
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)

            channel_enum = self._map_channel(channel)

            # Query analytics
            analytics = (
                self.db.query(Analytics)
                .filter(
                    and_(
                        Analytics.channel == channel_enum,
                        Analytics.recorded_at >= start_date,
                        Analytics.recorded_at <= end_date,
                    )
                )
                .all()
            )

            # Aggregate by metric type
            metrics_by_type = {}
            for a in analytics:
                if a.metric_name not in metrics_by_type:
                    metrics_by_type[a.metric_name] = []
                metrics_by_type[a.metric_name].append(a.metric_value)

            aggregates = {
                metric_name: {
                    "total": sum(values),
                    "average": sum(values) / len(values) if values else 0,
                    "count": len(values),
                }
                for metric_name, values in metrics_by_type.items()
            }

            # Get content count
            content_count = (
                self.db.query(ContentItem)
                .filter(ContentItem.channels.contains([channel]))
                .count()
            )

            return {
                "channel": channel,
                "period_start": start_date,
                "period_end": end_date,
                "content_count": content_count,
                "metrics": aggregates,
            }

        except Exception as e:
            logger.error(f"Error getting channel performance: {e}")
            raise

    def get_top_performing_content(
        self,
        metric: str = "engagement_rate",
        limit: int = 10,
        days: int = 30,
    ) -> list[dict]:
        """
        Get top performing content.

        Args:
            metric: Metric to sort by (views, likes, shares, engagement_rate)
            limit: Number of results
            days: Look back period

        Returns:
            List of top performing content
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=days)

            query = self.db.query(ContentItem).filter(
                ContentItem.created_at >= since_date
            )

            # Sort by metric
            if metric == "views":
                query = query.order_by(desc(ContentItem.views))
            elif metric == "likes":
                query = query.order_by(desc(ContentItem.likes))
            elif metric == "shares":
                query = query.order_by(desc(ContentItem.shares))
            else:
                query = query.order_by(desc(ContentItem.engagement_rate))

            top_content = query.limit(limit).all()

            result = [
                {
                    "id": item.id,
                    "title": item.title,
                    "content_type": item.content_type.value,
                    "views": item.views,
                    "likes": item.likes,
                    "shares": item.shares,
                    "comments": item.comments_count,
                    "engagement_rate": item.engagement_rate,
                    "published_at": item.published_at,
                }
                for item in top_content
            ]

            logger.info(f"Retrieved top {len(result)} performing content by {metric}")
            return result

        except Exception as e:
            logger.error(f"Error getting top performing content: {e}")
            raise

    def get_engagement_trends(
        self,
        content_id: Optional[int] = None,
        channel: Optional[str] = None,
        days: int = 30,
    ) -> dict:
        """
        Get engagement trends over time.

        Args:
            content_id: Filter by content ID
            channel: Filter by channel
            days: Number of days to analyze

        Returns:
            Trend data
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=days)

            query = self.db.query(Analytics).filter(
                Analytics.recorded_at >= since_date
            )

            if content_id:
                query = query.filter(Analytics.content_item_id == content_id)

            if channel:
                channel_enum = self._map_channel(channel)
                query = query.filter(Analytics.channel == channel_enum)

            analytics = query.all()

            # Group by date
            data_by_date = {}
            for a in analytics:
                date_key = a.recorded_at.date()
                if date_key not in data_by_date:
                    data_by_date[date_key] = {
                        "views": 0,
                        "likes": 0,
                        "shares": 0,
                        "comments": 0,
                    }

                if a.metric_name in data_by_date[date_key]:
                    data_by_date[date_key][a.metric_name] += a.metric_value

            # Convert to list
            trends = [
                {
                    "date": str(date),
                    **metrics,
                    "engagement_rate": (
                        ((metrics["likes"] + metrics["shares"] + metrics["comments"]) / metrics["views"] * 100)
                        if metrics["views"] > 0
                        else 0
                    ),
                }
                for date, metrics in sorted(data_by_date.items())
            ]

            return {
                "period_start": since_date,
                "period_end": datetime.utcnow(),
                "trends": trends,
            }

        except Exception as e:
            logger.error(f"Error getting engagement trends: {e}")
            raise

    def get_audience_insights(
        self,
        content_id: Optional[int] = None,
        days: int = 30,
    ) -> dict:
        """
        Get audience insights and demographics.

        Args:
            content_id: Filter by content ID
            days: Number of days to analyze

        Returns:
            Audience insights
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=days)

            query = self.db.query(Analytics).filter(
                Analytics.recorded_at >= since_date
            )

            if content_id:
                query = query.filter(Analytics.content_item_id == content_id)

            analytics = query.all()

            # Analyze metadata for insights
            locations = []
            devices = []
            age_groups = []

            for a in analytics:
                metadata = a.metadata or {}
                if "location" in metadata:
                    locations.append(metadata["location"])
                if "device" in metadata:
                    devices.append(metadata["device"])
                if "age_group" in metadata:
                    age_groups.append(metadata["age_group"])

            # Calculate distributions
            from collections import Counter

            return {
                "period_start": since_date,
                "period_end": datetime.utcnow(),
                "total_interactions": len(analytics),
                "top_locations": dict(Counter(locations).most_common(5)) if locations else {},
                "device_breakdown": dict(Counter(devices)) if devices else {},
                "age_distribution": dict(Counter(age_groups)) if age_groups else {},
            }

        except Exception as e:
            logger.error(f"Error getting audience insights: {e}")
            raise

    def generate_recommendations(
        self,
        content_id: Optional[int] = None,
    ) -> list[dict]:
        """
        Generate AI-powered recommendations.

        Args:
            content_id: Content ID to analyze

        Returns:
            List of recommendations
        """
        recommendations = []

        try:
            if content_id:
                # Get performance report
                report = self.get_content_performance(content_id)

                # Generate recommendations based on performance
                if report.engagement_rate < 2.0:
                    recommendations.append(
                        {
                            "type": "engagement",
                            "priority": "high",
                            "message": "Low engagement rate. Consider using more compelling visuals and calls-to-action.",
                        }
                    )

                if report.total_shares < report.total_views * 0.01:
                    recommendations.append(
                        {
                            "type": "shareability",
                            "priority": "medium",
                            "message": "Content has low share rate. Add shareable quotes or key takeaways.",
                        }
                    )

                if report.total_comments < report.total_views * 0.005:
                    recommendations.append(
                        {
                            "type": "interaction",
                            "priority": "medium",
                            "message": "Low comment rate. Try asking questions or encouraging discussion.",
                        }
                    )

            logger.info(f"Generated {len(recommendations)} recommendations")
            return recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return recommendations

    # Helper Methods
    def _update_content_aggregates(self, content_id: int) -> None:
        """Update content item aggregate metrics."""
        try:
            # Get all analytics for content
            analytics = (
                self.db.query(Analytics)
                .filter(Analytics.content_item_id == content_id)
                .all()
            )

            # Calculate aggregates
            total_views = sum(
                a.metric_value for a in analytics if a.metric_name == "views"
            )
            total_likes = sum(
                a.metric_value for a in analytics if a.metric_name == "likes"
            )
            total_shares = sum(
                a.metric_value for a in analytics if a.metric_name == "shares"
            )

            # Update content item
            content_item = (
                self.db.query(ContentItem)
                .filter(ContentItem.id == content_id)
                .first()
            )

            if content_item:
                content_item.views = int(total_views)
                content_item.likes = int(total_likes)
                content_item.shares = int(total_shares)

                # Calculate engagement rate
                if total_views > 0:
                    total_engagements = total_likes + total_shares + content_item.comments_count
                    content_item.engagement_rate = (total_engagements / total_views) * 100

                self.db.commit()

        except Exception as e:
            logger.error(f"Error updating content aggregates: {e}")
            self.db.rollback()

    def _calculate_content_roi(self, content_id: int, campaign_id: int) -> Optional[float]:
        """Calculate ROI for content."""
        try:
            content_item = (
                self.db.query(ContentItem)
                .filter(ContentItem.id == content_id)
                .first()
            )

            campaign = (
                self.db.query(Campaign)
                .filter(Campaign.id == campaign_id)
                .first()
            )

            if not content_item or not campaign or not campaign.budget:
                return None

            # Get campaign content count
            campaign_content_count = (
                self.db.query(ContentItem)
                .filter(ContentItem.campaign_id == campaign_id)
                .count()
            )

            # Allocate budget per content
            content_cost = campaign.budget / campaign_content_count if campaign_content_count > 0 else 0

            # Estimate value (simplified)
            estimated_value = (
                content_item.views * 0.01
                + content_item.likes * 0.05
                + content_item.shares * 0.10
            )

            if content_cost > 0:
                roi = ((estimated_value - content_cost) / content_cost) * 100
                return roi

            return None

        except Exception as e:
            logger.error(f"Error calculating ROI: {e}")
            return None

    def _map_channel(self, channel: str) -> Channel:
        """Map channel name to database enum."""
        mapping = {
            "twitter": Channel.TWITTER,
            "facebook": Channel.FACEBOOK,
            "instagram": Channel.INSTAGRAM,
            "linkedin": Channel.LINKEDIN,
            "youtube": Channel.YOUTUBE,
            "blog": Channel.BLOG,
            "email": Channel.EMAIL,
        }
        return mapping.get(channel.lower(), Channel.BLOG)
