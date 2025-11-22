"""
UI components for Word Editor module.
"""
import streamlit as st
from typing import Optional, Dict, Any
import base64
from io import BytesIO
from modules.word.document import Document
from modules.word.templates import DocumentTemplates
from modules.word.ai_features import AIFeatures
from modules.word.collab import VersionDiff
from core.utils import (
    count_words,
    count_characters,
    format_reading_time,
    sanitize_filename,
)
from config.constants import (
    FONTS,
    FONT_SIZES,
    HEADING_STYLES,
    TEXT_COLORS,
    TEMPLATE_TYPES,
)


def render_toolbar(doc: Document) -> Dict[str, Any]:
    """
    Render the formatting toolbar.

    Args:
        doc: Document instance

    Returns:
        Dictionary with formatting selections
    """
    st.markdown("### 📝 Formatting")

    col1, col2, col3 = st.columns(3)

    with col1:
        font = st.selectbox(
            "Font",
            FONTS,
            index=FONTS.index(doc.formatting.get("font", "Arial")),
            key="font_select",
        )

    with col2:
        font_size = st.selectbox(
            "Size",
            FONT_SIZES,
            index=FONT_SIZES.index(doc.formatting.get("font_size", 12)),
            key="size_select",
        )

    with col3:
        heading_style = st.selectbox(
            "Style",
            list(HEADING_STYLES.keys()),
            key="heading_select",
        )

    # Text formatting buttons
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        bold = st.checkbox("**B**", value=doc.formatting.get("bold", False), key="bold_check")

    with col2:
        italic = st.checkbox("*I*", value=doc.formatting.get("italic", False), key="italic_check")

    with col3:
        underline = st.checkbox("U", value=doc.formatting.get("underline", False), key="underline_check")

    with col4:
        color = st.selectbox("Color", list(TEXT_COLORS.keys()), key="color_select")

    with col5:
        alignment = st.selectbox(
            "Align",
            ["left", "center", "right", "justify"],
            key="align_select",
        )

    return {
        "font": font,
        "font_size": font_size,
        "heading_style": heading_style,
        "bold": bold,
        "italic": italic,
        "underline": underline,
        "color": TEXT_COLORS[color],
        "alignment": alignment,
    }


def render_editor(doc: Document, key: str = "editor") -> str:
    """
    Render the main text editor.

    Args:
        doc: Document instance
        key: Unique key for the text area

    Returns:
        Edited text content
    """
    st.markdown("### ✍️ Editor")

    # Create the text area with current content
    content = st.text_area(
        "Document Content",
        value=doc.content,
        height=400,
        key=key,
        label_visibility="collapsed",
    )

    return content


def render_statistics(doc: Document) -> None:
    """
    Render document statistics.

    Args:
        doc: Document instance
    """
    st.markdown("### 📊 Statistics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Words", doc.metadata.word_count)

    with col2:
        st.metric("Characters", doc.metadata.character_count)

    with col3:
        reading_time = format_reading_time(doc.content)
        st.metric("Reading Time", reading_time)

    with col4:
        st.metric("Version", doc.metadata.version)


def render_ai_assistant(doc: Document, ai_features: AIFeatures) -> None:
    """
    Render AI assistant sidebar.

    Args:
        doc: Document instance
        ai_features: AIFeatures instance
    """
    st.sidebar.markdown("## 🤖 AI Assistant")

    ai_feature = st.sidebar.selectbox(
        "Select AI Feature",
        [
            "Grammar Check",
            "Spell Check",
            "Summarize",
            "Expand Text",
            "Adjust Tone",
            "Writing Suggestions",
            "Autocomplete",
            "Create Outline",
            "Generate Title",
            "Suggest Keywords",
            "Check Readability",
        ],
        key="ai_feature_select",
    )

    if st.sidebar.button("✨ Apply AI Feature", key="apply_ai"):
        with st.spinner(f"Applying {ai_feature}..."):
            try:
                if ai_feature == "Grammar Check":
                    issues = ai_features.check_grammar(doc.content)
                    if issues:
                        st.sidebar.success(f"Found {len(issues)} grammar issues")
                        for i, issue in enumerate(issues[:5]):  # Show top 5
                            st.sidebar.warning(f"{i+1}. {issue.get('message', 'Issue found')}")
                    else:
                        st.sidebar.success("No grammar issues found!")

                elif ai_feature == "Spell Check":
                    errors = ai_features.check_spelling(doc.content)
                    if errors:
                        st.sidebar.warning(f"Found {len(errors)} spelling errors")
                        for error in errors[:5]:
                            st.sidebar.info(
                                f"**{error['word']}** → {', '.join(error['suggestions'][:3])}"
                            )
                    else:
                        st.sidebar.success("No spelling errors found!")

                elif ai_feature == "Summarize":
                    summary = ai_features.summarize(doc.content)
                    st.sidebar.success("Summary generated!")
                    st.sidebar.markdown(summary)

                elif ai_feature == "Expand Text":
                    if doc.content:
                        expanded = ai_features.expand_text(doc.content)
                        st.session_state.suggested_text = expanded
                        st.sidebar.success("Text expanded! Check the main editor.")

                elif ai_feature == "Adjust Tone":
                    tone = st.sidebar.radio("Select Tone", ["professional", "casual", "formal"])
                    adjusted = ai_features.adjust_tone(doc.content, tone)
                    st.session_state.suggested_text = adjusted
                    st.sidebar.success(f"Text adjusted to {tone} tone!")

                elif ai_feature == "Writing Suggestions":
                    suggestions = ai_features.get_writing_suggestions(doc.content)
                    st.sidebar.success("Suggestions generated!")
                    st.sidebar.markdown(suggestions)

                elif ai_feature == "Create Outline":
                    topic = st.sidebar.text_input("Enter topic:", key="outline_topic")
                    if topic:
                        outline = ai_features.create_outline(topic)
                        st.session_state.suggested_text = outline
                        st.sidebar.success("Outline created!")

                elif ai_feature == "Generate Title":
                    if doc.content:
                        title = ai_features.generate_title(doc.content)
                        st.sidebar.success(f"Suggested title: **{title}**")

                elif ai_feature == "Suggest Keywords":
                    if doc.content:
                        keywords = ai_features.suggest_keywords(doc.content)
                        st.sidebar.success("Keywords: " + ", ".join(keywords))

                elif ai_feature == "Check Readability":
                    analysis = ai_features.check_readability(doc.content)
                    st.sidebar.success("Readability Analysis")
                    st.sidebar.metric("Score", analysis["score"])
                    st.sidebar.metric("Level", analysis["level"])
                    st.sidebar.metric("Avg Words/Sentence", analysis["avg_sentence_length"])

            except Exception as e:
                st.sidebar.error(f"Error: {str(e)}")


def render_export_options(doc: Document) -> None:
    """
    Render export options.

    Args:
        doc: Document instance
    """
    st.sidebar.markdown("## 💾 Export")

    export_format = st.sidebar.selectbox(
        "Format",
        ["PDF", "DOCX", "HTML", "Markdown", "JSON"],
        key="export_format",
    )

    if st.sidebar.button("⬇️ Download", key="download_btn"):
        try:
            filename = sanitize_filename(doc.metadata.title)

            if export_format == "PDF":
                data = doc.export_to_pdf()
                st.sidebar.download_button(
                    "📄 Download PDF",
                    data,
                    file_name=f"{filename}.pdf",
                    mime="application/pdf",
                )

            elif export_format == "DOCX":
                data = doc.export_to_docx()
                st.sidebar.download_button(
                    "📄 Download DOCX",
                    data,
                    file_name=f"{filename}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )

            elif export_format == "HTML":
                data = doc.export_to_html()
                st.sidebar.download_button(
                    "📄 Download HTML",
                    data,
                    file_name=f"{filename}.html",
                    mime="text/html",
                )

            elif export_format == "Markdown":
                data = doc.export_to_markdown()
                st.sidebar.download_button(
                    "📄 Download Markdown",
                    data,
                    file_name=f"{filename}.md",
                    mime="text/markdown",
                )

            elif export_format == "JSON":
                data = doc.to_json()
                st.sidebar.download_button(
                    "📄 Download JSON",
                    data,
                    file_name=f"{filename}.json",
                    mime="application/json",
                )

        except Exception as e:
            st.sidebar.error(f"Export failed: {str(e)}")


def render_version_history(doc: Document) -> None:
    """
    Render version history panel.

    Args:
        doc: Document instance
    """
    st.markdown("### 🕐 Version History")

    if not doc.versions:
        st.info("No versions available")
        return

    for i, version in enumerate(reversed(doc.versions)):
        with st.expander(
            f"Version {len(doc.versions) - i} - {version.timestamp[:19]}",
            expanded=False,
        ):
            st.markdown(f"**Author:** {version.author}")
            st.markdown(f"**Comment:** {version.comment}")

            # Show diff if not the first version
            if i < len(doc.versions) - 1:
                prev_version = doc.versions[-(i + 2)]
                diff_summary = VersionDiff.get_change_summary(
                    prev_version.content,
                    version.content,
                )
                st.markdown(
                    f"**Changes:** +{diff_summary['additions']} / "
                    f"-{diff_summary['deletions']}"
                )

                if st.button(f"View Diff", key=f"diff_{version.id}"):
                    st.markdown("#### Diff View")
                    inline_diff = VersionDiff.get_inline_diff(
                        prev_version.content,
                        version.content,
                    )
                    st.markdown(inline_diff)

            if st.button(f"Restore", key=f"restore_{version.id}"):
                doc.restore_version(version.id)
                st.success("Version restored!")
                st.rerun()


def render_comments_panel(doc: Document, current_user: str = "User") -> None:
    """
    Render comments panel.

    Args:
        doc: Document instance
        current_user: Current user name
    """
    st.markdown("### 💬 Comments")

    # Add new comment
    with st.expander("➕ Add Comment", expanded=False):
        comment_text = st.text_area("Comment", key="new_comment")
        position = st.number_input("Position", min_value=0, value=0, key="comment_pos")

        if st.button("Add Comment", key="add_comment_btn"):
            if comment_text:
                doc.add_comment(comment_text, current_user, position)
                st.success("Comment added!")
                st.rerun()

    # Show existing comments
    unresolved = [c for c in doc.comments if not c.resolved]
    resolved = [c for c in doc.comments if c.resolved]

    if unresolved:
        st.markdown("#### Unresolved Comments")
        for comment in unresolved:
            with st.container():
                st.markdown(f"**{comment.author}** (Position: {comment.position})")
                st.markdown(comment.text)
                st.caption(comment.timestamp[:19])
                if st.button("✓ Resolve", key=f"resolve_{comment.id}"):
                    doc.resolve_comment(comment.id)
                    st.success("Comment resolved!")
                    st.rerun()
                st.divider()

    if resolved:
        with st.expander(f"✓ Resolved Comments ({len(resolved)})", expanded=False):
            for comment in resolved:
                st.markdown(f"**{comment.author}** (Position: {comment.position})")
                st.markdown(comment.text)
                st.caption(comment.timestamp[:19])
                st.divider()


def render_template_selector() -> Optional[str]:
    """
    Render template selector.

    Returns:
        Selected template name or None
    """
    st.markdown("### 📋 Templates")

    templates = DocumentTemplates.get_all_templates()
    template_name = st.selectbox(
        "Choose a template",
        list(templates.keys()),
        key="template_select",
    )

    st.caption(templates[template_name])

    if st.button("📄 Use Template", key="use_template_btn"):
        return template_name

    return None


def render_insert_menu() -> Optional[str]:
    """
    Render insert menu for tables, images, links.

    Returns:
        Item to insert or None
    """
    st.markdown("### ➕ Insert")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 Table"):
            rows = st.number_input("Rows", min_value=1, value=3, key="table_rows")
            cols = st.number_input("Columns", min_value=1, value=3, key="table_cols")

            # Generate markdown table
            header = "| " + " | ".join([f"Column {i+1}" for i in range(int(cols))]) + " |"
            separator = "| " + " | ".join(["---" for _ in range(int(cols))]) + " |"
            rows_md = "\n".join(
                ["| " + " | ".join([" " for _ in range(int(cols))]) + " |" for _ in range(int(rows))]
            )

            table_md = f"\n\n{header}\n{separator}\n{rows_md}\n\n"
            return table_md

    with col2:
        if st.button("🖼️ Image"):
            image_url = st.text_input("Image URL", key="image_url")
            alt_text = st.text_input("Alt Text", value="Image", key="image_alt")

            if image_url:
                return f"\n\n![{alt_text}]({image_url})\n\n"

    with col3:
        if st.button("🔗 Link"):
            link_text = st.text_input("Link Text", key="link_text")
            link_url = st.text_input("URL", key="link_url")

            if link_text and link_url:
                return f"[{link_text}]({link_url})"

    return None


def apply_custom_css() -> None:
    """Apply custom CSS styling."""
    st.markdown(
        """
        <style>
        /* Main editor styling */
        .stTextArea textarea {
            font-family: 'Georgia', serif;
            font-size: 14px;
            line-height: 1.6;
        }

        /* Toolbar styling */
        .stSelectbox {
            margin-bottom: 0.5rem;
        }

        /* Metrics styling */
        .stMetric {
            background-color: #f0f2f6;
            padding: 10px;
            border-radius: 5px;
        }

        /* Button styling */
        .stButton button {
            border-radius: 5px;
            transition: all 0.3s;
        }

        .stButton button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        /* Sidebar styling */
        .css-1d391kg {
            background-color: #f8f9fa;
        }

        /* Expander styling */
        .streamlit-expanderHeader {
            font-weight: 600;
            background-color: #e9ecef;
            border-radius: 5px;
        }

        /* Custom divider */
        hr {
            margin: 1rem 0;
            border: none;
            border-top: 2px solid #e9ecef;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
