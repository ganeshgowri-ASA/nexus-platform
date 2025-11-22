"""
Template Manager - 50+ professional website templates
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import json


class TemplateCategory(Enum):
    """Template categories"""
    BUSINESS = "business"
    PORTFOLIO = "portfolio"
    BLOG = "blog"
    ECOMMERCE = "ecommerce"
    LANDING_PAGE = "landing_page"
    AGENCY = "agency"
    RESTAURANT = "restaurant"
    EDUCATION = "education"
    HEALTH = "health"
    REAL_ESTATE = "real_estate"
    EVENTS = "events"
    NONPROFIT = "nonprofit"
    PERSONAL = "personal"
    TECHNOLOGY = "technology"


@dataclass
class TemplateSection:
    """Template section definition"""
    section_id: str
    section_type: str
    components: List[Dict[str, Any]]
    order: int


@dataclass
class Template:
    """Template definition"""
    template_id: str
    name: str
    category: TemplateCategory
    description: str
    preview_image: str
    tags: List[str]
    sections: List[TemplateSection]
    color_scheme: Dict[str, str]
    fonts: Dict[str, str]
    is_premium: bool = False
    is_responsive: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "preview_image": self.preview_image,
            "tags": self.tags,
            "sections": [
                {
                    "section_id": s.section_id,
                    "section_type": s.section_type,
                    "components": s.components,
                    "order": s.order,
                }
                for s in self.sections
            ],
            "color_scheme": self.color_scheme,
            "fonts": self.fonts,
            "is_premium": self.is_premium,
            "is_responsive": self.is_responsive,
        }


class TemplateManager:
    """Manager for website templates"""

    def __init__(self):
        self.templates: Dict[str, Template] = {}
        self._initialize_templates()

    def _initialize_templates(self) -> None:
        """Initialize all templates"""
        self._add_business_templates()
        self._add_portfolio_templates()
        self._add_blog_templates()
        self._add_ecommerce_templates()
        self._add_landing_page_templates()
        self._add_agency_templates()
        self._add_restaurant_templates()
        self._add_education_templates()
        self._add_health_templates()
        self._add_real_estate_templates()
        self._add_events_templates()
        self._add_nonprofit_templates()
        self._add_personal_templates()
        self._add_technology_templates()

    def _add_business_templates(self) -> None:
        """Add business templates"""
        # Corporate Business
        self.templates["corporate_business"] = Template(
            template_id="corporate_business",
            name="Corporate Business",
            category=TemplateCategory.BUSINESS,
            description="Professional corporate website with hero, services, and team sections",
            preview_image="/templates/corporate_business.jpg",
            tags=["corporate", "professional", "services"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("services", "features_grid", [], 3),
                TemplateSection("about", "content", [], 4),
                TemplateSection("team", "team", [], 5),
                TemplateSection("contact", "contact", [], 6),
                TemplateSection("footer", "footer", [], 7),
            ],
            color_scheme={
                "primary": "#1a237e",
                "secondary": "#0d47a1",
                "accent": "#2196f3",
                "background": "#ffffff",
                "text": "#333333",
            },
            fonts={
                "heading": "Montserrat",
                "body": "Open Sans",
            },
        )

        # Startup
        self.templates["startup"] = Template(
            template_id="startup",
            name="Startup",
            category=TemplateCategory.BUSINESS,
            description="Modern startup landing page with bold design",
            preview_image="/templates/startup.jpg",
            tags=["startup", "modern", "tech"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("features", "features_grid", [], 3),
                TemplateSection("pricing", "pricing", [], 4),
                TemplateSection("cta", "hero", [], 5),
                TemplateSection("footer", "footer", [], 6),
            ],
            color_scheme={
                "primary": "#6200ea",
                "secondary": "#b388ff",
                "accent": "#00e676",
                "background": "#fafafa",
                "text": "#212121",
            },
            fonts={
                "heading": "Poppins",
                "body": "Inter",
            },
        )

        # Consulting
        self.templates["consulting"] = Template(
            template_id="consulting",
            name="Consulting",
            category=TemplateCategory.BUSINESS,
            description="Professional consulting firm website",
            preview_image="/templates/consulting.jpg",
            tags=["consulting", "professional", "advisory"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("services", "features_grid", [], 3),
                TemplateSection("expertise", "content", [], 4),
                TemplateSection("testimonials", "testimonials", [], 5),
                TemplateSection("contact", "contact", [], 6),
                TemplateSection("footer", "footer", [], 7),
            ],
            color_scheme={
                "primary": "#263238",
                "secondary": "#37474f",
                "accent": "#ff6f00",
                "background": "#ffffff",
                "text": "#212121",
            },
            fonts={
                "heading": "Roboto",
                "body": "Lato",
            },
        )

        # Small Business
        self.templates["small_business"] = Template(
            template_id="small_business",
            name="Small Business",
            category=TemplateCategory.BUSINESS,
            description="Simple and effective small business website",
            preview_image="/templates/small_business.jpg",
            tags=["small business", "simple", "local"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("about", "content", [], 3),
                TemplateSection("services", "features_grid", [], 4),
                TemplateSection("contact", "contact", [], 5),
                TemplateSection("footer", "footer", [], 6),
            ],
            color_scheme={
                "primary": "#00695c",
                "secondary": "#00897b",
                "accent": "#ffc107",
                "background": "#ffffff",
                "text": "#424242",
            },
            fonts={
                "heading": "Raleway",
                "body": "Source Sans Pro",
            },
        )

    def _add_portfolio_templates(self) -> None:
        """Add portfolio templates"""
        # Creative Portfolio
        self.templates["creative_portfolio"] = Template(
            template_id="creative_portfolio",
            name="Creative Portfolio",
            category=TemplateCategory.PORTFOLIO,
            description="Stunning portfolio for creative professionals",
            preview_image="/templates/creative_portfolio.jpg",
            tags=["portfolio", "creative", "designer"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("gallery", "gallery", [], 3),
                TemplateSection("about", "content", [], 4),
                TemplateSection("contact", "contact", [], 5),
                TemplateSection("footer", "footer", [], 6),
            ],
            color_scheme={
                "primary": "#212121",
                "secondary": "#424242",
                "accent": "#ff4081",
                "background": "#fafafa",
                "text": "#212121",
            },
            fonts={
                "heading": "Playfair Display",
                "body": "Roboto",
            },
        )

        # Developer Portfolio
        self.templates["developer_portfolio"] = Template(
            template_id="developer_portfolio",
            name="Developer Portfolio",
            category=TemplateCategory.PORTFOLIO,
            description="Clean portfolio for developers and programmers",
            preview_image="/templates/developer_portfolio.jpg",
            tags=["portfolio", "developer", "tech"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("skills", "features_grid", [], 3),
                TemplateSection("projects", "gallery", [], 4),
                TemplateSection("about", "content", [], 5),
                TemplateSection("contact", "contact", [], 6),
                TemplateSection("footer", "footer", [], 7),
            ],
            color_scheme={
                "primary": "#0d1117",
                "secondary": "#161b22",
                "accent": "#58a6ff",
                "background": "#ffffff",
                "text": "#24292e",
            },
            fonts={
                "heading": "JetBrains Mono",
                "body": "Inter",
            },
        )

        # Photography Portfolio
        self.templates["photography_portfolio"] = Template(
            template_id="photography_portfolio",
            name="Photography Portfolio",
            category=TemplateCategory.PORTFOLIO,
            description="Elegant portfolio for photographers",
            preview_image="/templates/photography_portfolio.jpg",
            tags=["portfolio", "photography", "visual"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("gallery", "gallery", [], 3),
                TemplateSection("services", "features_grid", [], 4),
                TemplateSection("contact", "contact", [], 5),
                TemplateSection("footer", "footer", [], 6),
            ],
            color_scheme={
                "primary": "#000000",
                "secondary": "#333333",
                "accent": "#ffffff",
                "background": "#ffffff",
                "text": "#212121",
            },
            fonts={
                "heading": "Cormorant Garamond",
                "body": "Lora",
            },
        )

        # Minimalist Portfolio
        self.templates["minimalist_portfolio"] = Template(
            template_id="minimalist_portfolio",
            name="Minimalist Portfolio",
            category=TemplateCategory.PORTFOLIO,
            description="Clean and minimal portfolio design",
            preview_image="/templates/minimalist_portfolio.jpg",
            tags=["portfolio", "minimal", "clean"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("work", "gallery", [], 3),
                TemplateSection("about", "content", [], 4),
                TemplateSection("footer", "footer", [], 5),
            ],
            color_scheme={
                "primary": "#ffffff",
                "secondary": "#f5f5f5",
                "accent": "#000000",
                "background": "#ffffff",
                "text": "#333333",
            },
            fonts={
                "heading": "Work Sans",
                "body": "Work Sans",
            },
        )

    def _add_blog_templates(self) -> None:
        """Add blog templates"""
        # Personal Blog
        self.templates["personal_blog"] = Template(
            template_id="personal_blog",
            name="Personal Blog",
            category=TemplateCategory.BLOG,
            description="Beautiful personal blog layout",
            preview_image="/templates/personal_blog.jpg",
            tags=["blog", "personal", "writing"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("posts", "content", [], 3),
                TemplateSection("sidebar", "sidebar_menu", [], 4),
                TemplateSection("footer", "footer", [], 5),
            ],
            color_scheme={
                "primary": "#2c3e50",
                "secondary": "#34495e",
                "accent": "#e74c3c",
                "background": "#ecf0f1",
                "text": "#2c3e50",
            },
            fonts={
                "heading": "Merriweather",
                "body": "Georgia",
            },
        )

        # Magazine Blog
        self.templates["magazine_blog"] = Template(
            template_id="magazine_blog",
            name="Magazine Blog",
            category=TemplateCategory.BLOG,
            description="Magazine-style blog layout",
            preview_image="/templates/magazine_blog.jpg",
            tags=["blog", "magazine", "news"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("featured", "hero", [], 2),
                TemplateSection("articles", "content", [], 3),
                TemplateSection("categories", "sidebar_menu", [], 4),
                TemplateSection("footer", "footer", [], 5),
            ],
            color_scheme={
                "primary": "#c0392b",
                "secondary": "#e74c3c",
                "accent": "#2c3e50",
                "background": "#ffffff",
                "text": "#212121",
            },
            fonts={
                "heading": "Oswald",
                "body": "Roboto",
            },
        )

        # Tech Blog
        self.templates["tech_blog"] = Template(
            template_id="tech_blog",
            name="Tech Blog",
            category=TemplateCategory.BLOG,
            description="Modern tech blog design",
            preview_image="/templates/tech_blog.jpg",
            tags=["blog", "tech", "technology"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("posts", "content", [], 3),
                TemplateSection("categories", "sidebar_menu", [], 4),
                TemplateSection("newsletter", "contact", [], 5),
                TemplateSection("footer", "footer", [], 6),
            ],
            color_scheme={
                "primary": "#0066cc",
                "secondary": "#0080ff",
                "accent": "#00ccff",
                "background": "#f8f9fa",
                "text": "#212529",
            },
            fonts={
                "heading": "Nunito",
                "body": "Source Sans Pro",
            },
        )

    def _add_ecommerce_templates(self) -> None:
        """Add e-commerce templates"""
        # Fashion Store
        self.templates["fashion_store"] = Template(
            template_id="fashion_store",
            name="Fashion Store",
            category=TemplateCategory.ECOMMERCE,
            description="Elegant online fashion store",
            preview_image="/templates/fashion_store.jpg",
            tags=["ecommerce", "fashion", "store"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("products", "gallery", [], 3),
                TemplateSection("categories", "features_grid", [], 4),
                TemplateSection("testimonials", "testimonials", [], 5),
                TemplateSection("footer", "footer", [], 6),
            ],
            color_scheme={
                "primary": "#000000",
                "secondary": "#1a1a1a",
                "accent": "#d4af37",
                "background": "#ffffff",
                "text": "#333333",
            },
            fonts={
                "heading": "Didot",
                "body": "Helvetica",
            },
        )

        # Electronics Store
        self.templates["electronics_store"] = Template(
            template_id="electronics_store",
            name="Electronics Store",
            category=TemplateCategory.ECOMMERCE,
            description="Modern electronics e-commerce site",
            preview_image="/templates/electronics_store.jpg",
            tags=["ecommerce", "electronics", "gadgets"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("featured_products", "gallery", [], 3),
                TemplateSection("categories", "features_grid", [], 4),
                TemplateSection("deals", "content", [], 5),
                TemplateSection("footer", "footer", [], 6),
            ],
            color_scheme={
                "primary": "#0066cc",
                "secondary": "#004c99",
                "accent": "#ff9900",
                "background": "#f3f4f6",
                "text": "#1a1a1a",
            },
            fonts={
                "heading": "Roboto",
                "body": "Arial",
            },
        )

        # Handmade/Craft Store
        self.templates["handmade_store"] = Template(
            template_id="handmade_store",
            name="Handmade Store",
            category=TemplateCategory.ECOMMERCE,
            description="Artisan and handmade products store",
            preview_image="/templates/handmade_store.jpg",
            tags=["ecommerce", "handmade", "crafts"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("products", "gallery", [], 3),
                TemplateSection("about", "content", [], 4),
                TemplateSection("testimonials", "testimonials", [], 5),
                TemplateSection("footer", "footer", [], 6),
            ],
            color_scheme={
                "primary": "#8b4513",
                "secondary": "#a0522d",
                "accent": "#daa520",
                "background": "#faf8f3",
                "text": "#4a4a4a",
            },
            fonts={
                "heading": "Libre Baskerville",
                "body": "Crimson Text",
            },
        )

    def _add_landing_page_templates(self) -> None:
        """Add landing page templates"""
        # SaaS Landing
        self.templates["saas_landing"] = Template(
            template_id="saas_landing",
            name="SaaS Landing",
            category=TemplateCategory.LANDING_PAGE,
            description="High-converting SaaS landing page",
            preview_image="/templates/saas_landing.jpg",
            tags=["landing", "saas", "software"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("features", "features_grid", [], 3),
                TemplateSection("benefits", "content", [], 4),
                TemplateSection("pricing", "pricing", [], 5),
                TemplateSection("testimonials", "testimonials", [], 6),
                TemplateSection("cta", "hero", [], 7),
                TemplateSection("footer", "footer", [], 8),
            ],
            color_scheme={
                "primary": "#667eea",
                "secondary": "#764ba2",
                "accent": "#f093fb",
                "background": "#ffffff",
                "text": "#1a202c",
            },
            fonts={
                "heading": "Inter",
                "body": "Inter",
            },
        )

        # App Landing
        self.templates["app_landing"] = Template(
            template_id="app_landing",
            name="App Landing",
            category=TemplateCategory.LANDING_PAGE,
            description="Mobile app landing page",
            preview_image="/templates/app_landing.jpg",
            tags=["landing", "app", "mobile"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("features", "features_grid", [], 3),
                TemplateSection("screenshots", "gallery", [], 4),
                TemplateSection("download", "hero", [], 5),
                TemplateSection("footer", "footer", [], 6),
            ],
            color_scheme={
                "primary": "#6366f1",
                "secondary": "#8b5cf6",
                "accent": "#ec4899",
                "background": "#f9fafb",
                "text": "#111827",
            },
            fonts={
                "heading": "Poppins",
                "body": "Open Sans",
            },
        )

        # Product Launch
        self.templates["product_launch"] = Template(
            template_id="product_launch",
            name="Product Launch",
            category=TemplateCategory.LANDING_PAGE,
            description="Exciting product launch landing page",
            preview_image="/templates/product_launch.jpg",
            tags=["landing", "product", "launch"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("countdown", "content", [], 3),
                TemplateSection("features", "features_grid", [], 4),
                TemplateSection("early_access", "contact", [], 5),
                TemplateSection("footer", "footer", [], 6),
            ],
            color_scheme={
                "primary": "#ff6b6b",
                "secondary": "#ee5a6f",
                "accent": "#4ecdc4",
                "background": "#ffffff",
                "text": "#2d3436",
            },
            fonts={
                "heading": "Montserrat",
                "body": "Lato",
            },
        )

        # Webinar Landing
        self.templates["webinar_landing"] = Template(
            template_id="webinar_landing",
            name="Webinar Landing",
            category=TemplateCategory.LANDING_PAGE,
            description="Webinar registration landing page",
            preview_image="/templates/webinar_landing.jpg",
            tags=["landing", "webinar", "event"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("speakers", "team", [], 3),
                TemplateSection("agenda", "content", [], 4),
                TemplateSection("registration", "contact", [], 5),
                TemplateSection("footer", "footer", [], 6),
            ],
            color_scheme={
                "primary": "#1e3a8a",
                "secondary": "#1e40af",
                "accent": "#3b82f6",
                "background": "#f8fafc",
                "text": "#0f172a",
            },
            fonts={
                "heading": "Raleway",
                "body": "Roboto",
            },
        )

    def _add_agency_templates(self) -> None:
        """Add agency templates"""
        # Creative Agency
        self.templates["creative_agency"] = Template(
            template_id="creative_agency",
            name="Creative Agency",
            category=TemplateCategory.AGENCY,
            description="Bold creative agency website",
            preview_image="/templates/creative_agency.jpg",
            tags=["agency", "creative", "design"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("services", "features_grid", [], 3),
                TemplateSection("portfolio", "gallery", [], 4),
                TemplateSection("team", "team", [], 5),
                TemplateSection("contact", "contact", [], 6),
                TemplateSection("footer", "footer", [], 7),
            ],
            color_scheme={
                "primary": "#ff385c",
                "secondary": "#ff5a5f",
                "accent": "#00a699",
                "background": "#ffffff",
                "text": "#484848",
            },
            fonts={
                "heading": "Bebas Neue",
                "body": "Open Sans",
            },
        )

        # Digital Agency
        self.templates["digital_agency"] = Template(
            template_id="digital_agency",
            name="Digital Agency",
            category=TemplateCategory.AGENCY,
            description="Modern digital marketing agency",
            preview_image="/templates/digital_agency.jpg",
            tags=["agency", "digital", "marketing"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("services", "features_grid", [], 3),
                TemplateSection("case_studies", "gallery", [], 4),
                TemplateSection("testimonials", "testimonials", [], 5),
                TemplateSection("contact", "contact", [], 6),
                TemplateSection("footer", "footer", [], 7),
            ],
            color_scheme={
                "primary": "#6f42c1",
                "secondary": "#7952b3",
                "accent": "#20c997",
                "background": "#f8f9fa",
                "text": "#212529",
            },
            fonts={
                "heading": "Poppins",
                "body": "Inter",
            },
        )

    def _add_restaurant_templates(self) -> None:
        """Add restaurant templates"""
        # Fine Dining
        self.templates["fine_dining"] = Template(
            template_id="fine_dining",
            name="Fine Dining",
            category=TemplateCategory.RESTAURANT,
            description="Elegant fine dining restaurant",
            preview_image="/templates/fine_dining.jpg",
            tags=["restaurant", "dining", "elegant"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("menu", "content", [], 3),
                TemplateSection("gallery", "gallery", [], 4),
                TemplateSection("reservations", "contact", [], 5),
                TemplateSection("footer", "footer", [], 6),
            ],
            color_scheme={
                "primary": "#2c2416",
                "secondary": "#3d3020",
                "accent": "#d4af37",
                "background": "#fdfbf7",
                "text": "#2c2416",
            },
            fonts={
                "heading": "Playfair Display",
                "body": "Lora",
            },
        )

        # Cafe
        self.templates["cafe"] = Template(
            template_id="cafe",
            name="Cafe",
            category=TemplateCategory.RESTAURANT,
            description="Cozy cafe website",
            preview_image="/templates/cafe.jpg",
            tags=["restaurant", "cafe", "coffee"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("menu", "content", [], 3),
                TemplateSection("about", "content", [], 4),
                TemplateSection("location", "contact", [], 5),
                TemplateSection("footer", "footer", [], 6),
            ],
            color_scheme={
                "primary": "#6f4e37",
                "secondary": "#8b6f47",
                "accent": "#d2691e",
                "background": "#faf8f5",
                "text": "#4a4a4a",
            },
            fonts={
                "heading": "Pacifico",
                "body": "Merriweather",
            },
        )

    def _add_education_templates(self) -> None:
        """Add education templates"""
        # Online Course
        self.templates["online_course"] = Template(
            template_id="online_course",
            name="Online Course",
            category=TemplateCategory.EDUCATION,
            description="Online learning platform",
            preview_image="/templates/online_course.jpg",
            tags=["education", "course", "learning"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("courses", "gallery", [], 3),
                TemplateSection("benefits", "features_grid", [], 4),
                TemplateSection("testimonials", "testimonials", [], 5),
                TemplateSection("pricing", "pricing", [], 6),
                TemplateSection("footer", "footer", [], 7),
            ],
            color_scheme={
                "primary": "#4a148c",
                "secondary": "#6a1b9a",
                "accent": "#ab47bc",
                "background": "#ffffff",
                "text": "#212121",
            },
            fonts={
                "heading": "Nunito",
                "body": "Open Sans",
            },
        )

        # University
        self.templates["university"] = Template(
            template_id="university",
            name="University",
            category=TemplateCategory.EDUCATION,
            description="University/college website",
            preview_image="/templates/university.jpg",
            tags=["education", "university", "academic"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("programs", "features_grid", [], 3),
                TemplateSection("campus", "gallery", [], 4),
                TemplateSection("admissions", "content", [], 5),
                TemplateSection("contact", "contact", [], 6),
                TemplateSection("footer", "footer", [], 7),
            ],
            color_scheme={
                "primary": "#003366",
                "secondary": "#004080",
                "accent": "#cc0000",
                "background": "#ffffff",
                "text": "#333333",
            },
            fonts={
                "heading": "Merriweather",
                "body": "Source Sans Pro",
            },
        )

    def _add_health_templates(self) -> None:
        """Add health templates"""
        # Medical Clinic
        self.templates["medical_clinic"] = Template(
            template_id="medical_clinic",
            name="Medical Clinic",
            category=TemplateCategory.HEALTH,
            description="Professional medical clinic website",
            preview_image="/templates/medical_clinic.jpg",
            tags=["health", "medical", "clinic"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("services", "features_grid", [], 3),
                TemplateSection("doctors", "team", [], 4),
                TemplateSection("appointment", "contact", [], 5),
                TemplateSection("footer", "footer", [], 6),
            ],
            color_scheme={
                "primary": "#0077be",
                "secondary": "#0088cc",
                "accent": "#00c4cc",
                "background": "#f0f8ff",
                "text": "#333333",
            },
            fonts={
                "heading": "Roboto",
                "body": "Open Sans",
            },
        )

        # Fitness Center
        self.templates["fitness_center"] = Template(
            template_id="fitness_center",
            name="Fitness Center",
            category=TemplateCategory.HEALTH,
            description="Energetic fitness center website",
            preview_image="/templates/fitness_center.jpg",
            tags=["health", "fitness", "gym"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("classes", "features_grid", [], 3),
                TemplateSection("trainers", "team", [], 4),
                TemplateSection("membership", "pricing", [], 5),
                TemplateSection("contact", "contact", [], 6),
                TemplateSection("footer", "footer", [], 7),
            ],
            color_scheme={
                "primary": "#ff6b35",
                "secondary": "#f7931e",
                "accent": "#c1c119",
                "background": "#1a1a1a",
                "text": "#ffffff",
            },
            fonts={
                "heading": "Oswald",
                "body": "Roboto",
            },
        )

    def _add_real_estate_templates(self) -> None:
        """Add real estate templates"""
        # Real Estate Agency
        self.templates["real_estate_agency"] = Template(
            template_id="real_estate_agency",
            name="Real Estate Agency",
            category=TemplateCategory.REAL_ESTATE,
            description="Professional real estate agency",
            preview_image="/templates/real_estate_agency.jpg",
            tags=["real estate", "property", "agency"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("properties", "gallery", [], 3),
                TemplateSection("services", "features_grid", [], 4),
                TemplateSection("agents", "team", [], 5),
                TemplateSection("contact", "contact", [], 6),
                TemplateSection("footer", "footer", [], 7),
            ],
            color_scheme={
                "primary": "#1a5490",
                "secondary": "#2465a8",
                "accent": "#ffa500",
                "background": "#ffffff",
                "text": "#333333",
            },
            fonts={
                "heading": "Montserrat",
                "body": "Open Sans",
            },
        )

    def _add_events_templates(self) -> None:
        """Add events templates"""
        # Conference
        self.templates["conference"] = Template(
            template_id="conference",
            name="Conference",
            category=TemplateCategory.EVENTS,
            description="Professional conference website",
            preview_image="/templates/conference.jpg",
            tags=["event", "conference", "professional"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("speakers", "team", [], 3),
                TemplateSection("schedule", "content", [], 4),
                TemplateSection("venue", "contact", [], 5),
                TemplateSection("registration", "contact", [], 6),
                TemplateSection("footer", "footer", [], 7),
            ],
            color_scheme={
                "primary": "#0f2027",
                "secondary": "#203a43",
                "accent": "#2c5364",
                "background": "#f5f7fa",
                "text": "#2c3e50",
            },
            fonts={
                "heading": "Raleway",
                "body": "Lato",
            },
        )

        # Wedding
        self.templates["wedding"] = Template(
            template_id="wedding",
            name="Wedding",
            category=TemplateCategory.EVENTS,
            description="Beautiful wedding website",
            preview_image="/templates/wedding.jpg",
            tags=["event", "wedding", "celebration"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("story", "content", [], 3),
                TemplateSection("details", "content", [], 4),
                TemplateSection("gallery", "gallery", [], 5),
                TemplateSection("rsvp", "contact", [], 6),
                TemplateSection("footer", "footer", [], 7),
            ],
            color_scheme={
                "primary": "#d4a5a5",
                "secondary": "#edc7b7",
                "accent": "#ee8572",
                "background": "#fff9f5",
                "text": "#5e5e5e",
            },
            fonts={
                "heading": "Great Vibes",
                "body": "Lato",
            },
        )

    def _add_nonprofit_templates(self) -> None:
        """Add nonprofit templates"""
        # Charity
        self.templates["charity"] = Template(
            template_id="charity",
            name="Charity",
            category=TemplateCategory.NONPROFIT,
            description="Inspiring charity organization website",
            preview_image="/templates/charity.jpg",
            tags=["nonprofit", "charity", "donation"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("mission", "content", [], 3),
                TemplateSection("programs", "features_grid", [], 4),
                TemplateSection("impact", "content", [], 5),
                TemplateSection("donate", "contact", [], 6),
                TemplateSection("footer", "footer", [], 7),
            ],
            color_scheme={
                "primary": "#27ae60",
                "secondary": "#2ecc71",
                "accent": "#f39c12",
                "background": "#ffffff",
                "text": "#2c3e50",
            },
            fonts={
                "heading": "Montserrat",
                "body": "Open Sans",
            },
        )

    def _add_personal_templates(self) -> None:
        """Add personal templates"""
        # Resume/CV
        self.templates["resume"] = Template(
            template_id="resume",
            name="Resume/CV",
            category=TemplateCategory.PERSONAL,
            description="Professional online resume",
            preview_image="/templates/resume.jpg",
            tags=["personal", "resume", "cv"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("experience", "content", [], 3),
                TemplateSection("skills", "features_grid", [], 4),
                TemplateSection("education", "content", [], 5),
                TemplateSection("contact", "contact", [], 6),
                TemplateSection("footer", "footer", [], 7),
            ],
            color_scheme={
                "primary": "#34495e",
                "secondary": "#2c3e50",
                "accent": "#3498db",
                "background": "#ecf0f1",
                "text": "#2c3e50",
            },
            fonts={
                "heading": "Raleway",
                "body": "Roboto",
            },
        )

    def _add_technology_templates(self) -> None:
        """Add technology templates"""
        # AI/ML Company
        self.templates["ai_company"] = Template(
            template_id="ai_company",
            name="AI/ML Company",
            category=TemplateCategory.TECHNOLOGY,
            description="Modern AI/machine learning company",
            preview_image="/templates/ai_company.jpg",
            tags=["technology", "ai", "ml"],
            sections=[
                TemplateSection("header", "header", [], 1),
                TemplateSection("hero", "hero", [], 2),
                TemplateSection("solutions", "features_grid", [], 3),
                TemplateSection("technology", "content", [], 4),
                TemplateSection("case_studies", "gallery", [], 5),
                TemplateSection("contact", "contact", [], 6),
                TemplateSection("footer", "footer", [], 7),
            ],
            color_scheme={
                "primary": "#7c3aed",
                "secondary": "#a78bfa",
                "accent": "#06b6d4",
                "background": "#0f172a",
                "text": "#f1f5f9",
            },
            fonts={
                "heading": "Space Grotesk",
                "body": "Inter",
            },
        )

    def get_template(self, template_id: str) -> Optional[Template]:
        """Get template by ID"""
        return self.templates.get(template_id)

    def get_templates_by_category(self, category: TemplateCategory) -> List[Template]:
        """Get all templates in a category"""
        return [t for t in self.templates.values() if t.category == category]

    def get_all_templates(self) -> List[Template]:
        """Get all templates"""
        return list(self.templates.values())

    def search_templates(self, query: str) -> List[Template]:
        """Search templates by name, description, or tags"""
        query = query.lower()
        return [
            t for t in self.templates.values()
            if query in t.name.lower()
            or query in t.description.lower()
            or any(query in tag for tag in t.tags)
        ]

    def get_template_count(self) -> int:
        """Get total number of templates"""
        return len(self.templates)

    def apply_template(self, template_id: str, customizations: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Apply a template with optional customizations"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        result = template.to_dict()

        if customizations:
            # Apply color scheme customizations
            if "color_scheme" in customizations:
                result["color_scheme"].update(customizations["color_scheme"])

            # Apply font customizations
            if "fonts" in customizations:
                result["fonts"].update(customizations["fonts"])

        return result
