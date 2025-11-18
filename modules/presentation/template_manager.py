"""
Template Manager - Slide Template Library

Provides pre-designed templates for various presentation types including
business, education, marketing, and more.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import json


class TemplateCategory(Enum):
    """Template categories."""
    BUSINESS = "business"
    EDUCATION = "education"
    MARKETING = "marketing"
    CREATIVE = "creative"
    TECHNICAL = "technical"
    REPORT = "report"
    PITCH_DECK = "pitch_deck"
    INFOGRAPHIC = "infographic"
    PORTFOLIO = "portfolio"
    PHOTO_ALBUM = "photo_album"
    TIMELINE = "timeline"
    PROCESS = "process"
    COMPARISON = "comparison"
    AGENDA = "agenda"


@dataclass
class SlideTemplate:
    """Represents a slide template."""
    id: str
    name: str
    description: str
    category: TemplateCategory
    thumbnail: str = ""
    layout: Dict[str, Any] = field(default_factory=dict)
    elements: List[Dict[str, Any]] = field(default_factory=list)
    background: Dict[str, Any] = field(default_factory=dict)
    color_scheme: List[str] = field(default_factory=list)
    fonts: Dict[str, str] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "thumbnail": self.thumbnail,
            "layout": self.layout,
            "elements": self.elements,
            "background": self.background,
            "color_scheme": self.color_scheme,
            "fonts": self.fonts,
            "tags": self.tags,
        }


class TemplateManager:
    """
    Manages presentation templates.

    Features:
    - Pre-designed template library
    - Custom template creation
    - Template customization
    - Category-based organization
    - Search and filter
    """

    def __init__(self):
        """Initialize template manager."""
        self.templates: Dict[str, SlideTemplate] = {}
        self._init_default_templates()

    def _init_default_templates(self) -> None:
        """Initialize default template library."""

        # Business Templates
        self._add_template(SlideTemplate(
            id="business_title",
            name="Business Title Slide",
            description="Professional title slide for business presentations",
            category=TemplateCategory.BUSINESS,
            layout={"type": "title_slide"},
            elements=[
                {
                    "type": "text",
                    "content": "{{TITLE}}",
                    "position": {"x": 100, "y": 300},
                    "size": {"width": 1720, "height": 200},
                    "style": {
                        "font_family": "Arial",
                        "font_size": 60,
                        "color": "#1a1a1a",
                        "bold": True,
                        "align": "center"
                    }
                },
                {
                    "type": "text",
                    "content": "{{SUBTITLE}}",
                    "position": {"x": 100, "y": 520},
                    "size": {"width": 1720, "height": 100},
                    "style": {
                        "font_family": "Arial",
                        "font_size": 32,
                        "color": "#666666",
                        "align": "center"
                    }
                },
                {
                    "type": "shape",
                    "shape_type": "rectangle",
                    "position": {"x": 0, "y": 0},
                    "size": {"width": 1920, "height": 50},
                    "fill": {"type": "solid", "color": "#2E86AB"}
                }
            ],
            background={"type": "solid", "color": "#FFFFFF"},
            color_scheme=["#2E86AB", "#A23B72", "#F18F01", "#C73E1D"],
            fonts={"heading": "Arial", "body": "Arial"},
            tags=["business", "professional", "corporate"]
        ))

        self._add_template(SlideTemplate(
            id="business_content",
            name="Business Content Slide",
            description="Content slide with title and bullet points",
            category=TemplateCategory.BUSINESS,
            layout={"type": "title_content"},
            elements=[
                {
                    "type": "text",
                    "content": "{{TITLE}}",
                    "position": {"x": 80, "y": 60},
                    "size": {"width": 1760, "height": 100},
                    "style": {
                        "font_family": "Arial",
                        "font_size": 44,
                        "color": "#2E86AB",
                        "bold": True
                    }
                },
                {
                    "type": "text",
                    "content": "• {{POINT_1}}\n• {{POINT_2}}\n• {{POINT_3}}",
                    "position": {"x": 120, "y": 200},
                    "size": {"width": 1680, "height": 700},
                    "style": {
                        "font_family": "Arial",
                        "font_size": 28,
                        "color": "#333333",
                        "line_spacing": 1.5
                    }
                }
            ],
            background={"type": "solid", "color": "#FFFFFF"},
            color_scheme=["#2E86AB", "#A23B72", "#F18F01", "#C73E1D"],
            fonts={"heading": "Arial", "body": "Arial"},
            tags=["business", "content", "bullets"]
        ))

        # Education Templates
        self._add_template(SlideTemplate(
            id="education_lesson",
            name="Lesson Slide",
            description="Educational lesson slide with colorful design",
            category=TemplateCategory.EDUCATION,
            layout={"type": "title_content"},
            elements=[
                {
                    "type": "shape",
                    "shape_type": "rounded_rectangle",
                    "position": {"x": 50, "y": 40},
                    "size": {"width": 1820, "height": 120},
                    "fill": {"type": "gradient", "gradient_colors": ["#667eea", "#764ba2"]},
                    "border": {"rounded_corners": 20}
                },
                {
                    "type": "text",
                    "content": "{{LESSON_TITLE}}",
                    "position": {"x": 100, "y": 60},
                    "size": {"width": 1720, "height": 80},
                    "style": {
                        "font_family": "Comic Sans MS",
                        "font_size": 48,
                        "color": "#FFFFFF",
                        "bold": True,
                        "align": "center"
                    }
                },
                {
                    "type": "text",
                    "content": "{{CONTENT}}",
                    "position": {"x": 100, "y": 220},
                    "size": {"width": 1720, "height": 700},
                    "style": {
                        "font_family": "Arial",
                        "font_size": 32,
                        "color": "#333333",
                        "line_spacing": 1.6
                    }
                }
            ],
            background={"type": "solid", "color": "#F7F7F7"},
            color_scheme=["#667eea", "#764ba2", "#f093fb", "#4facfe"],
            fonts={"heading": "Comic Sans MS", "body": "Arial"},
            tags=["education", "learning", "colorful"]
        ))

        # Marketing Templates
        self._add_template(SlideTemplate(
            id="marketing_hero",
            name="Marketing Hero Slide",
            description="Eye-catching hero slide for marketing presentations",
            category=TemplateCategory.MARKETING,
            layout={"type": "title_slide"},
            elements=[
                {
                    "type": "shape",
                    "shape_type": "circle",
                    "position": {"x": 1200, "y": 200},
                    "size": {"width": 600, "height": 600},
                    "fill": {"type": "solid", "color": "#FF6B6B", "opacity": 0.3}
                },
                {
                    "type": "text",
                    "content": "{{HEADLINE}}",
                    "position": {"x": 100, "y": 300},
                    "size": {"width": 1000, "height": 300},
                    "style": {
                        "font_family": "Impact",
                        "font_size": 72,
                        "color": "#2C3E50",
                        "bold": True,
                        "line_spacing": 1.2
                    }
                },
                {
                    "type": "text",
                    "content": "{{TAGLINE}}",
                    "position": {"x": 100, "y": 650},
                    "size": {"width": 800, "height": 100},
                    "style": {
                        "font_family": "Arial",
                        "font_size": 36,
                        "color": "#7F8C8D"
                    }
                }
            ],
            background={"type": "solid", "color": "#FFFFFF"},
            color_scheme=["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A"],
            fonts={"heading": "Impact", "body": "Arial"},
            tags=["marketing", "hero", "bold"]
        ))

        # Pitch Deck Templates
        self._add_template(SlideTemplate(
            id="pitch_problem",
            name="Problem Statement",
            description="Pitch deck problem statement slide",
            category=TemplateCategory.PITCH_DECK,
            layout={"type": "title_content"},
            elements=[
                {
                    "type": "text",
                    "content": "The Problem",
                    "position": {"x": 100, "y": 80},
                    "size": {"width": 400, "height": 80},
                    "style": {
                        "font_family": "Helvetica",
                        "font_size": 48,
                        "color": "#E74C3C",
                        "bold": True
                    }
                },
                {
                    "type": "shape",
                    "shape_type": "rectangle",
                    "position": {"x": 100, "y": 170},
                    "size": {"width": 150, "height": 8},
                    "fill": {"type": "solid", "color": "#E74C3C"}
                },
                {
                    "type": "text",
                    "content": "{{PROBLEM_DESCRIPTION}}",
                    "position": {"x": 100, "y": 250},
                    "size": {"width": 1720, "height": 650},
                    "style": {
                        "font_family": "Helvetica",
                        "font_size": 36,
                        "color": "#2C3E50",
                        "line_spacing": 1.8
                    }
                }
            ],
            background={"type": "solid", "color": "#FAFAFA"},
            color_scheme=["#E74C3C", "#3498DB", "#2ECC71", "#F39C12"],
            fonts={"heading": "Helvetica", "body": "Helvetica"},
            tags=["pitch", "startup", "problem"]
        ))

        self._add_template(SlideTemplate(
            id="pitch_solution",
            name="Solution Slide",
            description="Pitch deck solution slide",
            category=TemplateCategory.PITCH_DECK,
            layout={"type": "title_content"},
            elements=[
                {
                    "type": "text",
                    "content": "Our Solution",
                    "position": {"x": 100, "y": 80},
                    "size": {"width": 500, "height": 80},
                    "style": {
                        "font_family": "Helvetica",
                        "font_size": 48,
                        "color": "#2ECC71",
                        "bold": True
                    }
                },
                {
                    "type": "shape",
                    "shape_type": "rectangle",
                    "position": {"x": 100, "y": 170},
                    "size": {"width": 150, "height": 8},
                    "fill": {"type": "solid", "color": "#2ECC71"}
                },
                {
                    "type": "text",
                    "content": "{{SOLUTION_DESCRIPTION}}",
                    "position": {"x": 100, "y": 250},
                    "size": {"width": 1720, "height": 650},
                    "style": {
                        "font_family": "Helvetica",
                        "font_size": 36,
                        "color": "#2C3E50",
                        "line_spacing": 1.8
                    }
                }
            ],
            background={"type": "solid", "color": "#FAFAFA"},
            color_scheme=["#2ECC71", "#3498DB", "#E74C3C", "#F39C12"],
            fonts={"heading": "Helvetica", "body": "Helvetica"},
            tags=["pitch", "startup", "solution"]
        ))

        # Infographic Templates
        self._add_template(SlideTemplate(
            id="infographic_stats",
            name="Statistics Infographic",
            description="Infographic slide for displaying key statistics",
            category=TemplateCategory.INFOGRAPHIC,
            layout={"type": "content_only"},
            elements=[
                {
                    "type": "shape",
                    "shape_type": "circle",
                    "position": {"x": 200, "y": 300},
                    "size": {"width": 250, "height": 250},
                    "fill": {"type": "solid", "color": "#3498DB"}
                },
                {
                    "type": "text",
                    "content": "{{STAT_1}}",
                    "position": {"x": 200, "y": 370},
                    "size": {"width": 250, "height": 120},
                    "style": {
                        "font_family": "Arial",
                        "font_size": 60,
                        "color": "#FFFFFF",
                        "bold": True,
                        "align": "center"
                    }
                },
                {
                    "type": "shape",
                    "shape_type": "circle",
                    "position": {"x": 835, "y": 300},
                    "size": {"width": 250, "height": 250},
                    "fill": {"type": "solid", "color": "#E74C3C"}
                },
                {
                    "type": "text",
                    "content": "{{STAT_2}}",
                    "position": {"x": 835, "y": 370},
                    "size": {"width": 250, "height": 120},
                    "style": {
                        "font_family": "Arial",
                        "font_size": 60,
                        "color": "#FFFFFF",
                        "bold": True,
                        "align": "center"
                    }
                },
                {
                    "type": "shape",
                    "shape_type": "circle",
                    "position": {"x": 1470, "y": 300},
                    "size": {"width": 250, "height": 250},
                    "fill": {"type": "solid", "color": "#2ECC71"}
                },
                {
                    "type": "text",
                    "content": "{{STAT_3}}",
                    "position": {"x": 1470, "y": 370},
                    "size": {"width": 250, "height": 120},
                    "style": {
                        "font_family": "Arial",
                        "font_size": 60,
                        "color": "#FFFFFF",
                        "bold": True,
                        "align": "center"
                    }
                }
            ],
            background={"type": "solid", "color": "#FFFFFF"},
            color_scheme=["#3498DB", "#E74C3C", "#2ECC71", "#F39C12"],
            fonts={"heading": "Arial", "body": "Arial"},
            tags=["infographic", "stats", "data"]
        ))

        # Timeline Templates
        self._add_template(SlideTemplate(
            id="timeline_horizontal",
            name="Horizontal Timeline",
            description="Horizontal timeline for project milestones",
            category=TemplateCategory.TIMELINE,
            layout={"type": "content_only"},
            elements=[
                {
                    "type": "shape",
                    "shape_type": "rectangle",
                    "position": {"x": 100, "y": 530},
                    "size": {"width": 1720, "height": 20},
                    "fill": {"type": "solid", "color": "#34495E"}
                },
                {
                    "type": "shape",
                    "shape_type": "circle",
                    "position": {"x": 280, "y": 500},
                    "size": {"width": 80, "height": 80},
                    "fill": {"type": "solid", "color": "#3498DB"}
                },
                {
                    "type": "text",
                    "content": "{{MILESTONE_1}}",
                    "position": {"x": 200, "y": 620},
                    "size": {"width": 240, "height": 150},
                    "style": {
                        "font_family": "Arial",
                        "font_size": 20,
                        "color": "#2C3E50",
                        "align": "center"
                    }
                },
                {
                    "type": "shape",
                    "shape_type": "circle",
                    "position": {"x": 710, "y": 500},
                    "size": {"width": 80, "height": 80},
                    "fill": {"type": "solid", "color": "#E74C3C"}
                },
                {
                    "type": "text",
                    "content": "{{MILESTONE_2}}",
                    "position": {"x": 630, "y": 620},
                    "size": {"width": 240, "height": 150},
                    "style": {
                        "font_family": "Arial",
                        "font_size": 20,
                        "color": "#2C3E50",
                        "align": "center"
                    }
                },
                {
                    "type": "shape",
                    "shape_type": "circle",
                    "position": {"x": 1140, "y": 500},
                    "size": {"width": 80, "height": 80},
                    "fill": {"type": "solid", "color": "#2ECC71"}
                },
                {
                    "type": "text",
                    "content": "{{MILESTONE_3}}",
                    "position": {"x": 1060, "y": 620},
                    "size": {"width": 240, "height": 150},
                    "style": {
                        "font_family": "Arial",
                        "font_size": 20,
                        "color": "#2C3E50",
                        "align": "center"
                    }
                },
                {
                    "type": "shape",
                    "shape_type": "circle",
                    "position": {"x": 1570, "y": 500},
                    "size": {"width": 80, "height": 80},
                    "fill": {"type": "solid", "color": "#F39C12"}
                },
                {
                    "type": "text",
                    "content": "{{MILESTONE_4}}",
                    "position": {"x": 1490, "y": 620},
                    "size": {"width": 240, "height": 150},
                    "style": {
                        "font_family": "Arial",
                        "font_size": 20,
                        "color": "#2C3E50",
                        "align": "center"
                    }
                }
            ],
            background={"type": "solid", "color": "#FFFFFF"},
            color_scheme=["#3498DB", "#E74C3C", "#2ECC71", "#F39C12"],
            fonts={"heading": "Arial", "body": "Arial"},
            tags=["timeline", "roadmap", "milestones"]
        ))

        # Comparison Templates
        self._add_template(SlideTemplate(
            id="comparison_two_column",
            name="Two-Column Comparison",
            description="Side-by-side comparison slide",
            category=TemplateCategory.COMPARISON,
            layout={"type": "two_content"},
            elements=[
                {
                    "type": "shape",
                    "shape_type": "rectangle",
                    "position": {"x": 100, "y": 100},
                    "size": {"width": 800, "height": 850},
                    "fill": {"type": "solid", "color": "#ECF0F1"},
                    "border": {"color": "#3498DB", "width": 3}
                },
                {
                    "type": "text",
                    "content": "{{OPTION_A}}",
                    "position": {"x": 150, "y": 150},
                    "size": {"width": 700, "height": 700},
                    "style": {
                        "font_family": "Arial",
                        "font_size": 28,
                        "color": "#2C3E50",
                        "line_spacing": 1.6
                    }
                },
                {
                    "type": "shape",
                    "shape_type": "rectangle",
                    "position": {"x": 1020, "y": 100},
                    "size": {"width": 800, "height": 850},
                    "fill": {"type": "solid", "color": "#ECF0F1"},
                    "border": {"color": "#E74C3C", "width": 3}
                },
                {
                    "type": "text",
                    "content": "{{OPTION_B}}",
                    "position": {"x": 1070, "y": 150},
                    "size": {"width": 700, "height": 700},
                    "style": {
                        "font_family": "Arial",
                        "font_size": 28,
                        "color": "#2C3E50",
                        "line_spacing": 1.6
                    }
                }
            ],
            background={"type": "solid", "color": "#FFFFFF"},
            color_scheme=["#3498DB", "#E74C3C", "#2ECC71", "#F39C12"],
            fonts={"heading": "Arial", "body": "Arial"},
            tags=["comparison", "vs", "options"]
        ))

    def _add_template(self, template: SlideTemplate) -> None:
        """Add template to library."""
        self.templates[template.id] = template

    def get_template(self, template_id: str) -> Optional[SlideTemplate]:
        """Get template by ID."""
        return self.templates.get(template_id)

    def get_templates_by_category(
        self,
        category: TemplateCategory
    ) -> List[SlideTemplate]:
        """Get all templates in a category."""
        return [
            template for template in self.templates.values()
            if template.category == category
        ]

    def get_all_templates(self) -> List[SlideTemplate]:
        """Get all templates."""
        return list(self.templates.values())

    def search_templates(self, query: str) -> List[SlideTemplate]:
        """Search templates by name, description, or tags."""
        query = query.lower()
        results = []

        for template in self.templates.values():
            if (query in template.name.lower() or
                query in template.description.lower() or
                any(query in tag.lower() for tag in template.tags)):
                results.append(template)

        return results

    def get_categories(self) -> List[TemplateCategory]:
        """Get all available categories."""
        return list(TemplateCategory)

    def create_custom_template(
        self,
        name: str,
        description: str,
        category: TemplateCategory,
        elements: List[Dict[str, Any]],
        background: Dict[str, Any],
        color_scheme: Optional[List[str]] = None,
        fonts: Optional[Dict[str, str]] = None,
        tags: Optional[List[str]] = None
    ) -> SlideTemplate:
        """Create a custom template."""
        import hashlib
        template_id = hashlib.md5(name.encode()).hexdigest()[:12]

        template = SlideTemplate(
            id=f"custom_{template_id}",
            name=name,
            description=description,
            category=category,
            elements=elements,
            background=background,
            color_scheme=color_scheme or [],
            fonts=fonts or {},
            tags=tags or []
        )

        self.templates[template.id] = template
        return template

    def delete_template(self, template_id: str) -> bool:
        """Delete a custom template."""
        if template_id.startswith("custom_") and template_id in self.templates:
            del self.templates[template_id]
            return True
        return False

    def apply_template(
        self,
        template_id: str,
        replacements: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Apply template and replace placeholders.

        Args:
            template_id: Template to apply
            replacements: Dictionary of placeholder replacements

        Returns:
            Slide data with template applied
        """
        template = self.get_template(template_id)
        if not template:
            return None

        replacements = replacements or {}

        # Deep copy elements and replace placeholders
        elements = json.loads(json.dumps(template.elements))

        for element in elements:
            if element.get("type") == "text" and "content" in element:
                content = element["content"]
                for placeholder, value in replacements.items():
                    content = content.replace(f"{{{{{placeholder}}}}}", value)
                element["content"] = content

        return {
            "elements": elements,
            "background": template.background.copy(),
            "color_scheme": template.color_scheme.copy(),
            "fonts": template.fonts.copy(),
        }

    def get_template_preview(self, template_id: str) -> Optional[str]:
        """Get template preview/thumbnail."""
        template = self.get_template(template_id)
        if template:
            return template.thumbnail
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "templates": {
                tid: template.to_dict()
                for tid, template in self.templates.items()
                if tid.startswith("custom_")  # Only save custom templates
            }
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load custom templates from dictionary."""
        for tid, template_data in data.get("templates", {}).items():
            template = SlideTemplate(
                id=template_data["id"],
                name=template_data["name"],
                description=template_data["description"],
                category=TemplateCategory(template_data["category"]),
                thumbnail=template_data.get("thumbnail", ""),
                layout=template_data.get("layout", {}),
                elements=template_data.get("elements", []),
                background=template_data.get("background", {}),
                color_scheme=template_data.get("color_scheme", []),
                fonts=template_data.get("fonts", {}),
                tags=template_data.get("tags", [])
            )
            self.templates[tid] = template
