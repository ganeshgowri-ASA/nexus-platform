"""
Mind Map Themes and Color Schemes

This module provides pre-designed themes, color palettes, and styling
templates for professional mind maps.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import colorsys


class ThemeName(Enum):
    """Available predefined themes."""
    CLASSIC = "classic"
    PROFESSIONAL = "professional"
    CREATIVE = "creative"
    MINIMAL = "minimal"
    DARK = "dark"
    OCEANIC = "oceanic"
    FOREST = "forest"
    SUNSET = "sunset"
    PASTEL = "pastel"
    VIBRANT = "vibrant"
    CORPORATE = "corporate"
    ACADEMIC = "academic"


@dataclass
class ColorPalette:
    """Color palette for a theme."""
    primary: str
    secondary: str
    accent: str
    background: str
    text: str
    border: str
    levels: List[str]  # Colors for different hierarchy levels

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "primary": self.primary,
            "secondary": self.secondary,
            "accent": self.accent,
            "background": self.background,
            "text": self.text,
            "border": self.border,
            "levels": self.levels,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ColorPalette:
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Theme:
    """Complete theme including colors, fonts, and styling."""
    name: str
    description: str
    palette: ColorPalette
    font_family: str = "Arial"
    root_font_size: int = 20
    child_font_size: int = 14
    border_width: int = 2
    shadow: bool = True
    rounded_corners: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "palette": self.palette.to_dict(),
            "font_family": self.font_family,
            "root_font_size": self.root_font_size,
            "child_font_size": self.child_font_size,
            "border_width": self.border_width,
            "shadow": self.shadow,
            "rounded_corners": self.rounded_corners,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Theme:
        """Create from dictionary."""
        data_copy = data.copy()
        data_copy["palette"] = ColorPalette.from_dict(data_copy["palette"])
        return cls(**data_copy)


class ThemeManager:
    """
    Manages themes and provides theme application functionality.

    Features:
    - Predefined professional themes
    - Custom theme creation
    - Color palette generation
    - Theme import/export
    """

    def __init__(self):
        self.themes: Dict[str, Theme] = self._load_default_themes()
        self.custom_themes: Dict[str, Theme] = {}

    def _load_default_themes(self) -> Dict[str, Theme]:
        """Load all default themes."""
        return {
            ThemeName.CLASSIC.value: self._create_classic_theme(),
            ThemeName.PROFESSIONAL.value: self._create_professional_theme(),
            ThemeName.CREATIVE.value: self._create_creative_theme(),
            ThemeName.MINIMAL.value: self._create_minimal_theme(),
            ThemeName.DARK.value: self._create_dark_theme(),
            ThemeName.OCEANIC.value: self._create_oceanic_theme(),
            ThemeName.FOREST.value: self._create_forest_theme(),
            ThemeName.SUNSET.value: self._create_sunset_theme(),
            ThemeName.PASTEL.value: self._create_pastel_theme(),
            ThemeName.VIBRANT.value: self._create_vibrant_theme(),
            ThemeName.CORPORATE.value: self._create_corporate_theme(),
            ThemeName.ACADEMIC.value: self._create_academic_theme(),
        }

    def _create_classic_theme(self) -> Theme:
        """Classic mind map theme."""
        return Theme(
            name="Classic",
            description="Traditional mind map with warm colors",
            palette=ColorPalette(
                primary="#FFD700",
                secondary="#87CEEB",
                accent="#FF6B6B",
                background="#FFFFFF",
                text="#000000",
                border="#333333",
                levels=["#FFD700", "#87CEEB", "#98FB98", "#FFB6C1", "#DDA0DD", "#F0E68C"],
            ),
            font_family="Arial",
        )

    def _create_professional_theme(self) -> Theme:
        """Professional business theme."""
        return Theme(
            name="Professional",
            description="Clean professional look for business",
            palette=ColorPalette(
                primary="#2C3E50",
                secondary="#34495E",
                accent="#3498DB",
                background="#ECF0F1",
                text="#2C3E50",
                border="#7F8C8D",
                levels=["#3498DB", "#1ABC9C", "#9B59B6", "#E74C3C", "#F39C12", "#16A085"],
            ),
            font_family="Helvetica",
            border_width=2,
        )

    def _create_creative_theme(self) -> Theme:
        """Creative theme with vibrant colors."""
        return Theme(
            name="Creative",
            description="Vibrant colors for creative brainstorming",
            palette=ColorPalette(
                primary="#FF3366",
                secondary="#33CCFF",
                accent="#FFCC33",
                background="#FFFFFF",
                text="#2C2C2C",
                border="#FF3366",
                levels=["#FF3366", "#33CCFF", "#FFCC33", "#9933FF", "#33FF99", "#FF9933"],
            ),
            font_family="Comic Sans MS",
            shadow=True,
            rounded_corners=True,
        )

    def _create_minimal_theme(self) -> Theme:
        """Minimalist theme."""
        return Theme(
            name="Minimal",
            description="Clean and simple minimalist design",
            palette=ColorPalette(
                primary="#FFFFFF",
                secondary="#F5F5F5",
                accent="#000000",
                background="#FFFFFF",
                text="#000000",
                border="#E0E0E0",
                levels=["#FFFFFF", "#F8F8F8", "#F0F0F0", "#E8E8E8", "#E0E0E0", "#D8D8D8"],
            ),
            font_family="Helvetica Neue",
            border_width=1,
            shadow=False,
        )

    def _create_dark_theme(self) -> Theme:
        """Dark mode theme."""
        return Theme(
            name="Dark",
            description="Easy on the eyes dark theme",
            palette=ColorPalette(
                primary="#1E1E1E",
                secondary="#2D2D2D",
                accent="#BB86FC",
                background="#121212",
                text="#E1E1E1",
                border="#3D3D3D",
                levels=["#BB86FC", "#03DAC6", "#CF6679", "#3700B3", "#018786", "#6200EE"],
            ),
            font_family="Segoe UI",
            shadow=True,
        )

    def _create_oceanic_theme(self) -> Theme:
        """Ocean-inspired theme."""
        return Theme(
            name="Oceanic",
            description="Calming ocean-inspired colors",
            palette=ColorPalette(
                primary="#006994",
                secondary="#0099CC",
                accent="#66D9EF",
                background="#F0F8FF",
                text="#003D5C",
                border="#005C7A",
                levels=["#006994", "#0099CC", "#66D9EF", "#33BBEE", "#008EAD", "#00749C"],
            ),
            font_family="Georgia",
        )

    def _create_forest_theme(self) -> Theme:
        """Forest-inspired theme."""
        return Theme(
            name="Forest",
            description="Natural forest colors",
            palette=ColorPalette(
                primary="#2D5016",
                secondary="#4E7C31",
                accent="#8BC34A",
                background="#F1F8E9",
                text="#1B3409",
                border="#3D6021",
                levels=["#2D5016", "#4E7C31", "#689F38", "#8BC34A", "#9CCC65", "#AED581"],
            ),
            font_family="Georgia",
        )

    def _create_sunset_theme(self) -> Theme:
        """Sunset-inspired theme."""
        return Theme(
            name="Sunset",
            description="Warm sunset gradient colors",
            palette=ColorPalette(
                primary="#FF6B35",
                secondary="#F7931E",
                accent="#FDC830",
                background="#FFF8F0",
                text="#4A2C2A",
                border="#D45113",
                levels=["#FF6B35", "#F7931E", "#FDC830", "#F37735", "#EF5B2B", "#E84A3F"],
            ),
            font_family="Trebuchet MS",
        )

    def _create_pastel_theme(self) -> Theme:
        """Soft pastel theme."""
        return Theme(
            name="Pastel",
            description="Soft pastel colors",
            palette=ColorPalette(
                primary="#FFB3BA",
                secondary="#BAFFC9",
                accent="#BAE1FF",
                background="#FFFFFF",
                text="#4A4A4A",
                border="#CCCCCC",
                levels=["#FFB3BA", "#FFDFBA", "#FFFFBA", "#BAFFC9", "#BAE1FF", "#E0BBE4"],
            ),
            font_family="Verdana",
            shadow=False,
        )

    def _create_vibrant_theme(self) -> Theme:
        """High-energy vibrant theme."""
        return Theme(
            name="Vibrant",
            description="High-energy vibrant colors",
            palette=ColorPalette(
                primary="#FF0080",
                secondary="#7B00FF",
                accent="#00D9FF",
                background="#FFFFFF",
                text="#1A1A1A",
                border="#FF0080",
                levels=["#FF0080", "#7B00FF", "#00D9FF", "#00FF9F", "#FFD600", "#FF4D00"],
            ),
            font_family="Impact",
            border_width=3,
        )

    def _create_corporate_theme(self) -> Theme:
        """Corporate business theme."""
        return Theme(
            name="Corporate",
            description="Professional corporate theme",
            palette=ColorPalette(
                primary="#003366",
                secondary="#0055A4",
                accent="#0077CC",
                background="#F5F5F5",
                text="#333333",
                border="#003366",
                levels=["#003366", "#0055A4", "#0077CC", "#0099DD", "#5AB3E8", "#A0D2F0"],
            ),
            font_family="Arial",
            border_width=2,
            shadow=False,
        )

    def _create_academic_theme(self) -> Theme:
        """Academic/educational theme."""
        return Theme(
            name="Academic",
            description="Scholarly theme for education",
            palette=ColorPalette(
                primary="#8B0000",
                secondary="#4B0082",
                accent="#DAA520",
                background="#FFFFF0",
                text="#2C2C2C",
                border="#8B0000",
                levels=["#8B0000", "#4B0082", "#DAA520", "#2F4F4F", "#8B4513", "#556B2F"],
            ),
            font_family="Times New Roman",
            root_font_size=22,
            child_font_size=16,
        )

    def get_theme(self, theme_name: str) -> Optional[Theme]:
        """Get a theme by name."""
        # Check built-in themes
        if theme_name in self.themes:
            return self.themes[theme_name]
        # Check custom themes
        if theme_name in self.custom_themes:
            return self.custom_themes[theme_name]
        return None

    def add_custom_theme(self, theme: Theme) -> None:
        """Add a custom theme."""
        self.custom_themes[theme.name] = theme

    def list_themes(self) -> List[str]:
        """List all available theme names."""
        return list(self.themes.keys()) + list(self.custom_themes.keys())

    def get_all_themes(self) -> Dict[str, Theme]:
        """Get all themes (built-in and custom)."""
        return {**self.themes, **self.custom_themes}

    def generate_color_palette(
        self, base_color: str, num_colors: int = 6
    ) -> List[str]:
        """
        Generate a harmonious color palette from a base color.

        Args:
            base_color: Base color in hex format (#RRGGBB)
            num_colors: Number of colors to generate

        Returns:
            List of hex color strings
        """
        # Convert hex to RGB
        r = int(base_color[1:3], 16) / 255
        g = int(base_color[3:5], 16) / 255
        b = int(base_color[5:7], 16) / 255

        # Convert to HSV
        h, s, v = colorsys.rgb_to_hsv(r, g, b)

        # Generate complementary colors
        colors = []
        for i in range(num_colors):
            # Rotate hue
            new_h = (h + (i / num_colors)) % 1.0
            # Vary saturation and value slightly
            new_s = min(1.0, s + (i % 3 - 1) * 0.1)
            new_v = min(1.0, v + ((i + 1) % 3 - 1) * 0.1)

            # Convert back to RGB
            new_r, new_g, new_b = colorsys.hsv_to_rgb(new_h, new_s, new_v)

            # Convert to hex
            hex_color = "#{:02X}{:02X}{:02X}".format(
                int(new_r * 255),
                int(new_g * 255),
                int(new_b * 255),
            )
            colors.append(hex_color)

        return colors

    def create_custom_theme(
        self,
        name: str,
        base_color: str,
        description: str = "Custom theme",
    ) -> Theme:
        """
        Create a custom theme from a base color.

        Args:
            name: Theme name
            base_color: Base color in hex format
            description: Theme description

        Returns:
            New Theme object
        """
        colors = self.generate_color_palette(base_color, 6)

        # Determine if theme should be light or dark based on base color
        r = int(base_color[1:3], 16)
        g = int(base_color[3:5], 16)
        b = int(base_color[5:7], 16)
        brightness = (r + g + b) / 3

        is_dark = brightness < 128

        palette = ColorPalette(
            primary=colors[0],
            secondary=colors[1],
            accent=colors[2],
            background="#FFFFFF" if not is_dark else "#1E1E1E",
            text="#000000" if not is_dark else "#E1E1E1",
            border=colors[0],
            levels=colors,
        )

        theme = Theme(
            name=name,
            description=description,
            palette=palette,
            font_family="Arial",
        )

        self.add_custom_theme(theme)
        return theme

    def apply_theme_to_node(self, node: Any, theme: Theme, level: int = 0) -> None:
        """
        Apply theme styling to a node.

        Args:
            node: MindMapNode to style
            theme: Theme to apply
            level: Hierarchy level (0 for root)
        """
        # Get color for this level
        level_idx = min(level, len(theme.palette.levels) - 1)
        level_color = theme.palette.levels[level_idx]

        # Apply colors
        node.style.background_color = level_color
        node.style.text_color = theme.palette.text
        node.style.border_color = theme.palette.border
        node.style.border_width = theme.border_width

        # Apply font
        node.style.font_family = theme.font_family
        if level == 0:
            node.style.font_size = theme.root_font_size
            node.style.font_weight = "bold"
        else:
            node.style.font_size = theme.child_font_size

        # Apply effects
        node.style.shadow = theme.shadow

        # Apply shape based on corners
        from .nodes import NodeShape
        if theme.rounded_corners:
            node.style.shape = NodeShape.ROUNDED_RECTANGLE
        else:
            node.style.shape = NodeShape.RECTANGLE

    def export_theme(self, theme_name: str) -> Optional[Dict[str, Any]]:
        """Export a theme to dictionary."""
        theme = self.get_theme(theme_name)
        if theme:
            return theme.to_dict()
        return None

    def import_theme(self, theme_data: Dict[str, Any]) -> Theme:
        """Import a theme from dictionary."""
        theme = Theme.from_dict(theme_data)
        self.add_custom_theme(theme)
        return theme
