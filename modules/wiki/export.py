"""
Wiki Export Service

Export wiki pages to multiple formats including PDF, HTML, Markdown, and DOCX.
Supports single page export, bulk export, and metadata preservation.

Author: NEXUS Platform Team
"""

import os
import io
import json
import zipfile
from datetime import datetime
from typing import Dict, List, Optional, Any, BinaryIO
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from app.utils import get_logger
from modules.wiki.models import WikiPage, WikiAttachment, WikiHistory
from modules.wiki.wiki_types import ExportFormat, ContentFormat
from modules.wiki.editor import EditorService

logger = get_logger(__name__)


class ExportService:
    """Handles export of wiki pages to various formats."""

    def __init__(self, db: Session):
        """
        Initialize ExportService.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.editor = EditorService()

    def export_page(
        self,
        page_id: int,
        format: ExportFormat,
        include_metadata: bool = True,
        include_attachments: bool = False
    ) -> Optional[bytes]:
        """
        Export a single page to specified format.

        Args:
            page_id: ID of the page to export
            format: Export format (PDF, HTML, MARKDOWN, DOCX)
            include_metadata: Include page metadata in export
            include_attachments: Include attachments in export

        Returns:
            Exported content as bytes or None if page not found

        Raises:
            ValueError: If format is not supported
            SQLAlchemyError: If database operation fails

        Example:
            >>> service = ExportService(db)
            >>> pdf_bytes = service.export_page(123, ExportFormat.PDF)
            >>> with open('page.pdf', 'wb') as f:
            ...     f.write(pdf_bytes)
        """
        try:
            page = self.db.query(WikiPage).filter(
                WikiPage.id == page_id,
                WikiPage.is_deleted == False
            ).options(
                joinedload(WikiPage.tags),
                joinedload(WikiPage.category),
                joinedload(WikiPage.attachments)
            ).first()

            if not page:
                logger.warning(f"Page {page_id} not found for export")
                return None

            if format == ExportFormat.HTML:
                return self._export_to_html(page, include_metadata)
            elif format == ExportFormat.MARKDOWN:
                return self._export_to_markdown(page, include_metadata)
            elif format == ExportFormat.PDF:
                return self._export_to_pdf(page, include_metadata)
            elif format == ExportFormat.DOCX:
                return self._export_to_docx(page, include_metadata)
            else:
                raise ValueError(f"Unsupported export format: {format}")

        except SQLAlchemyError as e:
            logger.error(f"Error exporting page {page_id}: {str(e)}")
            raise

    def export_pages_bulk(
        self,
        page_ids: List[int],
        format: ExportFormat,
        include_metadata: bool = True
    ) -> Optional[bytes]:
        """
        Export multiple pages as a ZIP archive.

        Args:
            page_ids: List of page IDs to export
            format: Export format for individual pages
            include_metadata: Include metadata in exports

        Returns:
            ZIP archive as bytes containing all exported pages

        Example:
            >>> zip_bytes = service.export_pages_bulk([1, 2, 3], ExportFormat.HTML)
            >>> with open('wiki_export.zip', 'wb') as f:
            ...     f.write(zip_bytes)
        """
        try:
            buffer = io.BytesIO()

            with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for page_id in page_ids:
                    exported_content = self.export_page(
                        page_id,
                        format,
                        include_metadata=include_metadata
                    )

                    if exported_content:
                        page = self.db.query(WikiPage).filter(
                            WikiPage.id == page_id
                        ).first()

                        if page:
                            ext = self._get_file_extension(format)
                            filename = f"{page.slug}_{page.id}{ext}"
                            zip_file.writestr(filename, exported_content)

                # Add export manifest
                manifest = self._create_export_manifest(page_ids, format)
                zip_file.writestr('manifest.json', json.dumps(manifest, indent=2))

            buffer.seek(0)
            return buffer.getvalue()

        except Exception as e:
            logger.error(f"Error in bulk export: {str(e)}")
            return None

    def export_category(
        self,
        category_id: int,
        format: ExportFormat,
        include_metadata: bool = True,
        recursive: bool = True
    ) -> Optional[bytes]:
        """
        Export all pages in a category.

        Args:
            category_id: ID of the category
            format: Export format
            include_metadata: Include metadata
            recursive: Include pages from subcategories

        Returns:
            ZIP archive containing all exported pages

        Example:
            >>> zip_bytes = service.export_category(5, ExportFormat.MARKDOWN)
        """
        try:
            pages = self.db.query(WikiPage).filter(
                WikiPage.category_id == category_id,
                WikiPage.is_deleted == False
            ).all()

            page_ids = [page.id for page in pages]

            if not page_ids:
                logger.warning(f"No pages found in category {category_id}")
                return None

            return self.export_pages_bulk(page_ids, format, include_metadata)

        except SQLAlchemyError as e:
            logger.error(f"Error exporting category {category_id}: {str(e)}")
            return None

    def export_with_history(
        self,
        page_id: int,
        format: ExportFormat,
        include_all_versions: bool = False
    ) -> Optional[bytes]:
        """
        Export page with version history.

        Args:
            page_id: ID of the page
            format: Export format
            include_all_versions: Export all versions or just latest

        Returns:
            ZIP archive with page and history

        Example:
            >>> archive = service.export_with_history(123, ExportFormat.HTML, True)
        """
        try:
            buffer = io.BytesIO()

            with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Export current page
                current_export = self.export_page(page_id, format, include_metadata=True)
                if current_export:
                    ext = self._get_file_extension(format)
                    zip_file.writestr(f"current{ext}", current_export)

                # Export version history
                if include_all_versions:
                    history = self.db.query(WikiHistory).filter(
                        WikiHistory.page_id == page_id
                    ).order_by(WikiHistory.version.desc()).all()

                    for entry in history:
                        version_content = self._export_history_entry(entry, format)
                        if version_content:
                            filename = f"versions/v{entry.version}{ext}"
                            zip_file.writestr(filename, version_content)

                # Add history metadata
                history_meta = self._create_history_metadata(page_id)
                zip_file.writestr('history.json', json.dumps(history_meta, indent=2))

            buffer.seek(0)
            return buffer.getvalue()

        except Exception as e:
            logger.error(f"Error exporting page with history: {str(e)}")
            return None

    # ========================================================================
    # FORMAT-SPECIFIC EXPORT METHODS
    # ========================================================================

    def _export_to_html(self, page: WikiPage, include_metadata: bool) -> bytes:
        """
        Export page to HTML format with embedded CSS.

        Args:
            page: WikiPage instance to export
            include_metadata: Include metadata section

        Returns:
            HTML content as bytes
        """
        # Convert content to HTML
        if page.content_format == ContentFormat.MARKDOWN:
            result = self.editor.convert_markdown_to_html(page.content)
            content_html = result['html']
            toc_html = result['toc']
        else:
            content_html = page.content
            toc_html = ""

        # Build metadata section
        metadata_html = ""
        if include_metadata:
            tags_html = ', '.join([f'<span class="tag">{tag.name}</span>'
                                  for tag in page.tags])

            metadata_html = f"""
            <div class="metadata">
                <p><strong>Created:</strong> {page.created_at.strftime('%Y-%m-%d %H:%M')}</p>
                <p><strong>Updated:</strong> {page.updated_at.strftime('%Y-%m-%d %H:%M')}</p>
                <p><strong>Version:</strong> {page.current_version}</p>
                <p><strong>Status:</strong> {page.status.value}</p>
                {f'<p><strong>Tags:</strong> {tags_html}</p>' if tags_html else ''}
            </div>
            """

        # Assemble complete HTML document
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page.title}</title>
    <style>
        {self._get_export_css()}
    </style>
</head>
<body>
    <article class="wiki-page">
        <header>
            <h1>{page.title}</h1>
            {metadata_html}
        </header>

        {f'<aside class="toc"><h2>Table of Contents</h2>{toc_html}</aside>' if toc_html else ''}

        <main class="content">
            {content_html}
        </main>

        <footer>
            <p>Exported from NEXUS Wiki on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>
        </footer>
    </article>
</body>
</html>"""

        return html_template.encode('utf-8')

    def _export_to_markdown(self, page: WikiPage, include_metadata: bool) -> bytes:
        """
        Export page to Markdown format.

        Args:
            page: WikiPage instance to export
            include_metadata: Include YAML frontmatter

        Returns:
            Markdown content as bytes
        """
        parts = []

        # Add YAML frontmatter with metadata
        if include_metadata:
            tags = [tag.name for tag in page.tags]
            frontmatter = f"""---
title: {page.title}
slug: {page.slug}
status: {page.status.value}
created: {page.created_at.isoformat()}
updated: {page.updated_at.isoformat()}
version: {page.current_version}
tags: {json.dumps(tags)}
---

"""
            parts.append(frontmatter)

        # Add title
        parts.append(f"# {page.title}\n\n")

        # Add content
        if page.content_format == ContentFormat.MARKDOWN:
            parts.append(page.content)
        elif page.content_format == ContentFormat.HTML:
            # Convert HTML to Markdown
            md_content = self.editor.convert_html_to_markdown(page.content)
            parts.append(md_content)
        else:
            parts.append(page.content)

        # Add footer
        if include_metadata:
            parts.append(f"\n\n---\n*Exported from NEXUS Wiki on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*\n")

        return '\n'.join(parts).encode('utf-8')

    def _export_to_pdf(self, page: WikiPage, include_metadata: bool) -> bytes:
        """
        Export page to PDF format.

        This is a placeholder for PDF generation. In production, integrate
        libraries like WeasyPrint, ReportLab, or wkhtmltopdf.

        Args:
            page: WikiPage instance to export
            include_metadata: Include metadata

        Returns:
            PDF content as bytes
        """
        # First generate HTML
        html_content = self._export_to_html(page, include_metadata)

        # TODO: Integrate PDF generation library
        # Example with WeasyPrint:
        # from weasyprint import HTML
        # pdf_bytes = HTML(string=html_content.decode('utf-8')).write_pdf()

        # For now, return HTML with a note
        logger.warning("PDF export requires PDF library integration (WeasyPrint, etc.)")

        # Return HTML as placeholder
        return html_content

    def _export_to_docx(self, page: WikiPage, include_metadata: bool) -> bytes:
        """
        Export page to DOCX format.

        This is a placeholder for DOCX generation. In production, integrate
        python-docx library for proper Word document generation.

        Args:
            page: WikiPage instance to export
            include_metadata: Include metadata

        Returns:
            DOCX content as bytes
        """
        # TODO: Integrate python-docx library
        # Example:
        # from docx import Document
        # doc = Document()
        # doc.add_heading(page.title, 0)
        # if include_metadata:
        #     doc.add_paragraph(f'Created: {page.created_at}')
        # # Add content paragraphs
        # buffer = io.BytesIO()
        # doc.save(buffer)
        # return buffer.getvalue()

        logger.warning("DOCX export requires python-docx library integration")

        # Return markdown as placeholder
        return self._export_to_markdown(page, include_metadata)

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _export_history_entry(self, entry: WikiHistory, format: ExportFormat) -> Optional[bytes]:
        """Export a single history entry in specified format."""
        try:
            # Create a temporary page-like object from history
            content_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{entry.title} - Version {entry.version}</title>
    <style>{self._get_export_css()}</style>
</head>
<body>
    <h1>{entry.title}</h1>
    <p><strong>Version:</strong> {entry.version}</p>
    <p><strong>Changed:</strong> {entry.changed_at.strftime('%Y-%m-%d %H:%M')}</p>
    <p><strong>Change Type:</strong> {entry.change_type.value}</p>
    <p><strong>Summary:</strong> {entry.change_summary or 'N/A'}</p>
    <hr>
    <div class="content">{entry.content}</div>
</body>
</html>"""

            if format == ExportFormat.HTML:
                return content_html.encode('utf-8')
            elif format == ExportFormat.MARKDOWN:
                md_content = f"""# {entry.title}

**Version:** {entry.version}
**Changed:** {entry.changed_at.strftime('%Y-%m-%d %H:%M')}
**Change Type:** {entry.change_type.value}
**Summary:** {entry.change_summary or 'N/A'}

---

{entry.content}
"""
                return md_content.encode('utf-8')

            return content_html.encode('utf-8')

        except Exception as e:
            logger.error(f"Error exporting history entry: {str(e)}")
            return None

    def _create_export_manifest(self, page_ids: List[int], format: ExportFormat) -> Dict:
        """Create export manifest with metadata."""
        return {
            'export_date': datetime.utcnow().isoformat(),
            'export_format': format.value,
            'page_count': len(page_ids),
            'page_ids': page_ids,
            'nexus_version': '1.0.0',
            'schema_version': '1.0'
        }

    def _create_history_metadata(self, page_id: int) -> Dict:
        """Create history metadata for export."""
        history = self.db.query(WikiHistory).filter(
            WikiHistory.page_id == page_id
        ).order_by(WikiHistory.version.desc()).all()

        return {
            'page_id': page_id,
            'total_versions': len(history),
            'versions': [
                {
                    'version': entry.version,
                    'changed_at': entry.changed_at.isoformat(),
                    'changed_by': entry.changed_by,
                    'change_type': entry.change_type.value,
                    'summary': entry.change_summary,
                    'size': entry.content_size
                }
                for entry in history
            ]
        }

    def _get_file_extension(self, format: ExportFormat) -> str:
        """Get file extension for export format."""
        extensions = {
            ExportFormat.HTML: '.html',
            ExportFormat.MARKDOWN: '.md',
            ExportFormat.PDF: '.pdf',
            ExportFormat.DOCX: '.docx',
        }
        return extensions.get(format, '.txt')

    def _get_export_css(self) -> str:
        """Get CSS styles for HTML exports."""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: #fff;
        }

        .wiki-page header h1 {
            font-size: 2.5rem;
            margin-bottom: 1rem;
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 0.5rem;
        }

        .metadata {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 5px;
            margin: 1rem 0;
            border-left: 4px solid #3498db;
        }

        .metadata p {
            margin: 0.5rem 0;
            font-size: 0.9rem;
        }

        .tag {
            display: inline-block;
            background: #3498db;
            color: white;
            padding: 0.2rem 0.6rem;
            border-radius: 3px;
            margin: 0 0.3rem;
            font-size: 0.85rem;
        }

        .toc {
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 5px;
            margin: 2rem 0;
        }

        .toc h2 {
            margin-bottom: 1rem;
            color: #2c3e50;
        }

        .content {
            margin: 2rem 0;
        }

        .content h1, .content h2, .content h3 {
            margin-top: 2rem;
            margin-bottom: 1rem;
            color: #2c3e50;
        }

        .content p {
            margin: 1rem 0;
        }

        .content code {
            background: #f4f4f4;
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }

        .content pre {
            background: #2c3e50;
            color: #ecf0f1;
            padding: 1rem;
            border-radius: 5px;
            overflow-x: auto;
            margin: 1rem 0;
        }

        .content pre code {
            background: none;
            color: inherit;
            padding: 0;
        }

        .content blockquote {
            border-left: 4px solid #3498db;
            padding-left: 1rem;
            margin: 1rem 0;
            color: #555;
            font-style: italic;
        }

        .content table {
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
        }

        .content th, .content td {
            border: 1px solid #ddd;
            padding: 0.75rem;
            text-align: left;
        }

        .content th {
            background: #3498db;
            color: white;
            font-weight: bold;
        }

        .content tr:nth-child(even) {
            background: #f8f9fa;
        }

        footer {
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #666;
            font-size: 0.9rem;
        }

        @media print {
            body {
                max-width: 100%;
            }

            .toc {
                page-break-after: always;
            }
        }
        """
