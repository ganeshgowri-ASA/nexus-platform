"""
Document Manager

Handles document saving, loading, version control, and export functionality.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import hashlib

from .editor import WordEditor, DocumentMetadata


@dataclass
class DocumentVersion:
    """Document version information"""
    version_id: str
    version_number: int
    created_at: datetime
    created_by: str
    content_hash: str
    description: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentVersion':
        """Create from dictionary"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


@dataclass
class PageSetup:
    """Page setup configuration"""
    page_size: str = "A4"  # A4, Letter, Legal, Custom
    orientation: str = "portrait"  # portrait, landscape
    margin_top: float = 2.54  # cm
    margin_bottom: float = 2.54  # cm
    margin_left: float = 2.54  # cm
    margin_right: float = 2.54  # cm
    header_margin: float = 1.27  # cm
    footer_margin: float = 1.27  # cm
    custom_width: Optional[float] = None  # cm
    custom_height: Optional[float] = None  # cm

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class DocumentManager:
    """
    Document Manager class for saving, loading, and exporting documents.

    Features:
    - Auto-save functionality
    - Version history tracking
    - Multiple export formats (PDF, DOCX, HTML, Markdown, LaTeX, TXT)
    - Document organization and search
    - Backup and restore
    """

    def __init__(self, storage_path: str = "./modules/files/documents"):
        """
        Initialize document manager.

        Args:
            storage_path: Base path for document storage
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Version history storage
        self.versions_path = self.storage_path / "versions"
        self.versions_path.mkdir(exist_ok=True)

        # Templates storage
        self.templates_path = self.storage_path / "templates"
        self.templates_path.mkdir(exist_ok=True)

    def save_document(
        self,
        editor: WordEditor,
        version_description: Optional[str] = None
    ) -> bool:
        """
        Save a document with optional version tracking.

        Args:
            editor: WordEditor instance to save
            version_description: Optional description for this version

        Returns:
            True if save was successful
        """
        try:
            document_data = editor.to_dict()

            # Create document directory
            doc_path = self.storage_path / editor.document_id
            doc_path.mkdir(exist_ok=True)

            # Save main document file
            doc_file = doc_path / "document.json"
            with open(doc_file, 'w', encoding='utf-8') as f:
                json.dump(document_data, f, indent=2, ensure_ascii=False)

            # Save version history if enabled
            if version_description or (editor.metadata and editor.metadata.version > 1):
                self._save_version(editor, version_description or "Auto-save")

            # Mark as saved
            editor.mark_as_saved()

            return True

        except Exception as e:
            print(f"Error saving document: {e}")
            return False

    def load_document(self, document_id: str, user_id: str) -> Optional[WordEditor]:
        """
        Load a document by ID.

        Args:
            document_id: Document ID to load
            user_id: Current user ID

        Returns:
            WordEditor instance or None if not found
        """
        try:
            doc_path = self.storage_path / document_id
            doc_file = doc_path / "document.json"

            if not doc_file.exists():
                return None

            with open(doc_file, 'r', encoding='utf-8') as f:
                document_data = json.load(f)

            editor = WordEditor.from_dict(document_data)
            return editor

        except Exception as e:
            print(f"Error loading document: {e}")
            return None

    def _save_version(self, editor: WordEditor, description: str) -> None:
        """
        Save a version snapshot of the document.

        Args:
            editor: WordEditor instance
            description: Version description
        """
        try:
            if not editor.metadata:
                return

            # Calculate content hash
            content_str = json.dumps(editor.content, sort_keys=True)
            content_hash = hashlib.sha256(content_str.encode()).hexdigest()

            # Create version info
            version = DocumentVersion(
                version_id=f"{editor.document_id}-v{editor.metadata.version}",
                version_number=editor.metadata.version,
                created_at=datetime.now(),
                created_by=editor.user_id,
                content_hash=content_hash,
                description=description
            )

            # Save version data
            version_dir = self.versions_path / editor.document_id
            version_dir.mkdir(exist_ok=True)

            version_file = version_dir / f"v{editor.metadata.version}.json"
            version_data = {
                'version_info': version.to_dict(),
                'content': editor.content,
                'metadata': editor.metadata.to_dict()
            }

            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump(version_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Error saving version: {e}")

    def get_version_history(self, document_id: str) -> List[DocumentVersion]:
        """
        Get version history for a document.

        Args:
            document_id: Document ID

        Returns:
            List of DocumentVersion objects
        """
        versions = []

        try:
            version_dir = self.versions_path / document_id

            if not version_dir.exists():
                return versions

            for version_file in sorted(version_dir.glob("v*.json")):
                with open(version_file, 'r', encoding='utf-8') as f:
                    version_data = json.load(f)

                version = DocumentVersion.from_dict(version_data['version_info'])
                versions.append(version)

        except Exception as e:
            print(f"Error getting version history: {e}")

        return versions

    def restore_version(
        self,
        document_id: str,
        version_number: int,
        user_id: str
    ) -> Optional[WordEditor]:
        """
        Restore a document to a previous version.

        Args:
            document_id: Document ID
            version_number: Version number to restore
            user_id: Current user ID

        Returns:
            WordEditor instance with restored content
        """
        try:
            version_file = self.versions_path / document_id / f"v{version_number}.json"

            if not version_file.exists():
                return None

            with open(version_file, 'r', encoding='utf-8') as f:
                version_data = json.load(f)

            # Create editor from version data
            editor_data = {
                'document_id': document_id,
                'user_id': user_id,
                'content': version_data['content'],
                'metadata': version_data['metadata'],
                'is_modified': True,
                'last_save_time': None
            }

            editor = WordEditor.from_dict(editor_data)

            # Increment version since this is a restore
            editor.increment_version()

            return editor

        except Exception as e:
            print(f"Error restoring version: {e}")
            return None

    def list_documents(
        self,
        user_id: Optional[str] = None,
        search_query: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        List documents with optional filtering.

        Args:
            user_id: Filter by user ID
            search_query: Search in title and description
            tags: Filter by tags

        Returns:
            List of document metadata dictionaries
        """
        documents = []

        try:
            for doc_dir in self.storage_path.iterdir():
                if not doc_dir.is_dir():
                    continue

                doc_file = doc_dir / "document.json"
                if not doc_file.exists():
                    continue

                with open(doc_file, 'r', encoding='utf-8') as f:
                    doc_data = json.load(f)

                metadata = doc_data.get('metadata')
                if not metadata:
                    continue

                # Apply filters
                if user_id and metadata.get('author') != user_id:
                    continue

                if search_query:
                    title = metadata.get('title', '').lower()
                    desc = metadata.get('description', '').lower()
                    query = search_query.lower()
                    if query not in title and query not in desc:
                        continue

                if tags:
                    doc_tags = set(metadata.get('tags', []))
                    filter_tags = set(tags)
                    if not filter_tags.intersection(doc_tags):
                        continue

                documents.append(metadata)

        except Exception as e:
            print(f"Error listing documents: {e}")

        # Sort by modified date (most recent first)
        documents.sort(
            key=lambda x: x.get('modified_at', ''),
            reverse=True
        )

        return documents

    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and its versions.

        Args:
            document_id: Document ID to delete

        Returns:
            True if deletion was successful
        """
        try:
            # Delete main document
            doc_path = self.storage_path / document_id
            if doc_path.exists():
                import shutil
                shutil.rmtree(doc_path)

            # Delete versions
            version_dir = self.versions_path / document_id
            if version_dir.exists():
                import shutil
                shutil.rmtree(version_dir)

            return True

        except Exception as e:
            print(f"Error deleting document: {e}")
            return False

    def export_to_pdf(
        self,
        editor: WordEditor,
        output_path: str,
        page_setup: Optional[PageSetup] = None
    ) -> bool:
        """
        Export document to PDF format.

        Args:
            editor: WordEditor instance
            output_path: Output file path
            page_setup: Page setup configuration

        Returns:
            True if export was successful
        """
        try:
            from reportlab.lib.pagesizes import A4, LETTER, LEGAL
            from reportlab.lib.units import cm
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY

            # Set up page configuration
            setup = page_setup or PageSetup()

            # Get page size
            if setup.page_size == "A4":
                pagesize = A4
            elif setup.page_size == "Letter":
                pagesize = LETTER
            elif setup.page_size == "Legal":
                pagesize = LEGAL
            else:
                # Custom size
                pagesize = (
                    (setup.custom_width or 21) * cm,
                    (setup.custom_height or 29.7) * cm
                )

            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=pagesize,
                topMargin=setup.margin_top * cm,
                bottomMargin=setup.margin_bottom * cm,
                leftMargin=setup.margin_left * cm,
                rightMargin=setup.margin_right * cm
            )

            # Build content
            story = []
            styles = getSampleStyleSheet()

            # Extract text from content
            from .formatting import TextFormatter
            text = TextFormatter.delta_to_plain_text(editor.content)

            # Add paragraphs
            for paragraph in text.split('\n\n'):
                if paragraph.strip():
                    p = Paragraph(paragraph.strip(), styles['Normal'])
                    story.append(p)
                    story.append(Spacer(1, 0.2 * cm))

            # Build PDF
            doc.build(story)

            return True

        except ImportError:
            print("reportlab not installed. Install with: pip install reportlab")
            return False
        except Exception as e:
            print(f"Error exporting to PDF: {e}")
            return False

    def export_to_docx(self, editor: WordEditor, output_path: str) -> bool:
        """
        Export document to Microsoft Word format (.docx).

        Args:
            editor: WordEditor instance
            output_path: Output file path

        Returns:
            True if export was successful
        """
        try:
            from docx import Document
            from docx.shared import Pt, RGBColor

            doc = Document()

            # Add document metadata
            if editor.metadata:
                core_properties = doc.core_properties
                core_properties.title = editor.metadata.title
                core_properties.author = editor.metadata.author

            # Extract text from content
            from .formatting import TextFormatter
            text = TextFormatter.delta_to_plain_text(editor.content)

            # Add paragraphs
            for paragraph_text in text.split('\n\n'):
                if paragraph_text.strip():
                    doc.add_paragraph(paragraph_text.strip())

            # Save document
            doc.save(output_path)

            return True

        except ImportError:
            print("python-docx not installed. Install with: pip install python-docx")
            return False
        except Exception as e:
            print(f"Error exporting to DOCX: {e}")
            return False

    def export_to_html(self, editor: WordEditor, output_path: str) -> bool:
        """
        Export document to HTML format.

        Args:
            editor: WordEditor instance
            output_path: Output file path

        Returns:
            True if export was successful
        """
        try:
            from .formatting import TextFormatter

            # Convert delta to HTML
            html_content = TextFormatter.delta_to_html(editor.content)

            # Create full HTML document
            html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{editor.metadata.title if editor.metadata else 'Document'}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }}
        h1, h2, h3, h4, h5, h6 {{
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }}
        p {{
            margin-bottom: 1em;
        }}
        a {{
            color: #0066cc;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>"""

            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_template)

            return True

        except Exception as e:
            print(f"Error exporting to HTML: {e}")
            return False

    def export_to_markdown(self, editor: WordEditor, output_path: str) -> bool:
        """
        Export document to Markdown format.

        Args:
            editor: WordEditor instance
            output_path: Output file path

        Returns:
            True if export was successful
        """
        try:
            from .formatting import TextFormatter

            # Extract plain text
            text = TextFormatter.delta_to_plain_text(editor.content)

            # Add metadata as frontmatter
            markdown = ""
            if editor.metadata:
                markdown += "---\n"
                markdown += f"title: {editor.metadata.title}\n"
                markdown += f"author: {editor.metadata.author}\n"
                markdown += f"date: {editor.metadata.created_at.strftime('%Y-%m-%d')}\n"
                if editor.metadata.tags:
                    markdown += f"tags: {', '.join(editor.metadata.tags)}\n"
                markdown += "---\n\n"

            markdown += text

            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown)

            return True

        except Exception as e:
            print(f"Error exporting to Markdown: {e}")
            return False

    def export_to_latex(self, editor: WordEditor, output_path: str) -> bool:
        """
        Export document to LaTeX format.

        Args:
            editor: WordEditor instance
            output_path: Output file path

        Returns:
            True if export was successful
        """
        try:
            from .formatting import TextFormatter

            # Extract plain text
            text = TextFormatter.delta_to_plain_text(editor.content)

            # Escape special LaTeX characters
            text = text.replace('\\', '\\textbackslash{}')
            text = text.replace('&', '\\&')
            text = text.replace('%', '\\%')
            text = text.replace('$', '\\$')
            text = text.replace('#', '\\#')
            text = text.replace('_', '\\_')
            text = text.replace('{', '\\{')
            text = text.replace('}', '\\}')
            text = text.replace('~', '\\textasciitilde{}')
            text = text.replace('^', '\\textasciicircum{}')

            # Create LaTeX document
            latex = f"""\\documentclass[12pt,a4paper]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[english]{{babel}}
\\usepackage{{geometry}}
\\geometry{{margin=1in}}

\\title{{{editor.metadata.title if editor.metadata else 'Document'}}}
\\author{{{editor.metadata.author if editor.metadata else ''}}}
\\date{{\\today}}

\\begin{{document}}

\\maketitle

{text}

\\end{{document}}"""

            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(latex)

            return True

        except Exception as e:
            print(f"Error exporting to LaTeX: {e}")
            return False

    def export_to_txt(self, editor: WordEditor, output_path: str) -> bool:
        """
        Export document to plain text format.

        Args:
            editor: WordEditor instance
            output_path: Output file path

        Returns:
            True if export was successful
        """
        try:
            from .formatting import TextFormatter

            # Extract plain text
            text = TextFormatter.delta_to_plain_text(editor.content)

            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)

            return True

        except Exception as e:
            print(f"Error exporting to TXT: {e}")
            return False
