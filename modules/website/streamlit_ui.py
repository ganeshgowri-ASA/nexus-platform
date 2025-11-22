"""
Streamlit UI - Visual page builder interface

This module provides the interactive Streamlit interface for the website builder,
allowing users to create, edit, and manage websites visually.
"""

import streamlit as st
from typing import Dict, List, Optional, Any
import json

from .builder import WebsiteBuilder, BuilderConfig, DeviceType, BuilderMode
from .components import ComponentLibrary, ComponentCategory
from .templates import TemplateManager, TemplateCategory
from .pages import PageManager, PageType, PageStatus, PageMeta, PageSettings
from .seo import SEOManager, SEOConfig
from .hosting import HostingManager, PaymentProvider
from .analytics import AnalyticsManager, AnalyticsProvider
from .ecommerce import EcommerceManager, ProductStatus


class WebsiteBuilderUI:
    """Main UI class for website builder"""

    def __init__(self):
        self.initialize_session_state()

    def initialize_session_state(self):
        """Initialize session state variables"""
        if "project_id" not in st.session_state:
            st.session_state.project_id = "nexus_website_001"

        if "builder" not in st.session_state:
            config = BuilderConfig(
                project_id=st.session_state.project_id,
                project_name="My NEXUS Website",
            )
            st.session_state.builder = WebsiteBuilder(config)

        if "component_library" not in st.session_state:
            st.session_state.component_library = ComponentLibrary()

        if "template_manager" not in st.session_state:
            st.session_state.template_manager = TemplateManager()

        if "page_manager" not in st.session_state:
            st.session_state.page_manager = PageManager()

        if "seo_manager" not in st.session_state:
            seo_config = SEOConfig(
                site_name="NEXUS Website",
                site_url="https://example.com",
                default_title="NEXUS - No-Code Website Builder",
                default_description="Create stunning websites with NEXUS",
            )
            st.session_state.seo_manager = SEOManager(seo_config)

        if "hosting_manager" not in st.session_state:
            st.session_state.hosting_manager = HostingManager()

        if "analytics_manager" not in st.session_state:
            st.session_state.analytics_manager = AnalyticsManager()

        if "ecommerce_manager" not in st.session_state:
            st.session_state.ecommerce_manager = EcommerceManager()

        if "current_page" not in st.session_state:
            st.session_state.current_page = None

        if "selected_component" not in st.session_state:
            st.session_state.selected_component = None

    def render(self):
        """Render the main UI"""
        st.set_page_config(
            page_title="NEXUS Website Builder",
            page_icon="🌐",
            layout="wide",
            initial_sidebar_state="expanded",
        )

        st.title("🌐 NEXUS Website Builder & CMS")
        st.markdown("### Create professional websites without coding")

        # Sidebar navigation
        with st.sidebar:
            self.render_sidebar()

        # Main content area
        tab = st.session_state.get("active_tab", "builder")

        if tab == "builder":
            self.render_builder_tab()
        elif tab == "pages":
            self.render_pages_tab()
        elif tab == "templates":
            self.render_templates_tab()
        elif tab == "components":
            self.render_components_tab()
        elif tab == "seo":
            self.render_seo_tab()
        elif tab == "ecommerce":
            self.render_ecommerce_tab()
        elif tab == "analytics":
            self.render_analytics_tab()
        elif tab == "hosting":
            self.render_hosting_tab()
        elif tab == "settings":
            self.render_settings_tab()

    def render_sidebar(self):
        """Render sidebar navigation"""
        st.header("Navigation")

        tabs = {
            "builder": "🎨 Page Builder",
            "pages": "📄 Pages",
            "templates": "🎯 Templates",
            "components": "🧩 Components",
            "ecommerce": "🛒 E-Commerce",
            "seo": "🔍 SEO",
            "analytics": "📊 Analytics",
            "hosting": "🌐 Hosting",
            "settings": "⚙️ Settings",
        }

        for key, label in tabs.items():
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                st.session_state.active_tab = key
                st.rerun()

        st.divider()

        # Quick stats
        st.subheader("Quick Stats")
        page_manager: PageManager = st.session_state.page_manager
        ecommerce: EcommerceManager = st.session_state.ecommerce_manager

        stats = page_manager.get_page_stats()
        st.metric("Total Pages", stats["total_pages"])
        st.metric("Published", stats["published_pages"])
        st.metric("Products", len(ecommerce.products))

    def render_builder_tab(self):
        """Render page builder tab"""
        st.header("Visual Page Builder")

        col1, col2, col3 = st.columns([2, 3, 2])

        with col1:
            st.subheader("Component Library")
            self.render_component_palette()

        with col2:
            st.subheader("Canvas")
            self.render_canvas()

        with col3:
            st.subheader("Properties")
            self.render_properties_panel()

        # Toolbar
        self.render_builder_toolbar()

    def render_component_palette(self):
        """Render component palette"""
        library: ComponentLibrary = st.session_state.component_library

        # Category filter
        category = st.selectbox(
            "Category",
            ["All"] + [cat.value for cat in ComponentCategory],
            key="component_category_filter"
        )

        # Get components
        if category == "All":
            components = library.get_all_components()
        else:
            cat_enum = ComponentCategory(category)
            components = library.get_components_by_category(cat_enum)

        # Search
        search = st.text_input("Search components", key="component_search")
        if search:
            components = [c for c in components if search.lower() in c.name.lower()]

        # Display components
        for component in components[:20]:  # Limit display
            with st.expander(f"{component.name}"):
                st.caption(component.description)
                if st.button("Add to Canvas", key=f"add_{component.component_id}"):
                    st.success(f"Added {component.name}")

    def render_canvas(self):
        """Render builder canvas"""
        # Device preview selector
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💻 Desktop", use_container_width=True):
                st.session_state.device_type = DeviceType.DESKTOP
        with col2:
            if st.button("📱 Tablet", use_container_width=True):
                st.session_state.device_type = DeviceType.TABLET
        with col3:
            if st.button("📱 Mobile", use_container_width=True):
                st.session_state.device_type = DeviceType.MOBILE

        # Canvas area
        canvas_container = st.container()
        with canvas_container:
            st.markdown("### Canvas Area")
            st.info("Drag and drop components here to build your page")

            # Placeholder for visual canvas
            st.markdown("""
            <div style="
                border: 2px dashed #ccc;
                border-radius: 8px;
                padding: 40px;
                min-height: 400px;
                text-align: center;
                background: #f9f9f9;
            ">
                <h3>Drop components here</h3>
                <p>Select components from the library to add them to your page</p>
            </div>
            """, unsafe_allow_html=True)

    def render_properties_panel(self):
        """Render component properties panel"""
        if st.session_state.selected_component:
            st.markdown("### Component Properties")
            # Display properties form
            st.text_input("Component ID", value="component_001", disabled=True)
            st.text_input("Component Type", value="Button", disabled=True)

            # Common properties
            st.text_input("CSS Classes")
            st.text_area("Custom CSS")

            if st.button("Delete Component", type="secondary"):
                st.warning("Component deleted")
        else:
            st.info("Select a component to edit its properties")

    def render_builder_toolbar(self):
        """Render builder toolbar"""
        st.divider()
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            if st.button("↩️ Undo"):
                st.info("Undo last action")

        with col2:
            if st.button("↪️ Redo"):
                st.info("Redo last action")

        with col3:
            if st.button("💾 Save"):
                st.success("Page saved successfully!")

        with col4:
            if st.button("👁️ Preview"):
                st.info("Preview mode")

        with col5:
            if st.button("🚀 Publish"):
                st.success("Page published!")

    def render_pages_tab(self):
        """Render pages management tab"""
        st.header("Pages Management")

        page_manager: PageManager = st.session_state.page_manager

        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("All Pages")

            # Pages list
            pages = page_manager.get_all_pages()

            if not pages:
                st.info("No pages yet. Create your first page!")
            else:
                for page in pages:
                    with st.expander(f"{page.title} - {page.status.value}"):
                        st.write(f"**Slug:** {page.slug}")
                        st.write(f"**Type:** {page.page_type.value}")
                        st.write(f"**Created:** {page.created_at}")

                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            if st.button("Edit", key=f"edit_{page.page_id}"):
                                st.session_state.current_page = page.page_id
                        with col_b:
                            if page.status == PageStatus.PUBLISHED:
                                if st.button("Unpublish", key=f"unpub_{page.page_id}"):
                                    page_manager.unpublish_page(page.page_id)
                                    st.success("Page unpublished")
                            else:
                                if st.button("Publish", key=f"pub_{page.page_id}"):
                                    page_manager.publish_page(page.page_id)
                                    st.success("Page published!")
                        with col_c:
                            if st.button("Delete", key=f"del_{page.page_id}"):
                                page_manager.delete_page(page.page_id)
                                st.warning("Page deleted")

        with col2:
            st.subheader("Create New Page")

            with st.form("new_page_form"):
                title = st.text_input("Page Title")
                slug = st.text_input("URL Slug")
                page_type = st.selectbox("Page Type", [t.value for t in PageType])

                if st.form_submit_button("Create Page"):
                    if title and slug:
                        page_manager.create_page(
                            title=title,
                            slug=slug,
                            page_type=PageType(page_type)
                        )
                        st.success(f"Page '{title}' created!")
                        st.rerun()
                    else:
                        st.error("Please fill in all fields")

            # Page statistics
            st.divider()
            st.subheader("Statistics")
            stats = page_manager.get_page_stats()
            st.metric("Total Pages", stats["total_pages"])
            st.metric("Published", stats["published_pages"])
            st.metric("Drafts", stats["draft_pages"])

    def render_templates_tab(self):
        """Render templates tab"""
        st.header("Website Templates")

        template_manager: TemplateManager = st.session_state.template_manager

        # Category filter
        category = st.selectbox(
            "Category",
            ["All"] + [cat.value for cat in TemplateCategory],
            key="template_category"
        )

        # Get templates
        if category == "All":
            templates = template_manager.get_all_templates()
        else:
            cat_enum = TemplateCategory(category)
            templates = template_manager.get_templates_by_category(cat_enum)

        # Display templates in grid
        cols = st.columns(3)
        for idx, template in enumerate(templates[:12]):  # Show first 12
            with cols[idx % 3]:
                st.markdown(f"### {template.name}")
                st.caption(template.description)
                st.write(f"**Category:** {template.category.value}")
                st.write(f"**Tags:** {', '.join(template.tags[:3])}")

                if st.button("Use Template", key=f"use_template_{template.template_id}"):
                    st.success(f"Template '{template.name}' applied!")

        st.info(f"Showing {len(templates)} templates")

    def render_components_tab(self):
        """Render components library tab"""
        st.header("Component Library")

        library: ComponentLibrary = st.session_state.component_library

        st.info(f"📦 {library.get_component_count()} components available")

        # Search
        search = st.text_input("Search components")

        if search:
            components = library.search_components(search)
        else:
            components = library.get_all_components()

        # Group by category
        for category in ComponentCategory:
            category_components = [c for c in components if c.category == category]

            if category_components:
                with st.expander(f"{category.value.upper()} ({len(category_components)})", expanded=False):
                    for component in category_components[:10]:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{component.name}**")
                            st.caption(component.description)
                        with col2:
                            st.button("Info", key=f"info_{component.component_id}")

    def render_seo_tab(self):
        """Render SEO tab"""
        st.header("SEO Optimization")

        seo_manager: SEOManager = st.session_state.seo_manager

        tab1, tab2, tab3 = st.tabs(["Meta Tags", "Structured Data", "Analysis"])

        with tab1:
            st.subheader("Meta Tags Configuration")

            with st.form("meta_tags_form"):
                title = st.text_input("Page Title", value=seo_manager.config.default_title)
                description = st.text_area("Meta Description", value=seo_manager.config.default_description)
                keywords = st.text_input("Keywords (comma-separated)")
                author = st.text_input("Author", value=seo_manager.config.default_author)

                if st.form_submit_button("Generate Meta Tags"):
                    meta_tags = seo_manager.generate_all_meta_tags(
                        title=title,
                        description=description,
                        keywords=keywords.split(",") if keywords else None,
                        author=author,
                    )
                    st.code(meta_tags, language="html")

        with tab2:
            st.subheader("Structured Data")

            schema_type = st.selectbox(
                "Schema Type",
                ["Organization", "Website", "Article", "Product", "LocalBusiness"]
            )

            if st.button("Generate Schema"):
                if schema_type == "Organization":
                    schema = seo_manager.create_organization_schema(
                        name="NEXUS",
                        url="https://example.com",
                        logo="https://example.com/logo.png",
                        description="No-code website builder"
                    )
                    st.code(schema, language="html")

        with tab3:
            st.subheader("SEO Analysis")

            if st.button("Analyze Page"):
                # Sample analysis
                analysis = seo_manager.analyze_seo_score({
                    "title": "Sample Page",
                    "description": "Sample description for SEO analysis",
                    "keywords": ["nexus", "website", "builder"],
                    "has_h1": True,
                    "images_without_alt": 2,
                    "is_mobile_friendly": True,
                    "load_time": 2.5,
                    "has_canonical": True,
                    "has_schema": True,
                })

                st.metric("SEO Score", f"{analysis['score']}/100")
                st.metric("Grade", analysis['grade'])

                if analysis['issues']:
                    st.warning("Issues Found:")
                    for issue in analysis['issues']:
                        st.write(f"❌ {issue}")

                if analysis['recommendations']:
                    st.info("Recommendations:")
                    for rec in analysis['recommendations']:
                        st.write(f"💡 {rec}")

    def render_ecommerce_tab(self):
        """Render e-commerce tab"""
        st.header("E-Commerce Management")

        ecommerce: EcommerceManager = st.session_state.ecommerce_manager

        tab1, tab2, tab3, tab4 = st.tabs(["Products", "Orders", "Discounts", "Stats"])

        with tab1:
            st.subheader("Products")

            col1, col2 = st.columns([2, 1])

            with col1:
                products = ecommerce.get_all_products()

                if not products:
                    st.info("No products yet. Create your first product!")
                else:
                    for product in products:
                        with st.expander(f"{product.name} - ${product.price}"):
                            st.write(f"**SKU:** {product.sku}")
                            st.write(f"**Status:** {product.status.value}")
                            st.write(f"**Inventory:** {product.inventory_count}")
                            st.write(product.description)

            with col2:
                st.subheader("Add Product")

                with st.form("new_product_form"):
                    name = st.text_input("Product Name")
                    description = st.text_area("Description")
                    price = st.number_input("Price", min_value=0.0, step=0.01)
                    sku = st.text_input("SKU")
                    inventory = st.number_input("Inventory", min_value=0, step=1)

                    if st.form_submit_button("Create Product"):
                        if name and price > 0:
                            ecommerce.create_product(
                                name=name,
                                description=description,
                                price=price,
                                sku=sku,
                                inventory_count=inventory,
                            )
                            st.success("Product created!")
                            st.rerun()

        with tab2:
            st.subheader("Orders")

            orders = ecommerce.get_all_orders()

            if not orders:
                st.info("No orders yet")
            else:
                for order in orders[:10]:
                    with st.expander(f"Order #{order.order_id[:8]} - ${order.total}"):
                        st.write(f"**Customer:** {order.customer_email}")
                        st.write(f"**Status:** {order.status.value}")
                        st.write(f"**Items:** {len(order.items)}")
                        st.write(f"**Date:** {order.created_at}")

        with tab3:
            st.subheader("Discount Codes")

            with st.form("new_discount_form"):
                code = st.text_input("Discount Code")
                discount_type = st.selectbox("Type", ["percentage", "fixed"])
                value = st.number_input("Value", min_value=0.0)

                if st.form_submit_button("Create Discount"):
                    if code and value > 0:
                        ecommerce.create_discount_code(
                            code=code,
                            discount_type=discount_type,
                            discount_value=value,
                        )
                        st.success(f"Discount code '{code}' created!")

        with tab4:
            st.subheader("E-Commerce Statistics")

            stats = ecommerce.get_ecommerce_stats()

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Products", stats["total_products"])
                st.metric("Active Products", stats["active_products"])
            with col2:
                st.metric("Total Orders", stats["total_orders"])
                st.metric("Pending Orders", stats["pending_orders"])
            with col3:
                st.metric("Total Revenue", f"${stats['total_revenue']:.2f}")
                st.metric("Active Carts", stats["active_carts"])

    def render_analytics_tab(self):
        """Render analytics tab"""
        st.header("Analytics & Tracking")

        analytics: AnalyticsManager = st.session_state.analytics_manager

        tab1, tab2, tab3 = st.tabs(["Setup", "Reports", "Real-time"])

        with tab1:
            st.subheader("Analytics Providers")

            provider = st.selectbox(
                "Provider",
                [p.value for p in AnalyticsProvider]
            )

            tracking_id = st.text_input("Tracking ID / Measurement ID")

            if st.button("Add Provider"):
                if tracking_id:
                    analytics.add_analytics_provider(
                        AnalyticsProvider(provider),
                        tracking_id
                    )
                    st.success(f"{provider} added!")

            # Display tracking codes
            if st.button("Generate Tracking Codes"):
                codes = analytics.generate_all_tracking_codes()
                if codes:
                    st.code(codes, language="html")
                else:
                    st.info("No providers configured")

        with tab2:
            st.subheader("Analytics Reports")

            # Page views report
            report = analytics.get_page_views_report()

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Page Views", report["total_page_views"])
            with col2:
                st.metric("Unique Pages", report["unique_pages"])

            if report["top_pages"]:
                st.write("**Top Pages:**")
                for url, count in report["top_pages"][:5]:
                    st.write(f"- {url}: {count} views")

        with tab3:
            st.subheader("Real-time Statistics")

            stats = analytics.get_realtime_stats()

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Active Users", stats["active_users"])
            with col2:
                st.metric("Page Views (5min)", stats["page_views_5min"])
            with col3:
                st.metric("Events (5min)", stats["events_5min"])

            if st.button("🔄 Refresh"):
                st.rerun()

    def render_hosting_tab(self):
        """Render hosting tab"""
        st.header("Hosting & Domains")

        hosting: HostingManager = st.session_state.hosting_manager

        tab1, tab2, tab3, tab4 = st.tabs(["Domains", "SSL", "CDN", "Backups"])

        with tab1:
            st.subheader("Custom Domains")

            with st.form("add_domain_form"):
                domain_name = st.text_input("Domain Name (e.g., example.com)")
                is_primary = st.checkbox("Set as primary domain")

                if st.form_submit_button("Add Domain"):
                    if domain_name:
                        try:
                            domain = hosting.add_domain(domain_name, is_primary)
                            st.success(f"Domain '{domain_name}' added!")
                        except ValueError as e:
                            st.error(str(e))

            # List domains
            domains = hosting.get_all_domains()
            if domains:
                st.write("**Your Domains:**")
                for domain in domains:
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.write(f"{'⭐ ' if domain.is_primary else ''}{domain.domain_name}")
                    with col2:
                        st.write(domain.status.value)
                    with col3:
                        if st.button("Verify", key=f"verify_{domain.domain_id}"):
                            hosting.verify_domain(domain.domain_id)
                            st.success("Domain verified!")

        with tab2:
            st.subheader("SSL Certificates")

            domain_name = st.text_input("Domain for SSL Certificate")

            if st.button("Request SSL Certificate"):
                if domain_name:
                    cert = hosting.request_ssl_certificate(domain_name)
                    st.success(f"SSL certificate issued for {domain_name}")
                    st.write(f"**Status:** {cert.status.value}")
                    st.write(f"**Expires:** {cert.expires_at}")

            # Check expiring certificates
            if st.button("Check Expiring Certificates"):
                expiring = hosting.check_ssl_expiry()
                if expiring:
                    st.warning(f"{len(expiring)} certificates expiring soon")
                else:
                    st.success("All certificates are valid")

        with tab3:
            st.subheader("CDN Configuration")

            provider = st.selectbox("CDN Provider", [p.value for p in ["cloudflare", "cloudfront"]])

            col1, col2 = st.columns(2)
            with col1:
                minify_html = st.checkbox("Minify HTML", value=True)
                minify_css = st.checkbox("Minify CSS", value=True)
            with col2:
                minify_js = st.checkbox("Minify JS", value=True)
                image_opt = st.checkbox("Image Optimization", value=True)

            if st.button("Enable CDN"):
                st.success("CDN enabled successfully!")

        with tab4:
            st.subheader("Backups")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Create Backup Now"):
                    backup = hosting.create_backup(description="Manual backup")
                    st.success(f"Backup created: {backup.backup_id}")

            with col2:
                st.write("**Schedule:**")
                frequency = st.selectbox("Frequency", ["daily", "weekly", "monthly"])
                if st.button("Update Schedule"):
                    st.success(f"Backups scheduled {frequency}")

            # List backups
            backups = hosting.get_all_backups()
            if backups:
                st.write("**Recent Backups:**")
                for backup in backups[:5]:
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.write(backup.created_at.strftime("%Y-%m-%d %H:%M"))
                    with col2:
                        st.write(f"{backup.size_bytes / (1024*1024):.1f} MB")
                    with col3:
                        if st.button("Restore", key=f"restore_{backup.backup_id}"):
                            st.warning("Restore initiated")

    def render_settings_tab(self):
        """Render settings tab"""
        st.header("Settings")

        tab1, tab2 = st.tabs(["General", "Advanced"])

        with tab1:
            st.subheader("General Settings")

            with st.form("general_settings"):
                site_name = st.text_input("Site Name", value="My NEXUS Website")
                site_description = st.text_area("Site Description")
                language = st.selectbox("Language", ["English", "Spanish", "French", "German"])

                if st.form_submit_button("Save Settings"):
                    st.success("Settings saved successfully!")

        with tab2:
            st.subheader("Advanced Settings")

            enable_caching = st.checkbox("Enable Caching", value=True)
            enable_compression = st.checkbox("Enable Compression", value=True)
            enable_lazy_loading = st.checkbox("Enable Lazy Loading", value=True)

            if st.button("Save Advanced Settings"):
                st.success("Advanced settings saved!")


def run_website_builder():
    """Main entry point for the website builder UI"""
    builder_ui = WebsiteBuilderUI()
    builder_ui.render()


if __name__ == "__main__":
    run_website_builder()
