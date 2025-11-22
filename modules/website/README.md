# NEXUS Website Builder & CMS Module

A professional no-code website builder with drag-drop interface, templates, e-commerce, SEO tools, and hosting capabilities. Rivals Wix, Webflow, and Squarespace!

## Features

### 1. Visual Drag-Drop Builder 🎨
- **Visual Page Editor**: Intuitive drag-and-drop interface
- **100+ Components**: Headers, footers, forms, galleries, and more
- **Responsive Preview**: Desktop, tablet, and mobile views
- **Live Editing**: Real-time visual feedback
- **Undo/Redo**: Full history management
- **Grid & Snap**: Precision layout tools

### 2. Professional Templates 🎯
- **50+ Templates**: Business, portfolio, blog, e-commerce, landing pages
- **Categories**:
  - Business (Corporate, Startup, Consulting, Small Business)
  - Portfolio (Creative, Developer, Photography, Minimalist)
  - Blog (Personal, Magazine, Tech)
  - E-commerce (Fashion, Electronics, Handmade)
  - Landing Pages (SaaS, App, Product Launch, Webinar)
  - Agency (Creative, Digital)
  - Restaurant (Fine Dining, Cafe)
  - Education (Online Course, University)
  - Health (Medical Clinic, Fitness Center)
  - Events (Conference, Wedding)
  - Non-profit (Charity)
  - And more!

### 3. Component Library 🧩
- **Layout**: Container, Row, Column, Section, Divider, Spacer
- **Navigation**: Header, Nav Menu, Breadcrumb, Sidebar, Tabs
- **Content**: Heading, Paragraph, Button, List, Quote, Accordion, Alert, Code Block
- **Media**: Image, Gallery, Video, Icon, Slider
- **Forms**: Form, Input, Textarea, Select, Checkbox, Radio
- **Hero Sections**: Full-width hero with background images
- **Features**: Feature boxes and grids
- **Testimonials**: Customer testimonial cards
- **Pricing**: Pricing tables and plans
- **Team**: Team member profiles
- **Contact**: Contact forms and maps
- **Footer**: Site footers
- **E-commerce**: Product cards, shopping cart
- **Widgets**: Progress bars, counters, modals, countdown timers
- **Social**: Social icons, share buttons

### 4. Multi-Page Support 📄
- **Unlimited Pages**: Create as many pages as needed
- **Page Types**: Static, Dynamic, Blog Posts, Products, Categories
- **URL Routing**: Clean, SEO-friendly URLs
- **Nested Pages**: Parent-child page hierarchy
- **Page Status**: Draft, Published, Archived, Scheduled
- **Breadcrumbs**: Automatic breadcrumb navigation
- **Sitemap**: Auto-generated XML sitemap

### 5. SEO Optimization 🔍
- **Meta Tags**: Title, description, keywords
- **Open Graph**: Social media preview optimization
- **Twitter Cards**: Twitter-specific meta tags
- **Structured Data**: Schema.org JSON-LD support
  - Organization, Website, Article, Product, LocalBusiness, FAQ, and more
- **Site Verification**: Google and Bing verification tags
- **Robots.txt**: Customizable robots.txt
- **SEO Analysis**: Page-level SEO scoring and recommendations
- **Canonical URLs**: Duplicate content prevention

### 6. E-Commerce 🛒
- **Product Management**: Full product catalog
- **Variants**: Product variants and options
- **Inventory**: Stock tracking
- **Shopping Cart**: Full-featured cart
- **Checkout**: Complete checkout flow
- **Orders**: Order management system
- **Discount Codes**: Coupon and discount system
- **Payment Integration**: Stripe, PayPal, Square, Razorpay, Braintree
- **Sales Reports**: Revenue and sales analytics
- **Tax Calculation**: Automatic tax calculation

### 7. Hosting & Domains 🌐
- **Custom Domains**: Add your own domain
- **SSL Certificates**: Free SSL with auto-renewal
- **DNS Management**: Full DNS control
- **CDN Integration**: Cloudflare, CloudFront, Fastly, Akamai
- **Asset Optimization**: Minification and compression
- **Image Optimization**: Automatic image optimization
- **Backups**: Automated backup system
- **Deployments**: Version control and rollbacks

### 8. Analytics 📊
- **Google Analytics**: GA and GA4 support
- **Facebook Pixel**: Facebook tracking
- **Mixpanel**: Product analytics
- **Hotjar**: Heatmaps and recordings
- **Matomo**: Privacy-focused analytics
- **Custom Events**: Track custom user actions
- **Page Views**: Detailed page view tracking
- **Conversion Funnels**: Track user journeys
- **Real-time Stats**: Live visitor tracking
- **Reports**: Comprehensive analytics reports

## Installation

```bash
# Install dependencies
pip install streamlit

# Import the module
from modules.website import WebsiteBuilder, TemplateManager, ComponentLibrary
```

## Quick Start

### 1. Create a Website Builder

```python
from modules.website import WebsiteBuilder, BuilderConfig

# Configure the builder
config = BuilderConfig(
    project_id="my_website",
    project_name="My Awesome Website",
    auto_save=True,
    enable_responsive=True,
)

# Initialize builder
builder = WebsiteBuilder(config)

# Create a new project
project = builder.create_project()
```

### 2. Use Templates

```python
from modules.website import TemplateManager, TemplateCategory

# Initialize template manager
template_manager = TemplateManager()

# Get all templates
all_templates = template_manager.get_all_templates()

# Get templates by category
business_templates = template_manager.get_templates_by_category(
    TemplateCategory.BUSINESS
)

# Apply a template
template_data = template_manager.apply_template("corporate_business")
```

### 3. Manage Pages

```python
from modules.website import PageManager, PageType

# Initialize page manager
page_manager = PageManager()

# Create a page
page = page_manager.create_page(
    title="Home",
    slug="home",
    page_type=PageType.STATIC,
)

# Publish the page
page_manager.publish_page(page.page_id)

# Get page URL
url = page_manager.get_page_url(page.page_id)
```

### 4. Add Components

```python
from modules.website import ComponentLibrary, ComponentCategory

# Initialize component library
library = ComponentLibrary()

# Get all components
all_components = library.get_all_components()

# Get components by category
layout_components = library.get_components_by_category(
    ComponentCategory.LAYOUT
)

# Get a specific component
button = library.get_component("button")
```

### 5. Configure SEO

```python
from modules.website import SEOManager, SEOConfig

# Configure SEO
seo_config = SEOConfig(
    site_name="My Website",
    site_url="https://example.com",
    default_title="Welcome to My Website",
    default_description="An amazing website built with NEXUS",
)

# Initialize SEO manager
seo_manager = SEOManager(seo_config)

# Generate meta tags
meta_tags = seo_manager.generate_all_meta_tags(
    title="Home Page",
    description="Welcome to our homepage",
    keywords=["nexus", "website", "builder"],
)

# Create structured data
org_schema = seo_manager.create_organization_schema(
    name="My Company",
    url="https://example.com",
    logo="https://example.com/logo.png",
)
```

### 6. Set Up E-Commerce

```python
from modules.website import EcommerceManager

# Initialize e-commerce
ecommerce = EcommerceManager()

# Create a product
product = ecommerce.create_product(
    name="Cool Product",
    description="An awesome product",
    price=29.99,
    sku="PROD-001",
    inventory_count=100,
)

# Create shopping cart
cart = ecommerce.create_cart()

# Add to cart
ecommerce.add_to_cart(cart.cart_id, product.product_id, quantity=2)

# Create order
order = ecommerce.create_order(
    cart_id=cart.cart_id,
    customer_email="customer@example.com",
    payment_method="stripe",
    shipping_address={
        "street": "123 Main St",
        "city": "Test City",
        "state": "TS",
        "zip": "12345",
    },
)
```

### 7. Configure Hosting

```python
from modules.website import HostingManager

# Initialize hosting
hosting = HostingManager()

# Add custom domain
domain = hosting.add_domain("example.com", is_primary=True)

# Request SSL certificate
ssl_cert = hosting.request_ssl_certificate("example.com")

# Setup CDN
from modules.website.hosting import CDNProvider
cdn = hosting.setup_cdn(CDNProvider.CLOUDFLARE)

# Create backup
backup = hosting.create_backup(description="Daily backup")
```

### 8. Add Analytics

```python
from modules.website import AnalyticsManager, AnalyticsProvider

# Initialize analytics
analytics = AnalyticsManager()

# Add Google Analytics
analytics.add_analytics_provider(
    AnalyticsProvider.GOOGLE_ANALYTICS_4,
    tracking_id="G-XXXXXXXXXX",
)

# Generate tracking code
tracking_code = analytics.generate_all_tracking_codes()

# Track events
analytics.track_event(
    event_type=EventType.PURCHASE,
    event_name="product_purchased",
    properties={"product_id": "123", "value": 29.99},
)

# Get analytics report
report = analytics.get_page_views_report()
```

## Running the UI

### Streamlit Interface

```bash
# Run the Streamlit UI
streamlit run modules/website/streamlit_ui.py
```

Or import and run programmatically:

```python
from modules.website.streamlit_ui import run_website_builder

run_website_builder()
```

## Architecture

The module is organized into focused, single-responsibility components:

```
modules/website/
├── __init__.py              # Module exports
├── builder.py               # Core builder logic
├── components.py            # Component library (100+ components)
├── templates.py             # Template manager (50+ templates)
├── pages.py                 # Page management & routing
├── seo.py                   # SEO optimization
├── hosting.py               # Hosting & domain management
├── analytics.py             # Analytics integration
├── ecommerce.py             # E-commerce functionality
├── streamlit_ui.py          # Streamlit interface
├── tests/                   # Comprehensive test suite
│   ├── __init__.py
│   ├── test_builder.py
│   ├── test_components.py
│   ├── test_pages.py
│   └── test_ecommerce.py
└── README.md                # This file
```

## Testing

```bash
# Run all tests
pytest modules/website/tests/ -v

# Run specific test file
pytest modules/website/tests/test_builder.py -v

# Run with coverage
pytest modules/website/tests/ --cov=modules.website --cov-report=html
```

## API Reference

### Builder API

- `WebsiteBuilder(config)`: Initialize builder
- `create_project()`: Create new project
- `initialize_builder(page_id)`: Initialize for page
- `add_component(...)`: Add component to canvas
- `remove_component(component_id)`: Remove component
- `update_component(...)`: Update component properties
- `duplicate_component(component_id)`: Duplicate component
- `undo()`: Undo last action
- `redo()`: Redo last undone action
- `save_state()`: Save current state
- `load_state(data)`: Load saved state

### Template API

- `TemplateManager()`: Initialize manager
- `get_all_templates()`: Get all templates
- `get_templates_by_category(category)`: Filter by category
- `search_templates(query)`: Search templates
- `apply_template(template_id)`: Apply template

### Component API

- `ComponentLibrary()`: Initialize library
- `get_all_components()`: Get all components
- `get_components_by_category(category)`: Filter by category
- `get_component(component_id)`: Get specific component
- `search_components(query)`: Search components

### Page API

- `PageManager()`: Initialize manager
- `create_page(...)`: Create new page
- `publish_page(page_id)`: Publish page
- `get_page_hierarchy()`: Get page tree
- `export_sitemap()`: Generate sitemap XML

### SEO API

- `SEOManager(config)`: Initialize SEO
- `generate_meta_tags(...)`: Generate meta tags
- `generate_open_graph_tags(...)`: Generate OG tags
- `create_structured_data(...)`: Create schema markup
- `analyze_seo_score(...)`: Analyze SEO quality

### E-commerce API

- `EcommerceManager()`: Initialize e-commerce
- `create_product(...)`: Create product
- `create_cart()`: Create shopping cart
- `add_to_cart(...)`: Add item to cart
- `create_order(...)`: Create order
- `create_discount_code(...)`: Create discount

### Hosting API

- `HostingManager()`: Initialize hosting
- `add_domain(...)`: Add custom domain
- `request_ssl_certificate(...)`: Get SSL cert
- `setup_cdn(...)`: Configure CDN
- `create_backup(...)`: Create backup

### Analytics API

- `AnalyticsManager()`: Initialize analytics
- `add_analytics_provider(...)`: Add provider
- `generate_tracking_codes()`: Generate codes
- `track_event(...)`: Track event
- `get_page_views_report()`: Get report

## Production Deployment

### Requirements

```txt
streamlit>=1.28.0
python>=3.8
```

### Environment Variables

```bash
# Set in production
export NEXUS_ENV=production
export NEXUS_SITE_URL=https://yoursite.com
export STRIPE_API_KEY=your_stripe_key
export GA_TRACKING_ID=your_ga_id
```

### Security Best Practices

1. **API Keys**: Store in environment variables
2. **SSL**: Always enable SSL in production
3. **Backups**: Schedule regular backups
4. **Input Validation**: All user inputs are validated
5. **XSS Prevention**: HTML is sanitized
6. **CSRF Protection**: Forms use CSRF tokens

## Performance Optimization

- **Lazy Loading**: Images and components
- **CDN**: Asset delivery via CDN
- **Caching**: Browser and server-side caching
- **Minification**: HTML, CSS, JS minification
- **Compression**: Gzip compression
- **Image Optimization**: Automatic image compression

## Browser Support

- Chrome (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Edge (latest 2 versions)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Contributing

This module is part of the NEXUS platform. For contributions:

1. Follow PEP 8 style guide
2. Add type hints to all functions
3. Write tests for new features
4. Update documentation

## License

Part of the NEXUS platform. All rights reserved.

## Support

For issues, questions, or feature requests, please contact the NEXUS development team.

---

**Built with ❤️ by the NEXUS team**

*Rivaling Wix, Webflow, and Squarespace with powerful no-code website building!*
