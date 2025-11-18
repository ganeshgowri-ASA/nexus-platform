"""
Streamlit UI - Presentation Editor Interface

Beautiful and intuitive Streamlit interface for the presentation editor.
"""

import streamlit as st
from typing import Optional, Dict, Any
import json
from io import BytesIO

try:
    from .editor import PresentationEditor
    from .slide_manager import SlideLayout, SlideSize
    from .element_handler import ShapeType
    from .animation import AnimationType, TransitionType
    from .template_manager import TemplateCategory
    from .theme_builder import ThemeStyle
    from .export_renderer import ExportFormat, ExportQuality
    from .collaboration import User, PermissionLevel
except ImportError:
    # For standalone testing
    from editor import PresentationEditor
    from slide_manager import SlideLayout, SlideSize
    from element_handler import ShapeType
    from animation import AnimationType, TransitionType
    from template_manager import TemplateCategory
    from theme_builder import ThemeStyle
    from export_renderer import ExportFormat, ExportQuality
    from collaboration import User, PermissionLevel


def init_session_state():
    """Initialize Streamlit session state."""
    if 'editor' not in st.session_state:
        st.session_state.editor = PresentationEditor()
        st.session_state.current_slide_index = 0
        st.session_state.selected_element_id = None
        st.session_state.presentation_mode = False
        st.session_state.show_notes = True
        st.session_state.show_animations = True
        st.session_state.user = User(
            id="user_1",
            name="Current User",
            email="user@example.com"
        )


def render_toolbar():
    """Render top toolbar."""
    col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 1, 1, 1, 2])

    with col1:
        st.title("📊 NEXUS Presentation")

    with col2:
        if st.button("💾 Save"):
            save_presentation()

    with col3:
        if st.button("📁 Load"):
            load_presentation()

    with col4:
        if st.button("📤 Export"):
            st.session_state.show_export_dialog = True

    with col5:
        if st.button("🎨 Themes"):
            st.session_state.show_theme_picker = True

    with col6:
        if st.button("▶️ Present", type="primary"):
            start_presentation()


def render_slide_sidebar():
    """Render left sidebar with slide thumbnails."""
    st.sidebar.header("Slides")

    editor = st.session_state.editor
    slides = editor.get_all_slides()

    # Add slide button
    if st.sidebar.button("➕ Add Slide", use_container_width=True):
        add_new_slide()

    # Slide list
    for i, slide in enumerate(slides):
        col1, col2 = st.sidebar.columns([4, 1])

        with col1:
            if st.button(
                f"{i+1}. {slide.title}",
                key=f"slide_{i}",
                use_container_width=True,
                type="primary" if i == st.session_state.current_slide_index else "secondary"
            ):
                st.session_state.current_slide_index = i

        with col2:
            if st.button("🗑️", key=f"delete_{i}"):
                if editor.delete_slide(slide.id):
                    st.rerun()


def render_properties_sidebar():
    """Render right sidebar with properties."""
    st.sidebar.header("Properties")

    editor = st.session_state.editor

    tabs = st.sidebar.tabs(["📄 Slide", "🎨 Design", "✨ Animations", "🤖 AI"])

    with tabs[0]:
        render_slide_properties()

    with tabs[1]:
        render_design_properties()

    with tabs[2]:
        render_animation_properties()

    with tabs[3]:
        render_ai_assistant()


def render_slide_properties():
    """Render slide properties."""
    editor = st.session_state.editor
    slides = editor.get_all_slides()

    if not slides:
        st.info("No slides yet. Add a slide to get started.")
        return

    current_slide = slides[st.session_state.current_slide_index]

    st.subheader("Slide Settings")

    # Slide title
    new_title = st.text_input("Title", value=current_slide.title)
    if new_title != current_slide.title:
        current_slide.title = new_title
        current_slide.update()

    # Layout
    layout = st.selectbox(
        "Layout",
        options=[l.value for l in SlideLayout],
        index=list(SlideLayout).index(current_slide.layout)
    )

    # Background
    st.subheader("Background")
    bg_type = st.selectbox("Type", ["Solid Color", "Gradient", "Image"])

    if bg_type == "Solid Color":
        bg_color = st.color_picker("Color", value="#FFFFFF")
        current_slide.background = {"type": "solid", "color": bg_color}

    # Speaker notes
    st.subheader("Speaker Notes")
    notes = st.text_area(
        "Notes",
        value=current_slide.notes.content,
        height=100,
        key="speaker_notes"
    )
    if notes != current_slide.notes.content:
        current_slide.notes.update(notes)


def render_design_properties():
    """Render design properties."""
    editor = st.session_state.editor

    st.subheader("Themes")

    themes = editor.get_available_themes()

    for theme in themes[:5]:  # Show first 5 themes
        if st.button(theme["name"], use_container_width=True):
            editor.apply_theme(theme["id"])
            st.rerun()

    st.divider()

    st.subheader("Templates")

    categories = ["Business", "Education", "Marketing", "Creative"]
    selected_category = st.selectbox("Category", categories)

    templates = editor.get_available_templates()

    for template in templates[:3]:  # Show first 3 templates
        if st.button(f"📄 {template['name']}", use_container_width=True):
            slides = editor.get_all_slides()
            if slides:
                current_slide = slides[st.session_state.current_slide_index]
                editor.apply_template_to_slide(current_slide.id, template["id"])
                st.rerun()


def render_animation_properties():
    """Render animation properties."""
    st.subheader("Transitions")

    transitions = ["None", "Fade", "Push", "Wipe", "Zoom", "Flip"]
    selected_transition = st.selectbox("Slide Transition", transitions)

    duration = st.slider("Duration (seconds)", 0.1, 2.0, 0.5, 0.1)

    st.divider()

    st.subheader("Element Animations")

    if st.session_state.selected_element_id:
        animation_types = ["Fade In", "Fly In", "Zoom In", "Bounce"]
        selected_animation = st.selectbox("Animation", animation_types)

        if st.button("Add Animation", use_container_width=True):
            add_animation()
    else:
        st.info("Select an element to add animations")


def render_ai_assistant():
    """Render AI assistant panel."""
    st.subheader("🤖 AI Assistant")

    editor = st.session_state.editor

    # Generate presentation
    with st.expander("Generate Presentation"):
        topic = st.text_input("Topic", placeholder="Enter presentation topic")
        num_slides = st.number_input("Number of Slides", 3, 20, 10)

        if st.button("Generate", use_container_width=True):
            with st.spinner("Generating presentation..."):
                if editor.generate_presentation_from_topic(topic, num_slides):
                    st.success("Presentation generated!")
                    st.rerun()
                else:
                    st.error("Failed to generate presentation")

    # Design suggestions
    with st.expander("Design Suggestions"):
        if st.button("Get Suggestions", use_container_width=True):
            slides = editor.get_all_slides()
            if slides:
                current_slide = slides[st.session_state.current_slide_index]
                suggestions = editor.get_ai_design_suggestions(current_slide.id)

                if suggestions.get("success"):
                    st.success("Suggestions:")
                    for suggestion in suggestions.get("suggestions", []):
                        st.write(f"• {suggestion}")

    # Content assistance
    with st.expander("Content Tools"):
        text = st.text_area("Text to improve", height=100)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Summarize", use_container_width=True):
                response = editor.ai_assistant.summarize_text(text)
                if response.success:
                    st.write(response.result.get("summary"))

        with col2:
            if st.button("Expand", use_container_width=True):
                response = editor.ai_assistant.expand_text(text)
                if response.success:
                    st.write(response.result.get("expanded_text"))


def render_main_canvas():
    """Render main editing canvas."""
    editor = st.session_state.editor
    slides = editor.get_all_slides()

    if not slides:
        st.info("👈 Add a slide from the sidebar to get started")
        return

    current_slide = slides[st.session_state.current_slide_index]

    # Slide header
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        st.header(current_slide.title)

    with col2:
        st.metric("Slide", f"{st.session_state.current_slide_index + 1}/{len(slides)}")

    with col3:
        if st.button("⚙️ Settings"):
            pass

    st.divider()

    # Insert toolbar
    render_insert_toolbar(current_slide)

    st.divider()

    # Canvas
    render_slide_canvas(current_slide)


def render_insert_toolbar(current_slide):
    """Render insert elements toolbar."""
    st.subheader("Insert")

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    editor = st.session_state.editor

    with col1:
        if st.button("📝 Text", use_container_width=True):
            editor.add_text_element(
                current_slide.id,
                "New Text",
                100, 100, 300, 100
            )
            st.rerun()

    with col2:
        if st.button("🖼️ Image", use_container_width=True):
            st.session_state.show_image_dialog = True

    with col3:
        if st.button("⬜ Shape", use_container_width=True):
            editor.add_shape_element(
                current_slide.id,
                ShapeType.RECTANGLE,
                100, 100, 200, 200
            )
            st.rerun()

    with col4:
        if st.button("📊 Chart", use_container_width=True):
            st.session_state.show_chart_dialog = True

    with col5:
        if st.button("📋 Table", use_container_width=True):
            st.session_state.show_table_dialog = True

    with col6:
        if st.button("🎬 Video", use_container_width=True):
            st.session_state.show_video_dialog = True


def render_slide_canvas(current_slide):
    """Render slide canvas with elements."""
    # Canvas container
    with st.container():
        st.markdown("""
        <style>
        .slide-canvas {
            background: white;
            border: 2px solid #ddd;
            border-radius: 8px;
            padding: 40px;
            min-height: 500px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        </style>
        """, unsafe_allow_html=True)

        with st.container():
            st.markdown('<div class="slide-canvas">', unsafe_allow_html=True)

            # Display slide elements
            if not current_slide.elements:
                st.info("This slide is empty. Use the toolbar above to add content.")
            else:
                for element in current_slide.elements:
                    render_element(element)

            st.markdown('</div>', unsafe_allow_html=True)


def render_element(element: Dict[str, Any]):
    """Render a single element."""
    element_type = element.get("type", "text")

    if element_type == "text":
        content = element.get("content", "")
        style = element.get("style", {})

        # Create styled text
        font_size = style.get("font_size", 18)
        color = style.get("color", "#000000")
        bold = style.get("bold", False)

        html = f'<div style="font-size:{font_size}px; color:{color}; '
        html += 'font-weight:bold;' if bold else ''
        html += f'">{content}</div>'

        st.markdown(html, unsafe_allow_html=True)

    elif element_type == "image":
        source = element.get("source", "")
        if source:
            st.image(source, width=300)

    elif element_type == "shape":
        shape_type = element.get("shape_type", "rectangle")
        fill = element.get("fill", {})
        color = fill.get("color", "#3498DB")

        st.markdown(
            f'<div style="width:100px; height:100px; background:{color};"></div>',
            unsafe_allow_html=True
        )


def add_new_slide():
    """Add a new slide."""
    editor = st.session_state.editor

    # Show template picker in dialog
    with st.sidebar:
        st.subheader("Choose Template")

        templates = editor.get_available_templates()

        if st.button("Blank Slide"):
            editor.add_slide(SlideLayout.BLANK, "New Slide")
            st.session_state.current_slide_index = editor.slide_manager.get_slide_count() - 1
            st.rerun()

        for template in templates[:5]:
            if st.button(template["name"]):
                slide = editor.add_slide(
                    template_id=template["id"],
                    title=template["name"]
                )
                st.session_state.current_slide_index = editor.slide_manager.get_slide_count() - 1
                st.rerun()


def add_animation():
    """Add animation to selected element."""
    editor = st.session_state.editor

    if st.session_state.selected_element_id:
        editor.add_animation(
            st.session_state.selected_element_id,
            AnimationType.FADE_IN,
            0.5
        )
        st.success("Animation added!")


def save_presentation():
    """Save presentation."""
    editor = st.session_state.editor
    data = editor.to_dict()

    # Create download button
    json_str = json.dumps(data, indent=2)
    st.download_button(
        label="Download Presentation",
        data=json_str,
        file_name=f"{editor.title}.json",
        mime="application/json"
    )


def load_presentation():
    """Load presentation."""
    uploaded_file = st.sidebar.file_uploader(
        "Choose presentation file",
        type=["json"]
    )

    if uploaded_file:
        data = json.load(uploaded_file)
        st.session_state.editor.from_dict(data)
        st.success("Presentation loaded!")
        st.rerun()


def start_presentation():
    """Start presentation mode."""
    st.session_state.presentation_mode = True
    editor = st.session_state.editor
    editor.start_presentation()
    st.rerun()


def render_export_dialog():
    """Render export dialog."""
    if not st.session_state.get('show_export_dialog'):
        return

    with st.dialog("Export Presentation"):
        st.subheader("Export Options")

        format_options = {
            "PowerPoint (PPTX)": ExportFormat.PPTX,
            "PDF Document": ExportFormat.PDF,
            "HTML5 Presentation": ExportFormat.HTML5,
            "PNG Images": ExportFormat.PNG,
            "Video (MP4)": ExportFormat.MP4,
        }

        selected_format = st.selectbox(
            "Format",
            options=list(format_options.keys())
        )

        quality = st.select_slider(
            "Quality",
            options=["Low", "Medium", "High", "Ultra"],
            value="High"
        )

        if st.button("Export", use_container_width=True):
            editor = st.session_state.editor

            quality_map = {
                "Low": ExportQuality.LOW,
                "Medium": ExportQuality.MEDIUM,
                "High": ExportQuality.HIGH,
                "Ultra": ExportQuality.ULTRA,
            }

            with st.spinner("Exporting..."):
                buffer = editor.export(
                    format=format_options[selected_format],
                    quality=quality_map[quality]
                )

                st.download_button(
                    label="Download",
                    data=buffer.getvalue(),
                    file_name=f"{editor.title}.{format_options[selected_format].value}",
                    mime="application/octet-stream"
                )

        if st.button("Close"):
            st.session_state.show_export_dialog = False
            st.rerun()


def render_presentation_info():
    """Render presentation information."""
    editor = st.session_state.editor

    with st.expander("ℹ️ Presentation Info"):
        info = editor.get_presentation_info()

        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input("Title", value=info["title"])
            author = st.text_input("Author", value=info["author"])

        with col2:
            st.metric("Slides", info["slide_count"])
            stats = editor.get_statistics()
            st.metric("Elements", stats["total_elements"])

        description = st.text_area(
            "Description",
            value=info["description"],
            height=100
        )

        if st.button("Update Info"):
            editor.set_presentation_info(
                title=title,
                author=author,
                description=description
            )
            st.success("Info updated!")


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="NEXUS Presentation Editor",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS
    st.markdown("""
    <style>
    .main { padding: 0rem 1rem; }
    .stButton>button { width: 100%; }
    .slide-thumbnail {
        border: 2px solid #ddd;
        border-radius: 4px;
        padding: 10px;
        margin: 5px 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # Initialize
    init_session_state()

    # Check if in presentation mode
    if st.session_state.presentation_mode:
        render_presentation_mode()
        return

    # Main UI
    render_toolbar()

    # Layout
    col1, col2, col3 = st.columns([1, 3, 1])

    with col1:
        render_slide_sidebar()

    with col2:
        render_main_canvas()
        render_presentation_info()

    with col3:
        render_properties_sidebar()

    # Dialogs
    render_export_dialog()


def render_presentation_mode():
    """Render presentation mode."""
    editor = st.session_state.editor
    presenter = editor.get_presenter_view()

    # Exit button
    if st.button("Exit Presentation"):
        st.session_state.presentation_mode = False
        presenter.end_presentation()
        st.rerun()

    # Current slide
    current_slide = presenter.get_current_slide()

    if current_slide:
        st.markdown(f"## {current_slide.get('title', '')}")

        # Navigation
        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            if st.button("◀️ Previous"):
                presenter.previous_slide()
                st.rerun()

        with col2:
            progress = presenter.get_progress()
            st.progress(progress["percentage"] / 100)
            st.write(f"Slide {progress['current_slide']} of {progress['total_slides']}")
            st.write(f"Time: {progress['elapsed_time']}")

        with col3:
            if st.button("Next ▶️"):
                presenter.next_slide()
                st.rerun()

        # Notes
        if st.session_state.show_notes:
            with st.expander("📝 Speaker Notes"):
                notes = presenter.get_current_notes()
                st.write(notes if notes else "No notes for this slide")


if __name__ == "__main__":
    main()
