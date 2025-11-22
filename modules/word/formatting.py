"""
Text Formatting Utilities

Provides comprehensive text formatting capabilities for the word processor.
"""

from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass


class TextAlign(Enum):
    """Text alignment options"""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


class ListType(Enum):
    """List type options"""
    BULLET = "bullet"
    ORDERED = "ordered"
    CHECKLIST = "checklist"


class HeadingLevel(Enum):
    """Heading level options"""
    H1 = 1
    H2 = 2
    H3 = 3
    H4 = 4
    H5 = 5
    H6 = 6


@dataclass
class FontStyle:
    """Font styling configuration"""
    family: str = "Arial"
    size: int = 12
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strikethrough: bool = False
    color: str = "#000000"
    background: str = "#FFFFFF"
    superscript: bool = False
    subscript: bool = False


@dataclass
class ParagraphStyle:
    """Paragraph styling configuration"""
    align: TextAlign = TextAlign.LEFT
    line_height: float = 1.5
    indent_first_line: int = 0
    indent_left: int = 0
    indent_right: int = 0
    spacing_before: int = 0
    spacing_after: int = 0


class TextFormatter:
    """
    Text formatting utility class.

    Provides methods for applying various text formatting operations
    including font styles, paragraph styles, lists, tables, and more.
    """

    # Available font families
    FONT_FAMILIES = [
        "Arial",
        "Times New Roman",
        "Courier New",
        "Georgia",
        "Verdana",
        "Helvetica",
        "Comic Sans MS",
        "Impact",
        "Trebuchet MS",
        "Palatino",
        "Garamond",
        "Bookman",
        "Tahoma",
        "Lucida Console",
    ]

    # Available font sizes (in points)
    FONT_SIZES = [8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 32, 36, 48, 72]

    # Common colors
    COLORS = {
        "black": "#000000",
        "white": "#FFFFFF",
        "red": "#FF0000",
        "green": "#00FF00",
        "blue": "#0000FF",
        "yellow": "#FFFF00",
        "orange": "#FFA500",
        "purple": "#800080",
        "pink": "#FFC0CB",
        "brown": "#A52A2A",
        "gray": "#808080",
        "light_gray": "#D3D3D3",
        "dark_gray": "#A9A9A9",
    }

    def __init__(self):
        """Initialize the text formatter"""
        self.current_font_style = FontStyle()
        self.current_paragraph_style = ParagraphStyle()

    @staticmethod
    def apply_bold(delta_ops: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply bold formatting to delta operations.

        Args:
            delta_ops: List of Quill Delta operations

        Returns:
            Modified delta operations with bold applied
        """
        for op in delta_ops:
            if "attributes" not in op:
                op["attributes"] = {}
            op["attributes"]["bold"] = True

        return delta_ops

    @staticmethod
    def apply_italic(delta_ops: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply italic formatting to delta operations.

        Args:
            delta_ops: List of Quill Delta operations

        Returns:
            Modified delta operations with italic applied
        """
        for op in delta_ops:
            if "attributes" not in op:
                op["attributes"] = {}
            op["attributes"]["italic"] = True

        return delta_ops

    @staticmethod
    def apply_underline(delta_ops: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply underline formatting to delta operations.

        Args:
            delta_ops: List of Quill Delta operations

        Returns:
            Modified delta operations with underline applied
        """
        for op in delta_ops:
            if "attributes" not in op:
                op["attributes"] = {}
            op["attributes"]["underline"] = True

        return delta_ops

    @staticmethod
    def apply_strikethrough(delta_ops: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply strikethrough formatting to delta operations.

        Args:
            delta_ops: List of Quill Delta operations

        Returns:
            Modified delta operations with strikethrough applied
        """
        for op in delta_ops:
            if "attributes" not in op:
                op["attributes"] = {}
            op["attributes"]["strike"] = True

        return delta_ops

    @staticmethod
    def apply_font_family(
        delta_ops: List[Dict[str, Any]],
        font_family: str
    ) -> List[Dict[str, Any]]:
        """
        Apply font family to delta operations.

        Args:
            delta_ops: List of Quill Delta operations
            font_family: Font family name

        Returns:
            Modified delta operations with font family applied
        """
        for op in delta_ops:
            if "attributes" not in op:
                op["attributes"] = {}
            op["attributes"]["font"] = font_family

        return delta_ops

    @staticmethod
    def apply_font_size(
        delta_ops: List[Dict[str, Any]],
        size: int
    ) -> List[Dict[str, Any]]:
        """
        Apply font size to delta operations.

        Args:
            delta_ops: List of Quill Delta operations
            size: Font size in points

        Returns:
            Modified delta operations with font size applied
        """
        for op in delta_ops:
            if "attributes" not in op:
                op["attributes"] = {}
            op["attributes"]["size"] = f"{size}pt"

        return delta_ops

    @staticmethod
    def apply_color(
        delta_ops: List[Dict[str, Any]],
        color: str
    ) -> List[Dict[str, Any]]:
        """
        Apply text color to delta operations.

        Args:
            delta_ops: List of Quill Delta operations
            color: Color in hex format (#RRGGBB)

        Returns:
            Modified delta operations with color applied
        """
        for op in delta_ops:
            if "attributes" not in op:
                op["attributes"] = {}
            op["attributes"]["color"] = color

        return delta_ops

    @staticmethod
    def apply_background_color(
        delta_ops: List[Dict[str, Any]],
        color: str
    ) -> List[Dict[str, Any]]:
        """
        Apply background color to delta operations.

        Args:
            delta_ops: List of Quill Delta operations
            color: Color in hex format (#RRGGBB)

        Returns:
            Modified delta operations with background color applied
        """
        for op in delta_ops:
            if "attributes" not in op:
                op["attributes"] = {}
            op["attributes"]["background"] = color

        return delta_ops

    @staticmethod
    def apply_heading(
        delta_ops: List[Dict[str, Any]],
        level: HeadingLevel
    ) -> List[Dict[str, Any]]:
        """
        Apply heading style to delta operations.

        Args:
            delta_ops: List of Quill Delta operations
            level: Heading level (H1-H6)

        Returns:
            Modified delta operations with heading applied
        """
        for op in delta_ops:
            if "attributes" not in op:
                op["attributes"] = {}
            op["attributes"]["header"] = level.value

        return delta_ops

    @staticmethod
    def apply_alignment(
        delta_ops: List[Dict[str, Any]],
        alignment: TextAlign
    ) -> List[Dict[str, Any]]:
        """
        Apply text alignment to delta operations.

        Args:
            delta_ops: List of Quill Delta operations
            alignment: Text alignment option

        Returns:
            Modified delta operations with alignment applied
        """
        for op in delta_ops:
            if "attributes" not in op:
                op["attributes"] = {}
            op["attributes"]["align"] = alignment.value

        return delta_ops

    @staticmethod
    def apply_list(
        delta_ops: List[Dict[str, Any]],
        list_type: ListType
    ) -> List[Dict[str, Any]]:
        """
        Apply list formatting to delta operations.

        Args:
            delta_ops: List of Quill Delta operations
            list_type: Type of list (bullet, ordered, checklist)

        Returns:
            Modified delta operations with list applied
        """
        for op in delta_ops:
            if "attributes" not in op:
                op["attributes"] = {}
            op["attributes"]["list"] = list_type.value

        return delta_ops

    @staticmethod
    def apply_indent(
        delta_ops: List[Dict[str, Any]],
        level: int
    ) -> List[Dict[str, Any]]:
        """
        Apply indentation to delta operations.

        Args:
            delta_ops: List of Quill Delta operations
            level: Indentation level (positive or negative)

        Returns:
            Modified delta operations with indentation applied
        """
        for op in delta_ops:
            if "attributes" not in op:
                op["attributes"] = {}
            op["attributes"]["indent"] = level

        return delta_ops

    @staticmethod
    def apply_superscript(delta_ops: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply superscript formatting to delta operations.

        Args:
            delta_ops: List of Quill Delta operations

        Returns:
            Modified delta operations with superscript applied
        """
        for op in delta_ops:
            if "attributes" not in op:
                op["attributes"] = {}
            op["attributes"]["script"] = "super"

        return delta_ops

    @staticmethod
    def apply_subscript(delta_ops: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply subscript formatting to delta operations.

        Args:
            delta_ops: List of Quill Delta operations

        Returns:
            Modified delta operations with subscript applied
        """
        for op in delta_ops:
            if "attributes" not in op:
                op["attributes"] = {}
            op["attributes"]["script"] = "sub"

        return delta_ops

    @staticmethod
    def create_link(text: str, url: str) -> Dict[str, Any]:
        """
        Create a hyperlink.

        Args:
            text: Link text
            url: Link URL

        Returns:
            Delta operation for a hyperlink
        """
        return {
            "insert": text,
            "attributes": {
                "link": url
            }
        }

    @staticmethod
    def create_blockquote(delta_ops: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create a blockquote.

        Args:
            delta_ops: List of Quill Delta operations

        Returns:
            Modified delta operations with blockquote applied
        """
        for op in delta_ops:
            if "attributes" not in op:
                op["attributes"] = {}
            op["attributes"]["blockquote"] = True

        return delta_ops

    @staticmethod
    def create_code_block(
        text: str,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a code block.

        Args:
            text: Code text
            language: Programming language for syntax highlighting

        Returns:
            Delta operation for a code block
        """
        attributes = {"code-block": True}
        if language:
            attributes["code-block"] = language

        return {
            "insert": text + "\n",
            "attributes": attributes
        }

    @staticmethod
    def create_horizontal_rule() -> Dict[str, Any]:
        """
        Create a horizontal rule.

        Returns:
            Delta operation for a horizontal rule
        """
        return {
            "insert": {"divider": True}
        }

    @staticmethod
    def create_image(
        url: str,
        alt_text: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create an image insertion.

        Args:
            url: Image URL or data URL
            alt_text: Alternative text for accessibility
            width: Image width in pixels
            height: Image height in pixels

        Returns:
            Delta operation for an image
        """
        image_data = {"image": url}

        attributes = {}
        if alt_text:
            attributes["alt"] = alt_text
        if width:
            attributes["width"] = width
        if height:
            attributes["height"] = height

        return {
            "insert": image_data,
            "attributes": attributes if attributes else None
        }

    @staticmethod
    def create_table(rows: int, columns: int) -> List[Dict[str, Any]]:
        """
        Create a table structure.

        Args:
            rows: Number of rows
            columns: Number of columns

        Returns:
            List of delta operations for a table
        """
        ops = []

        for row in range(rows):
            for col in range(columns):
                ops.append({
                    "insert": f"Cell {row + 1},{col + 1}",
                    "attributes": {
                        "table": f"table-{row}-{col}"
                    }
                })
            ops.append({"insert": "\n"})

        return ops

    @staticmethod
    def html_to_delta(html: str) -> Dict[str, Any]:
        """
        Convert HTML to Quill Delta format (simplified).

        Args:
            html: HTML string

        Returns:
            Quill Delta object
        """
        # This is a simplified version. In production, use a proper HTML parser
        # and quill-delta converter library

        import re

        ops = []

        # Remove HTML tags and extract text (very basic)
        text = re.sub('<[^<]+?>', '', html)

        ops.append({"insert": text})

        return {"ops": ops}

    @staticmethod
    def delta_to_html(delta: Dict[str, Any]) -> str:
        """
        Convert Quill Delta to HTML (simplified).

        Args:
            delta: Quill Delta object

        Returns:
            HTML string
        """
        # This is a simplified version. In production, use quill-delta-to-html

        html_parts = []

        for op in delta.get("ops", []):
            text = op.get("insert", "")
            if isinstance(text, str):
                attributes = op.get("attributes", {})

                # Apply formatting
                if attributes.get("bold"):
                    text = f"<strong>{text}</strong>"
                if attributes.get("italic"):
                    text = f"<em>{text}</em>"
                if attributes.get("underline"):
                    text = f"<u>{text}</u>"
                if attributes.get("strike"):
                    text = f"<s>{text}</s>"

                # Handle links
                if attributes.get("link"):
                    text = f'<a href="{attributes["link"]}">{text}</a>'

                # Handle headers
                if attributes.get("header"):
                    level = attributes["header"]
                    text = f"<h{level}>{text}</h{level}>"

                html_parts.append(text)

        return ''.join(html_parts)

    @staticmethod
    def delta_to_plain_text(delta: Dict[str, Any]) -> str:
        """
        Convert Quill Delta to plain text.

        Args:
            delta: Quill Delta object

        Returns:
            Plain text string
        """
        text_parts = []

        for op in delta.get("ops", []):
            if isinstance(op.get("insert"), str):
                text_parts.append(op["insert"])

        return ''.join(text_parts)

    @staticmethod
    def markdown_to_delta(markdown: str) -> Dict[str, Any]:
        """
        Convert Markdown to Quill Delta format (simplified).

        Args:
            markdown: Markdown string

        Returns:
            Quill Delta object
        """
        # This is a simplified version. In production, use a proper markdown parser

        ops = []

        lines = markdown.split('\n')
        for line in lines:
            # Handle headers
            if line.startswith('# '):
                ops.append({"insert": line[2:], "attributes": {"header": 1}})
            elif line.startswith('## '):
                ops.append({"insert": line[3:], "attributes": {"header": 2}})
            elif line.startswith('### '):
                ops.append({"insert": line[4:], "attributes": {"header": 3}})
            else:
                ops.append({"insert": line})

            ops.append({"insert": "\n"})

        return {"ops": ops}
