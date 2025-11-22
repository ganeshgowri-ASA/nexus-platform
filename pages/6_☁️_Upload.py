"""File Upload page for NEXUS Platform.

This page provides a comprehensive file upload interface with drag-drop,
multi-file support, progress tracking, and auto-categorization.
"""
import streamlit as st
from io import BytesIO
from database.engine import get_session, init_db
from modules.files import FileManager


# Page configuration
st.set_page_config(
    page_title="Upload Files - NEXUS Platform",
    page_icon="☁️",
    layout="wide"
)

# Initialize database
init_db()

# Initialize file manager
if 'file_manager' not in st.session_state:
    st.session_state.file_manager = FileManager()

# Mock user (in production, this would come from authentication)
if 'user_id' not in st.session_state:
    st.session_state.user_id = 1
if 'username' not in st.session_state:
    st.session_state.username = 'demo_user'

# Initialize upload state
if 'upload_results' not in st.session_state:
    st.session_state.upload_results = []


def get_file_icon(mime_type: str) -> str:
    """Get icon for file type."""
    if not mime_type:
        return "📎"

    if mime_type.startswith('image/'):
        return "🖼️"
    elif mime_type.startswith('video/'):
        return "🎥"
    elif mime_type.startswith('audio/'):
        return "🎵"
    elif 'pdf' in mime_type:
        return "📕"
    elif 'word' in mime_type or 'document' in mime_type:
        return "📄"
    elif 'excel' in mime_type or 'spreadsheet' in mime_type:
        return "📊"
    elif 'powerpoint' in mime_type or 'presentation' in mime_type:
        return "📽️"
    elif 'zip' in mime_type or 'compressed' in mime_type:
        return "📦"
    else:
        return "📎"


def upload_file(file, description: str, tags: list, session) -> dict:
    """Upload a single file."""
    try:
        # Convert UploadedFile to BytesIO
        file_content = BytesIO(file.read())
        file.seek(0)  # Reset for potential re-use

        # Upload file
        success, file_id, error = st.session_state.file_manager.upload_file(
            session=session,
            file_content=file_content,
            filename=file.name,
            user_id=st.session_state.user_id,
            description=description,
            tags=tags if tags else None
        )

        return {
            'filename': file.name,
            'success': success,
            'file_id': file_id,
            'error': error,
            'size': file.size,
            'type': file.type
        }

    except Exception as e:
        return {
            'filename': file.name,
            'success': False,
            'error': str(e),
            'size': file.size,
            'type': file.type
        }


def main():
    """Main function for the Upload page."""
    st.title("☁️ Upload Files")
    st.markdown("Upload and manage your files with drag-and-drop support")

    # Get database session
    session = next(get_session())

    # Sidebar - Upload settings
    with st.sidebar:
        st.header("Upload Settings")

        # Folder selection
        st.subheader("📁 Destination")
        folder = st.selectbox(
            "Select Folder",
            ["Root", "Documents", "Images", "Videos", "Archives"],
            help="Choose where to upload files"
        )

        # Tags
        st.subheader("🏷️ Tags")
        tags_input = st.text_input(
            "Add Tags",
            placeholder="work, important, project-x",
            help="Comma-separated tags"
        )
        tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()]

        # Description
        st.subheader("📝 Description")
        description = st.text_area(
            "File Description",
            placeholder="Optional description for uploaded files",
            help="Add a description for better organization"
        )

        # File type info
        st.divider()
        st.subheader("ℹ️ Supported Files")

        with st.expander("Documents"):
            st.markdown("""
            - Word: .doc, .docx
            - Excel: .xls, .xlsx, .csv
            - PowerPoint: .ppt, .pptx
            - PDF: .pdf
            - Text: .txt, .md, .rtf
            - Data: .json, .xml, .yaml
            """)

        with st.expander("Images"):
            st.markdown("""
            - .jpg, .jpeg, .png
            - .gif, .bmp, .svg, .webp
            - Max 50MB per image
            """)

        with st.expander("Media"):
            st.markdown("""
            - Video: .mp4, .avi, .mov, .wmv
            - Audio: .mp3, .wav, .ogg, .m4a
            """)

        with st.expander("Archives"):
            st.markdown("""
            - .zip, .tar, .gz, .rar, .7z
            - Auto-extract option available
            """)

    # Main upload area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("📤 Upload Files")

        # File uploader with drag-and-drop
        uploaded_files = st.file_uploader(
            "Choose files to upload",
            accept_multiple_files=True,
            help="Drag and drop files here or click to browse",
            label_visibility="collapsed"
        )

        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} file(s) selected")

            # Display selected files
            st.subheader("Selected Files")

            for idx, file in enumerate(uploaded_files):
                with st.container():
                    col_icon, col_name, col_size, col_type = st.columns([1, 4, 2, 2])

                    with col_icon:
                        st.write(get_file_icon(file.type))

                    with col_name:
                        st.write(f"**{file.name}**")

                    with col_size:
                        size_mb = file.size / (1024 * 1024)
                        st.write(f"{size_mb:.2f} MB")

                    with col_type:
                        st.write(file.type or "Unknown")

            st.divider()

            # Upload button
            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])

            with col_btn1:
                if st.button("🚀 Upload All", type="primary", use_container_width=True):
                    # Create progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    results = []
                    total_files = len(uploaded_files)

                    for idx, file in enumerate(uploaded_files):
                        status_text.text(f"Uploading {file.name}...")

                        result = upload_file(file, description, tags, session)
                        results.append(result)

                        # Update progress
                        progress = (idx + 1) / total_files
                        progress_bar.progress(progress)

                    st.session_state.upload_results = results

                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()

                    # Show summary
                    successful = sum(1 for r in results if r['success'])
                    failed = total_files - successful

                    if failed == 0:
                        st.success(f"✅ Successfully uploaded {successful} file(s)!")
                    else:
                        st.warning(f"⚠️ Uploaded {successful} file(s), {failed} failed")

                    st.rerun()

            with col_btn2:
                if st.button("🗑️ Clear All", use_container_width=True):
                    st.rerun()

    with col2:
        st.header("📊 Upload Queue")

        if uploaded_files:
            st.metric("Files in Queue", len(uploaded_files))

            total_size = sum(f.size for f in uploaded_files)
            size_mb = total_size / (1024 * 1024)
            st.metric("Total Size", f"{size_mb:.2f} MB")

            # File type distribution
            types = {}
            for file in uploaded_files:
                file_type = file.type or "Unknown"
                types[file_type] = types.get(file_type, 0) + 1

            st.subheader("File Types")
            for file_type, count in types.items():
                st.write(f"• {file_type}: {count}")

        else:
            st.info("No files in queue. Upload files to get started!")

    # Upload results section
    if st.session_state.upload_results:
        st.divider()
        st.header("📋 Upload Results")

        # Summary metrics
        total = len(st.session_state.upload_results)
        successful = sum(1 for r in st.session_state.upload_results if r['success'])
        failed = total - successful

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total", total)
        with col2:
            st.metric("Successful", successful, delta=successful, delta_color="normal")
        with col3:
            st.metric("Failed", failed, delta=-failed if failed > 0 else 0, delta_color="inverse")

        # Detailed results
        st.subheader("Details")

        # Tabs for success/failure
        tab1, tab2 = st.tabs(["✅ Successful", "❌ Failed"])

        with tab1:
            success_results = [r for r in st.session_state.upload_results if r['success']]
            if success_results:
                for result in success_results:
                    with st.container():
                        col1, col2, col3 = st.columns([3, 2, 1])
                        with col1:
                            icon = get_file_icon(result['type'])
                            st.write(f"{icon} **{result['filename']}**")
                        with col2:
                            size_mb = result['size'] / (1024 * 1024)
                            st.write(f"{size_mb:.2f} MB")
                        with col3:
                            st.write(f"ID: {result['file_id']}")
            else:
                st.info("No successful uploads yet")

        with tab2:
            failed_results = [r for r in st.session_state.upload_results if not r['success']]
            if failed_results:
                for result in failed_results:
                    with st.container():
                        col1, col2 = st.columns([3, 2])
                        with col1:
                            icon = get_file_icon(result['type'])
                            st.write(f"{icon} **{result['filename']}**")
                        with col2:
                            st.error(result['error'])
            else:
                st.success("No failed uploads!")

        # Clear results button
        if st.button("🧹 Clear Results"):
            st.session_state.upload_results = []
            st.rerun()

    # Tips section
    with st.expander("💡 Upload Tips"):
        st.markdown("""
        ### Quick Tips for Better File Management

        1. **Use Descriptive Names**: Name your files clearly before uploading
        2. **Add Tags**: Use tags to organize and find files easily
        3. **Add Descriptions**: Detailed descriptions help with search
        4. **Choose Right Folder**: Organize files in appropriate folders
        5. **Batch Upload**: Upload multiple files at once for efficiency
        6. **Check File Size**: Large files may take longer to upload
        7. **Supported Formats**: Check the sidebar for supported file types

        ### Security Notes

        - All files are scanned for security (if enabled)
        - Maximum file size: 100MB (configurable)
        - Duplicate files are detected automatically
        - Files are encrypted at rest (if enabled)
        """)

    # Recent uploads section
    st.divider()
    st.header("🕐 Recent Uploads")

    from modules.files import SearchIndexer
    search_indexer = SearchIndexer()

    recent = search_indexer.get_recent_files(
        session,
        st.session_state.user_id,
        limit=5
    )

    if recent:
        for file_info in recent:
            col1, col2, col3 = st.columns([3, 2, 2])
            with col1:
                icon = get_file_icon(file_info.get('mime_type'))
                st.write(f"{icon} {file_info['filename']}")
            with col2:
                size_mb = file_info['file_size'] / (1024 * 1024)
                st.write(f"{size_mb:.2f} MB")
            with col3:
                from datetime import datetime
                uploaded = file_info.get('uploaded_at')
                if uploaded:
                    st.write(uploaded.strftime("%Y-%m-%d %H:%M"))
    else:
        st.info("No recent uploads")

    session.close()


if __name__ == "__main__":
    main()
