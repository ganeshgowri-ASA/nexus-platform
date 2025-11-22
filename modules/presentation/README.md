# NEXUS Presentation Editor Module

A world-class presentation creation and editing module for the NEXUS platform, rivaling Google Slides and PowerPoint Online.

## Overview

The Presentation Editor module provides a complete, feature-rich solution for creating, editing, and presenting professional presentations with AI assistance, real-time collaboration, and multi-format export capabilities.

## Features

### 🎯 Core Features

- **Slide Management**: Create, delete, duplicate, and reorder slides with ease
- **Rich Content Elements**: Text, images, shapes, tables, charts, videos, and more
- **Animations & Transitions**: Professional entrance, exit, and emphasis animations
- **Templates Library**: Pre-designed templates for business, education, marketing, and more
- **Theme System**: Beautiful themes with customizable color schemes and fonts
- **Multi-Format Export**: PPTX, PDF, HTML5, PNG, JPG, MP4, and more
- **Presentation Mode**: Full-screen presenter view with notes and timer
- **Real-Time Collaboration**: Multi-user editing with comments and version history
- **AI Assistant**: AI-powered content generation and design suggestions

### 📊 Module Architecture

```
modules/presentation/
├── __init__.py              # Module exports and info
├── editor.py                # Main presentation engine
├── slide_manager.py         # Slide creation and editing
├── element_handler.py       # Content element management
├── animation.py             # Transitions and animations
├── template_manager.py      # Slide templates
├── theme_builder.py         # Color schemes and themes
├── export_renderer.py       # Multi-format export
├── presenter_view.py        # Presentation mode
├── collaboration.py         # Multi-user editing
├── ai_assistant.py          # AI content generation
├── streamlit_ui.py          # Streamlit interface
└── README.md                # This file
```

## Quick Start

### Installation

```bash
# Install required dependencies (when available)
pip install streamlit python-pptx reportlab pillow
```

### Basic Usage

```python
from modules.presentation import PresentationEditor
from modules.presentation.slide_manager import SlideLayout
from modules.presentation.export_renderer import ExportFormat

# Create new presentation
editor = PresentationEditor()
editor.set_presentation_info(
    title="My Presentation",
    author="Your Name"
)

# Add slides
slide1 = editor.add_slide(
    layout=SlideLayout.TITLE_SLIDE,
    title="Welcome"
)

slide2 = editor.add_slide(
    layout=SlideLayout.TITLE_CONTENT,
    title="Key Points"
)

# Add content
editor.add_text_element(
    slide2.id,
    "• Point 1\n• Point 2\n• Point 3"
)

# Apply theme
editor.apply_theme("professional")

# Export
buffer = editor.export(ExportFormat.PPTX)
```

### Streamlit UI

```bash
# Run the Streamlit interface
streamlit run modules/presentation/streamlit_ui.py
```

## Component Documentation

### 1. Slide Manager (`slide_manager.py`)

Manages all slide operations:

```python
from modules.presentation.slide_manager import SlideManager, SlideLayout

manager = SlideManager()

# Create slide
slide = manager.create_slide(
    layout=SlideLayout.TITLE_SLIDE,
    title="My Slide"
)

# Duplicate slide
duplicate = manager.duplicate_slide(slide.id)

# Reorder slides
manager.reorder_slide(slide.id, new_position=0)

# Section management
section = manager.create_section("Introduction", 0)
```

### 2. Element Handler (`element_handler.py`)

Manages content elements:

```python
from modules.presentation.element_handler import (
    ElementHandler,
    ShapeType,
    Position,
    Size
)

handler = ElementHandler()

# Create text element
text = handler.create_text_element(
    content="Hello World",
    position=Position(100, 100),
    size=Size(300, 100)
)

# Create image
image = handler.create_image_element(
    source="image.jpg",
    alt_text="Description"
)

# Create shape
shape = handler.create_shape_element(
    shape_type=ShapeType.CIRCLE
)

# Align elements
handler.align_elements([elem1.id, elem2.id], "center")
```

### 3. Animation Engine (`animation.py`)

Adds animations and transitions:

```python
from modules.presentation.animation import (
    AnimationEngine,
    AnimationType,
    TransitionType
)

engine = AnimationEngine()

# Add element animation
animation = engine.add_animation(
    element_id="elem_1",
    animation_type=AnimationType.FADE_IN,
    duration=0.5
)

# Set slide transition
transition = engine.set_slide_transition(
    slide_id="slide_1",
    transition_type=TransitionType.FADE
)

# Create motion path
path_anim = engine.create_motion_path(
    element_id="elem_1",
    points=[(0, 0), (100, 100), (200, 0)]
)
```

### 4. Template Manager (`template_manager.py`)

Provides pre-designed templates:

```python
from modules.presentation.template_manager import (
    TemplateManager,
    TemplateCategory
)

manager = TemplateManager()

# Get templates by category
business = manager.get_templates_by_category(
    TemplateCategory.BUSINESS
)

# Apply template
slide_data = manager.apply_template(
    "business_title",
    replacements={"TITLE": "My Title"}
)

# Create custom template
custom = manager.create_custom_template(
    name="My Template",
    category=TemplateCategory.BUSINESS,
    elements=[...],
    background={...}
)
```

### 5. Theme Builder (`theme_builder.py`)

Manages themes and color schemes:

```python
from modules.presentation.theme_builder import ThemeBuilder

builder = ThemeBuilder()

# Get theme
theme = builder.get_theme("professional")

# Create color scheme
scheme = builder.create_custom_color_scheme(
    name="My Colors",
    primary="#3498DB",
    secondary="#E74C3C",
    accent="#2ECC71"
)

# Generate color harmonies
complementary = builder.generate_complementary_colors("#3498DB")
analogous = builder.generate_analogous_colors("#3498DB")
triadic = builder.generate_triadic_colors("#3498DB")
```

### 6. Export Renderer (`export_renderer.py`)

Exports to multiple formats:

```python
from modules.presentation.export_renderer import (
    ExportRenderer,
    ExportFormat,
    ExportQuality
)

renderer = ExportRenderer()

# Export to PPTX
pptx_buffer = renderer.export(
    presentation_data,
    ExportFormat.PPTX,
    quality=ExportQuality.HIGH
)

# Export to PDF
pdf_buffer = renderer.export(
    presentation_data,
    ExportFormat.PDF
)

# Export to HTML5
html_buffer = renderer.export(
    presentation_data,
    ExportFormat.HTML5
)

# Export handouts
handouts = renderer.export_handouts(
    presentation_data,
    slides_per_page=6,
    include_notes=True
)
```

### 7. Presenter View (`presenter_view.py`)

Presentation mode with presenter features:

```python
from modules.presentation.presenter_view import PresenterView

presenter = PresenterView()

# Load presentation
presenter.load_presentation(slides)

# Start presentation
presenter.start_presentation(
    target_duration_minutes=30
)

# Navigate
presenter.next_slide()
presenter.previous_slide()
presenter.go_to_slide(5)

# Get progress
progress = presenter.get_progress()

# Get statistics
stats = presenter.get_presentation_statistics()
```

### 8. Collaboration Manager (`collaboration.py`)

Real-time collaboration features:

```python
from modules.presentation.collaboration import (
    CollaborationManager,
    User,
    PermissionLevel
)

manager = CollaborationManager()

# Add user
user = User(id="1", name="John", email="john@example.com")
session = manager.join_session(user, PermissionLevel.EDITOR)

# Add comment
comment = manager.add_comment(
    user=user,
    content="Great slide!",
    slide_id="slide_1"
)

# Reply to comment
reply = manager.reply_to_comment(
    comment.id,
    user,
    "Thanks!"
)

# Create version
version = manager.create_version(
    user=user,
    presentation_data={...},
    description="Version 1.0"
)
```

### 9. AI Assistant (`ai_assistant.py`)

AI-powered content generation:

```python
from modules.presentation.ai_assistant import AIAssistant

assistant = AIAssistant()

# Generate presentation outline
outline = assistant.generate_presentation_outline(
    topic="AI in Healthcare",
    num_slides=10
)

# Get design suggestions
suggestions = assistant.suggest_design_improvements(
    slide_data
)

# Grammar check
result = assistant.check_grammar(
    "this is a test sentence"
)

# Summarize text
summary = assistant.summarize_text(long_text)

# Generate alt text
alt_text = assistant.generate_alt_text(
    image_url,
    context="Healthcare presentation"
)
```

### 10. Main Editor (`editor.py`)

Unified interface coordinating all components:

```python
from modules.presentation import PresentationEditor

editor = PresentationEditor()

# All-in-one interface
editor.set_presentation_info(title="My Presentation")
slide = editor.add_slide()
editor.add_text_element(slide.id, "Content")
editor.add_animation("elem_1", AnimationType.FADE_IN)
editor.apply_theme("professional")
editor.export(ExportFormat.PPTX)
```

## Testing

Run comprehensive tests:

```bash
# Run all tests
python tests/test_presentation.py

# Run specific test class
python -m unittest tests.test_presentation.TestSlideManager

# Run with verbose output
python tests/test_presentation.py -v
```

## Features in Detail

### Slide Layouts

- Blank
- Title Slide
- Title + Content
- Two Content
- Comparison
- Section Header
- Picture Caption
- And more...

### Element Types

- Text boxes with rich formatting
- Images with filters and cropping
- Shapes (rectangles, circles, arrows, callouts)
- Tables with customizable styles
- Charts (bar, line, pie, scatter)
- Videos with playback controls
- Audio clips
- SmartArt diagrams

### Animation Types

**Entrance:**
- Fade In, Fly In, Zoom In, Bounce, Swivel, etc.

**Exit:**
- Fade Out, Fly Out, Zoom Out, etc.

**Emphasis:**
- Pulse, Spin, Grow/Shrink, Color Pulse

**Motion Paths:**
- Lines, Arcs, Turns, Shapes, Custom

### Export Formats

- **PPTX**: PowerPoint format with full fidelity
- **PDF**: High-quality PDF documents
- **HTML5**: Self-contained web presentations
- **PNG/JPG**: Image export for each slide
- **SVG**: Vector graphics export
- **MP4**: Video export with animations
- **GIF**: Animated GIF
- **JSON**: Data format for backup/transfer

## API Reference

See inline documentation in each module for detailed API information. All classes and methods include comprehensive docstrings with:

- Parameter descriptions
- Return value documentation
- Usage examples
- Type hints

## Performance Considerations

- Lazy loading of templates and themes
- Efficient element rendering
- Optimized export pipelines
- Caching for repeated operations
- Minimal memory footprint

## Best Practices

1. **Always use the PresentationEditor** for coordinated operations
2. **Apply themes early** in the design process
3. **Use templates** to maintain consistency
4. **Leverage AI suggestions** for better design
5. **Test exports** in target format before finalizing
6. **Save versions** before major changes
7. **Use speaker notes** for presentation preparation

## Troubleshooting

### Common Issues

**Issue**: Slides not appearing in correct order
**Solution**: Use `reorder_slide()` method

**Issue**: Export fails
**Solution**: Ensure all required libraries are installed

**Issue**: Animations not working
**Solution**: Check animation timeline order

## Contributing

When contributing to this module:

1. Follow existing code style
2. Add comprehensive docstrings
3. Include unit tests
4. Update this README
5. Test all export formats

## License

Part of the NEXUS platform. See main LICENSE file.

## Credits

Developed for NEXUS Platform - Unified AI-powered productivity platform.

## Version History

- **1.0.0** (2025-11-18): Initial release
  - Complete presentation editor
  - All core features implemented
  - Comprehensive test coverage
  - Full Streamlit UI

## Support

For issues, questions, or feature requests, please use the NEXUS platform issue tracker.

---

**Built with ❤️ for the NEXUS platform**
