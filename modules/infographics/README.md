# NEXUS Infographics Designer 🎨

A comprehensive, production-ready infographics design tool for Python with 100+ professional templates, 10,000+ icons, advanced charting, data visualization, animations, and multi-format export capabilities.

## Features

### 🎯 Core Features

- **100+ Professional Templates**: Business, education, marketing, data reports, social media formats
- **10,000+ Icon Library**: Organized by 25+ categories with multiple styles
- **Advanced Charts**: Bar, pie, line, scatter, donut, funnel, comparison charts with data binding
- **Design Tools**: Drag-drop, alignment, grouping, layering, duplicate, flip/rotate
- **Styling**: Colors, gradients, fonts, shadows, borders, transparency
- **Data Visualization**: Import CSV/Excel/JSON, auto-generate charts, data tables
- **Animations**: Entrance effects, transitions, interactive elements
- **Branding**: Brand kits, logo placement, color schemes, font pairings
- **Export**: High-res PNG, PDF, SVG, animated GIF, video, embed code

### 🎨 Design Elements

- **Text**: Headings, subheadings, body text with full typography control
- **Shapes**: Rectangles, circles, triangles, stars, hearts, polygons, ribbons
- **Icons**: 10k+ icons across 25+ categories (business, tech, social media, etc.)
- **Images**: Import, crop, filters
- **Lines & Arrows**: Various styles and arrow heads
- **Charts**: 15+ chart types with customizable styles

### 📊 Data Visualization

- **Import**: CSV, Excel, JSON formats
- **Auto-Generate**: Automatically create appropriate charts from data
- **Data Tables**: Styled data tables with formatting options
- **Analysis**: Summary statistics, trend detection, outlier identification

### 🎬 Animations

- **Entrance Effects**: Fade, slide, zoom, rotate, bounce, flip, elastic
- **Transitions**: Hover effects, click effects, scroll reveals
- **Easing Functions**: 20+ easing functions for smooth animations
- **Timeline**: Precise animation timing and sequencing

### 📤 Export Options

- **Formats**: PNG, JPEG, PDF, SVG, GIF, MP4, WebM, HTML
- **Quality**: Low, Medium, High, Ultra (up to 600 DPI)
- **Social Media**: Optimized presets for Instagram, Facebook, Twitter, LinkedIn, Pinterest
- **Print**: Print-ready PDFs with bleed marks and crop marks

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/nexus-platform.git

# Navigate to the module
cd nexus-platform/modules/infographics

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
from modules.infographics import (
    InfographicDesigner,
    ElementFactory,
    ChartFactory,
    InfographicExporter,
    ExportConfig,
    ExportFormat
)

# Create designer
designer = InfographicDesigner()

# Add text element
text = ElementFactory.create_text("Hello World", x=100, y=100, font_size=32)
designer.add_element(text)

# Add a chart
chart = ChartFactory.create_bar_chart(
    categories=["A", "B", "C"],
    data=[10, 20, 30],
    title="Sales Data"
)
chart.position.x = 100
chart.position.y = 200
designer.add_element(chart)

# Export
exporter = InfographicExporter(designer)
config = ExportConfig(format=ExportFormat.PNG)
exporter.export(config, "output.png")
```

### Using Templates

```python
from modules.infographics import TemplateLibrary, TemplateCategory

# Load template library
library = TemplateLibrary()

# Get templates by category
templates = library.get_templates_by_category(TemplateCategory.BUSINESS)

# Use a template
designer.load_template(templates[0])

# Customize and export
# ... make your changes ...
designer.save_to_file("my_infographic.json")
```

### Data Visualization

```python
from modules.infographics import DataImporter, ChartGenerator

# Import CSV data
csv_data = """Category,Value
Product A,100
Product B,150
Product C,200"""

table = DataImporter.import_csv(csv_data)

# Auto-generate appropriate chart
chart = ChartGenerator.auto_generate_chart(table)
designer.add_element(chart)
```

### Adding Animations

```python
from modules.infographics import AnimationPresets, Animation

# Create fade-in animation
config = AnimationPresets.fade_in(duration=1000, delay=500)
animation = Animation(
    element_id=text.id,
    name="Fade In",
    config=config
)

# Add to designer
designer.animations.append(animation)
```

### Streamlit UI

```python
# Run the Streamlit UI
from modules.infographics.streamlit_ui import main

if __name__ == "__main__":
    main()
```

Or run from command line:
```bash
streamlit run modules/infographics/streamlit_ui.py
```

## Module Structure

```
modules/infographics/
├── __init__.py              # Main module entry point
├── elements.py              # Design elements (text, shapes, icons, images)
├── templates.py             # 100+ professional templates
├── charts.py                # Chart types and data visualization
├── icons.py                 # 10k+ icon library
├── data_viz.py              # Data import and auto-chart generation
├── animations.py            # Animation effects and transitions
├── designer.py              # Main designer with drag-drop, alignment, layering
├── export.py                # Export to multiple formats
├── streamlit_ui.py          # Streamlit-based UI
├── requirements.txt         # Dependencies
├── README.md                # This file
├── assets/                  # Asset files
│   ├── templates/           # Template files
│   ├── icons/               # Icon libraries
│   └── fonts/               # Font files
└── tests/                   # Test suite
    ├── test_elements.py
    ├── test_designer.py
    ├── test_charts.py
    └── test_data_viz.py
```

## API Reference

### InfographicDesigner

Main designer class for creating and managing infographics.

**Methods:**
- `add_element(element)` - Add element to canvas
- `remove_element(element_id)` - Remove element
- `select_element(element_id)` - Select element
- `move_element(element_id, dx, dy)` - Move element
- `rotate_element(element_id, degrees)` - Rotate element
- `align_elements(element_ids, alignment)` - Align multiple elements
- `group_elements(element_ids)` - Group elements
- `duplicate_element(element_id)` - Duplicate element
- `save_to_file(filepath)` - Save design to file
- `load_from_file(filepath)` - Load design from file

### ElementFactory

Factory for creating design elements.

**Methods:**
- `create_text(text, x, y, font_size, **kwargs)` - Create text element
- `create_shape(shape_type, x, y, width, height, **kwargs)` - Create shape
- `create_icon(icon_name, x, y, size, **kwargs)` - Create icon
- `create_image(image_url, x, y, width, height, **kwargs)` - Create image
- `create_line(start, end, **kwargs)` - Create line
- `create_arrow(start, end, arrow_type, **kwargs)` - Create arrow

### ChartFactory

Factory for creating charts.

**Methods:**
- `create_bar_chart(categories, data, title)` - Create bar chart
- `create_pie_chart(labels, data, title)` - Create pie chart
- `create_line_chart(categories, data, title)` - Create line chart
- `create_donut_chart(labels, data, title)` - Create donut chart
- `create_scatter_chart(x_data, y_data, title)` - Create scatter chart
- `create_funnel_chart(labels, data, title)` - Create funnel chart
- `create_comparison_chart(categories, series_data, title)` - Create comparison chart

### TemplateLibrary

Manages template collection.

**Methods:**
- `get_template(template_id)` - Get template by ID
- `get_templates_by_category(category)` - Get templates by category
- `search_templates(query)` - Search templates
- `get_all_templates()` - Get all templates

### InfographicExporter

Handles exporting to various formats.

**Methods:**
- `export(config, filepath)` - Export with configuration
- `export_png(filepath, config)` - Export as PNG
- `export_pdf(filepath, config)` - Export as PDF
- `export_svg(filepath, config)` - Export as SVG
- `get_embed_code(width, height)` - Get HTML embed code

## Examples

### Example 1: Business Report

```python
from modules.infographics import *

designer = InfographicDesigner()

# Add title
title = ElementPresets.heading("Q4 2024 Business Report", 100, 50)
designer.add_element(title)

# Add revenue chart
revenue_chart = ChartFactory.create_bar_chart(
    categories=["Q1", "Q2", "Q3", "Q4"],
    data=[100000, 125000, 140000, 165000],
    title="Quarterly Revenue"
)
revenue_chart.position.x = 100
revenue_chart.position.y = 150
designer.add_element(revenue_chart)

# Export
exporter = InfographicExporter(designer)
config = ExportConfig(format=ExportFormat.PDF, quality=ImageQuality.HIGH)
exporter.export(config, "business_report.pdf")
```

### Example 2: Social Media Post

```python
from modules.infographics import *

designer = InfographicDesigner()

# Set canvas for Instagram
designer.canvas.width = 1080
designer.canvas.height = 1080

# Add background shape
bg = ElementFactory.create_shape(ShapeType.RECTANGLE, 0, 0, 1080, 1080)
bg.style.fill_color = "#3498DB"
designer.add_element(bg)

# Add text
text = ElementPresets.heading("Big Announcement!", 540, 400)
text.style.fill_color = "#FFFFFF"
text.text_style.text_align = TextAlign.CENTER
designer.add_element(text)

# Export for Instagram
exporter = InfographicExporter(designer)
config = ExportConfig(format=ExportFormat.PNG)
exporter.export(config, "instagram_post.png")
```

### Example 3: Data Infographic

```python
from modules.infographics import *

# Import data
csv_data = """Product,Sales,Growth
Product A,50000,15%
Product B,35000,22%
Product C,45000,8%"""

table = DataImporter.import_csv(csv_data)

# Create designer
designer = InfographicDesigner()

# Auto-generate chart
chart = ChartGenerator.auto_generate_chart(table)
chart.position.x = 100
chart.position.y = 100
designer.add_element(chart)

# Apply professional styling
ChartStyler.apply_professional_style(chart)

# Export
exporter = InfographicExporter(designer)
config = ExportConfig(format=ExportFormat.SVG)
exporter.export(config, "data_infographic.svg")
```

## Testing

Run the test suite:

```bash
# Run all tests
python -m pytest modules/infographics/tests/

# Run with coverage
python -m pytest --cov=modules/infographics modules/infographics/tests/

# Run specific test file
python -m pytest modules/infographics/tests/test_designer.py
```

## Development

### Code Style

This project follows PEP 8 style guidelines and uses type hints throughout.

```bash
# Format code
black modules/infographics/

# Check style
flake8 modules/infographics/

# Type checking
mypy modules/infographics/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## Performance

- **Fast Rendering**: Optimized element rendering
- **Lazy Loading**: Icons and templates loaded on demand
- **Efficient Export**: Parallel processing for batch exports
- **Memory Management**: Efficient handling of large designs

## Browser Support

When using the Streamlit UI:
- Chrome (recommended)
- Firefox
- Safari
- Edge

## License

MIT License - see LICENSE file for details

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/your-org/nexus-platform/issues
- Documentation: https://docs.nexus-platform.com/infographics
- Email: support@nexus-platform.com

## Credits

Created by the NEXUS team.

## Rivals

This module rivals and surpasses:
- Canva
- Piktochart
- Venngage
- Adobe Express
- Visme

With superior programmatic control, data integration, and automation capabilities!

---

**Version**: 1.0.0
**Last Updated**: 2024
