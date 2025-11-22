"""Streamlit UI for Notes module."""

import streamlit as st
from datetime import datetime, timedelta
from typing import Optional

from nexus.core.database import get_db_session
from nexus.modules.notes.ai_assistant import AIAssistant
from nexus.modules.notes.export import NoteExporter
from nexus.modules.notes.markdown_processor import MarkdownProcessor
from nexus.modules.notes.models import NoteStatus
from nexus.modules.notes.schemas import NoteCreate, NoteUpdate
from nexus.modules.notes.service import NoteService


def init_session_state():
    """Initialize Streamlit session state."""
    if "user_id" not in st.session_state:
        st.session_state.user_id = "demo_user"  # TODO: Replace with actual auth

    if "current_note_id" not in st.session_state:
        st.session_state.current_note_id = None

    if "view_mode" not in st.session_state:
        st.session_state.view_mode = "all"  # all, favorites, archived

    if "search_query" not in st.session_state:
        st.session_state.search_query = ""

    if "selected_tags" not in st.session_state:
        st.session_state.selected_tags = []

    if "show_ai_panel" not in st.session_state:
        st.session_state.show_ai_panel = False


def render_notes_app():
    """Main notes application."""
    st.set_page_config(
        page_title="Nexus Notes",
        page_icon="📝",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    init_session_state()

    # Initialize services
    db = get_db_session()
    note_service = NoteService(db)
    ai_assistant = AIAssistant()
    markdown_processor = MarkdownProcessor()
    exporter = NoteExporter()

    # Custom CSS
    st.markdown(
        """
        <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 1rem;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .note-card {
            padding: 1rem;
            border-radius: 0.5rem;
            border: 1px solid #e2e8f0;
            margin-bottom: 0.5rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        .note-card:hover {
            border-color: #667eea;
            box-shadow: 0 4px 6px rgba(102, 126, 234, 0.1);
        }
        .tag-pill {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 1rem;
            font-size: 0.75rem;
            margin-right: 0.5rem;
            margin-bottom: 0.5rem;
        }
        .stat-card {
            text-align: center;
            padding: 1rem;
            border-radius: 0.5rem;
            background: #f7fafc;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar
    with st.sidebar:
        st.markdown('<div class="main-header">📝 Nexus Notes</div>', unsafe_allow_html=True)

        # User stats
        stats = note_service.get_note_stats(st.session_state.user_id)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Notes", stats["total"])
            st.metric("Favorites", stats["favorites"])
        with col2:
            st.metric("Tags", stats["tags"])
            st.metric("Notebooks", stats["notebooks"])

        st.divider()

        # Navigation
        st.subheader("Navigation")

        if st.button("➕ New Note", use_container_width=True, type="primary"):
            st.session_state.current_note_id = None
            st.session_state.view_mode = "editor"
            st.rerun()

        view_options = {
            "all": "📋 All Notes",
            "favorites": "⭐ Favorites",
            "archived": "📦 Archived",
        }

        for mode, label in view_options.items():
            if st.button(label, use_container_width=True):
                st.session_state.view_mode = mode
                st.session_state.current_note_id = None
                st.rerun()

        st.divider()

        # Notebooks section
        render_notebooks_sidebar(note_service)

        st.divider()

        # Tags section
        render_tags_sidebar(note_service)

    # Main content area
    if st.session_state.view_mode == "editor" or st.session_state.current_note_id:
        render_note_editor(note_service, ai_assistant, markdown_processor)
    elif st.session_state.view_mode == "all":
        render_notes_list(note_service, NoteStatus.ACTIVE, "All Notes")
    elif st.session_state.view_mode == "favorites":
        render_favorites_list(note_service)
    elif st.session_state.view_mode == "archived":
        render_notes_list(note_service, NoteStatus.ARCHIVED, "Archived Notes")


def render_notebooks_sidebar(note_service: NoteService):
    """Render notebooks in sidebar."""
    st.subheader("📚 Notebooks")

    notebooks = note_service.notebook_repo.get_by_user(st.session_state.user_id)

    if notebooks:
        for notebook in notebooks:
            if st.button(
                f"{notebook.icon} {notebook.name}",
                key=f"notebook_{notebook.id}",
                use_container_width=True,
            ):
                st.session_state.selected_notebook = notebook.id
                st.session_state.view_mode = "notebook"
                st.rerun()
    else:
        st.info("No notebooks yet. Create one!")

    if st.button("➕ New Notebook", use_container_width=True):
        create_notebook_modal(note_service)


def render_tags_sidebar(note_service: NoteService):
    """Render tags cloud in sidebar."""
    st.subheader("🏷️ Tags")

    tags = note_service.tag_repo.get_by_user(st.session_state.user_id)

    if tags:
        # Display tags as pills
        for tag in tags[:15]:  # Show top 15 tags
            if st.button(
                f"🏷️ {tag.name}",
                key=f"tag_{tag.id}",
                use_container_width=True,
            ):
                if tag.name in st.session_state.selected_tags:
                    st.session_state.selected_tags.remove(tag.name)
                else:
                    st.session_state.selected_tags.append(tag.name)
                st.rerun()

        if st.session_state.selected_tags:
            st.caption(f"Filtering by: {', '.join(st.session_state.selected_tags)}")
            if st.button("Clear filters"):
                st.session_state.selected_tags = []
                st.rerun()
    else:
        st.info("No tags yet!")


def render_notes_list(note_service: NoteService, status: NoteStatus, title: str):
    """Render list of notes."""
    st.title(title)

    # Search bar
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        search_query = st.text_input("🔍 Search notes", placeholder="Search by title or content...")
    with col2:
        sort_by = st.selectbox("Sort by", ["Updated", "Created", "Title"])
    with col3:
        view_style = st.selectbox("View", ["Cards", "List"])

    # Fetch notes
    if search_query or st.session_state.selected_tags:
        notes = note_service.search_notes(
            user_id=st.session_state.user_id,
            query=search_query if search_query else None,
            tags=st.session_state.selected_tags if st.session_state.selected_tags else None,
            status=status,
        )
    else:
        notes = note_service.list_notes(
            user_id=st.session_state.user_id, status=status, limit=100
        )

    # Display notes
    if not notes:
        st.info("No notes found. Create your first note!")
        if st.button("Create Note", type="primary"):
            st.session_state.view_mode = "editor"
            st.session_state.current_note_id = None
            st.rerun()
    else:
        st.caption(f"Found {len(notes)} notes")

        for note in notes:
            with st.container():
                col1, col2, col3 = st.columns([6, 2, 1])

                with col1:
                    if st.button(
                        f"{'⭐ ' if note.is_favorite else ''}**{note.title}**",
                        key=f"note_{note.id}",
                        use_container_width=True,
                    ):
                        st.session_state.current_note_id = note.id
                        st.rerun()

                    # Preview
                    preview = (note.content or "")[:150]
                    st.caption(preview + "..." if len(preview) == 150 else preview)

                    # Tags
                    if note.tags:
                        tags_html = " ".join(
                            [
                                f'<span class="tag-pill" style="background: {tag.color}; color: white;">{tag.name}</span>'
                                for tag in note.tags
                            ]
                        )
                        st.markdown(tags_html, unsafe_allow_html=True)

                with col2:
                    st.caption(f"Updated: {note.updated_at.strftime('%Y-%m-%d %H:%M')}")

                with col3:
                    # Quick actions
                    if st.button("⭐", key=f"fav_{note.id}"):
                        note_service.toggle_favorite(note.id, st.session_state.user_id)
                        st.rerun()

                st.divider()


def render_favorites_list(note_service: NoteService):
    """Render favorite notes."""
    st.title("⭐ Favorite Notes")

    notes = note_service.list_notes(
        user_id=st.session_state.user_id, favorites_only=True, limit=100
    )

    if not notes:
        st.info("No favorite notes yet. Star some notes to see them here!")
    else:
        for note in notes:
            with st.container():
                col1, col2 = st.columns([8, 1])

                with col1:
                    if st.button(
                        f"**{note.title}**", key=f"note_{note.id}", use_container_width=True
                    ):
                        st.session_state.current_note_id = note.id
                        st.rerun()

                    preview = (note.content or "")[:150]
                    st.caption(preview + "..." if len(preview) == 150 else preview)

                with col2:
                    if st.button("Remove", key=f"unfav_{note.id}"):
                        note_service.toggle_favorite(note.id, st.session_state.user_id)
                        st.rerun()

                st.divider()


def render_note_editor(
    note_service: NoteService, ai_assistant: AIAssistant, markdown_processor: MarkdownProcessor
):
    """Render note editor."""
    # Load existing note or create new
    if st.session_state.current_note_id:
        note = note_service.get_note(st.session_state.current_note_id, st.session_state.user_id)
        is_new = False
    else:
        note = None
        is_new = True

    # Header
    col1, col2, col3 = st.columns([6, 1, 1])
    with col1:
        st.title("✏️ " + ("New Note" if is_new else "Edit Note"))
    with col2:
        if st.button("💾 Save" if is_new else "💾 Update", type="primary"):
            save_note(note_service, note, is_new)
            st.success("Saved!" )
    with col3:
        if st.button("❌ Cancel"):
            st.session_state.view_mode = "all"
            st.session_state.current_note_id = None
            st.rerun()

    # Editor area
    col_main, col_ai = st.columns([3, 1])

    with col_main:
        # Title
        title = st.text_input(
            "Title",
            value=note.title if note else "",
            placeholder="Enter note title...",
            key="note_title",
        )

        # Editor tabs
        tab_write, tab_preview = st.tabs(["✍️ Write", "👁️ Preview"])

        with tab_write:
            content = st.text_area(
                "Content (Markdown supported)",
                value=note.content_markdown or note.content if note else "",
                height=400,
                placeholder="Start writing... (Markdown supported)",
                key="note_content",
            )

        with tab_preview:
            if content:
                html = markdown_processor.to_html(content)
                st.markdown(html, unsafe_allow_html=True)
            else:
                st.info("Write something to see the preview!")

        # Tags
        tags_input = st.text_input(
            "Tags (comma-separated)",
            value=", ".join([tag.name for tag in note.tags]) if note and note.tags else "",
            placeholder="tag1, tag2, tag3",
            key="note_tags",
        )

    # AI Assistant panel
    with col_ai:
        st.subheader("🤖 AI Assistant")

        if st.button("✨ Generate Title", use_container_width=True):
            if content:
                with st.spinner("Generating..."):
                    title_suggestion = ai_assistant.generate_note_title(content)
                    st.session_state.note_title = title_suggestion
                    st.rerun()

        if st.button("📝 Summarize", use_container_width=True):
            if note:
                with st.spinner("Summarizing..."):
                    summary = ai_assistant.summarize_note(note)
                    st.info(summary)

        if st.button("🏷️ Suggest Tags", use_container_width=True):
            if note:
                with st.spinner("Analyzing..."):
                    tags = ai_assistant.suggest_tags(note)
                    st.session_state.note_tags = ", ".join(tags)
                    st.rerun()

        if st.button("📋 Extract Tasks", use_container_width=True):
            if note:
                with st.spinner("Extracting..."):
                    tasks = ai_assistant.extract_tasks(note)
                    if tasks:
                        st.write("**Found tasks:**")
                        for task in tasks:
                            st.markdown(f"- {task.get('task', 'N/A')}")
                    else:
                        st.info("No tasks found")

        if st.button("✅ Check Grammar", use_container_width=True):
            if content:
                with st.spinner("Checking..."):
                    result = ai_assistant.check_grammar(content)
                    if result.get("has_errors"):
                        st.write("**Suggestions:**")
                        for sugg in result.get("suggestions", []):
                            st.markdown(f"- {sugg.get('explanation', 'N/A')}")
                    else:
                        st.success("Looks good!")


def save_note(note_service: NoteService, note: Optional, is_new: bool):
    """Save or update note."""
    title = st.session_state.note_title
    content = st.session_state.note_content
    tags_str = st.session_state.note_tags

    tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]

    if not title:
        st.error("Title is required!")
        return

    if is_new:
        # Create new note
        note_data = NoteCreate(
            title=title, content=content, content_markdown=content, tags=tags
        )
        new_note = note_service.create_note(st.session_state.user_id, note_data)
        st.session_state.current_note_id = new_note.id
        st.session_state.view_mode = "all"
    else:
        # Update existing note
        note_data = NoteUpdate(
            title=title, content=content, content_markdown=content, tags=tags
        )
        note_service.update_note(note.id, st.session_state.user_id, note_data)
        st.session_state.view_mode = "all"


def create_notebook_modal(note_service: NoteService):
    """Create new notebook modal."""
    with st.form("new_notebook"):
        name = st.text_input("Notebook Name")
        description = st.text_area("Description")
        icon = st.text_input("Icon (emoji)", value="📓")
        color = st.color_picker("Color", value="#4A90E2")

        submitted = st.form_submit_button("Create Notebook")
        if submitted and name:
            note_service.notebook_repo.create(
                user_id=st.session_state.user_id,
                name=name,
                description=description,
                icon=icon,
                color=color,
            )
            st.success("Notebook created!")
            st.rerun()


if __name__ == "__main__":
    render_notes_app()
