"""
Component Library - 100+ customizable UI components
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Literal
from enum import Enum
import json


class ComponentCategory(Enum):
    """Component categories"""
    LAYOUT = "layout"
    NAVIGATION = "navigation"
    CONTENT = "content"
    MEDIA = "media"
    FORMS = "forms"
    ECOMMERCE = "ecommerce"
    SOCIAL = "social"
    WIDGETS = "widgets"
    HERO = "hero"
    FEATURES = "features"
    TESTIMONIALS = "testimonials"
    PRICING = "pricing"
    TEAM = "team"
    CONTACT = "contact"
    FOOTER = "footer"


@dataclass
class ComponentProperty:
    """Component property definition"""
    name: str
    prop_type: str  # text, number, color, image, select, etc.
    default_value: Any
    label: str
    description: str = ""
    options: List[str] = field(default_factory=list)
    required: bool = False
    validation: Optional[Dict[str, Any]] = None


@dataclass
class Component:
    """Component definition"""
    component_id: str
    name: str
    category: ComponentCategory
    description: str
    properties: List[ComponentProperty]
    default_styles: Dict[str, str]
    template: str
    preview_image: Optional[str] = None
    is_container: bool = False
    allowed_children: List[str] = field(default_factory=list)
    responsive: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "component_id": self.component_id,
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "properties": [
                {
                    "name": p.name,
                    "type": p.prop_type,
                    "default": p.default_value,
                    "label": p.label,
                    "description": p.description,
                    "options": p.options,
                    "required": p.required,
                }
                for p in self.properties
            ],
            "default_styles": self.default_styles,
            "template": self.template,
            "preview_image": self.preview_image,
            "is_container": self.is_container,
            "allowed_children": self.allowed_children,
            "responsive": self.responsive,
        }


class ComponentLibrary:
    """Library of all available components"""

    def __init__(self):
        self.components: Dict[str, Component] = {}
        self._initialize_components()

    def _initialize_components(self) -> None:
        """Initialize all components"""
        # Layout Components
        self._add_layout_components()
        # Navigation Components
        self._add_navigation_components()
        # Content Components
        self._add_content_components()
        # Media Components
        self._add_media_components()
        # Form Components
        self._add_form_components()
        # E-commerce Components
        self._add_ecommerce_components()
        # Hero Components
        self._add_hero_components()
        # Feature Components
        self._add_feature_components()
        # Testimonial Components
        self._add_testimonial_components()
        # Pricing Components
        self._add_pricing_components()
        # Team Components
        self._add_team_components()
        # Contact Components
        self._add_contact_components()
        # Footer Components
        self._add_footer_components()
        # Widget Components
        self._add_widget_components()
        # Social Components
        self._add_social_components()

    def _add_layout_components(self) -> None:
        """Add layout components"""
        # Container
        self.components["container"] = Component(
            component_id="container",
            name="Container",
            category=ComponentCategory.LAYOUT,
            description="Responsive container for page content",
            properties=[
                ComponentProperty("max_width", "select", "1200px", "Max Width",
                                options=["100%", "1200px", "1400px", "1600px"]),
                ComponentProperty("padding", "text", "20px", "Padding"),
                ComponentProperty("background", "color", "transparent", "Background"),
            ],
            default_styles={
                "max-width": "1200px",
                "margin": "0 auto",
                "padding": "20px",
            },
            template='<div class="container">{{content}}</div>',
            is_container=True,
        )

        # Row (Grid Row)
        self.components["row"] = Component(
            component_id="row",
            name="Row",
            category=ComponentCategory.LAYOUT,
            description="Flexible row container",
            properties=[
                ComponentProperty("gap", "text", "20px", "Gap between columns"),
                ComponentProperty("align", "select", "start", "Vertical Alignment",
                                options=["start", "center", "end", "stretch"]),
            ],
            default_styles={
                "display": "flex",
                "flex-wrap": "wrap",
                "gap": "20px",
            },
            template='<div class="row">{{content}}</div>',
            is_container=True,
        )

        # Column
        self.components["column"] = Component(
            component_id="column",
            name="Column",
            category=ComponentCategory.LAYOUT,
            description="Flexible column",
            properties=[
                ComponentProperty("width", "select", "auto", "Width",
                                options=["auto", "25%", "33%", "50%", "66%", "75%", "100%"]),
                ComponentProperty("padding", "text", "10px", "Padding"),
            ],
            default_styles={
                "flex": "1",
                "padding": "10px",
            },
            template='<div class="column">{{content}}</div>',
            is_container=True,
        )

        # Section
        self.components["section"] = Component(
            component_id="section",
            name="Section",
            category=ComponentCategory.LAYOUT,
            description="Page section with background",
            properties=[
                ComponentProperty("background", "color", "#ffffff", "Background Color"),
                ComponentProperty("padding_top", "text", "60px", "Top Padding"),
                ComponentProperty("padding_bottom", "text", "60px", "Bottom Padding"),
            ],
            default_styles={
                "padding": "60px 0",
                "background": "#ffffff",
            },
            template='<section class="section">{{content}}</section>',
            is_container=True,
        )

        # Divider
        self.components["divider"] = Component(
            component_id="divider",
            name="Divider",
            category=ComponentCategory.LAYOUT,
            description="Horizontal divider line",
            properties=[
                ComponentProperty("color", "color", "#e0e0e0", "Line Color"),
                ComponentProperty("thickness", "text", "1px", "Line Thickness"),
                ComponentProperty("margin", "text", "20px 0", "Margin"),
            ],
            default_styles={
                "border": "none",
                "border-top": "1px solid #e0e0e0",
                "margin": "20px 0",
            },
            template='<hr class="divider" />',
        )

        # Spacer
        self.components["spacer"] = Component(
            component_id="spacer",
            name="Spacer",
            category=ComponentCategory.LAYOUT,
            description="Empty space for layout control",
            properties=[
                ComponentProperty("height", "text", "40px", "Height"),
            ],
            default_styles={
                "height": "40px",
            },
            template='<div class="spacer"></div>',
        )

    def _add_navigation_components(self) -> None:
        """Add navigation components"""
        # Header
        self.components["header"] = Component(
            component_id="header",
            name="Header",
            category=ComponentCategory.NAVIGATION,
            description="Site header with logo and navigation",
            properties=[
                ComponentProperty("logo_text", "text", "NEXUS", "Logo Text"),
                ComponentProperty("logo_image", "image", "", "Logo Image"),
                ComponentProperty("sticky", "select", "no", "Sticky Header", options=["yes", "no"]),
                ComponentProperty("background", "color", "#ffffff", "Background"),
            ],
            default_styles={
                "background": "#ffffff",
                "padding": "20px 0",
                "box-shadow": "0 2px 4px rgba(0,0,0,0.1)",
            },
            template='<header class="header"><div class="container">{{content}}</div></header>',
            is_container=True,
        )

        # Navigation Menu
        self.components["nav_menu"] = Component(
            component_id="nav_menu",
            name="Navigation Menu",
            category=ComponentCategory.NAVIGATION,
            description="Horizontal navigation menu",
            properties=[
                ComponentProperty("menu_items", "text", "Home, About, Services, Contact", "Menu Items (comma-separated)"),
                ComponentProperty("align", "select", "right", "Alignment", options=["left", "center", "right"]),
            ],
            default_styles={
                "display": "flex",
                "gap": "30px",
                "list-style": "none",
            },
            template='<nav class="nav-menu">{{content}}</nav>',
        )

        # Breadcrumb
        self.components["breadcrumb"] = Component(
            component_id="breadcrumb",
            name="Breadcrumb",
            category=ComponentCategory.NAVIGATION,
            description="Breadcrumb navigation",
            properties=[
                ComponentProperty("items", "text", "Home / Products / Category", "Items (separated by /)"),
            ],
            default_styles={
                "display": "flex",
                "gap": "10px",
                "font-size": "14px",
                "color": "#666",
            },
            template='<nav class="breadcrumb">{{content}}</nav>',
        )

        # Sidebar Menu
        self.components["sidebar_menu"] = Component(
            component_id="sidebar_menu",
            name="Sidebar Menu",
            category=ComponentCategory.NAVIGATION,
            description="Vertical sidebar navigation",
            properties=[
                ComponentProperty("width", "text", "250px", "Width"),
                ComponentProperty("background", "color", "#f5f5f5", "Background"),
            ],
            default_styles={
                "width": "250px",
                "background": "#f5f5f5",
                "padding": "20px",
            },
            template='<aside class="sidebar-menu">{{content}}</aside>',
            is_container=True,
        )

        # Tabs
        self.components["tabs"] = Component(
            component_id="tabs",
            name="Tabs",
            category=ComponentCategory.NAVIGATION,
            description="Tabbed navigation",
            properties=[
                ComponentProperty("tabs", "text", "Tab 1, Tab 2, Tab 3", "Tab Labels (comma-separated)"),
                ComponentProperty("style", "select", "default", "Tab Style", options=["default", "pills", "underline"]),
            ],
            default_styles={
                "display": "flex",
                "border-bottom": "1px solid #e0e0e0",
            },
            template='<div class="tabs">{{content}}</div>',
            is_container=True,
        )

    def _add_content_components(self) -> None:
        """Add content components"""
        # Heading
        self.components["heading"] = Component(
            component_id="heading",
            name="Heading",
            category=ComponentCategory.CONTENT,
            description="Heading text (H1-H6)",
            properties=[
                ComponentProperty("text", "text", "Your Heading", "Text"),
                ComponentProperty("level", "select", "h2", "Heading Level",
                                options=["h1", "h2", "h3", "h4", "h5", "h6"]),
                ComponentProperty("align", "select", "left", "Alignment",
                                options=["left", "center", "right"]),
                ComponentProperty("color", "color", "#333333", "Text Color"),
            ],
            default_styles={
                "font-size": "32px",
                "font-weight": "bold",
                "margin": "20px 0",
            },
            template='<{{level}} class="heading">{{text}}</{{level}}>',
        )

        # Paragraph
        self.components["paragraph"] = Component(
            component_id="paragraph",
            name="Paragraph",
            category=ComponentCategory.CONTENT,
            description="Text paragraph",
            properties=[
                ComponentProperty("text", "text", "Your paragraph text here...", "Text"),
                ComponentProperty("align", "select", "left", "Alignment",
                                options=["left", "center", "right", "justify"]),
                ComponentProperty("font_size", "text", "16px", "Font Size"),
            ],
            default_styles={
                "font-size": "16px",
                "line-height": "1.6",
                "margin": "15px 0",
            },
            template='<p class="paragraph">{{text}}</p>',
        )

        # Button
        self.components["button"] = Component(
            component_id="button",
            name="Button",
            category=ComponentCategory.CONTENT,
            description="Call-to-action button",
            properties=[
                ComponentProperty("text", "text", "Click Me", "Button Text"),
                ComponentProperty("link", "text", "#", "Link URL"),
                ComponentProperty("style", "select", "primary", "Button Style",
                                options=["primary", "secondary", "outline", "ghost"]),
                ComponentProperty("size", "select", "medium", "Size",
                                options=["small", "medium", "large"]),
                ComponentProperty("background", "color", "#007bff", "Background Color"),
            ],
            default_styles={
                "padding": "12px 30px",
                "background": "#007bff",
                "color": "#ffffff",
                "border": "none",
                "border-radius": "4px",
                "cursor": "pointer",
                "font-size": "16px",
            },
            template='<a href="{{link}}" class="button button-{{style}} button-{{size}}">{{text}}</a>',
        )

        # List
        self.components["list"] = Component(
            component_id="list",
            name="List",
            category=ComponentCategory.CONTENT,
            description="Bulleted or numbered list",
            properties=[
                ComponentProperty("items", "text", "Item 1\nItem 2\nItem 3", "List Items (one per line)"),
                ComponentProperty("type", "select", "unordered", "List Type",
                                options=["unordered", "ordered"]),
                ComponentProperty("icon", "text", "✓", "Custom Icon (for unordered)"),
            ],
            default_styles={
                "margin": "15px 0",
                "padding-left": "30px",
            },
            template='<ul class="list">{{content}}</ul>',
        )

        # Quote
        self.components["quote"] = Component(
            component_id="quote",
            name="Quote",
            category=ComponentCategory.CONTENT,
            description="Blockquote element",
            properties=[
                ComponentProperty("text", "text", "Your quote here...", "Quote Text"),
                ComponentProperty("author", "text", "", "Author Name"),
                ComponentProperty("border_color", "color", "#007bff", "Border Color"),
            ],
            default_styles={
                "border-left": "4px solid #007bff",
                "padding": "15px 20px",
                "margin": "20px 0",
                "font-style": "italic",
            },
            template='<blockquote class="quote">{{text}}<cite>{{author}}</cite></blockquote>',
        )

        # Accordion
        self.components["accordion"] = Component(
            component_id="accordion",
            name="Accordion",
            category=ComponentCategory.CONTENT,
            description="Expandable accordion",
            properties=[
                ComponentProperty("title", "text", "Click to expand", "Title"),
                ComponentProperty("content", "text", "Accordion content...", "Content"),
            ],
            default_styles={
                "border": "1px solid #e0e0e0",
                "margin": "10px 0",
            },
            template='<details class="accordion"><summary>{{title}}</summary>{{content}}</details>',
        )

        # Alert/Notice
        self.components["alert"] = Component(
            component_id="alert",
            name="Alert",
            category=ComponentCategory.CONTENT,
            description="Alert or notice box",
            properties=[
                ComponentProperty("text", "text", "This is an alert message", "Message"),
                ComponentProperty("type", "select", "info", "Alert Type",
                                options=["info", "success", "warning", "error"]),
                ComponentProperty("dismissible", "select", "no", "Dismissible", options=["yes", "no"]),
            ],
            default_styles={
                "padding": "15px 20px",
                "border-radius": "4px",
                "margin": "15px 0",
            },
            template='<div class="alert alert-{{type}}">{{text}}</div>',
        )

        # Code Block
        self.components["code_block"] = Component(
            component_id="code_block",
            name="Code Block",
            category=ComponentCategory.CONTENT,
            description="Code snippet display",
            properties=[
                ComponentProperty("code", "text", "console.log('Hello');", "Code"),
                ComponentProperty("language", "text", "javascript", "Language"),
            ],
            default_styles={
                "background": "#f5f5f5",
                "padding": "15px",
                "border-radius": "4px",
                "font-family": "monospace",
                "overflow-x": "auto",
            },
            template='<pre class="code-block"><code>{{code}}</code></pre>',
        )

    def _add_media_components(self) -> None:
        """Add media components"""
        # Image
        self.components["image"] = Component(
            component_id="image",
            name="Image",
            category=ComponentCategory.MEDIA,
            description="Image element",
            properties=[
                ComponentProperty("src", "image", "", "Image URL", required=True),
                ComponentProperty("alt", "text", "", "Alt Text"),
                ComponentProperty("width", "text", "100%", "Width"),
                ComponentProperty("border_radius", "text", "0", "Border Radius"),
            ],
            default_styles={
                "max-width": "100%",
                "height": "auto",
            },
            template='<img src="{{src}}" alt="{{alt}}" class="image" />',
        )

        # Gallery
        self.components["gallery"] = Component(
            component_id="gallery",
            name="Gallery",
            category=ComponentCategory.MEDIA,
            description="Image gallery grid",
            properties=[
                ComponentProperty("columns", "select", "3", "Columns", options=["2", "3", "4", "5"]),
                ComponentProperty("gap", "text", "15px", "Gap"),
            ],
            default_styles={
                "display": "grid",
                "grid-template-columns": "repeat(3, 1fr)",
                "gap": "15px",
            },
            template='<div class="gallery">{{content}}</div>',
            is_container=True,
        )

        # Video
        self.components["video"] = Component(
            component_id="video",
            name="Video",
            category=ComponentCategory.MEDIA,
            description="Video player",
            properties=[
                ComponentProperty("src", "text", "", "Video URL"),
                ComponentProperty("autoplay", "select", "no", "Autoplay", options=["yes", "no"]),
                ComponentProperty("controls", "select", "yes", "Show Controls", options=["yes", "no"]),
            ],
            default_styles={
                "width": "100%",
                "max-width": "100%",
            },
            template='<video src="{{src}}" class="video" controls>Your browser does not support video.</video>',
        )

        # Icon
        self.components["icon"] = Component(
            component_id="icon",
            name="Icon",
            category=ComponentCategory.MEDIA,
            description="Icon element",
            properties=[
                ComponentProperty("icon_name", "text", "star", "Icon Name"),
                ComponentProperty("size", "text", "24px", "Size"),
                ComponentProperty("color", "color", "#333333", "Color"),
            ],
            default_styles={
                "font-size": "24px",
                "color": "#333333",
            },
            template='<i class="icon icon-{{icon_name}}"></i>',
        )

        # Slider/Carousel
        self.components["slider"] = Component(
            component_id="slider",
            name="Slider",
            category=ComponentCategory.MEDIA,
            description="Image slider/carousel",
            properties=[
                ComponentProperty("autoplay", "select", "yes", "Autoplay", options=["yes", "no"]),
                ComponentProperty("interval", "text", "5000", "Autoplay Interval (ms)"),
                ComponentProperty("arrows", "select", "yes", "Show Arrows", options=["yes", "no"]),
                ComponentProperty("dots", "select", "yes", "Show Dots", options=["yes", "no"]),
            ],
            default_styles={
                "position": "relative",
                "overflow": "hidden",
            },
            template='<div class="slider">{{content}}</div>',
            is_container=True,
        )

    def _add_form_components(self) -> None:
        """Add form components"""
        # Form
        self.components["form"] = Component(
            component_id="form",
            name="Form",
            category=ComponentCategory.FORMS,
            description="Form container",
            properties=[
                ComponentProperty("action", "text", "/submit", "Action URL"),
                ComponentProperty("method", "select", "post", "Method", options=["post", "get"]),
            ],
            default_styles={
                "max-width": "600px",
            },
            template='<form action="{{action}}" method="{{method}}" class="form">{{content}}</form>',
            is_container=True,
        )

        # Input Field
        self.components["input"] = Component(
            component_id="input",
            name="Input Field",
            category=ComponentCategory.FORMS,
            description="Text input field",
            properties=[
                ComponentProperty("label", "text", "Label", "Label"),
                ComponentProperty("placeholder", "text", "", "Placeholder"),
                ComponentProperty("type", "select", "text", "Input Type",
                                options=["text", "email", "password", "tel", "url"]),
                ComponentProperty("required", "select", "no", "Required", options=["yes", "no"]),
            ],
            default_styles={
                "width": "100%",
                "padding": "10px",
                "margin": "10px 0",
                "border": "1px solid #ddd",
                "border-radius": "4px",
            },
            template='<div class="form-field"><label>{{label}}</label><input type="{{type}}" placeholder="{{placeholder}}" /></div>',
        )

        # Textarea
        self.components["textarea"] = Component(
            component_id="textarea",
            name="Textarea",
            category=ComponentCategory.FORMS,
            description="Multi-line text input",
            properties=[
                ComponentProperty("label", "text", "Message", "Label"),
                ComponentProperty("placeholder", "text", "", "Placeholder"),
                ComponentProperty("rows", "text", "5", "Rows"),
            ],
            default_styles={
                "width": "100%",
                "padding": "10px",
                "margin": "10px 0",
                "border": "1px solid #ddd",
                "border-radius": "4px",
            },
            template='<div class="form-field"><label>{{label}}</label><textarea rows="{{rows}}" placeholder="{{placeholder}}"></textarea></div>',
        )

        # Select Dropdown
        self.components["select"] = Component(
            component_id="select",
            name="Select Dropdown",
            category=ComponentCategory.FORMS,
            description="Dropdown select",
            properties=[
                ComponentProperty("label", "text", "Select Option", "Label"),
                ComponentProperty("options", "text", "Option 1, Option 2, Option 3", "Options (comma-separated)"),
            ],
            default_styles={
                "width": "100%",
                "padding": "10px",
                "margin": "10px 0",
                "border": "1px solid #ddd",
                "border-radius": "4px",
            },
            template='<div class="form-field"><label>{{label}}</label><select>{{content}}</select></div>',
        )

        # Checkbox
        self.components["checkbox"] = Component(
            component_id="checkbox",
            name="Checkbox",
            category=ComponentCategory.FORMS,
            description="Checkbox input",
            properties=[
                ComponentProperty("label", "text", "I agree to terms", "Label"),
                ComponentProperty("checked", "select", "no", "Default Checked", options=["yes", "no"]),
            ],
            default_styles={
                "margin": "10px 0",
            },
            template='<div class="form-field"><label><input type="checkbox" /> {{label}}</label></div>',
        )

        # Radio Button
        self.components["radio"] = Component(
            component_id="radio",
            name="Radio Button",
            category=ComponentCategory.FORMS,
            description="Radio button input",
            properties=[
                ComponentProperty("label", "text", "Option", "Label"),
                ComponentProperty("name", "text", "radio_group", "Group Name"),
            ],
            default_styles={
                "margin": "10px 0",
            },
            template='<div class="form-field"><label><input type="radio" name="{{name}}" /> {{label}}</label></div>',
        )

    def _add_hero_components(self) -> None:
        """Add hero section components"""
        # Hero Section
        self.components["hero"] = Component(
            component_id="hero",
            name="Hero Section",
            category=ComponentCategory.HERO,
            description="Full-width hero section",
            properties=[
                ComponentProperty("title", "text", "Welcome to Our Website", "Title"),
                ComponentProperty("subtitle", "text", "Your subtitle here", "Subtitle"),
                ComponentProperty("background_image", "image", "", "Background Image"),
                ComponentProperty("height", "text", "500px", "Height"),
                ComponentProperty("overlay", "color", "rgba(0,0,0,0.3)", "Overlay Color"),
            ],
            default_styles={
                "height": "500px",
                "background-size": "cover",
                "background-position": "center",
                "display": "flex",
                "align-items": "center",
                "justify-content": "center",
                "text-align": "center",
                "color": "#ffffff",
            },
            template='<div class="hero">{{content}}</div>',
            is_container=True,
        )

    def _add_feature_components(self) -> None:
        """Add feature components"""
        # Feature Box
        self.components["feature_box"] = Component(
            component_id="feature_box",
            name="Feature Box",
            category=ComponentCategory.FEATURES,
            description="Feature highlight box",
            properties=[
                ComponentProperty("icon", "text", "✓", "Icon"),
                ComponentProperty("title", "text", "Feature Title", "Title"),
                ComponentProperty("description", "text", "Feature description", "Description"),
            ],
            default_styles={
                "text-align": "center",
                "padding": "30px",
                "border": "1px solid #e0e0e0",
                "border-radius": "8px",
            },
            template='<div class="feature-box"><div class="icon">{{icon}}</div><h3>{{title}}</h3><p>{{description}}</p></div>',
        )

        # Features Grid
        self.components["features_grid"] = Component(
            component_id="features_grid",
            name="Features Grid",
            category=ComponentCategory.FEATURES,
            description="Grid of feature boxes",
            properties=[
                ComponentProperty("columns", "select", "3", "Columns", options=["2", "3", "4"]),
            ],
            default_styles={
                "display": "grid",
                "grid-template-columns": "repeat(3, 1fr)",
                "gap": "30px",
            },
            template='<div class="features-grid">{{content}}</div>',
            is_container=True,
        )

    def _add_testimonial_components(self) -> None:
        """Add testimonial components"""
        # Testimonial Card
        self.components["testimonial"] = Component(
            component_id="testimonial",
            name="Testimonial",
            category=ComponentCategory.TESTIMONIALS,
            description="Customer testimonial card",
            properties=[
                ComponentProperty("quote", "text", "Great product!", "Quote"),
                ComponentProperty("author", "text", "John Doe", "Author Name"),
                ComponentProperty("role", "text", "CEO, Company", "Author Role"),
                ComponentProperty("avatar", "image", "", "Avatar Image"),
                ComponentProperty("rating", "select", "5", "Rating", options=["1", "2", "3", "4", "5"]),
            ],
            default_styles={
                "background": "#f9f9f9",
                "padding": "30px",
                "border-radius": "8px",
                "box-shadow": "0 2px 8px rgba(0,0,0,0.1)",
            },
            template='<div class="testimonial"><p>{{quote}}</p><div class="author"><strong>{{author}}</strong><span>{{role}}</span></div></div>',
        )

    def _add_pricing_components(self) -> None:
        """Add pricing components"""
        # Pricing Table
        self.components["pricing_table"] = Component(
            component_id="pricing_table",
            name="Pricing Table",
            category=ComponentCategory.PRICING,
            description="Pricing plan card",
            properties=[
                ComponentProperty("plan_name", "text", "Basic Plan", "Plan Name"),
                ComponentProperty("price", "text", "$29", "Price"),
                ComponentProperty("period", "text", "/month", "Period"),
                ComponentProperty("features", "text", "Feature 1\nFeature 2\nFeature 3", "Features (one per line)"),
                ComponentProperty("button_text", "text", "Get Started", "Button Text"),
                ComponentProperty("featured", "select", "no", "Featured", options=["yes", "no"]),
            ],
            default_styles={
                "border": "1px solid #e0e0e0",
                "border-radius": "8px",
                "padding": "40px 30px",
                "text-align": "center",
            },
            template='<div class="pricing-table"><h3>{{plan_name}}</h3><div class="price">{{price}}<span>{{period}}</span></div><ul>{{features}}</ul><a href="#" class="button">{{button_text}}</a></div>',
        )

    def _add_team_components(self) -> None:
        """Add team components"""
        # Team Member Card
        self.components["team_member"] = Component(
            component_id="team_member",
            name="Team Member",
            category=ComponentCategory.TEAM,
            description="Team member profile card",
            properties=[
                ComponentProperty("name", "text", "John Doe", "Name"),
                ComponentProperty("role", "text", "CEO", "Role"),
                ComponentProperty("photo", "image", "", "Photo"),
                ComponentProperty("bio", "text", "", "Bio"),
                ComponentProperty("social_links", "text", "", "Social Links"),
            ],
            default_styles={
                "text-align": "center",
                "padding": "20px",
            },
            template='<div class="team-member"><img src="{{photo}}" alt="{{name}}" /><h4>{{name}}</h4><p>{{role}}</p><p>{{bio}}</p></div>',
        )

    def _add_contact_components(self) -> None:
        """Add contact components"""
        # Contact Form
        self.components["contact_form"] = Component(
            component_id="contact_form",
            name="Contact Form",
            category=ComponentCategory.CONTACT,
            description="Complete contact form",
            properties=[
                ComponentProperty("title", "text", "Get in Touch", "Title"),
                ComponentProperty("show_phone", "select", "yes", "Show Phone Field", options=["yes", "no"]),
                ComponentProperty("show_company", "select", "no", "Show Company Field", options=["yes", "no"]),
            ],
            default_styles={
                "max-width": "600px",
                "margin": "0 auto",
            },
            template='<div class="contact-form"><h2>{{title}}</h2><form>{{content}}</form></div>',
            is_container=True,
        )

        # Map
        self.components["map"] = Component(
            component_id="map",
            name="Map",
            category=ComponentCategory.CONTACT,
            description="Embedded map",
            properties=[
                ComponentProperty("address", "text", "", "Address"),
                ComponentProperty("height", "text", "400px", "Height"),
                ComponentProperty("zoom", "text", "14", "Zoom Level"),
            ],
            default_styles={
                "width": "100%",
                "height": "400px",
                "border": "none",
            },
            template='<div class="map"><iframe src="https://maps.google.com/maps?q={{address}}&output=embed" width="100%" height="{{height}}"></iframe></div>',
        )

    def _add_footer_components(self) -> None:
        """Add footer components"""
        # Footer
        self.components["footer"] = Component(
            component_id="footer",
            name="Footer",
            category=ComponentCategory.FOOTER,
            description="Site footer",
            properties=[
                ComponentProperty("background", "color", "#333333", "Background"),
                ComponentProperty("text_color", "color", "#ffffff", "Text Color"),
                ComponentProperty("copyright", "text", "© 2025 NEXUS. All rights reserved.", "Copyright Text"),
            ],
            default_styles={
                "background": "#333333",
                "color": "#ffffff",
                "padding": "40px 0",
                "text-align": "center",
            },
            template='<footer class="footer">{{content}}<p>{{copyright}}</p></footer>',
            is_container=True,
        )

    def _add_ecommerce_components(self) -> None:
        """Add e-commerce components"""
        # Product Card
        self.components["product_card"] = Component(
            component_id="product_card",
            name="Product Card",
            category=ComponentCategory.ECOMMERCE,
            description="Product display card",
            properties=[
                ComponentProperty("image", "image", "", "Product Image"),
                ComponentProperty("name", "text", "Product Name", "Product Name"),
                ComponentProperty("price", "text", "$99.99", "Price"),
                ComponentProperty("description", "text", "", "Description"),
                ComponentProperty("badge", "text", "", "Badge (e.g., 'Sale', 'New')"),
            ],
            default_styles={
                "border": "1px solid #e0e0e0",
                "border-radius": "8px",
                "overflow": "hidden",
                "transition": "transform 0.3s",
            },
            template='<div class="product-card"><img src="{{image}}" alt="{{name}}" /><div class="product-info"><h3>{{name}}</h3><p class="price">{{price}}</p><p>{{description}}</p></div></div>',
        )

        # Shopping Cart
        self.components["shopping_cart"] = Component(
            component_id="shopping_cart",
            name="Shopping Cart",
            category=ComponentCategory.ECOMMERCE,
            description="Shopping cart widget",
            properties=[
                ComponentProperty("icon_color", "color", "#333333", "Icon Color"),
                ComponentProperty("position", "select", "right", "Position", options=["left", "right"]),
            ],
            default_styles={
                "position": "fixed",
                "top": "20px",
                "right": "20px",
                "cursor": "pointer",
            },
            template='<div class="shopping-cart">🛒 <span class="cart-count">0</span></div>',
        )

    def _add_widget_components(self) -> None:
        """Add widget components"""
        # Progress Bar
        self.components["progress_bar"] = Component(
            component_id="progress_bar",
            name="Progress Bar",
            category=ComponentCategory.WIDGETS,
            description="Progress indicator",
            properties=[
                ComponentProperty("label", "text", "Progress", "Label"),
                ComponentProperty("percentage", "text", "75", "Percentage"),
                ComponentProperty("color", "color", "#007bff", "Bar Color"),
            ],
            default_styles={
                "width": "100%",
                "height": "20px",
                "background": "#e0e0e0",
                "border-radius": "10px",
                "overflow": "hidden",
            },
            template='<div class="progress-bar"><div class="progress-label">{{label}}</div><div class="progress" style="width: {{percentage}}%; background: {{color}};"></div></div>',
        )

        # Counter/Stats
        self.components["counter"] = Component(
            component_id="counter",
            name="Counter",
            category=ComponentCategory.WIDGETS,
            description="Animated counter",
            properties=[
                ComponentProperty("number", "text", "1000", "Number"),
                ComponentProperty("label", "text", "Happy Clients", "Label"),
                ComponentProperty("prefix", "text", "", "Prefix (e.g., $)"),
                ComponentProperty("suffix", "text", "+", "Suffix (e.g., +)"),
            ],
            default_styles={
                "text-align": "center",
                "padding": "20px",
            },
            template='<div class="counter"><div class="counter-number">{{prefix}}{{number}}{{suffix}}</div><div class="counter-label">{{label}}</div></div>',
        )

        # Modal/Popup
        self.components["modal"] = Component(
            component_id="modal",
            name="Modal",
            category=ComponentCategory.WIDGETS,
            description="Modal dialog",
            properties=[
                ComponentProperty("title", "text", "Modal Title", "Title"),
                ComponentProperty("trigger_text", "text", "Open Modal", "Trigger Button Text"),
            ],
            default_styles={
                "display": "none",
                "position": "fixed",
                "top": "50%",
                "left": "50%",
                "transform": "translate(-50%, -50%)",
                "background": "#ffffff",
                "padding": "30px",
                "border-radius": "8px",
                "box-shadow": "0 4px 20px rgba(0,0,0,0.3)",
            },
            template='<div class="modal"><button class="modal-trigger">{{trigger_text}}</button><div class="modal-content"><h2>{{title}}</h2>{{content}}</div></div>',
            is_container=True,
        )

        # Countdown Timer
        self.components["countdown"] = Component(
            component_id="countdown",
            name="Countdown Timer",
            category=ComponentCategory.WIDGETS,
            description="Countdown timer",
            properties=[
                ComponentProperty("end_date", "text", "2025-12-31", "End Date (YYYY-MM-DD)"),
                ComponentProperty("title", "text", "Limited Time Offer", "Title"),
            ],
            default_styles={
                "text-align": "center",
                "padding": "30px",
                "background": "#f5f5f5",
            },
            template='<div class="countdown"><h3>{{title}}</h3><div class="countdown-timer" data-end="{{end_date}}"></div></div>',
        )

    def _add_social_components(self) -> None:
        """Add social media components"""
        # Social Icons
        self.components["social_icons"] = Component(
            component_id="social_icons",
            name="Social Icons",
            category=ComponentCategory.SOCIAL,
            description="Social media icons",
            properties=[
                ComponentProperty("networks", "text", "facebook, twitter, instagram, linkedin", "Networks (comma-separated)"),
                ComponentProperty("size", "text", "32px", "Icon Size"),
                ComponentProperty("style", "select", "rounded", "Style", options=["rounded", "square", "circle"]),
            ],
            default_styles={
                "display": "flex",
                "gap": "15px",
                "justify-content": "center",
            },
            template='<div class="social-icons">{{content}}</div>',
        )

        # Share Buttons
        self.components["share_buttons"] = Component(
            component_id="share_buttons",
            name="Share Buttons",
            category=ComponentCategory.SOCIAL,
            description="Social share buttons",
            properties=[
                ComponentProperty("networks", "text", "facebook, twitter, linkedin", "Networks (comma-separated)"),
                ComponentProperty("layout", "select", "horizontal", "Layout", options=["horizontal", "vertical"]),
            ],
            default_styles={
                "display": "flex",
                "gap": "10px",
            },
            template='<div class="share-buttons">{{content}}</div>',
        )

    def get_component(self, component_id: str) -> Optional[Component]:
        """Get component by ID"""
        return self.components.get(component_id)

    def get_components_by_category(self, category: ComponentCategory) -> List[Component]:
        """Get all components in a category"""
        return [c for c in self.components.values() if c.category == category]

    def get_all_components(self) -> List[Component]:
        """Get all components"""
        return list(self.components.values())

    def get_component_count(self) -> int:
        """Get total number of components"""
        return len(self.components)

    def search_components(self, query: str) -> List[Component]:
        """Search components by name or description"""
        query = query.lower()
        return [
            c for c in self.components.values()
            if query in c.name.lower() or query in c.description.lower()
        ]
