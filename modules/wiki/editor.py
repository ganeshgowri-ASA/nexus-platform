"""
Wiki Editor Service

Rich text editing with markdown support, syntax highlighting, and content processing.
Provides WYSIWYG editor functionality and content transformation.

Author: NEXUS Platform Team
"""

import re
import markdown
import html
from typing import Dict, List, Optional, Any
from markdown.extensions import extra, codehilite, toc, tables, fenced_code

from app.utils import get_logger
from modules.wiki.wiki_types import ContentFormat

logger = get_logger(__name__)


class EditorService:
    """Provides rich text editing and content processing capabilities."""

    def __init__(self):
        """Initialize EditorService with markdown extensions."""
        self.md_extensions = [
            'extra',
            'codehilite',
            'toc',
            'tables',
            'fenced_code',
            'nl2br',
            'sane_lists',
        ]

        self.md_extension_configs = {
            'codehilite': {
                'css_class': 'highlight',
                'linenums': False,
                'guess_lang': True,
            },
            'toc': {
                'permalink': True,
                'baselevel': 1,
            }
        }

    def convert_markdown_to_html(self, markdown_text: str) -> Dict[str, Any]:
        """
        Convert markdown text to HTML.

        Args:
            markdown_text: Markdown formatted text

        Returns:
            Dictionary with 'html' and 'toc' keys

        Example:
            >>> editor = EditorService()
            >>> result = editor.convert_markdown_to_html("# Hello World\\nThis is **bold**")
            >>> print(result['html'])
        """
        try:
            md = markdown.Markdown(
                extensions=self.md_extensions,
                extension_configs=self.md_extension_configs
            )

            html_content = md.convert(markdown_text)

            return {
                'html': html_content,
                'toc': md.toc if hasattr(md, 'toc') else '',
                'toc_tokens': md.toc_tokens if hasattr(md, 'toc_tokens') else []
            }

        except Exception as e:
            logger.error(f"Error converting markdown to HTML: {str(e)}")
            return {
                'html': f'<p>Error processing markdown: {str(e)}</p>',
                'toc': '',
                'toc_tokens': []
            }

    def convert_html_to_markdown(self, html_text: str) -> str:
        """
        Convert HTML to markdown (basic conversion).

        Args:
            html_text: HTML formatted text

        Returns:
            Markdown text

        Example:
            >>> md = editor.convert_html_to_markdown("<h1>Title</h1><p>Content</p>")
        """
        try:
            # Basic HTML to Markdown conversion
            # For production, consider using libraries like html2text or markdownify

            text = html_text

            # Convert headers
            text = re.sub(r'<h1>(.*?)</h1>', r'# \1\n', text, flags=re.IGNORECASE)
            text = re.sub(r'<h2>(.*?)</h2>', r'## \1\n', text, flags=re.IGNORECASE)
            text = re.sub(r'<h3>(.*?)</h3>', r'### \1\n', text, flags=re.IGNORECASE)
            text = re.sub(r'<h4>(.*?)</h4>', r'#### \1\n', text, flags=re.IGNORECASE)
            text = re.sub(r'<h5>(.*?)</h5>', r'##### \1\n', text, flags=re.IGNORECASE)
            text = re.sub(r'<h6>(.*?)</h6>', r'###### \1\n', text, flags=re.IGNORECASE)

            # Convert bold and italic
            text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', text, flags=re.IGNORECASE)
            text = re.sub(r'<b>(.*?)</b>', r'**\1**', text, flags=re.IGNORECASE)
            text = re.sub(r'<em>(.*?)</em>', r'*\1*', text, flags=re.IGNORECASE)
            text = re.sub(r'<i>(.*?)</i>', r'*\1*', text, flags=re.IGNORECASE)

            # Convert links
            text = re.sub(r'<a href="(.*?)">(.*?)</a>', r'[\2](\1)', text, flags=re.IGNORECASE)

            # Convert lists
            text = re.sub(r'<li>(.*?)</li>', r'- \1\n', text, flags=re.IGNORECASE)
            text = re.sub(r'<ul>|</ul>|<ol>|</ol>', '', text, flags=re.IGNORECASE)

            # Convert code
            text = re.sub(r'<code>(.*?)</code>', r'`\1`', text, flags=re.IGNORECASE)
            text = re.sub(r'<pre>(.*?)</pre>', r'```\n\1\n```', text, flags=re.IGNORECASE | re.DOTALL)

            # Convert paragraphs
            text = re.sub(r'<p>(.*?)</p>', r'\1\n\n', text, flags=re.IGNORECASE | re.DOTALL)

            # Convert line breaks
            text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)

            # Remove any remaining HTML tags
            text = re.sub(r'<[^>]+>', '', text)

            # Decode HTML entities
            text = html.unescape(text)

            return text.strip()

        except Exception as e:
            logger.error(f"Error converting HTML to markdown: {str(e)}")
            return html_text

    def sanitize_html(self, html_text: str) -> str:
        """
        Sanitize HTML to prevent XSS attacks.

        Args:
            html_text: HTML text to sanitize

        Returns:
            Sanitized HTML

        Example:
            >>> clean_html = editor.sanitize_html(user_input)
        """
        # For production, use a library like bleach
        # This is a basic implementation
        allowed_tags = [
            'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'blockquote', 'code', 'pre', 'hr', 'div', 'span',
            'ul', 'ol', 'li', 'dl', 'dt', 'dd',
            'table', 'thead', 'tbody', 'tr', 'th', 'td',
            'a', 'img',
        ]

        allowed_attrs = {
            'a': ['href', 'title', 'target'],
            'img': ['src', 'alt', 'title', 'width', 'height'],
            'code': ['class'],
            'pre': ['class'],
            'div': ['class'],
            'span': ['class'],
        }

        # For now, just escape the HTML
        # In production, implement proper sanitization
        return html.escape(html_text)

    def extract_headings(self, content: str, format: ContentFormat) -> List[Dict[str, Any]]:
        """
        Extract headings from content for table of contents.

        Args:
            content: Page content
            format: Content format (markdown, html, etc.)

        Returns:
            List of heading dictionaries with level, text, and anchor

        Example:
            >>> headings = editor.extract_headings(content, ContentFormat.MARKDOWN)
        """
        headings = []

        try:
            if format == ContentFormat.MARKDOWN:
                # Extract markdown headings
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    match = re.match(r'^(#{1,6})\s+(.+)$', line)
                    if match:
                        level = len(match.group(1))
                        text = match.group(2).strip()
                        anchor = self._generate_anchor(text)
                        headings.append({
                            'level': level,
                            'text': text,
                            'anchor': anchor,
                            'line': i + 1
                        })

            elif format == ContentFormat.HTML:
                # Extract HTML headings
                pattern = r'<h([1-6])(?:\s+id="([^"]*)")?>(.+?)</h\1>'
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    level = int(match.group(1))
                    anchor = match.group(2) or self._generate_anchor(match.group(3))
                    text = re.sub(r'<[^>]+>', '', match.group(3))
                    headings.append({
                        'level': level,
                        'text': text,
                        'anchor': anchor
                    })

        except Exception as e:
            logger.error(f"Error extracting headings: {str(e)}")

        return headings

    def generate_toc(self, headings: List[Dict[str, Any]]) -> str:
        """
        Generate table of contents HTML from headings.

        Args:
            headings: List of heading dictionaries

        Returns:
            HTML table of contents

        Example:
            >>> toc_html = editor.generate_toc(headings)
        """
        if not headings:
            return ""

        toc_lines = ['<div class="toc">', '<ul>']
        current_level = 0

        for heading in headings:
            level = heading['level']

            # Adjust nesting
            while current_level < level:
                toc_lines.append('<ul>')
                current_level += 1

            while current_level > level:
                toc_lines.append('</ul>')
                current_level -= 1

            # Add TOC item
            toc_lines.append(
                f'<li><a href="#{heading["anchor"]}">{html.escape(heading["text"])}</a></li>'
            )

        # Close remaining lists
        while current_level > 0:
            toc_lines.append('</ul>')
            current_level -= 1

        toc_lines.extend(['</ul>', '</div>'])

        return '\n'.join(toc_lines)

    def extract_links(self, content: str, format: ContentFormat) -> List[Dict[str, str]]:
        """
        Extract links from content.

        Args:
            content: Page content
            format: Content format

        Returns:
            List of link dictionaries with url and text

        Example:
            >>> links = editor.extract_links(content, ContentFormat.MARKDOWN)
        """
        links = []

        try:
            if format == ContentFormat.MARKDOWN:
                # Extract markdown links: [text](url)
                pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
                for match in re.finditer(pattern, content):
                    links.append({
                        'text': match.group(1),
                        'url': match.group(2)
                    })

            elif format == ContentFormat.HTML:
                # Extract HTML links
                pattern = r'<a\s+href="([^"]+)"[^>]*>(.+?)</a>'
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    links.append({
                        'url': match.group(1),
                        'text': re.sub(r'<[^>]+>', '', match.group(2))
                    })

        except Exception as e:
            logger.error(f"Error extracting links: {str(e)}")

        return links

    def format_code_block(
        self,
        code: str,
        language: str = "python",
        show_line_numbers: bool = False
    ) -> str:
        """
        Format code block with syntax highlighting.

        Args:
            code: Code to format
            language: Programming language
            show_line_numbers: Whether to show line numbers

        Returns:
            HTML formatted code block

        Example:
            >>> html = editor.format_code_block("print('hello')", language="python")
        """
        try:
            # Use markdown code fence for highlighting
            fence = f"```{language}"
            if show_line_numbers:
                fence += " linenums"

            markdown_code = f"{fence}\n{code}\n```"

            result = self.convert_markdown_to_html(markdown_code)
            return result['html']

        except Exception as e:
            logger.error(f"Error formatting code block: {str(e)}")
            return f"<pre><code>{html.escape(code)}</code></pre>"

    def insert_image(
        self,
        url: str,
        alt_text: str = "",
        title: str = "",
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> str:
        """
        Generate markdown/HTML for image insertion.

        Args:
            url: Image URL
            alt_text: Alt text for accessibility
            title: Image title
            width: Optional width
            height: Optional height

        Returns:
            Markdown formatted image

        Example:
            >>> img_md = editor.insert_image("/images/logo.png", alt_text="Logo")
        """
        # Basic markdown image
        img = f"![{alt_text}]({url}"

        if title:
            img += f' "{title}"'

        img += ")"

        # For width/height, use HTML
        if width or height:
            attrs = f'src="{url}" alt="{alt_text}"'
            if title:
                attrs += f' title="{title}"'
            if width:
                attrs += f' width="{width}"'
            if height:
                attrs += f' height="{height}"'

            img = f"<img {attrs} />"

        return img

    def create_table(
        self,
        headers: List[str],
        rows: List[List[str]],
        alignment: Optional[List[str]] = None
    ) -> str:
        """
        Create markdown table.

        Args:
            headers: List of header cells
            rows: List of rows (each row is a list of cells)
            alignment: List of alignments ('left', 'center', 'right')

        Returns:
            Markdown formatted table

        Example:
            >>> table = editor.create_table(
            ...     ['Name', 'Age'],
            ...     [['Alice', '30'], ['Bob', '25']]
            ... )
        """
        if not headers or not rows:
            return ""

        # Create header row
        table_lines = ['| ' + ' | '.join(headers) + ' |']

        # Create separator row
        if alignment:
            sep_cells = []
            for align in alignment:
                if align == 'center':
                    sep_cells.append(':---:')
                elif align == 'right':
                    sep_cells.append('---:')
                else:
                    sep_cells.append('---')
        else:
            sep_cells = ['---'] * len(headers)

        table_lines.append('| ' + ' | '.join(sep_cells) + ' |')

        # Create data rows
        for row in rows:
            table_lines.append('| ' + ' | '.join(str(cell) for cell in row) + ' |')

        return '\n'.join(table_lines)

    def _generate_anchor(self, text: str) -> str:
        """Generate URL-safe anchor from heading text."""
        anchor = text.lower()
        anchor = re.sub(r'[^\w\s-]', '', anchor)
        anchor = re.sub(r'[\s_-]+', '-', anchor)
        anchor = re.sub(r'^-+|-+$', '', anchor)
        return anchor or 'section'

    def get_content_statistics(self, content: str) -> Dict[str, int]:
        """
        Get statistics about content.

        Args:
            content: Content to analyze

        Returns:
            Dictionary with statistics (word count, character count, etc.)

        Example:
            >>> stats = editor.get_content_statistics(content)
            >>> print(f"Words: {stats['words']}")
        """
        # Remove markdown/HTML tags for accurate word count
        text = re.sub(r'<[^>]+>', '', content)
        text = re.sub(r'[#*`_\[\]\(\)]', '', text)

        words = text.split()
        sentences = re.split(r'[.!?]+', text)

        return {
            'characters': len(content),
            'characters_no_spaces': len(content.replace(' ', '')),
            'words': len(words),
            'sentences': len([s for s in sentences if s.strip()]),
            'paragraphs': len([p for p in content.split('\n\n') if p.strip()]),
            'lines': len(content.split('\n')),
        }
