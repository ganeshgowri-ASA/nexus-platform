"""
Wiki Navigation Service

Navigation and discovery features for the NEXUS Wiki System including:
- Breadcrumb generation
- Table of contents extraction
- Related pages discovery
- Site map generation
- Navigation menu building

Author: NEXUS Platform Team
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from app.utils import get_logger
from modules.wiki.models import WikiPage, WikiCategory, WikiSection, WikiLink
from modules.wiki.wiki_types import BreadcrumbItem, PageTreeNode, ContentFormat

logger = get_logger(__name__)


class NavigationService:
    """Provides navigation and content discovery capabilities."""

    def __init__(self, db: Session):
        """
        Initialize NavigationService.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_breadcrumbs(
        self,
        page_id: int,
        include_home: bool = True
    ) -> List[BreadcrumbItem]:
        """
        Generate breadcrumb trail for a page.

        Args:
            page_id: Page ID
            include_home: Include home page at start

        Returns:
            List of BreadcrumbItem instances

        Example:
            >>> service = NavigationService(db)
            >>> breadcrumbs = service.get_breadcrumbs(123)
            >>> for item in breadcrumbs:
            ...     print(f"{item.title} > ", end="")
        """
        try:
            breadcrumbs = []

            # Add home if requested
            if include_home:
                breadcrumbs.append(BreadcrumbItem(
                    page_id=0,
                    title="Home",
                    slug="",
                    url="/"
                ))

            # Get current page
            page = self.db.query(WikiPage).filter(WikiPage.id == page_id).first()
            if not page:
                return breadcrumbs

            # Build trail from parent pages
            trail = []
            current = page

            while current:
                trail.insert(0, current)
                if current.parent_page_id:
                    current = self.db.query(WikiPage).filter(
                        WikiPage.id == current.parent_page_id
                    ).first()
                else:
                    break

            # Add category breadcrumbs if exists
            if page.category_id:
                category_trail = self._get_category_breadcrumbs(page.category_id)
                for cat in category_trail:
                    breadcrumbs.append(BreadcrumbItem(
                        page_id=0,
                        title=cat.name,
                        slug=cat.slug,
                        url=f"/category/{cat.slug}"
                    ))

            # Add page trail
            for p in trail:
                breadcrumbs.append(BreadcrumbItem(
                    page_id=p.id,
                    title=p.title,
                    slug=p.slug,
                    url=p.full_path
                ))

            return breadcrumbs

        except Exception as e:
            logger.error(f"Error generating breadcrumbs: {str(e)}")
            return []

    def generate_table_of_contents(
        self,
        page_id: int,
        max_depth: int = 6,
        min_level: int = 1
    ) -> List[Dict]:
        """
        Generate table of contents from page headings.

        Args:
            page_id: Page ID
            max_depth: Maximum heading depth to include
            min_level: Minimum heading level to include

        Returns:
            List of TOC item dictionaries

        Example:
            >>> toc = service.generate_table_of_contents(123)
            >>> for item in toc:
            ...     print(f"{'  ' * item['level']}{item['title']}")
        """
        try:
            page = self.db.query(WikiPage).filter(WikiPage.id == page_id).first()
            if not page:
                return []

            toc_items = []

            # Extract from sections if they exist
            sections = self.db.query(WikiSection).filter(
                WikiSection.page_id == page_id
            ).order_by(WikiSection.order).all()

            if sections:
                for section in sections:
                    if min_level <= section.level <= max_depth:
                        toc_items.append({
                            'level': section.level,
                            'title': section.title,
                            'anchor': section.anchor_id,
                            'order': section.order
                        })
            else:
                # Extract from content
                toc_items = self._extract_headings_from_content(
                    page.content,
                    page.content_format,
                    max_depth,
                    min_level
                )

            return toc_items

        except Exception as e:
            logger.error(f"Error generating TOC: {str(e)}")
            return []

    def get_related_pages(
        self,
        page_id: int,
        limit: int = 5,
        strategy: str = 'auto'
    ) -> List[WikiPage]:
        """
        Find related pages based on various criteria.

        Args:
            page_id: Reference page ID
            limit: Maximum number of related pages
            strategy: 'auto', 'tags', 'category', 'links', 'content'

        Returns:
            List of related WikiPage instances

        Example:
            >>> related = service.get_related_pages(123, limit=5)
        """
        try:
            page = self.db.query(WikiPage).filter(WikiPage.id == page_id).first()
            if not page:
                return []

            related_pages = []

            if strategy == 'auto' or strategy == 'tags':
                # Find pages with similar tags
                if page.tags:
                    tag_ids = [t.id for t in page.tags]
                    from modules.wiki.models import page_tags

                    tag_related = self.db.query(WikiPage).join(page_tags).filter(
                        page_tags.c.tag_id.in_(tag_ids),
                        WikiPage.id != page_id,
                        WikiPage.is_deleted == False
                    ).distinct().limit(limit).all()

                    related_pages.extend(tag_related)

            if (strategy == 'auto' or strategy == 'category') and len(related_pages) < limit:
                # Find pages in same category
                if page.category_id:
                    cat_related = self.db.query(WikiPage).filter(
                        WikiPage.category_id == page.category_id,
                        WikiPage.id != page_id,
                        WikiPage.is_deleted == False
                    ).limit(limit - len(related_pages)).all()

                    related_pages.extend(cat_related)

            if (strategy == 'auto' or strategy == 'links') and len(related_pages) < limit:
                # Find linked pages
                linked = self.db.query(WikiPage).join(
                    WikiLink,
                    WikiLink.target_page_id == WikiPage.id
                ).filter(
                    WikiLink.source_page_id == page_id,
                    WikiPage.is_deleted == False
                ).limit(limit - len(related_pages)).all()

                related_pages.extend(linked)

            # Remove duplicates while preserving order
            seen = set()
            unique_related = []
            for p in related_pages:
                if p.id not in seen:
                    seen.add(p.id)
                    unique_related.append(p)

            return unique_related[:limit]

        except Exception as e:
            logger.error(f"Error finding related pages: {str(e)}")
            return []

    def get_child_pages(
        self,
        page_id: Optional[int] = None,
        recursive: bool = False,
        max_depth: int = 3
    ) -> List[WikiPage]:
        """
        Get child pages of a parent page.

        Args:
            page_id: Parent page ID (None for root pages)
            recursive: Include all descendants
            max_depth: Maximum recursion depth

        Returns:
            List of child WikiPage instances

        Example:
            >>> children = service.get_child_pages(123, recursive=True)
        """
        try:
            if recursive:
                return self._get_descendants_recursive(page_id, 0, max_depth)
            else:
                children = self.db.query(WikiPage).filter(
                    WikiPage.parent_page_id == page_id,
                    WikiPage.is_deleted == False
                ).order_by(WikiPage.title).all()
                return children

        except SQLAlchemyError as e:
            logger.error(f"Error getting child pages: {str(e)}")
            return []

    def build_page_tree(
        self,
        root_page_id: Optional[int] = None,
        max_depth: int = 3,
        include_metadata: bool = False
    ) -> List[Dict]:
        """
        Build hierarchical page tree structure.

        Args:
            root_page_id: Root page ID (None for top level)
            max_depth: Maximum tree depth
            include_metadata: Include full page metadata

        Returns:
            List of page tree dictionaries

        Example:
            >>> tree = service.build_page_tree(max_depth=2)
        """
        try:
            def build_node(page_id: Optional[int], depth: int) -> List[Dict]:
                if depth >= max_depth:
                    return []

                pages = self.db.query(WikiPage).filter(
                    WikiPage.parent_page_id == page_id,
                    WikiPage.is_deleted == False
                ).order_by(WikiPage.title).all()

                nodes = []
                for page in pages:
                    node = {
                        'id': page.id,
                        'title': page.title,
                        'slug': page.slug,
                        'url': page.full_path,
                        'depth': depth,
                        'children': build_node(page.id, depth + 1)
                    }

                    if include_metadata:
                        node.update({
                            'status': page.status.value,
                            'view_count': page.view_count,
                            'updated_at': page.updated_at,
                            'author_id': page.author_id
                        })

                    nodes.append(node)

                return nodes

            return build_node(root_page_id, 0)

        except Exception as e:
            logger.error(f"Error building page tree: {str(e)}")
            return []

    def generate_sitemap(
        self,
        include_categories: bool = True,
        published_only: bool = True,
        max_pages: int = 1000
    ) -> Dict[str, List]:
        """
        Generate complete site map.

        Args:
            include_categories: Include category pages
            published_only: Only include published pages
            max_pages: Maximum pages to include

        Returns:
            Dictionary with sitemap structure

        Example:
            >>> sitemap = service.generate_sitemap()
            >>> print(f"Total pages: {len(sitemap['pages'])}")
        """
        try:
            sitemap = {
                'pages': [],
                'categories': [],
                'generated_at': datetime.utcnow()
            }

            # Get pages
            query = self.db.query(WikiPage).filter(
                WikiPage.is_deleted == False
            )

            if published_only:
                from modules.wiki.wiki_types import PageStatus
                query = query.filter(WikiPage.status == PageStatus.PUBLISHED)

            pages = query.order_by(WikiPage.title).limit(max_pages).all()

            for page in pages:
                sitemap['pages'].append({
                    'id': page.id,
                    'title': page.title,
                    'url': page.full_path,
                    'updated_at': page.updated_at,
                    'priority': self._calculate_sitemap_priority(page)
                })

            # Get categories
            if include_categories:
                categories = self.db.query(WikiCategory).filter(
                    WikiCategory.is_active == True
                ).order_by(WikiCategory.name).all()

                for cat in categories:
                    sitemap['categories'].append({
                        'id': cat.id,
                        'name': cat.name,
                        'slug': cat.slug,
                        'url': f"/category/{cat.slug}",
                        'page_count': cat.page_count
                    })

            return sitemap

        except Exception as e:
            logger.error(f"Error generating sitemap: {str(e)}")
            return {'pages': [], 'categories': [], 'generated_at': datetime.utcnow()}

    def get_navigation_menu(
        self,
        menu_type: str = 'main',
        max_items: int = 10
    ) -> List[Dict]:
        """
        Build navigation menu structure.

        Args:
            menu_type: Type of menu ('main', 'sidebar', 'footer')
            max_items: Maximum menu items

        Returns:
            List of menu item dictionaries

        Example:
            >>> menu = service.get_navigation_menu('main')
        """
        try:
            menu_items = []

            if menu_type == 'main':
                # Get top-level categories
                categories = self.db.query(WikiCategory).filter(
                    WikiCategory.parent_id.is_(None),
                    WikiCategory.is_active == True
                ).order_by(
                    WikiCategory.order,
                    WikiCategory.name
                ).limit(max_items).all()

                for cat in categories:
                    menu_items.append({
                        'type': 'category',
                        'id': cat.id,
                        'title': cat.name,
                        'url': f"/category/{cat.slug}",
                        'icon': cat.icon,
                        'children': self._get_category_children_menu(cat.id, max_depth=2)
                    })

            elif menu_type == 'sidebar':
                # Get recently updated pages
                from modules.wiki.wiki_types import PageStatus

                recent_pages = self.db.query(WikiPage).filter(
                    WikiPage.is_deleted == False,
                    WikiPage.status == PageStatus.PUBLISHED
                ).order_by(desc(WikiPage.updated_at)).limit(max_items).all()

                for page in recent_pages:
                    menu_items.append({
                        'type': 'page',
                        'id': page.id,
                        'title': page.title,
                        'url': page.full_path
                    })

            elif menu_type == 'footer':
                # Get featured/important pages
                featured = self.db.query(WikiPage).filter(
                    WikiPage.is_featured == True,
                    WikiPage.is_deleted == False
                ).order_by(WikiPage.title).limit(max_items).all()

                for page in featured:
                    menu_items.append({
                        'type': 'page',
                        'id': page.id,
                        'title': page.title,
                        'url': page.full_path
                    })

            return menu_items

        except Exception as e:
            logger.error(f"Error building navigation menu: {str(e)}")
            return []

    def get_page_siblings(self, page_id: int) -> Tuple[Optional[WikiPage], Optional[WikiPage]]:
        """
        Get previous and next sibling pages.

        Args:
            page_id: Current page ID

        Returns:
            Tuple of (previous_page, next_page)

        Example:
            >>> prev, next = service.get_page_siblings(123)
        """
        try:
            page = self.db.query(WikiPage).filter(WikiPage.id == page_id).first()
            if not page:
                return None, None

            # Get siblings (same parent, same category)
            siblings = self.db.query(WikiPage).filter(
                WikiPage.parent_page_id == page.parent_page_id,
                WikiPage.category_id == page.category_id,
                WikiPage.is_deleted == False,
                WikiPage.id != page_id
            ).order_by(WikiPage.title).all()

            if not siblings:
                return None, None

            # Find current page position
            current_index = None
            for i, sibling in enumerate(siblings):
                if sibling.id == page_id:
                    current_index = i
                    break

            # If page not in siblings, add it and sort
            if current_index is None:
                siblings.append(page)
                siblings.sort(key=lambda p: p.title)
                current_index = next(i for i, p in enumerate(siblings) if p.id == page_id)

            # Get previous and next
            prev_page = siblings[current_index - 1] if current_index > 0 else None
            next_page = siblings[current_index + 1] if current_index < len(siblings) - 1 else None

            return prev_page, next_page

        except Exception as e:
            logger.error(f"Error getting page siblings: {str(e)}")
            return None, None

    def get_recently_viewed(
        self,
        user_id: Optional[int] = None,
        limit: int = 10
    ) -> List[WikiPage]:
        """
        Get recently viewed pages for a user or globally.

        Args:
            user_id: Optional user ID (None for global)
            limit: Maximum results

        Returns:
            List of recently viewed WikiPage instances

        Example:
            >>> recent = service.get_recently_viewed(user_id=5, limit=10)
        """
        try:
            # This would typically use analytics data
            # For now, return recently updated pages
            pages = self.db.query(WikiPage).filter(
                WikiPage.is_deleted == False,
                WikiPage.last_viewed_at.isnot(None)
            ).order_by(desc(WikiPage.last_viewed_at)).limit(limit).all()

            return pages

        except SQLAlchemyError as e:
            logger.error(f"Error getting recently viewed: {str(e)}")
            return []

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _get_category_breadcrumbs(self, category_id: int) -> List[WikiCategory]:
        """Get category breadcrumb trail."""
        breadcrumbs = []
        current = self.db.query(WikiCategory).filter(
            WikiCategory.id == category_id
        ).first()

        while current:
            breadcrumbs.insert(0, current)
            if current.parent_id:
                current = self.db.query(WikiCategory).filter(
                    WikiCategory.id == current.parent_id
                ).first()
            else:
                break

        return breadcrumbs

    def _extract_headings_from_content(
        self,
        content: str,
        format: ContentFormat,
        max_depth: int,
        min_level: int
    ) -> List[Dict]:
        """Extract headings from page content."""
        headings = []

        if format == ContentFormat.MARKDOWN:
            # Match markdown headings: # Heading
            pattern = r'^(#{1,6})\s+(.+)$'
            for i, line in enumerate(content.split('\n')):
                match = re.match(pattern, line)
                if match:
                    level = len(match.group(1))
                    if min_level <= level <= max_depth:
                        title = match.group(2).strip()
                        headings.append({
                            'level': level,
                            'title': title,
                            'anchor': self._generate_anchor(title),
                            'order': i
                        })

        elif format == ContentFormat.HTML:
            # Match HTML headings: <h1>Heading</h1>
            pattern = r'<h([1-6])(?:\s+id="([^"]*)")?>(.*?)</h\1>'
            for match in re.finditer(pattern, content, re.IGNORECASE):
                level = int(match.group(1))
                if min_level <= level <= max_depth:
                    anchor = match.group(2) or self._generate_anchor(match.group(3))
                    title = re.sub(r'<[^>]+>', '', match.group(3))
                    headings.append({
                        'level': level,
                        'title': title,
                        'anchor': anchor,
                        'order': len(headings)
                    })

        return headings

    def _generate_anchor(self, text: str) -> str:
        """Generate URL-safe anchor from text."""
        anchor = text.lower()
        anchor = re.sub(r'[^\w\s-]', '', anchor)
        anchor = re.sub(r'[\s_-]+', '-', anchor)
        anchor = re.sub(r'^-+|-+$', '', anchor)
        return anchor or 'section'

    def _get_descendants_recursive(
        self,
        page_id: Optional[int],
        depth: int,
        max_depth: int
    ) -> List[WikiPage]:
        """Recursively get all descendant pages."""
        if depth >= max_depth:
            return []

        pages = []
        children = self.db.query(WikiPage).filter(
            WikiPage.parent_page_id == page_id,
            WikiPage.is_deleted == False
        ).all()

        for child in children:
            pages.append(child)
            pages.extend(self._get_descendants_recursive(child.id, depth + 1, max_depth))

        return pages

    def _get_category_children_menu(self, category_id: int, max_depth: int) -> List[Dict]:
        """Get child categories for menu."""
        if max_depth <= 0:
            return []

        children = self.db.query(WikiCategory).filter(
            WikiCategory.parent_id == category_id,
            WikiCategory.is_active == True
        ).order_by(WikiCategory.order).limit(5).all()

        menu_items = []
        for cat in children:
            menu_items.append({
                'id': cat.id,
                'title': cat.name,
                'url': f"/category/{cat.slug}",
                'icon': cat.icon
            })

        return menu_items

    def _calculate_sitemap_priority(self, page: WikiPage) -> float:
        """Calculate sitemap priority for a page."""
        priority = 0.5

        # Increase for featured pages
        if page.is_featured:
            priority += 0.3

        # Increase based on view count
        if page.view_count > 100:
            priority += 0.2
        elif page.view_count > 50:
            priority += 0.1

        # Increase for recently updated
        if page.updated_at:
            days_old = (datetime.utcnow() - page.updated_at).days
            if days_old < 7:
                priority += 0.2
            elif days_old < 30:
                priority += 0.1

        return min(priority, 1.0)
