"""
Streamlit user interface for the flowchart and diagram editor.
Provides full-featured diagram creation and editing capabilities.
"""

import streamlit as st
from typing import Optional, Dict, Any, List
import json
import base64
from io import BytesIO

from .diagram_engine import DiagramEngine, DiagramMetadata, DiagramSettings
from .shapes import Point, ShapeStyle, ShapeCategory, shape_library
from .connectors import ConnectorType, ConnectorStyle, ArrowType, LineStyle
from .layout import LayoutEngine, LayoutConfig
from .templates import template_library
from .export import DiagramExporter, EmbedCodeGenerator, SVGExporter
from .collaboration import CollaborationEngine, User
from .ai_generator import AIGenerator


def init_session_state():
    """Initialize session state variables."""
    if 'diagram_engine' not in st.session_state:
        st.session_state.diagram_engine = DiagramEngine()

    if 'selected_shape_id' not in st.session_state:
        st.session_state.selected_shape_id = None

    if 'selected_tool' not in st.session_state:
        st.session_state.selected_tool = "select"

    if 'collaboration_engine' not in st.session_state:
        st.session_state.collaboration_engine = CollaborationEngine()

    if 'zoom_level' not in st.session_state:
        st.session_state.zoom_level = 1.0

    if 'show_grid' not in st.session_state:
        st.session_state.show_grid = True


def render_toolbar():
    """Render the main toolbar."""
    col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 2])

    with col1:
        if st.button("🆕 New", use_container_width=True):
            st.session_state.diagram_engine = DiagramEngine()
            st.rerun()

    with col2:
        if st.button("📂 Open", use_container_width=True):
            st.session_state.show_open_dialog = True

    with col3:
        if st.button("💾 Save", use_container_width=True):
            save_diagram()

    with col4:
        if st.button("📤 Export", use_container_width=True):
            st.session_state.show_export_dialog = True

    with col5:
        if st.button("🤖 AI Generate", use_container_width=True):
            st.session_state.show_ai_dialog = True

    with col6:
        st.selectbox(
            "Template",
            [""] + [t.name for t in template_library.get_all_templates()],
            key="template_selector",
            on_change=load_template
        )


def render_shape_palette():
    """Render the shape palette sidebar."""
    st.sidebar.title("Shape Library")

    # Category filter
    categories = ["All"] + [cat.value.replace("_", " ").title() for cat in ShapeCategory]
    selected_category = st.sidebar.selectbox("Category", categories)

    # Search
    search_query = st.sidebar.text_input("Search shapes", "")

    # Get shapes
    if selected_category == "All":
        shapes = shape_library.shapes
    else:
        cat_enum = ShapeCategory(selected_category.lower().replace(" ", "_"))
        shapes = shape_library.get_shapes_by_category(cat_enum)

    # Filter by search
    if search_query:
        shapes = {
            sid: sdef for sid, sdef in shapes.items()
            if search_query.lower() in sdef["name"].lower() or
               search_query.lower() in sdef["description"].lower()
        }

    # Display shapes
    st.sidebar.markdown("### Available Shapes")

    # Group shapes by category
    shapes_by_cat = {}
    for shape_id, shape_def in shapes.items():
        cat = shape_def["category"].value
        if cat not in shapes_by_cat:
            shapes_by_cat[cat] = []
        shapes_by_cat[cat].append((shape_id, shape_def))

    for category, shape_list in shapes_by_cat.items():
        with st.sidebar.expander(category.replace("_", " ").title(), expanded=False):
            for shape_id, shape_def in shape_list:
                if st.button(
                    f"➕ {shape_def['name']}",
                    key=f"add_{shape_id}",
                    use_container_width=True
                ):
                    add_shape_to_canvas(shape_id)


def render_canvas():
    """Render the main diagram canvas."""
    st.markdown("### Diagram Canvas")

    engine = st.session_state.diagram_engine

    # Canvas controls
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        st.markdown(f"**{engine.metadata.title}**")

    with col2:
        if st.button("🔍 Zoom In"):
            st.session_state.zoom_level *= 1.2

    with col3:
        if st.button("🔍 Zoom Out"):
            st.session_state.zoom_level /= 1.2

    with col4:
        if st.button("↻ Reset View"):
            st.session_state.zoom_level = 1.0

    # Generate and display SVG
    svg_content = SVGExporter.export(engine)

    # Apply zoom
    zoom = st.session_state.zoom_level
    svg_content = svg_content.replace(
        '<svg ',
        f'<svg style="transform: scale({zoom}); transform-origin: top left;" '
    )

    # Display SVG
    st.markdown(
        f'<div style="border: 1px solid #ddd; padding: 20px; overflow: auto; background: {engine.settings.background_color};">'
        f'{svg_content}'
        f'</div>',
        unsafe_allow_html=True
    )

    # Canvas stats
    st.markdown(f"**Shapes:** {len(engine.shapes)} | **Connectors:** {len(engine.connectors)} | **Zoom:** {zoom:.1%}")


def render_properties_panel():
    """Render properties panel for selected items."""
    st.sidebar.markdown("---")
    st.sidebar.title("Properties")

    engine = st.session_state.diagram_engine

    if st.session_state.selected_shape_id:
        shape_id = st.session_state.selected_shape_id
        shape = engine.get_shape(shape_id)

        if shape:
            st.sidebar.markdown(f"### Shape: {shape.shape_type}")

            # Text
            new_text = st.sidebar.text_area("Text", shape.text, key="shape_text")
            if new_text != shape.text:
                engine.update_shape(shape_id, text=new_text)

            # Position
            col1, col2 = st.sidebar.columns(2)
            with col1:
                new_x = st.number_input("X", value=shape.position.x, key="shape_x")
            with col2:
                new_y = st.number_input("Y", value=shape.position.y, key="shape_y")

            if new_x != shape.position.x or new_y != shape.position.y:
                engine.update_shape(shape_id, position=Point(new_x, new_y))

            # Size
            col1, col2 = st.sidebar.columns(2)
            with col1:
                new_w = st.number_input("Width", value=shape.width, key="shape_w")
            with col2:
                new_h = st.number_input("Height", value=shape.height, key="shape_h")

            if new_w != shape.width or new_h != shape.height:
                engine.update_shape(shape_id, width=new_w, height=new_h)

            # Rotation
            new_rotation = st.sidebar.slider(
                "Rotation",
                0, 360,
                int(shape.rotation),
                key="shape_rotation"
            )
            if new_rotation != shape.rotation:
                engine.update_shape(shape_id, rotation=float(new_rotation))

            # Style
            st.sidebar.markdown("#### Style")

            new_fill = st.sidebar.color_picker(
                "Fill Color",
                shape.style.fill_color,
                key="shape_fill"
            )
            if new_fill != shape.style.fill_color:
                shape.style.fill_color = new_fill
                engine.update_shape(shape_id, style=shape.style)

            new_stroke = st.sidebar.color_picker(
                "Stroke Color",
                shape.style.stroke_color,
                key="shape_stroke"
            )
            if new_stroke != shape.style.stroke_color:
                shape.style.stroke_color = new_stroke
                engine.update_shape(shape_id, style=shape.style)

            new_stroke_width = st.sidebar.slider(
                "Stroke Width",
                0.0, 10.0,
                shape.style.stroke_width,
                0.5,
                key="shape_stroke_width"
            )
            if new_stroke_width != shape.style.stroke_width:
                shape.style.stroke_width = new_stroke_width
                engine.update_shape(shape_id, style=shape.style)

            # Font
            new_font_size = st.sidebar.slider(
                "Font Size",
                8, 48,
                shape.style.font_size,
                key="shape_font_size"
            )
            if new_font_size != shape.style.font_size:
                shape.style.font_size = new_font_size
                engine.update_shape(shape_id, style=shape.style)

            # Actions
            if st.sidebar.button("🗑️ Delete Shape", use_container_width=True):
                engine.remove_shape(shape_id)
                st.session_state.selected_shape_id = None
                st.rerun()

    else:
        st.sidebar.info("Select a shape to edit its properties")


def render_layers_panel():
    """Render layers panel."""
    with st.expander("📚 Layers", expanded=False):
        engine = st.session_state.diagram_engine

        # Add new layer
        col1, col2 = st.columns([3, 1])
        with col1:
            new_layer_name = st.text_input("New Layer Name", key="new_layer_name")
        with col2:
            if st.button("Add", key="add_layer"):
                if new_layer_name:
                    engine.add_layer(new_layer_name)
                    st.rerun()

        # List layers
        for layer_id, layer in sorted(engine.layers.items()):
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

            with col1:
                st.markdown(f"**{layer.name}**")

            with col2:
                visible = st.checkbox(
                    "👁️",
                    layer.visible,
                    key=f"layer_visible_{layer_id}",
                    label_visibility="collapsed"
                )
                if visible != layer.visible:
                    engine.set_layer_visibility(layer_id, visible)

            with col3:
                locked = st.checkbox(
                    "🔒",
                    layer.locked,
                    key=f"layer_locked_{layer_id}",
                    label_visibility="collapsed"
                )
                if locked != layer.locked:
                    engine.set_layer_locked(layer_id, locked)

            with col4:
                if layer_id != 0:  # Can't delete default layer
                    if st.button("🗑️", key=f"delete_layer_{layer_id}"):
                        engine.remove_layer(layer_id)
                        st.rerun()

            shapes, connectors = engine.get_layer_items(layer_id)
            st.caption(f"{len(shapes)} shapes, {len(connectors)} connectors")


def render_auto_layout():
    """Render auto-layout controls."""
    with st.expander("🎯 Auto Layout", expanded=False):
        engine = st.session_state.diagram_engine

        layout_type = st.selectbox(
            "Layout Algorithm",
            ["hierarchical", "organic", "circular", "tree", "grid"]
        )

        col1, col2 = st.columns(2)
        with col1:
            h_spacing = st.number_input("Horizontal Spacing", 50, 300, 100)
        with col2:
            v_spacing = st.number_input("Vertical Spacing", 30, 200, 80)

        if st.button("Apply Layout", use_container_width=True):
            config = LayoutConfig(
                horizontal_spacing=h_spacing,
                vertical_spacing=v_spacing
            )

            positions = LayoutEngine.apply_layout(
                layout_type,
                engine.shapes,
                engine.connectors,
                config
            )

            for shape_id, position in positions.items():
                engine.update_shape(shape_id, position=position)

            st.success(f"Applied {layout_type} layout!")
            st.rerun()


def render_ai_features():
    """Render AI features dialog."""
    if st.session_state.get('show_ai_dialog', False):
        with st.expander("🤖 AI Features", expanded=True):
            tab1, tab2, tab3 = st.tabs(["Generate from Text", "Optimize", "Suggestions"])

            with tab1:
                st.markdown("### Generate Diagram from Description")

                description = st.text_area(
                    "Describe your diagram:",
                    placeholder='Example: Create a flowchart with "Start", "Process Data", "Validate", "Save", and "End". Start leads to Process Data, which goes to Validate...',
                    height=150
                )

                if st.button("🚀 Generate Diagram"):
                    if description:
                        with st.spinner("Generating diagram..."):
                            new_engine = AIGenerator.generate_from_text(description)
                            st.session_state.diagram_engine = new_engine
                            st.success("Diagram generated!")
                            st.rerun()
                    else:
                        st.warning("Please enter a description")

            with tab2:
                st.markdown("### Optimize Layout")

                engine = st.session_state.diagram_engine

                layout_suggestion = st.selectbox(
                    "Layout Type",
                    ["Auto-detect", "hierarchical", "organic", "circular", "tree", "grid"]
                )

                if st.button("✨ Optimize"):
                    with st.spinner("Optimizing..."):
                        layout = None if layout_suggestion == "Auto-detect" else layout_suggestion
                        AIGenerator.optimize_layout(engine, layout)
                        st.success("Layout optimized!")
                        st.rerun()

                # Color scheme
                st.markdown("### Apply Color Scheme")

                scheme = st.selectbox(
                    "Color Scheme",
                    ["professional", "pastel", "vibrant", "monochrome"]
                )

                if st.button("🎨 Apply Colors"):
                    AIGenerator.apply_color_scheme(engine, scheme)
                    st.success(f"Applied {scheme} color scheme!")
                    st.rerun()

            with tab3:
                st.markdown("### AI Suggestions")

                engine = st.session_state.diagram_engine
                suggestions = AIGenerator.suggest_improvements(engine)

                if suggestions:
                    for suggestion in suggestions:
                        severity_icon = {
                            "warning": "⚠️",
                            "info": "ℹ️",
                            "error": "❌"
                        }.get(suggestion["severity"], "ℹ️")

                        st.markdown(f"{severity_icon} **{suggestion['message']}**")

                        if "action" in suggestion:
                            st.caption(f"💡 {suggestion['action']}")

                        st.markdown("---")
                else:
                    st.success("No issues found! Your diagram looks great!")


def render_export_dialog():
    """Render export dialog."""
    if st.session_state.get('show_export_dialog', False):
        with st.expander("📤 Export Diagram", expanded=True):
            engine = st.session_state.diagram_engine

            tab1, tab2, tab3 = st.tabs(["File Export", "Embed Code", "Share"])

            with tab1:
                st.markdown("### Export to File")

                export_format = st.selectbox(
                    "Format",
                    ["SVG", "PNG", "PDF", "JSON", "Visio (VSDX)"]
                )

                if st.button("Download", use_container_width=True):
                    format_ext = export_format.lower().replace(" ", "").replace("(", "").replace(")", "")

                    try:
                        content = DiagramExporter.export(engine, format_ext)

                        # Create download button
                        b64 = base64.b64encode(content).decode()
                        filename = f"{engine.metadata.title.replace(' ', '_')}.{format_ext}"

                        href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">Click here to download {filename}</a>'
                        st.markdown(href, unsafe_allow_html=True)

                        st.success(f"Export ready! Click the link above to download.")
                    except Exception as e:
                        st.error(f"Export failed: {str(e)}")

            with tab2:
                st.markdown("### Embed Code")

                embed_type = st.selectbox(
                    "Embed Type",
                    ["HTML", "Iframe", "Markdown"]
                )

                embed_code = EmbedCodeGenerator.get_embed_code(
                    engine,
                    embed_type.lower()
                )

                st.code(embed_code, language="html" if embed_type != "Markdown" else "markdown")

                if st.button("📋 Copy to Clipboard"):
                    st.info("Code displayed above - copy manually")

            with tab3:
                st.markdown("### Share Diagram")

                st.info("Sharing features require backend integration")

                share_url = st.text_input(
                    "Share URL",
                    f"https://example.com/diagrams/{engine.metadata.title}",
                    disabled=True
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📧 Email"):
                        st.info("Email sharing coming soon")
                with col2:
                    if st.button("💬 Social"):
                        st.info("Social sharing coming soon")


def add_shape_to_canvas(shape_id: str):
    """Add a shape to the canvas."""
    engine = st.session_state.diagram_engine

    # Calculate position (center of visible area)
    position = Point(300, 200)

    # Add shape
    shape = engine.add_shape(shape_id, position)

    if shape:
        st.session_state.selected_shape_id = shape.id
        st.success(f"Added {shape_library.shapes[shape_id]['name']}")
        st.rerun()


def save_diagram():
    """Save diagram to session state / file."""
    engine = st.session_state.diagram_engine

    # Save to JSON
    diagram_json = engine.to_json()

    # Create download
    b64 = base64.b64encode(diagram_json.encode()).decode()
    filename = f"{engine.metadata.title.replace(' ', '_')}.json"

    href = f'<a href="data:application/json;base64,{b64}" download="{filename}">Click here to download {filename}</a>'
    st.markdown(href, unsafe_allow_html=True)

    st.success("Diagram saved! Click the link above to download.")


def load_template():
    """Load a template."""
    template_name = st.session_state.get('template_selector')

    if template_name:
        try:
            new_engine = template_library.create_from_template(template_name)
            st.session_state.diagram_engine = new_engine
            st.success(f"Loaded template: {template_name}")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to load template: {str(e)}")


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="NEXUS Flowchart & Diagram Editor",
        page_icon="📊",
        layout="wide"
    )

    # Initialize
    init_session_state()

    # Header
    st.title("📊 NEXUS Flowchart & Diagram Editor")
    st.markdown("Professional diagramming tool - Rival Lucidchart, Draw.io, Visio!")

    # Toolbar
    render_toolbar()

    # Main layout
    col_sidebar, col_main = st.columns([1, 3])

    with col_sidebar:
        render_shape_palette()
        render_properties_panel()

    with col_main:
        render_canvas()

        # Additional panels
        col1, col2 = st.columns(2)

        with col1:
            render_layers_panel()
            render_auto_layout()

        with col2:
            render_ai_features()
            render_export_dialog()

    # Footer
    st.markdown("---")
    engine = st.session_state.diagram_engine
    stats = engine.get_statistics()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Shapes", stats["total_shapes"])
    with col2:
        st.metric("Total Connectors", stats["total_connectors"])
    with col3:
        st.metric("Layers", stats["total_layers"])
    with col4:
        if st.button("📊 Full Statistics"):
            st.json(stats)


if __name__ == "__main__":
    main()
