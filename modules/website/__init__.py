"""
NEXUS Website Builder & CMS Module

A professional no-code website builder with drag-drop interface,
templates, e-commerce, SEO tools, and hosting capabilities.

Features:
- Visual drag-drop page builder
- 50+ professional templates
- 100+ customizable components
- Multi-page support with routing
- SEO optimization tools
- E-commerce integration
- Custom domain hosting
- Analytics integration
"""

from .builder import WebsiteBuilder, BuilderConfig
from .templates import TemplateManager, Template, TemplateCategory
from .pages import PageManager, Page, PageType
from .components import ComponentLibrary, Component, ComponentCategory
from .seo import SEOManager, SEOConfig
from .hosting import HostingManager, DomainConfig
from .analytics import AnalyticsManager, AnalyticsProvider
from .ecommerce import EcommerceManager, Product, Cart

__version__ = "1.0.0"
__all__ = [
    "WebsiteBuilder",
    "BuilderConfig",
    "TemplateManager",
    "Template",
    "TemplateCategory",
    "PageManager",
    "Page",
    "PageType",
    "ComponentLibrary",
    "Component",
    "ComponentCategory",
    "SEOManager",
    "SEOConfig",
    "HostingManager",
    "DomainConfig",
    "AnalyticsManager",
    "AnalyticsProvider",
    "EcommerceManager",
    "Product",
    "Cart",
]
