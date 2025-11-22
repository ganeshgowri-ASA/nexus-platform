"""
Unit Tests for Wiki Search Service

Tests for search functionality, filters, full-text search, and search utilities.

Author: NEXUS Platform Team
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from modules.wiki.search import SearchService
from modules.wiki.models import WikiPage, WikiTag, WikiCategory
from modules.wiki.wiki_types import PageStatus


class TestBasicSearch:
    """Tests for basic search functionality."""

    def test_search_by_title(self, db_session: Session, sample_pages):
        """Test searching pages by title."""
        service = SearchService(db_session)
        results, total = service.search(query='Introduction')

        assert total > 0
        assert len(results) > 0
        # Should find the page with 'Introduction' in title
        assert any('introduction' in r['page'].title.lower() for r in results)

    def test_search_by_content(self, db_session: Session, sample_pages):
        """Test searching pages by content."""
        service = SearchService(db_session)
        results, total = service.search(query='Welcome')

        assert total > 0
        # Should find pages with 'Welcome' in content

    def test_search_case_insensitive(self, db_session: Session, sample_pages):
        """Test that search is case-insensitive."""
        service = SearchService(db_session)

        results_lower, _ = service.search(query='introduction')
        results_upper, _ = service.search(query='INTRODUCTION')
        results_mixed, _ = service.search(query='InTrOdUcTiOn')

        # All should return same results
        assert len(results_lower) == len(results_upper) == len(results_mixed)

    def test_search_multiple_terms(self, db_session: Session, page_factory):
        """Test searching with multiple terms."""
        page_factory(
            title='Python Tutorial',
            content='Learn Python programming basics',
            status=PageStatus.PUBLISHED
        )

        service = SearchService(db_session)
        results, total = service.search(query='python programming')

        assert total > 0

    def test_search_empty_query(self, db_session: Session, sample_pages):
        """Test searching with empty query."""
        service = SearchService(db_session)
        results, total = service.search(query='')

        # Should return all pages
        assert total > 0

    def test_search_no_results(self, db_session: Session, sample_pages):
        """Test searching with no matching results."""
        service = SearchService(db_session)
        results, total = service.search(query='xyznonexistentquery123')

        assert total == 0
        assert len(results) == 0


class TestSearchFilters:
    """Tests for search filters."""

    def test_filter_by_category(self, db_session: Session, sample_pages, sample_category):
        """Test filtering search results by category."""
        service = SearchService(db_session)
        results, total = service.search(
            query='',
            filters={'category_id': sample_category.id}
        )

        assert all(r['page'].category_id == sample_category.id for r in results)

    def test_filter_by_status(self, db_session: Session, sample_pages):
        """Test filtering by page status."""
        service = SearchService(db_session)
        results, total = service.search(
            query='',
            filters={'status': PageStatus.PUBLISHED}
        )

        assert all(r['page'].status == PageStatus.PUBLISHED for r in results)

    def test_filter_by_author(self, db_session: Session, sample_pages, mock_user):
        """Test filtering by author."""
        service = SearchService(db_session)
        results, total = service.search(
            query='',
            filters={'author_id': mock_user['id']}
        )

        assert all(r['page'].author_id == mock_user['id'] for r in results)

    def test_filter_by_namespace(self, db_session: Session, page_factory):
        """Test filtering by namespace."""
        page_factory(
            title='Docs Page',
            content='Documentation',
            status=PageStatus.PUBLISHED
        )
        page = page_factory(
            title='Test Page',
            content='Test',
            slug='test-namespace',
            status=PageStatus.PUBLISHED
        )
        page.namespace = 'test'
        db_session.commit()

        service = SearchService(db_session)
        results, total = service.search(
            query='',
            filters={'namespace': 'test'}
        )

        assert all(r['page'].namespace == 'test' for r in results)

    def test_filter_by_tags(self, db_session: Session, page_factory, tag_factory):
        """Test filtering by tags."""
        tag1 = tag_factory(name='python')
        tag2 = tag_factory(name='tutorial')

        page = page_factory(
            title='Python Tutorial',
            content='Learn Python',
            status=PageStatus.PUBLISHED
        )
        page.tags.append(tag1)
        page.tags.append(tag2)
        db_session.commit()

        service = SearchService(db_session)
        results, total = service.search(
            query='',
            filters={'tags': ['python']}
        )

        assert total > 0
        # All results should have the python tag
        for result in results:
            tag_names = [t.name for t in result['page'].tags]
            assert 'python' in tag_names

    def test_combined_filters(self, db_session: Session, page_factory, sample_category, tag_factory):
        """Test combining multiple filters."""
        tag = tag_factory(name='test-tag')
        page = page_factory(
            title='Test Page',
            content='Test content',
            status=PageStatus.PUBLISHED,
            category_id=sample_category.id
        )
        page.tags.append(tag)
        db_session.commit()

        service = SearchService(db_session)
        results, total = service.search(
            query='Test',
            filters={
                'category_id': sample_category.id,
                'status': PageStatus.PUBLISHED,
                'tags': ['test-tag']
            }
        )

        assert total > 0


class TestSearchPagination:
    """Tests for search pagination."""

    def test_search_limit(self, db_session: Session, sample_pages):
        """Test limiting search results."""
        service = SearchService(db_session)
        results, total = service.search(query='', limit=2)

        assert len(results) <= 2

    def test_search_offset(self, db_session: Session, sample_pages):
        """Test offsetting search results."""
        service = SearchService(db_session)

        # Get first page
        results1, total = service.search(query='', limit=1, offset=0)

        # Get second page
        results2, total = service.search(query='', limit=1, offset=1)

        # Results should be different
        if len(results1) > 0 and len(results2) > 0:
            assert results1[0]['page'].id != results2[0]['page'].id

    def test_search_pagination_consistency(self, db_session: Session, sample_pages):
        """Test that pagination returns consistent total count."""
        service = SearchService(db_session)

        _, total1 = service.search(query='', limit=10, offset=0)
        _, total2 = service.search(query='', limit=10, offset=10)

        assert total1 == total2


class TestSearchOrdering:
    """Tests for search result ordering."""

    def test_order_by_relevance(self, db_session: Session, page_factory):
        """Test ordering by relevance score."""
        # Create pages with varying relevance
        page_factory(
            title='Python Tutorial',
            content='Learn Python basics',
            status=PageStatus.PUBLISHED
        )
        page_factory(
            title='Advanced Topics',
            content='Python advanced programming techniques',
            status=PageStatus.PUBLISHED
        )

        service = SearchService(db_session)
        results, _ = service.search(query='Python', order_by='relevance')

        # Results should have scores
        assert all('score' in r for r in results)

    def test_order_by_date(self, db_session: Session, page_factory):
        """Test ordering by creation date."""
        page1 = page_factory(title='Old Page', status=PageStatus.PUBLISHED)
        page1.created_at = datetime.utcnow() - timedelta(days=10)
        page2 = page_factory(title='New Page', slug='new-page', status=PageStatus.PUBLISHED)
        page2.created_at = datetime.utcnow()
        db_session.commit()

        service = SearchService(db_session)
        results, _ = service.search(query='', order_by='date')

        # Most recent should be first
        if len(results) >= 2:
            assert results[0]['page'].created_at >= results[-1]['page'].created_at

    def test_order_by_title(self, db_session: Session, sample_pages):
        """Test ordering by title."""
        service = SearchService(db_session)
        results, _ = service.search(query='', order_by='title')

        titles = [r['page'].title for r in results]
        assert titles == sorted(titles)

    def test_order_by_views(self, db_session: Session, page_factory):
        """Test ordering by view count."""
        page1 = page_factory(title='Popular Page', status=PageStatus.PUBLISHED)
        page1.view_count = 100
        page2 = page_factory(title='Unpopular Page', slug='unpopular', status=PageStatus.PUBLISHED)
        page2.view_count = 10
        db_session.commit()

        service = SearchService(db_session)
        results, _ = service.search(query='Page', order_by='views')

        # Should be ordered by views descending
        if len(results) >= 2:
            assert results[0]['page'].view_count >= results[-1]['page'].view_count


class TestFullTextSearch:
    """Tests for full-text search functionality."""

    def test_full_text_search(self, db_session: Session, page_factory):
        """Test full-text search."""
        page_factory(
            title='Machine Learning Guide',
            content='Introduction to machine learning concepts',
            status=PageStatus.PUBLISHED
        )

        service = SearchService(db_session)
        pages, total = service.full_text_search('machine learning')

        assert total > 0
        assert len(pages) > 0

    def test_full_text_search_title_match(self, db_session: Session, page_factory):
        """Test that full-text search matches titles."""
        page_factory(
            title='Python Programming',
            content='Other content',
            status=PageStatus.PUBLISHED
        )

        service = SearchService(db_session)
        pages, total = service.full_text_search('Python')

        assert total > 0

    def test_full_text_search_content_match(self, db_session: Session, page_factory):
        """Test that full-text search matches content."""
        page_factory(
            title='Tutorial',
            content='Learn about JavaScript frameworks',
            status=PageStatus.PUBLISHED
        )

        service = SearchService(db_session)
        pages, total = service.full_text_search('JavaScript')

        assert total > 0

    def test_full_text_search_summary_match(self, db_session: Session, page_factory):
        """Test that full-text search matches summaries."""
        page = page_factory(
            title='Test Page',
            content='Content',
            status=PageStatus.PUBLISHED
        )
        page.summary = 'Database optimization techniques'
        db_session.commit()

        service = SearchService(db_session)
        pages, total = service.full_text_search('Database')

        assert total > 0


class TestSearchByTags:
    """Tests for tag-based searching."""

    def test_search_by_single_tag(self, db_session: Session, page_factory, tag_factory):
        """Test searching by a single tag."""
        tag = tag_factory(name='python')
        page = page_factory(
            title='Python Guide',
            content='Guide',
            status=PageStatus.PUBLISHED
        )
        page.tags.append(tag)
        db_session.commit()

        service = SearchService(db_session)
        pages = service.search_by_tags(['python'])

        assert len(pages) > 0
        assert any(tag.name == 'python' for tag in pages[0].tags)

    def test_search_by_multiple_tags_any(self, db_session: Session, page_factory, tag_factory):
        """Test searching by multiple tags (match any)."""
        tag1 = tag_factory(name='python')
        tag2 = tag_factory(name='javascript')

        page1 = page_factory(title='Python Page', slug='python-page', status=PageStatus.PUBLISHED)
        page1.tags.append(tag1)

        page2 = page_factory(title='JS Page', slug='js-page', status=PageStatus.PUBLISHED)
        page2.tags.append(tag2)

        db_session.commit()

        service = SearchService(db_session)
        pages = service.search_by_tags(['python', 'javascript'], match_all=False)

        assert len(pages) >= 2

    def test_search_by_multiple_tags_all(self, db_session: Session, page_factory, tag_factory):
        """Test searching by multiple tags (match all)."""
        tag1 = tag_factory(name='python')
        tag2 = tag_factory(name='tutorial')

        page = page_factory(
            title='Python Tutorial',
            content='Tutorial content',
            status=PageStatus.PUBLISHED
        )
        page.tags.extend([tag1, tag2])
        db_session.commit()

        service = SearchService(db_session)
        pages = service.search_by_tags(['python', 'tutorial'], match_all=True)

        assert len(pages) > 0
        # Page should have both tags
        page_tags = {t.name for t in pages[0].tags}
        assert 'python' in page_tags
        assert 'tutorial' in page_tags

    def test_search_by_nonexistent_tag(self, db_session: Session):
        """Test searching by non-existent tag."""
        service = SearchService(db_session)
        pages = service.search_by_tags(['nonexistent'])

        assert len(pages) == 0


class TestSearchByCategory:
    """Tests for category-based searching."""

    def test_search_by_category(self, db_session: Session, page_factory, category_factory):
        """Test searching by category."""
        category = category_factory(name='Documentation')
        page = page_factory(
            title='Docs Page',
            content='Documentation',
            category_id=category.id,
            status=PageStatus.PUBLISHED
        )

        service = SearchService(db_session)
        pages = service.search_by_category(category.id, include_subcategories=False)

        assert len(pages) > 0
        assert all(p.category_id == category.id for p in pages)

    def test_search_by_category_with_subcategories(
        self, db_session: Session, page_factory, category_factory
    ):
        """Test searching by category including subcategories."""
        parent = category_factory(name='Parent')
        child = category_factory(name='Child', slug='child', parent_id=parent.id)

        page1 = page_factory(
            title='Parent Page',
            content='Content',
            category_id=parent.id,
            status=PageStatus.PUBLISHED
        )
        page2 = page_factory(
            title='Child Page',
            slug='child-page',
            content='Content',
            category_id=child.id,
            status=PageStatus.PUBLISHED
        )

        service = SearchService(db_session)
        pages = service.search_by_category(parent.id, include_subcategories=True)

        # Should include both parent and child category pages
        assert len(pages) >= 2


class TestAdvancedSearch:
    """Tests for advanced search with multiple criteria."""

    def test_advanced_search_title_only(self, db_session: Session, page_factory):
        """Test advanced search by title."""
        page_factory(
            title='Python Tutorial',
            content='Content',
            status=PageStatus.PUBLISHED
        )

        service = SearchService(db_session)
        pages, total = service.advanced_search(title='Python')

        assert total > 0

    def test_advanced_search_content_only(self, db_session: Session, page_factory):
        """Test advanced search by content."""
        page_factory(
            title='Guide',
            content='Machine learning algorithms',
            status=PageStatus.PUBLISHED
        )

        service = SearchService(db_session)
        pages, total = service.advanced_search(content='algorithms')

        assert total > 0

    def test_advanced_search_date_range(self, db_session: Session, page_factory):
        """Test advanced search with date range."""
        old_page = page_factory(title='Old Page', status=PageStatus.PUBLISHED)
        old_page.created_at = datetime.utcnow() - timedelta(days=100)

        new_page = page_factory(title='New Page', slug='new-page', status=PageStatus.PUBLISHED)
        new_page.created_at = datetime.utcnow()

        db_session.commit()

        service = SearchService(db_session)
        date_from = datetime.utcnow() - timedelta(days=50)
        pages, total = service.advanced_search(date_from=date_from)

        # Should only get new page
        assert all(p.created_at >= date_from for p in pages)

    def test_advanced_search_combined_criteria(
        self, db_session: Session, page_factory, category_factory, tag_factory
    ):
        """Test advanced search with multiple criteria."""
        category = category_factory(name='Tutorials')
        tag = tag_factory(name='beginner')

        page = page_factory(
            title='Python Basics',
            content='Introduction to Python',
            category_id=category.id,
            status=PageStatus.PUBLISHED
        )
        page.tags.append(tag)
        db_session.commit()

        service = SearchService(db_session)
        pages, total = service.advanced_search(
            title='Python',
            category_ids=[category.id],
            tags=['beginner'],
            status=PageStatus.PUBLISHED
        )

        assert total > 0


class TestSimilarPages:
    """Tests for finding similar pages."""

    def test_suggest_similar_pages(self, db_session: Session, page_factory, tag_factory, category_factory):
        """Test suggesting similar pages."""
        category = category_factory(name='Programming')
        tag = tag_factory(name='python')

        page1 = page_factory(
            title='Python Basics',
            content='Python fundamentals',
            category_id=category.id,
            status=PageStatus.PUBLISHED
        )
        page1.tags.append(tag)

        page2 = page_factory(
            title='Python Advanced',
            slug='python-advanced',
            content='Advanced Python topics',
            category_id=category.id,
            status=PageStatus.PUBLISHED
        )
        page2.tags.append(tag)

        db_session.commit()

        service = SearchService(db_session)
        similar = service.suggest_similar_pages(page1.id, limit=5)

        # Should find page2 as similar
        assert len(similar) > 0

    def test_similar_pages_same_category(self, db_session: Session, page_factory, category_factory):
        """Test that similar pages prioritize same category."""
        category = category_factory(name='Category')

        page1 = page_factory(
            title='Page 1',
            content='Content',
            category_id=category.id,
            status=PageStatus.PUBLISHED
        )
        page2 = page_factory(
            title='Page 2',
            slug='page-2',
            content='Content',
            category_id=category.id,
            status=PageStatus.PUBLISHED
        )

        db_session.commit()

        service = SearchService(db_session)
        similar = service.suggest_similar_pages(page1.id)

        if len(similar) > 0:
            assert any(p.category_id == category.id for p in similar)


class TestSearchSuggestions:
    """Tests for search query suggestions."""

    def test_get_search_suggestions(self, db_session: Session, page_factory, tag_factory):
        """Test getting search suggestions."""
        page_factory(
            title='Python Tutorial',
            content='Content',
            status=PageStatus.PUBLISHED
        )
        tag_factory(name='python')

        service = SearchService(db_session)
        suggestions = service.get_search_suggestions('pyth')

        assert len(suggestions) > 0
        assert any('python' in s.lower() for s in suggestions)

    def test_suggestions_from_titles(self, db_session: Session, page_factory):
        """Test that suggestions include page titles."""
        page_factory(
            title='JavaScript Guide',
            content='Content',
            status=PageStatus.PUBLISHED
        )

        service = SearchService(db_session)
        suggestions = service.get_search_suggestions('java')

        assert any('javascript' in s.lower() for s in suggestions)

    def test_suggestions_from_tags(self, db_session: Session, tag_factory):
        """Test that suggestions include tag names."""
        tag_factory(name='tutorial')

        service = SearchService(db_session)
        suggestions = service.get_search_suggestions('tuto')

        assert any('tutorial' in s.lower() for s in suggestions)


class TestSearchScoring:
    """Tests for search relevance scoring."""

    def test_title_match_higher_score(self, db_session: Session, page_factory):
        """Test that title matches get higher relevance scores."""
        page1 = page_factory(
            title='Python Programming',
            content='Other content',
            status=PageStatus.PUBLISHED
        )
        page2 = page_factory(
            title='Tutorial',
            slug='tutorial',
            content='This is about Python programming',
            status=PageStatus.PUBLISHED
        )

        service = SearchService(db_session)
        results, _ = service.search(query='Python')

        # Find scores
        scores = {r['page'].id: r['score'] for r in results}

        # Title match should have higher score than content match
        if page1.id in scores and page2.id in scores:
            assert scores[page1.id] >= scores[page2.id]

    def test_exact_title_match_bonus(self, db_session: Session, page_factory):
        """Test that exact title matches get bonus score."""
        page = page_factory(
            title='Python',
            content='Content',
            status=PageStatus.PUBLISHED
        )

        service = SearchService(db_session)
        results, _ = service.search(query='Python')

        if len(results) > 0:
            # Exact match should have high score
            page_result = next((r for r in results if r['page'].id == page.id), None)
            if page_result:
                assert page_result['score'] > 0.5


class TestSearchHighlights:
    """Tests for search result highlights."""

    def test_extract_highlights(self, db_session: Session, page_factory):
        """Test extracting highlighted snippets."""
        page_factory(
            title='Guide',
            content='This is a comprehensive guide about Python programming. Python is widely used.',
            status=PageStatus.PUBLISHED
        )

        service = SearchService(db_session)
        results, _ = service.search(query='Python')

        assert len(results) > 0
        # Results should have highlights
        assert 'highlights' in results[0]

    def test_highlights_show_context(self, db_session: Session, page_factory):
        """Test that highlights show surrounding context."""
        page_factory(
            title='Article',
            content='Before context. The keyword appears here. After context.',
            status=PageStatus.PUBLISHED
        )

        service = SearchService(db_session)
        results, _ = service.search(query='keyword')

        if len(results) > 0 and len(results[0]['highlights']) > 0:
            highlight = results[0]['highlights'][0]
            # Should include context
            assert len(highlight) > len('keyword')

    def test_matched_fields_reported(self, db_session: Session, page_factory):
        """Test that matched fields are reported."""
        page = page_factory(
            title='Python Guide',
            content='Content about Python',
            status=PageStatus.PUBLISHED
        )
        page.summary = 'A Python tutorial'
        db_session.commit()

        service = SearchService(db_session)
        results, _ = service.search(query='Python')

        page_result = next((r for r in results if r['page'].id == page.id), None)
        if page_result:
            matched = page_result['matched_fields']
            assert 'title' in matched or 'content' in matched or 'summary' in matched
