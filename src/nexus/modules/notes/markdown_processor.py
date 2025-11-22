"""Markdown processing utilities for notes."""

import re
from typing import Any, Dict, List

import bleach
import markdown as md
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor


class ChecklistExtension(Extension):
    """Markdown extension for task lists/checklists."""

    def extendMarkdown(self, md_instance: md.Markdown) -> None:
        """Register the extension."""
        md_instance.treeprocessors.register(
            ChecklistTreeprocessor(md_instance), "checklist", 15
        )


class ChecklistTreeprocessor(Treeprocessor):
    """Process checklist items in markdown."""

    def run(self, root: Any) -> None:
        """Process the markdown tree."""
        # Find all list items
        for li in root.iter("li"):
            text = li.text or ""
            # Check for [ ] or [x] pattern
            if text.strip().startswith("[ ]"):
                li.set("class", "task-list-item")
                checkbox = '<input type="checkbox" disabled>'
                li.text = text.replace("[ ]", checkbox, 1)
            elif text.strip().startswith("[x]") or text.strip().startswith("[X]"):
                li.set("class", "task-list-item")
                checkbox = '<input type="checkbox" checked disabled>'
                li.text = text.replace("[x]", checkbox, 1).replace("[X]", checkbox, 1)


class MarkdownProcessor:
    """Process markdown content with extended features."""

    def __init__(self):
        """Initialize markdown processor."""
        self.md = md.Markdown(
            extensions=[
                "extra",
                "codehilite",
                "tables",
                "fenced_code",
                "nl2br",
                "toc",
                "sane_lists",
                ChecklistExtension(),
            ],
            extension_configs={
                "codehilite": {
                    "css_class": "highlight",
                    "linenums": False,
                },
                "toc": {
                    "permalink": True,
                    "toc_depth": "2-6",
                },
            },
        )

    def to_html(self, markdown_text: str, sanitize: bool = True) -> str:
        """Convert markdown to HTML.

        Args:
            markdown_text: Markdown content
            sanitize: Whether to sanitize HTML output

        Returns:
            HTML content
        """
        if not markdown_text:
            return ""

        html = self.md.convert(markdown_text)

        if sanitize:
            html = self.sanitize_html(html)

        return html

    def sanitize_html(self, html: str) -> str:
        """Sanitize HTML to prevent XSS attacks.

        Args:
            html: HTML content

        Returns:
            Sanitized HTML
        """
        allowed_tags = [
            "p",
            "br",
            "strong",
            "em",
            "u",
            "s",
            "del",
            "ins",
            "mark",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "blockquote",
            "code",
            "pre",
            "ul",
            "ol",
            "li",
            "a",
            "img",
            "table",
            "thead",
            "tbody",
            "tr",
            "th",
            "td",
            "hr",
            "div",
            "span",
            "input",
        ]

        allowed_attrs = {
            "a": ["href", "title", "target", "rel"],
            "img": ["src", "alt", "title", "width", "height"],
            "code": ["class"],
            "pre": ["class"],
            "div": ["class", "id"],
            "span": ["class"],
            "input": ["type", "checked", "disabled"],
            "li": ["class"],
            "th": ["align"],
            "td": ["align"],
        }

        return bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs)

    def extract_headings(self, markdown_text: str) -> List[Dict[str, Any]]:
        """Extract headings from markdown for table of contents.

        Args:
            markdown_text: Markdown content

        Returns:
            List of headings with level and text
        """
        headings = []
        for line in markdown_text.split("\n"):
            match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
            if match:
                level = len(match.group(1))
                text = match.group(2)
                headings.append({"level": level, "text": text})
        return headings

    def extract_tasks(self, markdown_text: str) -> List[Dict[str, Any]]:
        """Extract task list items from markdown.

        Args:
            markdown_text: Markdown content

        Returns:
            List of tasks with completion status
        """
        tasks = []
        lines = markdown_text.split("\n")

        for i, line in enumerate(lines):
            # Match [ ] or [x] patterns
            unchecked = re.match(r"^[\s-]*\[\s\]\s+(.+)$", line.strip())
            checked = re.match(r"^[\s-]*\[x\]\s+(.+)$", line.strip(), re.IGNORECASE)

            if unchecked:
                tasks.append(
                    {"line": i + 1, "text": unchecked.group(1), "completed": False}
                )
            elif checked:
                tasks.append({"line": i + 1, "text": checked.group(1), "completed": True})

        return tasks

    def extract_links(self, markdown_text: str) -> List[Dict[str, str]]:
        """Extract links from markdown.

        Args:
            markdown_text: Markdown content

        Returns:
            List of links with text and URL
        """
        links = []

        # Match markdown links [text](url)
        for match in re.finditer(r"\[([^\]]+)\]\(([^\)]+)\)", markdown_text):
            links.append({"text": match.group(1), "url": match.group(2)})

        # Match bare URLs
        for match in re.finditer(
            r"https?://[^\s<>\"]+|www\.[^\s<>\"]+", markdown_text
        ):
            url = match.group(0)
            links.append({"text": url, "url": url})

        return links

    def extract_code_blocks(self, markdown_text: str) -> List[Dict[str, str]]:
        """Extract code blocks from markdown.

        Args:
            markdown_text: Markdown content

        Returns:
            List of code blocks with language and content
        """
        code_blocks = []

        # Match fenced code blocks ```language\ncode\n```
        pattern = r"```(\w*)\n(.*?)\n```"
        for match in re.finditer(pattern, markdown_text, re.DOTALL):
            language = match.group(1) or "text"
            code = match.group(2)
            code_blocks.append({"language": language, "code": code})

        return code_blocks

    def get_word_count(self, markdown_text: str) -> int:
        """Get word count from markdown (excluding code blocks).

        Args:
            markdown_text: Markdown content

        Returns:
            Word count
        """
        # Remove code blocks
        text = re.sub(r"```.*?```", "", markdown_text, flags=re.DOTALL)

        # Remove inline code
        text = re.sub(r"`[^`]+`", "", text)

        # Remove markdown syntax
        text = re.sub(r"[#*\[\]()_~`]", "", text)

        # Count words
        words = text.split()
        return len(words)

    def get_reading_time(self, markdown_text: str, wpm: int = 200) -> int:
        """Estimate reading time in minutes.

        Args:
            markdown_text: Markdown content
            wpm: Words per minute (default 200)

        Returns:
            Reading time in minutes
        """
        word_count = self.get_word_count(markdown_text)
        return max(1, word_count // wpm)
