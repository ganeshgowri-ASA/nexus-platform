"""
Page Manager - Multi-page support with routing and dynamic pages
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
import re
import uuid


class PageType(Enum):
    """Page types"""
    STATIC = "static"
    DYNAMIC = "dynamic"
    BLOG_POST = "blog_post"
    PRODUCT = "product"
    CATEGORY = "category"
    LANDING = "landing"


class PageStatus(Enum):
    """Page status"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    SCHEDULED = "scheduled"


@dataclass
class PageMeta:
    """Page metadata"""
    title: str
    description: str = ""
    keywords: List[str] = field(default_factory=list)
    author: str = ""
    canonical_url: str = ""
    og_image: str = ""
    og_title: str = ""
    og_description: str = ""
    twitter_card: str = "summary_large_image"


@dataclass
class PageSettings:
    """Page settings"""
    show_header: bool = True
    show_footer: bool = True
    show_sidebar: bool = False
    custom_css: str = ""
    custom_js: str = ""
    password_protected: bool = False
    password: str = ""
    allow_comments: bool = False
    enable_search: bool = False


@dataclass
class Page:
    """Page definition"""
    page_id: str
    title: str
    slug: str
    page_type: PageType
    status: PageStatus
    content: List[Dict[str, Any]]  # Component structure
    meta: PageMeta
    settings: PageSettings
    parent_id: Optional[str] = None
    order: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    template_id: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "page_id": self.page_id,
            "title": self.title,
            "slug": self.slug,
            "page_type": self.page_type.value,
            "status": self.status.value,
            "content": self.content,
            "meta": {
                "title": self.meta.title,
                "description": self.meta.description,
                "keywords": self.meta.keywords,
                "author": self.meta.author,
                "canonical_url": self.meta.canonical_url,
                "og_image": self.meta.og_image,
                "og_title": self.meta.og_title,
                "og_description": self.meta.og_description,
                "twitter_card": self.meta.twitter_card,
            },
            "settings": {
                "show_header": self.settings.show_header,
                "show_footer": self.settings.show_footer,
                "show_sidebar": self.settings.show_sidebar,
                "custom_css": self.settings.custom_css,
                "custom_js": self.settings.custom_js,
                "password_protected": self.settings.password_protected,
                "allow_comments": self.settings.allow_comments,
                "enable_search": self.settings.enable_search,
            },
            "parent_id": self.parent_id,
            "order": self.order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "template_id": self.template_id,
        }


@dataclass
class Route:
    """URL route definition"""
    route_id: str
    path: str
    page_id: str
    params: Dict[str, str] = field(default_factory=dict)
    is_dynamic: bool = False


class PageManager:
    """Manager for website pages and routing"""

    def __init__(self):
        self.pages: Dict[str, Page] = {}
        self.routes: Dict[str, Route] = {}

    def create_page(
        self,
        title: str,
        slug: str,
        page_type: PageType = PageType.STATIC,
        template_id: Optional[str] = None,
        parent_id: Optional[str] = None,
    ) -> Page:
        """Create a new page"""
        # Validate slug
        if not self._is_valid_slug(slug):
            raise ValueError(f"Invalid slug: {slug}")

        # Check for duplicate slugs
        if self._slug_exists(slug, parent_id):
            raise ValueError(f"Slug '{slug}' already exists")

        page_id = str(uuid.uuid4())

        page = Page(
            page_id=page_id,
            title=title,
            slug=slug,
            page_type=page_type,
            status=PageStatus.DRAFT,
            content=[],
            meta=PageMeta(title=title),
            settings=PageSettings(),
            parent_id=parent_id,
            template_id=template_id,
        )

        self.pages[page_id] = page

        # Create route
        self._create_route_for_page(page)

        return page

    def get_page(self, page_id: str) -> Optional[Page]:
        """Get page by ID"""
        return self.pages.get(page_id)

    def get_page_by_slug(self, slug: str) -> Optional[Page]:
        """Get page by slug"""
        for page in self.pages.values():
            if page.slug == slug and page.parent_id is None:
                return page
        return None

    def update_page(
        self,
        page_id: str,
        title: Optional[str] = None,
        slug: Optional[str] = None,
        content: Optional[List[Dict[str, Any]]] = None,
        meta: Optional[PageMeta] = None,
        settings: Optional[PageSettings] = None,
    ) -> Optional[Page]:
        """Update page properties"""
        page = self.pages.get(page_id)
        if not page:
            return None

        if title:
            page.title = title
        if slug and slug != page.slug:
            if not self._is_valid_slug(slug):
                raise ValueError(f"Invalid slug: {slug}")
            if self._slug_exists(slug, page.parent_id, exclude_page_id=page_id):
                raise ValueError(f"Slug '{slug}' already exists")
            page.slug = slug
            self._update_route_for_page(page)
        if content is not None:
            page.content = content
        if meta:
            page.meta = meta
        if settings:
            page.settings = settings

        page.updated_at = datetime.now()
        return page

    def delete_page(self, page_id: str) -> bool:
        """Delete a page"""
        if page_id not in self.pages:
            return False

        # Delete child pages
        child_pages = self.get_child_pages(page_id)
        for child in child_pages:
            self.delete_page(child.page_id)

        # Delete routes
        routes_to_delete = [
            route_id for route_id, route in self.routes.items()
            if route.page_id == page_id
        ]
        for route_id in routes_to_delete:
            del self.routes[route_id]

        # Delete page
        del self.pages[page_id]
        return True

    def duplicate_page(self, page_id: str, new_title: Optional[str] = None) -> Optional[Page]:
        """Duplicate a page"""
        original = self.pages.get(page_id)
        if not original:
            return None

        new_page_id = str(uuid.uuid4())
        title = new_title or f"{original.title} (Copy)"
        slug = self._generate_unique_slug(original.slug)

        new_page = Page(
            page_id=new_page_id,
            title=title,
            slug=slug,
            page_type=original.page_type,
            status=PageStatus.DRAFT,
            content=original.content.copy(),
            meta=PageMeta(
                title=original.meta.title,
                description=original.meta.description,
                keywords=original.meta.keywords.copy(),
                author=original.meta.author,
                canonical_url="",
                og_image=original.meta.og_image,
                og_title=original.meta.og_title,
                og_description=original.meta.og_description,
                twitter_card=original.meta.twitter_card,
            ),
            settings=PageSettings(
                show_header=original.settings.show_header,
                show_footer=original.settings.show_footer,
                show_sidebar=original.settings.show_sidebar,
                custom_css=original.settings.custom_css,
                custom_js=original.settings.custom_js,
                password_protected=False,
                password="",
                allow_comments=original.settings.allow_comments,
                enable_search=original.settings.enable_search,
            ),
            parent_id=original.parent_id,
            template_id=original.template_id,
        )

        self.pages[new_page_id] = new_page
        self._create_route_for_page(new_page)

        return new_page

    def publish_page(self, page_id: str) -> bool:
        """Publish a page"""
        page = self.pages.get(page_id)
        if not page:
            return False

        page.status = PageStatus.PUBLISHED
        page.published_at = datetime.now()
        page.updated_at = datetime.now()
        return True

    def unpublish_page(self, page_id: str) -> bool:
        """Unpublish a page"""
        page = self.pages.get(page_id)
        if not page:
            return False

        page.status = PageStatus.DRAFT
        page.updated_at = datetime.now()
        return True

    def schedule_page(self, page_id: str, scheduled_at: datetime) -> bool:
        """Schedule a page for publication"""
        page = self.pages.get(page_id)
        if not page:
            return False

        page.status = PageStatus.SCHEDULED
        page.scheduled_at = scheduled_at
        page.updated_at = datetime.now()
        return True

    def archive_page(self, page_id: str) -> bool:
        """Archive a page"""
        page = self.pages.get(page_id)
        if not page:
            return False

        page.status = PageStatus.ARCHIVED
        page.updated_at = datetime.now()
        return True

    def get_all_pages(self) -> List[Page]:
        """Get all pages"""
        return list(self.pages.values())

    def get_published_pages(self) -> List[Page]:
        """Get all published pages"""
        return [p for p in self.pages.values() if p.status == PageStatus.PUBLISHED]

    def get_pages_by_type(self, page_type: PageType) -> List[Page]:
        """Get pages by type"""
        return [p for p in self.pages.values() if p.page_type == page_type]

    def get_child_pages(self, parent_id: str) -> List[Page]:
        """Get child pages of a parent"""
        return sorted(
            [p for p in self.pages.values() if p.parent_id == parent_id],
            key=lambda x: x.order
        )

    def get_root_pages(self) -> List[Page]:
        """Get all root pages (no parent)"""
        return sorted(
            [p for p in self.pages.values() if p.parent_id is None],
            key=lambda x: x.order
        )

    def get_page_hierarchy(self) -> List[Dict[str, Any]]:
        """Get page hierarchy as nested structure"""
        def build_tree(parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
            children = self.get_child_pages(parent_id) if parent_id else self.get_root_pages()
            result = []
            for page in children:
                result.append({
                    "page": page,
                    "children": build_tree(page.page_id),
                })
            return result

        return build_tree()

    def reorder_pages(self, page_ids: List[str]) -> bool:
        """Reorder pages"""
        for index, page_id in enumerate(page_ids):
            page = self.pages.get(page_id)
            if page:
                page.order = index
        return True

    def move_page(self, page_id: str, new_parent_id: Optional[str]) -> bool:
        """Move page to new parent"""
        page = self.pages.get(page_id)
        if not page:
            return False

        # Prevent circular references
        if new_parent_id and self._would_create_cycle(page_id, new_parent_id):
            return False

        page.parent_id = new_parent_id
        page.updated_at = datetime.now()
        self._update_route_for_page(page)
        return True

    def search_pages(self, query: str) -> List[Page]:
        """Search pages by title or content"""
        query = query.lower()
        return [
            p for p in self.pages.values()
            if query in p.title.lower() or query in p.meta.description.lower()
        ]

    def get_breadcrumb(self, page_id: str) -> List[Page]:
        """Get breadcrumb trail for a page"""
        breadcrumb = []
        current = self.pages.get(page_id)

        while current:
            breadcrumb.insert(0, current)
            if current.parent_id:
                current = self.pages.get(current.parent_id)
            else:
                break

        return breadcrumb

    def resolve_route(self, path: str) -> Optional[Page]:
        """Resolve URL path to page"""
        # Normalize path
        path = path.strip("/")

        # Check static routes first
        for route in self.routes.values():
            if not route.is_dynamic and route.path == path:
                return self.pages.get(route.page_id)

        # Check dynamic routes
        for route in self.routes.values():
            if route.is_dynamic:
                params = self._match_dynamic_route(path, route.path)
                if params:
                    return self.pages.get(route.page_id)

        return None

    def get_page_url(self, page_id: str) -> str:
        """Get URL for a page"""
        page = self.pages.get(page_id)
        if not page:
            return ""

        # Build URL from breadcrumb
        breadcrumb = self.get_breadcrumb(page_id)
        parts = [p.slug for p in breadcrumb]
        return "/" + "/".join(parts)

    def _create_route_for_page(self, page: Page) -> None:
        """Create route for a page"""
        path = self.get_page_url(page.page_id).strip("/")
        is_dynamic = "{" in path or page.page_type == PageType.DYNAMIC

        route = Route(
            route_id=str(uuid.uuid4()),
            path=path,
            page_id=page.page_id,
            is_dynamic=is_dynamic,
        )

        self.routes[route.route_id] = route

    def _update_route_for_page(self, page: Page) -> None:
        """Update route for a page"""
        # Delete old routes
        routes_to_delete = [
            route_id for route_id, route in self.routes.items()
            if route.page_id == page.page_id
        ]
        for route_id in routes_to_delete:
            del self.routes[route_id]

        # Create new route
        self._create_route_for_page(page)

    def _is_valid_slug(self, slug: str) -> bool:
        """Validate slug format"""
        # Slug should be lowercase, alphanumeric with hyphens
        pattern = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
        return bool(re.match(pattern, slug))

    def _slug_exists(
        self,
        slug: str,
        parent_id: Optional[str],
        exclude_page_id: Optional[str] = None
    ) -> bool:
        """Check if slug exists at the same level"""
        for page in self.pages.values():
            if page.page_id == exclude_page_id:
                continue
            if page.slug == slug and page.parent_id == parent_id:
                return True
        return False

    def _generate_unique_slug(self, base_slug: str) -> str:
        """Generate unique slug by adding suffix"""
        counter = 1
        new_slug = f"{base_slug}-{counter}"

        while self._slug_exists(new_slug, None):
            counter += 1
            new_slug = f"{base_slug}-{counter}"

        return new_slug

    def _would_create_cycle(self, page_id: str, new_parent_id: str) -> bool:
        """Check if moving page would create circular reference"""
        current = self.pages.get(new_parent_id)

        while current:
            if current.page_id == page_id:
                return True
            if current.parent_id:
                current = self.pages.get(current.parent_id)
            else:
                break

        return False

    def _match_dynamic_route(self, path: str, route_pattern: str) -> Optional[Dict[str, str]]:
        """Match path against dynamic route pattern"""
        # Convert route pattern to regex
        # Example: "blog/{category}/{slug}" -> "blog/([^/]+)/([^/]+)"
        pattern = route_pattern
        params = re.findall(r"\{([^}]+)\}", route_pattern)

        for param in params:
            pattern = pattern.replace(f"{{{param}}}", r"([^/]+)")

        match = re.match(f"^{pattern}$", path)
        if match:
            return dict(zip(params, match.groups()))

        return None

    def export_sitemap(self) -> str:
        """Export sitemap XML"""
        sitemap = ['<?xml version="1.0" encoding="UTF-8"?>']
        sitemap.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

        for page in self.get_published_pages():
            url = self.get_page_url(page.page_id)
            lastmod = page.updated_at.strftime("%Y-%m-%d") if page.updated_at else ""

            sitemap.append("  <url>")
            sitemap.append(f"    <loc>{url}</loc>")
            if lastmod:
                sitemap.append(f"    <lastmod>{lastmod}</lastmod>")
            sitemap.append("    <changefreq>weekly</changefreq>")
            sitemap.append("    <priority>0.8</priority>")
            sitemap.append("  </url>")

        sitemap.append("</urlset>")
        return "\n".join(sitemap)

    def get_page_stats(self) -> Dict[str, Any]:
        """Get page statistics"""
        return {
            "total_pages": len(self.pages),
            "published_pages": len(self.get_published_pages()),
            "draft_pages": len([p for p in self.pages.values() if p.status == PageStatus.DRAFT]),
            "archived_pages": len([p for p in self.pages.values() if p.status == PageStatus.ARCHIVED]),
            "scheduled_pages": len([p for p in self.pages.values() if p.status == PageStatus.SCHEDULED]),
            "pages_by_type": {
                page_type.value: len(self.get_pages_by_type(page_type))
                for page_type in PageType
            },
        }
