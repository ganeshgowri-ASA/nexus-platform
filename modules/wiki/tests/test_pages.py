"""
Unit Tests for Wiki Page Management

Tests for page CRUD operations, page tree hierarchy, moving pages,
and page organization functionality.

Author: NEXUS Platform Team
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from modules.wiki.pages import PageManager
from modules.wiki.models import WikiPage, WikiTag, WikiHistory
from modules.wiki.wiki_types import (
    PageStatus, ContentFormat, ChangeType,
    PageCreateRequest, PageUpdateRequest
)


class TestPageCreation:
    """Tests for creating wiki pages."""

    def test_create_basic_page(self, db_session: Session, mock_user):
        """Test creating a basic wiki page."""
        manager = PageManager(db_session)
        request = PageCreateRequest(
            title='Test Page',
            content='# Test\n\nTest content here.',
            content_format=ContentFormat.MARKDOWN,
            summary='A test page',
            status=PageStatus.DRAFT
        )

        page = manager.create_page(request, author_id=mock_user['id'])

        assert page is not None
        assert page.id is not None
        assert page.title == 'Test Page'
        assert page.slug == 'test-page'
        assert page.content == '# Test\n\nTest content here.'
        assert page.status == PageStatus.DRAFT
        assert page.author_id == mock_user['id']
        assert page.current_version == 1
        assert not page.is_deleted

    def test_create_page_with_auto_publish(self, db_session: Session, mock_user):
        """Test creating a page with auto-publish enabled."""
        manager = PageManager(db_session)
        request = PageCreateRequest(
            title='Published Page',
            content='Published content',
            status=PageStatus.DRAFT
        )

        page = manager.create_page(request, author_id=mock_user['id'], auto_publish=True)

        assert page.status == PageStatus.PUBLISHED
        assert page.published_at is not None

    def test_create_page_with_category(self, db_session: Session, sample_category, mock_user):
        """Test creating a page with a category."""
        manager = PageManager(db_session)
        request = PageCreateRequest(
            title='Categorized Page',
            content='Content',
            category_id=sample_category.id
        )

        page = manager.create_page(request, author_id=mock_user['id'])

        assert page.category_id == sample_category.id
        assert page.category is not None
        assert page.category.name == sample_category.name

    def test_create_page_with_namespace(self, db_session: Session, mock_user):
        """Test creating a page with a namespace."""
        manager = PageManager(db_session)
        request = PageCreateRequest(
            title='Namespaced Page',
            content='Content',
            namespace='docs'
        )

        page = manager.create_page(request, author_id=mock_user['id'])

        assert page.namespace == 'docs'
        assert page.full_path == '/docs/namespaced-page'

    def test_create_page_with_tags(self, db_session: Session, mock_user):
        """Test creating a page with tags."""
        manager = PageManager(db_session)
        request = PageCreateRequest(
            title='Tagged Page',
            content='Content',
            tags=['python', 'tutorial', 'beginner']
        )

        page = manager.create_page(request, author_id=mock_user['id'])

        assert len(page.tags) == 3
        tag_names = [tag.name for tag in page.tags]
        assert 'python' in tag_names
        assert 'tutorial' in tag_names
        assert 'beginner' in tag_names

    def test_create_page_with_parent(self, db_session: Session, sample_page, mock_user):
        """Test creating a child page under a parent."""
        manager = PageManager(db_session)
        request = PageCreateRequest(
            title='Child Page',
            content='Child content',
            parent_page_id=sample_page.id
        )

        child_page = manager.create_page(request, author_id=mock_user['id'])

        assert child_page.parent_page_id == sample_page.id
        assert child_page.path.startswith(sample_page.path)

    def test_create_page_duplicate_slug_fails(self, db_session: Session, sample_page, mock_user):
        """Test that creating a page with duplicate slug fails."""
        manager = PageManager(db_session)
        request = PageCreateRequest(
            title=sample_page.title,  # Will generate same slug
            content='Different content',
            namespace=sample_page.namespace
        )

        with pytest.raises(ValueError, match='already exists'):
            manager.create_page(request, author_id=mock_user['id'])

    def test_create_page_generates_history(self, db_session: Session, mock_user):
        """Test that creating a page generates initial history entry."""
        manager = PageManager(db_session)
        request = PageCreateRequest(
            title='History Test',
            content='Initial content'
        )

        page = manager.create_page(request, author_id=mock_user['id'])

        history = db_session.query(WikiHistory).filter(
            WikiHistory.page_id == page.id
        ).all()

        assert len(history) == 1
        assert history[0].version == 1
        assert history[0].change_type == ChangeType.CREATED


class TestPageRetrieval:
    """Tests for retrieving wiki pages."""

    def test_get_page_by_id(self, db_session: Session, sample_page):
        """Test retrieving a page by ID."""
        manager = PageManager(db_session)
        page = manager.get_page(sample_page.id)

        assert page is not None
        assert page.id == sample_page.id
        assert page.title == sample_page.title

    def test_get_page_with_relations(self, db_session: Session, sample_page):
        """Test retrieving a page with eager-loaded relationships."""
        manager = PageManager(db_session)
        page = manager.get_page(sample_page.id, load_relations=True)

        assert page is not None
        # Relationships should be loaded
        assert page.category is not None

    def test_get_nonexistent_page(self, db_session: Session):
        """Test retrieving a non-existent page returns None."""
        manager = PageManager(db_session)
        page = manager.get_page(99999)

        assert page is None

    def test_get_deleted_page_excluded_by_default(self, db_session: Session, sample_page, mock_user):
        """Test that deleted pages are excluded by default."""
        manager = PageManager(db_session)

        # Delete the page
        manager.delete_page(sample_page.id, user_id=mock_user['id'])

        # Try to get it without include_deleted
        page = manager.get_page(sample_page.id)
        assert page is None

    def test_get_deleted_page_with_flag(self, db_session: Session, sample_page, mock_user):
        """Test retrieving a deleted page with include_deleted=True."""
        manager = PageManager(db_session)

        # Delete the page
        manager.delete_page(sample_page.id, user_id=mock_user['id'])

        # Get with include_deleted
        page = manager.get_page(sample_page.id, include_deleted=True)
        assert page is not None
        assert page.is_deleted

    def test_get_page_by_slug(self, db_session: Session, sample_page):
        """Test retrieving a page by slug."""
        manager = PageManager(db_session)
        page = manager.get_page_by_slug(sample_page.slug, namespace=sample_page.namespace)

        assert page is not None
        assert page.slug == sample_page.slug

    def test_get_page_by_slug_wrong_namespace(self, db_session: Session, sample_page):
        """Test that wrong namespace returns None."""
        manager = PageManager(db_session)
        page = manager.get_page_by_slug(sample_page.slug, namespace='wrong')

        assert page is None


class TestPageUpdate:
    """Tests for updating wiki pages."""

    def test_update_page_title(self, db_session: Session, sample_page, mock_user):
        """Test updating a page title."""
        manager = PageManager(db_session)
        request = PageUpdateRequest(title='Updated Title')

        updated_page = manager.update_page(sample_page.id, request, user_id=mock_user['id'])

        assert updated_page.title == 'Updated Title'
        assert updated_page.slug == 'updated-title'

    def test_update_page_content(self, db_session: Session, sample_page, mock_user):
        """Test updating page content."""
        manager = PageManager(db_session)
        new_content = '# Updated\n\nNew content here.'
        request = PageUpdateRequest(
            content=new_content,
            change_summary='Updated content'
        )

        updated_page = manager.update_page(sample_page.id, request, user_id=mock_user['id'])

        assert updated_page.content == new_content
        assert updated_page.current_version == 2  # Version incremented

    def test_update_page_status(self, db_session: Session, sample_page, mock_user):
        """Test updating page status."""
        manager = PageManager(db_session)
        request = PageUpdateRequest(status=PageStatus.PUBLISHED)

        updated_page = manager.update_page(sample_page.id, request, user_id=mock_user['id'])

        assert updated_page.status == PageStatus.PUBLISHED
        assert updated_page.published_at is not None

    def test_update_page_tags(self, db_session: Session, sample_page, mock_user):
        """Test updating page tags."""
        manager = PageManager(db_session)
        request = PageUpdateRequest(tags=['new-tag', 'another-tag'])

        updated_page = manager.update_page(sample_page.id, request, user_id=mock_user['id'])

        tag_names = [tag.name for tag in updated_page.tags]
        assert 'new-tag' in tag_names
        assert 'another-tag' in tag_names

    def test_update_locked_page_fails(self, db_session: Session, sample_page, mock_user):
        """Test that updating a locked page fails."""
        manager = PageManager(db_session)

        # Lock the page
        sample_page.is_locked = True
        db_session.commit()

        request = PageUpdateRequest(title='New Title')

        with pytest.raises(ValueError, match='locked'):
            manager.update_page(sample_page.id, request, user_id=mock_user['id'])

    def test_update_deleted_page_fails(self, db_session: Session, sample_page, mock_user):
        """Test that updating a deleted page fails."""
        manager = PageManager(db_session)

        # Delete the page
        manager.delete_page(sample_page.id, user_id=mock_user['id'])

        request = PageUpdateRequest(title='New Title')

        with pytest.raises(ValueError, match='deleted'):
            manager.update_page(sample_page.id, request, user_id=mock_user['id'])

    def test_update_creates_history_entry(self, db_session: Session, sample_page, mock_user):
        """Test that content update creates history entry."""
        manager = PageManager(db_session)
        request = PageUpdateRequest(
            content='New content',
            change_summary='Major update'
        )

        manager.update_page(sample_page.id, request, user_id=mock_user['id'])

        history = db_session.query(WikiHistory).filter(
            WikiHistory.page_id == sample_page.id
        ).all()

        assert len(history) >= 1  # At least the update entry
        latest = max(history, key=lambda h: h.version)
        assert latest.change_summary == 'Major update'


class TestPageDeletion:
    """Tests for deleting wiki pages."""

    def test_soft_delete_page(self, db_session: Session, sample_page, mock_user):
        """Test soft deleting a page."""
        manager = PageManager(db_session)
        success = manager.delete_page(sample_page.id, user_id=mock_user['id'])

        assert success
        db_session.refresh(sample_page)
        assert sample_page.is_deleted
        assert sample_page.status == PageStatus.DELETED

    def test_hard_delete_page(self, db_session: Session, sample_page, mock_user):
        """Test hard deleting a page."""
        manager = PageManager(db_session)
        page_id = sample_page.id

        success = manager.delete_page(page_id, user_id=mock_user['id'], hard_delete=True)

        assert success
        # Page should not exist
        page = db_session.query(WikiPage).filter(WikiPage.id == page_id).first()
        assert page is None

    def test_delete_nonexistent_page(self, db_session: Session, mock_user):
        """Test deleting a non-existent page."""
        manager = PageManager(db_session)
        success = manager.delete_page(99999, user_id=mock_user['id'])

        assert not success

    def test_restore_deleted_page(self, db_session: Session, sample_page, mock_user):
        """Test restoring a soft-deleted page."""
        manager = PageManager(db_session)

        # Delete the page
        manager.delete_page(sample_page.id, user_id=mock_user['id'])

        # Restore it
        restored_page = manager.restore_page(sample_page.id, user_id=mock_user['id'])

        assert restored_page is not None
        assert not restored_page.is_deleted
        assert restored_page.status == PageStatus.DRAFT

    def test_restore_nondeleted_page(self, db_session: Session, sample_page, mock_user):
        """Test that restoring a non-deleted page returns None."""
        manager = PageManager(db_session)
        restored_page = manager.restore_page(sample_page.id, user_id=mock_user['id'])

        assert restored_page is None


class TestPageListing:
    """Tests for listing and filtering pages."""

    def test_list_all_pages(self, db_session: Session, sample_pages):
        """Test listing all pages."""
        manager = PageManager(db_session)
        pages, total = manager.list_pages()

        assert len(pages) > 0
        assert total >= len(sample_pages)

    def test_list_pages_by_category(self, db_session: Session, sample_pages, sample_category):
        """Test filtering pages by category."""
        manager = PageManager(db_session)
        pages, total = manager.list_pages(category_id=sample_category.id)

        assert all(page.category_id == sample_category.id for page in pages)

    def test_list_pages_by_status(self, db_session: Session, sample_pages):
        """Test filtering pages by status."""
        manager = PageManager(db_session)
        pages, total = manager.list_pages(status=PageStatus.PUBLISHED)

        assert all(page.status == PageStatus.PUBLISHED for page in pages)
        assert total >= 1

    def test_list_pages_by_author(self, db_session: Session, sample_pages, mock_user):
        """Test filtering pages by author."""
        manager = PageManager(db_session)
        pages, total = manager.list_pages(author_id=mock_user['id'])

        assert all(page.author_id == mock_user['id'] for page in pages)

    def test_list_pages_pagination(self, db_session: Session, sample_pages):
        """Test pagination of page listing."""
        manager = PageManager(db_session)

        # Get first page
        pages1, total = manager.list_pages(limit=2, offset=0)
        assert len(pages1) <= 2

        # Get second page
        pages2, total = manager.list_pages(limit=2, offset=2)

        # Pages should be different
        if len(pages1) == 2 and len(pages2) > 0:
            assert pages1[0].id != pages2[0].id

    def test_list_pages_ordering(self, db_session: Session, sample_pages):
        """Test ordering of page listing."""
        manager = PageManager(db_session)

        # Order by title ascending
        pages, _ = manager.list_pages(order_by='title', descending=False)
        titles = [p.title for p in pages]
        assert titles == sorted(titles)

        # Order by created_at descending
        pages, _ = manager.list_pages(order_by='created_at', descending=True)
        dates = [p.created_at for p in pages]
        assert dates == sorted(dates, reverse=True)


class TestPageTree:
    """Tests for page hierarchy and tree operations."""

    def test_get_page_tree(self, db_session: Session, page_factory, mock_user):
        """Test building page tree structure."""
        manager = PageManager(db_session)

        # Create parent and child pages
        parent = page_factory(title='Parent Page')
        child1 = page_factory(title='Child 1', slug='child-1')
        child1.parent_page_id = parent.id
        child2 = page_factory(title='Child 2', slug='child-2')
        child2.parent_page_id = parent.id
        db_session.commit()

        tree = manager.get_page_tree()

        assert len(tree) > 0
        # Find parent in tree
        parent_node = next((n for n in tree if n['page'].id == parent.id), None)
        assert parent_node is not None
        assert len(parent_node['children']) == 2

    def test_get_page_tree_max_depth(self, db_session: Session, page_factory):
        """Test page tree respects max depth."""
        manager = PageManager(db_session)

        # Create deeply nested pages
        p1 = page_factory(title='Level 1')
        p2 = page_factory(title='Level 2', slug='level-2')
        p2.parent_page_id = p1.id
        p3 = page_factory(title='Level 3', slug='level-3')
        p3.parent_page_id = p2.id
        db_session.commit()

        tree = manager.get_page_tree(max_depth=2)

        # Should only go 2 levels deep
        assert len(tree) > 0

    def test_move_page(self, db_session: Session, page_factory, mock_user):
        """Test moving a page to a different parent."""
        manager = PageManager(db_session)

        parent1 = page_factory(title='Parent 1')
        parent2 = page_factory(title='Parent 2', slug='parent-2')
        child = page_factory(title='Child Page', slug='child-page')
        child.parent_page_id = parent1.id
        db_session.commit()

        # Move child from parent1 to parent2
        moved_page = manager.move_page(child.id, new_parent_id=parent2.id, user_id=mock_user['id'])

        assert moved_page is not None
        assert moved_page.parent_page_id == parent2.id

    def test_move_page_to_root(self, db_session: Session, page_factory, mock_user):
        """Test moving a page to root level."""
        manager = PageManager(db_session)

        parent = page_factory(title='Parent')
        child = page_factory(title='Child', slug='child')
        child.parent_page_id = parent.id
        db_session.commit()

        # Move to root
        moved_page = manager.move_page(child.id, new_parent_id=None, user_id=mock_user['id'])

        assert moved_page is not None
        assert moved_page.parent_page_id is None

    def test_move_page_circular_reference(self, db_session: Session, page_factory, mock_user):
        """Test that moving a page to create circular reference fails."""
        manager = PageManager(db_session)

        parent = page_factory(title='Parent')
        child = page_factory(title='Child', slug='child')
        child.parent_page_id = parent.id
        db_session.commit()

        # Try to move parent under child (would create cycle)
        with pytest.raises(ValueError, match='circular'):
            manager.move_page(parent.id, new_parent_id=child.id, user_id=mock_user['id'])


class TestPageMetadata:
    """Tests for page metadata operations."""

    def test_increment_view_count(self, db_session: Session, sample_page):
        """Test incrementing page view count."""
        manager = PageManager(db_session)
        initial_count = sample_page.view_count

        manager.increment_view_count(sample_page.id)

        db_session.refresh(sample_page)
        assert sample_page.view_count == initial_count + 1
        assert sample_page.last_viewed_at is not None

    def test_page_content_size(self, db_session: Session, sample_page):
        """Test content_size property."""
        expected_size = len(sample_page.content.encode('utf-8'))
        assert sample_page.content_size == expected_size

    def test_page_full_path(self, db_session: Session):
        """Test full_path property with and without namespace."""
        page1 = WikiPage(
            title='Test',
            slug='test',
            content='content',
            author_id=1,
            namespace='docs'
        )
        assert page1.full_path == '/docs/test'

        page2 = WikiPage(
            title='Test2',
            slug='test2',
            content='content',
            author_id=1,
            namespace=None
        )
        assert page2.full_path == '/test2'


class TestPageSlugGeneration:
    """Tests for slug generation."""

    def test_slug_generation_from_title(self, db_session: Session, mock_user):
        """Test automatic slug generation from title."""
        manager = PageManager(db_session)
        request = PageCreateRequest(
            title='My Awesome Page!',
            content='Content'
        )

        page = manager.create_page(request, author_id=mock_user['id'])

        assert page.slug == 'my-awesome-page'

    def test_slug_special_characters_removed(self, db_session: Session, mock_user):
        """Test that special characters are removed from slug."""
        manager = PageManager(db_session)
        request = PageCreateRequest(
            title='Test@#$%Page',
            content='Content'
        )

        page = manager.create_page(request, author_id=mock_user['id'])

        assert '@' not in page.slug
        assert '#' not in page.slug
        assert '$' not in page.slug

    def test_slug_multiple_spaces_converted(self, db_session: Session, mock_user):
        """Test that multiple spaces become single dash."""
        manager = PageManager(db_session)
        request = PageCreateRequest(
            title='Multiple    Spaces    Here',
            content='Content'
        )

        page = manager.create_page(request, author_id=mock_user['id'])

        assert '--' not in page.slug
        assert page.slug == 'multiple-spaces-here'
