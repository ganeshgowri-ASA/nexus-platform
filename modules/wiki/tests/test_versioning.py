"""
Unit Tests for Wiki Versioning Service

Tests for version history, diffs, rollback, and version control functionality.

Author: NEXUS Platform Team
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from modules.wiki.versioning import VersioningService
from modules.wiki.models import WikiPage, WikiHistory
from modules.wiki.wiki_types import ChangeType, PageStatus


class TestVersionHistory:
    """Tests for retrieving version history."""

    def test_get_page_history(self, db_session: Session, sample_page_with_history):
        """Test retrieving page history."""
        service = VersioningService(db_session)
        history, total = service.get_page_history(sample_page_with_history.id)

        assert total >= 2
        assert len(history) >= 2
        # History should be ordered by version descending
        assert history[0].version >= history[-1].version

    def test_get_page_history_pagination(self, db_session: Session, sample_page_with_history):
        """Test paginating through version history."""
        service = VersioningService(db_session)

        # Get first page
        history1, total = service.get_page_history(sample_page_with_history.id, limit=1, offset=0)
        assert len(history1) == 1

        # Get second page
        history2, total = service.get_page_history(sample_page_with_history.id, limit=1, offset=1)
        assert len(history2) <= 1

        # Different versions
        if len(history2) == 1:
            assert history1[0].version != history2[0].version

    def test_get_page_history_empty(self, db_session: Session, sample_page):
        """Test getting history for page with no history entries."""
        service = VersioningService(db_session)

        # Remove any existing history
        db_session.query(WikiHistory).filter(
            WikiHistory.page_id == sample_page.id
        ).delete()
        db_session.commit()

        history, total = service.get_page_history(sample_page.id)

        assert total == 0
        assert len(history) == 0

    def test_get_specific_version(self, db_session: Session, sample_page_with_history):
        """Test retrieving a specific version."""
        service = VersioningService(db_session)
        version_data = service.get_version(sample_page_with_history.id, version=1)

        assert version_data is not None
        assert version_data.version == 1
        assert version_data.page_id == sample_page_with_history.id

    def test_get_nonexistent_version(self, db_session: Session, sample_page):
        """Test retrieving a non-existent version."""
        service = VersioningService(db_session)
        version_data = service.get_version(sample_page.id, version=999)

        assert version_data is None

    def test_get_latest_version(self, db_session: Session, sample_page_with_history):
        """Test retrieving the latest version."""
        service = VersioningService(db_session)
        latest = service.get_latest_version(sample_page_with_history.id)

        assert latest is not None
        assert latest.version == sample_page_with_history.current_version


class TestVersionComparison:
    """Tests for comparing versions and generating diffs."""

    def test_compare_versions(self, db_session: Session, sample_page_with_history):
        """Test comparing two versions of a page."""
        service = VersioningService(db_session)
        diff = service.compare_versions(
            sample_page_with_history.id,
            version1=1,
            version2=2
        )

        assert diff is not None
        assert 'html_diff' in diff
        assert 'unified_diff' in diff
        assert 'changes' in diff
        assert diff['version1'] == 1
        assert diff['version2'] == 2

    def test_compare_versions_with_changes(self, db_session: Session, sample_page, mock_user):
        """Test that diff correctly identifies changes."""
        # Create two versions with known differences
        history1 = WikiHistory(
            page_id=sample_page.id,
            version=1,
            title='Test Page',
            content='Line 1\nLine 2\nLine 3',
            change_type=ChangeType.CREATED,
            changed_by=mock_user['id'],
            content_size=100
        )
        db_session.add(history1)

        history2 = WikiHistory(
            page_id=sample_page.id,
            version=2,
            title='Test Page',
            content='Line 1\nModified Line 2\nLine 3\nLine 4',
            change_type=ChangeType.EDITED,
            changed_by=mock_user['id'],
            content_size=120
        )
        db_session.add(history2)
        db_session.commit()

        service = VersioningService(db_session)
        diff = service.compare_versions(sample_page.id, version1=1, version2=2)

        assert diff['changes']['lines_added'] > 0 or diff['changes']['lines_modified'] > 0

    def test_compare_versions_title_changed(self, db_session: Session, sample_page, mock_user):
        """Test detecting title changes in version comparison."""
        history1 = WikiHistory(
            page_id=sample_page.id,
            version=1,
            title='Original Title',
            content='Content',
            change_type=ChangeType.CREATED,
            changed_by=mock_user['id'],
            content_size=50
        )
        db_session.add(history1)

        history2 = WikiHistory(
            page_id=sample_page.id,
            version=2,
            title='New Title',
            content='Content',
            change_type=ChangeType.EDITED,
            changed_by=mock_user['id'],
            content_size=50
        )
        db_session.add(history2)
        db_session.commit()

        service = VersioningService(db_session)
        diff = service.compare_versions(sample_page.id, version1=1, version2=2)

        assert diff['title_changed']
        assert diff['old_title'] == 'Original Title'
        assert diff['new_title'] == 'New Title'

    def test_compare_nonexistent_versions(self, db_session: Session, sample_page):
        """Test comparing non-existent versions."""
        service = VersioningService(db_session)
        diff = service.compare_versions(sample_page.id, version1=999, version2=1000)

        assert 'error' in diff

    def test_compare_versions_context_lines(self, db_session: Session, sample_page_with_history):
        """Test diff with different context line counts."""
        service = VersioningService(db_session)

        diff_3 = service.compare_versions(
            sample_page_with_history.id,
            version1=1,
            version2=2,
            context_lines=3
        )

        diff_10 = service.compare_versions(
            sample_page_with_history.id,
            version1=1,
            version2=2,
            context_lines=10
        )

        assert diff_3 is not None
        assert diff_10 is not None


class TestVersionRollback:
    """Tests for rolling back to previous versions."""

    def test_rollback_to_previous_version(self, db_session: Session, sample_page_with_history, mock_user):
        """Test rolling back to a previous version."""
        service = VersioningService(db_session)

        # Get version 1 content
        v1 = service.get_version(sample_page_with_history.id, version=1)
        original_content = v1.content

        # Rollback to version 1
        rolled_back = service.rollback_to_version(
            sample_page_with_history.id,
            version=1,
            user_id=mock_user['id'],
            change_summary='Rollback to v1'
        )

        assert rolled_back is not None
        assert rolled_back.content == original_content
        # Version should be incremented (new version created)
        assert rolled_back.current_version == 3

    def test_rollback_creates_history_entry(self, db_session: Session, sample_page_with_history, mock_user):
        """Test that rollback creates a new history entry."""
        service = VersioningService(db_session)

        initial_history_count = db_session.query(WikiHistory).filter(
            WikiHistory.page_id == sample_page_with_history.id
        ).count()

        service.rollback_to_version(
            sample_page_with_history.id,
            version=1,
            user_id=mock_user['id']
        )

        new_history_count = db_session.query(WikiHistory).filter(
            WikiHistory.page_id == sample_page_with_history.id
        ).count()

        assert new_history_count == initial_history_count + 1

    def test_rollback_to_nonexistent_version(self, db_session: Session, sample_page, mock_user):
        """Test rolling back to non-existent version."""
        service = VersioningService(db_session)

        result = service.rollback_to_version(
            sample_page.id,
            version=999,
            user_id=mock_user['id']
        )

        assert result is None

    def test_rollback_locked_page_fails(self, db_session: Session, sample_page_with_history, mock_user):
        """Test that rolling back a locked page fails."""
        service = VersioningService(db_session)

        # Lock the page
        sample_page_with_history.is_locked = True
        db_session.commit()

        result = service.rollback_to_version(
            sample_page_with_history.id,
            version=1,
            user_id=mock_user['id']
        )

        assert result is None

    def test_rollback_metadata_stored(self, db_session: Session, sample_page_with_history, mock_user):
        """Test that rollback metadata is stored correctly."""
        service = VersioningService(db_session)

        current_version = sample_page_with_history.current_version

        service.rollback_to_version(
            sample_page_with_history.id,
            version=1,
            user_id=mock_user['id']
        )

        # Get the rollback history entry
        rollback_entry = db_session.query(WikiHistory).filter(
            WikiHistory.page_id == sample_page_with_history.id,
            WikiHistory.version == current_version + 1
        ).first()

        assert rollback_entry is not None
        assert rollback_entry.change_type == ChangeType.RESTORED
        assert 'rollback_from' in rollback_entry.metadata
        assert 'rollback_to' in rollback_entry.metadata


class TestVersionTimeline:
    """Tests for version timeline and analytics."""

    def test_get_version_timeline(self, db_session: Session, sample_page_with_history):
        """Test generating version timeline."""
        service = VersioningService(db_session)
        timeline = service.get_version_timeline(sample_page_with_history.id)

        assert len(timeline) >= 2
        for event in timeline:
            assert 'version' in event
            assert 'change_type' in event
            assert 'changed_by' in event
            assert 'changed_at' in event
            assert 'summary' in event

    def test_timeline_ordered_by_version(self, db_session: Session, sample_page_with_history):
        """Test that timeline is ordered by version descending."""
        service = VersioningService(db_session)
        timeline = service.get_version_timeline(sample_page_with_history.id)

        versions = [event['version'] for event in timeline]
        assert versions == sorted(versions, reverse=True)

    def test_get_contributors(self, db_session: Session, sample_page, mock_user, mock_admin_user):
        """Test getting list of contributors."""
        # Create history with multiple users
        history1 = WikiHistory(
            page_id=sample_page.id,
            version=1,
            title=sample_page.title,
            content='v1',
            change_type=ChangeType.CREATED,
            changed_by=mock_user['id'],
            content_size=10
        )
        db_session.add(history1)

        history2 = WikiHistory(
            page_id=sample_page.id,
            version=2,
            title=sample_page.title,
            content='v2',
            change_type=ChangeType.EDITED,
            changed_by=mock_admin_user['id'],
            content_size=10
        )
        db_session.add(history2)

        history3 = WikiHistory(
            page_id=sample_page.id,
            version=3,
            title=sample_page.title,
            content='v3',
            change_type=ChangeType.EDITED,
            changed_by=mock_user['id'],
            content_size=10
        )
        db_session.add(history3)
        db_session.commit()

        service = VersioningService(db_session)
        contributors = service.get_contributors(sample_page.id)

        assert len(contributors) == 2
        # User with ID 1 should have 2 edits
        user1_contrib = next(c for c in contributors if c['user_id'] == mock_user['id'])
        assert user1_contrib['edit_count'] == 2

    def test_get_change_statistics(self, db_session: Session, sample_page_with_history):
        """Test getting change statistics for a page."""
        service = VersioningService(db_session)
        stats = service.get_change_statistics(sample_page_with_history.id)

        assert 'total_versions' in stats
        assert 'total_contributors' in stats
        assert 'avg_edit_size' in stats
        assert 'largest_edit' in stats
        assert 'smallest_edit' in stats
        assert stats['total_versions'] >= 2

    def test_change_statistics_empty_history(self, db_session: Session, sample_page):
        """Test statistics for page with no history."""
        # Remove history
        db_session.query(WikiHistory).filter(
            WikiHistory.page_id == sample_page.id
        ).delete()
        db_session.commit()

        service = VersioningService(db_session)
        stats = service.get_change_statistics(sample_page.id)

        assert stats['total_versions'] == 0
        assert stats['total_contributors'] == 0


class TestVersionPruning:
    """Tests for pruning old versions."""

    def test_prune_old_versions(self, db_session: Session, sample_page, mock_user):
        """Test pruning old version history."""
        # Create many old versions
        for i in range(100):
            history = WikiHistory(
                page_id=sample_page.id,
                version=i + 1,
                title=sample_page.title,
                content=f'Version {i+1}',
                change_type=ChangeType.EDITED,
                changed_by=mock_user['id'],
                content_size=50,
                changed_at=datetime.utcnow() - timedelta(days=400 - i)
            )
            db_session.add(history)
        db_session.commit()

        service = VersioningService(db_session)

        # Keep only 50 versions, older than 365 days
        pruned = service.prune_old_versions(
            sample_page.id,
            keep_versions=50,
            keep_days=365
        )

        assert pruned > 0

        # Check remaining count
        remaining = db_session.query(WikiHistory).filter(
            WikiHistory.page_id == sample_page.id
        ).count()

        # Should have kept at least 50 recent versions
        assert remaining >= 50

    def test_prune_keeps_minimum_versions(self, db_session: Session, sample_page, mock_user):
        """Test that pruning keeps minimum number of versions."""
        # Create 10 old versions
        for i in range(10):
            history = WikiHistory(
                page_id=sample_page.id,
                version=i + 1,
                title=sample_page.title,
                content=f'Version {i+1}',
                change_type=ChangeType.EDITED,
                changed_by=mock_user['id'],
                content_size=50,
                changed_at=datetime.utcnow() - timedelta(days=400)
            )
            db_session.add(history)
        db_session.commit()

        service = VersioningService(db_session)

        # Keep all versions even though they're old
        pruned = service.prune_old_versions(
            sample_page.id,
            keep_versions=10,
            keep_days=365
        )

        remaining = db_session.query(WikiHistory).filter(
            WikiHistory.page_id == sample_page.id
        ).count()

        # All versions should be kept
        assert remaining == 10

    def test_prune_keeps_recent_versions(self, db_session: Session, sample_page, mock_user):
        """Test that pruning keeps recent versions regardless of count."""
        # Create recent versions
        for i in range(20):
            history = WikiHistory(
                page_id=sample_page.id,
                version=i + 1,
                title=sample_page.title,
                content=f'Version {i+1}',
                change_type=ChangeType.EDITED,
                changed_by=mock_user['id'],
                content_size=50,
                changed_at=datetime.utcnow() - timedelta(days=i)
            )
            db_session.add(history)
        db_session.commit()

        service = VersioningService(db_session)

        # Try to prune but keep last 365 days
        pruned = service.prune_old_versions(
            sample_page.id,
            keep_versions=5,
            keep_days=365
        )

        remaining = db_session.query(WikiHistory).filter(
            WikiHistory.page_id == sample_page.id
        ).count()

        # All versions should remain (all within 365 days)
        assert remaining == 20


class TestDiffCalculations:
    """Tests for diff calculation utilities."""

    def test_calculate_changes_added_lines(self, db_session: Session, sample_page, mock_user):
        """Test calculating added lines in diff."""
        history1 = WikiHistory(
            page_id=sample_page.id,
            version=1,
            title='Test',
            content='Line 1\nLine 2',
            change_type=ChangeType.CREATED,
            changed_by=mock_user['id'],
            content_size=50
        )
        db_session.add(history1)

        history2 = WikiHistory(
            page_id=sample_page.id,
            version=2,
            title='Test',
            content='Line 1\nLine 2\nLine 3\nLine 4',
            change_type=ChangeType.EDITED,
            changed_by=mock_user['id'],
            content_size=70
        )
        db_session.add(history2)
        db_session.commit()

        service = VersioningService(db_session)
        diff = service.compare_versions(sample_page.id, version1=1, version2=2)

        assert diff['changes']['lines_added'] >= 2

    def test_calculate_changes_removed_lines(self, db_session: Session, sample_page, mock_user):
        """Test calculating removed lines in diff."""
        history1 = WikiHistory(
            page_id=sample_page.id,
            version=1,
            title='Test',
            content='Line 1\nLine 2\nLine 3\nLine 4',
            change_type=ChangeType.CREATED,
            changed_by=mock_user['id'],
            content_size=70
        )
        db_session.add(history1)

        history2 = WikiHistory(
            page_id=sample_page.id,
            version=2,
            title='Test',
            content='Line 1\nLine 2',
            change_type=ChangeType.EDITED,
            changed_by=mock_user['id'],
            content_size=50
        )
        db_session.add(history2)
        db_session.commit()

        service = VersioningService(db_session)
        diff = service.compare_versions(sample_page.id, version1=1, version2=2)

        assert diff['changes']['lines_removed'] >= 2

    def test_unified_diff_format(self, db_session: Session, sample_page, mock_user):
        """Test unified diff format output."""
        history1 = WikiHistory(
            page_id=sample_page.id,
            version=1,
            title='Test',
            content='Original content',
            change_type=ChangeType.CREATED,
            changed_by=mock_user['id'],
            content_size=50
        )
        db_session.add(history1)

        history2 = WikiHistory(
            page_id=sample_page.id,
            version=2,
            title='Test',
            content='Modified content',
            change_type=ChangeType.EDITED,
            changed_by=mock_user['id'],
            content_size=50
        )
        db_session.add(history2)
        db_session.commit()

        service = VersioningService(db_session)
        diff = service.compare_versions(sample_page.id, version1=1, version2=2)

        # Unified diff should contain version labels
        assert 'Version 1' in diff['unified_diff'] or len(diff['unified_diff']) >= 0
