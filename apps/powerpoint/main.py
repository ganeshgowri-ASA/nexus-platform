"""PowerPoint / Presentation Editor Application"""


def main():
    """Main application entry point with lazy loading"""
    import streamlit as st

    st.set_page_config(
        page_title="PowerPoint - NEXUS",
        page_icon="📊",
        layout="wide"
    )

    try:
        # Lazy imports to avoid circular dependencies
        from datetime import datetime
        from database import init_database, get_session
        from database.models import Presentation, Slide
        from config.settings import settings
        from config.constants import PRESENTATION_THEMES

        # Initialize database
        init_database()

        # Initialize session state
        if 'current_presentation' not in st.session_state:
            st.session_state.current_presentation = None
        if 'current_slide_idx' not in st.session_state:
            st.session_state.current_slide_idx = 0
        if 'slides' not in st.session_state:
            st.session_state.slides = []

        # Sidebar
        st.sidebar.title("📊 PowerPoint")

        if st.sidebar.button("➕ New Presentation", use_container_width=True):
            st.session_state.current_presentation = None
            st.session_state.slides = []
            st.session_state.current_slide_idx = 0
            st.rerun()

        st.sidebar.divider()

        # List existing presentations
        db = get_session()
        try:
            presentations = db.query(Presentation).order_by(Presentation.updated_at.desc()).all()

            st.sidebar.subheader("My Presentations")
            for pres in presentations:
                col1, col2 = st.sidebar.columns([3, 1])
                with col1:
                    if st.button(f"📑 {pres.title}", key=f"pres_{pres.id}", use_container_width=True):
                        st.session_state.current_presentation = pres.id
                        slides = db.query(Slide).filter(
                            Slide.presentation_id == pres.id
                        ).order_by(Slide.slide_number).all()
                        st.session_state.slides = slides
                        st.session_state.current_slide_idx = 0
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"del_pres_{pres.id}"):
                        db.query(Slide).filter(Slide.presentation_id == pres.id).delete()
                        db.delete(pres)
                        db.commit()
                        st.rerun()
        finally:
            db.close()

        # Main content
        st.title("📊 PowerPoint / Presentation Editor")

        # Presentation metadata
        col1, col2 = st.columns([2, 1])
        with col1:
            pres_title = st.text_input("Presentation Title", value="Untitled Presentation")
        with col2:
            theme = st.selectbox("Theme", list(PRESENTATION_THEMES.keys()))

        pres_description = st.text_area("Description", height=80)
        pres_author = st.text_input("Author", value="")

        st.divider()

        # AI Content Generation
        with st.expander("🤖 AI Content Generation"):
            topic = st.text_input("Topic", placeholder="e.g., Machine Learning Fundamentals")
            num_slides = st.slider("Number of Slides", 3, 15, 5)

            if st.button("Generate Slides with AI", type="primary"):
                if topic and settings.ENABLE_AI_FEATURES:
                    try:
                        from ai.claude_client import ClaudeClient
                        with st.spinner("Generating slides..."):
                            ai_client = ClaudeClient()
                            result = ai_client.generate_slide_content(topic, num_slides)
                            st.session_state.slides = []
                            for i, slide_data in enumerate(result.get('slides', [])):
                                slide = Slide(
                                    presentation_id="temp",
                                    slide_number=i + 1,
                                    title=slide_data.get('title', f'Slide {i+1}'),
                                    content='\n'.join(slide_data.get('content', [])),
                                    layout='title_and_content'
                                )
                                st.session_state.slides.append(slide)
                            st.success(f"Generated {len(st.session_state.slides)} slides!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error generating slides: {e}")
                else:
                    st.warning("Please enter a topic and ensure AI features are enabled")

        st.divider()

        # Slide Editor
        st.subheader("Slides")

        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            if st.button("➕ Add Slide"):
                new_slide = Slide(
                    presentation_id="temp",
                    slide_number=len(st.session_state.slides) + 1,
                    title="New Slide",
                    content="",
                    layout='title_and_content'
                )
                st.session_state.slides.append(new_slide)
                st.session_state.current_slide_idx = len(st.session_state.slides) - 1
                st.rerun()

        if st.session_state.slides:
            slide_tabs = st.tabs([f"Slide {i+1}" for i in range(len(st.session_state.slides))])

            for idx, tab in enumerate(slide_tabs):
                with tab:
                    slide = st.session_state.slides[idx]
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        slide.title = st.text_input("Slide Title", value=slide.title or "", key=f"title_{idx}")
                    with col2:
                        slide.layout = st.selectbox("Layout", ["title_and_content", "title_only", "blank"],
                                                   index=0, key=f"layout_{idx}")

                    slide.content = st.text_area("Content", value=slide.content or "",
                                                height=200, key=f"content_{idx}",
                                                help="Use bullet points separated by new lines")
                    slide.notes = st.text_area("Speaker Notes", value=slide.notes or "",
                                              height=100, key=f"notes_{idx}")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if idx > 0 and st.button("⬆️ Move Up", key=f"up_{idx}"):
                            st.session_state.slides[idx], st.session_state.slides[idx-1] = \
                                st.session_state.slides[idx-1], st.session_state.slides[idx]
                            st.rerun()
                    with col2:
                        if idx < len(st.session_state.slides) - 1 and st.button("⬇️ Move Down", key=f"down_{idx}"):
                            st.session_state.slides[idx], st.session_state.slides[idx+1] = \
                                st.session_state.slides[idx+1], st.session_state.slides[idx]
                            st.rerun()
                    with col3:
                        if st.button("🗑️ Delete Slide", key=f"del_{idx}"):
                            st.session_state.slides.pop(idx)
                            st.rerun()
        else:
            st.info("No slides yet. Click 'Add Slide' or use AI to generate slides.")

        st.divider()

        # Save and Export
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("💾 Save Presentation", type="primary"):
                if pres_title:
                    db = get_session()
                    try:
                        if st.session_state.current_presentation:
                            pres = db.query(Presentation).filter(
                                Presentation.id == st.session_state.current_presentation
                            ).first()
                            pres.title = pres_title
                            pres.description = pres_description
                            pres.author = pres_author
                            pres.theme = theme
                            pres.slides_count = len(st.session_state.slides)
                            pres.updated_at = datetime.utcnow()
                            db.query(Slide).filter(Slide.presentation_id == pres.id).delete()
                        else:
                            pres = Presentation(
                                title=pres_title,
                                description=pres_description,
                                author=pres_author,
                                theme=theme,
                                slides_count=len(st.session_state.slides)
                            )
                            db.add(pres)
                            db.flush()
                            st.session_state.current_presentation = pres.id

                        for idx, slide in enumerate(st.session_state.slides):
                            new_slide = Slide(
                                presentation_id=pres.id,
                                slide_number=idx + 1,
                                title=slide.title,
                                content=slide.content,
                                layout=slide.layout,
                                notes=slide.notes
                            )
                            db.add(new_slide)
                        db.commit()
                        st.success("Presentation saved successfully!")
                    finally:
                        db.close()
                else:
                    st.error("Please enter a presentation title")

        with col2:
            if st.button("📄 Export to PPTX"):
                if st.session_state.slides:
                    try:
                        from utils.exporters import export_to_pptx
                        slides_data = [
                            {'title': slide.title, 'content': slide.content.split('\n') if slide.content else []}
                            for slide in st.session_state.slides
                        ]
                        output_path = settings.EXPORTS_DIR / f"{pres_title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pptx"
                        export_to_pptx(slides_data, str(output_path), theme)
                        with open(output_path, 'rb') as f:
                            st.download_button("⬇️ Download PPTX", f, file_name=output_path.name,
                                             mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")
                        st.success("PPTX exported!")
                    except Exception as e:
                        st.error(f"Export error: {e}")
                else:
                    st.warning("No slides to export")

        with col3:
            if st.button("📄 Export to PDF"):
                if st.session_state.slides:
                    try:
                        from utils.exporters import export_to_pdf
                        presentation_data = {
                            'title': pres_title,
                            'slides': [{'title': slide.title, 'content': slide.content} for slide in st.session_state.slides]
                        }
                        output_path = settings.EXPORTS_DIR / f"{pres_title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                        export_to_pdf(presentation_data, str(output_path), "presentation")
                        with open(output_path, 'rb') as f:
                            st.download_button("⬇️ Download PDF", f, file_name=output_path.name, mime="application/pdf")
                        st.success("PDF exported!")
                    except Exception as e:
                        st.error(f"Export error: {e}")
                else:
                    st.warning("No slides to export")

    except Exception as e:
        st.error(f"Error in PowerPoint module: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
