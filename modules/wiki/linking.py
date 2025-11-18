"""
Wiki Linking Service

Comprehensive link management for the NEXUS Wiki System including:
- Internal and external link tracking
- Backlink discovery
- Broken link detection and reporting
- Link redirect management
- Orphaned page detection

Author: NEXUS Platform Team
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse, urljoin
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from app.utils import get_logger
from modules.wiki.models import WikiPage, WikiLink
from modules.wiki.wiki_types import LinkType

logger = get_logger(__name__)


class LinkingService:
    """Manages wiki links, backlinks, and link validation."""

    def __init__(self, db: Session):
        """
        Initialize LinkingService.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.wiki_link_pattern = re.compile(r'\[\[([^\]]+)\]\]')  # [[Page Name]]
        self.md_link_pattern = re.compile(r'\[([^\]]+)\]\(([^\)]+)\)')  # [text](url)

    def extract_links_from_content(
        self,
        content: str,
        page_id: int
    ) -> List[WikiLink]:
        """
        Extract all links from page content.

        Args:
            content: Page content to parse
            page_id: ID of the source page

        Returns:
            List of WikiLink instances (not yet committed)

        Example:
            >>> service = LinkingService(db)
            >>> links = service.extract_links_from_content(content, page_id=123)
        """
        links = []

        try:
            # Extract wiki-style links [[Page Name]]
            for match in self.wiki_link_pattern.finditer(content):
                link_text = match.group(1)

                # Handle anchor links [[Page#section]]
                if '#' in link_text:
                    page_part, anchor = link_text.split('#', 1)
                else:
                    page_part = link_text
                    anchor = None

                # Find target page by title or slug
                target_page = self.db.query(WikiPage).filter(
                    or_(
                        WikiPage.title == page_part.strip(),
                        WikiPage.slug == page_part.strip().lower().replace(' ', '-')
                    ),
                    WikiPage.is_deleted == False
                ).first()

                link = WikiLink(
                    source_page_id=page_id,
                    target_page_id=target_page.id if target_page else None,
                    link_type=LinkType.INTERNAL,
                    title=link_text,
                    anchor=anchor,
                    is_broken=target_page is None
                )
                links.append(link)

            # Extract markdown links [text](url)
            for match in self.md_link_pattern.finditer(content):
                link_text = match.group(1)
                url = match.group(2)

                # Determine if internal or external
                if self._is_internal_url(url):
                    # Try to resolve internal link
                    target_page = self._resolve_internal_url(url)
                    link = WikiLink(
                        source_page_id=page_id,
                        target_page_id=target_page.id if target_page else None,
                        target_url=url if not target_page else None,
                        link_type=LinkType.INTERNAL,
                        title=link_text,
                        is_broken=target_page is None
                    )
                else:
                    link = WikiLink(
                        source_page_id=page_id,
                        target_url=url,
                        link_type=LinkType.EXTERNAL,
                        title=link_text,
                        is_broken=False
                    )
                links.append(link)

            logger.debug(f"Extracted {len(links)} links from page {page_id}")
            return links

        except Exception as e:
            logger.error(f"Error extracting links: {str(e)}")
            return []

    def update_page_links(self, page_id: int, content: str) -> int:
        """
        Update all links for a page based on current content.

        Args:
            page_id: ID of the page
            content: Current page content

        Returns:
            Number of links created/updated

        Example:
            >>> count = service.update_page_links(123, page_content)
        """
        try:
            # Remove existing links
            self.db.query(WikiLink).filter(
                WikiLink.source_page_id == page_id
            ).delete()

            # Extract and create new links
            links = self.extract_links_from_content(content, page_id)

            for link in links:
                self.db.add(link)

            self.db.commit()

            logger.info(f"Updated {len(links)} links for page {page_id}")
            return len(links)

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating page links: {str(e)}")
            return 0

    def get_backlinks(
        self,
        page_id: int,
        include_broken: bool = False
    ) -> List[WikiLink]:
        """
        Get all pages that link to this page (backlinks).

        Args:
            page_id: ID of the target page
            include_broken: Include broken links

        Returns:
            List of WikiLink instances pointing to this page

        Example:
            >>> backlinks = service.get_backlinks(123)
            >>> for link in backlinks:
            ...     print(f"Linked from page: {link.source_page_id}")
        """
        try:
            query = self.db.query(WikiLink).filter(
                WikiLink.target_page_id == page_id
            ).options(joinedload(WikiLink.source_page))

            if not include_broken:
                query = query.filter(WikiLink.is_broken == False)

            backlinks = query.all()
            logger.debug(f"Found {len(backlinks)} backlinks for page {page_id}")
            return backlinks

        except SQLAlchemyError as e:
            logger.error(f"Error getting backlinks: {str(e)}")
            return []

    def get_outgoing_links(
        self,
        page_id: int,
        link_type: Optional[LinkType] = None
    ) -> List[WikiLink]:
        """
        Get all links from this page to other pages.

        Args:
            page_id: ID of the source page
            link_type: Optional filter by link type

        Returns:
            List of WikiLink instances from this page

        Example:
            >>> links = service.get_outgoing_links(123, LinkType.INTERNAL)
        """
        try:
            query = self.db.query(WikiLink).filter(
                WikiLink.source_page_id == page_id
            ).options(joinedload(WikiLink.target_page))

            if link_type:
                query = query.filter(WikiLink.link_type == link_type)

            links = query.all()
            return links

        except SQLAlchemyError as e:
            logger.error(f"Error getting outgoing links: {str(e)}")
            return []

    def find_broken_links(
        self,
        page_id: Optional[int] = None,
        limit: int = 100
    ) -> List[WikiLink]:
        """
        Find broken links across all pages or for a specific page.

        Args:
            page_id: Optional page ID to check (None for all pages)
            limit: Maximum number of results

        Returns:
            List of broken WikiLink instances

        Example:
            >>> broken = service.find_broken_links()
            >>> print(f"Found {len(broken)} broken links")
        """
        try:
            query = self.db.query(WikiLink).filter(
                WikiLink.is_broken == True
            ).options(joinedload(WikiLink.source_page))

            if page_id:
                query = query.filter(WikiLink.source_page_id == page_id)

            broken_links = query.limit(limit).all()

            logger.info(f"Found {len(broken_links)} broken links")
            return broken_links

        except SQLAlchemyError as e:
            logger.error(f"Error finding broken links: {str(e)}")
            return []

    def repair_broken_links(
        self,
        dry_run: bool = True
    ) -> Dict[str, int]:
        """
        Attempt to repair broken links by finding matching pages.

        Args:
            dry_run: If True, don't commit changes

        Returns:
            Dictionary with repair statistics

        Example:
            >>> stats = service.repair_broken_links(dry_run=False)
            >>> print(f"Repaired: {stats['repaired']}")
        """
        try:
            broken_links = self.find_broken_links(limit=1000)
            repaired = 0
            still_broken = 0

            for link in broken_links:
                # Try to find target page
                if link.link_type == LinkType.INTERNAL and link.title:
                    target = self.db.query(WikiPage).filter(
                        or_(
                            WikiPage.title.ilike(f"%{link.title}%"),
                            WikiPage.slug == link.title.lower().replace(' ', '-')
                        ),
                        WikiPage.is_deleted == False
                    ).first()

                    if target:
                        link.target_page_id = target.id
                        link.is_broken = False
                        repaired += 1
                    else:
                        still_broken += 1
                else:
                    still_broken += 1

            if not dry_run:
                self.db.commit()
                logger.info(f"Repaired {repaired} broken links")
            else:
                self.db.rollback()
                logger.info(f"Dry run: Would repair {repaired} broken links")

            return {
                'total_checked': len(broken_links),
                'repaired': repaired,
                'still_broken': still_broken
            }

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error repairing broken links: {str(e)}")
            return {'total_checked': 0, 'repaired': 0, 'still_broken': 0}

    def check_external_links(
        self,
        page_id: Optional[int] = None,
        verify_online: bool = False
    ) -> List[Dict]:
        """
        Check external links for validity.

        Args:
            page_id: Optional page ID (None for all pages)
            verify_online: Actually check if URLs are accessible

        Returns:
            List of external link status dictionaries

        Example:
            >>> status = service.check_external_links(verify_online=True)
        """
        try:
            query = self.db.query(WikiLink).filter(
                WikiLink.link_type == LinkType.EXTERNAL
            )

            if page_id:
                query = query.filter(WikiLink.source_page_id == page_id)

            external_links = query.all()
            results = []

            for link in external_links:
                result = {
                    'link_id': link.id,
                    'url': link.target_url,
                    'title': link.title,
                    'source_page_id': link.source_page_id,
                    'is_valid': True,
                    'status_code': None,
                    'error': None
                }

                if verify_online:
                    # In production, use requests library to check URL
                    # For now, just validate URL format
                    try:
                        parsed = urlparse(link.target_url)
                        result['is_valid'] = bool(parsed.scheme and parsed.netloc)
                    except Exception as e:
                        result['is_valid'] = False
                        result['error'] = str(e)

                results.append(result)

            logger.debug(f"Checked {len(results)} external links")
            return results

        except Exception as e:
            logger.error(f"Error checking external links: {str(e)}")
            return []

    def find_orphaned_pages(self) -> List[WikiPage]:
        """
        Find pages with no incoming links (orphaned pages).

        Returns:
            List of orphaned WikiPage instances

        Example:
            >>> orphans = service.find_orphaned_pages()
            >>> print(f"Found {len(orphans)} orphaned pages")
        """
        try:
            # Subquery for pages with backlinks
            linked_pages = self.db.query(WikiLink.target_page_id).distinct()

            # Find pages not in the linked pages list
            orphaned = self.db.query(WikiPage).filter(
                WikiPage.id.notin_(linked_pages),
                WikiPage.is_deleted == False,
                WikiPage.parent_page_id.is_(None)  # Exclude child pages
            ).all()

            logger.info(f"Found {len(orphaned)} orphaned pages")
            return orphaned

        except SQLAlchemyError as e:
            logger.error(f"Error finding orphaned pages: {str(e)}")
            return []

    def create_redirect(
        self,
        from_page_id: int,
        to_page_id: int,
        user_id: int
    ) -> Optional[WikiLink]:
        """
        Create a redirect from one page to another.

        Args:
            from_page_id: Source page ID
            to_page_id: Target page ID
            user_id: User creating the redirect

        Returns:
            Created WikiLink with redirect type

        Example:
            >>> redirect = service.create_redirect(
            ...     from_page_id=123,
            ...     to_page_id=456,
            ...     user_id=1
            ... )
        """
        try:
            # Verify both pages exist
            from_page = self.db.query(WikiPage).filter(WikiPage.id == from_page_id).first()
            to_page = self.db.query(WikiPage).filter(WikiPage.id == to_page_id).first()

            if not from_page or not to_page:
                logger.warning("Cannot create redirect: page not found")
                return None

            # Check if redirect already exists
            existing = self.db.query(WikiLink).filter(
                WikiLink.source_page_id == from_page_id,
                WikiLink.target_page_id == to_page_id,
                WikiLink.link_type == LinkType.REDIRECT
            ).first()

            if existing:
                return existing

            # Create redirect link
            redirect = WikiLink(
                source_page_id=from_page_id,
                target_page_id=to_page_id,
                link_type=LinkType.REDIRECT,
                title=f"Redirect to {to_page.title}",
                is_broken=False
            )

            self.db.add(redirect)
            self.db.commit()
            self.db.refresh(redirect)

            logger.info(f"Created redirect from page {from_page_id} to {to_page_id}")
            return redirect

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating redirect: {str(e)}")
            return None

    def get_redirects(
        self,
        page_id: int,
        direction: str = 'from'
    ) -> List[WikiLink]:
        """
        Get redirects for a page.

        Args:
            page_id: Page ID
            direction: 'from' for redirects from this page, 'to' for redirects to this page

        Returns:
            List of redirect WikiLink instances

        Example:
            >>> redirects = service.get_redirects(123, direction='to')
        """
        try:
            if direction == 'from':
                query = self.db.query(WikiLink).filter(
                    WikiLink.source_page_id == page_id,
                    WikiLink.link_type == LinkType.REDIRECT
                )
            else:
                query = self.db.query(WikiLink).filter(
                    WikiLink.target_page_id == page_id,
                    WikiLink.link_type == LinkType.REDIRECT
                )

            return query.all()

        except SQLAlchemyError as e:
            logger.error(f"Error getting redirects: {str(e)}")
            return []

    def get_link_graph(
        self,
        max_pages: int = 100,
        min_links: int = 1
    ) -> Dict[str, List]:
        """
        Generate a graph of page connections for visualization.

        Args:
            max_pages: Maximum number of pages to include
            min_links: Minimum number of links a page must have

        Returns:
            Dictionary with nodes and edges for graph visualization

        Example:
            >>> graph = service.get_link_graph(max_pages=50)
            >>> print(f"Nodes: {len(graph['nodes'])}, Edges: {len(graph['edges'])}")
        """
        try:
            # Get pages with sufficient links
            link_counts = self.db.query(
                WikiLink.source_page_id,
                func.count(WikiLink.id).label('link_count')
            ).filter(
                WikiLink.link_type == LinkType.INTERNAL
            ).group_by(
                WikiLink.source_page_id
            ).having(
                func.count(WikiLink.id) >= min_links
            ).limit(max_pages).all()

            page_ids = [row[0] for row in link_counts]

            # Get pages
            pages = self.db.query(WikiPage).filter(
                WikiPage.id.in_(page_ids)
            ).all()

            # Get links between these pages
            links = self.db.query(WikiLink).filter(
                WikiLink.source_page_id.in_(page_ids),
                WikiLink.target_page_id.in_(page_ids),
                WikiLink.link_type == LinkType.INTERNAL
            ).all()

            # Build graph structure
            nodes = [
                {
                    'id': page.id,
                    'label': page.title,
                    'slug': page.slug,
                    'size': page.view_count
                }
                for page in pages
            ]

            edges = [
                {
                    'source': link.source_page_id,
                    'target': link.target_page_id,
                    'title': link.title
                }
                for link in links
            ]

            return {
                'nodes': nodes,
                'edges': edges
            }

        except Exception as e:
            logger.error(f"Error generating link graph: {str(e)}")
            return {'nodes': [], 'edges': []}

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _is_internal_url(self, url: str) -> bool:
        """Check if URL is internal to the wiki."""
        if url.startswith('/') or url.startswith('#'):
            return True

        # Check if URL doesn't have a scheme (relative link)
        parsed = urlparse(url)
        if not parsed.scheme:
            return True

        return False

    def _resolve_internal_url(self, url: str) -> Optional[WikiPage]:
        """Resolve an internal URL to a WikiPage."""
        try:
            # Remove leading slash and anchor
            path = url.lstrip('/').split('#')[0]

            # Try to find by slug or path
            page = self.db.query(WikiPage).filter(
                or_(
                    WikiPage.slug == path,
                    WikiPage.path == f"/{path}/"
                ),
                WikiPage.is_deleted == False
            ).first()

            return page

        except Exception as e:
            logger.debug(f"Could not resolve internal URL '{url}': {str(e)}")
            return None
