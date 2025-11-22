"""
Wiki Collaboration Service

Real-time collaboration features for the NEXUS Wiki System including:
- Simultaneous editing support
- Change notifications and watchers
- Discussion threads and comments
- User mentions and reactions
- Edit conflict resolution

Author: NEXUS Platform Team
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from app.utils import get_logger
from modules.wiki.models import (
    WikiPage, WikiComment, page_watchers,
    WikiHistory
)
from modules.wiki.wiki_types import NotificationType

logger = get_logger(__name__)


class CollaborationService:
    """Manages collaborative editing and communication features."""

    def __init__(self, db: Session):
        """
        Initialize CollaborationService.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self._active_editors: Dict[int, Set[int]] = defaultdict(set)  # page_id -> set of user_ids

    # ========================================================================
    # COMMENTS AND DISCUSSIONS
    # ========================================================================

    def add_comment(
        self,
        page_id: int,
        author_id: int,
        content: str,
        parent_comment_id: Optional[int] = None,
        mentions: Optional[List[int]] = None
    ) -> Optional[WikiComment]:
        """
        Add a comment to a page.

        Args:
            page_id: Page ID
            author_id: Comment author ID
            content: Comment content
            parent_comment_id: Parent comment ID for replies
            mentions: List of mentioned user IDs

        Returns:
            Created WikiComment instance

        Example:
            >>> service = CollaborationService(db)
            >>> comment = service.add_comment(
            ...     page_id=123,
            ...     author_id=5,
            ...     content="Great article!",
            ...     mentions=[10, 15]
            ... )
        """
        try:
            # Verify page exists
            page = self.db.query(WikiPage).filter(WikiPage.id == page_id).first()
            if not page:
                logger.warning(f"Page {page_id} not found")
                return None

            # Verify parent comment if specified
            if parent_comment_id:
                parent = self.db.query(WikiComment).filter(
                    WikiComment.id == parent_comment_id,
                    WikiComment.page_id == page_id
                ).first()
                if not parent:
                    logger.warning(f"Parent comment {parent_comment_id} not found")
                    return None

            # Create comment
            comment = WikiComment(
                page_id=page_id,
                author_id=author_id,
                content=content,
                parent_comment_id=parent_comment_id,
                mentions=mentions or []
            )

            self.db.add(comment)

            # Update page comment count
            page.comment_count += 1

            self.db.commit()
            self.db.refresh(comment)

            # Send notifications
            self._notify_comment_added(comment, mentions or [])

            logger.info(f"Added comment {comment.id} to page {page_id}")
            return comment

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error adding comment: {str(e)}")
            return None

    def get_comments(
        self,
        page_id: int,
        include_resolved: bool = False,
        limit: int = 100
    ) -> List[WikiComment]:
        """
        Get comments for a page.

        Args:
            page_id: Page ID
            include_resolved: Include resolved comments
            limit: Maximum comments to return

        Returns:
            List of WikiComment instances

        Example:
            >>> comments = service.get_comments(123, include_resolved=True)
        """
        try:
            query = self.db.query(WikiComment).filter(
                WikiComment.page_id == page_id,
                WikiComment.is_deleted == False
            )

            if not include_resolved:
                query = query.filter(WikiComment.is_resolved == False)

            comments = query.order_by(
                WikiComment.created_at
            ).limit(limit).all()

            return comments

        except SQLAlchemyError as e:
            logger.error(f"Error getting comments: {str(e)}")
            return []

    def update_comment(
        self,
        comment_id: int,
        content: Optional[str] = None,
        is_resolved: Optional[bool] = None
    ) -> Optional[WikiComment]:
        """
        Update a comment.

        Args:
            comment_id: Comment ID
            content: New content
            is_resolved: Resolved status

        Returns:
            Updated WikiComment instance

        Example:
            >>> comment = service.update_comment(10, is_resolved=True)
        """
        try:
            comment = self.db.query(WikiComment).filter(
                WikiComment.id == comment_id
            ).first()

            if not comment:
                return None

            if content is not None:
                comment.content = content
            if is_resolved is not None:
                comment.is_resolved = is_resolved

            comment.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(comment)

            logger.info(f"Updated comment {comment_id}")
            return comment

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating comment: {str(e)}")
            return None

    def delete_comment(self, comment_id: int, hard_delete: bool = False) -> bool:
        """
        Delete a comment.

        Args:
            comment_id: Comment ID
            hard_delete: Permanently delete vs soft delete

        Returns:
            True if successful

        Example:
            >>> success = service.delete_comment(10)
        """
        try:
            comment = self.db.query(WikiComment).filter(
                WikiComment.id == comment_id
            ).first()

            if not comment:
                return False

            if hard_delete:
                # Update page comment count
                page = self.db.query(WikiPage).filter(
                    WikiPage.id == comment.page_id
                ).first()
                if page:
                    page.comment_count = max(0, page.comment_count - 1)

                self.db.delete(comment)
            else:
                comment.is_deleted = True

            self.db.commit()

            logger.info(f"Deleted comment {comment_id}")
            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting comment: {str(e)}")
            return False

    def add_reaction(
        self,
        comment_id: int,
        user_id: int,
        reaction: str
    ) -> bool:
        """
        Add a reaction to a comment.

        Args:
            comment_id: Comment ID
            user_id: User adding reaction
            reaction: Reaction emoji/type

        Returns:
            True if successful

        Example:
            >>> success = service.add_reaction(10, user_id=5, reaction="👍")
        """
        try:
            comment = self.db.query(WikiComment).filter(
                WikiComment.id == comment_id
            ).first()

            if not comment:
                return False

            # Initialize reactions dict if needed
            if not comment.reactions:
                comment.reactions = {}

            # Add user to reaction list
            if reaction not in comment.reactions:
                comment.reactions[reaction] = []

            if user_id not in comment.reactions[reaction]:
                comment.reactions[reaction].append(user_id)

            # Mark as modified for SQLAlchemy to detect change
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(comment, "reactions")

            self.db.commit()

            logger.debug(f"Added reaction '{reaction}' to comment {comment_id}")
            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error adding reaction: {str(e)}")
            return False

    # ========================================================================
    # PAGE WATCHERS AND NOTIFICATIONS
    # ========================================================================

    def add_watcher(self, page_id: int, user_id: int) -> bool:
        """
        Add a user as a watcher of a page.

        Args:
            page_id: Page ID
            user_id: User ID to watch

        Returns:
            True if successful

        Example:
            >>> success = service.add_watcher(123, user_id=5)
        """
        try:
            # Check if already watching
            existing = self.db.query(page_watchers).filter(
                page_watchers.c.page_id == page_id,
                page_watchers.c.user_id == user_id
            ).first()

            if existing:
                return True

            # Add watcher
            self.db.execute(
                page_watchers.insert().values(
                    page_id=page_id,
                    user_id=user_id,
                    created_at=datetime.utcnow()
                )
            )
            self.db.commit()

            logger.info(f"User {user_id} is now watching page {page_id}")
            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error adding watcher: {str(e)}")
            return False

    def remove_watcher(self, page_id: int, user_id: int) -> bool:
        """
        Remove a user from page watchers.

        Args:
            page_id: Page ID
            user_id: User ID

        Returns:
            True if successful

        Example:
            >>> success = service.remove_watcher(123, user_id=5)
        """
        try:
            self.db.execute(
                page_watchers.delete().where(
                    and_(
                        page_watchers.c.page_id == page_id,
                        page_watchers.c.user_id == user_id
                    )
                )
            )
            self.db.commit()

            logger.info(f"User {user_id} stopped watching page {page_id}")
            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error removing watcher: {str(e)}")
            return False

    def get_watchers(self, page_id: int) -> List[int]:
        """
        Get list of users watching a page.

        Args:
            page_id: Page ID

        Returns:
            List of user IDs

        Example:
            >>> watchers = service.get_watchers(123)
        """
        try:
            result = self.db.query(page_watchers.c.user_id).filter(
                page_watchers.c.page_id == page_id
            ).all()

            return [user_id for (user_id,) in result]

        except SQLAlchemyError as e:
            logger.error(f"Error getting watchers: {str(e)}")
            return []

    def notify_watchers(
        self,
        page_id: int,
        notification_type: NotificationType,
        data: Dict
    ) -> int:
        """
        Send notification to all page watchers.

        Args:
            page_id: Page ID
            notification_type: Type of notification
            data: Notification data

        Returns:
            Number of notifications sent

        Example:
            >>> count = service.notify_watchers(
            ...     123,
            ...     NotificationType.PAGE_EDITED,
            ...     {'editor_id': 5, 'changes': 'Updated content'}
            ... )
        """
        try:
            watchers = self.get_watchers(page_id)

            # In a real implementation, this would integrate with a notification system
            # For now, just log
            for user_id in watchers:
                logger.debug(
                    f"Would notify user {user_id} about {notification_type.value} "
                    f"on page {page_id}"
                )

            return len(watchers)

        except Exception as e:
            logger.error(f"Error notifying watchers: {str(e)}")
            return 0

    # ========================================================================
    # SIMULTANEOUS EDITING
    # ========================================================================

    def register_editor(
        self,
        page_id: int,
        user_id: int,
        session_id: Optional[str] = None
    ) -> bool:
        """
        Register a user as actively editing a page.

        Args:
            page_id: Page ID
            user_id: User ID
            session_id: Optional session identifier

        Returns:
            True if successful

        Example:
            >>> success = service.register_editor(123, user_id=5)
        """
        try:
            self._active_editors[page_id].add(user_id)
            logger.debug(f"User {user_id} started editing page {page_id}")
            return True

        except Exception as e:
            logger.error(f"Error registering editor: {str(e)}")
            return False

    def unregister_editor(self, page_id: int, user_id: int) -> bool:
        """
        Unregister a user from active editing.

        Args:
            page_id: Page ID
            user_id: User ID

        Returns:
            True if successful

        Example:
            >>> success = service.unregister_editor(123, user_id=5)
        """
        try:
            if page_id in self._active_editors:
                self._active_editors[page_id].discard(user_id)
                logger.debug(f"User {user_id} stopped editing page {page_id}")
            return True

        except Exception as e:
            logger.error(f"Error unregistering editor: {str(e)}")
            return False

    def get_active_editors(self, page_id: int) -> List[int]:
        """
        Get list of users currently editing a page.

        Args:
            page_id: Page ID

        Returns:
            List of user IDs

        Example:
            >>> editors = service.get_active_editors(123)
            >>> if editors:
            ...     print(f"{len(editors)} users are editing this page")
        """
        return list(self._active_editors.get(page_id, set()))

    def check_edit_conflict(
        self,
        page_id: int,
        user_id: int,
        base_version: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if there's an edit conflict.

        Args:
            page_id: Page ID
            user_id: User attempting to save
            base_version: Version user started editing from

        Returns:
            Tuple of (has_conflict, conflict_message)

        Example:
            >>> has_conflict, msg = service.check_edit_conflict(123, 5, base_version=10)
            >>> if has_conflict:
            ...     print(f"Conflict: {msg}")
        """
        try:
            page = self.db.query(WikiPage).filter(WikiPage.id == page_id).first()
            if not page:
                return True, "Page not found"

            if page.current_version > base_version:
                # Get who edited since
                recent_edits = self.db.query(WikiHistory).filter(
                    WikiHistory.page_id == page_id,
                    WikiHistory.version > base_version
                ).order_by(WikiHistory.version).all()

                editors = set(edit.changed_by for edit in recent_edits)
                editors.discard(user_id)  # Remove current user

                if editors:
                    msg = (
                        f"Page has been edited {len(recent_edits)} time(s) "
                        f"since version {base_version}. "
                        f"Current version is {page.current_version}."
                    )
                    return True, msg

            return False, None

        except Exception as e:
            logger.error(f"Error checking edit conflict: {str(e)}")
            return True, str(e)

    def get_recent_activity(
        self,
        page_id: int,
        hours: int = 24,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get recent activity on a page.

        Args:
            page_id: Page ID
            hours: Look back this many hours
            limit: Maximum activity items

        Returns:
            List of activity dictionaries

        Example:
            >>> activity = service.get_recent_activity(123, hours=48)
        """
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            activities = []

            # Get edits
            edits = self.db.query(WikiHistory).filter(
                WikiHistory.page_id == page_id,
                WikiHistory.changed_at >= since
            ).order_by(desc(WikiHistory.changed_at)).limit(limit).all()

            for edit in edits:
                activities.append({
                    'type': 'edit',
                    'user_id': edit.changed_by,
                    'timestamp': edit.changed_at,
                    'version': edit.version,
                    'change_type': edit.change_type.value,
                    'summary': edit.change_summary
                })

            # Get comments
            comments = self.db.query(WikiComment).filter(
                WikiComment.page_id == page_id,
                WikiComment.created_at >= since,
                WikiComment.is_deleted == False
            ).order_by(desc(WikiComment.created_at)).limit(limit).all()

            for comment in comments:
                activities.append({
                    'type': 'comment',
                    'user_id': comment.author_id,
                    'timestamp': comment.created_at,
                    'content': comment.content[:100]
                })

            # Sort by timestamp
            activities.sort(key=lambda x: x['timestamp'], reverse=True)

            return activities[:limit]

        except Exception as e:
            logger.error(f"Error getting recent activity: {str(e)}")
            return []

    def get_user_contributions(
        self,
        user_id: int,
        days: int = 30,
        limit: int = 100
    ) -> Dict[str, List]:
        """
        Get a user's contributions across all pages.

        Args:
            user_id: User ID
            days: Look back this many days
            limit: Maximum contributions per type

        Returns:
            Dictionary with edits and comments

        Example:
            >>> contributions = service.get_user_contributions(5, days=30)
            >>> print(f"Edits: {len(contributions['edits'])}")
        """
        try:
            since = datetime.utcnow() - timedelta(days=days)

            # Get edits
            edits = self.db.query(WikiHistory).filter(
                WikiHistory.changed_by == user_id,
                WikiHistory.changed_at >= since
            ).order_by(desc(WikiHistory.changed_at)).limit(limit).all()

            # Get comments
            comments = self.db.query(WikiComment).filter(
                WikiComment.author_id == user_id,
                WikiComment.created_at >= since,
                WikiComment.is_deleted == False
            ).order_by(desc(WikiComment.created_at)).limit(limit).all()

            return {
                'edits': [
                    {
                        'page_id': e.page_id,
                        'version': e.version,
                        'timestamp': e.changed_at,
                        'change_type': e.change_type.value,
                        'summary': e.change_summary
                    }
                    for e in edits
                ],
                'comments': [
                    {
                        'page_id': c.page_id,
                        'comment_id': c.id,
                        'timestamp': c.created_at,
                        'content': c.content
                    }
                    for c in comments
                ]
            }

        except Exception as e:
            logger.error(f"Error getting user contributions: {str(e)}")
            return {'edits': [], 'comments': []}

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _notify_comment_added(
        self,
        comment: WikiComment,
        mentioned_users: List[int]
    ) -> None:
        """Send notifications for new comment."""
        try:
            # Notify watchers
            self.notify_watchers(
                comment.page_id,
                NotificationType.COMMENT_ADDED,
                {
                    'comment_id': comment.id,
                    'author_id': comment.author_id,
                    'content': comment.content[:100]
                }
            )

            # Notify mentioned users
            for user_id in mentioned_users:
                logger.debug(
                    f"Would notify user {user_id} about mention "
                    f"in comment {comment.id}"
                )

        except Exception as e:
            logger.error(f"Error sending comment notifications: {str(e)}")
