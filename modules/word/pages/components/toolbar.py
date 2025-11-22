"""
Toolbar Component

Renders the formatting toolbar for the word editor.
"""

import streamlit as st
from typing import Dict, Any, Optional


def render_toolbar() -> Dict[str, Any]:
    """
    Render the formatting toolbar.

    Returns:
        Dictionary containing toolbar actions and selections
    """
    actions = {}

    # Use columns for toolbar layout
    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])

    with col1:
        st.markdown("**File**")
        if st.button("💾 Save", key="save_btn", use_container_width=True):
            actions['save'] = True

        if st.button("📂 Open", key="open_btn", use_container_width=True):
            actions['open'] = True

    with col2:
        st.markdown("**Format**")
        format_cols = st.columns(3)

        with format_cols[0]:
            if st.button("**B**", key="bold_btn", help="Bold"):
                actions['bold'] = True

        with format_cols[1]:
            if st.button("*I*", key="italic_btn", help="Italic"):
                actions['italic'] = True

        with format_cols[2]:
            if st.button("U", key="underline_btn", help="Underline"):
                actions['underline'] = True

    with col3:
        st.markdown("**Insert**")
        if st.button("🖼️ Image", key="image_btn", use_container_width=True):
            actions['insert_image'] = True

        if st.button("🔗 Link", key="link_btn", use_container_width=True):
            actions['insert_link'] = True

    with col4:
        st.markdown("**AI Assist**")
        if st.button("✨ AI Help", key="ai_btn", use_container_width=True):
            actions['ai_assist'] = True

        if st.button("📝 Grammar", key="grammar_btn", use_container_width=True):
            actions['grammar_check'] = True

    with col5:
        st.markdown("**Export**")
        export_format = st.selectbox(
            "Format",
            ["PDF", "DOCX", "HTML", "Markdown", "LaTeX", "TXT"],
            key="export_format",
            label_visibility="collapsed"
        )

        if st.button("⬇️ Export", key="export_btn", use_container_width=True):
            actions['export'] = export_format

    # Second row of toolbar with more options
    st.markdown("---")

    col6, col7, col8, col9, col10 = st.columns([2, 2, 2, 2, 2])

    with col6:
        st.markdown("**Text Style**")
        font_family = st.selectbox(
            "Font",
            [
                "Arial", "Times New Roman", "Courier New", "Georgia",
                "Verdana", "Helvetica", "Comic Sans MS", "Impact",
                "Trebuchet MS", "Palatino", "Garamond", "Bookman"
            ],
            key="font_family"
        )
        actions['font_family'] = font_family

        font_size = st.selectbox(
            "Size",
            [8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 32, 36, 48, 72],
            index=4,  # Default to 12
            key="font_size"
        )
        actions['font_size'] = font_size

    with col7:
        st.markdown("**Colors**")
        text_color = st.color_picker("Text", "#000000", key="text_color")
        actions['text_color'] = text_color

        bg_color = st.color_picker("Highlight", "#FFFF00", key="bg_color")
        actions['bg_color'] = bg_color

    with col8:
        st.markdown("**Alignment**")
        align_cols = st.columns(4)

        with align_cols[0]:
            if st.button("⬅️", key="align_left", help="Align Left"):
                actions['align'] = 'left'

        with align_cols[1]:
            if st.button("⬆️", key="align_center", help="Align Center"):
                actions['align'] = 'center'

        with align_cols[2]:
            if st.button("➡️", key="align_right", help="Align Right"):
                actions['align'] = 'right'

        with align_cols[3]:
            if st.button("↔️", key="align_justify", help="Justify"):
                actions['align'] = 'justify'

    with col9:
        st.markdown("**Lists**")
        list_cols = st.columns(3)

        with list_cols[0]:
            if st.button("•", key="bullet_list", help="Bullet List"):
                actions['list'] = 'bullet'

        with list_cols[1]:
            if st.button("1.", key="numbered_list", help="Numbered List"):
                actions['list'] = 'ordered'

        with list_cols[2]:
            if st.button("☑", key="checklist", help="Checklist"):
                actions['list'] = 'checklist'

    with col10:
        st.markdown("**More**")
        if st.button("🔍 Find", key="find_btn", use_container_width=True):
            actions['find'] = True

        if st.button("↩️ Undo", key="undo_btn", use_container_width=True):
            actions['undo'] = True

    return actions


def render_advanced_toolbar() -> Dict[str, Any]:
    """
    Render advanced formatting options in an expander.

    Returns:
        Dictionary containing advanced toolbar actions
    """
    actions = {}

    with st.expander("🛠️ Advanced Formatting", expanded=False):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("**Headings**")
            heading = st.selectbox(
                "Select heading level",
                ["Normal", "H1", "H2", "H3", "H4", "H5", "H6"],
                key="heading_level",
                label_visibility="collapsed"
            )
            if heading != "Normal":
                actions['heading'] = heading

        with col2:
            st.markdown("**Special**")
            if st.button("x²", key="superscript_btn", help="Superscript"):
                actions['superscript'] = True

            if st.button("x₂", key="subscript_btn", help="Subscript"):
                actions['subscript'] = True

            if st.button("S̶", key="strikethrough_btn", help="Strikethrough"):
                actions['strikethrough'] = True

        with col3:
            st.markdown("**Blocks**")
            if st.button("\" Quote", key="blockquote_btn"):
                actions['blockquote'] = True

            if st.button("</> Code", key="codeblock_btn"):
                actions['code_block'] = True

            if st.button("─ Line", key="hr_btn", help="Horizontal Rule"):
                actions['horizontal_rule'] = True

        with col4:
            st.markdown("**Table**")
            table_cols = st.columns(2)

            with table_cols[0]:
                rows = st.number_input("Rows", 1, 20, 3, key="table_rows")

            with table_cols[1]:
                cols = st.number_input("Cols", 1, 10, 3, key="table_cols")

            if st.button("Insert Table", key="insert_table_btn"):
                actions['insert_table'] = {'rows': rows, 'cols': cols}

    return actions


def render_status_bar(stats: Dict[str, Any]) -> None:
    """
    Render the bottom status bar.

    Args:
        stats: Document statistics dictionary
    """
    st.markdown("---")

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric("Words", stats.get('word_count', 0))

    with col2:
        st.metric("Characters", stats.get('character_count', 0))

    with col3:
        st.metric("Paragraphs", stats.get('paragraph_count', 0))

    with col4:
        st.metric("Reading Time", f"{stats.get('reading_time_minutes', 0)} min")

    with col5:
        save_status = "✅ Saved" if stats.get('saved', True) else "⚠️ Unsaved"
        st.markdown(f"**Status:** {save_status}")

    with col6:
        if stats.get('last_save_time'):
            st.markdown(f"**Last saved:** {stats['last_save_time']}")
        else:
            st.markdown("**Last saved:** Never")
