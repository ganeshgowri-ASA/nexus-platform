"""
Wiki Versioning Service

Complete version history tracking, diff viewing, rollback, and branching capabilities.
Provides comprehensive version control for wiki pages.

Author: NEXUS Platform Team
"""

import difflib
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy import desc
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.utils import get_logger
from modules.wiki.models import WikiPage, WikiHistory
from modules.wiki.wiki_types import ChangeType

logger = get_logger(__name__)


class VersioningService:
    """Manages version history and provides version control operations."""

    def __init__(self, db: Session):
        """
        Initialize VersioningService.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_page_history(
        self,
        page_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[WikiHistory], int]:
        """
        Get version history for a page.

        Args:
            page_id: ID of the page
            limit: Maximum number of versions to return
            offset: Number of versions to skip

        Returns:
            Tuple of (list of history entries, total count)

        Example:
            >>> service = VersioningService(db)
            >>> history, total = service.get_page_history(123)
        """
        try:
            query = self.db.query(WikiHistory).filter(
                WikiHistory.page_id == page_id
            ).order_by(desc(WikiHistory.version))

            total_count = query.count()
            history = query.limit(limit).offset(offset).all()

            return history, total_count

        except SQLAlchemyError as e:
            logger.error(f"Error getting page history: {str(e)}")
            return [], 0

    def get_version(self, page_id: int, version: int) -> Optional[WikiHistory]:
        """
        Get a specific version of a page.

        Args:
            page_id: ID of the page
            version: Version number to retrieve

        Returns:
            WikiHistory instance or None if not found

        Example:
            >>> version_data = service.get_version(123, version=5)
        """
        try:
            return self.db.query(WikiHistory).filter(
                WikiHistory.page_id == page_id,
                WikiHistory.version == version
            ).first()

        except SQLAlchemyError as e:
            logger.error(f"Error getting version {version} for page {page_id}: {str(e)}")
            return None

    def get_latest_version(self, page_id: int) -> Optional[WikiHistory]:
        """
        Get the latest version of a page.

        Args:
            page_id: ID of the page

        Returns:
            WikiHistory instance or None if not found

        Example:
            >>> latest = service.get_latest_version(123)
        """
        try:
            return self.db.query(WikiHistory).filter(
                WikiHistory.page_id == page_id
            ).order_by(desc(WikiHistory.version)).first()

        except SQLAlchemyError as e:
            logger.error(f"Error getting latest version for page {page_id}: {str(e)}")
            return None

    def compare_versions(
        self,
        page_id: int,
        version1: int,
        version2: int,
        context_lines: int = 3
    ) -> Dict:
        """
        Compare two versions of a page and generate diff.

        Args:
            page_id: ID of the page
            version1: First version number
            version2: Second version number
            context_lines: Number of context lines to show in diff

        Returns:
            Dictionary with diff data (html_diff, unified_diff, changes)

        Example:
            >>> diff = service.compare_versions(123, version1=1, version2=2)
            >>> print(diff['html_diff'])
        """
        try:
            v1 = self.get_version(page_id, version1)
            v2 = self.get_version(page_id, version2)

            if not v1 or not v2:
                logger.warning(f"Version not found for comparison: {version1} or {version2}")
                return {
                    'error': 'One or both versions not found',
                    'html_diff': '',
                    'unified_diff': '',
                    'changes': {}
                }

            # Generate diffs
            v1_lines = v1.content.splitlines(keepends=True)
            v2_lines = v2.content.splitlines(keepends=True)

            # HTML diff
            html_diff = difflib.HtmlDiff()
            html_table = html_diff.make_table(
                v1_lines,
                v2_lines,
                fromdesc=f"Version {version1}",
                todesc=f"Version {version2}",
                context=True,
                numlines=context_lines
            )

            # Unified diff
            unified_diff = ''.join(difflib.unified_diff(
                v1_lines,
                v2_lines,
                fromfile=f"Version {version1}",
                tofile=f"Version {version2}",
                lineterm='',
                n=context_lines
            ))

            # Calculate changes
            changes = self._calculate_changes(v1_lines, v2_lines)

            # Title comparison
            title_changed = v1.title != v2.title

            return {
                'html_diff': html_table,
                'unified_diff': unified_diff,
                'changes': changes,
                'title_changed': title_changed,
                'old_title': v1.title,
                'new_title': v2.title,
                'version1': version1,
                'version2': version2,
                'changed_by_v1': v1.changed_by,
                'changed_by_v2': v2.changed_by,
                'changed_at_v1': v1.changed_at,
                'changed_at_v2': v2.changed_at,
            }

        except Exception as e:
            logger.error(f"Error comparing versions: {str(e)}")
            return {
                'error': str(e),
                'html_diff': '',
                'unified_diff': '',
                'changes': {}
            }

    def rollback_to_version(
        self,
        page_id: int,
        version: int,
        user_id: int,
        change_summary: Optional[str] = None
    ) -> Optional[WikiPage]:
        """
        Rollback a page to a specific version.

        Args:
            page_id: ID of the page
            version: Version number to rollback to
            user_id: ID of the user performing rollback
            change_summary: Optional summary of the rollback

        Returns:
            Updated WikiPage instance or None if failed

        Example:
            >>> page = service.rollback_to_version(123, version=5, user_id=1)
        """
        try:
            # Get the target version
            target_version = self.get_version(page_id, version)
            if not target_version:
                logger.warning(f"Version {version} not found for page {page_id}")
                return None

            # Get current page
            page = self.db.query(WikiPage).filter(WikiPage.id == page_id).first()
            if not page:
                logger.warning(f"Page {page_id} not found")
                return None

            if page.is_locked:
                logger.warning(f"Cannot rollback locked page {page_id}")
                return None

            # Store current version before rollback
            current_version = page.current_version

            # Restore content from target version
            page.title = target_version.title
            page.content = target_version.content
            page.current_version += 1
            page.updated_at = datetime.utcnow()

            # Create history entry for rollback
            summary = change_summary or f"Rolled back to version {version}"
            history = WikiHistory(
                page_id=page.id,
                version=page.current_version,
                title=page.title,
                content=page.content,
                change_type=ChangeType.RESTORED,
                change_summary=summary,
                changed_by=user_id,
                content_size=len(page.content.encode('utf-8')),
                metadata={
                    'rollback_from': current_version,
                    'rollback_to': version
                }
            )

            self.db.add(history)
            self.db.commit()
            self.db.refresh(page)

            logger.info(f"Rolled back page {page_id} from v{current_version} to v{version}")
            return page

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error rolling back page {page_id}: {str(e)}")
            return None

    def get_version_timeline(self, page_id: int) -> List[Dict]:
        """
        Get a timeline visualization of page versions.

        Args:
            page_id: ID of the page

        Returns:
            List of timeline events

        Example:
            >>> timeline = service.get_version_timeline(123)
        """
        try:
            history, _ = self.get_page_history(page_id, limit=100)

            timeline = []
            for entry in history:
                timeline.append({
                    'version': entry.version,
                    'change_type': entry.change_type.value,
                    'changed_by': entry.changed_by,
                    'changed_at': entry.changed_at,
                    'summary': entry.change_summary,
                    'content_size': entry.content_size,
                })

            return timeline

        except Exception as e:
            logger.error(f"Error getting version timeline: {str(e)}")
            return []

    def get_contributors(self, page_id: int) -> List[Dict]:
        """
        Get list of contributors to a page.

        Args:
            page_id: ID of the page

        Returns:
            List of contributor data with edit counts

        Example:
            >>> contributors = service.get_contributors(123)
        """
        try:
            from sqlalchemy import func

            results = self.db.query(
                WikiHistory.changed_by,
                func.count(WikiHistory.id).label('edit_count'),
                func.max(WikiHistory.changed_at).label('last_edit')
            ).filter(
                WikiHistory.page_id == page_id
            ).group_by(
                WikiHistory.changed_by
            ).order_by(
                desc('edit_count')
            ).all()

            contributors = []
            for user_id, edit_count, last_edit in results:
                contributors.append({
                    'user_id': user_id,
                    'edit_count': edit_count,
                    'last_edit': last_edit
                })

            return contributors

        except Exception as e:
            logger.error(f"Error getting contributors: {str(e)}")
            return []

    def get_change_statistics(self, page_id: int) -> Dict:
        """
        Get statistics about changes to a page.

        Args:
            page_id: ID of the page

        Returns:
            Dictionary with change statistics

        Example:
            >>> stats = service.get_change_statistics(123)
        """
        try:
            history, total = self.get_page_history(page_id, limit=1000)

            if not history:
                return {
                    'total_versions': 0,
                    'total_contributors': 0,
                    'avg_edit_size': 0,
                    'largest_edit': 0,
                    'smallest_edit': 0,
                }

            # Calculate statistics
            edit_sizes = [h.content_size for h in history]
            contributors = set(h.changed_by for h in history)

            return {
                'total_versions': total,
                'total_contributors': len(contributors),
                'avg_edit_size': sum(edit_sizes) / len(edit_sizes) if edit_sizes else 0,
                'largest_edit': max(edit_sizes) if edit_sizes else 0,
                'smallest_edit': min(edit_sizes) if edit_sizes else 0,
                'first_created': history[-1].changed_at if history else None,
                'last_modified': history[0].changed_at if history else None,
            }

        except Exception as e:
            logger.error(f"Error getting change statistics: {str(e)}")
            return {}

    def prune_old_versions(
        self,
        page_id: int,
        keep_versions: int = 50,
        keep_days: int = 365
    ) -> int:
        """
        Prune old versions to save storage space.

        Args:
            page_id: ID of the page
            keep_versions: Minimum number of versions to keep
            keep_days: Keep versions from last N days

        Returns:
            Number of versions pruned

        Example:
            >>> pruned = service.prune_old_versions(123, keep_versions=30)
        """
        try:
            from datetime import timedelta

            cutoff_date = datetime.utcnow() - timedelta(days=keep_days)

            # Get versions to prune (old versions beyond keep_versions threshold)
            versions_to_prune = self.db.query(WikiHistory).filter(
                WikiHistory.page_id == page_id,
                WikiHistory.changed_at < cutoff_date
            ).order_by(desc(WikiHistory.version)).offset(keep_versions).all()

            count = len(versions_to_prune)

            for version in versions_to_prune:
                self.db.delete(version)

            self.db.commit()

            logger.info(f"Pruned {count} old versions for page {page_id}")
            return count

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error pruning versions: {str(e)}")
            return 0

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _calculate_changes(
        self,
        old_lines: List[str],
        new_lines: List[str]
    ) -> Dict:
        """Calculate detailed change statistics between two versions."""
        diff = list(difflib.unified_diff(old_lines, new_lines, lineterm=''))

        added = 0
        removed = 0
        modified = 0

        for line in diff:
            if line.startswith('+') and not line.startswith('+++'):
                added += 1
            elif line.startswith('-') and not line.startswith('---'):
                removed += 1

        # Rough estimate of modified lines
        modified = min(added, removed)
        added = added - modified
        removed = removed - modified

        return {
            'lines_added': added,
            'lines_removed': removed,
            'lines_modified': modified,
            'total_changes': added + removed + modified,
        }
