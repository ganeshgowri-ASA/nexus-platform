"""
Wiki Analytics Service

Analytics and metrics tracking for wiki pages including page views, popular pages,
contributor statistics, activity heatmaps, and search analytics.

Author: NEXUS Platform Team
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy import func, desc, and_, or_, case
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.utils import get_logger
from modules.wiki.models import (
    WikiPage, WikiAnalytics, WikiHistory, WikiComment,
    WikiAttachment, WikiCategory, page_watchers
)

logger = get_logger(__name__)


class AnalyticsService:
    """Provides analytics and metrics for wiki pages and users."""

    def __init__(self, db: Session):
        """
        Initialize AnalyticsService.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def track_page_view(
        self,
        page_id: int,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Track a page view event.

        Args:
            page_id: ID of the viewed page
            user_id: Optional ID of viewing user
            session_id: Optional session identifier
            ip_address: Optional IP address
            user_agent: Optional user agent string

        Returns:
            True if tracking succeeded, False otherwise

        Example:
            >>> service = AnalyticsService(db)
            >>> service.track_page_view(
            ...     page_id=123,
            ...     user_id=1,
            ...     session_id='abc123',
            ...     ip_address='192.168.1.1'
            ... )
        """
        try:
            analytics = WikiAnalytics(
                page_id=page_id,
                user_id=user_id,
                event_type='page_view',
                event_data={
                    'timestamp': datetime.utcnow().isoformat()
                },
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent
            )

            self.db.add(analytics)
            self.db.commit()

            logger.debug(f"Tracked page view for page {page_id}")
            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error tracking page view: {str(e)}")
            return False

    def track_event(
        self,
        page_id: int,
        event_type: str,
        user_id: Optional[int] = None,
        event_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Track a custom analytics event.

        Args:
            page_id: ID of the page
            event_type: Type of event (e.g., 'search', 'export', 'share')
            user_id: Optional user ID
            event_data: Optional event data dictionary

        Returns:
            True if tracking succeeded, False otherwise

        Example:
            >>> service.track_event(
            ...     page_id=123,
            ...     event_type='export',
            ...     user_id=1,
            ...     event_data={'format': 'pdf'}
            ... )
        """
        try:
            analytics = WikiAnalytics(
                page_id=page_id,
                user_id=user_id,
                event_type=event_type,
                event_data=event_data or {}
            )

            self.db.add(analytics)
            self.db.commit()

            logger.debug(f"Tracked event '{event_type}' for page {page_id}")
            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error tracking event: {str(e)}")
            return False

    def get_page_views(
        self,
        page_id: int,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> int:
        """
        Get total page views for a page.

        Args:
            page_id: ID of the page
            date_from: Optional start date filter
            date_to: Optional end date filter

        Returns:
            Total number of page views

        Example:
            >>> views = service.get_page_views(123)
            >>> print(f"Total views: {views}")
        """
        try:
            query = self.db.query(func.count(WikiAnalytics.id)).filter(
                WikiAnalytics.page_id == page_id,
                WikiAnalytics.event_type == 'page_view'
            )

            if date_from:
                query = query.filter(WikiAnalytics.created_at >= date_from)

            if date_to:
                query = query.filter(WikiAnalytics.created_at <= date_to)

            return query.scalar() or 0

        except SQLAlchemyError as e:
            logger.error(f"Error getting page views: {str(e)}")
            return 0

    def get_unique_page_views(
        self,
        page_id: int,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> int:
        """
        Get unique page views (by user or session).

        Args:
            page_id: ID of the page
            date_from: Optional start date filter
            date_to: Optional end date filter

        Returns:
            Number of unique viewers

        Example:
            >>> unique_views = service.get_unique_page_views(123)
        """
        try:
            # Count unique users and sessions
            user_query = self.db.query(
                func.count(func.distinct(WikiAnalytics.user_id))
            ).filter(
                WikiAnalytics.page_id == page_id,
                WikiAnalytics.event_type == 'page_view',
                WikiAnalytics.user_id.isnot(None)
            )

            session_query = self.db.query(
                func.count(func.distinct(WikiAnalytics.session_id))
            ).filter(
                WikiAnalytics.page_id == page_id,
                WikiAnalytics.event_type == 'page_view',
                WikiAnalytics.session_id.isnot(None),
                WikiAnalytics.user_id.is_(None)
            )

            if date_from:
                user_query = user_query.filter(WikiAnalytics.created_at >= date_from)
                session_query = session_query.filter(WikiAnalytics.created_at >= date_from)

            if date_to:
                user_query = user_query.filter(WikiAnalytics.created_at <= date_to)
                session_query = session_query.filter(WikiAnalytics.created_at <= date_to)

            unique_users = user_query.scalar() or 0
            unique_sessions = session_query.scalar() or 0

            return unique_users + unique_sessions

        except SQLAlchemyError as e:
            logger.error(f"Error getting unique page views: {str(e)}")
            return 0

    def get_popular_pages(
        self,
        limit: int = 10,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        category_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get most popular pages by view count.

        Args:
            limit: Maximum number of pages to return
            date_from: Optional start date filter
            date_to: Optional end date filter
            category_id: Optional category filter

        Returns:
            List of dictionaries with page info and view counts

        Example:
            >>> popular = service.get_popular_pages(limit=5)
            >>> for page_data in popular:
            ...     print(f"{page_data['title']}: {page_data['views']} views")
        """
        try:
            # Subquery for view counts
            view_counts = self.db.query(
                WikiAnalytics.page_id,
                func.count(WikiAnalytics.id).label('view_count')
            ).filter(
                WikiAnalytics.event_type == 'page_view'
            )

            if date_from:
                view_counts = view_counts.filter(WikiAnalytics.created_at >= date_from)

            if date_to:
                view_counts = view_counts.filter(WikiAnalytics.created_at <= date_to)

            view_counts = view_counts.group_by(
                WikiAnalytics.page_id
            ).subquery()

            # Join with pages
            query = self.db.query(
                WikiPage,
                view_counts.c.view_count
            ).join(
                view_counts,
                WikiPage.id == view_counts.c.page_id
            ).filter(
                WikiPage.is_deleted == False
            )

            if category_id:
                query = query.filter(WikiPage.category_id == category_id)

            results = query.order_by(
                desc(view_counts.c.view_count)
            ).limit(limit).all()

            popular_pages = []
            for page, view_count in results:
                popular_pages.append({
                    'page_id': page.id,
                    'title': page.title,
                    'slug': page.slug,
                    'views': view_count,
                    'category_id': page.category_id,
                    'created_at': page.created_at,
                    'updated_at': page.updated_at
                })

            return popular_pages

        except SQLAlchemyError as e:
            logger.error(f"Error getting popular pages: {str(e)}")
            return []

    def get_contributor_statistics(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get statistics about top contributors.

        Args:
            date_from: Optional start date filter
            date_to: Optional end date filter
            limit: Maximum number of contributors

        Returns:
            List of contributor statistics

        Example:
            >>> contributors = service.get_contributor_statistics(limit=10)
            >>> for contrib in contributors:
            ...     print(f"User {contrib['user_id']}: {contrib['total_edits']} edits")
        """
        try:
            query = self.db.query(
                WikiHistory.changed_by.label('user_id'),
                func.count(WikiHistory.id).label('total_edits'),
                func.count(func.distinct(WikiHistory.page_id)).label('pages_edited'),
                func.max(WikiHistory.changed_at).label('last_edit'),
                func.sum(WikiHistory.diff_size).label('total_changes')
            ).filter(
                WikiHistory.changed_by.isnot(None)
            )

            if date_from:
                query = query.filter(WikiHistory.changed_at >= date_from)

            if date_to:
                query = query.filter(WikiHistory.changed_at <= date_to)

            results = query.group_by(
                WikiHistory.changed_by
            ).order_by(
                desc('total_edits')
            ).limit(limit).all()

            contributors = []
            for user_id, total_edits, pages_edited, last_edit, total_changes in results:
                contributors.append({
                    'user_id': user_id,
                    'total_edits': total_edits,
                    'pages_edited': pages_edited,
                    'last_edit': last_edit,
                    'total_changes': total_changes or 0
                })

            return contributors

        except SQLAlchemyError as e:
            logger.error(f"Error getting contributor statistics: {str(e)}")
            return []

    def get_activity_heatmap(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        granularity: str = 'day'
    ) -> Dict[str, int]:
        """
        Get activity heatmap data.

        Args:
            date_from: Start date (defaults to 90 days ago)
            date_to: End date (defaults to now)
            granularity: Time granularity ('hour', 'day', 'week', 'month')

        Returns:
            Dictionary mapping time periods to activity counts

        Example:
            >>> heatmap = service.get_activity_heatmap(granularity='day')
            >>> for date, count in heatmap.items():
            ...     print(f"{date}: {count} activities")
        """
        try:
            if not date_from:
                date_from = datetime.utcnow() - timedelta(days=90)

            if not date_to:
                date_to = datetime.utcnow()

            # Query for page edits
            edits = self.db.query(
                func.date_trunc(granularity, WikiHistory.changed_at).label('period'),
                func.count(WikiHistory.id).label('count')
            ).filter(
                WikiHistory.changed_at >= date_from,
                WikiHistory.changed_at <= date_to
            ).group_by('period').all()

            # Query for comments
            comments = self.db.query(
                func.date_trunc(granularity, WikiComment.created_at).label('period'),
                func.count(WikiComment.id).label('count')
            ).filter(
                WikiComment.created_at >= date_from,
                WikiComment.created_at <= date_to,
                WikiComment.is_deleted == False
            ).group_by('period').all()

            # Combine activities
            activity_map = defaultdict(int)

            for period, count in edits:
                period_str = period.isoformat()
                activity_map[period_str] += count

            for period, count in comments:
                period_str = period.isoformat()
                activity_map[period_str] += count

            return dict(activity_map)

        except SQLAlchemyError as e:
            logger.error(f"Error getting activity heatmap: {str(e)}")
            return {}

    def get_page_analytics_summary(
        self,
        page_id: int,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive analytics summary for a page.

        Args:
            page_id: ID of the page
            date_from: Optional start date
            date_to: Optional end date

        Returns:
            Dictionary with analytics summary

        Example:
            >>> summary = service.get_page_analytics_summary(123)
            >>> print(f"Views: {summary['total_views']}")
        """
        try:
            page = self.db.query(WikiPage).filter(WikiPage.id == page_id).first()
            if not page:
                return {}

            # Get view statistics
            total_views = self.get_page_views(page_id, date_from, date_to)
            unique_views = self.get_unique_page_views(page_id, date_from, date_to)

            # Get edit count
            edit_query = self.db.query(func.count(WikiHistory.id)).filter(
                WikiHistory.page_id == page_id
            )
            if date_from:
                edit_query = edit_query.filter(WikiHistory.changed_at >= date_from)
            if date_to:
                edit_query = edit_query.filter(WikiHistory.changed_at <= date_to)
            total_edits = edit_query.scalar() or 0

            # Get comment count
            comment_query = self.db.query(func.count(WikiComment.id)).filter(
                WikiComment.page_id == page_id,
                WikiComment.is_deleted == False
            )
            if date_from:
                comment_query = comment_query.filter(WikiComment.created_at >= date_from)
            if date_to:
                comment_query = comment_query.filter(WikiComment.created_at <= date_to)
            total_comments = comment_query.scalar() or 0

            # Get contributor count
            contributors = self.db.query(
                func.count(func.distinct(WikiHistory.changed_by))
            ).filter(
                WikiHistory.page_id == page_id
            ).scalar() or 0

            # Get attachment count
            attachments = self.db.query(func.count(WikiAttachment.id)).filter(
                WikiAttachment.page_id == page_id,
                WikiAttachment.is_deleted == False
            ).scalar() or 0

            return {
                'page_id': page_id,
                'title': page.title,
                'total_views': total_views,
                'unique_views': unique_views,
                'total_edits': total_edits,
                'total_comments': total_comments,
                'total_contributors': contributors,
                'total_attachments': attachments,
                'current_version': page.current_version,
                'created_at': page.created_at,
                'updated_at': page.updated_at,
                'last_viewed_at': page.last_viewed_at,
                'view_to_edit_ratio': round(total_views / max(total_edits, 1), 2)
            }

        except SQLAlchemyError as e:
            logger.error(f"Error getting page analytics summary: {str(e)}")
            return {}

    def get_search_analytics(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get analytics about search queries.

        Args:
            date_from: Optional start date
            date_to: Optional end date
            limit: Maximum number of results

        Returns:
            List of popular search queries

        Example:
            >>> searches = service.get_search_analytics(limit=10)
        """
        try:
            query = self.db.query(
                WikiAnalytics.event_data['query'].astext.label('search_query'),
                func.count(WikiAnalytics.id).label('search_count')
            ).filter(
                WikiAnalytics.event_type == 'search'
            )

            if date_from:
                query = query.filter(WikiAnalytics.created_at >= date_from)

            if date_to:
                query = query.filter(WikiAnalytics.created_at <= date_to)

            results = query.group_by(
                'search_query'
            ).order_by(
                desc('search_count')
            ).limit(limit).all()

            searches = []
            for search_query, search_count in results:
                if search_query:
                    searches.append({
                        'query': search_query,
                        'count': search_count
                    })

            return searches

        except SQLAlchemyError as e:
            logger.error(f"Error getting search analytics: {str(e)}")
            return []

    def get_category_statistics(self, category_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get statistics for categories.

        Args:
            category_id: Optional specific category ID

        Returns:
            List of category statistics

        Example:
            >>> stats = service.get_category_statistics()
        """
        try:
            query = self.db.query(
                WikiCategory.id,
                WikiCategory.name,
                func.count(WikiPage.id).label('page_count'),
                func.sum(WikiPage.view_count).label('total_views'),
                func.sum(WikiPage.comment_count).label('total_comments')
            ).outerjoin(
                WikiPage,
                and_(
                    WikiPage.category_id == WikiCategory.id,
                    WikiPage.is_deleted == False
                )
            )

            if category_id:
                query = query.filter(WikiCategory.id == category_id)

            results = query.group_by(
                WikiCategory.id,
                WikiCategory.name
            ).all()

            statistics = []
            for cat_id, name, page_count, total_views, total_comments in results:
                statistics.append({
                    'category_id': cat_id,
                    'category_name': name,
                    'page_count': page_count,
                    'total_views': total_views or 0,
                    'total_comments': total_comments or 0
                })

            return statistics

        except SQLAlchemyError as e:
            logger.error(f"Error getting category statistics: {str(e)}")
            return []

    def export_analytics_data(
        self,
        page_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        format: str = 'json'
    ) -> Dict[str, Any]:
        """
        Export analytics data for reporting.

        Args:
            page_id: Optional page ID filter
            date_from: Optional start date
            date_to: Optional end date
            format: Export format (currently only 'json')

        Returns:
            Dictionary with exported analytics data

        Example:
            >>> data = service.export_analytics_data(page_id=123)
        """
        try:
            export_data = {
                'export_date': datetime.utcnow().isoformat(),
                'date_from': date_from.isoformat() if date_from else None,
                'date_to': date_to.isoformat() if date_to else None,
                'page_id': page_id
            }

            if page_id:
                export_data['page_summary'] = self.get_page_analytics_summary(
                    page_id, date_from, date_to
                )
            else:
                export_data['popular_pages'] = self.get_popular_pages(
                    limit=50, date_from=date_from, date_to=date_to
                )
                export_data['top_contributors'] = self.get_contributor_statistics(
                    date_from=date_from, date_to=date_to, limit=50
                )
                export_data['search_analytics'] = self.get_search_analytics(
                    date_from=date_from, date_to=date_to, limit=100
                )
                export_data['activity_heatmap'] = self.get_activity_heatmap(
                    date_from=date_from, date_to=date_to, granularity='day'
                )
                export_data['category_statistics'] = self.get_category_statistics()

            return export_data

        except Exception as e:
            logger.error(f"Error exporting analytics data: {str(e)}")
            return {'error': str(e)}

    def get_trending_pages(
        self,
        limit: int = 10,
        time_window: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get trending pages based on recent activity.

        Args:
            limit: Maximum number of pages
            time_window: Time window in days to consider

        Returns:
            List of trending pages

        Example:
            >>> trending = service.get_trending_pages(limit=5, time_window=7)
        """
        try:
            date_from = datetime.utcnow() - timedelta(days=time_window)

            # Calculate trend score based on views, edits, and comments
            view_counts = self.db.query(
                WikiAnalytics.page_id,
                func.count(WikiAnalytics.id).label('recent_views')
            ).filter(
                WikiAnalytics.event_type == 'page_view',
                WikiAnalytics.created_at >= date_from
            ).group_by(WikiAnalytics.page_id).subquery()

            edit_counts = self.db.query(
                WikiHistory.page_id,
                func.count(WikiHistory.id).label('recent_edits')
            ).filter(
                WikiHistory.changed_at >= date_from
            ).group_by(WikiHistory.page_id).subquery()

            # Combine scores
            query = self.db.query(
                WikiPage,
                func.coalesce(view_counts.c.recent_views, 0).label('views'),
                func.coalesce(edit_counts.c.recent_edits, 0).label('edits')
            ).outerjoin(
                view_counts,
                WikiPage.id == view_counts.c.page_id
            ).outerjoin(
                edit_counts,
                WikiPage.id == edit_counts.c.page_id
            ).filter(
                WikiPage.is_deleted == False
            )

            # Calculate trend score (weighted combination)
            results = query.all()

            trending = []
            for page, views, edits in results:
                trend_score = (views * 1.0) + (edits * 3.0)

                if trend_score > 0:
                    trending.append({
                        'page_id': page.id,
                        'title': page.title,
                        'slug': page.slug,
                        'trend_score': trend_score,
                        'recent_views': views,
                        'recent_edits': edits
                    })

            # Sort by trend score
            trending.sort(key=lambda x: x['trend_score'], reverse=True)

            return trending[:limit]

        except SQLAlchemyError as e:
            logger.error(f"Error getting trending pages: {str(e)}")
            return []
