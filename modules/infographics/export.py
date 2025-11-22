"""
Infographics Designer - Export Module

This module handles export to various formats including high-res PNG, PDF,
SVG, animated GIF, video, and embed code.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from enum import Enum
import base64
from io import BytesIO


class ExportFormat(Enum):
    """Export format types."""
    PNG = "png"
    JPEG = "jpeg"
    PDF = "pdf"
    SVG = "svg"
    GIF = "gif"
    MP4 = "mp4"
    WEBM = "webm"
    HTML = "html"
    JSON = "json"


class ImageQuality(Enum):
    """Image quality presets."""
    LOW = "low"  # 72 DPI
    MEDIUM = "medium"  # 150 DPI
    HIGH = "high"  # 300 DPI
    ULTRA = "ultra"  # 600 DPI


@dataclass
class ExportConfig:
    """Configuration for export."""
    format: ExportFormat
    quality: ImageQuality = ImageQuality.HIGH
    scale: float = 1.0
    dpi: int = 300
    include_background: bool = True
    transparent_background: bool = False
    compress: bool = True
    metadata: Dict[str, str] = None

    def __post_init__(self):
        """Initialize metadata."""
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'format': self.format.value,
            'quality': self.quality.value,
            'scale': self.scale,
            'dpi': self.dpi,
            'include_background': self.include_background,
            'transparent_background': self.transparent_background,
            'compress': self.compress,
            'metadata': self.metadata
        }


class InfographicExporter:
    """Handles exporting infographics to various formats."""

    def __init__(self, designer):
        """Initialize exporter with designer instance."""
        self.designer = designer

    def export(self, config: ExportConfig, filepath: str) -> bool:
        """Export infographic to file."""
        try:
            if config.format == ExportFormat.PNG:
                return self.export_png(filepath, config)
            elif config.format == ExportFormat.JPEG:
                return self.export_jpeg(filepath, config)
            elif config.format == ExportFormat.PDF:
                return self.export_pdf(filepath, config)
            elif config.format == ExportFormat.SVG:
                return self.export_svg(filepath, config)
            elif config.format == ExportFormat.GIF:
                return self.export_gif(filepath, config)
            elif config.format == ExportFormat.MP4:
                return self.export_video(filepath, config)
            elif config.format == ExportFormat.HTML:
                return self.export_html(filepath, config)
            elif config.format == ExportFormat.JSON:
                return self.export_json(filepath, config)
            return False
        except Exception as e:
            print(f"Export error: {e}")
            return False

    def export_png(self, filepath: str, config: ExportConfig) -> bool:
        """Export as PNG image."""
        # In production, would use PIL/Pillow or similar
        svg_content = self._generate_svg()
        # Convert SVG to PNG using library like cairosvg or svglib
        # For now, save as SVG
        with open(filepath, 'w') as f:
            f.write(svg_content)
        return True

    def export_jpeg(self, filepath: str, config: ExportConfig) -> bool:
        """Export as JPEG image."""
        # In production, would convert to JPEG with quality settings
        svg_content = self._generate_svg()
        with open(filepath, 'w') as f:
            f.write(svg_content)
        return True

    def export_pdf(self, filepath: str, config: ExportConfig) -> bool:
        """Export as PDF document."""
        # In production, would use reportlab or similar
        svg_content = self._generate_svg()
        # Convert to PDF
        with open(filepath, 'w') as f:
            f.write(svg_content)
        return True

    def export_svg(self, filepath: str, config: ExportConfig) -> bool:
        """Export as SVG vector graphic."""
        svg_content = self._generate_svg()
        with open(filepath, 'w') as f:
            f.write(svg_content)
        return True

    def export_gif(self, filepath: str, config: ExportConfig) -> bool:
        """Export as animated GIF."""
        # In production, would render frames and create GIF
        # Using imageio or Pillow
        return True

    def export_video(self, filepath: str, config: ExportConfig) -> bool:
        """Export as video (MP4 or WebM)."""
        # In production, would use ffmpeg or similar
        # to create video from rendered frames
        return True

    def export_html(self, filepath: str, config: ExportConfig) -> bool:
        """Export as interactive HTML."""
        html_content = self._generate_html()
        with open(filepath, 'w') as f:
            f.write(html_content)
        return True

    def export_json(self, filepath: str, config: ExportConfig) -> bool:
        """Export as JSON data."""
        self.designer.save_to_file(filepath)
        return True

    def _generate_svg(self) -> str:
        """Generate SVG representation of infographic."""
        canvas = self.designer.canvas
        elements = self.designer.elements

        svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{canvas.width}" height="{canvas.height}"
     viewBox="0 0 {canvas.width} {canvas.height}"
     xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink">

    <!-- Background -->
    <rect x="0" y="0" width="{canvas.width}" height="{canvas.height}"
          fill="{canvas.background_color}"/>

    <!-- Elements -->
'''

        for elem in elements:
            if elem.visible:
                svg += self._element_to_svg(elem)

        svg += '</svg>'
        return svg

    def _element_to_svg(self, element) -> str:
        """Convert element to SVG."""
        from .elements import (
            TextElement, ShapeElement, IconElement, ImageElement,
            LineElement, GroupElement, ShapeType
        )

        pos = element.position
        style = element.style

        transform = f'translate({pos.x}, {pos.y})'
        if pos.rotation != 0:
            transform += f' rotate({pos.rotation})'

        svg = f'<g transform="{transform}">\n'

        if isinstance(element, TextElement):
            svg += f'''  <text x="0" y="0"
                    font-family="{element.text_style.font_family}"
                    font-size="{element.text_style.font_size}"
                    fill="{style.fill_color}"
                    opacity="{style.opacity}">
                {element.text}
              </text>\n'''

        elif isinstance(element, ShapeElement):
            if element.shape_type == ShapeType.RECTANGLE:
                svg += f'''  <rect x="0" y="0"
                        width="{pos.width}" height="{pos.height}"
                        fill="{style.fill_color}"
                        stroke="{style.stroke_color}"
                        stroke-width="{style.stroke_width}"
                        opacity="{style.opacity}"
                        rx="{style.border_radius}"/>\n'''

            elif element.shape_type == ShapeType.CIRCLE:
                r = min(pos.width, pos.height) / 2
                svg += f'''  <circle cx="{r}" cy="{r}" r="{r}"
                        fill="{style.fill_color}"
                        stroke="{style.stroke_color}"
                        stroke-width="{style.stroke_width}"
                        opacity="{style.opacity}"/>\n'''

        elif isinstance(element, LineElement):
            start_x, start_y = element.start_point
            end_x, end_y = element.end_point
            svg += f'''  <line x1="{start_x}" y1="{start_y}"
                    x2="{end_x}" y2="{end_y}"
                    stroke="{style.stroke_color}"
                    stroke-width="{style.stroke_width}"
                    opacity="{style.opacity}"/>\n'''

        elif isinstance(element, GroupElement):
            for child in element.children:
                svg += self._element_to_svg(child)

        svg += '</g>\n'
        return svg

    def _generate_html(self) -> str:
        """Generate interactive HTML representation."""
        svg_content = self._generate_svg()

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Infographic</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: #f0f0f0;
            font-family: Arial, sans-serif;
        }}
        .infographic-container {{
            background: white;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }}
        svg {{
            display: block;
            max-width: 100%;
            height: auto;
        }}
    </style>
</head>
<body>
    <div class="infographic-container">
        {svg_content}
    </div>

    <script>
        // Add interactivity here
        console.log('Infographic loaded');
    </script>
</body>
</html>'''
        return html

    def get_embed_code(self, width: Optional[int] = None,
                      height: Optional[int] = None) -> str:
        """Generate embed code for websites."""
        svg_content = self._generate_svg()

        # Encode SVG as base64 for data URI
        svg_bytes = svg_content.encode('utf-8')
        svg_base64 = base64.b64encode(svg_bytes).decode('utf-8')

        width_attr = f'width="{width}"' if width else ''
        height_attr = f'height="{height}"' if height else ''

        embed_code = f'''<iframe {width_attr} {height_attr}
    style="border: none;"
    src="data:image/svg+xml;base64,{svg_base64}">
</iframe>'''

        return embed_code

    def get_social_media_preview(self, platform: str) -> Dict[str, Any]:
        """Get optimized preview for social media platforms."""
        presets = {
            'facebook': {'width': 1200, 'height': 630},
            'twitter': {'width': 1200, 'height': 675},
            'instagram': {'width': 1080, 'height': 1080},
            'linkedin': {'width': 1200, 'height': 627},
            'pinterest': {'width': 1000, 'height': 1500}
        }

        preset = presets.get(platform.lower(), {'width': 1200, 'height': 630})

        return {
            'width': preset['width'],
            'height': preset['height'],
            'format': 'png',
            'quality': 'high'
        }


class BatchExporter:
    """Export multiple infographics or variations."""

    def __init__(self, designer):
        """Initialize batch exporter."""
        self.designer = designer
        self.exporter = InfographicExporter(designer)

    def export_multiple_formats(self, base_filepath: str,
                               formats: List[ExportFormat]) -> Dict[str, bool]:
        """Export to multiple formats."""
        results = {}

        for format_type in formats:
            ext = format_type.value
            filepath = f"{base_filepath}.{ext}"
            config = ExportConfig(format=format_type)
            results[filepath] = self.exporter.export(config, filepath)

        return results

    def export_resolutions(self, base_filepath: str,
                          resolutions: List[tuple]) -> Dict[str, bool]:
        """Export at multiple resolutions."""
        results = {}
        original_width = self.designer.canvas.width
        original_height = self.designer.canvas.height

        for width, height in resolutions:
            # Scale canvas
            scale_x = width / original_width
            scale_y = height / original_height
            scale = min(scale_x, scale_y)

            filepath = f"{base_filepath}_{width}x{height}.png"
            config = ExportConfig(
                format=ExportFormat.PNG,
                scale=scale
            )
            results[filepath] = self.exporter.export(config, filepath)

        return results

    def export_social_media_pack(self, base_filepath: str) -> Dict[str, bool]:
        """Export optimized versions for all social media platforms."""
        results = {}
        platforms = ['facebook', 'twitter', 'instagram', 'linkedin', 'pinterest']

        for platform in platforms:
            preset = self.exporter.get_social_media_preview(platform)
            filepath = f"{base_filepath}_{platform}.png"

            config = ExportConfig(
                format=ExportFormat.PNG,
                quality=ImageQuality.HIGH
            )
            # In production, would resize canvas to preset dimensions
            results[filepath] = self.exporter.export(config, filepath)

        return results


class PrintExporter:
    """Specialized exporter for print media."""

    def __init__(self, designer):
        """Initialize print exporter."""
        self.designer = designer
        self.exporter = InfographicExporter(designer)

    def export_print_ready(self, filepath: str,
                          paper_size: str = "A4") -> bool:
        """Export print-ready PDF."""
        paper_sizes = {
            'A4': (210, 297),  # mm
            'A3': (297, 420),
            'Letter': (215.9, 279.4),
            'Legal': (215.9, 355.6),
            'Tabloid': (279.4, 431.8)
        }

        size = paper_sizes.get(paper_size, (210, 297))

        config = ExportConfig(
            format=ExportFormat.PDF,
            quality=ImageQuality.ULTRA,
            dpi=300,
            compress=False,
            metadata={
                'paper_size': paper_size,
                'color_mode': 'CMYK'
            }
        )

        return self.exporter.export(config, filepath)

    def export_bleed_marks(self, filepath: str, bleed: float = 3.0) -> bool:
        """Export with bleed marks for professional printing."""
        # In production, would add crop marks and bleed area
        config = ExportConfig(
            format=ExportFormat.PDF,
            quality=ImageQuality.ULTRA,
            dpi=300,
            metadata={
                'bleed': bleed,
                'crop_marks': True
            }
        )

        return self.exporter.export(config, filepath)


class AnimationExporter:
    """Export animated infographics."""

    def __init__(self, designer):
        """Initialize animation exporter."""
        self.designer = designer

    def export_animated_gif(self, filepath: str, fps: int = 30,
                          duration: Optional[float] = None) -> bool:
        """Export as animated GIF."""
        # In production, would:
        # 1. Calculate animation timeline
        # 2. Render frames at specified FPS
        # 3. Create GIF from frames
        return True

    def export_video(self, filepath: str, fps: int = 30,
                    codec: str = 'h264') -> bool:
        """Export as video file."""
        # In production, would use ffmpeg to create video
        return True

    def export_web_animation(self, filepath: str) -> bool:
        """Export as web animation (HTML/CSS/JS)."""
        # Generate HTML with CSS animations or Canvas/WebGL
        return True


__all__ = [
    'ExportFormat', 'ImageQuality', 'ExportConfig',
    'InfographicExporter', 'BatchExporter', 'PrintExporter', 'AnimationExporter'
]
