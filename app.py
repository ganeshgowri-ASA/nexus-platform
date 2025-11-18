"""NEXUS Platform - Main Application Entry Point

NEXUS: Unified AI-powered productivity platform with 24 integrated modules
including comprehensive file management system.
"""
import streamlit as st
from database.engine import init_db


# Page configuration
st.set_page_config(
    page_title="NEXUS Platform",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
init_db()


def main():
    """Main application page."""
    st.title("🚀 NEXUS Platform")
    st.markdown("""
    ### Welcome to NEXUS - Your Unified Productivity Platform

    NEXUS is a comprehensive platform integrating 24 modules for enhanced productivity.
    """)

    # Feature cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        #### 📁 File Management
        - Upload & organize files
        - Version control
        - Sharing & permissions
        - Full-text search
        - Cloud-ready storage

        [Go to Files →](pages/5_📁_Files.py)
        """)

    with col2:
        st.markdown("""
        #### ☁️ File Upload
        - Drag & drop interface
        - Multi-file upload
        - Progress tracking
        - Auto-categorization
        - Tag & organize

        [Go to Upload →](pages/6_☁️_Upload.py)
        """)

    with col3:
        st.markdown("""
        #### 🔍 Advanced Search
        - Full-text search
        - Advanced filters
        - Tag-based search
        - Recent & popular files
        - Smart suggestions

        [Go to Search →](pages/7_🔍_Search_Files.py)
        """)

    st.divider()

    # Statistics section
    st.header("📊 Platform Overview")

    # Mock statistics (in production, fetch from database)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Files", "0", help="Total files uploaded")

    with col2:
        st.metric("Storage Used", "0 MB", help="Total storage used")

    with col3:
        st.metric("Active Users", "1", help="Currently active users")

    with col4:
        st.metric("Modules", "3/24", help="Implemented modules")

    st.divider()

    # Quick start guide
    st.header("🚀 Quick Start Guide")

    with st.expander("1. Upload Your First File"):
        st.markdown("""
        1. Navigate to **☁️ Upload** page
        2. Drag and drop files or click to browse
        3. Add tags and description (optional)
        4. Click **Upload All**
        5. Files are automatically processed and indexed
        """)

    with st.expander("2. Organize Your Files"):
        st.markdown("""
        1. Go to **📁 Files** page
        2. Use folders to organize files
        3. Add tags for easy categorization
        4. Mark favorites for quick access
        5. Use the trash for deleted files
        """)

    with st.expander("3. Search and Find Files"):
        st.markdown("""
        1. Visit **🔍 Search Files** page
        2. Enter search terms (searches name and content)
        3. Apply filters (category, date, size, tags)
        4. Sort results by various criteria
        5. View file details and download
        """)

    with st.expander("4. Share Files"):
        st.markdown("""
        1. Select a file in **📁 Files**
        2. Click share button
        3. Choose users or create public link
        4. Set permissions (viewer, editor, etc.)
        5. Optional: password protect and set expiration
        """)

    st.divider()

    # Features showcase
    st.header("✨ Key Features")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📂 File Management",
        "🔐 Security",
        "🔄 Version Control",
        "🔍 Search"
    ])

    with tab1:
        st.markdown("""
        ### Comprehensive File Management

        - **Multi-format Support**: Documents, images, videos, audio, archives
        - **Smart Organization**: Folders, tags, categories, favorites
        - **Bulk Operations**: Upload, download, move, delete multiple files
        - **Thumbnails**: Auto-generated previews for images and PDFs
        - **Metadata**: Track size, type, owner, dates, download counts
        - **Trash**: 30-day retention for deleted files
        """)

    with tab2:
        st.markdown("""
        ### Enterprise-grade Security

        - **Access Control**: Owner, editor, commenter, viewer permissions
        - **File Validation**: Type, size, and content validation
        - **Virus Scanning**: ClamAV integration ready
        - **Encryption**: At-rest encryption support
        - **Audit Logs**: Track all file access and modifications
        - **Public Links**: Password-protected, expiring share links
        """)

    with tab3:
        st.markdown("""
        ### Built-in Version Control

        - **Automatic Versioning**: Track file changes over time
        - **Version History**: View and compare all versions
        - **Easy Restore**: Rollback to any previous version
        - **Change Tracking**: See who modified what and when
        - **Storage Optimization**: Configurable version limits
        - **Diff Support**: Compare versions side-by-side
        """)

    with tab4:
        st.markdown("""
        ### Powerful Search Capabilities

        - **Full-text Search**: Search inside documents
        - **Smart Filters**: Category, date, size, owner, tags
        - **Faceted Search**: Quick category filtering
        - **Recent Files**: Track recently accessed files
        - **Popular Files**: See most downloaded files
        - **Tag Search**: Find files by tags
        """)

    st.divider()

    # Supported file types
    st.header("📋 Supported File Types")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **Documents** (max 100MB)
        - Word: .doc, .docx
        - Excel: .xls, .xlsx, .csv
        - PowerPoint: .ppt, .pptx
        - PDF: .pdf
        - Text: .txt, .md, .rtf
        - Data: .json, .xml, .yaml
        """)

    with col2:
        st.markdown("""
        **Media** (max 500MB)
        - Images: .jpg, .png, .gif, .svg
        - Videos: .mp4, .avi, .mov
        - Audio: .mp3, .wav, .ogg

        **Archives** (max 1GB)
        - .zip, .tar, .gz, .rar
        """)

    with col3:
        st.markdown("""
        **Processing Features**
        - Text extraction from PDFs
        - OCR from images (optional)
        - Thumbnail generation
        - Format conversion
        - Metadata extraction
        """)

    st.divider()

    # Footer
    st.markdown("""
    ---
    **NEXUS Platform** - Phase 1 Session 5: Complete File Management System

    Built with Streamlit, SQLAlchemy, and Claude AI
    """)


if __name__ == "__main__":
    main()
