"""
Infographics Designer - Streamlit UI Module

This module provides the Streamlit-based user interface including
canvas editor, element library, template gallery, data panel, and properties sidebar.
"""

import streamlit as st
from typing import Optional, Dict, Any, List
import json

from .designer import InfographicDesigner, CanvasConfig, AlignmentType, DistributionType
from .elements import (
    ElementFactory, ElementPresets, ShapeType, TextAlign,
    TextElement, ShapeElement, IconElement, ImageElement, LineElement
)
from .templates import TemplateLibrary, TemplateCategory, TemplateStyle, SocialMediaFormat
from .charts import ChartFactory, ChartType, ChartStyler
from .icons import IconLibrary, IconCategory, IconStyle
from .data_viz import DataImporter, ChartGenerator, DataAnalyzer
from .animations import AnimationPresets, AnimationType, AnimationDirection
from .export import InfographicExporter, BatchExporter, ExportFormat, ImageQuality, ExportConfig


class InfographicsUI:
    """Main UI class for the infographics designer."""

    def __init__(self):
        """Initialize the UI."""
        self._initialize_session_state()
        self.designer = st.session_state.designer
        self.template_library = st.session_state.template_library
        self.icon_library = st.session_state.icon_library

    def _initialize_session_state(self):
        """Initialize Streamlit session state."""
        if 'designer' not in st.session_state:
            st.session_state.designer = InfographicDesigner()

        if 'template_library' not in st.session_state:
            st.session_state.template_library = TemplateLibrary()

        if 'icon_library' not in st.session_state:
            st.session_state.icon_library = IconLibrary()

        if 'selected_element_id' not in st.session_state:
            st.session_state.selected_element_id = None

        if 'current_tab' not in st.session_state:
            st.session_state.current_tab = 'Elements'

        if 'show_grid' not in st.session_state:
            st.session_state.show_grid = True

        if 'zoom_level' not in st.session_state:
            st.session_state.zoom_level = 100

    def render(self):
        """Render the main UI."""
        st.set_page_config(
            page_title="NEXUS Infographics Designer",
            page_icon="🎨",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        st.title("🎨 NEXUS Infographics Designer")

        # Main layout
        col1, col2, col3 = st.columns([1, 3, 1])

        with col1:
            self._render_left_sidebar()

        with col2:
            self._render_canvas()

        with col3:
            self._render_right_sidebar()

        # Bottom toolbar
        self._render_bottom_toolbar()

    def _render_left_sidebar(self):
        """Render left sidebar with elements, templates, and tools."""
        st.subheader("Tools")

        tab = st.radio(
            "Select Tool",
            ["Elements", "Templates", "Charts", "Icons", "Data"],
            key="tool_tab",
            horizontal=False
        )

        if tab == "Elements":
            self._render_elements_panel()
        elif tab == "Templates":
            self._render_templates_panel()
        elif tab == "Charts":
            self._render_charts_panel()
        elif tab == "Icons":
            self._render_icons_panel()
        elif tab == "Data":
            self._render_data_panel()

    def _render_elements_panel(self):
        """Render elements panel."""
        st.markdown("### Elements")

        # Text elements
        with st.expander("📝 Text", expanded=True):
            if st.button("Add Heading", use_container_width=True):
                elem = ElementPresets.heading("Heading", 100, 100)
                self.designer.add_element(elem)
                st.rerun()

            if st.button("Add Subheading", use_container_width=True):
                elem = ElementPresets.subheading("Subheading", 100, 150)
                self.designer.add_element(elem)
                st.rerun()

            if st.button("Add Body Text", use_container_width=True):
                elem = ElementPresets.body_text("Body text", 100, 200)
                self.designer.add_element(elem)
                st.rerun()

        # Shapes
        with st.expander("⬛ Shapes", expanded=True):
            shapes = {
                "Rectangle": ShapeType.RECTANGLE,
                "Circle": ShapeType.CIRCLE,
                "Triangle": ShapeType.TRIANGLE,
                "Star": ShapeType.STAR,
                "Heart": ShapeType.HEART
            }

            for name, shape_type in shapes.items():
                if st.button(f"Add {name}", use_container_width=True, key=f"shape_{name}"):
                    elem = ElementFactory.create_shape(shape_type, 100, 100, 100, 100)
                    self.designer.add_element(elem)
                    st.rerun()

        # Lines & Arrows
        with st.expander("↗️ Lines & Arrows"):
            if st.button("Add Line", use_container_width=True):
                elem = ElementFactory.create_line((100, 100), (200, 200))
                self.designer.add_element(elem)
                st.rerun()

            if st.button("Add Arrow", use_container_width=True):
                elem = ElementFactory.create_arrow((100, 100), (200, 200))
                self.designer.add_element(elem)
                st.rerun()

    def _render_templates_panel(self):
        """Render templates panel."""
        st.markdown("### Templates")

        # Category filter
        category = st.selectbox(
            "Category",
            ["All"] + [cat.value for cat in TemplateCategory]
        )

        # Style filter
        style = st.selectbox(
            "Style",
            ["All"] + [s.value for s in TemplateStyle]
        )

        # Get filtered templates
        if category == "All":
            templates = self.template_library.get_all_templates()
        else:
            templates = self.template_library.get_templates_by_category(
                TemplateCategory(category)
            )

        # Search
        search = st.text_input("Search templates", "")
        if search:
            templates = self.template_library.search_templates(search)

        # Display templates
        for template in templates[:10]:  # Limit display
            with st.container():
                st.markdown(f"**{template.metadata.name}**")
                st.caption(template.metadata.description)

                if st.button(f"Use Template", key=f"template_{template.metadata.id}"):
                    self.designer.load_template(template)
                    st.success(f"Loaded: {template.metadata.name}")
                    st.rerun()

                st.divider()

    def _render_charts_panel(self):
        """Render charts panel."""
        st.markdown("### Charts")

        chart_type = st.selectbox(
            "Chart Type",
            ["Bar", "Pie", "Line", "Donut", "Scatter", "Funnel"]
        )

        with st.form("chart_form"):
            st.subheader("Chart Data")

            categories_input = st.text_input(
                "Categories (comma-separated)",
                "A, B, C, D"
            )

            values_input = st.text_input(
                "Values (comma-separated)",
                "10, 20, 30, 40"
            )

            title = st.text_input("Chart Title", "My Chart")

            if st.form_submit_button("Create Chart"):
                categories = [c.strip() for c in categories_input.split(",")]
                values = [float(v.strip()) for v in values_input.split(",")]

                if chart_type == "Bar":
                    chart = ChartFactory.create_bar_chart(categories, values, title)
                elif chart_type == "Pie":
                    chart = ChartFactory.create_pie_chart(categories, values, title)
                elif chart_type == "Line":
                    chart = ChartFactory.create_line_chart(categories, values, title)
                elif chart_type == "Donut":
                    chart = ChartFactory.create_donut_chart(categories, values, title)
                elif chart_type == "Scatter":
                    chart = ChartFactory.create_scatter_chart(values, values, title)
                elif chart_type == "Funnel":
                    chart = ChartFactory.create_funnel_chart(categories, values, title)

                chart.position.x = 100
                chart.position.y = 100
                self.designer.add_element(chart)
                st.success("Chart created!")
                st.rerun()

    def _render_icons_panel(self):
        """Render icons panel."""
        st.markdown("### Icons")

        # Category filter
        category = st.selectbox(
            "Icon Category",
            [cat.value for cat in IconCategory]
        )

        # Search
        search = st.text_input("Search icons", "")

        # Get icons
        if search:
            icons = self.icon_library.search_icons(search)
        else:
            icons = self.icon_library.get_icons_by_category(IconCategory(category))

        # Display icons in grid
        cols = st.columns(4)
        for i, icon in enumerate(icons[:20]):  # Limit display
            with cols[i % 4]:
                if st.button(
                    icon.name,
                    key=f"icon_{icon.id}",
                    use_container_width=True
                ):
                    elem = ElementFactory.create_icon(icon.name, 100, 100, 50)
                    elem.icon_data = icon.svg_data
                    self.designer.add_element(elem)
                    st.rerun()

    def _render_data_panel(self):
        """Render data import panel."""
        st.markdown("### Data Import")

        data_type = st.selectbox(
            "Data Format",
            ["CSV", "JSON", "Manual Entry"]
        )

        if data_type == "CSV":
            csv_data = st.text_area(
                "Paste CSV Data",
                "Name,Value\nA,10\nB,20\nC,30",
                height=150
            )

            if st.button("Import CSV"):
                table = DataImporter.import_csv(csv_data)
                st.success(f"Imported {table.get_row_count()} rows")

                # Auto-generate chart
                if st.checkbox("Auto-generate chart"):
                    chart = ChartGenerator.auto_generate_chart(table)
                    if chart:
                        chart.position.x = 100
                        chart.position.y = 100
                        self.designer.add_element(chart)
                        st.rerun()

        elif data_type == "JSON":
            json_data = st.text_area(
                "Paste JSON Data",
                '{"labels": ["A", "B", "C"], "values": [10, 20, 30]}',
                height=150
            )

            if st.button("Import JSON"):
                table = DataImporter.import_json(json_data)
                st.success("Data imported!")

    def _render_canvas(self):
        """Render main canvas."""
        st.subheader("Canvas")

        # Canvas toolbar
        col1, col2, col3, col4, col5, col6 = st.columns(6)

        with col1:
            if st.button("➕ New"):
                self.designer.clear_canvas()
                st.rerun()

        with col2:
            if st.button("💾 Save"):
                self.designer.save_to_file("infographic.json")
                st.success("Saved!")

        with col3:
            if st.button("📂 Load"):
                st.info("Load functionality")

        with col4:
            if st.button("↩️ Undo"):
                self.designer.undo()
                st.rerun()

        with col5:
            if st.button("↪️ Redo"):
                self.designer.redo()
                st.rerun()

        with col6:
            if st.button("🗑️ Delete"):
                for elem_id in list(self.designer.selected_elements):
                    self.designer.remove_element(elem_id)
                st.rerun()

        # Canvas settings
        with st.expander("Canvas Settings"):
            col1, col2 = st.columns(2)

            with col1:
                new_width = st.number_input(
                    "Width",
                    min_value=100,
                    max_value=5000,
                    value=int(self.designer.canvas.width)
                )

            with col2:
                new_height = st.number_input(
                    "Height",
                    min_value=100,
                    max_value=5000,
                    value=int(self.designer.canvas.height)
                )

            bg_color = st.color_picker(
                "Background Color",
                self.designer.canvas.background_color
            )

            if st.button("Apply Canvas Settings"):
                self.designer.canvas.width = new_width
                self.designer.canvas.height = new_height
                self.designer.canvas.background_color = bg_color
                st.rerun()

        # Canvas preview
        st.markdown("### Preview")
        canvas_html = self._render_canvas_preview()
        st.components.v1.html(canvas_html, height=600, scrolling=True)

        # Elements list
        with st.expander("Elements List", expanded=True):
            elements = self.designer.get_elements()
            st.write(f"Total elements: {len(elements)}")

            for elem in elements:
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.text(f"{elem.element_type.value}: {elem.name}")

                with col2:
                    if st.button("Select", key=f"select_{elem.id}"):
                        st.session_state.selected_element_id = elem.id
                        self.designer.select_element(elem.id)
                        st.rerun()

                with col3:
                    if st.button("Delete", key=f"delete_{elem.id}"):
                        self.designer.remove_element(elem.id)
                        st.rerun()

    def _render_canvas_preview(self) -> str:
        """Generate HTML preview of canvas."""
        canvas = self.designer.canvas
        elements = self.designer.elements

        html = f"""
        <div style="
            width: {canvas.width}px;
            height: {canvas.height}px;
            background-color: {canvas.background_color};
            position: relative;
            border: 1px solid #ccc;
            overflow: hidden;
        ">
        """

        for elem in elements:
            if elem.visible:
                html += self._element_to_html(elem)

        html += "</div>"
        return html

    def _element_to_html(self, element) -> str:
        """Convert element to HTML preview."""
        pos = element.position
        style = element.style

        base_style = f"""
            position: absolute;
            left: {pos.x}px;
            top: {pos.y}px;
            width: {pos.width}px;
            height: {pos.height}px;
            transform: rotate({pos.rotation}deg);
            opacity: {style.opacity};
        """

        from .elements import TextElement, ShapeElement

        if isinstance(element, TextElement):
            return f"""
            <div style="{base_style}
                color: {style.fill_color};
                font-family: {element.text_style.font_family};
                font-size: {element.text_style.font_size}px;
                font-weight: {element.text_style.font_weight};
                text-align: {element.text_style.text_align.value};
            ">
                {element.text}
            </div>
            """

        elif isinstance(element, ShapeElement):
            return f"""
            <div style="{base_style}
                background-color: {style.fill_color};
                border: {style.stroke_width}px solid {style.stroke_color};
                border-radius: {style.border_radius}px;
            "></div>
            """

        return ""

    def _render_right_sidebar(self):
        """Render right sidebar with properties."""
        st.subheader("Properties")

        if st.session_state.selected_element_id:
            elem = self.designer.get_element(st.session_state.selected_element_id)
            if elem:
                self._render_element_properties(elem)
            else:
                st.info("No element selected")
        else:
            st.info("Select an element to edit properties")

        # Alignment tools
        st.divider()
        st.markdown("### Alignment")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("⬅️ Left"):
                selected = list(self.designer.selected_elements)
                self.designer.align_elements(selected, AlignmentType.LEFT)
                st.rerun()

        with col2:
            if st.button("↔️ Center"):
                selected = list(self.designer.selected_elements)
                self.designer.align_elements(selected, AlignmentType.CENTER)
                st.rerun()

        with col3:
            if st.button("➡️ Right"):
                selected = list(self.designer.selected_elements)
                self.designer.align_elements(selected, AlignmentType.RIGHT)
                st.rerun()

        # Layer controls
        st.divider()
        st.markdown("### Layers")

        if st.session_state.selected_element_id:
            col1, col2 = st.columns(2)

            with col1:
                if st.button("⬆️ Bring Forward"):
                    self.designer.bring_forward(st.session_state.selected_element_id)
                    st.rerun()

            with col2:
                if st.button("⬇️ Send Backward"):
                    self.designer.send_backward(st.session_state.selected_element_id)
                    st.rerun()

    def _render_element_properties(self, element):
        """Render properties for selected element."""
        st.markdown(f"**{element.name}**")

        # Position
        with st.expander("Position & Size", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                new_x = st.number_input("X", value=float(element.position.x))
                new_width = st.number_input("Width", value=float(element.position.width))

            with col2:
                new_y = st.number_input("Y", value=float(element.position.y))
                new_height = st.number_input("Height", value=float(element.position.height))

            new_rotation = st.slider(
                "Rotation",
                min_value=0,
                max_value=360,
                value=int(element.position.rotation)
            )

            if st.button("Apply Position"):
                element.position.x = new_x
                element.position.y = new_y
                element.position.width = new_width
                element.position.height = new_height
                element.position.rotation = new_rotation
                st.rerun()

        # Style
        with st.expander("Style", expanded=True):
            fill_color = st.color_picker(
                "Fill Color",
                element.style.fill_color
            )

            stroke_color = st.color_picker(
                "Stroke Color",
                element.style.stroke_color
            )

            stroke_width = st.slider(
                "Stroke Width",
                0.0, 10.0,
                float(element.style.stroke_width)
            )

            opacity = st.slider(
                "Opacity",
                0.0, 1.0,
                float(element.style.opacity)
            )

            if st.button("Apply Style"):
                element.style.fill_color = fill_color
                element.style.stroke_color = stroke_color
                element.style.stroke_width = stroke_width
                element.style.opacity = opacity
                st.rerun()

        # Text properties
        from .elements import TextElement
        if isinstance(element, TextElement):
            with st.expander("Text", expanded=True):
                new_text = st.text_area("Text", element.text)

                font_size = st.slider(
                    "Font Size",
                    8, 72,
                    int(element.text_style.font_size)
                )

                if st.button("Apply Text"):
                    element.text = new_text
                    element.text_style.font_size = font_size
                    st.rerun()

    def _render_bottom_toolbar(self):
        """Render bottom toolbar with export options."""
        st.divider()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("### Export")

        with col2:
            export_format = st.selectbox(
                "Format",
                ["PNG", "PDF", "SVG", "JSON"]
            )

        with col3:
            quality = st.selectbox(
                "Quality",
                ["Low", "Medium", "High", "Ultra"]
            )

        with col4:
            if st.button("📥 Export"):
                exporter = InfographicExporter(self.designer)
                config = ExportConfig(
                    format=ExportFormat(export_format.lower()),
                    quality=ImageQuality(quality.lower())
                )
                filename = f"infographic.{export_format.lower()}"
                exporter.export(config, filename)
                st.success(f"Exported as {filename}")


def main():
    """Main entry point for the UI."""
    ui = InfographicsUI()
    ui.render()


if __name__ == "__main__":
    main()


__all__ = ['InfographicsUI', 'main']
