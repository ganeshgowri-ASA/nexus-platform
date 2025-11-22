# NEXUS Flowchart & Diagram Editor

A professional-grade flowchart and diagram editor built to rival Lucidchart, Draw.io, and Visio.

## Features

### 🎨 Comprehensive Shape Library (100+ Shapes)
- **Flowchart**: Process, Decision, Terminator, Data, Document, Database, and more
- **UML**: Class, Interface, Actor, Use Case, Component, Package, State
- **Network**: Server, Router, Switch, Firewall, Cloud, Workstation, Laptop
- **Cloud Providers**: AWS (EC2, S3, Lambda, RDS), Azure (VM, Storage, Functions), GCP
- **Organization Charts**: Executive, Manager, Employee, Team, Assistant
- **BPMN**: Task, Gateway, Events, Subprocess, Data Object
- **Wireframes**: Button, Textbox, Checkbox, Radio, Dropdown, Image, Window, Browser
- **Floor Plans**: Wall, Door, Window, Stairs, Furniture
- **Basic Shapes**: Rectangle, Circle, Triangle, Pentagon, Hexagon, Star, Cross
- **Arrows**: Right, Left, Up, Down, Double, Chevron
- **Symbols**: User, Gear, Lock, Heart, Mail, Phone
- **Infographic**: Badge, Ribbon, Callout, Banner, Pie Slice

### 🔗 Smart Connectors
- **Line Types**: Straight, Curved, Elbow (orthogonal), Bezier
- **Arrow Styles**: None, Simple, Filled, Hollow, Diamond, Circle
- **Line Styles**: Solid, Dashed, Dotted
- **Features**: Auto-routing, snap-to-anchor, labels on lines, waypoints

### 📐 Auto-Layout Algorithms
- **Hierarchical**: Top-down flow with layer-based arrangement
- **Organic**: Force-directed physics simulation for natural layouts
- **Circular**: Radial arrangement in a circle
- **Tree**: Hierarchical tree structure
- **Grid**: Regular grid pattern
- **Customizable**: Adjust spacing, margins, and alignment

### 📋 Pre-built Templates
- Basic Flowchart
- Organization Chart
- Network Diagram
- Cloud Architecture (AWS)
- UML Class Diagram
- Web Wireframe
- BPMN Business Process

### 📤 Multi-Format Export
- **SVG**: Scalable vector graphics
- **PNG**: High-resolution raster images
- **PDF**: Print-ready documents
- **Visio**: VSDX format for Microsoft Visio
- **JSON**: Native format for saving and loading
- **Embed**: HTML, iframe, and Markdown embed codes

### 🤝 Real-Time Collaboration
- Multi-user editing
- User presence tracking (cursors, selections)
- Comments and annotations
- Version history and comparison
- Conflict detection and resolution
- Locking mechanism to prevent concurrent edits

### 🤖 AI-Powered Features
- **Generate from Text**: Describe your diagram in natural language
- **Auto-Optimize**: AI suggests the best layout
- **Smart Suggestions**: Detect overlaps, disconnected shapes, styling issues
- **Color Schemes**: Apply professional color palettes
- **Layout Detection**: Automatically choose the best layout algorithm

### 🎯 Advanced Features
- **Layers**: Organize complex diagrams with multiple layers
- **Undo/Redo**: Full history with 50-level undo
- **Snap-to-Grid**: Precision alignment
- **Zoom & Pan**: Navigate large diagrams easily
- **Selection Tools**: Multi-select, group operations
- **Styling**: Colors, gradients, shadows, borders, fonts
- **Rotation**: Rotate shapes to any angle
- **Custom Shapes**: SVG path support for custom designs

## Installation

```bash
pip install streamlit anthropic
```

## Quick Start

### Using the UI

```python
import streamlit as st
from modules.flowchart import run_ui

if __name__ == "__main__":
    run_ui()
```

Run with:
```bash
streamlit run your_app.py
```

### Programmatic Usage

```python
from modules.flowchart import DiagramEngine, Point, template_library

# Create a new diagram
engine = DiagramEngine()
engine.metadata.title = "My Flowchart"

# Add shapes
start = engine.add_shape("flowchart_terminator", Point(100, 50), "Start")
process = engine.add_shape("flowchart_process", Point(100, 150), "Process Data")

# Add connector
engine.add_connector("straight", start.id, process.id)

# Save to file
engine.save_to_file("my_diagram.json")

# Export to SVG
from modules.flowchart import SVGExporter
SVGExporter.save_to_file(engine, "my_diagram.svg")
```

### AI-Powered Generation

```python
from modules.flowchart import generate_diagram_from_text

description = """
Create a flowchart with the following steps:
1. Start
2. Get user input
3. Validate input
4. If valid, process data
5. If invalid, show error
6. Save result
7. End
"""

engine = generate_diagram_from_text(description)
```

### Using Templates

```python
from modules.flowchart import create_diagram

# Create from template
engine = create_diagram("Basic Flowchart")

# Modify as needed
# ...

# Save
engine.save_to_file("flowchart.json")
```

### Auto-Layout

```python
from modules.flowchart import LayoutEngine, LayoutConfig

# Apply hierarchical layout
config = LayoutConfig(
    horizontal_spacing=150,
    vertical_spacing=100
)

positions = LayoutEngine.apply_layout(
    "hierarchical",
    engine.shapes,
    engine.connectors,
    config
)

# Update shape positions
for shape_id, position in positions.items():
    engine.update_shape(shape_id, position=position)
```

## API Reference

### Core Classes

#### DiagramEngine
Main class for managing diagrams.

```python
engine = DiagramEngine()

# Add shapes
shape = engine.add_shape(shape_type, position, text, style)

# Add connectors
connector = engine.add_connector(type, source_id, target_id)

# Layers
layer = engine.add_layer(name)

# Selection
engine.select(item_id)
engine.select_all()
engine.clear_selection()

# Undo/Redo
engine.undo()
engine.redo()

# Serialization
data = engine.to_dict()
json_str = engine.to_json()
engine.save_to_file(filepath)
```

#### Shape
Represents a diagram shape.

```python
shape = Shape(
    id="shape1",
    shape_type="flowchart_process",
    category=ShapeCategory.FLOWCHART,
    position=Point(100, 100),
    width=120,
    height=60,
    text="Process",
    style=ShapeStyle(fill_color="#87CEEB")
)
```

#### Connector
Represents a connection between shapes.

```python
connector = Connector(
    id="conn1",
    connector_type=ConnectorType.ELBOW,
    source_shape_id="shape1",
    target_shape_id="shape2",
    style=ConnectorStyle(color="#000000", width=2.0)
)
```

### Shape Library

```python
from modules.flowchart import shape_library

# Get all shapes
all_shapes = shape_library.shapes

# Get shapes by category
flowchart_shapes = shape_library.get_shapes_by_category(ShapeCategory.FLOWCHART)

# Search shapes
results = shape_library.search_shapes("decision")

# Create shape instance
shape = shape_library.create_shape_instance(
    "flowchart_process",
    "id1",
    Point(100, 100),
    "My Process"
)
```

### Export

```python
from modules.flowchart import DiagramExporter

# Export to file
DiagramExporter.export(engine, "svg", "diagram.svg")
DiagramExporter.export(engine, "png", "diagram.png", scale=2.0)
DiagramExporter.export(engine, "pdf", "diagram.pdf")

# Get embed code
embed_html = DiagramExporter.get_embed_code(engine, "html")
embed_iframe = DiagramExporter.get_embed_code(engine, "iframe", width=800, height=600)
```

### AI Features

```python
from modules.flowchart import AIGenerator

# Generate from text
engine = AIGenerator.generate_from_text("Create a simple flowchart...")

# Optimize layout
AIGenerator.optimize_layout(engine, "hierarchical")

# Get suggestions
suggestions = AIGenerator.suggest_improvements(engine)

# Apply color scheme
AIGenerator.apply_color_scheme(engine, "professional")
```

## Architecture

```
modules/flowchart/
├── __init__.py              # Module exports
├── shapes.py                # Shape library (100+ shapes)
├── connectors.py            # Connector system
├── diagram_engine.py        # Core diagram management
├── layout.py                # Auto-layout algorithms
├── templates.py             # Pre-built templates
├── export.py                # Multi-format export
├── collaboration.py         # Real-time collaboration
├── ai_generator.py          # AI-powered features
├── streamlit_ui.py          # Streamlit interface
├── README.md                # This file
└── tests/                   # Test suite
    ├── __init__.py
    ├── test_shapes.py
    ├── test_diagram_engine.py
    └── ...
```

## Shape Categories

- **Flowchart** (10+ shapes): Process flow diagrams
- **UML** (8+ shapes): Object-oriented design
- **Network** (8+ shapes): Infrastructure diagrams
- **AWS** (4+ shapes): AWS cloud architecture
- **Azure** (3+ shapes): Azure cloud services
- **GCP** (2+ shapes): Google Cloud Platform
- **Org Chart** (5+ shapes): Organizational hierarchy
- **BPMN** (6+ shapes): Business processes
- **Wireframe** (8+ shapes): UI/UX mockups
- **Floor Plan** (6+ shapes): Space planning
- **Basic** (9+ shapes): Geometric shapes
- **Arrows** (6+ shapes): Directional indicators
- **Symbols** (6+ shapes): Icons and symbols
- **Infographic** (5+ shapes): Visual storytelling

## Layout Algorithms

### Hierarchical
Best for: Flowcharts, org charts, decision trees
- Layer-based arrangement
- Minimizes edge crossings
- Top-to-bottom or left-to-right flow

### Organic (Force-Directed)
Best for: Complex networks, relationship diagrams
- Physics-based simulation
- Natural-looking layouts
- Balances space utilization

### Circular
Best for: Cycle diagrams, network topologies
- Radial arrangement
- Equal spacing
- Good for showing relationships

### Tree
Best for: Hierarchical structures, file systems
- Parent-child relationships
- Balanced tree layout
- Optimal for hierarchies

### Grid
Best for: Catalogs, galleries, matrices
- Regular grid pattern
- Predictable placement
- Good for uniform items

## Performance

- Handles 1000+ shapes efficiently
- Real-time updates
- Optimized SVG rendering
- Lazy loading for large diagrams
- Efficient collision detection

## Browser Compatibility

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support
- Mobile: ⚠️ View-only recommended

## Contributing

This is a production-ready module. For bug reports or feature requests, please contact the NEXUS team.

## License

Proprietary - NEXUS Platform

## Credits

Built with:
- Python 3.8+
- Streamlit
- SVG for rendering
- Advanced graph algorithms

---

**NEXUS Flowchart & Diagram Editor** - Rival to Lucidchart, Draw.io, Visio! 🚀
