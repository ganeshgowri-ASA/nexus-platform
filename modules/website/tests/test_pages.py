"""
Tests for page management
"""

import pytest
from modules.website.pages import (
    PageManager,
    PageType,
    PageStatus,
    PageMeta,
    PageSettings,
)


def test_create_page():
    """Test page creation"""
    manager = PageManager()

    page = manager.create_page(
        title="Home",
        slug="home",
        page_type=PageType.STATIC,
    )

    assert page.title == "Home"
    assert page.slug == "home"
    assert page.page_type == PageType.STATIC
    assert page.status == PageStatus.DRAFT


def test_duplicate_slug_prevention():
    """Test that duplicate slugs are prevented"""
    manager = PageManager()

    manager.create_page(title="Home", slug="home")

    with pytest.raises(ValueError):
        manager.create_page(title="Another Home", slug="home")


def test_publish_page():
    """Test publishing a page"""
    manager = PageManager()

    page = manager.create_page(title="Home", slug="home")

    result = manager.publish_page(page.page_id)

    assert result is True
    assert page.status == PageStatus.PUBLISHED
    assert page.published_at is not None


def test_get_page_hierarchy():
    """Test page hierarchy"""
    manager = PageManager()

    # Create parent page
    parent = manager.create_page(title="Products", slug="products")

    # Create child pages
    child1 = manager.create_page(
        title="Electronics",
        slug="electronics",
        parent_id=parent.page_id
    )

    child2 = manager.create_page(
        title="Clothing",
        slug="clothing",
        parent_id=parent.page_id
    )

    hierarchy = manager.get_page_hierarchy()

    assert len(hierarchy) == 1
    assert hierarchy[0]["page"].page_id == parent.page_id
    assert len(hierarchy[0]["children"]) == 2


def test_page_url_generation():
    """Test URL generation for pages"""
    manager = PageManager()

    parent = manager.create_page(title="Products", slug="products")
    child = manager.create_page(
        title="Electronics",
        slug="electronics",
        parent_id=parent.page_id
    )

    url = manager.get_page_url(child.page_id)

    assert url == "/products/electronics"


def test_breadcrumb():
    """Test breadcrumb generation"""
    manager = PageManager()

    parent = manager.create_page(title="Products", slug="products")
    child = manager.create_page(
        title="Electronics",
        slug="electronics",
        parent_id=parent.page_id
    )

    breadcrumb = manager.get_breadcrumb(child.page_id)

    assert len(breadcrumb) == 2
    assert breadcrumb[0].page_id == parent.page_id
    assert breadcrumb[1].page_id == child.page_id


def test_sitemap_export():
    """Test sitemap XML export"""
    manager = PageManager()

    page1 = manager.create_page(title="Home", slug="home")
    page2 = manager.create_page(title="About", slug="about")

    manager.publish_page(page1.page_id)
    manager.publish_page(page2.page_id)

    sitemap = manager.export_sitemap()

    assert "<?xml version" in sitemap
    assert "<urlset" in sitemap
    assert "/home" in sitemap or "home" in sitemap


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
