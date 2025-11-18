"""
Mind Map Export System

This module provides export functionality to multiple formats including
PNG, PDF, JSON, text outline, and integration with Word/PowerPoint.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from enum import Enum
import json
from datetime import datetime
from io import BytesIO
import base64

if TYPE_CHECKING:
    from .nodes import MindMapNode
    from .branches import Branch


class ExportFormat(Enum):
    """Available export formats."""
    JSON = "json"
    PNG = "png"
    PDF = "pdf"
    SVG = "svg"
    TEXT_OUTLINE = "text_outline"
    MARKDOWN = "markdown"
    HTML = "html"
    DOCX = "docx"  # Word document
    PPTX = "pptx"  # PowerPoint
    OPML = "opml"  # Outline format
    FREEMIND = "freemind"  # FreeMind format
    XMIND = "xmind"  # XMind format


class ExportEngine:
    """
    Handles exporting mind maps to various formats.

    Features:
    - Multiple export formats
    - Customizable styling
    - Metadata preservation
    - Integration with NEXUS modules
    """

    def __init__(self):
        self.metadata: Dict[str, Any] = {
            "generator": "NEXUS Mind Map Module",
            "version": "1.0.0",
        }

    def export(
        self,
        nodes: Dict[str, MindMapNode],
        branches: Dict[str, Branch],
        root_id: str,
        format: ExportFormat,
        options: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """
        Export mind map to specified format.

        Args:
            nodes: Dictionary of all nodes
            branches: Dictionary of all branches
            root_id: ID of the root node
            format: Export format
            options: Format-specific options

        Returns:
            Exported data as bytes
        """
        options = options or {}

        exporters = {
            ExportFormat.JSON: self._export_json,
            ExportFormat.TEXT_OUTLINE: self._export_text_outline,
            ExportFormat.MARKDOWN: self._export_markdown,
            ExportFormat.HTML: self._export_html,
            ExportFormat.OPML: self._export_opml,
            ExportFormat.SVG: self._export_svg,
        }

        exporter = exporters.get(format)
        if not exporter:
            raise ValueError(f"Export format {format.value} not implemented")

        return exporter(nodes, branches, root_id, options)

    def _export_json(
        self,
        nodes: Dict[str, MindMapNode],
        branches: Dict[str, Branch],
        root_id: str,
        options: Dict[str, Any],
    ) -> bytes:
        """Export to JSON format."""
        data = {
            "metadata": {
                **self.metadata,
                "exported_at": datetime.now().isoformat(),
                "root_id": root_id,
                "node_count": len(nodes),
                "branch_count": len(branches),
            },
            "nodes": {node_id: node.to_dict() for node_id, node in nodes.items()},
            "branches": {
                branch_id: branch.to_dict() for branch_id, branch in branches.items()
            },
        }

        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        return json_str.encode("utf-8")

    def _export_text_outline(
        self,
        nodes: Dict[str, MindMapNode],
        branches: Dict[str, Branch],
        root_id: str,
        options: Dict[str, Any],
    ) -> bytes:
        """Export to plain text outline format."""
        lines = []
        include_notes = options.get("include_notes", False)
        include_tasks = options.get("include_tasks", False)

        def add_node(node_id: str, indent: int = 0):
            if node_id not in nodes:
                return

            node = nodes[node_id]
            prefix = "  " * indent + "- " if indent > 0 else ""

            # Add main text
            lines.append(f"{prefix}{node.text}")

            # Add notes if requested
            if include_notes and node.notes:
                note_prefix = "  " * (indent + 1) + "  Note: "
                lines.append(f"{note_prefix}{node.notes}")

            # Add tasks if requested
            if include_tasks and node.tasks:
                for task in node.tasks:
                    task_prefix = "  " * (indent + 1) + "  "
                    status = "✓" if task.completed else "☐"
                    lines.append(f"{task_prefix}{status} {task.description}")

            # Add children recursively
            for child_id in node.children_ids:
                add_node(child_id, indent + 1)

        add_node(root_id)
        return "\n".join(lines).encode("utf-8")

    def _export_markdown(
        self,
        nodes: Dict[str, MindMapNode],
        branches: Dict[str, Branch],
        root_id: str,
        options: Dict[str, Any],
    ) -> bytes:
        """Export to Markdown format."""
        lines = []
        root = nodes.get(root_id)

        if root:
            lines.append(f"# {root.text}\n")
            if root.notes:
                lines.append(f"{root.notes}\n")

        def add_node(node_id: str, level: int = 2):
            if node_id not in nodes or node_id == root_id:
                return

            node = nodes[node_id]
            heading = "#" * min(level, 6)

            # Add heading
            lines.append(f"{heading} {node.text}\n")

            # Add notes
            if node.notes:
                lines.append(f"{node.notes}\n")

            # Add links
            if node.links:
                lines.append("**Links:**\n")
                for link in node.links:
                    lines.append(f"- {link}\n")

            # Add tasks
            if node.tasks:
                lines.append("**Tasks:**\n")
                for task in node.tasks:
                    status = "x" if task.completed else " "
                    lines.append(f"- [{status}] {task.description}\n")

            # Add tags
            if node.tags:
                tags_str = " ".join(f"#{tag}" for tag in node.tags)
                lines.append(f"\n{tags_str}\n")

            lines.append("\n")

            # Add children
            for child_id in node.children_ids:
                add_node(child_id, level + 1)

        if root:
            for child_id in root.children_ids:
                add_node(child_id)

        return "".join(lines).encode("utf-8")

    def _export_html(
        self,
        nodes: Dict[str, MindMapNode],
        branches: Dict[str, Branch],
        root_id: str,
        options: Dict[str, Any],
    ) -> bytes:
        """Export to HTML format."""
        root = nodes.get(root_id)
        if not root:
            return b"<html><body>Empty mind map</body></html>"

        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            '    <meta charset="UTF-8">',
            f"    <title>{root.text}</title>",
            "    <style>",
            "        body { font-family: Arial, sans-serif; margin: 20px; }",
            "        .node { margin: 10px 0; padding: 10px; border-left: 3px solid #3498db; }",
            "        .root { font-size: 24px; font-weight: bold; border-left: 5px solid #e74c3c; }",
            "        .level-1 { margin-left: 20px; }",
            "        .level-2 { margin-left: 40px; }",
            "        .level-3 { margin-left: 60px; }",
            "        .notes { color: #666; font-style: italic; margin-top: 5px; }",
            "        .tasks { margin-top: 5px; }",
            "        .task { margin-left: 10px; }",
            "        .task.completed { text-decoration: line-through; color: #999; }",
            "        .tags { margin-top: 5px; }",
            "        .tag { display: inline-block; background: #ecf0f1; padding: 2px 8px; margin: 2px; border-radius: 3px; font-size: 12px; }",
            "    </style>",
            "</head>",
            "<body>",
        ]

        def add_node_html(node_id: str, level: int = 0):
            if node_id not in nodes:
                return

            node = nodes[node_id]
            level_class = f"level-{min(level, 3)}" if level > 0 else "root"

            html_parts.append(f'    <div class="node {level_class}">')
            html_parts.append(f"        <div>{node.text}</div>")

            if node.notes:
                html_parts.append(f'        <div class="notes">{node.notes}</div>')

            if node.tasks:
                html_parts.append('        <div class="tasks">')
                for task in node.tasks:
                    completed_class = "completed" if task.completed else ""
                    html_parts.append(
                        f'            <div class="task {completed_class}">{"✓" if task.completed else "☐"} {task.description}</div>'
                    )
                html_parts.append("        </div>")

            if node.tags:
                html_parts.append('        <div class="tags">')
                for tag in node.tags:
                    html_parts.append(f'            <span class="tag">#{tag}</span>')
                html_parts.append("        </div>")

            # Add children
            for child_id in node.children_ids:
                add_node_html(child_id, level + 1)

            html_parts.append("    </div>")

        add_node_html(root_id)
        html_parts.extend(["</body>", "</html>"])

        return "\n".join(html_parts).encode("utf-8")

    def _export_opml(
        self,
        nodes: Dict[str, MindMapNode],
        branches: Dict[str, Branch],
        root_id: str,
        options: Dict[str, Any],
    ) -> bytes:
        """Export to OPML (Outline) format."""
        root = nodes.get(root_id)
        if not root:
            return b"<opml version='2.0'></opml>"

        opml_parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<opml version="2.0">',
            "  <head>",
            f"    <title>{self._escape_xml(root.text)}</title>",
            f"    <dateCreated>{datetime.now().isoformat()}</dateCreated>",
            "  </head>",
            "  <body>",
        ]

        def add_outline(node_id: str, indent: int = 2):
            if node_id not in nodes:
                return

            node = nodes[node_id]
            spaces = "  " * indent

            attrs = [f'text="{self._escape_xml(node.text)}"']

            if node.notes:
                attrs.append(f'_note="{self._escape_xml(node.notes)}"')

            if node.children_ids:
                opml_parts.append(f"{spaces}<outline {' '.join(attrs)}>")
                for child_id in node.children_ids:
                    add_outline(child_id, indent + 1)
                opml_parts.append(f"{spaces}</outline>")
            else:
                opml_parts.append(f"{spaces}<outline {' '.join(attrs)} />")

        add_outline(root_id)
        opml_parts.extend(["  </body>", "</opml>"])

        return "\n".join(opml_parts).encode("utf-8")

    def _export_svg(
        self,
        nodes: Dict[str, MindMapNode],
        branches: Dict[str, Branch],
        root_id: str,
        options: Dict[str, Any],
    ) -> bytes:
        """Export to SVG format."""
        width = options.get("width", 1920)
        height = options.get("height", 1080)

        svg_parts = [
            f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
            '  <defs>',
            '    <style>',
            '      .node-rect { stroke: #333; stroke-width: 2; }',
            '      .node-text { font-family: Arial; font-size: 14px; fill: #000; }',
            '      .branch-line { stroke: #666; stroke-width: 2; fill: none; }',
            '    </style>',
            '  </defs>',
        ]

        # Draw branches first (so they appear behind nodes)
        for branch in branches.values():
            if branch.source_id in nodes and branch.target_id in nodes:
                source = nodes[branch.source_id]
                target = nodes[branch.target_id]

                svg_parts.append(
                    f'  <line class="branch-line" '
                    f'x1="{source.position.x}" y1="{source.position.y}" '
                    f'x2="{target.position.x}" y2="{target.position.y}" '
                    f'stroke="{branch.style.color}" />'
                )

        # Draw nodes
        for node in nodes.values():
            x, y = node.position.x, node.position.y
            text_length = len(node.text) * 8
            rect_width = max(text_length, 100)
            rect_height = 40

            # Draw rectangle
            svg_parts.append(
                f'  <rect x="{x - rect_width/2}" y="{y - rect_height/2}" '
                f'width="{rect_width}" height="{rect_height}" '
                f'fill="{node.style.background_color}" '
                f'class="node-rect" rx="5" />'
            )

            # Draw text
            svg_parts.append(
                f'  <text x="{x}" y="{y + 5}" '
                f'text-anchor="middle" class="node-text">'
                f'{self._escape_xml(node.text)}</text>'
            )

        svg_parts.append('</svg>')
        return "\n".join(svg_parts).encode("utf-8")

    def _escape_xml(self, text: str) -> str:
        """Escape special XML characters."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )

    def import_json(
        self, data: bytes
    ) -> tuple[Dict[str, MindMapNode], Dict[str, Branch], str]:
        """
        Import mind map from JSON format.

        Returns:
            Tuple of (nodes, branches, root_id)
        """
        from .nodes import MindMapNode
        from .branches import Branch

        json_data = json.loads(data.decode("utf-8"))

        # Import nodes
        nodes = {}
        for node_id, node_data in json_data["nodes"].items():
            nodes[node_id] = MindMapNode.from_dict(node_data)

        # Import branches
        branches = {}
        for branch_id, branch_data in json_data["branches"].items():
            branches[branch_id] = Branch.from_dict(branch_data)

        root_id = json_data["metadata"]["root_id"]

        return nodes, branches, root_id

    def export_for_presentation(
        self,
        nodes: Dict[str, MindMapNode],
        branches: Dict[str, Branch],
        root_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Export mind map as slides for presentation module integration.

        Returns:
            List of slide data dictionaries
        """
        slides = []

        # Title slide
        root = nodes.get(root_id)
        if root:
            slides.append(
                {
                    "type": "title",
                    "title": root.text,
                    "subtitle": root.notes if root.notes else "Mind Map Presentation",
                }
            )

        # Create slides for main branches
        if root:
            for child_id in root.children_ids:
                if child_id not in nodes:
                    continue

                child = nodes[child_id]
                slide_data = {
                    "type": "content",
                    "title": child.text,
                    "bullets": [],
                }

                # Add child notes as first bullet
                if child.notes:
                    slide_data["bullets"].append(child.notes)

                # Add sub-children as bullets
                for subchild_id in child.children_ids:
                    if subchild_id in nodes:
                        slide_data["bullets"].append(nodes[subchild_id].text)

                slides.append(slide_data)

        return slides

    def export_for_word(
        self,
        nodes: Dict[str, MindMapNode],
        branches: Dict[str, Branch],
        root_id: str,
    ) -> Dict[str, Any]:
        """
        Export mind map as structured document for Word module integration.

        Returns:
            Document structure dictionary
        """
        sections = []

        root = nodes.get(root_id)
        if root:
            sections.append(
                {
                    "type": "heading",
                    "level": 1,
                    "text": root.text,
                }
            )

            if root.notes:
                sections.append(
                    {
                        "type": "paragraph",
                        "text": root.notes,
                    }
                )

        def add_node_sections(node_id: str, level: int = 2):
            if node_id not in nodes or node_id == root_id:
                return

            node = nodes[node_id]

            # Add heading
            sections.append(
                {
                    "type": "heading",
                    "level": min(level, 6),
                    "text": node.text,
                }
            )

            # Add notes
            if node.notes:
                sections.append(
                    {
                        "type": "paragraph",
                        "text": node.notes,
                    }
                )

            # Add tasks as bulleted list
            if node.tasks:
                task_items = [
                    f"{'✓' if task.completed else '☐'} {task.description}"
                    for task in node.tasks
                ]
                sections.append(
                    {
                        "type": "bulleted_list",
                        "items": task_items,
                    }
                )

            # Process children
            for child_id in node.children_ids:
                add_node_sections(child_id, level + 1)

        if root:
            for child_id in root.children_ids:
                add_node_sections(child_id)

        return {
            "sections": sections,
            "metadata": {
                "title": root.text if root else "Mind Map",
                "created_at": datetime.now().isoformat(),
            },
        }
