"""Notes Application with Rich Text, Tags, Folders, AI Summaries"""
import streamlit as st
from datetime import datetime
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from database.connection import SessionLocal, init_db
from database.models import Note
from ai.claude_client import ClaudeClient
from config.settings import settings
from config.constants import NOTE_CATEGORIES
from utils.exporters import export_to_pdf, export_to_docx
from utils.formatters import format_relative_time, truncate_text

def initialize_session_state():
    """Initialize session state variables"""
    if 'current_note' not in st.session_state:
        st.session_state.current_note = None
    if 'current_folder' not in st.session_state:
        st.session_state.current_folder = 'General'
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""

def render_sidebar():
    """Render sidebar with folders and filters"""
    st.sidebar.title("📝 Notes")

    # New note button
    if st.sidebar.button("➕ New Note", use_container_width=True):
        st.session_state.current_note = None
        st.rerun()

    st.sidebar.divider()

    # Search
    search = st.sidebar.text_input("🔍 Search", value=st.session_state.search_query)
    if search != st.session_state.search_query:
        st.session_state.search_query = search
        st.rerun()

    st.sidebar.divider()

    # Folders
    st.sidebar.subheader("Folders")

    db = SessionLocal()

    # Get unique folders
    folders = db.query(Note.folder).distinct().all()
    folder_list = ['All'] + [f[0] for f in folders if f[0]]

    for folder in folder_list:
        count = db.query(Note).filter(Note.folder == folder).count() if folder != 'All' else db.query(Note).count()

        if st.sidebar.button(f"📁 {folder} ({count})", key=f"folder_{folder}", use_container_width=True):
            st.session_state.current_folder = folder
            st.rerun()

    db.close()

    st.sidebar.divider()

    # Categories filter
    st.sidebar.subheader("Categories")
    if 'filter_categories' not in st.session_state:
        st.session_state.filter_categories = NOTE_CATEGORIES

    for category in NOTE_CATEGORIES:
        checked = st.sidebar.checkbox(category,
                                      value=category in st.session_state.filter_categories,
                                      key=f"cat_{category}")
        if checked and category not in st.session_state.filter_categories:
            st.session_state.filter_categories.append(category)
        elif not checked and category in st.session_state.filter_categories:
            st.session_state.filter_categories.remove(category)

    st.sidebar.divider()

    # Quick filters
    st.sidebar.subheader("Quick Filters")
    if st.sidebar.button("⭐ Favorites", use_container_width=True):
        st.session_state.show_favorites = True
        st.rerun()

    if st.sidebar.button("📦 Archived", use_container_width=True):
        st.session_state.show_archived = True
        st.rerun()

def render_note_list(db):
    """Render list of notes"""
    st.subheader("📝 Notes")

    # Build query
    query = db.query(Note)

    # Apply folder filter
    if st.session_state.current_folder != 'All':
        query = query.filter(Note.folder == st.session_state.current_folder)

    # Apply category filter
    if hasattr(st.session_state, 'filter_categories'):
        query = query.filter(Note.category.in_(st.session_state.filter_categories))

    # Apply search
    if st.session_state.search_query:
        search_term = f"%{st.session_state.search_query}%"
        query = query.filter(
            (Note.title.like(search_term)) |
            (Note.content.like(search_term))
        )

    # Apply special filters
    if hasattr(st.session_state, 'show_favorites') and st.session_state.show_favorites:
        query = query.filter(Note.is_favorite == True)
        st.session_state.show_favorites = False

    if hasattr(st.session_state, 'show_archived') and st.session_state.show_archived:
        query = query.filter(Note.is_archived == True)
        st.session_state.show_archived = False
    else:
        query = query.filter(Note.is_archived == False)

    # Order by most recent
    notes = query.order_by(Note.updated_at.desc()).all()

    # Display notes
    if notes:
        for note in notes:
            with st.container():
                col1, col2, col3 = st.columns([4, 1, 1])

                with col1:
                    # Note title and preview
                    title_prefix = "⭐ " if note.is_favorite else ""
                    if st.button(f"{title_prefix}{note.title}", key=f"note_{note.id}",
                               use_container_width=True):
                        st.session_state.current_note = note.id
                        st.rerun()

                    # Preview
                    preview = truncate_text(note.content or "", 100)
                    st.caption(preview)

                    # Tags
                    if note.tags:
                        tags_text = " ".join([f"#{tag}" for tag in note.tags])
                        st.caption(tags_text)

                with col2:
                    st.caption(f"📁 {note.folder}")
                    st.caption(format_relative_time(note.updated_at))

                with col3:
                    col_fav, col_del = st.columns(2)
                    with col_fav:
                        if st.button("⭐" if not note.is_favorite else "⭐",
                                   key=f"fav_{note.id}"):
                            note.is_favorite = not note.is_favorite
                            db.commit()
                            st.rerun()

                    with col_del:
                        if st.button("🗑️", key=f"del_{note.id}"):
                            db.delete(note)
                            db.commit()
                            st.rerun()

                st.divider()
    else:
        st.info("No notes found. Create your first note!")

def render_note_editor(db):
    """Render note editor"""

    if st.session_state.current_note:
        note = db.query(Note).filter(Note.id == st.session_state.current_note).first()
        if not note:
            st.error("Note not found")
            return
    else:
        # New note
        note = Note(
            title="Untitled Note",
            content="",
            folder=st.session_state.current_folder,
            category='Personal'
        )

    # Back button
    if st.button("← Back to Notes"):
        st.session_state.current_note = None
        st.rerun()

    st.divider()

    # Note editor
    col1, col2 = st.columns([3, 1])

    with col1:
        note.title = st.text_input("Title", value=note.title)

    with col2:
        note.color = st.color_picker("Color", value=note.color or "#FFFFFF")

    # Rich text editor (using text area as placeholder - can be enhanced with custom component)
    note.content = st.text_area("Content", value=note.content or "", height=400,
                                help="Supports markdown formatting")

    # Metadata
    col1, col2, col3 = st.columns(3)

    with col1:
        note.folder = st.text_input("Folder", value=note.folder or "General")

    with col2:
        note.category = st.selectbox("Category", NOTE_CATEGORIES,
                                    index=NOTE_CATEGORIES.index(note.category) if note.category in NOTE_CATEGORIES else 0)

    with col3:
        note.author = st.text_input("Author", value=note.author or "")

    # Tags
    tags_input = st.text_input("Tags (comma-separated)",
                              value=", ".join(note.tags) if note.tags else "")
    note.tags = [t.strip() for t in tags_input.split(',') if t.strip()]

    # Checkboxes
    col1, col2 = st.columns(2)
    with col1:
        note.is_favorite = st.checkbox("⭐ Favorite", value=note.is_favorite)
    with col2:
        note.is_archived = st.checkbox("📦 Archived", value=note.is_archived)

    st.divider()

    # AI Summary
    if settings.ENABLE_AI_FEATURES:
        with st.expander("🤖 AI Summary"):
            if note.ai_summary:
                st.write(note.ai_summary)

            if st.button("Generate Summary", type="primary"):
                if note.content:
                    try:
                        with st.spinner("Generating summary..."):
                            ai_client = ClaudeClient()
                            summary = ai_client.summarize_note(note.content)
                            note.ai_summary = summary
                            db.commit()
                            st.success("Summary generated!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Add content to generate summary")

    st.divider()

    # Actions
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("💾 Save", type="primary"):
            if note.title:
                if not st.session_state.current_note:
                    db.add(note)
                    db.flush()
                    st.session_state.current_note = note.id

                db.commit()
                st.success("Note saved!")
            else:
                st.error("Please enter a title")

    with col2:
        if st.button("📄 Export to PDF"):
            if note.content:
                note_data = {
                    'title': note.title,
                    'content': note.content
                }

                output_path = settings.EXPORTS_DIR / f"{note.title.replace(' ', '_')}.pdf"
                export_to_pdf(note_data, str(output_path), "note")

                with open(output_path, 'rb') as f:
                    st.download_button(
                        "⬇️ Download PDF",
                        f,
                        file_name=output_path.name,
                        mime="application/pdf"
                    )

    with col3:
        if st.button("📄 Export to DOCX"):
            if note.content:
                note_data = {
                    'title': note.title,
                    'content': note.content
                }

                output_path = settings.EXPORTS_DIR / f"{note.title.replace(' ', '_')}.docx"
                export_to_docx(note_data, str(output_path))

                with open(output_path, 'rb') as f:
                    st.download_button(
                        "⬇️ Download DOCX",
                        f,
                        file_name=output_path.name,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )

    with col4:
        if st.button("📋 Export to Markdown"):
            if note.content:
                md_content = f"# {note.title}\n\n{note.content}"

                output_path = settings.EXPORTS_DIR / f"{note.title.replace(' ', '_')}.md"
                with open(output_path, 'w') as f:
                    f.write(md_content)

                with open(output_path, 'rb') as f:
                    st.download_button(
                        "⬇️ Download MD",
                        f,
                        file_name=output_path.name,
                        mime="text/markdown"
                    )

def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="Notes - NEXUS",
        page_icon="📝",
        layout="wide"
    )

    # Initialize database
    init_db()

    # Initialize session state
    initialize_session_state()

    # Render sidebar
    render_sidebar()

    # Render main content
    st.title("📝 Notes")

    db = SessionLocal()

    if st.session_state.current_note is not None or st.button("Create New Note"):
        render_note_editor(db)
    else:
        render_note_list(db)

    db.close()

if __name__ == "__main__":
    main()
