"""
Wiki Import Service

Import wiki content from various sources including Confluence, MediaWiki, Notion,
Google Docs, and markdown files. Handles structure preservation, attachment migration,
and link resolution.

Author: NEXUS Platform Team
"""

import os
import re
import json
import zipfile
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from xml.etree import ElementTree as ET
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.utils import get_logger
from modules.wiki.models import WikiPage, WikiCategory, WikiTag
from modules.wiki.wiki_types import (
    ImportSource, PageStatus, ContentFormat, ChangeType,
    PageCreateRequest
)
from modules.wiki.pages import PageManager
from modules.wiki.editor import EditorService

logger = get_logger(__name__)


class ImportService:
    """Handles import of wiki content from various external sources."""

    def __init__(self, db: Session):
        """
        Initialize ImportService.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.page_manager = PageManager(db)
        self.editor = EditorService()

    def import_from_file(
        self,
        file_path: str,
        source: ImportSource,
        user_id: int,
        namespace: Optional[str] = None,
        category_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Import wiki content from a file.

        Args:
            file_path: Path to import file
            source: Source format type
            user_id: ID of user performing import
            namespace: Optional namespace for imported pages
            category_id: Optional category ID for imported pages

        Returns:
            Dictionary with import results (success count, errors, page IDs)

        Raises:
            FileNotFoundError: If import file doesn't exist
            ValueError: If source format is unsupported

        Example:
            >>> service = ImportService(db)
            >>> result = service.import_from_file(
            ...     'confluence_export.xml',
            ...     ImportSource.CONFLUENCE,
            ...     user_id=1
            ... )
            >>> print(f"Imported {result['success_count']} pages")
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Import file not found: {file_path}")

        try:
            if source == ImportSource.CONFLUENCE:
                return self._import_confluence(file_path, user_id, namespace, category_id)
            elif source == ImportSource.MEDIAWIKI:
                return self._import_mediawiki(file_path, user_id, namespace, category_id)
            elif source == ImportSource.NOTION:
                return self._import_notion(file_path, user_id, namespace, category_id)
            elif source == ImportSource.MARKDOWN:
                return self._import_markdown(file_path, user_id, namespace, category_id)
            elif source == ImportSource.HTML:
                return self._import_html(file_path, user_id, namespace, category_id)
            else:
                raise ValueError(f"Unsupported import source: {source}")

        except Exception as e:
            logger.error(f"Error importing from {file_path}: {str(e)}")
            return {
                'success': False,
                'success_count': 0,
                'error_count': 1,
                'errors': [str(e)],
                'page_ids': []
            }

    def import_from_archive(
        self,
        archive_path: str,
        source: ImportSource,
        user_id: int,
        namespace: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Import from ZIP archive containing multiple pages.

        Args:
            archive_path: Path to ZIP archive
            source: Source format type
            user_id: ID of user performing import
            namespace: Optional namespace

        Returns:
            Dictionary with import results

        Example:
            >>> result = service.import_from_archive(
            ...     'wiki_backup.zip',
            ...     ImportSource.MARKDOWN,
            ...     user_id=1
            ... )
        """
        try:
            import tempfile
            import shutil

            # Extract archive to temp directory
            temp_dir = tempfile.mkdtemp()

            try:
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)

                # Process all files in archive
                results = {
                    'success': True,
                    'success_count': 0,
                    'error_count': 0,
                    'errors': [],
                    'page_ids': []
                }

                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if self._is_importable_file(file, source):
                            file_path = os.path.join(root, file)

                            try:
                                file_result = self.import_from_file(
                                    file_path,
                                    source,
                                    user_id,
                                    namespace=namespace
                                )

                                results['success_count'] += file_result['success_count']
                                results['error_count'] += file_result['error_count']
                                results['errors'].extend(file_result['errors'])
                                results['page_ids'].extend(file_result['page_ids'])

                            except Exception as e:
                                logger.error(f"Error importing file {file}: {str(e)}")
                                results['error_count'] += 1
                                results['errors'].append(f"{file}: {str(e)}")

                return results

            finally:
                # Cleanup temp directory
                shutil.rmtree(temp_dir, ignore_errors=True)

        except Exception as e:
            logger.error(f"Error importing from archive: {str(e)}")
            return {
                'success': False,
                'success_count': 0,
                'error_count': 1,
                'errors': [str(e)],
                'page_ids': []
            }

    # ========================================================================
    # SOURCE-SPECIFIC IMPORT METHODS
    # ========================================================================

    def _import_confluence(
        self,
        file_path: str,
        user_id: int,
        namespace: Optional[str],
        category_id: Optional[int]
    ) -> Dict[str, Any]:
        """
        Import from Confluence XML/HTML export.

        Confluence exports typically use custom XML or HTML format with
        specific macros and formatting.

        Args:
            file_path: Path to Confluence export file
            user_id: User ID
            namespace: Optional namespace
            category_id: Optional category

        Returns:
            Import results dictionary
        """
        results = {
            'success': True,
            'success_count': 0,
            'error_count': 0,
            'errors': [],
            'page_ids': []
        }

        try:
            # Parse Confluence XML
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Confluence exports often have <object> elements for pages
            pages = root.findall('.//object[@class="Page"]')

            for page_elem in pages:
                try:
                    # Extract page data
                    title = self._get_confluence_property(page_elem, 'title')
                    content = self._get_confluence_property(page_elem, 'bodyContent')

                    if not title:
                        logger.warning("Skipping page without title")
                        continue

                    # Convert Confluence storage format to HTML/Markdown
                    converted_content = self._convert_confluence_content(content)

                    # Create page
                    request = PageCreateRequest(
                        title=title,
                        content=converted_content,
                        content_format=ContentFormat.HTML,
                        namespace=namespace,
                        category_id=category_id,
                        status=PageStatus.PUBLISHED
                    )

                    page = self.page_manager.create_page(request, user_id, auto_publish=True)

                    if page:
                        results['success_count'] += 1
                        results['page_ids'].append(page.id)
                        logger.info(f"Imported Confluence page: {title}")
                    else:
                        results['error_count'] += 1
                        results['errors'].append(f"Failed to create page: {title}")

                except Exception as e:
                    logger.error(f"Error importing Confluence page: {str(e)}")
                    results['error_count'] += 1
                    results['errors'].append(str(e))

        except ET.ParseError as e:
            logger.error(f"Error parsing Confluence XML: {str(e)}")
            results['success'] = False
            results['errors'].append(f"XML parse error: {str(e)}")

        return results

    def _import_mediawiki(
        self,
        file_path: str,
        user_id: int,
        namespace: Optional[str],
        category_id: Optional[int]
    ) -> Dict[str, Any]:
        """
        Import from MediaWiki format.

        MediaWiki uses wikitext format with specific syntax for
        formatting, links, and templates.

        Args:
            file_path: Path to MediaWiki export file
            user_id: User ID
            namespace: Optional namespace
            category_id: Optional category

        Returns:
            Import results dictionary
        """
        results = {
            'success': True,
            'success_count': 0,
            'error_count': 0,
            'errors': [],
            'page_ids': []
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # MediaWiki XML format
            tree = ET.fromstring(content)

            # Find all page elements
            namespace_uri = '{http://www.mediawiki.org/xml/export-0.10/}'
            pages = tree.findall(f'.//{namespace_uri}page')

            for page_elem in pages:
                try:
                    title_elem = page_elem.find(f'{namespace_uri}title')
                    revision_elem = page_elem.find(f'{namespace_uri}revision')

                    if title_elem is None or revision_elem is None:
                        continue

                    title = title_elem.text
                    text_elem = revision_elem.find(f'{namespace_uri}text')

                    if text_elem is None or text_elem.text is None:
                        continue

                    wikitext = text_elem.text

                    # Convert MediaWiki wikitext to Markdown
                    markdown_content = self._convert_mediawiki_to_markdown(wikitext)

                    # Create page
                    request = PageCreateRequest(
                        title=title,
                        content=markdown_content,
                        content_format=ContentFormat.MARKDOWN,
                        namespace=namespace,
                        category_id=category_id,
                        status=PageStatus.PUBLISHED
                    )

                    page = self.page_manager.create_page(request, user_id, auto_publish=True)

                    if page:
                        results['success_count'] += 1
                        results['page_ids'].append(page.id)
                        logger.info(f"Imported MediaWiki page: {title}")

                except Exception as e:
                    logger.error(f"Error importing MediaWiki page: {str(e)}")
                    results['error_count'] += 1
                    results['errors'].append(str(e))

        except Exception as e:
            logger.error(f"Error parsing MediaWiki file: {str(e)}")
            results['success'] = False
            results['errors'].append(str(e))

        return results

    def _import_notion(
        self,
        file_path: str,
        user_id: int,
        namespace: Optional[str],
        category_id: Optional[int]
    ) -> Dict[str, Any]:
        """
        Import from Notion export format.

        Notion exports as HTML or Markdown with specific structure
        and embedded content.

        Args:
            file_path: Path to Notion export file
            user_id: User ID
            namespace: Optional namespace
            category_id: Optional category

        Returns:
            Import results dictionary
        """
        results = {
            'success': True,
            'success_count': 0,
            'error_count': 0,
            'errors': [],
            'page_ids': []
        }

        try:
            # Notion typically exports as HTML
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Extract title from filename or HTML
            title = os.path.splitext(os.path.basename(file_path))[0]

            # Clean Notion-specific formatting
            cleaned_content = self._clean_notion_html(html_content)

            # Convert to Markdown
            markdown_content = self.editor.convert_html_to_markdown(cleaned_content)

            # Create page
            request = PageCreateRequest(
                title=title,
                content=markdown_content,
                content_format=ContentFormat.MARKDOWN,
                namespace=namespace,
                category_id=category_id,
                status=PageStatus.PUBLISHED
            )

            page = self.page_manager.create_page(request, user_id, auto_publish=True)

            if page:
                results['success_count'] += 1
                results['page_ids'].append(page.id)
                logger.info(f"Imported Notion page: {title}")
            else:
                results['error_count'] += 1
                results['errors'].append(f"Failed to create page: {title}")

        except Exception as e:
            logger.error(f"Error importing Notion page: {str(e)}")
            results['success'] = False
            results['errors'].append(str(e))

        return results

    def _import_markdown(
        self,
        file_path: str,
        user_id: int,
        namespace: Optional[str],
        category_id: Optional[int]
    ) -> Dict[str, Any]:
        """
        Import from Markdown file.

        Supports standard Markdown with optional YAML frontmatter
        for metadata.

        Args:
            file_path: Path to Markdown file
            user_id: User ID
            namespace: Optional namespace
            category_id: Optional category

        Returns:
            Import results dictionary
        """
        results = {
            'success': True,
            'success_count': 0,
            'error_count': 0,
            'errors': [],
            'page_ids': []
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse frontmatter if present
            metadata, markdown_content = self._parse_frontmatter(content)

            # Get title from metadata or filename
            title = metadata.get('title') or os.path.splitext(os.path.basename(file_path))[0]

            # Get tags from metadata
            tags = metadata.get('tags', [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(',')]

            # Get status from metadata
            status_str = metadata.get('status', 'published')
            try:
                status = PageStatus(status_str)
            except ValueError:
                status = PageStatus.PUBLISHED

            # Create page
            request = PageCreateRequest(
                title=title,
                content=markdown_content,
                content_format=ContentFormat.MARKDOWN,
                namespace=namespace or metadata.get('namespace'),
                category_id=category_id,
                tags=tags,
                status=status
            )

            page = self.page_manager.create_page(request, user_id, auto_publish=True)

            if page:
                results['success_count'] += 1
                results['page_ids'].append(page.id)
                logger.info(f"Imported Markdown page: {title}")
            else:
                results['error_count'] += 1
                results['errors'].append(f"Failed to create page: {title}")

        except Exception as e:
            logger.error(f"Error importing Markdown file: {str(e)}")
            results['success'] = False
            results['errors'].append(str(e))

        return results

    def _import_html(
        self,
        file_path: str,
        user_id: int,
        namespace: Optional[str],
        category_id: Optional[int]
    ) -> Dict[str, Any]:
        """
        Import from HTML file.

        Args:
            file_path: Path to HTML file
            user_id: User ID
            namespace: Optional namespace
            category_id: Optional category

        Returns:
            Import results dictionary
        """
        results = {
            'success': True,
            'success_count': 0,
            'error_count': 0,
            'errors': [],
            'page_ids': []
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Extract title from HTML or filename
            title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE)
            title = title_match.group(1) if title_match else os.path.splitext(
                os.path.basename(file_path)
            )[0]

            # Extract body content
            body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content,
                                  re.IGNORECASE | re.DOTALL)
            content = body_match.group(1) if body_match else html_content

            # Clean HTML
            content = self._clean_html(content)

            # Create page
            request = PageCreateRequest(
                title=title,
                content=content,
                content_format=ContentFormat.HTML,
                namespace=namespace,
                category_id=category_id,
                status=PageStatus.PUBLISHED
            )

            page = self.page_manager.create_page(request, user_id, auto_publish=True)

            if page:
                results['success_count'] += 1
                results['page_ids'].append(page.id)
                logger.info(f"Imported HTML page: {title}")
            else:
                results['error_count'] += 1
                results['errors'].append(f"Failed to create page: {title}")

        except Exception as e:
            logger.error(f"Error importing HTML file: {str(e)}")
            results['success'] = False
            results['errors'].append(str(e))

        return results

    # ========================================================================
    # CONTENT CONVERSION HELPERS
    # ========================================================================

    def _convert_confluence_content(self, content: str) -> str:
        """Convert Confluence storage format to HTML."""
        if not content:
            return ""

        # Convert Confluence macros to HTML
        # ac:structured-macro -> HTML equivalent
        content = re.sub(
            r'<ac:structured-macro ac:name="code">(.*?)</ac:structured-macro>',
            r'<pre><code>\1</code></pre>',
            content,
            flags=re.DOTALL
        )

        # Convert Confluence links
        content = re.sub(
            r'<ri:page ri:content-title="([^"]+)"\s*/>',
            r'<a href="/wiki/\1">\1</a>',
            content
        )

        return content

    def _convert_mediawiki_to_markdown(self, wikitext: str) -> str:
        """Convert MediaWiki wikitext to Markdown."""
        if not wikitext:
            return ""

        # Convert headings
        text = re.sub(r'======\s*(.+?)\s*======', r'###### \1', wikitext)
        text = re.sub(r'=====\s*(.+?)\s*=====', r'##### \1', text)
        text = re.sub(r'====\s*(.+?)\s*====', r'#### \1', text)
        text = re.sub(r'===\s*(.+?)\s*===', r'### \1', text)
        text = re.sub(r'==\s*(.+?)\s*==', r'## \1', text)

        # Convert bold and italic
        text = re.sub(r"'''(.+?)'''", r'**\1**', text)
        text = re.sub(r"''(.+?)''", r'*\1*', text)

        # Convert links
        text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'[\2](\1)', text)
        text = re.sub(r'\[\[([^\]]+)\]\]', r'[\1](\1)', text)

        # Convert external links
        text = re.sub(r'\[([^\s]+)\s+([^\]]+)\]', r'[\2](\1)', text)

        # Convert lists
        text = re.sub(r'^\*\s', r'- ', text, flags=re.MULTILINE)
        text = re.sub(r'^#\s', r'1. ', text, flags=re.MULTILINE)

        return text

    def _clean_notion_html(self, html: str) -> str:
        """Clean Notion-specific HTML formatting."""
        # Remove Notion-specific classes and IDs
        html = re.sub(r'\s+class="[^"]*notion[^"]*"', '', html, flags=re.IGNORECASE)
        html = re.sub(r'\s+id="[^"]*notion[^"]*"', '', html, flags=re.IGNORECASE)

        # Remove Notion wrapper divs
        html = re.sub(r'<div[^>]*page-body[^>]*>(.*?)</div>', r'\1', html,
                     flags=re.DOTALL | re.IGNORECASE)

        return html

    def _clean_html(self, html: str) -> str:
        """Clean and sanitize HTML content."""
        # Remove script tags
        html = re.sub(r'<script[^>]*>.*?</script>', '', html,
                     flags=re.DOTALL | re.IGNORECASE)

        # Remove style tags
        html = re.sub(r'<style[^>]*>.*?</style>', '', html,
                     flags=re.DOTALL | re.IGNORECASE)

        # Remove comments
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)

        return html.strip()

    def _parse_frontmatter(self, content: str) -> Tuple[Dict[str, Any], str]:
        """Parse YAML frontmatter from markdown content."""
        frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(frontmatter_pattern, content, re.DOTALL)

        if not match:
            return {}, content

        yaml_content = match.group(1)
        markdown_content = match.group(2)

        # Simple YAML parsing (for production, use PyYAML)
        metadata = {}
        for line in yaml_content.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                # Try to parse JSON for arrays
                if value.startswith('['):
                    try:
                        metadata[key] = json.loads(value)
                    except json.JSONDecodeError:
                        metadata[key] = value
                else:
                    metadata[key] = value

        return metadata, markdown_content

    def _get_confluence_property(self, element: ET.Element, property_name: str) -> Optional[str]:
        """Extract property value from Confluence XML element."""
        prop = element.find(f".//property[@name='{property_name}']")
        if prop is not None:
            return prop.text
        return None

    def _is_importable_file(self, filename: str, source: ImportSource) -> bool:
        """Check if file is importable based on source type."""
        extensions = {
            ImportSource.MARKDOWN: ['.md', '.markdown'],
            ImportSource.HTML: ['.html', '.htm'],
            ImportSource.CONFLUENCE: ['.xml', '.html'],
            ImportSource.MEDIAWIKI: ['.xml'],
            ImportSource.NOTION: ['.html', '.md'],
        }

        _, ext = os.path.splitext(filename.lower())
        return ext in extensions.get(source, [])
