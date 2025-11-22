"""
Theme Builder - Color Schemes and Theme Management

Manages presentation themes including color schemes, font pairs,
background styles, and overall design consistency.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import colorsys


class ThemeStyle(Enum):
    """Theme style categories."""
    PROFESSIONAL = "professional"
    CREATIVE = "creative"
    MINIMAL = "minimal"
    BOLD = "bold"
    ELEGANT = "elegant"
    MODERN = "modern"
    CLASSIC = "classic"
    PLAYFUL = "playful"


@dataclass
class ColorScheme:
    """Color scheme definition."""
    id: str
    name: str
    primary: str
    secondary: str
    accent: str
    background: str
    text: str
    text_secondary: str
    success: str = "#2ECC71"
    warning: str = "#F39C12"
    error: str = "#E74C3C"
    info: str = "#3498DB"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "primary": self.primary,
            "secondary": self.secondary,
            "accent": self.accent,
            "background": self.background,
            "text": self.text,
            "text_secondary": self.text_secondary,
            "success": self.success,
            "warning": self.warning,
            "error": self.error,
            "info": self.info,
        }

    def get_palette(self) -> List[str]:
        """Get all colors as a list."""
        return [
            self.primary,
            self.secondary,
            self.accent,
            self.success,
            self.info,
            self.warning,
            self.error,
        ]


@dataclass
class FontPair:
    """Font pairing definition."""
    id: str
    name: str
    heading_font: str
    body_font: str
    heading_weight: str = "bold"
    body_weight: str = "normal"
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "heading_font": self.heading_font,
            "body_font": self.body_font,
            "heading_weight": self.heading_weight,
            "body_weight": self.body_weight,
            "description": self.description,
        }


@dataclass
class BackgroundStyle:
    """Background style definition."""
    type: str = "solid"  # solid, gradient, pattern, image
    color: Optional[str] = "#FFFFFF"
    gradient_colors: Optional[List[str]] = None
    gradient_angle: float = 45.0
    gradient_type: str = "linear"  # linear, radial
    pattern: Optional[str] = None
    image_url: Optional[str] = None
    opacity: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type,
            "color": self.color,
            "gradient_colors": self.gradient_colors,
            "gradient_angle": self.gradient_angle,
            "gradient_type": self.gradient_type,
            "pattern": self.pattern,
            "image_url": self.image_url,
            "opacity": self.opacity,
        }


@dataclass
class Theme:
    """Complete presentation theme."""
    id: str
    name: str
    description: str
    style: ThemeStyle
    color_scheme: ColorScheme
    font_pair: FontPair
    background: BackgroundStyle
    thumbnail: str = ""
    is_custom: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "style": self.style.value,
            "color_scheme": self.color_scheme.to_dict(),
            "font_pair": self.font_pair.to_dict(),
            "background": self.background.to_dict(),
            "thumbnail": self.thumbnail,
            "is_custom": self.is_custom,
        }


class ThemeBuilder:
    """
    Manages presentation themes.

    Features:
    - Pre-designed theme library
    - Custom theme creation
    - Color scheme generation
    - Font pairing recommendations
    - Theme customization
    - Color harmony tools
    """

    def __init__(self):
        """Initialize theme builder."""
        self.themes: Dict[str, Theme] = {}
        self.color_schemes: Dict[str, ColorScheme] = {}
        self.font_pairs: Dict[str, FontPair] = {}
        self._init_default_themes()

    def _init_default_themes(self) -> None:
        """Initialize default themes, color schemes, and font pairs."""

        # Color Schemes
        self.color_schemes["professional_blue"] = ColorScheme(
            id="professional_blue",
            name="Professional Blue",
            primary="#2E86AB",
            secondary="#A23B72",
            accent="#F18F01",
            background="#FFFFFF",
            text="#1A1A1A",
            text_secondary="#666666"
        )

        self.color_schemes["modern_purple"] = ColorScheme(
            id="modern_purple",
            name="Modern Purple",
            primary="#667eea",
            secondary="#764ba2",
            accent="#f093fb",
            background="#FFFFFF",
            text="#2C3E50",
            text_secondary="#7F8C8D"
        )

        self.color_schemes["creative_sunset"] = ColorScheme(
            id="creative_sunset",
            name="Creative Sunset",
            primary="#FF6B6B",
            secondary="#4ECDC4",
            accent="#FFA07A",
            background="#FFFFFF",
            text="#2C3E50",
            text_secondary="#95A5A6"
        )

        self.color_schemes["elegant_dark"] = ColorScheme(
            id="elegant_dark",
            name="Elegant Dark",
            primary="#D4AF37",
            secondary="#C0C0C0",
            accent="#FFD700",
            background="#1A1A1A",
            text="#FFFFFF",
            text_secondary="#CCCCCC"
        )

        self.color_schemes["minimal_gray"] = ColorScheme(
            id="minimal_gray",
            name="Minimal Gray",
            primary="#34495E",
            secondary="#7F8C8D",
            accent="#3498DB",
            background="#FAFAFA",
            text="#2C3E50",
            text_secondary="#95A5A6"
        )

        self.color_schemes["vibrant_energy"] = ColorScheme(
            id="vibrant_energy",
            name="Vibrant Energy",
            primary="#E74C3C",
            secondary="#9B59B6",
            accent="#F39C12",
            background="#FFFFFF",
            text="#2C3E50",
            text_secondary="#7F8C8D"
        )

        self.color_schemes["nature_green"] = ColorScheme(
            id="nature_green",
            name="Nature Green",
            primary="#27AE60",
            secondary="#16A085",
            accent="#F39C12",
            background="#FFFFFF",
            text="#2C3E50",
            text_secondary="#7F8C8D"
        )

        self.color_schemes["ocean_blue"] = ColorScheme(
            id="ocean_blue",
            name="Ocean Blue",
            primary="#3498DB",
            secondary="#2980B9",
            accent="#1ABC9C",
            background="#ECF0F1",
            text="#2C3E50",
            text_secondary="#7F8C8D"
        )

        # Font Pairs
        self.font_pairs["classic"] = FontPair(
            id="classic",
            name="Classic",
            heading_font="Georgia",
            body_font="Arial",
            description="Timeless and professional"
        )

        self.font_pairs["modern"] = FontPair(
            id="modern",
            name="Modern",
            heading_font="Helvetica",
            body_font="Helvetica",
            description="Clean and contemporary"
        )

        self.font_pairs["bold"] = FontPair(
            id="bold",
            name="Bold",
            heading_font="Impact",
            body_font="Arial",
            description="Strong and impactful"
        )

        self.font_pairs["elegant"] = FontPair(
            id="elegant",
            name="Elegant",
            heading_font="Palatino",
            body_font="Garamond",
            description="Sophisticated and refined"
        )

        self.font_pairs["creative"] = FontPair(
            id="creative",
            name="Creative",
            heading_font="Courier New",
            body_font="Arial",
            description="Unique and artistic"
        )

        self.font_pairs["friendly"] = FontPair(
            id="friendly",
            name="Friendly",
            heading_font="Comic Sans MS",
            body_font="Verdana",
            description="Approachable and warm"
        )

        # Create Default Themes
        self.themes["professional"] = Theme(
            id="professional",
            name="Professional",
            description="Clean and corporate theme for business presentations",
            style=ThemeStyle.PROFESSIONAL,
            color_scheme=self.color_schemes["professional_blue"],
            font_pair=self.font_pairs["modern"],
            background=BackgroundStyle(type="solid", color="#FFFFFF")
        )

        self.themes["modern_gradient"] = Theme(
            id="modern_gradient",
            name="Modern Gradient",
            description="Contemporary theme with gradient backgrounds",
            style=ThemeStyle.MODERN,
            color_scheme=self.color_schemes["modern_purple"],
            font_pair=self.font_pairs["modern"],
            background=BackgroundStyle(
                type="gradient",
                gradient_colors=["#667eea", "#764ba2"],
                gradient_type="linear",
                gradient_angle=135.0
            )
        )

        self.themes["creative_vibrant"] = Theme(
            id="creative_vibrant",
            name="Creative Vibrant",
            description="Bold and colorful theme for creative presentations",
            style=ThemeStyle.CREATIVE,
            color_scheme=self.color_schemes["creative_sunset"],
            font_pair=self.font_pairs["bold"],
            background=BackgroundStyle(type="solid", color="#FFFFFF")
        )

        self.themes["minimal"] = Theme(
            id="minimal",
            name="Minimal",
            description="Simple and clean minimalist theme",
            style=ThemeStyle.MINIMAL,
            color_scheme=self.color_schemes["minimal_gray"],
            font_pair=self.font_pairs["modern"],
            background=BackgroundStyle(type="solid", color="#FAFAFA")
        )

        self.themes["elegant_dark"] = Theme(
            id="elegant_dark",
            name="Elegant Dark",
            description="Sophisticated dark theme with gold accents",
            style=ThemeStyle.ELEGANT,
            color_scheme=self.color_schemes["elegant_dark"],
            font_pair=self.font_pairs["elegant"],
            background=BackgroundStyle(type="solid", color="#1A1A1A")
        )

        self.themes["nature"] = Theme(
            id="nature",
            name="Nature",
            description="Fresh and natural theme with green tones",
            style=ThemeStyle.PROFESSIONAL,
            color_scheme=self.color_schemes["nature_green"],
            font_pair=self.font_pairs["classic"],
            background=BackgroundStyle(type="solid", color="#FFFFFF")
        )

    def get_theme(self, theme_id: str) -> Optional[Theme]:
        """Get theme by ID."""
        return self.themes.get(theme_id)

    def get_all_themes(self) -> List[Theme]:
        """Get all available themes."""
        return list(self.themes.values())

    def get_themes_by_style(self, style: ThemeStyle) -> List[Theme]:
        """Get themes by style category."""
        return [
            theme for theme in self.themes.values()
            if theme.style == style
        ]

    def get_color_scheme(self, scheme_id: str) -> Optional[ColorScheme]:
        """Get color scheme by ID."""
        return self.color_schemes.get(scheme_id)

    def get_all_color_schemes(self) -> List[ColorScheme]:
        """Get all color schemes."""
        return list(self.color_schemes.values())

    def get_font_pair(self, pair_id: str) -> Optional[FontPair]:
        """Get font pair by ID."""
        return self.font_pairs.get(pair_id)

    def get_all_font_pairs(self) -> List[FontPair]:
        """Get all font pairs."""
        return list(self.font_pairs.values())

    def create_custom_theme(
        self,
        name: str,
        description: str,
        style: ThemeStyle,
        color_scheme: ColorScheme,
        font_pair: FontPair,
        background: BackgroundStyle
    ) -> Theme:
        """Create a custom theme."""
        import hashlib
        theme_id = f"custom_{hashlib.md5(name.encode()).hexdigest()[:12]}"

        theme = Theme(
            id=theme_id,
            name=name,
            description=description,
            style=style,
            color_scheme=color_scheme,
            font_pair=font_pair,
            background=background,
            is_custom=True
        )

        self.themes[theme_id] = theme
        return theme

    def create_custom_color_scheme(
        self,
        name: str,
        primary: str,
        secondary: str,
        accent: str,
        background: str = "#FFFFFF",
        text: str = "#1A1A1A"
    ) -> ColorScheme:
        """Create a custom color scheme."""
        import hashlib
        scheme_id = f"custom_{hashlib.md5(name.encode()).hexdigest()[:12]}"

        scheme = ColorScheme(
            id=scheme_id,
            name=name,
            primary=primary,
            secondary=secondary,
            accent=accent,
            background=background,
            text=text,
            text_secondary=self._generate_secondary_text_color(text, background)
        )

        self.color_schemes[scheme_id] = scheme
        return scheme

    def create_custom_font_pair(
        self,
        name: str,
        heading_font: str,
        body_font: str,
        description: str = ""
    ) -> FontPair:
        """Create a custom font pair."""
        import hashlib
        pair_id = f"custom_{hashlib.md5(name.encode()).hexdigest()[:12]}"

        pair = FontPair(
            id=pair_id,
            name=name,
            heading_font=heading_font,
            body_font=body_font,
            description=description
        )

        self.font_pairs[pair_id] = pair
        return pair

    def _generate_secondary_text_color(
        self,
        text_color: str,
        background_color: str
    ) -> str:
        """Generate a secondary text color with reduced opacity effect."""
        # Simple implementation - mix text color with background
        # In production, would use proper color mixing
        if text_color == "#FFFFFF" or text_color == "#FFF":
            return "#CCCCCC"
        else:
            return "#666666"

    # Color Generation Tools

    def generate_complementary_colors(self, base_color: str) -> List[str]:
        """Generate complementary color scheme from base color."""
        rgb = self._hex_to_rgb(base_color)
        h, s, v = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)

        # Complementary (opposite on color wheel)
        comp_h = (h + 0.5) % 1.0
        comp_rgb = colorsys.hsv_to_rgb(comp_h, s, v)
        complementary = self._rgb_to_hex(
            int(comp_rgb[0] * 255),
            int(comp_rgb[1] * 255),
            int(comp_rgb[2] * 255)
        )

        return [base_color, complementary]

    def generate_analogous_colors(self, base_color: str) -> List[str]:
        """Generate analogous color scheme from base color."""
        rgb = self._hex_to_rgb(base_color)
        h, s, v = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)

        colors = [base_color]

        # Analogous colors (adjacent on color wheel)
        for offset in [-0.083, 0.083]:  # ±30 degrees
            new_h = (h + offset) % 1.0
            new_rgb = colorsys.hsv_to_rgb(new_h, s, v)
            color = self._rgb_to_hex(
                int(new_rgb[0] * 255),
                int(new_rgb[1] * 255),
                int(new_rgb[2] * 255)
            )
            colors.append(color)

        return colors

    def generate_triadic_colors(self, base_color: str) -> List[str]:
        """Generate triadic color scheme from base color."""
        rgb = self._hex_to_rgb(base_color)
        h, s, v = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)

        colors = [base_color]

        # Triadic colors (120 degrees apart)
        for offset in [0.333, 0.667]:
            new_h = (h + offset) % 1.0
            new_rgb = colorsys.hsv_to_rgb(new_h, s, v)
            color = self._rgb_to_hex(
                int(new_rgb[0] * 255),
                int(new_rgb[1] * 255),
                int(new_rgb[2] * 255)
            )
            colors.append(color)

        return colors

    def generate_monochromatic_colors(self, base_color: str, count: int = 5) -> List[str]:
        """Generate monochromatic color variations."""
        rgb = self._hex_to_rgb(base_color)
        h, s, v = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)

        colors = []
        for i in range(count):
            # Vary lightness
            new_v = 0.3 + (0.6 * i / (count - 1))
            new_rgb = colorsys.hsv_to_rgb(h, s, new_v)
            color = self._rgb_to_hex(
                int(new_rgb[0] * 255),
                int(new_rgb[1] * 255),
                int(new_rgb[2] * 255)
            )
            colors.append(color)

        return colors

    def lighten_color(self, color: str, amount: float = 0.2) -> str:
        """Lighten a color by amount (0-1)."""
        rgb = self._hex_to_rgb(color)
        h, s, v = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)

        v = min(1.0, v + amount)
        new_rgb = colorsys.hsv_to_rgb(h, s, v)

        return self._rgb_to_hex(
            int(new_rgb[0] * 255),
            int(new_rgb[1] * 255),
            int(new_rgb[2] * 255)
        )

    def darken_color(self, color: str, amount: float = 0.2) -> str:
        """Darken a color by amount (0-1)."""
        rgb = self._hex_to_rgb(color)
        h, s, v = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)

        v = max(0.0, v - amount)
        new_rgb = colorsys.hsv_to_rgb(h, s, v)

        return self._rgb_to_hex(
            int(new_rgb[0] * 255),
            int(new_rgb[1] * 255),
            int(new_rgb[2] * 255)
        )

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _rgb_to_hex(self, r: int, g: int, b: int) -> str:
        """Convert RGB to hex color."""
        return f"#{r:02x}{g:02x}{b:02x}".upper()

    def get_contrast_color(self, background_color: str) -> str:
        """Get contrasting text color (black or white) for background."""
        rgb = self._hex_to_rgb(background_color)

        # Calculate relative luminance
        luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255

        # Return black for light backgrounds, white for dark
        return "#000000" if luminance > 0.5 else "#FFFFFF"

    def delete_custom_theme(self, theme_id: str) -> bool:
        """Delete a custom theme."""
        if theme_id.startswith("custom_") and theme_id in self.themes:
            del self.themes[theme_id]
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "themes": {
                tid: theme.to_dict()
                for tid, theme in self.themes.items()
                if theme.is_custom
            },
            "color_schemes": {
                sid: scheme.to_dict()
                for sid, scheme in self.color_schemes.items()
                if sid.startswith("custom_")
            },
            "font_pairs": {
                fid: pair.to_dict()
                for fid, pair in self.font_pairs.items()
                if fid.startswith("custom_")
            }
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load custom items from dictionary."""
        # Load custom color schemes
        for sid, scheme_data in data.get("color_schemes", {}).items():
            scheme = ColorScheme(**scheme_data)
            self.color_schemes[sid] = scheme

        # Load custom font pairs
        for fid, pair_data in data.get("font_pairs", {}).items():
            pair = FontPair(**pair_data)
            self.font_pairs[fid] = pair

        # Load custom themes
        for tid, theme_data in data.get("themes", {}).items():
            theme = Theme(
                id=theme_data["id"],
                name=theme_data["name"],
                description=theme_data["description"],
                style=ThemeStyle(theme_data["style"]),
                color_scheme=ColorScheme(**theme_data["color_scheme"]),
                font_pair=FontPair(**theme_data["font_pair"]),
                background=BackgroundStyle(**theme_data["background"]),
                thumbnail=theme_data.get("thumbnail", ""),
                is_custom=theme_data.get("is_custom", True)
            )
            self.themes[tid] = theme
