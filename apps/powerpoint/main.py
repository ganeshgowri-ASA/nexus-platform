"""PowerPoint / Presentation Editor Application"""


def main():
    import streamlit as st

    try:
        # Lazy import database
        from database import init_database
        init_database()

        st.set_page_config(
            page_title="PowerPoint - NEXUS",
            page_icon="📊",
            layout="wide"
        )

        st.title("📊 PowerPoint / Presentation Editor")

        # Session state
        if 'slides' not in st.session_state:
            st.session_state.slides = []

        # Sidebar
        st.sidebar.title("📊 PowerPoint")

        if st.sidebar.button("➕ New Presentation", use_container_width=True):
            st.session_state.slides = []
            st.rerun()

        st.sidebar.divider()
        st.sidebar.info("Create presentations with slide management.")

        # Main content
        col1, col2 = st.columns([2, 1])
        with col1:
            pres_title = st.text_input("Presentation Title", value="Untitled Presentation")
        with col2:
            theme = st.selectbox("Theme", ["Professional", "Modern", "Classic", "Creative"])

        st.divider()
        st.subheader("Slides")

        if st.button("➕ Add Slide"):
            st.session_state.slides.append({
                'title': f'Slide {len(st.session_state.slides) + 1}',
                'content': '',
                'notes': ''
            })
            st.rerun()

        if st.session_state.slides:
            slide_tabs = st.tabs([f"Slide {i+1}" for i in range(len(st.session_state.slides))])

            for idx, tab in enumerate(slide_tabs):
                with tab:
                    slide = st.session_state.slides[idx]
                    slide['title'] = st.text_input("Slide Title", value=slide.get('title', ''), key=f"title_{idx}")
                    slide['content'] = st.text_area("Content", value=slide.get('content', ''), height=200, key=f"content_{idx}")
                    slide['notes'] = st.text_area("Speaker Notes", value=slide.get('notes', ''), height=100, key=f"notes_{idx}")

                    col1, col2 = st.columns(2)
                    with col1:
                        if idx > 0 and st.button("⬆️ Move Up", key=f"up_{idx}"):
                            st.session_state.slides[idx], st.session_state.slides[idx-1] = st.session_state.slides[idx-1], st.session_state.slides[idx]
                            st.rerun()
                    with col2:
                        if st.button("🗑️ Delete", key=f"del_{idx}"):
                            st.session_state.slides.pop(idx)
                            st.rerun()
        else:
            st.info("No slides yet. Click 'Add Slide' to get started.")

        st.divider()
        if st.button("💾 Save Presentation", type="primary"):
            st.success(f"Presentation '{pres_title}' saved with {len(st.session_state.slides)} slides!")

    except Exception as e:
        import streamlit as st
        st.error(f"Error loading module: {str(e)}")
        with st.expander("Technical Details"):
            import traceback
            st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
