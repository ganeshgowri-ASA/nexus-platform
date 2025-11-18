"""
NEXUS Word Processing Editor

A world-class word processor with rich text editing, AI assistance,
real-time collaboration, and comprehensive document management.
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Import word processing modules
from modules.word.editor import WordEditor, DocumentMetadata, DocumentStatus
from modules.word.formatting import TextFormatter
from modules.word.document_manager import DocumentManager, PageSetup
from modules.word.ai_assistant import AIWritingAssistant, ToneStyle
from modules.word.collaboration import CollaborationManager
from modules.word.templates import TemplateManager

# Import UI components
from modules.word.pages.components.toolbar import (
    render_toolbar,
    render_advanced_toolbar,
    render_status_bar
)
from modules.word.pages.components.editor_canvas import (
    render_editor,
    render_simple_editor,
    render_markdown_editor,
    apply_custom_css
)
from modules.word.pages.components.sidebar import (
    render_sidebar,
    render_ai_assistant_sidebar,
    render_comments_sidebar,
    render_version_history_sidebar,
    render_collaboration_sidebar,
    render_document_info_sidebar
)


# Page configuration
st.set_page_config(
    page_title="NEXUS Word Editor",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
apply_custom_css()


def initialize_session_state():
    """Initialize session state variables"""
    if 'current_user_id' not in st.session_state:
        st.session_state.current_user_id = "user_001"  # In production, get from auth

    if 'current_document_id' not in st.session_state:
        st.session_state.current_document_id = None

    if 'editor' not in st.session_state:
        st.session_state.editor = None

    if 'document_manager' not in st.session_state:
        st.session_state.document_manager = DocumentManager()

    if 'template_manager' not in st.session_state:
        st.session_state.template_manager = TemplateManager()

    if 'ai_assistant' not in st.session_state:
        # In production, pass API key from environment
        st.session_state.ai_assistant = AIWritingAssistant()

    if 'collaboration_manager' not in st.session_state:
        st.session_state.collaboration_manager = None

    if 'auto_save_enabled' not in st.session_state:
        st.session_state.auto_save_enabled = True

    if 'last_auto_save' not in st.session_state:
        st.session_state.last_auto_save = None

    if 'sidebar_mode' not in st.session_state:
        st.session_state.sidebar_mode = "documents"  # documents, ai, comments, versions, collaboration

    if 'editor_mode' not in st.session_state:
        st.session_state.editor_mode = "rich"  # rich, markdown, simple


def create_new_document():
    """Create a new document"""
    editor = WordEditor(user_id=st.session_state.current_user_id)
    st.session_state.editor = editor
    st.session_state.current_document_id = editor.document_id

    # Initialize collaboration manager
    st.session_state.collaboration_manager = CollaborationManager(editor.document_id)

    st.success("✅ New document created!")


def load_document(document_id: str):
    """Load an existing document"""
    doc_manager = st.session_state.document_manager
    editor = doc_manager.load_document(document_id, st.session_state.current_user_id)

    if editor:
        st.session_state.editor = editor
        st.session_state.current_document_id = document_id

        # Initialize collaboration manager
        st.session_state.collaboration_manager = CollaborationManager(document_id)

        st.success(f"✅ Document loaded: {editor.metadata.title}")
    else:
        st.error("❌ Failed to load document")


def save_document():
    """Save the current document"""
    if not st.session_state.editor:
        st.warning("No document to save")
        return

    doc_manager = st.session_state.document_manager
    success = doc_manager.save_document(st.session_state.editor)

    if success:
        st.session_state.last_auto_save = datetime.now()
        st.success("✅ Document saved!")
    else:
        st.error("❌ Failed to save document")


def load_template(template_id: str):
    """Load a template"""
    template_manager = st.session_state.template_manager
    template = template_manager.get_template(template_id)

    if template:
        # Create new document from template
        editor = WordEditor(user_id=st.session_state.current_user_id)
        editor.set_content(template.content)
        editor.update_metadata(title=template.name)

        st.session_state.editor = editor
        st.session_state.current_document_id = editor.document_id

        # Initialize collaboration manager
        st.session_state.collaboration_manager = CollaborationManager(editor.document_id)

        st.success(f"✅ Template loaded: {template.name}")
    else:
        st.error("❌ Template not found")


def export_document(format: str):
    """Export document to specified format"""
    if not st.session_state.editor:
        st.warning("No document to export")
        return

    doc_manager = st.session_state.document_manager
    editor = st.session_state.editor

    # Generate filename
    title = editor.metadata.title.replace(" ", "_") if editor.metadata else "document"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{title}_{timestamp}"

    output_path = f"./modules/files/exports/{filename}"

    success = False

    if format == "PDF":
        success = doc_manager.export_to_pdf(editor, f"{output_path}.pdf")
    elif format == "DOCX":
        success = doc_manager.export_to_docx(editor, f"{output_path}.docx")
    elif format == "HTML":
        success = doc_manager.export_to_html(editor, f"{output_path}.html")
    elif format == "Markdown":
        success = doc_manager.export_to_markdown(editor, f"{output_path}.md")
    elif format == "LaTeX":
        success = doc_manager.export_to_latex(editor, f"{output_path}.tex")
    elif format == "TXT":
        success = doc_manager.export_to_txt(editor, f"{output_path}.txt")

    if success:
        st.success(f"✅ Document exported as {format}: {filename}")
    else:
        st.error(f"❌ Failed to export as {format}")


def main():
    """Main application"""
    initialize_session_state()

    # Sidebar
    with st.sidebar:
        # Sidebar mode selector
        mode = st.radio(
            "Sidebar",
            ["📂 Documents", "✨ AI Assistant", "💬 Comments", "🕐 Versions", "👥 Collaboration", "ℹ️ Info"],
            key="sidebar_mode_selector",
            label_visibility="collapsed"
        )

        st.markdown("---")

        # Render appropriate sidebar based on mode
        if mode == "📂 Documents":
            sidebar_actions = render_sidebar(
                current_doc_id=st.session_state.current_document_id,
                on_document_select=load_document
            )

            # Handle new document
            if sidebar_actions.get('new_document'):
                create_new_document()

            # Handle template selection
            template_id = sidebar_actions.get('template_selected')
            if template_id:
                load_template(template_id)

        elif mode == "✨ AI Assistant":
            ai_actions = render_ai_assistant_sidebar()

            # Handle AI actions
            if ai_actions.get('apply') and st.session_state.editor:
                feature = ai_actions.get('feature')
                ai = st.session_state.ai_assistant

                with st.spinner(f"Applying {feature}..."):
                    # Get current text
                    text = st.session_state.editor._extract_text_from_content()

                    # Apply AI feature
                    if feature == "Grammar Check":
                        issues = ai.check_grammar(text)
                        st.session_state.ai_suggestions = [
                            {'text': issue.message} for issue in issues
                        ]
                    elif feature == "Summarize":
                        result = ai.summarize(text, ai_actions.get('target_length'))
                        st.session_state.ai_suggestions = [{'text': result}]
                    # Add more AI features...

        elif mode == "💬 Comments" and st.session_state.collaboration_manager:
            comments = st.session_state.collaboration_manager.get_comments()
            comment_actions = render_comments_sidebar(
                [comment.to_dict() for comment in comments]
            )

        elif mode == "🕐 Versions":
            if st.session_state.current_document_id:
                versions = st.session_state.document_manager.get_version_history(
                    st.session_state.current_document_id
                )
                version_actions = render_version_history_sidebar(
                    [v.to_dict() for v in versions]
                )

                # Handle version restore
                if 'restore_version' in version_actions:
                    version_num = version_actions['restore_version']
                    editor = st.session_state.document_manager.restore_version(
                        st.session_state.current_document_id,
                        version_num,
                        st.session_state.current_user_id
                    )
                    if editor:
                        st.session_state.editor = editor
                        st.success(f"✅ Restored to version {version_num}")

        elif mode == "👥 Collaboration" and st.session_state.collaboration_manager:
            active_users = st.session_state.collaboration_manager.get_active_users()
            collab_actions = render_collaboration_sidebar(
                [user.to_dict() for user in active_users]
            )

        elif mode == "ℹ️ Info" and st.session_state.editor:
            render_document_info_sidebar(st.session_state.editor.metadata.to_dict())

    # Main content area
    st.title("📝 NEXUS Word Editor")

    # Check if we have a document
    if not st.session_state.editor:
        st.info("👈 Create a new document or select a template from the sidebar to get started!")

        # Show template gallery in main area
        st.markdown("## 📄 Template Gallery")

        template_manager = st.session_state.template_manager
        templates = template_manager.get_all_templates()

        # Group by category
        categories = {}
        for template in templates:
            cat = template.category.value
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(template)

        for category, cat_templates in categories.items():
            st.markdown(f"### {category.title()}")

            cols = st.columns(3)
            for i, template in enumerate(cat_templates):
                with cols[i % 3]:
                    with st.container():
                        st.markdown(f"**{template.name}**")
                        st.caption(template.description)

                        if st.button("Use Template", key=f"use_{template.template_id}"):
                            load_template(template.template_id)

        return

    # Toolbar
    toolbar_actions = render_toolbar()

    # Handle toolbar actions
    if toolbar_actions.get('save'):
        save_document()

    if toolbar_actions.get('export'):
        export_document(toolbar_actions['export'])

    if toolbar_actions.get('undo') and st.session_state.editor:
        st.session_state.editor.undo()

    # Advanced toolbar
    adv_actions = render_advanced_toolbar()

    st.markdown("---")

    # Editor area
    editor_col, preview_col = st.columns([7, 3])

    with editor_col:
        st.markdown("### Document")

        # Editor mode selector
        mode_cols = st.columns([1, 1, 1, 6])

        with mode_cols[0]:
            if st.button("📝 Rich", use_container_width=True):
                st.session_state.editor_mode = "rich"

        with mode_cols[1]:
            if st.button("⌨️ Markdown", use_container_width=True):
                st.session_state.editor_mode = "markdown"

        with mode_cols[2]:
            if st.button("📄 Simple", use_container_width=True):
                st.session_state.editor_mode = "simple"

        # Render appropriate editor
        editor = st.session_state.editor

        if st.session_state.editor_mode == "rich":
            new_content = render_editor(
                content=editor.get_content(),
                placeholder="Start writing your document...",
                height=600
            )

            if new_content:
                editor.set_content(new_content)

        elif st.session_state.editor_mode == "markdown":
            text = editor._extract_text_from_content()
            new_text = render_markdown_editor(text, height=600)

            if new_text != text:
                editor.set_content({"ops": [{"insert": new_text}]})

        else:  # simple
            text = editor._extract_text_from_content()
            new_text = render_simple_editor(
                content=text,
                placeholder="Start writing your document...",
                height=600
            )

            if new_text != text:
                editor.set_content({"ops": [{"insert": new_text}]})

    with preview_col:
        st.markdown("### Quick Stats")

        # Get statistics
        stats = editor.get_statistics()

        # Display stats
        st.metric("Words", stats['word_count'])
        st.metric("Characters", stats['character_count'])
        st.metric("Sentences", stats['sentence_count'])
        st.metric("Paragraphs", stats['paragraph_count'])
        st.metric("Reading Time", f"{stats['reading_time_minutes']} min")

        st.markdown("---")

        # Advanced stats
        with st.expander("📊 Advanced Stats"):
            ai = st.session_state.ai_assistant
            text = editor._extract_text_from_content()

            if text.strip():
                writing_stats = ai.get_writing_statistics(text)

                st.metric("Readability Score", writing_stats['flesch_reading_ease'])
                st.info(f"Grade Level: {writing_stats['grade_level']}")
                st.metric("Complex Words", writing_stats['complex_words'])
                st.metric("Avg Syllables/Word", writing_stats['avg_syllables_per_word'])

    # Status bar
    st.markdown("---")

    status_stats = {
        'word_count': stats['word_count'],
        'character_count': stats['character_count'],
        'paragraph_count': stats['paragraph_count'],
        'reading_time_minutes': stats['reading_time_minutes'],
        'saved': not editor.needs_save(),
        'last_save_time': editor.last_save_time.strftime("%H:%M:%S") if editor.last_save_time else None
    }

    render_status_bar(status_stats)

    # Auto-save functionality
    if st.session_state.auto_save_enabled and editor.needs_save():
        last_save = st.session_state.last_auto_save

        if last_save is None or (datetime.now() - last_save).total_seconds() > 30:
            save_document()


if __name__ == "__main__":
    main()
