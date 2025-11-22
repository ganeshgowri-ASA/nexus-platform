"""
Social Media Module - Engagement Management.

This module provides unified inbox functionality for managing comments, messages,
and other engagements across all social media platforms with sentiment analysis.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from .platforms import BasePlatform
from .social_types import (
    Engagement,
    EngagementType,
    PlatformType,
    Post,
    SentimentType,
)

logger = logging.getLogger(__name__)


class EngagementError(Exception):
    """Base exception for engagement errors."""

    pass


class EngagementManager:
    """Unified inbox manager for all social media engagements."""

    def __init__(self):
        """Initialize engagement manager."""
        self._engagements: Dict[UUID, Engagement] = {}
        self._platforms: Dict[PlatformType, BasePlatform] = {}
        self._sentiment_cache: Dict[str, Tuple[SentimentType, float]] = {}

    def register_platform(
        self, platform_type: PlatformType, platform: BasePlatform
    ) -> None:
        """
        Register a platform for engagement tracking.

        Args:
            platform_type: Platform type
            platform: Platform instance
        """
        self._platforms[platform_type] = platform
        logger.info(f"Registered platform {platform_type.value} for engagement tracking")

    async def fetch_engagements(
        self,
        platform: Optional[PlatformType] = None,
        post_id: Optional[UUID] = None,
        limit: int = 100,
    ) -> List[Engagement]:
        """
        Fetch engagements from platforms.

        Args:
            platform: Optional specific platform to fetch from
            post_id: Optional specific post to fetch engagements for
            limit: Maximum engagements to fetch

        Returns:
            List of Engagement objects
        """
        try:
            engagements = []

            # Determine which platforms to fetch from
            platforms_to_fetch = (
                [platform] if platform else list(self._platforms.keys())
            )

            for platform_type in platforms_to_fetch:
                if platform_type not in self._platforms:
                    continue

                platform_instance = self._platforms[platform_type]

                # Fetch from platform
                platform_engagements = await platform_instance.get_engagements(
                    post_id=str(post_id) if post_id else None, limit=limit
                )

                # Analyze sentiment for each engagement
                for engagement in platform_engagements:
                    if engagement.content:
                        sentiment, score = self._analyze_sentiment(engagement.content)
                        engagement.sentiment = sentiment
                        engagement.sentiment_score = score
                        engagement.priority = self._calculate_priority(engagement)

                    self._engagements[engagement.id] = engagement
                    engagements.append(engagement)

            logger.info(f"Fetched {len(engagements)} engagements")
            return engagements

        except Exception as e:
            logger.error(f"Failed to fetch engagements: {e}")
            raise EngagementError(f"Failed to fetch engagements: {e}")

    def _analyze_sentiment(self, text: str) -> Tuple[SentimentType, float]:
        """
        Analyze sentiment of text.

        Args:
            text: Text to analyze

        Returns:
            Tuple of (SentimentType, score)
        """
        # Check cache first
        if text in self._sentiment_cache:
            return self._sentiment_cache[text]

        # Simple keyword-based sentiment analysis
        # In production, use NLP library like TextBlob or transformers
        positive_keywords = [
            "love",
            "great",
            "awesome",
            "excellent",
            "amazing",
            "fantastic",
            "wonderful",
            "good",
            "best",
            "thank",
            "thanks",
            "appreciate",
        ]
        negative_keywords = [
            "hate",
            "terrible",
            "awful",
            "bad",
            "worst",
            "horrible",
            "disappointing",
            "disappointed",
            "poor",
            "useless",
            "waste",
        ]

        text_lower = text.lower()
        positive_count = sum(1 for word in positive_keywords if word in text_lower)
        negative_count = sum(1 for word in negative_keywords if word in text_lower)

        # Calculate score
        if positive_count > negative_count:
            sentiment = SentimentType.POSITIVE
            score = min(1.0, positive_count / (positive_count + negative_count + 1))
        elif negative_count > positive_count:
            sentiment = SentimentType.NEGATIVE
            score = -min(1.0, negative_count / (positive_count + negative_count + 1))
        else:
            sentiment = SentimentType.NEUTRAL
            score = 0.0

        # Cache result
        self._sentiment_cache[text] = (sentiment, score)
        return sentiment, score

    def _calculate_priority(self, engagement: Engagement) -> int:
        """
        Calculate priority score for an engagement.

        Args:
            engagement: Engagement to prioritize

        Returns:
            Priority score (higher = more important)
        """
        priority = 0

        # Sentiment-based priority
        if engagement.sentiment == SentimentType.NEGATIVE:
            priority += 50  # High priority for negative sentiment
        elif engagement.sentiment == SentimentType.POSITIVE:
            priority += 10

        # Engagement type priority
        if engagement.engagement_type == EngagementType.DIRECT_MESSAGE:
            priority += 30
        elif engagement.engagement_type == EngagementType.MENTION:
            priority += 20
        elif engagement.engagement_type == EngagementType.COMMENT:
            priority += 15

        # Unread/unreplied priority
        if not engagement.is_read:
            priority += 10
        if not engagement.is_replied:
            priority += 5

        return priority

    def get_engagement(self, engagement_id: UUID) -> Optional[Engagement]:
        """
        Get an engagement by ID.

        Args:
            engagement_id: Engagement UUID

        Returns:
            Engagement object or None
        """
        return self._engagements.get(engagement_id)

    def get_engagements(
        self,
        platform: Optional[PlatformType] = None,
        sentiment: Optional[SentimentType] = None,
        engagement_type: Optional[EngagementType] = None,
        is_read: Optional[bool] = None,
        is_replied: Optional[bool] = None,
        min_priority: Optional[int] = None,
        sort_by: str = "priority",
        limit: Optional[int] = None,
    ) -> List[Engagement]:
        """
        Get filtered engagements.

        Args:
            platform: Filter by platform
            sentiment: Filter by sentiment
            engagement_type: Filter by type
            is_read: Filter by read status
            is_replied: Filter by reply status
            min_priority: Minimum priority score
            sort_by: Sort field (priority, created_at)
            limit: Maximum results

        Returns:
            List of filtered Engagement objects
        """
        engagements = list(self._engagements.values())

        # Apply filters
        if platform:
            engagements = [e for e in engagements if e.platform == platform]
        if sentiment:
            engagements = [e for e in engagements if e.sentiment == sentiment]
        if engagement_type:
            engagements = [
                e for e in engagements if e.engagement_type == engagement_type
            ]
        if is_read is not None:
            engagements = [e for e in engagements if e.is_read == is_read]
        if is_replied is not None:
            engagements = [e for e in engagements if e.is_replied == is_replied]
        if min_priority is not None:
            engagements = [e for e in engagements if e.priority >= min_priority]

        # Sort
        if sort_by == "priority":
            engagements.sort(key=lambda e: e.priority, reverse=True)
        elif sort_by == "created_at":
            engagements.sort(key=lambda e: e.created_at, reverse=True)

        # Limit
        if limit:
            engagements = engagements[:limit]

        return engagements

    async def reply_to_engagement(
        self, engagement_id: UUID, reply_text: str
    ) -> Dict[str, Any]:
        """
        Reply to an engagement.

        Args:
            engagement_id: Engagement UUID
            reply_text: Reply content

        Returns:
            Dictionary with reply result

        Raises:
            ValueError: If engagement not found
            EngagementError: If reply fails
        """
        if engagement_id not in self._engagements:
            raise ValueError(f"Engagement {engagement_id} not found")

        engagement = self._engagements[engagement_id]

        # Get platform instance
        if engagement.platform not in self._platforms:
            raise EngagementError(
                f"Platform {engagement.platform.value} not registered"
            )

        platform = self._platforms[engagement.platform]

        try:
            # Send reply via platform
            result = await platform.reply_to_engagement(
                engagement.platform_engagement_id, reply_text
            )

            # Update engagement
            engagement.is_replied = True
            engagement.reply_content = reply_text
            engagement.replied_at = datetime.utcnow()

            logger.info(f"Replied to engagement {engagement_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to reply to engagement: {e}")
            raise EngagementError(f"Reply failed: {e}")

    def mark_as_read(self, engagement_id: UUID) -> bool:
        """
        Mark engagement as read.

        Args:
            engagement_id: Engagement UUID

        Returns:
            True if marked, False if not found
        """
        if engagement_id in self._engagements:
            self._engagements[engagement_id].is_read = True
            logger.info(f"Marked engagement {engagement_id} as read")
            return True
        return False

    def mark_multiple_as_read(self, engagement_ids: List[UUID]) -> int:
        """
        Mark multiple engagements as read.

        Args:
            engagement_ids: List of engagement UUIDs

        Returns:
            Number of engagements marked as read
        """
        count = 0
        for engagement_id in engagement_ids:
            if self.mark_as_read(engagement_id):
                count += 1
        return count

    def get_inbox_stats(self) -> Dict[str, Any]:
        """
        Get inbox statistics.

        Returns:
            Dictionary with inbox stats
        """
        total = len(self._engagements)
        unread = sum(1 for e in self._engagements.values() if not e.is_read)
        unreplied = sum(1 for e in self._engagements.values() if not e.is_replied)

        sentiment_breakdown = {
            "positive": sum(
                1
                for e in self._engagements.values()
                if e.sentiment == SentimentType.POSITIVE
            ),
            "negative": sum(
                1
                for e in self._engagements.values()
                if e.sentiment == SentimentType.NEGATIVE
            ),
            "neutral": sum(
                1
                for e in self._engagements.values()
                if e.sentiment == SentimentType.NEUTRAL
            ),
        }

        type_breakdown = {}
        for engagement_type in EngagementType:
            count = sum(
                1
                for e in self._engagements.values()
                if e.engagement_type == engagement_type
            )
            if count > 0:
                type_breakdown[engagement_type.value] = count

        platform_breakdown = {}
        for platform in PlatformType:
            count = sum(
                1 for e in self._engagements.values() if e.platform == platform
            )
            if count > 0:
                platform_breakdown[platform.value] = count

        return {
            "total": total,
            "unread": unread,
            "unreplied": unreplied,
            "by_sentiment": sentiment_breakdown,
            "by_type": type_breakdown,
            "by_platform": platform_breakdown,
            "high_priority": sum(
                1 for e in self._engagements.values() if e.priority >= 50
            ),
        }

    def get_auto_response_suggestions(
        self, engagement_id: UUID
    ) -> List[str]:
        """
        Get AI-powered auto-response suggestions.

        Args:
            engagement_id: Engagement UUID

        Returns:
            List of suggested responses
        """
        if engagement_id not in self._engagements:
            return []

        engagement = self._engagements[engagement_id]

        # Generate context-aware suggestions based on sentiment and type
        suggestions = []

        if engagement.sentiment == SentimentType.POSITIVE:
            suggestions = [
                "Thank you so much for your kind words! We really appreciate your support. 😊",
                "We're thrilled to hear you're enjoying it! Thanks for sharing!",
                "Your feedback means the world to us. Thank you! ❤️",
            ]
        elif engagement.sentiment == SentimentType.NEGATIVE:
            suggestions = [
                "We're sorry to hear about your experience. Could you please DM us with more details so we can help?",
                "Thank you for bringing this to our attention. We'd like to make this right. Please contact us directly.",
                "We apologize for the inconvenience. Our team is looking into this. We'll reach out soon.",
            ]
        else:  # Neutral
            suggestions = [
                "Thank you for reaching out! How can we help you today?",
                "Thanks for your message! We appreciate you taking the time to connect.",
                "We've received your message and will get back to you soon!",
            ]

        return suggestions
