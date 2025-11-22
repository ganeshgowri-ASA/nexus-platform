"""
Export functionality for diagrams to multiple formats.
Supports PNG, JPG, SVG, PDF, Visio, and embed code generation.
"""

from typing import Optional, Dict, Any
import base64
from io import BytesIO
import json

from .diagram_engine import DiagramEngine
from .shapes import Shape
from .connectors import Connector


class SVGExporter:
    """Export diagrams to SVG format."""

    @staticmethod
    def export(engine: DiagramEngine, include_metadata: bool = True) -> str:
        """Export diagram to SVG string."""
        # Calculate bounds
        min_point, max_point = engine.get_bounds()

        # Add padding
        padding = 20
        width = max_point.x - min_point.x + 2 * padding
        height = max_point.y - min_point.y + 2 * padding
        view_x = min_point.x - padding
        view_y = min_point.y - padding

        # Start SVG
        svg_parts = [
            f'<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{width}" height="{height}" '
            f'viewBox="{view_x} {view_y} {width} {height}">'
        ]

        # Add metadata as comment if requested
        if include_metadata:
            svg_parts.append(f'<!-- {engine.metadata.title} -->')
            svg_parts.append(f'<!-- Created: {engine.metadata.created_at} -->')

        # Add background
        if engine.settings.background_color != "transparent":
            svg_parts.append(
                f'<rect x="{view_x}" y="{view_y}" '
                f'width="{width}" height="{height}" '
                f'fill="{engine.settings.background_color}" />'
            )

        # Group by layers
        for layer_id in sorted(engine.layers.keys()):
            layer = engine.layers[layer_id]

            if not layer.visible:
                continue

            svg_parts.append(f'<g id="layer_{layer_id}" opacity="{layer.opacity}">')

            # Add shapes in this layer
            for shape in engine.shapes.values():
                if shape.layer == layer_id:
                    svg_parts.append(SVGExporter._shape_to_svg(shape))

            # Add connectors in this layer
            for connector in engine.connectors.values():
                if connector.layer == layer_id:
                    svg_parts.append(connector.to_svg(engine.shapes))

            svg_parts.append('</g>')

        svg_parts.append('</svg>')

        return '\n'.join(svg_parts)

    @staticmethod
    def _shape_to_svg(shape: Shape) -> str:
        """Convert a single shape to SVG."""
        parts = []

        # Group for transform
        transform = ""
        if shape.rotation != 0:
            cx = shape.position.x + shape.width / 2
            cy = shape.position.y + shape.height / 2
            transform = f'transform="rotate({shape.rotation} {cx} {cy})"'

        parts.append(f'<g id="{shape.id}" {transform}>')

        # Add shadow if enabled
        if shape.style.shadow:
            shadow_shape = shape.to_svg()
            shadow_style = (
                f'fill="{shape.style.shadow_color}"; '
                f'stroke="none"; '
                f'transform: translate({shape.style.shadow_offset_x}px, '
                f'{shape.style.shadow_offset_y}px)'
            )
            parts.append(f'<g style="{shadow_style}">{shadow_shape}</g>')

        # Add main shape
        parts.append(shape.to_svg())

        # Add text if present
        if shape.text:
            text_x = shape.position.x + shape.width / 2
            text_y = shape.position.y + shape.height / 2

            # Split multiline text
            lines = shape.text.split('\n')
            line_height = shape.style.font_size * 1.2

            for i, line in enumerate(lines):
                y_offset = (i - len(lines) / 2 + 0.5) * line_height

                parts.append(
                    f'<text x="{text_x}" y="{text_y + y_offset}" '
                    f'font-family="{shape.style.font_family}" '
                    f'font-size="{shape.style.font_size}" '
                    f'font-weight="{shape.style.font_weight}" '
                    f'font-style="{shape.style.font_style}" '
                    f'fill="{shape.style.font_color}" '
                    f'text-anchor="{shape.style.text_align}" '
                    f'dominant-baseline="middle">'
                    f'{line}'
                    f'</text>'
                )

        parts.append('</g>')

        return '\n'.join(parts)

    @staticmethod
    def save_to_file(engine: DiagramEngine, filepath: str):
        """Save diagram to SVG file."""
        svg_content = SVGExporter.export(engine)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(svg_content)


class PNGExporter:
    """Export diagrams to PNG format (requires external rendering)."""

    @staticmethod
    def export(
        engine: DiagramEngine,
        scale: float = 2.0,
        background: Optional[str] = None
    ) -> bytes:
        """
        Export diagram to PNG bytes.

        Note: This requires an SVG-to-PNG conversion library like cairosvg.
        For production use, integrate with a rendering service.
        """
        svg_content = SVGExporter.export(engine)

        try:
            import cairosvg
            png_bytes = cairosvg.svg2png(
                bytestring=svg_content.encode('utf-8'),
                scale=scale
            )
            return png_bytes
        except ImportError:
            # Fallback: return SVG as data URL
            return svg_content.encode('utf-8')

    @staticmethod
    def save_to_file(
        engine: DiagramEngine,
        filepath: str,
        scale: float = 2.0
    ):
        """Save diagram to PNG file."""
        png_bytes = PNGExporter.export(engine, scale)
        with open(filepath, 'wb') as f:
            f.write(png_bytes)


class PDFExporter:
    """Export diagrams to PDF format."""

    @staticmethod
    def export(engine: DiagramEngine) -> bytes:
        """
        Export diagram to PDF bytes.

        Note: Requires a PDF generation library like reportlab or weasyprint.
        """
        svg_content = SVGExporter.export(engine)

        try:
            from weasyprint import HTML, CSS
            from io import BytesIO

            # Wrap SVG in HTML
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ margin: 0; padding: 20px; }}
                    svg {{ max-width: 100%; height: auto; }}
                </style>
            </head>
            <body>
                {svg_content}
            </body>
            </html>
            """

            pdf_bytes = HTML(string=html_content).write_pdf()
            return pdf_bytes

        except ImportError:
            # Fallback: return SVG
            return svg_content.encode('utf-8')

    @staticmethod
    def save_to_file(engine: DiagramEngine, filepath: str):
        """Save diagram to PDF file."""
        pdf_bytes = PDFExporter.export(engine)
        with open(filepath, 'wb') as f:
            f.write(pdf_bytes)


class VisioExporter:
    """Export diagrams to Visio-compatible format (VSDX)."""

    @staticmethod
    def export(engine: DiagramEngine) -> bytes:
        """
        Export diagram to VSDX format.

        Note: This is a simplified implementation. For full Visio compatibility,
        use a library like vsdx or implement full VSDX spec.
        """
        # For now, export as XML representation
        # In production, implement proper VSDX package creation

        visio_xml = VisioExporter._to_visio_xml(engine)
        return visio_xml.encode('utf-8')

    @staticmethod
    def _to_visio_xml(engine: DiagramEngine) -> str:
        """Convert diagram to Visio XML format."""
        xml_parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<VisioDocument xmlns="http://schemas.microsoft.com/visio/2003/core">',
            '<DocumentProperties>',
            f'<Title>{engine.metadata.title}</Title>',
            f'<Creator>{engine.metadata.author}</Creator>',
            '</DocumentProperties>',
            '<Pages>',
            '<Page ID="0" Name="Page-1">',
            '<Shapes>'
        ]

        # Add shapes
        for idx, shape in enumerate(engine.shapes.values()):
            xml_parts.append(
                f'<Shape ID="{idx}" Type="{shape.shape_type}" '
                f'X="{shape.position.x}" Y="{shape.position.y}" '
                f'Width="{shape.width}" Height="{shape.height}" '
                f'Text="{shape.text}" />'
            )

        xml_parts.extend([
            '</Shapes>',
            '<Connects>'
        ])

        # Add connectors
        for idx, connector in enumerate(engine.connectors.values()):
            if connector.source_shape_id and connector.target_shape_id:
                xml_parts.append(
                    f'<Connect FromSheet="{connector.source_shape_id}" '
                    f'ToSheet="{connector.target_shape_id}" />'
                )

        xml_parts.extend([
            '</Connects>',
            '</Page>',
            '</Pages>',
            '</VisioDocument>'
        ])

        return '\n'.join(xml_parts)

    @staticmethod
    def save_to_file(engine: DiagramEngine, filepath: str):
        """Save diagram to Visio file."""
        visio_bytes = VisioExporter.export(engine)
        with open(filepath, 'wb') as f:
            f.write(visio_bytes)


class EmbedCodeGenerator:
    """Generate embed code for diagrams."""

    @staticmethod
    def generate_html_embed(
        engine: DiagramEngine,
        width: Optional[int] = None,
        height: Optional[int] = None,
        responsive: bool = True
    ) -> str:
        """Generate HTML embed code."""
        svg_content = SVGExporter.export(engine, include_metadata=False)

        # Encode SVG as base64 data URL
        svg_base64 = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
        data_url = f"data:image/svg+xml;base64,{svg_base64}"

        if responsive:
            html = f"""
<div style="max-width: 100%; overflow: auto;">
    <img src="{data_url}" alt="{engine.metadata.title}" style="width: 100%; height: auto;" />
</div>
"""
        else:
            width_attr = f'width="{width}"' if width else ''
            height_attr = f'height="{height}"' if height else ''
            html = f"""
<img src="{data_url}" alt="{engine.metadata.title}" {width_attr} {height_attr} />
"""

        return html.strip()

    @staticmethod
    def generate_iframe_embed(
        engine: DiagramEngine,
        width: int = 800,
        height: int = 600
    ) -> str:
        """Generate iframe embed code."""
        svg_content = SVGExporter.export(engine)

        # Create full HTML page
        html_page = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{engine.metadata.title}</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: {engine.settings.background_color};
        }}
        svg {{
            max-width: 100%;
            height: auto;
        }}
    </style>
</head>
<body>
    {svg_content}
</body>
</html>
"""

        # Encode as data URL
        html_base64 = base64.b64encode(html_page.encode('utf-8')).decode('utf-8')
        data_url = f"data:text/html;base64,{html_base64}"

        iframe = f'<iframe src="{data_url}" width="{width}" height="{height}" frameborder="0"></iframe>'

        return iframe

    @staticmethod
    def generate_markdown_embed(engine: DiagramEngine) -> str:
        """Generate Markdown embed code."""
        svg_content = SVGExporter.export(engine, include_metadata=False)
        svg_base64 = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
        data_url = f"data:image/svg+xml;base64,{svg_base64}"

        return f"![{engine.metadata.title}]({data_url})"


class DiagramExporter:
    """Main exporter class with all export formats."""

    @staticmethod
    def export(
        engine: DiagramEngine,
        format: str,
        filepath: Optional[str] = None,
        **kwargs
    ) -> Optional[bytes]:
        """
        Export diagram to specified format.

        Args:
            engine: DiagramEngine to export
            format: Export format ('svg', 'png', 'jpg', 'pdf', 'visio', 'json')
            filepath: Optional file path to save to
            **kwargs: Additional format-specific options

        Returns:
            Bytes of exported content if filepath is None, otherwise None
        """
        format = format.lower()

        if format == 'svg':
            content = SVGExporter.export(engine).encode('utf-8')
            if filepath:
                SVGExporter.save_to_file(engine, filepath)
                return None
            return content

        elif format == 'png':
            content = PNGExporter.export(engine, **kwargs)
            if filepath:
                PNGExporter.save_to_file(engine, filepath, **kwargs)
                return None
            return content

        elif format == 'jpg' or format == 'jpeg':
            # Convert PNG to JPG
            png_bytes = PNGExporter.export(engine, **kwargs)
            # For production, convert PNG to JPG using PIL/Pillow
            if filepath:
                with open(filepath, 'wb') as f:
                    f.write(png_bytes)
                return None
            return png_bytes

        elif format == 'pdf':
            content = PDFExporter.export(engine)
            if filepath:
                PDFExporter.save_to_file(engine, filepath)
                return None
            return content

        elif format == 'visio' or format == 'vsdx':
            content = VisioExporter.export(engine)
            if filepath:
                VisioExporter.save_to_file(engine, filepath)
                return None
            return content

        elif format == 'json':
            content = engine.to_json().encode('utf-8')
            if filepath:
                engine.save_to_file(filepath)
                return None
            return content

        else:
            raise ValueError(f"Unsupported export format: {format}")

    @staticmethod
    def get_embed_code(
        engine: DiagramEngine,
        embed_type: str = 'html',
        **kwargs
    ) -> str:
        """
        Generate embed code for diagram.

        Args:
            engine: DiagramEngine to embed
            embed_type: Type of embed ('html', 'iframe', 'markdown')
            **kwargs: Additional options

        Returns:
            Embed code string
        """
        if embed_type == 'html':
            return EmbedCodeGenerator.generate_html_embed(engine, **kwargs)
        elif embed_type == 'iframe':
            return EmbedCodeGenerator.generate_iframe_embed(engine, **kwargs)
        elif embed_type == 'markdown':
            return EmbedCodeGenerator.generate_markdown_embed(engine)
        else:
            raise ValueError(f"Unsupported embed type: {embed_type}")
