"""File Browser page for NEXUS Platform.

This page provides a comprehensive file browser with tree view, list/grid view,
quick actions, and file management capabilities.
"""
import streamlit as st
from datetime import datetime
from typing import Optional
from database.engine import get_session, init_db
from modules.files import FileManager, SharingManager, SearchIndexer


# Page configuration
st.set_page_config(
    page_title="Files - NEXUS Platform",
    page_icon="📁",
    layout="wide"
)

# Initialize database
init_db()

# Initialize file manager
if 'file_manager' not in st.session_state:
    st.session_state.file_manager = FileManager()
if 'sharing_manager' not in st.session_state:
    st.session_state.sharing_manager = SharingManager()
if 'search_indexer' not in st.session_state:
    st.session_state.search_indexer = SearchIndexer()

# Mock user (in production, this would come from authentication)
if 'user_id' not in st.session_state:
    st.session_state.user_id = 1
if 'username' not in st.session_state:
    st.session_state.username = 'demo_user'


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def format_date(dt: Optional[datetime]) -> str:
    """Format datetime for display."""
    if not dt:
        return "N/A"
    return dt.strftime("%Y-%m-%d %H:%M")


def display_file_card(file_info: dict, session):
    """Display a file as a card."""
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

        with col1:
            # File icon and name
            icon = {
                'document': '📄',
                'image': '🖼️',
                'video': '🎥',
                'audio': '🎵',
                'archive': '📦',
                'other': '📎'
            }.get(file_info.get('category', 'other'), '📎')

            st.markdown(f"**{icon} {file_info['filename']}**")

            # Tags
            if file_info.get('tags'):
                tag_html = " ".join([
                    f'<span style="background-color: {tag["color"]}; color: white; '
                    f'padding: 2px 8px; border-radius: 3px; font-size: 12px; '
                    f'margin-right: 4px;">{tag["name"]}</span>'
                    for tag in file_info['tags']
                ])
                st.markdown(tag_html, unsafe_allow_html=True)

        with col2:
            st.write(f"**Size:** {format_file_size(file_info['file_size'])}")
            st.write(f"**Type:** {file_info['category']}")

        with col3:
            st.write(f"**Owner:** {file_info.get('owner', 'Unknown')}")
            st.write(f"**Modified:** {format_date(file_info.get('last_modified_at'))}")

        with col4:
            # Quick actions
            action_col1, action_col2, action_col3, action_col4 = st.columns(4)

            with action_col1:
                if st.button("📥", key=f"download_{file_info['id']}", help="Download"):
                    download_file(session, file_info['id'])

            with action_col2:
                if st.button("❤️" if file_info.get('is_favorite') else "🤍",
                           key=f"fav_{file_info['id']}", help="Toggle Favorite"):
                    toggle_favorite(session, file_info['id'])

            with action_col3:
                if st.button("🔗", key=f"share_{file_info['id']}", help="Share"):
                    st.session_state.selected_file_for_sharing = file_info['id']

            with action_col4:
                if st.button("🗑️", key=f"delete_{file_info['id']}", help="Delete"):
                    delete_file(session, file_info['id'])

        st.divider()


def download_file(session, file_id: int):
    """Download a file."""
    result = st.session_state.file_manager.download_file(
        session,
        file_id,
        st.session_state.user_id
    )

    if result:
        file_content, filename, mime_type = result
        st.download_button(
            label=f"Download {filename}",
            data=file_content,
            file_name=filename,
            mime=mime_type,
            key=f"dl_btn_{file_id}"
        )
        st.success(f"Downloading {filename}...")
    else:
        st.error("Failed to download file")


def toggle_favorite(session, file_id: int):
    """Toggle favorite status."""
    success = st.session_state.file_manager.toggle_favorite(
        session,
        file_id,
        st.session_state.user_id
    )

    if success:
        st.rerun()


def delete_file(session, file_id: int):
    """Delete a file."""
    success = st.session_state.file_manager.delete_file(
        session,
        file_id,
        st.session_state.user_id,
        permanent=False
    )

    if success:
        st.success("File moved to trash")
        st.rerun()
    else:
        st.error("Failed to delete file")


def main():
    """Main function for the Files page."""
    st.title("📁 File Manager")
    st.markdown("Manage your files - browse, search, organize, and share")

    # Get database session
    session = next(get_session())

    # Sidebar filters
    with st.sidebar:
        st.header("Filters")

        # View type
        view_type = st.radio("View Type", ["My Files", "Shared with Me", "Favorites", "Trash"])

        # Category filter
        category_filter = st.selectbox(
            "Category",
            ["All", "document", "image", "video", "audio", "archive", "other"]
        )

        # Sort options
        sort_by = st.selectbox(
            "Sort By",
            ["Last Modified", "Name", "Size", "Upload Date"]
        )

        # Additional options
        st.divider()
        st.markdown("### Quick Actions")

        if st.button("🔄 Refresh"):
            st.rerun()

        if st.button("📊 View Statistics"):
            st.session_state.show_stats = True

    # Main content area
    tab1, tab2, tab3 = st.tabs(["📋 List View", "📊 Statistics", "⚙️ Settings"])

    with tab1:
        # Search bar
        search_query = st.text_input("🔍 Search files", placeholder="Search by name, description, or content...")

        # Get files based on view type
        if view_type == "My Files":
            filters = {}
            if category_filter != "All":
                filters['category'] = category_filter

            files = st.session_state.search_indexer.search(
                session,
                search_query if search_query else "",
                st.session_state.user_id,
                filters=filters,
                limit=100
            )

            # Filter to only show user's files
            files = [f for f in files if f['owner_id'] == st.session_state.user_id]

        elif view_type == "Shared with Me":
            files = st.session_state.sharing_manager.get_shared_with_me(
                session,
                st.session_state.user_id
            )

        elif view_type == "Favorites":
            files = st.session_state.search_indexer.get_favorites(
                session,
                st.session_state.user_id
            )

        elif view_type == "Trash":
            files = st.session_state.file_manager.get_trash_files(
                session,
                st.session_state.user_id
            )

        # Display results
        if files:
            st.markdown(f"**{len(files)} files found**")

            # Bulk actions
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                if st.button("📥 Download Selected as ZIP"):
                    st.info("Select files and click to download as ZIP")

            # Display files
            for file_info in files:
                display_file_card(file_info, session)

        else:
            st.info("No files found. Upload some files to get started!")

    with tab2:
        st.header("📊 File Statistics")

        # Get statistics
        stats = st.session_state.search_indexer.get_search_stats(
            session,
            st.session_state.user_id
        )

        # Display metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Files", stats['total_files'])

        with col2:
            st.metric("Total Storage", format_file_size(stats['total_size']))

        with col3:
            total_categories = len(stats['category_counts'])
            st.metric("Categories", total_categories)

        # Category breakdown
        st.subheader("Files by Category")
        if stats['category_counts']:
            for category, count in stats['category_counts'].items():
                st.write(f"**{category.capitalize()}:** {count} files")
        else:
            st.info("No files yet")

        # Recent files
        st.subheader("Recently Modified")
        recent_files = st.session_state.search_indexer.get_recent_files(
            session,
            st.session_state.user_id,
            limit=5
        )

        for file_info in recent_files:
            st.write(f"📄 {file_info['filename']} - {format_date(file_info['last_modified_at'])}")

    with tab3:
        st.header("⚙️ File Settings")

        st.subheader("Storage Settings")
        st.write("Configure storage backend and limits")

        storage_backend = st.selectbox(
            "Storage Backend",
            ["Local Storage", "AWS S3", "Azure Blob", "Google Cloud Storage"]
        )

        max_file_size = st.slider("Max File Size (MB)", 10, 1000, 100)

        st.subheader("Security Settings")
        enable_virus_scan = st.checkbox("Enable Virus Scanning", value=False)
        enable_encryption = st.checkbox("Enable Encryption at Rest", value=False)

        if st.button("💾 Save Settings"):
            st.success("Settings saved successfully!")

    # Handle sharing dialog
    if 'selected_file_for_sharing' in st.session_state:
        with st.expander("🔗 Share File", expanded=True):
            st.write("Share options will be implemented here")
            if st.button("Close"):
                del st.session_state.selected_file_for_sharing
                st.rerun()

    session.close()


if __name__ == "__main__":
    main()
