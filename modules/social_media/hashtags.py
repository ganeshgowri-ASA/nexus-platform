"""
Social Media Module - Hashtag Intelligence.

This module provides hashtag suggestions, trending hashtag tracking,
performance analysis, and saved hashtag sets.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from .social_types import Hashtag, PlatformType

logger = logging.getLogger(__name__)


class HashtagError(Exception):
    """Base exception for hashtag errors."""

    pass


class HashtagManager:
    """Hashtag intelligence and management system."""

    def __init__(self):
        """Initialize hashtag manager."""
        self._hashtags: Dict[str, Hashtag] = {}  # tag -> Hashtag
        self._saved_sets: Dict[str, List[str]] = {}  # set_name -> [tags]
        self._trending_cache: Dict[PlatformType, List[str]] = {}
        self._related_cache: Dict[str, List[str]] = {}

    def track_hashtag(
        self,
        tag: str,
        platform: PlatformType,
        reach: int = 0,
        engagement: int = 0,
        category: Optional[str] = None,
    ) -> Hashtag:
        """
        Track a hashtag's performance.

        Args:
            tag: Hashtag text (with or without #)
            platform: Platform where hashtag was used
            reach: Reach/impressions for the hashtag
            engagement: Engagement count
            category: Optional category

        Returns:
            Hashtag object
        """
        # Normalize tag
        normalized_tag = tag.strip().lstrip("#").lower()
        key = f"{platform.value}:{normalized_tag}"

        if key not in self._hashtags:
            self._hashtags[key] = Hashtag(
                id=uuid4(),
                tag=f"#{normalized_tag}",
                platform=platform,
                category=category,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

        hashtag = self._hashtags[key]
        hashtag.usage_count += 1
        hashtag.reach += reach
        hashtag.engagement += engagement
        hashtag.updated_at = datetime.utcnow()

        # Add to performance history
        hashtag.performance_history.append(
            {
                "date": datetime.utcnow().isoformat(),
                "reach": reach,
                "engagement": engagement,
            }
        )

        logger.info(f"Tracked hashtag {hashtag.tag} on {platform.value}")
        return hashtag

    def get_trending_hashtags(
        self,
        platform: PlatformType,
        category: Optional[str] = None,
        limit: int = 20,
        refresh: bool = False,
    ) -> List[Hashtag]:
        """
        Get trending hashtags for a platform.

        Args:
            platform: Platform to get trends for
            category: Optional category filter
            limit: Maximum hashtags to return
            refresh: Force refresh from API

        Returns:
            List of trending Hashtag objects
        """
        # In production, fetch from platform API
        # For now, return top performing tracked hashtags
        platform_hashtags = [
            h
            for h in self._hashtags.values()
            if h.platform == platform and (not category or h.category == category)
        ]

        # Calculate trend score based on recent performance
        for hashtag in platform_hashtags:
            hashtag.trend_score = self._calculate_trend_score(hashtag)
            hashtag.is_trending = hashtag.trend_score > 70

        # Sort by trend score
        platform_hashtags.sort(key=lambda h: h.trend_score, reverse=True)

        logger.info(f"Retrieved {len(platform_hashtags[:limit])} trending hashtags for {platform.value}")
        return platform_hashtags[:limit]

    def _calculate_trend_score(self, hashtag: Hashtag) -> float:
        """
        Calculate trending score for a hashtag.

        Args:
            hashtag: Hashtag to score

        Returns:
            Score from 0-100
        """
        # Simple scoring based on recent usage and engagement
        if not hashtag.performance_history:
            return 0.0

        # Recent performance (last 7 days)
        recent_threshold = datetime.utcnow() - timedelta(days=7)
        recent_performances = [
            p
            for p in hashtag.performance_history
            if datetime.fromisoformat(p["date"]) > recent_threshold
        ]

        if not recent_performances:
            return 0.0

        recent_engagement = sum(p["engagement"] for p in recent_performances)
        recent_reach = sum(p["reach"] for p in recent_performances)

        # Normalize to 0-100 scale
        engagement_score = min(100, recent_engagement / 10)  # 1000+ engagement = max score
        reach_score = min(100, recent_reach / 100)  # 10000+ reach = max score
        frequency_score = min(100, len(recent_performances) * 20)  # 5+ uses = max score

        # Weighted average
        trend_score = (engagement_score * 0.5 + reach_score * 0.3 + frequency_score * 0.2)

        return round(trend_score, 2)

    def suggest_hashtags(
        self,
        content: str,
        platform: PlatformType,
        category: Optional[str] = None,
        limit: int = 10,
    ) -> List[str]:
        """
        Suggest relevant hashtags for content.

        Args:
            content: Post content text
            platform: Target platform
            category: Optional category
            limit: Maximum suggestions

        Returns:
            List of suggested hashtag strings
        """
        suggestions = []

        # Get trending hashtags for platform
        trending = self.get_trending_hashtags(platform, category, limit=30)

        # Simple keyword matching (in production, use NLP/ML)
        content_lower = content.lower()
        for hashtag in trending:
            tag_text = hashtag.tag.lstrip("#").lower()
            if tag_text in content_lower or any(
                word in content_lower for word in tag_text.split("_")
            ):
                suggestions.append(hashtag.tag)

        # Add high-performing hashtags from same category
        if category:
            category_hashtags = [
                h
                for h in self._hashtags.values()
                if h.platform == platform and h.category == category
            ]
            category_hashtags.sort(key=lambda h: h.engagement, reverse=True)

            for hashtag in category_hashtags[:limit]:
                if hashtag.tag not in suggestions:
                    suggestions.append(hashtag.tag)

        logger.info(f"Generated {len(suggestions[:limit])} hashtag suggestions")
        return suggestions[:limit]

    def get_related_hashtags(
        self, tag: str, platform: PlatformType, limit: int = 10
    ) -> List[str]:
        """
        Get hashtags related to a given hashtag.

        Args:
            tag: Source hashtag
            platform: Platform
            limit: Maximum related tags

        Returns:
            List of related hashtag strings
        """
        normalized_tag = tag.strip().lstrip("#").lower()
        cache_key = f"{platform.value}:{normalized_tag}"

        if cache_key in self._related_cache:
            return self._related_cache[cache_key][:limit]

        # In production, fetch from platform API or use co-occurrence analysis
        # For now, return hashtags from same category
        key = f"{platform.value}:{normalized_tag}"
        if key not in self._hashtags:
            return []

        source_hashtag = self._hashtags[key]
        related = []

        if source_hashtag.related_hashtags:
            related = source_hashtag.related_hashtags[:limit]
        elif source_hashtag.category:
            # Get other hashtags from same category
            category_hashtags = [
                h.tag
                for h in self._hashtags.values()
                if h.platform == platform
                and h.category == source_hashtag.category
                and h.tag != source_hashtag.tag
            ]
            related = category_hashtags[:limit]

        self._related_cache[cache_key] = related
        return related

    def create_hashtag_set(self, name: str, tags: List[str]) -> None:
        """
        Save a set of hashtags for reuse.

        Args:
            name: Set name
            tags: List of hashtags
        """
        # Normalize tags
        normalized_tags = [
            tag if tag.startswith("#") else f"#{tag}" for tag in tags
        ]

        self._saved_sets[name] = normalized_tags

        # Update hashtags with set membership
        for tag in normalized_tags:
            for hashtag in self._hashtags.values():
                if hashtag.tag.lower() == tag.lower():
                    if name not in hashtag.saved_sets:
                        hashtag.saved_sets.append(name)

        logger.info(f"Created hashtag set '{name}' with {len(normalized_tags)} tags")

    def get_hashtag_set(self, name: str) -> List[str]:
        """
        Get a saved hashtag set.

        Args:
            name: Set name

        Returns:
            List of hashtags in the set

        Raises:
            ValueError: If set not found
        """
        if name not in self._saved_sets:
            raise ValueError(f"Hashtag set '{name}' not found")

        return self._saved_sets[name]

    def list_hashtag_sets(self) -> List[str]:
        """
        List all saved hashtag sets.

        Returns:
            List of set names
        """
        return list(self._saved_sets.keys())

    def delete_hashtag_set(self, name: str) -> bool:
        """
        Delete a saved hashtag set.

        Args:
            name: Set name

        Returns:
            True if deleted, False if not found
        """
        if name in self._saved_sets:
            # Remove from hashtags
            for hashtag in self._hashtags.values():
                if name in hashtag.saved_sets:
                    hashtag.saved_sets.remove(name)

            del self._saved_sets[name]
            logger.info(f"Deleted hashtag set '{name}'")
            return True
        return False

    def get_hashtag_performance(
        self, tag: str, platform: PlatformType, days: int = 30
    ) -> Dict[str, Any]:
        """
        Get performance metrics for a hashtag.

        Args:
            tag: Hashtag to analyze
            platform: Platform
            days: Number of days to analyze

        Returns:
            Performance metrics dictionary
        """
        normalized_tag = tag.strip().lstrip("#").lower()
        key = f"{platform.value}:{normalized_tag}"

        if key not in self._hashtags:
            return {
                "tag": f"#{normalized_tag}",
                "platform": platform.value,
                "tracked": False,
            }

        hashtag = self._hashtags[key]

        # Filter recent performance
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_history = [
            p
            for p in hashtag.performance_history
            if datetime.fromisoformat(p["date"]) > cutoff_date
        ]

        total_reach = sum(p["reach"] for p in recent_history)
        total_engagement = sum(p["engagement"] for p in recent_history)
        avg_engagement_rate = (
            (total_engagement / total_reach * 100) if total_reach > 0 else 0.0
        )

        return {
            "tag": hashtag.tag,
            "platform": platform.value,
            "tracked": True,
            "category": hashtag.category,
            "usage_count": len(recent_history),
            "total_reach": total_reach,
            "total_engagement": total_engagement,
            "avg_engagement_rate": round(avg_engagement_rate, 2),
            "trend_score": hashtag.trend_score,
            "is_trending": hashtag.is_trending,
            "saved_sets": hashtag.saved_sets,
        }

    def analyze_hashtag_effectiveness(
        self, tags: List[str], platform: PlatformType
    ) -> Dict[str, Any]:
        """
        Analyze the effectiveness of a list of hashtags.

        Args:
            tags: List of hashtags to analyze
            platform: Platform

        Returns:
            Effectiveness analysis
        """
        hashtag_scores = []
        total_reach = 0
        total_engagement = 0

        for tag in tags:
            performance = self.get_hashtag_performance(tag, platform)

            if performance.get("tracked"):
                hashtag_scores.append(
                    {
                        "tag": performance["tag"],
                        "engagement_rate": performance["avg_engagement_rate"],
                        "reach": performance["total_reach"],
                        "trend_score": performance["trend_score"],
                        "is_trending": performance["is_trending"],
                    }
                )
                total_reach += performance["total_reach"]
                total_engagement += performance["total_engagement"]

        # Sort by engagement rate
        hashtag_scores.sort(key=lambda x: x["engagement_rate"], reverse=True)

        avg_engagement_rate = (
            (total_engagement / total_reach * 100) if total_reach > 0 else 0.0
        )

        trending_count = sum(1 for h in hashtag_scores if h["is_trending"])

        return {
            "platform": platform.value,
            "total_hashtags": len(tags),
            "tracked_hashtags": len(hashtag_scores),
            "trending_count": trending_count,
            "total_reach": total_reach,
            "total_engagement": total_engagement,
            "avg_engagement_rate": round(avg_engagement_rate, 2),
            "hashtags": hashtag_scores,
            "recommendations": self._generate_recommendations(hashtag_scores),
        }

    def _generate_recommendations(
        self, hashtag_scores: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on hashtag analysis."""
        recommendations = []

        if not hashtag_scores:
            recommendations.append("No tracked hashtags found. Start tracking hashtags to get insights.")
            return recommendations

        # Check for low performers
        low_performers = [h for h in hashtag_scores if h["engagement_rate"] < 1.0]
        if low_performers:
            recommendations.append(
                f"Consider replacing {len(low_performers)} low-performing hashtags with trending alternatives."
            )

        # Check for trending
        trending = [h for h in hashtag_scores if h["is_trending"]]
        if len(trending) < len(hashtag_scores) * 0.3:
            recommendations.append(
                "Add more trending hashtags to increase visibility."
            )

        # Check mix
        if len(hashtag_scores) < 3:
            recommendations.append(
                "Use at least 3-5 hashtags for optimal reach."
            )
        elif len(hashtag_scores) > 10:
            recommendations.append(
                "Too many hashtags may reduce engagement. Focus on 5-10 highly relevant tags."
            )

        return recommendations

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get hashtag tracking statistics.

        Returns:
            Statistics dictionary
        """
        total_tracked = len(self._hashtags)
        trending_count = sum(1 for h in self._hashtags.values() if h.is_trending)

        platform_breakdown = {}
        for hashtag in self._hashtags.values():
            platform = hashtag.platform.value
            if platform not in platform_breakdown:
                platform_breakdown[platform] = 0
            platform_breakdown[platform] += 1

        return {
            "total_hashtags_tracked": total_tracked,
            "trending_hashtags": trending_count,
            "saved_sets": len(self._saved_sets),
            "by_platform": platform_breakdown,
        }
