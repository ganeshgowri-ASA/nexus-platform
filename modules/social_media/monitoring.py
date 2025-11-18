"""
Social Media Module - Brand Monitoring and Social Listening.

This module provides brand mention tracking, hashtag monitoring,
competitor analysis, and keyword alert functionality.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from .social_types import EngagementType, PlatformType, SentimentType

logger = logging.getLogger(__name__)


class MonitoringError(Exception):
    """Base exception for monitoring errors."""

    pass


class SocialMonitor:
    """Brand monitoring and social listening system."""

    def __init__(self):
        """Initialize social monitor."""
        self._monitors: Dict[UUID, Dict[str, Any]] = {}
        self._mentions: List[Dict[str, Any]] = []
        self._alerts: List[Dict[str, Any]] = []

    def create_monitor(
        self,
        name: str,
        keywords: List[str],
        platforms: List[PlatformType],
        monitor_type: str = "brand",  # brand, hashtag, competitor, keyword
        alert_threshold: Optional[int] = None,
        sentiment_alerts: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a new monitoring setup.

        Args:
            name: Monitor name
            keywords: Keywords/hashtags to monitor
            platforms: Platforms to monitor on
            monitor_type: Type of monitoring
            alert_threshold: Mention threshold for alerts
            sentiment_alerts: Alert on negative sentiment

        Returns:
            Monitor configuration dictionary
        """
        monitor = {
            "id": uuid4(),
            "name": name,
            "keywords": keywords,
            "platforms": platforms,
            "type": monitor_type,
            "alert_threshold": alert_threshold,
            "sentiment_alerts": sentiment_alerts,
            "is_active": True,
            "mention_count": 0,
            "created_at": datetime.utcnow(),
        }

        self._monitors[monitor["id"]] = monitor
        logger.info(f"Created monitor: {name} (type: {monitor_type})")
        return monitor

    async def fetch_mentions(
        self,
        monitor_id: UUID,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Fetch mentions for a monitor.

        Args:
            monitor_id: Monitor UUID
            since: Optional start date
            limit: Maximum mentions to fetch

        Returns:
            List of mention dictionaries

        Raises:
            ValueError: If monitor not found
        """
        if monitor_id not in self._monitors:
            raise ValueError(f"Monitor {monitor_id} not found")

        monitor = self._monitors[monitor_id]

        # In production, fetch from platform APIs
        # For now, return simulated mentions
        logger.info(f"Fetching mentions for monitor {monitor_id}")

        mentions = []
        # Simulated mention data
        for i in range(min(10, limit)):
            mention = {
                "id": uuid4(),
                "monitor_id": monitor_id,
                "platform": monitor["platforms"][0].value,
                "author": f"user_{i}",
                "content": f"Mention of {monitor['keywords'][0]}",
                "url": f"https://example.com/post/{i}",
                "sentiment": SentimentType.NEUTRAL.value,
                "engagement_count": 10,
                "created_at": datetime.utcnow() - timedelta(hours=i),
            }
            mentions.append(mention)
            self._mentions.append(mention)

        monitor["mention_count"] += len(mentions)
        return mentions

    def get_mentions(
        self,
        monitor_id: Optional[UUID] = None,
        platform: Optional[PlatformType] = None,
        sentiment: Optional[SentimentType] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get stored mentions with filters.

        Args:
            monitor_id: Optional filter by monitor
            platform: Optional filter by platform
            sentiment: Optional filter by sentiment
            since: Optional start date
            limit: Maximum mentions

        Returns:
            List of filtered mentions
        """
        mentions = self._mentions.copy()

        if monitor_id:
            mentions = [m for m in mentions if m["monitor_id"] == monitor_id]
        if platform:
            mentions = [m for m in mentions if m["platform"] == platform.value]
        if sentiment:
            mentions = [m for m in mentions if m["sentiment"] == sentiment.value]
        if since:
            mentions = [m for m in mentions if m["created_at"] >= since]

        mentions.sort(key=lambda m: m["created_at"], reverse=True)
        return mentions[:limit]

    def analyze_sentiment_distribution(
        self, monitor_id: UUID, days: int = 7
    ) -> Dict[str, Any]:
        """
        Analyze sentiment distribution for mentions.

        Args:
            monitor_id: Monitor UUID
            days: Number of days to analyze

        Returns:
            Sentiment analysis dictionary
        """
        since = datetime.utcnow() - timedelta(days=days)
        mentions = self.get_mentions(monitor_id=monitor_id, since=since, limit=1000)

        sentiment_counts = {
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "mixed": 0,
        }

        for mention in mentions:
            sentiment = mention.get("sentiment", "neutral")
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1

        total = len(mentions)

        return {
            "monitor_id": str(monitor_id),
            "period_days": days,
            "total_mentions": total,
            "sentiment_counts": sentiment_counts,
            "sentiment_percentages": {
                sentiment: round((count / total * 100), 2) if total > 0 else 0
                for sentiment, count in sentiment_counts.items()
            },
            "overall_sentiment": self._calculate_overall_sentiment(sentiment_counts),
        }

    def _calculate_overall_sentiment(
        self, sentiment_counts: Dict[str, int]
    ) -> str:
        """Calculate overall sentiment from counts."""
        total = sum(sentiment_counts.values())
        if total == 0:
            return "neutral"

        positive_score = sentiment_counts.get("positive", 0) / total
        negative_score = sentiment_counts.get("negative", 0) / total

        if positive_score > 0.6:
            return "positive"
        elif negative_score > 0.4:
            return "negative"
        else:
            return "neutral"

    def get_trending_topics(
        self, platform: PlatformType, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get trending topics from mentions.

        Args:
            platform: Platform to analyze
            limit: Maximum topics

        Returns:
            List of trending topics
        """
        # Analyze mentions for trends
        recent_mentions = self.get_mentions(
            platform=platform,
            since=datetime.utcnow() - timedelta(hours=24),
            limit=1000,
        )

        # Count keyword occurrences
        keyword_counts: Dict[str, int] = {}
        for mention in recent_mentions:
            content = mention.get("content", "").lower()
            words = content.split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    keyword_counts[word] = keyword_counts.get(word, 0) + 1

        # Get top keywords
        trending = sorted(
            [
                {"keyword": k, "mentions": v, "platform": platform.value}
                for k, v in keyword_counts.items()
            ],
            key=lambda x: x["mentions"],
            reverse=True,
        )

        return trending[:limit]

    def create_alert(
        self,
        monitor_id: UUID,
        alert_type: str,
        message: str,
        severity: str = "info",
    ) -> Dict[str, Any]:
        """
        Create a monitoring alert.

        Args:
            monitor_id: Monitor UUID
            alert_type: Alert type (threshold, sentiment, spike, etc.)
            message: Alert message
            severity: Severity level (info, warning, critical)

        Returns:
            Alert dictionary
        """
        alert = {
            "id": uuid4(),
            "monitor_id": monitor_id,
            "type": alert_type,
            "message": message,
            "severity": severity,
            "created_at": datetime.utcnow(),
            "acknowledged": False,
        }

        self._alerts.append(alert)
        logger.warning(f"Alert created: {message} (severity: {severity})")
        return alert

    def get_alerts(
        self,
        monitor_id: Optional[UUID] = None,
        severity: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get monitoring alerts.

        Args:
            monitor_id: Optional filter by monitor
            severity: Optional filter by severity
            acknowledged: Optional filter by acknowledgment status
            limit: Maximum alerts

        Returns:
            List of alerts
        """
        alerts = self._alerts.copy()

        if monitor_id:
            alerts = [a for a in alerts if a["monitor_id"] == monitor_id]
        if severity:
            alerts = [a for a in alerts if a["severity"] == severity]
        if acknowledged is not None:
            alerts = [a for a in alerts if a["acknowledged"] == acknowledged]

        alerts.sort(key=lambda a: a["created_at"], reverse=True)
        return alerts[:limit]

    def acknowledge_alert(self, alert_id: UUID) -> bool:
        """
        Acknowledge an alert.

        Args:
            alert_id: Alert UUID

        Returns:
            True if acknowledged
        """
        for alert in self._alerts:
            if alert["id"] == alert_id:
                alert["acknowledged"] = True
                alert["acknowledged_at"] = datetime.utcnow()
                return True
        return False

    def get_monitor_statistics(self, monitor_id: UUID) -> Dict[str, Any]:
        """
        Get statistics for a monitor.

        Args:
            monitor_id: Monitor UUID

        Returns:
            Statistics dictionary
        """
        if monitor_id not in self._monitors:
            raise ValueError(f"Monitor {monitor_id} not found")

        monitor = self._monitors[monitor_id]
        mentions = self.get_mentions(monitor_id=monitor_id, limit=1000)

        # Calculate metrics
        total_mentions = len(mentions)
        mentions_24h = len(
            self.get_mentions(
                monitor_id=monitor_id,
                since=datetime.utcnow() - timedelta(hours=24),
            )
        )
        mentions_7d = len(
            self.get_mentions(
                monitor_id=monitor_id,
                since=datetime.utcnow() - timedelta(days=7),
            )
        )

        total_engagement = sum(m.get("engagement_count", 0) for m in mentions)

        return {
            "monitor_id": str(monitor_id),
            "name": monitor["name"],
            "type": monitor["type"],
            "keywords": monitor["keywords"],
            "total_mentions": total_mentions,
            "mentions_24h": mentions_24h,
            "mentions_7d": mentions_7d,
            "total_engagement": total_engagement,
            "avg_engagement": round(total_engagement / total_mentions, 2)
            if total_mentions > 0
            else 0,
            "is_active": monitor["is_active"],
        }

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall monitoring statistics.

        Returns:
            Statistics dictionary
        """
        total_monitors = len(self._monitors)
        active_monitors = sum(1 for m in self._monitors.values() if m["is_active"])
        total_mentions = len(self._mentions)
        unacknowledged_alerts = sum(1 for a in self._alerts if not a["acknowledged"])

        return {
            "total_monitors": total_monitors,
            "active_monitors": active_monitors,
            "total_mentions": total_mentions,
            "total_alerts": len(self._alerts),
            "unacknowledged_alerts": unacknowledged_alerts,
        }
