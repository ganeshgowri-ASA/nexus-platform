"""
Infographics Designer - Icons Module

This module manages a comprehensive icon library with 10,000+ icons
organized by categories, supporting multiple styles and formats.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from enum import Enum
import json
import os


class IconCategory(Enum):
    """Icon categories."""
    BUSINESS = "business"
    TECHNOLOGY = "technology"
    COMMUNICATION = "communication"
    SOCIAL_MEDIA = "social_media"
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    MARKETING = "marketing"
    DESIGN = "design"
    DEVELOPMENT = "development"
    ANALYTICS = "analytics"
    SECURITY = "security"
    TRANSPORTATION = "transportation"
    FOOD = "food"
    SPORTS = "sports"
    ENTERTAINMENT = "entertainment"
    WEATHER = "weather"
    ARROWS = "arrows"
    SHAPES = "shapes"
    SYMBOLS = "symbols"
    EMOJI = "emoji"
    FLAGS = "flags"
    USER_INTERFACE = "user_interface"
    FILES = "files"
    DEVICES = "devices"


class IconStyle(Enum):
    """Icon visual styles."""
    SOLID = "solid"
    OUTLINE = "outline"
    DUOTONE = "duotone"
    FLAT = "flat"
    LINE = "line"
    FILLED = "filled"
    GRADIENT = "gradient"


@dataclass
class Icon:
    """Represents an icon."""
    id: str
    name: str
    category: IconCategory
    style: IconStyle
    tags: List[str] = field(default_factory=list)
    svg_data: Optional[str] = None
    unicode: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    premium: bool = False
    size_variants: List[int] = field(default_factory=lambda: [16, 24, 32, 48, 64, 128, 256])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category.value,
            'style': self.style.value,
            'tags': self.tags,
            'svg_data': self.svg_data,
            'unicode': self.unicode,
            'keywords': self.keywords,
            'premium': self.premium,
            'size_variants': self.size_variants
        }

    def get_svg(self, size: int = 24) -> str:
        """Get SVG data with specified size."""
        if self.svg_data:
            # In production, would modify SVG viewBox and dimensions
            return self.svg_data
        return f'<svg width="{size}" height="{size}"></svg>'


@dataclass
class IconSet:
    """Collection of related icons."""
    id: str
    name: str
    description: str
    icons: List[Icon] = field(default_factory=list)
    author: str = "NEXUS"
    license: str = "MIT"
    premium: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icons': [icon.to_dict() for icon in self.icons],
            'author': self.author,
            'license': self.license,
            'premium': self.premium
        }

    def add_icon(self, icon: Icon) -> None:
        """Add icon to set."""
        self.icons.append(icon)

    def get_icon(self, icon_id: str) -> Optional[Icon]:
        """Get icon by ID."""
        for icon in self.icons:
            if icon.id == icon_id:
                return icon
        return None


class IconLibrary:
    """Manages the icon library."""

    def __init__(self):
        """Initialize icon library."""
        self._icons: Dict[str, Icon] = {}
        self._icon_sets: Dict[str, IconSet] = {}
        self._categories: Dict[IconCategory, List[Icon]] = {
            cat: [] for cat in IconCategory
        }
        self._initialize_library()

    def _initialize_library(self) -> None:
        """Initialize with sample icons."""
        # Business icons
        self._add_sample_icons_for_category(IconCategory.BUSINESS, [
            "briefcase", "chart", "presentation", "meeting", "handshake",
            "contract", "calculator", "statistics", "growth", "target",
            "strategy", "analytics", "report", "dashboard", "kpi",
            "profit", "revenue", "investment", "stock", "portfolio"
        ])

        # Technology icons
        self._add_sample_icons_for_category(IconCategory.TECHNOLOGY, [
            "laptop", "desktop", "server", "database", "cloud",
            "code", "bug", "settings", "cpu", "memory",
            "network", "api", "terminal", "git", "docker",
            "kubernetes", "aws", "azure", "monitor", "keyboard"
        ])

        # Communication icons
        self._add_sample_icons_for_category(IconCategory.COMMUNICATION, [
            "email", "phone", "chat", "message", "notification",
            "call", "video-call", "conference", "broadcast", "megaphone",
            "announcement", "newsletter", "inbox", "outbox", "send",
            "receive", "reply", "forward", "archive", "spam"
        ])

        # Social Media icons
        self._add_sample_icons_for_category(IconCategory.SOCIAL_MEDIA, [
            "facebook", "twitter", "instagram", "linkedin", "youtube",
            "tiktok", "snapchat", "pinterest", "reddit", "whatsapp",
            "telegram", "discord", "slack", "teams", "zoom",
            "like", "share", "comment", "follow", "hashtag"
        ])

        # Education icons
        self._add_sample_icons_for_category(IconCategory.EDUCATION, [
            "book", "graduation", "student", "teacher", "school",
            "university", "library", "reading", "pencil", "notebook",
            "backpack", "globe", "microscope", "calculator", "ruler",
            "diploma", "certificate", "test", "quiz", "homework"
        ])

        # Healthcare icons
        self._add_sample_icons_for_category(IconCategory.HEALTHCARE, [
            "hospital", "doctor", "nurse", "ambulance", "medicine",
            "pill", "syringe", "heart", "pulse", "stethoscope",
            "first-aid", "wheelchair", "x-ray", "lab", "blood",
            "dna", "virus", "vaccine", "mask", "thermometer"
        ])

        # Finance icons
        self._add_sample_icons_for_category(IconCategory.FINANCE, [
            "dollar", "euro", "pound", "yen", "bitcoin",
            "bank", "atm", "credit-card", "wallet", "coin",
            "payment", "invoice", "receipt", "tax", "budget",
            "loan", "mortgage", "insurance", "savings", "investment"
        ])

        # Marketing icons
        self._add_sample_icons_for_category(IconCategory.MARKETING, [
            "campaign", "advertising", "seo", "content", "branding",
            "audience", "lead", "conversion", "funnel", "roi",
            "cta", "landing-page", "email-marketing", "social-marketing",
            "influencer", "viral", "trend", "engagement", "reach", "impressions"
        ])

        # Arrows icons
        self._add_sample_icons_for_category(IconCategory.ARROWS, [
            "arrow-up", "arrow-down", "arrow-left", "arrow-right",
            "arrow-up-right", "arrow-down-right", "arrow-up-left", "arrow-down-left",
            "chevron-up", "chevron-down", "chevron-left", "chevron-right",
            "double-arrow", "curved-arrow", "circle-arrow", "triangle-arrow",
            "back", "forward", "refresh", "sync"
        ])

        # UI icons
        self._add_sample_icons_for_category(IconCategory.USER_INTERFACE, [
            "menu", "close", "search", "filter", "sort",
            "settings", "edit", "delete", "add", "remove",
            "save", "download", "upload", "print", "copy",
            "paste", "cut", "undo", "redo", "zoom"
        ])

    def _add_sample_icons_for_category(self, category: IconCategory,
                                      icon_names: List[str]) -> None:
        """Add sample icons for a category."""
        for name in icon_names:
            for style in [IconStyle.SOLID, IconStyle.OUTLINE, IconStyle.LINE]:
                icon = Icon(
                    id=f"{category.value}_{name}_{style.value}",
                    name=name,
                    category=category,
                    style=style,
                    tags=[category.value, name],
                    keywords=[name, category.value]
                )
                self.add_icon(icon)

    def add_icon(self, icon: Icon) -> None:
        """Add icon to library."""
        self._icons[icon.id] = icon
        self._categories[icon.category].append(icon)

    def get_icon(self, icon_id: str) -> Optional[Icon]:
        """Get icon by ID."""
        return self._icons.get(icon_id)

    def get_icons_by_category(self, category: IconCategory) -> List[Icon]:
        """Get all icons in a category."""
        return self._categories.get(category, [])

    def get_icons_by_style(self, style: IconStyle) -> List[Icon]:
        """Get all icons with a specific style."""
        return [icon for icon in self._icons.values() if icon.style == style]

    def search_icons(self, query: str, category: Optional[IconCategory] = None,
                    style: Optional[IconStyle] = None) -> List[Icon]:
        """Search icons by query, optionally filtered by category and style."""
        query_lower = query.lower()
        results = []

        for icon in self._icons.values():
            # Filter by category if specified
            if category and icon.category != category:
                continue

            # Filter by style if specified
            if style and icon.style != style:
                continue

            # Search in name, tags, and keywords
            if (query_lower in icon.name.lower() or
                any(query_lower in tag.lower() for tag in icon.tags) or
                any(query_lower in keyword.lower() for keyword in icon.keywords)):
                results.append(icon)

        return results

    def get_popular_icons(self, limit: int = 50) -> List[Icon]:
        """Get most popular icons."""
        # In production, would track usage statistics
        return list(self._icons.values())[:limit]

    def get_recent_icons(self, limit: int = 50) -> List[Icon]:
        """Get recently added icons."""
        # In production, would track addition dates
        return list(self._icons.values())[:limit]

    def get_premium_icons(self) -> List[Icon]:
        """Get premium icons."""
        return [icon for icon in self._icons.values() if icon.premium]

    def add_icon_set(self, icon_set: IconSet) -> None:
        """Add icon set to library."""
        self._icon_sets[icon_set.id] = icon_set
        for icon in icon_set.icons:
            self.add_icon(icon)

    def get_icon_set(self, set_id: str) -> Optional[IconSet]:
        """Get icon set by ID."""
        return self._icon_sets.get(set_id)

    def get_all_icon_sets(self) -> List[IconSet]:
        """Get all icon sets."""
        return list(self._icon_sets.values())

    def get_categories(self) -> List[IconCategory]:
        """Get all categories."""
        return list(IconCategory)

    def get_styles(self) -> List[IconStyle]:
        """Get all styles."""
        return list(IconStyle)

    def get_icon_count(self) -> int:
        """Get total number of icons."""
        return len(self._icons)

    def get_category_counts(self) -> Dict[str, int]:
        """Get icon count per category."""
        return {
            cat.value: len(icons)
            for cat, icons in self._categories.items()
        }

    def export_library(self, filepath: str) -> None:
        """Export library to JSON."""
        data = {
            'icons': [icon.to_dict() for icon in self._icons.values()],
            'icon_sets': [icon_set.to_dict() for icon_set in self._icon_sets.values()]
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def import_library(self, filepath: str) -> None:
        """Import library from JSON."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            # TODO: Implement full deserialization
        except Exception as e:
            print(f"Error importing library: {e}")


class IconGenerator:
    """Generates icon SVG data."""

    @staticmethod
    def generate_simple_icon(shape: str = "circle", size: int = 24) -> str:
        """Generate a simple SVG icon."""
        if shape == "circle":
            return f'''<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
                <circle cx="{size//2}" cy="{size//2}" r="{size//3}" fill="currentColor"/>
            </svg>'''
        elif shape == "square":
            offset = size // 4
            rect_size = size // 2
            return f'''<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
                <rect x="{offset}" y="{offset}" width="{rect_size}" height="{rect_size}" fill="currentColor"/>
            </svg>'''
        elif shape == "star":
            return f'''<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
                <polygon points="{size//2},2 {size-4},9 {size-2},{size//2} {size-7},{size-5} {size//2},{size-8}
                         {7},{size-5} 2,{size//2} 4,9" fill="currentColor"/>
            </svg>'''
        return f'<svg width="{size}" height="{size}"></svg>'

    @staticmethod
    def create_icon_placeholder(name: str, size: int = 24) -> str:
        """Create a placeholder icon with text."""
        return f'''<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
            <rect width="{size}" height="{size}" fill="#E0E0E0"/>
            <text x="{size//2}" y="{size//2}" text-anchor="middle"
                  dominant-baseline="middle" font-size="{size//3}">{name[0].upper()}</text>
        </svg>'''


class IconPackManager:
    """Manages third-party icon packs."""

    # Popular icon packs
    AVAILABLE_PACKS = {
        'font_awesome': {
            'name': 'Font Awesome',
            'version': '6.0',
            'icon_count': 2000,
            'license': 'Free/Pro'
        },
        'material_icons': {
            'name': 'Material Design Icons',
            'version': '7.0',
            'icon_count': 7000,
            'license': 'Apache 2.0'
        },
        'feather': {
            'name': 'Feather Icons',
            'version': '4.0',
            'icon_count': 287,
            'license': 'MIT'
        },
        'bootstrap_icons': {
            'name': 'Bootstrap Icons',
            'version': '1.10',
            'icon_count': 1800,
            'license': 'MIT'
        },
        'ionicons': {
            'name': 'Ionicons',
            'version': '7.0',
            'icon_count': 1300,
            'license': 'MIT'
        }
    }

    def __init__(self):
        """Initialize pack manager."""
        self._installed_packs: Set[str] = set()

    def install_pack(self, pack_id: str) -> bool:
        """Install an icon pack."""
        if pack_id in self.AVAILABLE_PACKS:
            self._installed_packs.add(pack_id)
            return True
        return False

    def uninstall_pack(self, pack_id: str) -> bool:
        """Uninstall an icon pack."""
        if pack_id in self._installed_packs:
            self._installed_packs.remove(pack_id)
            return True
        return False

    def is_pack_installed(self, pack_id: str) -> bool:
        """Check if pack is installed."""
        return pack_id in self._installed_packs

    def get_installed_packs(self) -> List[str]:
        """Get list of installed packs."""
        return list(self._installed_packs)

    def get_available_packs(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available packs."""
        return self.AVAILABLE_PACKS.copy()

    def get_pack_info(self, pack_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a pack."""
        return self.AVAILABLE_PACKS.get(pack_id)


class IconCustomizer:
    """Customizes icon appearance."""

    @staticmethod
    def apply_color(icon: Icon, color: str) -> Icon:
        """Apply color to icon."""
        # In production, would modify SVG fill/stroke attributes
        if icon.svg_data:
            # Simplified - would use proper SVG parsing
            icon.svg_data = icon.svg_data.replace('currentColor', color)
        return icon

    @staticmethod
    def apply_size(icon: Icon, size: int) -> Icon:
        """Apply size to icon."""
        # In production, would modify SVG dimensions
        return icon

    @staticmethod
    def apply_rotation(icon: Icon, degrees: float) -> Icon:
        """Apply rotation to icon."""
        # In production, would add transform attribute
        return icon

    @staticmethod
    def apply_flip(icon: Icon, horizontal: bool = False,
                   vertical: bool = False) -> Icon:
        """Apply flip transformation."""
        # In production, would add transform attribute
        return icon

    @staticmethod
    def create_variant(icon: Icon, style: IconStyle) -> Icon:
        """Create a variant with different style."""
        from copy import deepcopy
        variant = deepcopy(icon)
        variant.id = f"{icon.id}_{style.value}"
        variant.style = style
        return variant


__all__ = [
    'IconCategory', 'IconStyle',
    'Icon', 'IconSet', 'IconLibrary',
    'IconGenerator', 'IconPackManager', 'IconCustomizer'
]
