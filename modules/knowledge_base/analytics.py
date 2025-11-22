"""
Analytics Module

Usage analytics, search analytics, content gaps, and effectiveness metrics.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from .kb_types import ContentType
from .models import AnalyticsEvent, Article

logger = logging.getLogger(__name__)


class AnalyticsManager:
    """Manager for KB analytics and insights."""

    def __init__(self, db_session: Session):
        self.db = db_session

    async def track_event(
        self,
        event_type: str,
        content_id: Optional[UUID] = None,
        content_type: Optional[ContentType] = None,
        user_id: Optional[UUID] = None,
        session_id: str = "",
        metadata: Optional[Dict] = None,
        **kwargs,
    ) -> AnalyticsEvent:
        """Track an analytics event."""
        try:
            event = AnalyticsEvent(
                event_type=event_type,
                content_id=content_id,
                content_type=content_type.value if content_type else None,
                user_id=user_id,
                session_id=session_id,
                metadata=metadata or {},
                **kwargs,
            )

            self.db.add(event)
            self.db.commit()

            return event

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error tracking event: {str(e)}")
            raise

    async def get_content_stats(
        self,
        content_id: UUID,
        days: int = 30,
    ) -> Dict:
        """Get analytics for specific content."""
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)

            # Get view count
            views = (
                self.db.query(func.count(AnalyticsEvent.id))
                .filter(
                    and_(
                        AnalyticsEvent.content_id == content_id,
                        AnalyticsEvent.event_type == "view",
                        AnalyticsEvent.timestamp >= cutoff,
                    )
                )
                .scalar()
            ) or 0

            # Get unique users
            unique_users = (
                self.db.query(func.count(func.distinct(AnalyticsEvent.user_id)))
                .filter(
                    and_(
                        AnalyticsEvent.content_id == content_id,
                        AnalyticsEvent.timestamp >= cutoff,
                    )
                )
                .scalar()
            ) or 0

            return {
                "views": views,
                "unique_users": unique_users,
                "period_days": days,
            }

        except Exception as e:
            logger.error(f"Error getting content stats: {str(e)}")
            return {}

    async def get_popular_content(
        self,
        days: int = 7,
        limit: int = 10,
    ) -> List[Dict]:
        """Get most popular content."""
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)

            results = (
                self.db.query(
                    AnalyticsEvent.content_id,
                    func.count(AnalyticsEvent.id).label("view_count"),
                )
                .filter(
                    and_(
                        AnalyticsEvent.event_type == "view",
                        AnalyticsEvent.timestamp >= cutoff,
                    )
                )
                .group_by(AnalyticsEvent.content_id)
                .order_by(desc("view_count"))
                .limit(limit)
                .all()
            )

            return [{"content_id": r[0], "views": r[1]} for r in results]

        except Exception as e:
            logger.error(f"Error getting popular content: {str(e)}")
            return []

    async def get_search_analytics(self, days: int = 7) -> Dict:
        """Get search analytics."""
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)

            # Get search count
            searches = (
                self.db.query(func.count(AnalyticsEvent.id))
                .filter(
                    and_(
                        AnalyticsEvent.event_type == "search",
                        AnalyticsEvent.timestamp >= cutoff,
                    )
                )
                .scalar()
            ) or 0

            # Get top searches (from metadata)
            # This is simplified - in production, aggregate search queries

            return {
                "total_searches": searches,
                "period_days": days,
            }

        except Exception as e:
            logger.error(f"Error getting search analytics: {str(e)}")
            return {}
