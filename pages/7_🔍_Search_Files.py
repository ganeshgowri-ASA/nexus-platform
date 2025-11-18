"""File Search page for NEXUS Platform.

This page provides advanced file search with full-text search, filters,
faceted search, and result previews.
"""
import streamlit as st
from datetime import datetime, timedelta
from database.engine import get_session, init_db
from modules.files import SearchIndexer, FileManager


# Page configuration
st.set_page_config(
    page_title="Search Files - NEXUS Platform",
    page_icon="🔍",
    layout="wide"
)

# Initialize database
init_db()

# Initialize managers
if 'search_indexer' not in st.session_state:
    st.session_state.search_indexer = SearchIndexer()
if 'file_manager' not in st.session_state:
    st.session_state.file_manager = FileManager()

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


def format_date(dt: datetime) -> str:
    """Format datetime for display."""
    if not dt:
        return "N/A"
    return dt.strftime("%Y-%m-%d %H:%M")


def get_file_icon(category: str) -> str:
    """Get icon for file category."""
    icons = {
        'document': '📄',
        'image': '🖼️',
        'video': '🎥',
        'audio': '🎵',
        'archive': '📦',
        'other': '📎'
    }
    return icons.get(category, '📎')


def display_search_result(file_info: dict, session, show_preview: bool = True):
    """Display a search result."""
    with st.container():
        col1, col2, col3 = st.columns([3, 2, 1])

        with col1:
            icon = get_file_icon(file_info.get('category', 'other'))
            st.markdown(f"### {icon} {file_info['filename']}")

            # Description
            if file_info.get('description'):
                st.write(file_info['description'])

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
            st.write(f"**Owner:** {file_info.get('owner', 'Unknown')}")
            st.write(f"**Modified:** {format_date(file_info.get('last_modified_at'))}")

        with col3:
            # Quick actions
            if st.button("📥 Download", key=f"dl_{file_info['id']}"):
                download_file(session, file_info['id'])

            if st.button("ℹ️ Details", key=f"info_{file_info['id']}"):
                st.session_state.selected_file = file_info['id']

            # Stats
            st.write(f"👁️ {file_info.get('view_count', 0)}")
            st.write(f"📥 {file_info.get('download_count', 0)}")

        # Preview section
        if show_preview and file_info.get('thumbnail_path'):
            st.image(file_info['thumbnail_path'], width=200)

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
            key=f"dl_btn_{file_id}_main"
        )
    else:
        st.error("Failed to download file")


def main():
    """Main function for the Search Files page."""
    st.title("🔍 Search Files")
    st.markdown("Advanced file search with filters and full-text search")

    # Get database session
    session = next(get_session())

    # Sidebar - Advanced filters
    with st.sidebar:
        st.header("🔧 Advanced Filters")

        # Category filter
        st.subheader("📂 Category")
        categories = st.multiselect(
            "Select Categories",
            ["document", "image", "video", "audio", "archive", "other"],
            default=[]
        )

        # Date range filter
        st.subheader("📅 Date Range")
        date_option = st.selectbox(
            "Upload Date",
            ["Any Time", "Today", "This Week", "This Month", "Custom Range"]
        )

        start_date = None
        end_date = None

        if date_option == "Today":
            start_date = datetime.now().replace(hour=0, minute=0, second=0)
            end_date = datetime.now()
        elif date_option == "This Week":
            start_date = datetime.now() - timedelta(days=7)
            end_date = datetime.now()
        elif date_option == "This Month":
            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now()
        elif date_option == "Custom Range":
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("From")
            with col2:
                end_date = st.date_input("To")

        # Size filter
        st.subheader("📏 File Size")
        size_option = st.selectbox(
            "Size Range",
            ["Any Size", "< 1 MB", "1-10 MB", "10-100 MB", "> 100 MB", "Custom"]
        )

        min_size = None
        max_size = None

        if size_option == "< 1 MB":
            max_size = 1024 * 1024
        elif size_option == "1-10 MB":
            min_size = 1024 * 1024
            max_size = 10 * 1024 * 1024
        elif size_option == "10-100 MB":
            min_size = 10 * 1024 * 1024
            max_size = 100 * 1024 * 1024
        elif size_option == "> 100 MB":
            min_size = 100 * 1024 * 1024
        elif size_option == "Custom":
            min_size_mb = st.number_input("Min Size (MB)", min_value=0.0, value=0.0)
            max_size_mb = st.number_input("Max Size (MB)", min_value=0.0, value=100.0)
            min_size = int(min_size_mb * 1024 * 1024) if min_size_mb > 0 else None
            max_size = int(max_size_mb * 1024 * 1024) if max_size_mb > 0 else None

        # Tags filter
        st.subheader("🏷️ Tags")
        tags_input = st.text_input(
            "Search by Tags",
            placeholder="work, important, project",
            help="Comma-separated tags"
        )
        tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()]

        # Owner filter
        st.subheader("👤 Owner")
        owner_filter = st.selectbox(
            "Files by",
            ["All Users", "My Files Only", "Shared with Me"]
        )

        # Favorites
        st.subheader("⭐ Special")
        favorites_only = st.checkbox("Favorites Only")

        # Clear filters button
        st.divider()
        if st.button("🗑️ Clear All Filters"):
            st.rerun()

    # Main search area
    st.header("🔍 Search")

    # Search input with autocomplete support
    search_query = st.text_input(
        "Search files by name, description, or content",
        placeholder="Enter search terms...",
        help="Search in filename, description, and extracted text content"
    )

    # Search options
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        search_in = st.multiselect(
            "Search in:",
            ["Filename", "Description", "Content", "Tags"],
            default=["Filename", "Content"]
        )

    with col2:
        sort_by = st.selectbox(
            "Sort by:",
            ["Relevance", "Date (Newest)", "Date (Oldest)", "Name (A-Z)", "Name (Z-A)", "Size (Large)", "Size (Small)"]
        )

    with col3:
        results_per_page = st.selectbox(
            "Results per page:",
            [10, 25, 50, 100],
            index=1
        )

    # Build filters dictionary
    filters = {}

    if categories:
        # For single category (search expects single value)
        if len(categories) == 1:
            filters['category'] = categories[0]

    if start_date:
        filters['start_date'] = start_date
    if end_date:
        filters['end_date'] = end_date
    if min_size:
        filters['min_size'] = min_size
    if max_size:
        filters['max_size'] = max_size

    if owner_filter == "My Files Only":
        filters['owner_id'] = st.session_state.user_id

    if favorites_only:
        filters['is_favorite'] = True

    if tags:
        filters['tags'] = tags

    # Perform search
    search_button = st.button("🔍 Search", type="primary")

    # Auto-search if query is provided or show recent files
    if search_query or search_button or filters:
        with st.spinner("Searching..."):
            results = st.session_state.search_indexer.search(
                session,
                search_query or "",
                st.session_state.user_id,
                filters=filters,
                limit=results_per_page
            )

        # Display results
        st.divider()
        st.header(f"📊 Search Results ({len(results)})")

        if results:
            # Results summary
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Files Found", len(results))

            with col2:
                total_size = sum(r['file_size'] for r in results)
                st.metric("Total Size", format_file_size(total_size))

            with col3:
                categories_found = len(set(r['category'] for r in results))
                st.metric("Categories", categories_found)

            # Category facets
            st.subheader("Filter by Category")
            category_counts = {}
            for result in results:
                cat = result.get('category', 'other')
                category_counts[cat] = category_counts.get(cat, 0) + 1

            facet_cols = st.columns(len(category_counts) or 1)
            for idx, (cat, count) in enumerate(category_counts.items()):
                with facet_cols[idx]:
                    icon = get_file_icon(cat)
                    st.button(f"{icon} {cat.capitalize()} ({count})", key=f"facet_{cat}")

            st.divider()

            # Display results
            show_previews = st.checkbox("Show Previews", value=False)

            for result in results:
                display_search_result(result, session, show_preview=show_previews)

            # Pagination (simplified)
            if len(results) >= results_per_page:
                st.info("More results available. Use filters to narrow down your search.")

        else:
            st.info("No files found matching your search criteria. Try different search terms or filters.")

            # Suggestions
            st.subheader("💡 Suggestions")
            st.markdown("""
            - Try different search terms
            - Remove some filters
            - Check spelling
            - Use broader categories
            - Search in all fields
            """)

    else:
        # Show popular and recent files when no search
        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            st.header("🔥 Popular Files")
            popular = st.session_state.search_indexer.get_popular_files(
                session,
                st.session_state.user_id,
                limit=5
            )

            if popular:
                for file_info in popular:
                    icon = get_file_icon(file_info.get('category', 'other'))
                    st.write(f"{icon} **{file_info['filename']}**")
                    st.write(f"   👁️ {file_info.get('view_count', 0)} views | "
                           f"📥 {file_info.get('download_count', 0)} downloads")
            else:
                st.info("No popular files yet")

        with col2:
            st.header("🕐 Recent Files")
            recent = st.session_state.search_indexer.get_recent_files(
                session,
                st.session_state.user_id,
                limit=5
            )

            if recent:
                for file_info in recent:
                    icon = get_file_icon(file_info.get('category', 'other'))
                    st.write(f"{icon} **{file_info['filename']}**")
                    st.write(f"   📅 {format_date(file_info.get('last_modified_at'))}")
            else:
                st.info("No recent files")

    # Search tips
    with st.expander("💡 Search Tips"):
        st.markdown("""
        ### How to Search Effectively

        **Basic Search:**
        - Enter any keyword to search in filenames and content
        - Search is case-insensitive

        **Advanced Filters:**
        - Use category filters to narrow by file type
        - Set date ranges for time-based search
        - Filter by file size ranges
        - Search by tags for organized results

        **Search Scope:**
        - **Filename**: Searches only in file names
        - **Description**: Searches in file descriptions
        - **Content**: Full-text search in file contents
        - **Tags**: Searches in assigned tags

        **Examples:**
        - `project report` - Find files with these words
        - Filter by "document" category + "This Week" - Recent documents
        - Use tags: `work, important` - Files with these tags
        - Size filter + Category - Large video files, etc.

        **Tips:**
        - More filters = more specific results
        - Use tags for better organization
        - Favorites for quick access
        - Check "Show Previews" for visual files
        """)

    # File details modal
    if 'selected_file' in st.session_state:
        with st.expander("📄 File Details", expanded=True):
            file_info = st.session_state.file_manager.get_file_info(
                session,
                st.session_state.selected_file,
                st.session_state.user_id
            )

            if file_info:
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Basic Information")
                    st.write(f"**Filename:** {file_info['filename']}")
                    st.write(f"**Original Name:** {file_info['original_filename']}")
                    st.write(f"**Size:** {format_file_size(file_info['file_size'])}")
                    st.write(f"**Type:** {file_info['mime_type']}")
                    st.write(f"**Category:** {file_info['category']}")

                with col2:
                    st.subheader("Metadata")
                    st.write(f"**Owner:** {file_info['owner']}")
                    st.write(f"**Uploaded:** {format_date(file_info['uploaded_at'])}")
                    st.write(f"**Modified:** {format_date(file_info['last_modified_at'])}")
                    st.write(f"**Views:** {file_info['view_count']}")
                    st.write(f"**Downloads:** {file_info['download_count']}")

                if file_info.get('description'):
                    st.subheader("Description")
                    st.write(file_info['description'])

                if file_info.get('tags'):
                    st.subheader("Tags")
                    tags_str = ", ".join([tag['name'] for tag in file_info['tags']])
                    st.write(tags_str)

                if st.button("Close Details"):
                    del st.session_state.selected_file
                    st.rerun()

    session.close()


if __name__ == "__main__":
    main()
