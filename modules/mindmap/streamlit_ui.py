"""
Mind Map Streamlit UI

This module provides the Streamlit-based user interface for the mind map module,
including an infinite canvas, node editing, and all interactive features.
"""

import streamlit as st
from typing import Dict, List, Optional, Any
import json

from .mind_engine import MindMapEngine
from .nodes import MindMapNode, Position, NodeShape, Priority
from .branches import ConnectionType
from .layout import LayoutType
from .themes import ThemeName
from .export import ExportFormat
from .ai_brainstorm import AIBrainstormEngine


class MindMapUI:
    """
    Main UI class for the mind map module.

    Features:
    - Infinite canvas with pan and zoom
    - Node creation and editing
    - Visual branch connections
    - Theme selector
    - Layout options
    - Export functionality
    - AI-powered features
    """

    def __init__(self):
        self._initialize_session_state()

    def _initialize_session_state(self) -> None:
        """Initialize Streamlit session state."""
        if "mindmap_engine" not in st.session_state:
            st.session_state.mindmap_engine = MindMapEngine()

        if "selected_node_id" not in st.session_state:
            st.session_state.selected_node_id = None

        if "view_mode" not in st.session_state:
            st.session_state.view_mode = "full"  # full, focus, outline, presentation

        if "canvas_offset_x" not in st.session_state:
            st.session_state.canvas_offset_x = 0

        if "canvas_offset_y" not in st.session_state:
            st.session_state.canvas_offset_y = 0

        if "canvas_zoom" not in st.session_state:
            st.session_state.canvas_zoom = 1.0

    def render(self) -> None:
        """Render the complete mind map UI."""
        st.title("Mind Map & Brainstorming")

        # Sidebar for controls
        self._render_sidebar()

        # Main canvas area
        if st.session_state.view_mode == "full":
            self._render_full_map_view()
        elif st.session_state.view_mode == "focus":
            self._render_focus_view()
        elif st.session_state.view_mode == "outline":
            self._render_outline_view()
        elif st.session_state.view_mode == "presentation":
            self._render_presentation_view()

    def _render_sidebar(self) -> None:
        """Render the sidebar with controls."""
        with st.sidebar:
            st.header("Controls")

            # File operations
            with st.expander("File", expanded=True):
                col1, col2 = st.columns(2)

                with col1:
                    if st.button("New Map", use_container_width=True):
                        self._new_mindmap()

                with col2:
                    if st.button("Load", use_container_width=True):
                        self._load_mindmap()

                # Title input
                engine = st.session_state.mindmap_engine
                engine.title = st.text_input("Title", value=engine.title)

            # Node operations
            with st.expander("Nodes", expanded=True):
                if st.button("Add Root Node", use_container_width=True, disabled=engine.root_id is not None):
                    self._add_root_node()

                if st.button("Add Child Node", use_container_width=True, disabled=st.session_state.selected_node_id is None):
                    self._add_child_node()

                if st.button("Add Sibling Node", use_container_width=True, disabled=st.session_state.selected_node_id is None):
                    self._add_sibling_node()

                if st.button("Delete Node", use_container_width=True, disabled=st.session_state.selected_node_id is None):
                    self._delete_node()

            # Layout
            with st.expander("Layout"):
                layout_type = st.selectbox(
                    "Layout Algorithm",
                    options=[lt.value for lt in LayoutType],
                    format_func=lambda x: x.replace("_", " ").title(),
                )

                if st.button("Apply Layout", use_container_width=True):
                    engine.apply_layout(LayoutType(layout_type))
                    st.rerun()

            # Themes
            with st.expander("Themes"):
                theme_name = st.selectbox(
                    "Theme",
                    options=engine.theme_manager.list_themes(),
                )

                if st.button("Apply Theme", use_container_width=True):
                    engine.apply_theme(theme_name)
                    st.rerun()

            # AI Features
            with st.expander("AI Assistant"):
                if st.button("Generate from Text", use_container_width=True):
                    self._show_ai_generate_dialog()

                if st.button("Suggest Ideas", use_container_width=True, disabled=st.session_state.selected_node_id is None):
                    self._show_ai_suggestions()

                if st.button("Auto-Organize", use_container_width=True):
                    self._auto_organize()

            # Export
            with st.expander("Export"):
                export_format = st.selectbox(
                    "Format",
                    options=[ef.value for ef in ExportFormat if ef.value in ["json", "markdown", "html", "svg", "text_outline"]],
                    format_func=lambda x: x.upper().replace("_", " "),
                )

                if st.button("Export", use_container_width=True):
                    self._export_mindmap(ExportFormat(export_format))

            # View mode
            with st.expander("View"):
                st.session_state.view_mode = st.radio(
                    "View Mode",
                    options=["full", "focus", "outline", "presentation"],
                    format_func=lambda x: x.title(),
                )

            # Statistics
            with st.expander("Statistics"):
                stats = engine.get_statistics()
                if stats:
                    st.metric("Total Nodes", stats.get("total_nodes", 0))
                    st.metric("Max Depth", stats.get("max_depth", 0))
                    st.metric("With Tasks", stats.get("nodes_with_tasks", 0))

    def _render_full_map_view(self) -> None:
        """Render the full mind map view with canvas."""
        engine = st.session_state.mindmap_engine

        st.subheader("Mind Map Canvas")

        if not engine.root_id:
            st.info("Create a root node to get started!")
            return

        # Render canvas controls
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("Zoom In"):
                st.session_state.canvas_zoom *= 1.2
                st.rerun()
        with col2:
            if st.button("Zoom Out"):
                st.session_state.canvas_zoom *= 0.8
                st.rerun()
        with col3:
            if st.button("Reset View"):
                st.session_state.canvas_zoom = 1.0
                st.session_state.canvas_offset_x = 0
                st.session_state.canvas_offset_y = 0
                st.rerun()

        # Render the mind map visualization
        self._render_mindmap_svg()

        # Node editor panel
        if st.session_state.selected_node_id:
            self._render_node_editor()

    def _render_mindmap_svg(self) -> None:
        """Render mind map as interactive SVG."""
        engine = st.session_state.mindmap_engine

        if not engine.root_id or not engine.nodes:
            return

        # Generate SVG
        svg_parts = [
            '<svg width="100%" height="800" xmlns="http://www.w3.org/2000/svg" style="border: 1px solid #ccc;">',
            '<defs>',
            '<style>',
            '.node-rect { cursor: pointer; transition: all 0.2s; }',
            '.node-rect:hover { filter: brightness(1.1); stroke-width: 3; }',
            '.node-text { pointer-events: none; }',
            '.branch-line { pointer-events: none; }',
            '</style>',
            '</defs>',
            f'<g transform="translate({st.session_state.canvas_offset_x}, {st.session_state.canvas_offset_y}) scale({st.session_state.canvas_zoom})">',
        ]

        # Draw branches first
        for branch in engine.branch_manager.branches.values():
            if branch.source_id in engine.nodes and branch.target_id in engine.nodes:
                source = engine.nodes[branch.source_id]
                target = engine.nodes[branch.target_id]

                svg_parts.append(
                    f'<line class="branch-line" '
                    f'x1="{source.position.x}" y1="{source.position.y}" '
                    f'x2="{target.position.x}" y2="{target.position.y}" '
                    f'stroke="{branch.style.color}" '
                    f'stroke-width="{branch.style.width}" />'
                )

        # Draw nodes
        for node_id, node in engine.nodes.items():
            is_selected = node_id == st.session_state.selected_node_id
            self._draw_node_svg(svg_parts, node, is_selected)

        svg_parts.append('</g>')
        svg_parts.append('</svg>')

        # Display SVG
        st.markdown('\n'.join(svg_parts), unsafe_allow_html=True)

        # Node selection (simplified - in production would use JavaScript)
        st.write("Select a node:")
        node_options = {node.text[:30]: node_id for node_id, node in engine.nodes.items()}
        selected_text = st.selectbox(
            "Selected Node",
            options=list(node_options.keys()),
            key="node_selector",
        )
        if selected_text:
            st.session_state.selected_node_id = node_options[selected_text]

    def _draw_node_svg(self, svg_parts: List[str], node: MindMapNode, is_selected: bool) -> None:
        """Draw a single node in SVG."""
        x, y = node.position.x, node.position.y
        text_length = len(node.text) * 8
        rect_width = max(text_length, 120)
        rect_height = 50

        # Highlight if selected
        stroke_color = "#FF4444" if is_selected else node.style.border_color
        stroke_width = 4 if is_selected else node.style.border_width

        # Draw rectangle
        rx = 10 if node.style.shape == NodeShape.ROUNDED_RECTANGLE else 0

        svg_parts.append(
            f'<rect class="node-rect" '
            f'x="{x - rect_width/2}" y="{y - rect_height/2}" '
            f'width="{rect_width}" height="{rect_height}" '
            f'fill="{node.style.background_color}" '
            f'stroke="{stroke_color}" '
            f'stroke-width="{stroke_width}" '
            f'rx="{rx}" '
            f'opacity="{node.style.opacity}" />'
        )

        # Draw text
        svg_parts.append(
            f'<text class="node-text" '
            f'x="{x}" y="{y + 5}" '
            f'text-anchor="middle" '
            f'fill="{node.style.text_color}" '
            f'font-family="{node.style.font_family}" '
            f'font-size="{node.style.font_size}" '
            f'font-weight="{node.style.font_weight}">'
            f'{self._escape_svg(node.text[:40])}</text>'
        )

        # Draw task indicator if has tasks
        if node.tasks:
            pending = sum(1 for t in node.tasks if not t.completed)
            if pending > 0:
                svg_parts.append(
                    f'<circle cx="{x + rect_width/2 - 10}" cy="{y - rect_height/2 + 10}" '
                    f'r="8" fill="#FF6B6B" />'
                )
                svg_parts.append(
                    f'<text x="{x + rect_width/2 - 10}" y="{y - rect_height/2 + 14}" '
                    f'text-anchor="middle" fill="white" font-size="10">{pending}</text>'
                )

    def _escape_svg(self, text: str) -> str:
        """Escape special characters for SVG."""
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _render_node_editor(self) -> None:
        """Render node editing panel."""
        engine = st.session_state.mindmap_engine
        node_id = st.session_state.selected_node_id

        if node_id not in engine.nodes:
            return

        node = engine.nodes[node_id]

        st.divider()
        st.subheader("Node Editor")

        # Text editing
        new_text = st.text_input("Node Text", value=node.text, key="node_text_edit")
        if new_text != node.text:
            engine.update_node_text(node_id, new_text)

        # Notes
        new_notes = st.text_area("Notes", value=node.notes, key="node_notes_edit")
        if new_notes != node.notes:
            node.notes = new_notes
            engine._mark_modified()

        # Tasks
        st.write("**Tasks:**")
        for i, task in enumerate(node.tasks):
            col1, col2, col3 = st.columns([1, 4, 1])
            with col1:
                completed = st.checkbox("", value=task.completed, key=f"task_{i}_check")
                if completed != task.completed:
                    node.toggle_task(task.id)
            with col2:
                st.write(task.description)
            with col3:
                if st.button("🗑️", key=f"task_{i}_delete"):
                    node.remove_task(task.id)
                    st.rerun()

        # Add new task
        new_task_desc = st.text_input("Add Task", key="new_task_input")
        if st.button("Add Task") and new_task_desc:
            from .nodes import Task
            node.add_task(Task(description=new_task_desc))
            st.rerun()

        # Tags
        st.write("**Tags:**")
        tags_str = ", ".join(node.tags)
        new_tags = st.text_input("Tags (comma-separated)", value=tags_str, key="node_tags_edit")
        if new_tags != tags_str:
            node.tags = set(tag.strip() for tag in new_tags.split(",") if tag.strip())
            engine._mark_modified()

    def _render_focus_view(self) -> None:
        """Render focus view showing only selected node and immediate connections."""
        st.subheader("Focus Mode")

        if not st.session_state.selected_node_id:
            st.info("Select a node to focus on")
            return

        engine = st.session_state.mindmap_engine
        node = engine.get_node(st.session_state.selected_node_id)

        if node:
            st.markdown(f"## {node.text}")
            if node.notes:
                st.markdown(node.notes)

            # Show children
            children = engine.get_children(node.id)
            if children:
                st.write("**Children:**")
                for child in children:
                    st.markdown(f"- {child.text}")

    def _render_outline_view(self) -> None:
        """Render outline view."""
        st.subheader("Outline View")

        engine = st.session_state.mindmap_engine

        if not engine.root_id:
            st.info("No mind map to display")
            return

        outline = engine.ai_engine.generate_outline(engine.nodes, engine.root_id)
        st.text(outline)

    def _render_presentation_view(self) -> None:
        """Render presentation mode."""
        st.subheader("Presentation Mode")

        engine = st.session_state.mindmap_engine

        if not engine.root_id:
            st.info("No mind map to present")
            return

        # Generate slides
        slides = engine.export_engine.export_for_presentation(
            engine.nodes,
            engine.branch_manager.branches,
            engine.root_id,
        )

        # Simple slide navigation
        if "slide_index" not in st.session_state:
            st.session_state.slide_index = 0

        if slides:
            current_slide = slides[st.session_state.slide_index]

            if current_slide["type"] == "title":
                st.markdown(f"# {current_slide['title']}")
                st.markdown(f"### {current_slide['subtitle']}")
            else:
                st.markdown(f"## {current_slide['title']}")
                for bullet in current_slide["bullets"]:
                    st.markdown(f"- {bullet}")

            # Navigation
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if st.button("← Previous") and st.session_state.slide_index > 0:
                    st.session_state.slide_index -= 1
                    st.rerun()
            with col2:
                st.write(f"Slide {st.session_state.slide_index + 1} of {len(slides)}")
            with col3:
                if st.button("Next →") and st.session_state.slide_index < len(slides) - 1:
                    st.session_state.slide_index += 1
                    st.rerun()

    # ==================== Action Methods ====================

    def _new_mindmap(self) -> None:
        """Create a new mind map."""
        st.session_state.mindmap_engine = MindMapEngine()
        st.session_state.selected_node_id = None
        st.rerun()

    def _add_root_node(self) -> None:
        """Add a root node."""
        engine = st.session_state.mindmap_engine
        text = st.text_input("Root node text:", key="root_text_input")
        if st.button("Create Root"):
            if text:
                root_id = engine.create_root_node(text)
                st.session_state.selected_node_id = root_id
                st.rerun()

    def _add_child_node(self) -> None:
        """Add a child node to selected node."""
        if not st.session_state.selected_node_id:
            return

        engine = st.session_state.mindmap_engine
        text = st.text_input("Child node text:", key="child_text_input")
        if st.button("Create Child"):
            if text:
                child_id = engine.create_node(text, parent_id=st.session_state.selected_node_id)
                engine.apply_layout(LayoutType.MIND_MAP)
                st.session_state.selected_node_id = child_id
                st.rerun()

    def _add_sibling_node(self) -> None:
        """Add a sibling node to selected node."""
        if not st.session_state.selected_node_id:
            return

        engine = st.session_state.mindmap_engine
        node = engine.get_node(st.session_state.selected_node_id)

        if node and node.parent_id:
            text = st.text_input("Sibling node text:", key="sibling_text_input")
            if st.button("Create Sibling"):
                if text:
                    sibling_id = engine.create_node(text, parent_id=node.parent_id)
                    engine.apply_layout(LayoutType.MIND_MAP)
                    st.session_state.selected_node_id = sibling_id
                    st.rerun()

    def _delete_node(self) -> None:
        """Delete selected node."""
        if not st.session_state.selected_node_id:
            return

        engine = st.session_state.mindmap_engine
        if st.button("Confirm Delete", type="primary"):
            engine.delete_node(st.session_state.selected_node_id)
            st.session_state.selected_node_id = None
            st.rerun()

    def _show_ai_generate_dialog(self) -> None:
        """Show AI generation dialog."""
        text = st.text_area("Enter text to generate mind map from:", key="ai_gen_text")
        root_text = st.text_input("Root node text (optional):", key="ai_gen_root")

        if st.button("Generate Mind Map"):
            if text:
                engine = st.session_state.mindmap_engine
                engine.generate_from_text(text, root_text or None)
                st.success("Mind map generated!")
                st.rerun()

    def _show_ai_suggestions(self) -> None:
        """Show AI suggestions for selected node."""
        if not st.session_state.selected_node_id:
            return

        engine = st.session_state.mindmap_engine
        suggestions = engine.suggest_ideas_for_node(st.session_state.selected_node_id)

        st.write("**AI Suggestions:**")
        for i, suggestion in enumerate(suggestions):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"{i+1}. {suggestion}")
            with col2:
                if st.button("Add", key=f"add_suggestion_{i}"):
                    engine.create_node(suggestion, parent_id=st.session_state.selected_node_id)
                    engine.apply_layout(LayoutType.MIND_MAP)
                    st.rerun()

    def _auto_organize(self) -> None:
        """Run auto-organize."""
        engine = st.session_state.mindmap_engine
        suggestions = engine.auto_organize()

        st.write("**Organization Suggestions:**")
        st.json(suggestions)

    def _export_mindmap(self, format: ExportFormat) -> None:
        """Export mind map."""
        engine = st.session_state.mindmap_engine

        try:
            data = engine.export(format)
            filename = f"{engine.title.replace(' ', '_')}.{format.value}"

            st.download_button(
                label=f"Download {format.value.upper()}",
                data=data,
                file_name=filename,
                mime=self._get_mime_type(format),
            )
        except Exception as e:
            st.error(f"Export failed: {e}")

    def _load_mindmap(self) -> None:
        """Load mind map from file."""
        uploaded_file = st.file_uploader("Choose a JSON file", type=["json"])

        if uploaded_file:
            try:
                data = uploaded_file.read()
                engine = st.session_state.mindmap_engine
                engine.import_from_json(data)
                st.success("Mind map loaded!")
                st.rerun()
            except Exception as e:
                st.error(f"Load failed: {e}")

    def _get_mime_type(self, format: ExportFormat) -> str:
        """Get MIME type for export format."""
        mime_types = {
            ExportFormat.JSON: "application/json",
            ExportFormat.PNG: "image/png",
            ExportFormat.PDF: "application/pdf",
            ExportFormat.SVG: "image/svg+xml",
            ExportFormat.TEXT_OUTLINE: "text/plain",
            ExportFormat.MARKDOWN: "text/markdown",
            ExportFormat.HTML: "text/html",
        }
        return mime_types.get(format, "application/octet-stream")


def main():
    """Main entry point for the mind map UI."""
    st.set_page_config(
        page_title="NEXUS Mind Map",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    ui = MindMapUI()
    ui.render()


if __name__ == "__main__":
    main()
