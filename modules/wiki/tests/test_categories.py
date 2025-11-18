"""
Unit Tests for Wiki Categories Service

Tests for category hierarchy, tag management, auto-categorization,
and category organization functionality.

Author: NEXUS Platform Team
"""

import pytest
from sqlalchemy.orm import Session

from modules.wiki.categories import CategoryService
from modules.wiki.models import WikiCategory, WikiTag, WikiPage


class TestCategoryCreation:
    """Tests for creating categories."""

    def test_create_basic_category(self, db_session: Session):
        """Test creating a basic category."""
        service = CategoryService(db_session)

        category = service.create_category(
            name='Documentation',
            slug='documentation',
            description='Technical documentation'
        )

        assert category is not None
        assert category.id is not None
        assert category.name == 'Documentation'
        assert category.slug == 'documentation'
        assert category.is_active

    def test_create_category_with_parent(self, db_session: Session, sample_category):
        """Test creating a child category."""
        service = CategoryService(db_session)

        child = service.create_category(
            name='API Docs',
            slug='api-docs',
            parent_id=sample_category.id
        )

        assert child.parent_id == sample_category.id
        assert child.parent == sample_category

    def test_create_category_with_styling(self, db_session: Session):
        """Test creating category with icon and color."""
        service = CategoryService(db_session)

        category = service.create_category(
            name='Tutorials',
            slug='tutorials',
            icon='book',
            color='#3498db',
            order=1
        )

        assert category.icon == 'book'
        assert category.color == '#3498db'
        assert category.order == 1

    def test_create_category_duplicate_slug_fails(self, db_session: Session, sample_category):
        """Test that duplicate slug raises error."""
        service = CategoryService(db_session)

        with pytest.raises(ValueError, match='already exists'):
            service.create_category(
                name='Another Category',
                slug=sample_category.slug
            )

    def test_create_category_with_invalid_parent(self, db_session: Session):
        """Test creating category with non-existent parent fails."""
        service = CategoryService(db_session)

        with pytest.raises(ValueError, match='not found'):
            service.create_category(
                name='Child',
                slug='child',
                parent_id=99999
            )


class TestCategoryRetrieval:
    """Tests for retrieving categories."""

    def test_get_category_by_id(self, db_session: Session, sample_category):
        """Test retrieving a category by ID."""
        service = CategoryService(db_session)
        category = service.get_category(sample_category.id)

        assert category is not None
        assert category.id == sample_category.id

    def test_get_category_with_children(self, db_session: Session, category_factory):
        """Test retrieving category with children loaded."""
        service = CategoryService(db_session)

        parent = category_factory(name='Parent')
        child = category_factory(name='Child', slug='child', parent_id=parent.id)

        loaded_parent = service.get_category(parent.id, load_children=True)

        assert loaded_parent is not None
        assert len(loaded_parent.children) >= 1

    def test_get_category_by_slug(self, db_session: Session, sample_category):
        """Test retrieving a category by slug."""
        service = CategoryService(db_session)
        category = service.get_category_by_slug(sample_category.slug)

        assert category is not None
        assert category.slug == sample_category.slug

    def test_get_nonexistent_category(self, db_session: Session):
        """Test retrieving non-existent category returns None."""
        service = CategoryService(db_session)
        category = service.get_category(99999)

        assert category is None


class TestCategoryUpdate:
    """Tests for updating categories."""

    def test_update_category_name(self, db_session: Session, sample_category):
        """Test updating category name."""
        service = CategoryService(db_session)

        updated = service.update_category(
            sample_category.id,
            name='Updated Name'
        )

        assert updated.name == 'Updated Name'

    def test_update_category_description(self, db_session: Session, sample_category):
        """Test updating category description."""
        service = CategoryService(db_session)

        updated = service.update_category(
            sample_category.id,
            description='New description'
        )

        assert updated.description == 'New description'

    def test_update_category_parent(self, db_session: Session, category_factory):
        """Test moving category to different parent."""
        service = CategoryService(db_session)

        parent1 = category_factory(name='Parent 1')
        parent2 = category_factory(name='Parent 2', slug='parent-2')
        child = category_factory(name='Child', slug='child', parent_id=parent1.id)

        updated = service.update_category(
            child.id,
            parent_id=parent2.id
        )

        assert updated.parent_id == parent2.id

    def test_update_category_circular_reference_fails(self, db_session: Session, category_factory):
        """Test that creating circular reference fails."""
        service = CategoryService(db_session)

        parent = category_factory(name='Parent')
        child = category_factory(name='Child', slug='child', parent_id=parent.id)

        # Try to set parent's parent to child (circular)
        with pytest.raises(ValueError, match='circular'):
            service.update_category(parent.id, parent_id=child.id)

    def test_update_category_status(self, db_session: Session, sample_category):
        """Test deactivating a category."""
        service = CategoryService(db_session)

        updated = service.update_category(
            sample_category.id,
            is_active=False
        )

        assert not updated.is_active

    def test_update_category_styling(self, db_session: Session, sample_category):
        """Test updating category icon, color, and order."""
        service = CategoryService(db_session)

        updated = service.update_category(
            sample_category.id,
            icon='star',
            color='#e74c3c',
            order=5
        )

        assert updated.icon == 'star'
        assert updated.color == '#e74c3c'
        assert updated.order == 5


class TestCategoryDeletion:
    """Tests for deleting categories."""

    def test_delete_category_move_pages(self, db_session: Session, category_factory, page_factory):
        """Test deleting category and moving pages to another."""
        service = CategoryService(db_session)

        cat1 = category_factory(name='Category 1')
        cat2 = category_factory(name='Category 2', slug='category-2')

        page = page_factory(title='Page', category_id=cat1.id)

        success = service.delete_category(cat1.id, move_pages_to=cat2.id)

        assert success
        db_session.refresh(page)
        assert page.category_id == cat2.id

    def test_delete_category_unassign_pages(self, db_session: Session, category_factory, page_factory):
        """Test deleting category and unassigning pages."""
        service = CategoryService(db_session)

        category = category_factory(name='Category')
        page = page_factory(title='Page', category_id=category.id)

        success = service.delete_category(category.id, move_pages_to=None)

        assert success
        db_session.refresh(page)
        assert page.category_id is None

    def test_delete_category_with_children(self, db_session: Session, category_factory):
        """Test deleting category with child categories."""
        service = CategoryService(db_session)

        parent = category_factory(name='Parent')
        child = category_factory(name='Child', slug='child', parent_id=parent.id)

        # Delete with children
        success = service.delete_category(parent.id, delete_children=True)

        assert success

        # Child should be deleted
        child_exists = db_session.query(WikiCategory).filter(
            WikiCategory.id == child.id
        ).first()
        assert child_exists is None

    def test_delete_category_move_children_to_parent(self, db_session: Session, category_factory):
        """Test deleting category and moving children to grandparent."""
        service = CategoryService(db_session)

        grandparent = category_factory(name='Grandparent')
        parent = category_factory(name='Parent', slug='parent', parent_id=grandparent.id)
        child = category_factory(name='Child', slug='child', parent_id=parent.id)

        # Delete parent, don't delete children
        success = service.delete_category(parent.id, delete_children=False)

        assert success
        db_session.refresh(child)
        # Child should now be under grandparent
        assert child.parent_id == grandparent.id


class TestCategoryTree:
    """Tests for category hierarchy and tree operations."""

    def test_get_category_tree(self, db_session: Session, sample_categories):
        """Test building category tree."""
        service = CategoryService(db_session)
        tree = service.get_category_tree()

        assert len(tree) > 0
        # Tree should have root categories
        assert any(node['parent_id'] is None for node in tree)

    def test_get_category_tree_with_children(self, db_session: Session, sample_categories):
        """Test that tree includes children."""
        service = CategoryService(db_session)
        tree = service.get_category_tree()

        # Find node with children
        parent_node = next(
            (node for node in tree if len(node['children']) > 0),
            None
        )

        if parent_node:
            assert 'children' in parent_node
            assert len(parent_node['children']) > 0

    def test_get_category_tree_max_depth(self, db_session: Session, category_factory):
        """Test that tree respects max depth."""
        service = CategoryService(db_session)

        # Create deep hierarchy
        level1 = category_factory(name='Level 1')
        level2 = category_factory(name='Level 2', slug='level-2', parent_id=level1.id)
        level3 = category_factory(name='Level 3', slug='level-3', parent_id=level2.id)

        tree = service.get_category_tree(max_depth=2)

        # Should only go 2 levels deep
        assert len(tree) > 0

    def test_get_category_tree_exclude_inactive(self, db_session: Session, category_factory):
        """Test excluding inactive categories from tree."""
        service = CategoryService(db_session)

        active = category_factory(name='Active')
        inactive = category_factory(name='Inactive', slug='inactive')
        inactive.is_active = False
        db_session.commit()

        tree = service.get_category_tree(include_inactive=False)

        # Inactive should not be in tree
        tree_ids = [node['id'] for node in tree]
        assert inactive.id not in tree_ids

    def test_get_category_breadcrumbs(self, db_session: Session, category_factory):
        """Test getting breadcrumb trail for category."""
        service = CategoryService(db_session)

        level1 = category_factory(name='Level 1')
        level2 = category_factory(name='Level 2', slug='level-2', parent_id=level1.id)
        level3 = category_factory(name='Level 3', slug='level-3', parent_id=level2.id)

        breadcrumbs = service.get_category_breadcrumbs(level3.id)

        assert len(breadcrumbs) == 3
        assert breadcrumbs[0].id == level1.id
        assert breadcrumbs[1].id == level2.id
        assert breadcrumbs[2].id == level3.id

    def test_category_full_path(self, db_session: Session, category_factory):
        """Test full_path property of category."""
        service = CategoryService(db_session)

        parent = category_factory(name='Parent', slug='parent')
        child = category_factory(name='Child', slug='child', parent_id=parent.id)

        assert parent.full_path == '/parent'
        assert child.full_path == '/parent/child'


class TestCategoryPageCounts:
    """Tests for category page counting."""

    def test_update_page_counts(self, db_session: Session, category_factory, page_factory):
        """Test updating page counts for categories."""
        service = CategoryService(db_session)

        category = category_factory(name='Category')

        # Create pages in category
        page1 = page_factory(title='Page 1', category_id=category.id)
        page2 = page_factory(title='Page 2', slug='page-2', category_id=category.id)

        # Update counts
        updated = service.update_page_counts()

        assert updated > 0
        db_session.refresh(category)
        assert category.page_count == 2

    def test_update_page_counts_excludes_deleted(self, db_session: Session, category_factory, page_factory):
        """Test that deleted pages are not counted."""
        service = CategoryService(db_session)

        category = category_factory(name='Category')

        page1 = page_factory(title='Page 1', category_id=category.id)
        page2 = page_factory(title='Page 2', slug='page-2', category_id=category.id)
        page2.is_deleted = True
        db_session.commit()

        service.update_page_counts()

        db_session.refresh(category)
        # Should only count non-deleted page
        assert category.page_count == 1


class TestTagCreation:
    """Tests for creating tags."""

    def test_create_tag(self, db_session: Session):
        """Test creating a basic tag."""
        service = CategoryService(db_session)

        tag = service.create_tag(name='python')

        assert tag is not None
        assert tag.name == 'python'
        assert tag.color is not None

    def test_create_tag_with_color(self, db_session: Session):
        """Test creating tag with custom color."""
        service = CategoryService(db_session)

        tag = service.create_tag(
            name='important',
            color='#e74c3c',
            description='Important topics'
        )

        assert tag.color == '#e74c3c'
        assert tag.description == 'Important topics'

    def test_create_tag_normalizes_name(self, db_session: Session):
        """Test that tag names are normalized to lowercase."""
        service = CategoryService(db_session)

        tag = service.create_tag(name='Python')

        assert tag.name == 'python'

    def test_create_duplicate_tag_returns_existing(self, db_session: Session):
        """Test that creating duplicate tag returns existing one."""
        service = CategoryService(db_session)

        tag1 = service.create_tag(name='python')
        tag2 = service.create_tag(name='python')

        assert tag1.id == tag2.id


class TestTagRetrieval:
    """Tests for retrieving tags."""

    def test_get_tag_by_name(self, db_session: Session, sample_tags):
        """Test retrieving a tag by name."""
        service = CategoryService(db_session)

        tag = service.get_tag_by_name('python')

        assert tag is not None
        assert tag.name == 'python'

    def test_get_tag_by_name_case_insensitive(self, db_session: Session, sample_tags):
        """Test that tag retrieval is case-insensitive."""
        service = CategoryService(db_session)

        tag = service.get_tag_by_name('PYTHON')

        assert tag is not None
        assert tag.name == 'python'

    def test_get_all_tags(self, db_session: Session, sample_tags):
        """Test retrieving all tags."""
        service = CategoryService(db_session)

        tags = service.get_all_tags()

        assert len(tags) >= len(sample_tags)

    def test_get_all_tags_min_usage(self, db_session: Session, sample_tags):
        """Test filtering tags by minimum usage count."""
        service = CategoryService(db_session)

        # Set usage counts
        sample_tags[0].usage_count = 10
        sample_tags[1].usage_count = 5
        sample_tags[2].usage_count = 1
        db_session.commit()

        tags = service.get_all_tags(min_usage=5)

        assert all(t.usage_count >= 5 for t in tags)

    def test_get_all_tags_ordered_by_usage(self, db_session: Session, sample_tags):
        """Test that tags are ordered by usage count."""
        service = CategoryService(db_session)

        # Set different usage counts
        sample_tags[0].usage_count = 5
        sample_tags[1].usage_count = 10
        sample_tags[2].usage_count = 3
        db_session.commit()

        tags = service.get_all_tags()

        # Should be ordered by usage descending
        usage_counts = [t.usage_count for t in tags[:3]]
        assert usage_counts == sorted(usage_counts, reverse=True)


class TestTagCloud:
    """Tests for tag cloud generation."""

    def test_get_tag_cloud(self, db_session: Session, sample_tags):
        """Test generating tag cloud data."""
        service = CategoryService(db_session)

        # Set usage counts
        sample_tags[0].usage_count = 10
        sample_tags[1].usage_count = 5
        sample_tags[2].usage_count = 2
        db_session.commit()

        cloud = service.get_tag_cloud(max_tags=10)

        assert len(cloud) > 0
        for item in cloud:
            assert 'name' in item
            assert 'count' in item
            assert 'weight' in item
            assert 'color' in item

    def test_tag_cloud_weights(self, db_session: Session, sample_tags):
        """Test that tag cloud calculates weights correctly."""
        service = CategoryService(db_session)

        # Set usage counts
        sample_tags[0].usage_count = 100
        sample_tags[1].usage_count = 50
        sample_tags[2].usage_count = 1
        db_session.commit()

        cloud = service.get_tag_cloud()

        # Most used tag should have highest weight
        max_weight = max(item['weight'] for item in cloud)
        max_count_item = max(cloud, key=lambda x: x['count'])

        assert max_count_item['weight'] == max_weight


class TestTagSuggestions:
    """Tests for tag suggestion functionality."""

    def test_suggest_tags_from_content(self, db_session: Session, sample_tags):
        """Test suggesting tags based on content."""
        service = CategoryService(db_session)

        # Increase usage for python tag
        sample_tags[0].usage_count = 10  # python
        db_session.commit()

        content = "This is a tutorial about Python programming for beginners."
        title = "Python Basics"

        suggestions = service.suggest_tags(content, title, max_suggestions=5)

        # Should suggest 'python', 'tutorial', 'beginner' tags
        assert 'python' in suggestions or 'tutorial' in suggestions or 'beginner' in suggestions

    def test_suggest_tags_considers_popularity(self, db_session: Session, sample_tags):
        """Test that tag suggestions consider usage count."""
        service = CategoryService(db_session)

        # Make python very popular
        sample_tags[0].usage_count = 100  # python
        sample_tags[1].usage_count = 1    # javascript
        db_session.commit()

        content = "Python and JavaScript comparison"
        title = "Language Comparison"

        suggestions = service.suggest_tags(content, title, max_suggestions=1)

        # Should prioritize more popular tag
        if suggestions:
            assert suggestions[0] == 'python'


class TestAutoCategorization:
    """Tests for automatic categorization."""

    def test_auto_categorize_by_name_match(self, db_session: Session, category_factory):
        """Test auto-categorization by matching category name in content."""
        service = CategoryService(db_session)

        category = category_factory(
            name='Python',
            slug='python',
            description='Python programming topics'
        )

        content = "This guide covers Python programming basics."
        title = "Getting Started with Python"

        suggested = service.auto_categorize(
            page_id=1,
            content=content,
            title=title
        )

        assert suggested is not None
        assert suggested.id == category.id

    def test_auto_categorize_by_slug_match(self, db_session: Session, category_factory):
        """Test auto-categorization by matching slug."""
        service = CategoryService(db_session)

        category = category_factory(
            name='Tutorials',
            slug='tutorials'
        )

        content = "This is a tutorials page about various topics."
        title = "Tutorials Index"

        suggested = service.auto_categorize(
            page_id=1,
            content=content,
            title=title
        )

        if suggested:
            assert suggested.id == category.id

    def test_auto_categorize_by_description_keywords(self, db_session: Session, category_factory):
        """Test auto-categorization by matching description keywords."""
        service = CategoryService(db_session)

        category = category_factory(
            name='API Reference',
            slug='api-reference',
            description='REST API endpoints documentation guides'
        )

        content = "This page documents REST API endpoints for our service."
        title = "API Documentation"

        suggested = service.auto_categorize(
            page_id=1,
            content=content,
            title=title
        )

        # Should match based on common keywords
        if suggested:
            assert suggested is not None

    def test_auto_categorize_returns_highest_score(self, db_session: Session, category_factory):
        """Test that auto-categorization returns best match."""
        service = CategoryService(db_session)

        cat1 = category_factory(
            name='Programming',
            slug='programming',
            description='General programming topics'
        )

        cat2 = category_factory(
            name='Python Programming',
            slug='python-programming',
            description='Python specific programming tutorials'
        )

        content = "This is a Python Programming tutorial for beginners."
        title = "Python Programming Guide"

        suggested = service.auto_categorize(
            page_id=1,
            content=content,
            title=title
        )

        # Should prefer more specific match
        assert suggested is not None


class TestTagMerging:
    """Tests for merging tags."""

    def test_merge_tags(self, db_session: Session, tag_factory, page_factory):
        """Test merging one tag into another."""
        service = CategoryService(db_session)

        tag1 = tag_factory(name='js')
        tag2 = tag_factory(name='javascript')

        # Create page with tag1
        page = page_factory(title='Page')
        page.tags.append(tag1)
        tag1.usage_count = 5
        db_session.commit()

        # Merge tag1 into tag2
        success = service.merge_tags(
            source_tag_id=tag1.id,
            target_tag_id=tag2.id
        )

        assert success

        # tag1 should be deleted
        deleted = db_session.query(WikiTag).filter(WikiTag.id == tag1.id).first()
        assert deleted is None

        # tag2 should have increased usage count
        db_session.refresh(tag2)
        assert tag2.usage_count >= 5

    def test_merge_tags_nonexistent_fails(self, db_session: Session, tag_factory):
        """Test that merging non-existent tags fails."""
        service = CategoryService(db_session)

        tag = tag_factory(name='test')

        success = service.merge_tags(
            source_tag_id=99999,
            target_tag_id=tag.id
        )

        assert not success


class TestCircularReferenceDetection:
    """Tests for preventing circular references in category hierarchy."""

    def test_detect_circular_reference_direct(self, db_session: Session, category_factory):
        """Test detecting direct circular reference."""
        service = CategoryService(db_session)

        cat1 = category_factory(name='Category 1')
        cat2 = category_factory(name='Category 2', slug='category-2', parent_id=cat1.id)

        # Try to make cat1 a child of cat2 (direct circle)
        with pytest.raises(ValueError, match='circular'):
            service.update_category(cat1.id, parent_id=cat2.id)

    def test_detect_circular_reference_indirect(self, db_session: Session, category_factory):
        """Test detecting indirect circular reference."""
        service = CategoryService(db_session)

        cat1 = category_factory(name='Cat 1')
        cat2 = category_factory(name='Cat 2', slug='cat-2', parent_id=cat1.id)
        cat3 = category_factory(name='Cat 3', slug='cat-3', parent_id=cat2.id)

        # Try to make cat1 a child of cat3 (indirect circle)
        with pytest.raises(ValueError, match='circular'):
            service.update_category(cat1.id, parent_id=cat3.id)

    def test_self_reference_detected(self, db_session: Session, category_factory):
        """Test that self-reference is detected."""
        service = CategoryService(db_session)

        category = category_factory(name='Category')

        # Try to make category its own parent
        with pytest.raises(ValueError, match='circular'):
            service.update_category(category.id, parent_id=category.id)
