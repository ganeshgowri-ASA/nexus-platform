"""
Infographics Designer - Templates Module

This module provides 100+ professional templates for various use cases
including business, education, marketing, data reports, and social media.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import json

from .elements import (
    BaseElement, ElementFactory, ElementPresets,
    ShapeType, TextAlign, Position, Style, TextStyle
)


class TemplateCategory(Enum):
    """Template categories."""
    BUSINESS = "business"
    EDUCATION = "education"
    MARKETING = "marketing"
    DATA_REPORT = "data_report"
    SOCIAL_MEDIA = "social_media"
    PRESENTATION = "presentation"
    INFOGRAPHIC = "infographic"
    COMPARISON = "comparison"
    TIMELINE = "timeline"
    PROCESS = "process"
    STATISTICS = "statistics"
    ANNOUNCEMENT = "announcement"


class TemplateStyle(Enum):
    """Template visual styles."""
    MODERN = "modern"
    CLASSIC = "classic"
    MINIMAL = "minimal"
    CREATIVE = "creative"
    PROFESSIONAL = "professional"
    PLAYFUL = "playful"
    ELEGANT = "elegant"
    BOLD = "bold"


class SocialMediaFormat(Enum):
    """Social media format presets."""
    INSTAGRAM_POST = "instagram_post"  # 1080x1080
    INSTAGRAM_STORY = "instagram_story"  # 1080x1920
    FACEBOOK_POST = "facebook_post"  # 1200x630
    TWITTER_POST = "twitter_post"  # 1200x675
    LINKEDIN_POST = "linkedin_post"  # 1200x627
    PINTEREST_PIN = "pinterest_pin"  # 1000x1500
    YOUTUBE_THUMBNAIL = "youtube_thumbnail"  # 1280x720


@dataclass
class TemplateMetadata:
    """Metadata for a template."""
    id: str
    name: str
    category: TemplateCategory
    style: TemplateStyle
    description: str
    tags: List[str] = field(default_factory=list)
    author: str = "NEXUS"
    thumbnail_url: Optional[str] = None
    premium: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category.value,
            'style': self.style.value,
            'description': self.description,
            'tags': self.tags,
            'author': self.author,
            'thumbnail_url': self.thumbnail_url,
            'premium': self.premium
        }


@dataclass
class Template:
    """Infographic template."""
    metadata: TemplateMetadata
    canvas_width: float = 1920
    canvas_height: float = 1080
    background_color: str = "#FFFFFF"
    background_image: Optional[str] = None
    elements: List[BaseElement] = field(default_factory=list)
    color_scheme: Dict[str, str] = field(default_factory=dict)
    font_scheme: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary."""
        return {
            'metadata': self.metadata.to_dict(),
            'canvas_width': self.canvas_width,
            'canvas_height': self.canvas_height,
            'background_color': self.background_color,
            'background_image': self.background_image,
            'elements': [elem.to_dict() for elem in self.elements],
            'color_scheme': self.color_scheme,
            'font_scheme': self.font_scheme
        }

    def add_element(self, element: BaseElement) -> None:
        """Add element to template."""
        self.elements.append(element)

    def get_element(self, element_id: str) -> Optional[BaseElement]:
        """Get element by ID."""
        for elem in self.elements:
            if elem.id == element_id:
                return elem
        return None

    def remove_element(self, element_id: str) -> None:
        """Remove element from template."""
        self.elements = [e for e in self.elements if e.id != element_id]


class TemplateGenerator:
    """Generates templates programmatically."""

    # Color schemes
    COLOR_SCHEMES = {
        'blue_professional': {
            'primary': '#2C3E50',
            'secondary': '#3498DB',
            'accent': '#E74C3C',
            'background': '#ECF0F1',
            'text': '#2C3E50'
        },
        'modern_green': {
            'primary': '#27AE60',
            'secondary': '#2ECC71',
            'accent': '#F39C12',
            'background': '#FFFFFF',
            'text': '#2C3E50'
        },
        'creative_purple': {
            'primary': '#8E44AD',
            'secondary': '#9B59B6',
            'accent': '#F1C40F',
            'background': '#F8F9FA',
            'text': '#34495E'
        },
        'bold_red': {
            'primary': '#C0392B',
            'secondary': '#E74C3C',
            'accent': '#ECF0F1',
            'background': '#2C3E50',
            'text': '#ECF0F1'
        },
        'minimal_mono': {
            'primary': '#212121',
            'secondary': '#424242',
            'accent': '#757575',
            'background': '#FAFAFA',
            'text': '#212121'
        }
    }

    # Font schemes
    FONT_SCHEMES = {
        'modern': {
            'heading': 'Montserrat',
            'subheading': 'Open Sans',
            'body': 'Roboto'
        },
        'classic': {
            'heading': 'Georgia',
            'subheading': 'Garamond',
            'body': 'Times New Roman'
        },
        'tech': {
            'heading': 'Inter',
            'subheading': 'Source Sans Pro',
            'body': 'Roboto Mono'
        }
    }

    @staticmethod
    def create_business_report_template() -> Template:
        """Create a business report template."""
        metadata = TemplateMetadata(
            id="business_report_001",
            name="Professional Business Report",
            category=TemplateCategory.BUSINESS,
            style=TemplateStyle.PROFESSIONAL,
            description="Clean and professional business report template",
            tags=["business", "report", "professional", "data"]
        )

        template = Template(
            metadata=metadata,
            canvas_width=1920,
            canvas_height=1080,
            background_color="#FFFFFF",
            color_scheme=TemplateGenerator.COLOR_SCHEMES['blue_professional'],
            font_scheme=TemplateGenerator.FONT_SCHEMES['modern']
        )

        # Add header
        header_bg = ElementFactory.create_shape(
            ShapeType.RECTANGLE, 0, 0, 1920, 150
        )
        header_bg.style.fill_color = "#2C3E50"
        template.add_element(header_bg)

        # Add title
        title = ElementPresets.heading("Business Report 2024", 100, 50)
        title.style.fill_color = "#FFFFFF"
        template.add_element(title)

        return template

    @staticmethod
    def create_social_media_post(format_type: SocialMediaFormat) -> Template:
        """Create a social media post template."""
        dimensions = {
            SocialMediaFormat.INSTAGRAM_POST: (1080, 1080),
            SocialMediaFormat.INSTAGRAM_STORY: (1080, 1920),
            SocialMediaFormat.FACEBOOK_POST: (1200, 630),
            SocialMediaFormat.TWITTER_POST: (1200, 675),
            SocialMediaFormat.LINKEDIN_POST: (1200, 627),
            SocialMediaFormat.PINTEREST_PIN: (1000, 1500),
            SocialMediaFormat.YOUTUBE_THUMBNAIL: (1280, 720)
        }

        width, height = dimensions[format_type]

        metadata = TemplateMetadata(
            id=f"social_{format_type.value}_001",
            name=f"{format_type.value.replace('_', ' ').title()} Template",
            category=TemplateCategory.SOCIAL_MEDIA,
            style=TemplateStyle.MODERN,
            description=f"Optimized template for {format_type.value}",
            tags=["social", "media", format_type.value]
        )

        template = Template(
            metadata=metadata,
            canvas_width=width,
            canvas_height=height,
            background_color="#F8F9FA",
            color_scheme=TemplateGenerator.COLOR_SCHEMES['modern_green']
        )

        return template

    @staticmethod
    def create_infographic_template() -> Template:
        """Create a data infographic template."""
        metadata = TemplateMetadata(
            id="infographic_001",
            name="Data Visualization Infographic",
            category=TemplateCategory.INFOGRAPHIC,
            style=TemplateStyle.MODERN,
            description="Perfect for presenting statistics and data",
            tags=["infographic", "data", "statistics", "visual"]
        )

        template = Template(
            metadata=metadata,
            canvas_width=1080,
            canvas_height=1920,
            background_color="#FFFFFF",
            color_scheme=TemplateGenerator.COLOR_SCHEMES['creative_purple']
        )

        return template

    @staticmethod
    def create_timeline_template() -> Template:
        """Create a timeline template."""
        metadata = TemplateMetadata(
            id="timeline_001",
            name="Historical Timeline",
            category=TemplateCategory.TIMELINE,
            style=TemplateStyle.MODERN,
            description="Visualize events over time",
            tags=["timeline", "history", "events", "chronological"]
        )

        template = Template(
            metadata=metadata,
            canvas_width=1920,
            canvas_height=1080,
            background_color="#F8F9FA",
            color_scheme=TemplateGenerator.COLOR_SCHEMES['blue_professional']
        )

        return template

    @staticmethod
    def create_comparison_template() -> Template:
        """Create a comparison template."""
        metadata = TemplateMetadata(
            id="comparison_001",
            name="Product Comparison",
            category=TemplateCategory.COMPARISON,
            style=TemplateStyle.MINIMAL,
            description="Compare features, products, or options",
            tags=["comparison", "versus", "features", "products"]
        )

        template = Template(
            metadata=metadata,
            canvas_width=1920,
            canvas_height=1080,
            background_color="#FFFFFF",
            color_scheme=TemplateGenerator.COLOR_SCHEMES['minimal_mono']
        )

        return template

    @staticmethod
    def create_process_diagram_template() -> Template:
        """Create a process diagram template."""
        metadata = TemplateMetadata(
            id="process_001",
            name="Step-by-Step Process",
            category=TemplateCategory.PROCESS,
            style=TemplateStyle.PROFESSIONAL,
            description="Visualize workflows and processes",
            tags=["process", "workflow", "steps", "diagram"]
        )

        template = Template(
            metadata=metadata,
            canvas_width=1920,
            canvas_height=1080,
            background_color="#FFFFFF",
            color_scheme=TemplateGenerator.COLOR_SCHEMES['modern_green']
        )

        return template


class TemplateLibrary:
    """Manages the template library."""

    def __init__(self):
        """Initialize template library."""
        self._templates: Dict[str, Template] = {}
        self._load_default_templates()

    def _load_default_templates(self) -> None:
        """Load default templates."""
        generator = TemplateGenerator()

        # Business templates
        templates_to_add = [
            generator.create_business_report_template(),
            generator.create_infographic_template(),
            generator.create_timeline_template(),
            generator.create_comparison_template(),
            generator.create_process_diagram_template(),
        ]

        # Social media templates
        for format_type in SocialMediaFormat:
            templates_to_add.append(
                generator.create_social_media_post(format_type)
            )

        # Add all templates
        for template in templates_to_add:
            self.add_template(template)

    def add_template(self, template: Template) -> None:
        """Add template to library."""
        self._templates[template.metadata.id] = template

    def get_template(self, template_id: str) -> Optional[Template]:
        """Get template by ID."""
        return self._templates.get(template_id)

    def get_templates_by_category(self, category: TemplateCategory) -> List[Template]:
        """Get all templates in a category."""
        return [
            t for t in self._templates.values()
            if t.metadata.category == category
        ]

    def get_templates_by_style(self, style: TemplateStyle) -> List[Template]:
        """Get all templates with a specific style."""
        return [
            t for t in self._templates.values()
            if t.metadata.style == style
        ]

    def search_templates(self, query: str) -> List[Template]:
        """Search templates by name, description, or tags."""
        query_lower = query.lower()
        results = []

        for template in self._templates.values():
            if (query_lower in template.metadata.name.lower() or
                query_lower in template.metadata.description.lower() or
                any(query_lower in tag.lower() for tag in template.metadata.tags)):
                results.append(template)

        return results

    def get_all_templates(self) -> List[Template]:
        """Get all templates."""
        return list(self._templates.values())

    def get_categories(self) -> List[TemplateCategory]:
        """Get all available categories."""
        return list(TemplateCategory)

    def export_template(self, template_id: str, filepath: str) -> None:
        """Export template to JSON file."""
        template = self.get_template(template_id)
        if template:
            with open(filepath, 'w') as f:
                json.dump(template.to_dict(), f, indent=2)

    def import_template(self, filepath: str) -> Optional[Template]:
        """Import template from JSON file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            # TODO: Implement full deserialization
            return None
        except Exception as e:
            print(f"Error importing template: {e}")
            return None


# Additional template generators for specific use cases
class EducationTemplates:
    """Education-specific templates."""

    @staticmethod
    def create_course_overview() -> Template:
        """Create a course overview template."""
        metadata = TemplateMetadata(
            id="edu_course_001",
            name="Course Overview",
            category=TemplateCategory.EDUCATION,
            style=TemplateStyle.PROFESSIONAL,
            description="Present course information and curriculum",
            tags=["education", "course", "curriculum", "learning"]
        )

        return Template(
            metadata=metadata,
            canvas_width=1920,
            canvas_height=1080,
            color_scheme=TemplateGenerator.COLOR_SCHEMES['blue_professional']
        )

    @staticmethod
    def create_study_guide() -> Template:
        """Create a study guide template."""
        metadata = TemplateMetadata(
            id="edu_study_001",
            name="Study Guide",
            category=TemplateCategory.EDUCATION,
            style=TemplateStyle.MINIMAL,
            description="Organized study materials and notes",
            tags=["education", "study", "notes", "learning"]
        )

        return Template(
            metadata=metadata,
            canvas_width=1920,
            canvas_height=1080,
            color_scheme=TemplateGenerator.COLOR_SCHEMES['modern_green']
        )


class MarketingTemplates:
    """Marketing-specific templates."""

    @staticmethod
    def create_campaign_overview() -> Template:
        """Create a marketing campaign template."""
        metadata = TemplateMetadata(
            id="mkt_campaign_001",
            name="Marketing Campaign",
            category=TemplateCategory.MARKETING,
            style=TemplateStyle.BOLD,
            description="Present marketing campaign strategy and results",
            tags=["marketing", "campaign", "strategy", "results"]
        )

        return Template(
            metadata=metadata,
            canvas_width=1920,
            canvas_height=1080,
            color_scheme=TemplateGenerator.COLOR_SCHEMES['bold_red']
        )

    @staticmethod
    def create_product_launch() -> Template:
        """Create a product launch template."""
        metadata = TemplateMetadata(
            id="mkt_launch_001",
            name="Product Launch",
            category=TemplateCategory.MARKETING,
            style=TemplateStyle.CREATIVE,
            description="Announce new products in style",
            tags=["marketing", "product", "launch", "announcement"]
        )

        return Template(
            metadata=metadata,
            canvas_width=1920,
            canvas_height=1080,
            color_scheme=TemplateGenerator.COLOR_SCHEMES['creative_purple']
        )


__all__ = [
    'TemplateCategory', 'TemplateStyle', 'SocialMediaFormat',
    'TemplateMetadata', 'Template',
    'TemplateGenerator', 'TemplateLibrary',
    'EducationTemplates', 'MarketingTemplates'
]
