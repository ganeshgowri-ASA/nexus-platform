"""Notes Application with Rich Text, Tags, Folders"""


def main():
    import streamlit as st
    from datetime import datetime

    try:
        # Lazy import database
        from database import init_database
        init_database()

        st.set_page_config(
            page_title="Notes - NEXUS",
            page_icon="📝",
            layout="wide"
        )

        st.title("📝 Notes")

        # Session state
        if 'notes' not in st.session_state:
            st.session_state.notes = []
        if 'current_note' not in st.session_state:
            st.session_state.current_note = None
        if 'current_folder' not in st.session_state:
            st.session_state.current_folder = 'All'

        # Sidebar
        st.sidebar.title("📝 Notes")

        if st.sidebar.button("➕ New Note", use_container_width=True):
            st.session_state.current_note = None
            st.rerun()

        st.sidebar.divider()
        search = st.sidebar.text_input("🔍 Search")

        st.sidebar.divider()
        st.sidebar.subheader("Folders")

        folders = ['All'] + list(set(n.get('folder', 'General') for n in st.session_state.notes))
        for folder in folders:
            count = len(st.session_state.notes) if folder == 'All' else len([n for n in st.session_state.notes if n.get('folder') == folder])
            if st.sidebar.button(f"📁 {folder} ({count})", key=f"folder_{folder}", use_container_width=True):
                st.session_state.current_folder = folder
                st.session_state.current_note = None
                st.rerun()

        # Main content
        if st.session_state.current_note is not None:
            note = st.session_state.notes[st.session_state.current_note]

            if st.button("← Back to Notes"):
                st.session_state.current_note = None
                st.rerun()

            note['title'] = st.text_input("Title", value=note.get('title', ''))
            note['content'] = st.text_area("Content", value=note.get('content', ''), height=400)

            col1, col2 = st.columns(2)
            with col1:
                note['folder'] = st.text_input("Folder", value=note.get('folder', 'General'))
            with col2:
                note['category'] = st.selectbox("Category", ["Personal", "Work", "Ideas", "Archive"],
                                                index=["Personal", "Work", "Ideas", "Archive"].index(note.get('category', 'Personal')))

            tags_input = st.text_input("Tags (comma-separated)", value=", ".join(note.get('tags', [])))
            note['tags'] = [t.strip() for t in tags_input.split(',') if t.strip()]

            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save", type="primary"):
                    st.success("Note saved!")
            with col2:
                if st.button("🗑️ Delete"):
                    st.session_state.notes.pop(st.session_state.current_note)
                    st.session_state.current_note = None
                    st.rerun()
        else:
            # Note list or new note form
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"📝 {st.session_state.current_folder}")
            with col2:
                if st.button("Create New Note"):
                    st.session_state.notes.append({
                        'title': 'Untitled Note',
                        'content': '',
                        'folder': 'General',
                        'category': 'Personal',
                        'tags': [],
                        'created': datetime.now().isoformat()
                    })
                    st.session_state.current_note = len(st.session_state.notes) - 1
                    st.rerun()

            # Filter notes
            filtered_notes = st.session_state.notes
            if st.session_state.current_folder != 'All':
                filtered_notes = [n for n in filtered_notes if n.get('folder') == st.session_state.current_folder]
            if search:
                filtered_notes = [n for n in filtered_notes if search.lower() in n.get('title', '').lower() or search.lower() in n.get('content', '').lower()]

            if filtered_notes:
                for idx, note in enumerate(filtered_notes):
                    actual_idx = st.session_state.notes.index(note)
                    col1, col2, col3 = st.columns([4, 1, 1])
                    with col1:
                        if st.button(f"📝 {note.get('title', 'Untitled')}", key=f"note_{actual_idx}", use_container_width=True):
                            st.session_state.current_note = actual_idx
                            st.rerun()
                        preview = (note.get('content', '')[:100] + '...') if len(note.get('content', '')) > 100 else note.get('content', '')
                        st.caption(preview)
                    with col2:
                        st.caption(f"📁 {note.get('folder', 'General')}")
                    with col3:
                        if st.button("🗑️", key=f"del_{actual_idx}"):
                            st.session_state.notes.pop(actual_idx)
                            st.rerun()
                    st.divider()
            else:
                st.info("No notes found. Create your first note!")

    except Exception as e:
        import streamlit as st
        st.error(f"Error loading module: {str(e)}")
        with st.expander("Technical Details"):
            import traceback
            st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
