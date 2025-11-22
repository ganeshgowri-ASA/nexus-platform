"""
Word Editor Module for NEXUS platform.
"""
import streamlit as st
from typing import Any, Dict, Optional
from pathlib import Path
from modules.base_module import BaseModule
from modules.word.document import Document
from modules.word.templates import DocumentTemplates
from modules.word.ai_features import AIFeatures
from modules.word.collab import CollaborativeSession, VersionDiff
from modules.word import ui
from core.logging import get_logger
from config.settings import settings

logger = get_logger(__name__)


class WordEditorModule(BaseModule):
    """Word Editor module with AI-powered features."""

    def __init__(self):
        """Initialize Word Editor module."""
        super().__init__()
        self.module_name = "Word Editor"
        self.icon = "📝"
        self.description = "AI-powered word processor with collaboration features"
        self.version = "1.0.0"

        # Initialize session state defaults
        self._initialize_module_state()

    def _initialize_module_state(self) -> None:
        """Initialize module-specific session state."""
        defaults = {
            "word_current_document": None,
            "word_ai_features": None,
            "word_collab_session": None,
            "word_auto_save_enabled": True,
            "word_suggested_text": None,
            "word_current_user": "User",
        }
        self.initialize_session_state(defaults)

    def _get_or_create_document(self) -> Document:
        """
        Get current document or create a new one.

        Returns:
            Document instance
        """
        if st.session_state.word_current_document is None:
            st.session_state.word_current_document = Document(
                title="Untitled Document",
                author=st.session_state.word_current_user,
            )
        return st.session_state.word_current_document

    def _get_or_create_ai_features(self) -> Optional[AIFeatures]:
        """
        Get AI features instance.

        Returns:
            AIFeatures instance or None
        """
        if st.session_state.word_ai_features is None:
            try:
                st.session_state.word_ai_features = AIFeatures(
                    api_key=settings.anthropic_api_key
                )
            except Exception as e:
                logger.error(f"Failed to initialize AI features: {e}")
                return None
        return st.session_state.word_ai_features

    def render(self) -> None:
        """Render the Word Editor module."""
        # Apply custom styling
        ui.apply_custom_css()

        # Show header
        self.show_header()

        # Get current document
        doc = self._get_or_create_document()

        # Sidebar
        with st.sidebar:
            self._render_sidebar(doc)

        # Main content area
        self._render_main_content(doc)

    def _render_sidebar(self, doc: Document) -> None:
        """
        Render sidebar with tools and options.

        Args:
            doc: Document instance
        """
        st.sidebar.title("🛠️ Tools")

        # Document title
        new_title = st.sidebar.text_input(
            "Document Title",
            value=doc.metadata.title,
            key="doc_title_input",
        )
        if new_title != doc.metadata.title:
            doc.metadata.title = new_title

        # Current user
        st.session_state.word_current_user = st.sidebar.text_input(
            "Your Name",
            value=st.session_state.word_current_user,
            key="user_name_input",
        )

        st.sidebar.divider()

        # Template selection
        template_name = ui.render_template_selector()
        if template_name:
            template_content = DocumentTemplates.get_template(template_name)
            doc.update_content(template_content)
            st.sidebar.success(f"Template '{template_name}' applied!")
            st.rerun()

        st.sidebar.divider()

        # AI Assistant
        ai_features = self._get_or_create_ai_features()
        if ai_features:
            ui.render_ai_assistant(doc, ai_features)
        else:
            st.sidebar.warning("⚠️ AI features unavailable. Set ANTHROPIC_API_KEY in .env")

        st.sidebar.divider()

        # Export options
        ui.render_export_options(doc)

        st.sidebar.divider()

        # Auto-save toggle
        st.session_state.word_auto_save_enabled = st.sidebar.checkbox(
            "💾 Auto-save",
            value=st.session_state.word_auto_save_enabled,
            key="auto_save_toggle",
        )

        # Save version button
        if st.sidebar.button("📌 Save Version", key="save_version_btn"):
            comment = st.sidebar.text_input("Version comment:", key="version_comment")
            doc.save_version(comment or "Manual save")
            st.sidebar.success("Version saved!")

        # New document button
        if st.sidebar.button("➕ New Document", key="new_doc_btn"):
            st.session_state.word_current_document = None
            st.rerun()

        st.sidebar.divider()

        # File upload
        st.sidebar.markdown("### 📂 Import")
        uploaded_file = st.sidebar.file_uploader(
            "Upload document",
            type=["docx", "txt", "md", "html"],
            key="file_uploader",
        )

        if uploaded_file:
            self._handle_file_upload(uploaded_file, doc)

    def _render_main_content(self, doc: Document) -> None:
        """
        Render main content area.

        Args:
            doc: Document instance
        """
        # Create tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs([
            "📝 Editor",
            "🕐 History",
            "💬 Comments",
            "👥 Collaboration"
        ])

        with tab1:
            self._render_editor_tab(doc)

        with tab2:
            ui.render_version_history(doc)

        with tab3:
            ui.render_comments_panel(doc, st.session_state.word_current_user)

        with tab4:
            self._render_collaboration_tab(doc)

    def _render_editor_tab(self, doc: Document) -> None:
        """
        Render the editor tab.

        Args:
            doc: Document instance
        """
        # Formatting toolbar
        formatting = ui.render_toolbar(doc)
        doc.formatting.update(formatting)

        st.divider()

        # Insert menu
        insert_item = ui.render_insert_menu()
        if insert_item:
            doc.content += insert_item
            st.rerun()

        st.divider()

        # Main editor
        new_content = ui.render_editor(doc, key="main_editor")

        # Update document if content changed
        if new_content != doc.content:
            doc.update_content(new_content)

            # Auto-save
            if st.session_state.word_auto_save_enabled:
                doc.save_version("Auto-save")

        st.divider()

        # Statistics
        ui.render_statistics(doc)

        # Show suggested text if available
        if st.session_state.word_suggested_text:
            st.info("💡 AI Suggestion Available")
            with st.expander("View Suggestion", expanded=True):
                st.markdown(st.session_state.word_suggested_text)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Apply", key="apply_suggestion"):
                        doc.update_content(st.session_state.word_suggested_text)
                        st.session_state.word_suggested_text = None
                        st.rerun()
                with col2:
                    if st.button("❌ Dismiss", key="dismiss_suggestion"):
                        st.session_state.word_suggested_text = None
                        st.rerun()

    def _render_collaboration_tab(self, doc: Document) -> None:
        """
        Render collaboration features.

        Args:
            doc: Document instance
        """
        st.markdown("### 👥 Collaborative Editing")

        # Get or create collaboration session
        if st.session_state.word_collab_session is None:
            st.session_state.word_collab_session = CollaborativeSession(
                doc.metadata.id
            )

        collab = st.session_state.word_collab_session

        # Show active users
        st.markdown("#### Active Users")
        active_users = collab.get_active_users()

        if active_users:
            for user in active_users:
                st.markdown(
                    f"<span style='color:{user.color}'>●</span> {user.name} (Position: {user.cursor_position})",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No other users currently active")

        st.divider()

        # Add simulated user (for demo purposes)
        st.markdown("#### Join Collaboration")
        col1, col2 = st.columns(2)

        with col1:
            new_user_name = st.text_input("User name", key="collab_user_name")

        with col2:
            colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8"]
            user_color = st.selectbox("Cursor color", colors, key="collab_user_color")

        if st.button("Join Session", key="join_collab"):
            if new_user_name:
                collab.add_user(new_user_name, new_user_name, user_color)
                st.success(f"{new_user_name} joined the session!")
                st.rerun()

        st.divider()

        # Cursor positions
        cursors = collab.get_cursor_positions()
        if cursors:
            st.markdown("#### Cursor Positions")
            for user_id, cursor_info in cursors.items():
                st.markdown(
                    f"**{cursor_info['name']}**: Character {cursor_info['position']}"
                )

    def _handle_file_upload(self, uploaded_file, doc: Document) -> None:
        """
        Handle file upload.

        Args:
            uploaded_file: Uploaded file
            doc: Document instance
        """
        try:
            file_extension = Path(uploaded_file.name).suffix.lower()

            if file_extension == ".docx":
                # Save temporarily and import
                temp_path = settings.temp_path / uploaded_file.name
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                doc.import_from_docx(temp_path)
                temp_path.unlink()  # Delete temp file

            elif file_extension in [".txt", ".md"]:
                content = uploaded_file.getvalue().decode("utf-8")
                doc.import_from_markdown(content)

            elif file_extension == ".html":
                content = uploaded_file.getvalue().decode("utf-8")
                doc.import_from_html(content)

            doc.metadata.title = Path(uploaded_file.name).stem
            st.sidebar.success(f"Imported: {uploaded_file.name}")
            st.rerun()

        except Exception as e:
            st.sidebar.error(f"Import failed: {str(e)}")
            logger.error(f"File import error: {e}")

    def handle_user_input(self, input_data: Any) -> Dict[str, Any]:
        """
        Handle user input.

        Args:
            input_data: User input

        Returns:
            Processing results
        """
        # This method is called by the base module
        # For Word Editor, most interaction is handled through Streamlit widgets
        return {"status": "success"}

    def export_data(self, data: Any, format: str = "json") -> bytes:
        """
        Export document data.

        Args:
            data: Document data
            format: Export format

        Returns:
            Exported data as bytes
        """
        doc = self._get_or_create_document()

        if format == "pdf":
            return doc.export_to_pdf()
        elif format == "docx":
            return doc.export_to_docx()
        elif format == "html":
            return doc.export_to_html().encode("utf-8")
        elif format == "markdown":
            return doc.export_to_markdown().encode("utf-8")
        else:
            return doc.to_json().encode("utf-8")

    def import_data(self, data: bytes, format: str = "json") -> Any:
        """
        Import document data.

        Args:
            data: Data to import
            format: Data format

        Returns:
            Imported document
        """
        if format == "json":
            doc = Document.from_json(data.decode("utf-8"))
            st.session_state.word_current_document = doc
            return doc

        return None
