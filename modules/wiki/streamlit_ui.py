"""
NEXUS Wiki System - Streamlit UI

Complete wiki interface with modern design including:
- Page browser with search and filters
- Rich text editor with markdown preview
- Page viewer with table of contents
- Version history with diff visualization
- Category browser with tree view
- Tag cloud and tag browser
- Comment system interface
- Analytics dashboard
- Settings and configuration

Author: NEXUS Platform Team
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import re
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database import get_db
from modules.wiki import (
    get_page_manager, get_editor_service, get_versioning_service,
    get_search_service, get_ai_assistant
)
from modules.wiki.models import WikiPage, WikiCategory, WikiTag
from modules.wiki.wiki_types import (
    PageStatus, ContentFormat, PageCreateRequest, PageUpdateRequest,
    PageSearchRequest
)
from modules.wiki.categories import CategoryService
from modules.wiki.comments import CommentService
from modules.wiki.analytics import AnalyticsService
from modules.wiki.attachments import AttachmentService
from app.utils import get_logger

logger = get_logger(__name__)


# ============================================================================
# CUSTOM CSS AND STYLING
# ============================================================================

def apply_wiki_css() -> None:
    """Apply custom CSS for wiki interface."""
    st.markdown("""
        <style>
        /* Main wiki container */
        .wiki-container {
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin: 10px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        /* Wiki header */
        .wiki-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }

        .wiki-header h1 {
            color: white !important;
            margin: 0;
        }

        /* Page card */
        .page-card {
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            transition: all 0.3s ease;
            cursor: pointer;
        }

        .page-card:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transform: translateY(-2px);
        }

        .page-title {
            font-size: 1.2em;
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
        }

        .page-meta {
            font-size: 0.9em;
            color: #666;
        }

        /* Tag styling */
        .wiki-tag {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 0.85em;
            margin: 2px;
            background: #667eea;
            color: white;
        }

        /* Category tree */
        .category-item {
            padding: 8px 12px;
            margin: 4px 0;
            border-radius: 5px;
            cursor: pointer;
            transition: background 0.2s;
        }

        .category-item:hover {
            background: #f0f0f0;
        }

        /* Editor styles */
        .editor-toolbar {
            background: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
        }

        /* Version diff */
        .diff-added {
            background-color: #d4edda;
            color: #155724;
            padding: 2px 4px;
        }

        .diff-removed {
            background-color: #f8d7da;
            color: #721c24;
            padding: 2px 4px;
            text-decoration: line-through;
        }

        /* TOC styles */
        .toc-container {
            background: #f8f9fa;
            border-left: 3px solid #667eea;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }

        .toc-item {
            padding: 5px 0;
            cursor: pointer;
            color: #495057;
        }

        .toc-item:hover {
            color: #667eea;
        }

        /* Comment styles */
        .comment-card {
            background: #f8f9fa;
            border-left: 3px solid #667eea;
            padding: 12px;
            margin: 10px 0;
            border-radius: 5px;
        }

        .comment-author {
            font-weight: 600;
            color: #333;
        }

        .comment-date {
            font-size: 0.85em;
            color: #666;
        }

        /* Analytics cards */
        .analytics-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }

        .analytics-value {
            font-size: 2.5em;
            font-weight: 700;
        }

        .analytics-label {
            font-size: 1em;
            opacity: 0.9;
        }

        /* Sidebar navigation */
        .nav-item {
            padding: 10px 15px;
            margin: 5px 0;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .nav-item:hover {
            background: rgba(255,255,255,0.1);
        }

        .nav-item.active {
            background: rgba(255,255,255,0.2);
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)


# ============================================================================
# SESSION STATE MANAGEMENT
# ============================================================================

def init_session_state() -> None:
    """Initialize session state variables."""
    if 'wiki_view' not in st.session_state:
        st.session_state.wiki_view = 'home'
    if 'current_page_id' not in st.session_state:
        st.session_state.current_page_id = None
    if 'selected_category' not in st.session_state:
        st.session_state.selected_category = None
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ''
    if 'editor_content' not in st.session_state:
        st.session_state.editor_content = ''
    if 'editing_page_id' not in st.session_state:
        st.session_state.editing_page_id = None
    if 'current_user_id' not in st.session_state:
        st.session_state.current_user_id = 1  # Default user for demo


# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================

def render_sidebar() -> None:
    """Render sidebar navigation."""
    with st.sidebar:
        st.markdown("## 📚 Wiki Navigation")

        # Main navigation
        nav_items = [
            ('home', '🏠 Home', 'home'),
            ('browse', '📖 Browse Pages', 'browse'),
            ('create', '✏️ Create Page', 'create'),
            ('categories', '📂 Categories', 'categories'),
            ('tags', '🏷️ Tags', 'tags'),
            ('search', '🔍 Search', 'search'),
            ('recent', '🕒 Recent Changes', 'recent'),
            ('analytics', '📊 Analytics', 'analytics'),
            ('settings', '⚙️ Settings', 'settings'),
        ]

        for key, label, view in nav_items:
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                st.session_state.wiki_view = view
                st.rerun()

        st.markdown("---")

        # Quick stats
        st.markdown("### 📊 Quick Stats")
        db = next(get_db())
        try:
            from modules.wiki.pages import PageManager
            pm = PageManager(db)

            total_pages = db.query(WikiPage).filter(
                WikiPage.is_deleted == False
            ).count()

            published_pages = db.query(WikiPage).filter(
                WikiPage.is_deleted == False,
                WikiPage.status == PageStatus.PUBLISHED
            ).count()

            total_categories = db.query(WikiCategory).count()

            st.metric("Total Pages", total_pages)
            st.metric("Published", published_pages)
            st.metric("Categories", total_categories)
        except Exception as e:
            logger.error(f"Error loading stats: {e}")
            st.error("Failed to load stats")
        finally:
            db.close()

        st.markdown("---")

        # User info
        st.markdown("### 👤 User")
        st.markdown(f"**User ID:** {st.session_state.current_user_id}")


# ============================================================================
# HOME VIEW
# ============================================================================

def render_home() -> None:
    """Render wiki home page."""
    st.markdown('<div class="wiki-header">', unsafe_allow_html=True)
    st.markdown("# 📚 NEXUS Wiki")
    st.markdown("*Your central knowledge repository*")
    st.markdown('</div>', unsafe_allow_html=True)

    # Welcome section
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("## Welcome to the Wiki")
        st.markdown("""
        The NEXUS Wiki is your comprehensive knowledge management system with:

        - **Rich Text Editing** - Create beautiful pages with markdown support
        - **Version Control** - Track all changes with complete history
        - **Real-time Collaboration** - Work together seamlessly
        - **Advanced Search** - Find anything instantly
        - **AI-Powered Assistance** - Get smart suggestions and insights
        - **Analytics** - Understand how your wiki is being used
        """)

    with col2:
        st.markdown("## Quick Actions")
        if st.button("📝 Create New Page", use_container_width=True):
            st.session_state.wiki_view = 'create'
            st.rerun()
        if st.button("📖 Browse Pages", use_container_width=True):
            st.session_state.wiki_view = 'browse'
            st.rerun()
        if st.button("🔍 Search Wiki", use_container_width=True):
            st.session_state.wiki_view = 'search'
            st.rerun()

    st.markdown("---")

    # Recent pages
    st.markdown("## 📄 Recent Pages")
    db = next(get_db())
    try:
        recent_pages = db.query(WikiPage).filter(
            WikiPage.is_deleted == False,
            WikiPage.status == PageStatus.PUBLISHED
        ).order_by(WikiPage.updated_at.desc()).limit(5).all()

        for page in recent_pages:
            render_page_card(page)
    except Exception as e:
        logger.error(f"Error loading recent pages: {e}")
        st.error("Failed to load recent pages")
    finally:
        db.close()


# ============================================================================
# BROWSE PAGES VIEW
# ============================================================================

def render_browse() -> None:
    """Render page browser with search and filters."""
    st.markdown("# 📖 Browse Pages")

    # Filters
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        status_filter = st.selectbox(
            "Status",
            ["All", "Published", "Draft", "Archived"],
            key="browse_status_filter"
        )

    with col2:
        db = next(get_db())
        categories = db.query(WikiCategory).all()
        category_options = ["All"] + [cat.name for cat in categories]
        category_filter = st.selectbox(
            "Category",
            category_options,
            key="browse_category_filter"
        )
        db.close()

    with col3:
        sort_by = st.selectbox(
            "Sort By",
            ["Updated (Newest)", "Updated (Oldest)", "Title (A-Z)", "Title (Z-A)", "Views"],
            key="browse_sort"
        )

    with col4:
        view_mode = st.selectbox(
            "View Mode",
            ["Cards", "List", "Tree"],
            key="browse_view_mode"
        )

    # Search
    search_query = st.text_input("🔍 Search pages...", key="browse_search")

    st.markdown("---")

    # Load and filter pages
    db = next(get_db())
    try:
        query = db.query(WikiPage).filter(WikiPage.is_deleted == False)

        # Apply status filter
        if status_filter != "All":
            status_map = {
                "Published": PageStatus.PUBLISHED,
                "Draft": PageStatus.DRAFT,
                "Archived": PageStatus.ARCHIVED
            }
            query = query.filter(WikiPage.status == status_map[status_filter])

        # Apply category filter
        if category_filter != "All":
            category = db.query(WikiCategory).filter(
                WikiCategory.name == category_filter
            ).first()
            if category:
                query = query.filter(WikiPage.category_id == category.id)

        # Apply search
        if search_query:
            query = query.filter(
                WikiPage.title.ilike(f"%{search_query}%") |
                WikiPage.content.ilike(f"%{search_query}%")
            )

        # Apply sorting
        if sort_by == "Updated (Newest)":
            query = query.order_by(WikiPage.updated_at.desc())
        elif sort_by == "Updated (Oldest)":
            query = query.order_by(WikiPage.updated_at.asc())
        elif sort_by == "Title (A-Z)":
            query = query.order_by(WikiPage.title.asc())
        elif sort_by == "Title (Z-A)":
            query = query.order_by(WikiPage.title.desc())
        elif sort_by == "Views":
            query = query.order_by(WikiPage.view_count.desc())

        pages = query.all()

        # Display pages
        st.markdown(f"**Found {len(pages)} pages**")

        if view_mode == "Cards":
            for page in pages:
                render_page_card(page)
        elif view_mode == "List":
            for page in pages:
                render_page_list_item(page)
        else:  # Tree
            render_page_tree(pages)

    except Exception as e:
        logger.error(f"Error browsing pages: {e}")
        st.error("Failed to load pages")
    finally:
        db.close()


# ============================================================================
# CREATE/EDIT PAGE VIEW
# ============================================================================

def render_create_edit_page() -> None:
    """Render page creation/editing interface."""
    is_editing = st.session_state.editing_page_id is not None

    if is_editing:
        st.markdown("# ✏️ Edit Page")
        db = next(get_db())
        page = db.query(WikiPage).get(st.session_state.editing_page_id)
        db.close()
    else:
        st.markdown("# ✏️ Create New Page")
        page = None

    # Editor toolbar
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        if st.button("💾 Save", type="primary"):
            save_page()

    with col2:
        if st.button("👁️ Preview"):
            st.session_state.show_preview = not st.session_state.get('show_preview', False)

    with col3:
        if st.button("🤖 AI Assist"):
            show_ai_assistant()

    with col4:
        if st.button("❌ Cancel"):
            st.session_state.wiki_view = 'browse'
            st.session_state.editing_page_id = None
            st.rerun()

    st.markdown("---")

    # Editor form
    col1, col2 = st.columns([2, 1])

    with col1:
        # Title
        title = st.text_input(
            "Page Title",
            value=page.title if page else "",
            key="edit_title"
        )

        # Content editor
        content_format = st.selectbox(
            "Content Format",
            [ContentFormat.MARKDOWN, ContentFormat.HTML, ContentFormat.RICH_TEXT],
            index=0 if not page else [ContentFormat.MARKDOWN, ContentFormat.HTML, ContentFormat.RICH_TEXT].index(page.content_format),
            key="edit_format"
        )

        content = st.text_area(
            "Content",
            value=page.content if page else st.session_state.get('editor_content', ''),
            height=400,
            key="edit_content"
        )

        # Summary
        summary = st.text_area(
            "Summary (optional)",
            value=page.summary if page else "",
            height=100,
            key="edit_summary"
        )

    with col2:
        # Metadata
        st.markdown("### Metadata")

        db = next(get_db())

        # Category
        categories = db.query(WikiCategory).all()
        category_options = ["None"] + [cat.name for cat in categories]
        category_idx = 0
        if page and page.category_id:
            for i, cat in enumerate(categories):
                if cat.id == page.category_id:
                    category_idx = i + 1
                    break

        category = st.selectbox(
            "Category",
            category_options,
            index=category_idx,
            key="edit_category"
        )

        # Tags
        all_tags = db.query(WikiTag).all()
        tag_options = [tag.name for tag in all_tags]
        current_tags = [tag.name for tag in page.tags] if page else []
        tags = st.multiselect(
            "Tags",
            tag_options,
            default=current_tags,
            key="edit_tags"
        )

        # Status
        status = st.selectbox(
            "Status",
            [PageStatus.DRAFT, PageStatus.PUBLISHED, PageStatus.ARCHIVED],
            index=0 if not page else [PageStatus.DRAFT, PageStatus.PUBLISHED, PageStatus.ARCHIVED].index(page.status),
            key="edit_status"
        )

        # Namespace
        namespace = st.text_input(
            "Namespace (optional)",
            value=page.namespace if page else "",
            key="edit_namespace"
        )

        db.close()

        st.markdown("---")

        # Change summary (for edits)
        if is_editing:
            change_summary = st.text_area(
                "Change Summary",
                placeholder="Describe your changes...",
                key="edit_change_summary"
            )

    # Preview
    if st.session_state.get('show_preview', False):
        st.markdown("---")
        st.markdown("## Preview")
        st.markdown(content)


def save_page() -> None:
    """Save the current page being edited."""
    try:
        db = next(get_db())
        from modules.wiki.pages import PageManager
        pm = PageManager(db)

        is_editing = st.session_state.editing_page_id is not None

        if is_editing:
            # Update existing page
            request = PageUpdateRequest(
                title=st.session_state.edit_title,
                content=st.session_state.edit_content,
                content_format=st.session_state.edit_format,
                summary=st.session_state.edit_summary,
                status=st.session_state.edit_status,
                tags=[tag for tag in st.session_state.edit_tags],
                change_summary=st.session_state.get('edit_change_summary', '')
            )

            page = pm.update_page(
                st.session_state.editing_page_id,
                request,
                st.session_state.current_user_id
            )
        else:
            # Create new page
            request = PageCreateRequest(
                title=st.session_state.edit_title,
                content=st.session_state.edit_content,
                content_format=st.session_state.edit_format,
                summary=st.session_state.edit_summary,
                namespace=st.session_state.edit_namespace or None,
                tags=[tag for tag in st.session_state.edit_tags],
                status=st.session_state.edit_status
            )

            page = pm.create_page(
                request,
                st.session_state.current_user_id
            )

        db.commit()
        st.success(f"Page {'updated' if is_editing else 'created'} successfully!")

        # Navigate to the page
        st.session_state.current_page_id = page.id
        st.session_state.wiki_view = 'view'
        st.session_state.editing_page_id = None
        st.rerun()

    except Exception as e:
        logger.error(f"Error saving page: {e}")
        st.error(f"Failed to save page: {str(e)}")
    finally:
        db.close()


# ============================================================================
# PAGE VIEWER
# ============================================================================

def render_page_viewer() -> None:
    """Render individual page with TOC and comments."""
    if not st.session_state.current_page_id:
        st.warning("No page selected")
        return

    db = next(get_db())
    try:
        page = db.query(WikiPage).get(st.session_state.current_page_id)

        if not page or page.is_deleted:
            st.error("Page not found")
            return

        # Update view count
        page.view_count += 1
        page.last_viewed_at = datetime.utcnow()
        db.commit()

        # Page header with actions
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

        with col1:
            st.markdown(f"# {page.title}")

        with col2:
            if st.button("✏️ Edit"):
                st.session_state.editing_page_id = page.id
                st.session_state.wiki_view = 'create'
                st.rerun()

        with col3:
            if st.button("📜 History"):
                st.session_state.wiki_view = 'history'
                st.rerun()

        with col4:
            if st.button("🗑️ Delete"):
                if st.confirm("Are you sure you want to delete this page?"):
                    page.is_deleted = True
                    db.commit()
                    st.success("Page deleted")
                    st.session_state.wiki_view = 'browse'
                    st.rerun()

        # Page metadata
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Views", page.view_count)
        with col2:
            st.metric("Likes", page.like_count)
        with col3:
            st.metric("Comments", page.comment_count)
        with col4:
            st.metric("Version", page.current_version)

        # Tags
        if page.tags:
            st.markdown("**Tags:** " + " ".join([
                f'<span class="wiki-tag">{tag.name}</span>'
                for tag in page.tags
            ]), unsafe_allow_html=True)

        # Breadcrumbs
        if page.category:
            st.markdown(f"📂 {page.category.name}")

        st.markdown("---")

        # Layout: TOC and Content
        col1, col2 = st.columns([3, 1])

        with col1:
            # Main content
            st.markdown(page.content)

        with col2:
            # Table of Contents
            render_toc(page.content)

            # Page info
            st.markdown("### 📊 Page Info")
            st.markdown(f"**Author:** User {page.author_id}")
            st.markdown(f"**Created:** {page.created_at.strftime('%Y-%m-%d %H:%M')}")
            st.markdown(f"**Updated:** {page.updated_at.strftime('%Y-%m-%d %H:%M')}")
            st.markdown(f"**Status:** {page.status.value}")

        st.markdown("---")

        # Comments section
        render_comments_section(page)

    except Exception as e:
        logger.error(f"Error rendering page: {e}")
        st.error("Failed to load page")
    finally:
        db.close()


def render_toc(content: str) -> None:
    """Render table of contents from markdown headings."""
    st.markdown("### 📑 Table of Contents")

    # Extract headings
    headings = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)

    if not headings:
        st.info("No headings found")
        return

    st.markdown('<div class="toc-container">', unsafe_allow_html=True)
    for level_hashes, title in headings:
        level = len(level_hashes)
        indent = "&nbsp;" * (level - 1) * 4
        st.markdown(
            f'{indent}<div class="toc-item">{title}</div>',
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================================
# VERSION HISTORY VIEW
# ============================================================================

def render_history() -> None:
    """Render version history with diff visualization."""
    if not st.session_state.current_page_id:
        st.warning("No page selected")
        return

    st.markdown("# 📜 Version History")

    db = next(get_db())
    try:
        page = db.query(WikiPage).get(st.session_state.current_page_id)

        if not page:
            st.error("Page not found")
            return

        st.markdown(f"### {page.title}")
        st.markdown("---")

        # Load history
        from modules.wiki.models import WikiHistory
        history_entries = db.query(WikiHistory).filter(
            WikiHistory.page_id == page.id
        ).order_by(WikiHistory.version.desc()).all()

        if not history_entries:
            st.info("No history available")
            return

        # Display history entries
        for entry in history_entries:
            with st.expander(
                f"Version {entry.version} - {entry.change_type.value} - "
                f"{entry.changed_at.strftime('%Y-%m-%d %H:%M')} by User {entry.changed_by}"
            ):
                col1, col2 = st.columns([3, 1])

                with col1:
                    if entry.change_summary:
                        st.markdown(f"**Change Summary:** {entry.change_summary}")

                    st.markdown("**Content:**")
                    st.markdown(entry.content[:500] + "..." if len(entry.content) > 500 else entry.content)

                with col2:
                    st.metric("Content Size", f"{entry.content_size} bytes")
                    st.metric("Diff Size", f"{entry.diff_size} bytes")

                    if st.button(f"Restore v{entry.version}", key=f"restore_{entry.id}"):
                        restore_version(page, entry)
                        st.rerun()

                # Show diff with previous version
                if entry.version > 1:
                    prev_entry = db.query(WikiHistory).filter(
                        WikiHistory.page_id == page.id,
                        WikiHistory.version == entry.version - 1
                    ).first()

                    if prev_entry:
                        st.markdown("**Changes from previous version:**")
                        render_diff(prev_entry.content, entry.content)

    except Exception as e:
        logger.error(f"Error rendering history: {e}")
        st.error("Failed to load history")
    finally:
        db.close()


def render_diff(old_content: str, new_content: str) -> None:
    """Render diff between two versions."""
    import difflib

    diff = difflib.unified_diff(
        old_content.splitlines(),
        new_content.splitlines(),
        lineterm=''
    )

    diff_html = []
    for line in diff:
        if line.startswith('+'):
            diff_html.append(f'<span class="diff-added">{line}</span>')
        elif line.startswith('-'):
            diff_html.append(f'<span class="diff-removed">{line}</span>')
        else:
            diff_html.append(line)

    st.markdown('<br>'.join(diff_html[:50]), unsafe_allow_html=True)  # Limit to 50 lines


def restore_version(page: WikiPage, history_entry) -> None:
    """Restore a page to a previous version."""
    try:
        db = next(get_db())
        from modules.wiki.pages import PageManager
        pm = PageManager(db)

        request = PageUpdateRequest(
            title=history_entry.title,
            content=history_entry.content,
            change_summary=f"Restored to version {history_entry.version}"
        )

        pm.update_page(page.id, request, st.session_state.current_user_id)
        db.commit()
        st.success(f"Restored to version {history_entry.version}")
    except Exception as e:
        logger.error(f"Error restoring version: {e}")
        st.error("Failed to restore version")
    finally:
        db.close()


# ============================================================================
# CATEGORIES VIEW
# ============================================================================

def render_categories() -> None:
    """Render category browser with tree view."""
    st.markdown("# 📂 Categories")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### Category Tree")
        db = next(get_db())
        try:
            categories = db.query(WikiCategory).filter(
                WikiCategory.parent_id == None
            ).all()

            for category in categories:
                render_category_tree_node(category, 0)
        finally:
            db.close()

    with col2:
        if st.session_state.selected_category:
            db = next(get_db())
            try:
                category = db.query(WikiCategory).get(st.session_state.selected_category)

                if category:
                    st.markdown(f"### {category.name}")
                    if category.description:
                        st.markdown(category.description)

                    st.metric("Pages", category.page_count)

                    # List pages in category
                    pages = db.query(WikiPage).filter(
                        WikiPage.category_id == category.id,
                        WikiPage.is_deleted == False
                    ).all()

                    for page in pages:
                        render_page_card(page)
            finally:
                db.close()
        else:
            st.info("Select a category to view details")


def render_category_tree_node(category: WikiCategory, depth: int) -> None:
    """Render a category tree node recursively."""
    indent = "&nbsp;" * depth * 4

    if st.button(
        f"{category.icon or '📁'} {category.name} ({category.page_count})",
        key=f"cat_{category.id}",
        use_container_width=True
    ):
        st.session_state.selected_category = category.id
        st.rerun()

    # Render children
    for child in category.children:
        render_category_tree_node(child, depth + 1)


# ============================================================================
# TAGS VIEW
# ============================================================================

def render_tags() -> None:
    """Render tag cloud and tag browser."""
    st.markdown("# 🏷️ Tags")

    db = next(get_db())
    try:
        tags = db.query(WikiTag).order_by(WikiTag.usage_count.desc()).all()

        # Tag cloud
        st.markdown("### Tag Cloud")
        tag_html = []
        for tag in tags:
            size = min(2.0, 0.8 + (tag.usage_count / 10))
            tag_html.append(
                f'<span class="wiki-tag" style="font-size: {size}em; '
                f'background: {tag.color}; cursor: pointer;">'
                f'{tag.name} ({tag.usage_count})</span>'
            )

        st.markdown(" ".join(tag_html), unsafe_allow_html=True)

        st.markdown("---")

        # Tag list
        st.markdown("### All Tags")
        for tag in tags:
            with st.expander(f"{tag.name} ({tag.usage_count} pages)"):
                if tag.description:
                    st.markdown(f"**Description:** {tag.description}")

                # List pages with this tag
                pages = db.query(WikiPage).join(
                    WikiPage.tags
                ).filter(
                    WikiTag.id == tag.id,
                    WikiPage.is_deleted == False
                ).all()

                for page in pages:
                    if st.button(page.title, key=f"tag_page_{tag.id}_{page.id}"):
                        st.session_state.current_page_id = page.id
                        st.session_state.wiki_view = 'view'
                        st.rerun()

    finally:
        db.close()


# ============================================================================
# SEARCH VIEW
# ============================================================================

def render_search() -> None:
    """Render advanced search interface."""
    st.markdown("# 🔍 Advanced Search")

    # Search input
    query = st.text_input(
        "Search query",
        value=st.session_state.search_query,
        placeholder="Enter search terms...",
        key="search_input"
    )

    # Advanced filters
    with st.expander("Advanced Filters"):
        col1, col2, col3 = st.columns(3)

        with col1:
            status_filter = st.multiselect(
                "Status",
                [PageStatus.PUBLISHED, PageStatus.DRAFT, PageStatus.ARCHIVED],
                key="search_status"
            )

        with col2:
            db = next(get_db())
            categories = db.query(WikiCategory).all()
            category_filter = st.multiselect(
                "Categories",
                [cat.name for cat in categories],
                key="search_categories"
            )
            db.close()

        with col3:
            date_range = st.date_input(
                "Date Range",
                value=[],
                key="search_dates"
            )

    # Search button
    if st.button("🔍 Search", type="primary") or query:
        perform_search(query, status_filter, category_filter, date_range)


def perform_search(
    query: str,
    status_filter: List[PageStatus],
    category_filter: List[str],
    date_range: List
) -> None:
    """Perform search and display results."""
    if not query:
        st.warning("Please enter a search query")
        return

    db = next(get_db())
    try:
        # Build search query
        search_query = db.query(WikiPage).filter(
            WikiPage.is_deleted == False,
            (WikiPage.title.ilike(f"%{query}%") |
             WikiPage.content.ilike(f"%{query}%"))
        )

        # Apply filters
        if status_filter:
            search_query = search_query.filter(WikiPage.status.in_(status_filter))

        if category_filter:
            categories = db.query(WikiCategory).filter(
                WikiCategory.name.in_(category_filter)
            ).all()
            cat_ids = [cat.id for cat in categories]
            search_query = search_query.filter(WikiPage.category_id.in_(cat_ids))

        if date_range and len(date_range) == 2:
            search_query = search_query.filter(
                WikiPage.created_at.between(date_range[0], date_range[1])
            )

        results = search_query.all()

        st.markdown(f"### Found {len(results)} results")

        for page in results:
            render_page_card(page, highlight_query=query)

    except Exception as e:
        logger.error(f"Error performing search: {e}")
        st.error("Search failed")
    finally:
        db.close()


# ============================================================================
# COMMENTS SECTION
# ============================================================================

def render_comments_section(page: WikiPage) -> None:
    """Render comments section for a page."""
    st.markdown("## 💬 Comments")

    # Add comment form
    with st.form("add_comment"):
        comment_text = st.text_area("Add a comment", height=100)
        submit = st.form_submit_button("Post Comment")

        if submit and comment_text:
            add_comment(page.id, comment_text)
            st.rerun()

    # Display comments
    db = next(get_db())
    try:
        from modules.wiki.models import WikiComment
        comments = db.query(WikiComment).filter(
            WikiComment.page_id == page.id,
            WikiComment.is_deleted == False,
            WikiComment.parent_comment_id == None
        ).order_by(WikiComment.created_at.desc()).all()

        for comment in comments:
            render_comment(comment)
    finally:
        db.close()


def render_comment(comment) -> None:
    """Render a single comment."""
    st.markdown(
        f'<div class="comment-card">'
        f'<div class="comment-author">User {comment.author_id}</div>'
        f'<div class="comment-date">{comment.created_at.strftime("%Y-%m-%d %H:%M")}</div>'
        f'<div style="margin-top: 10px;">{comment.content}</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    # Render replies
    if comment.replies:
        st.markdown('<div style="margin-left: 30px;">', unsafe_allow_html=True)
        for reply in comment.replies:
            render_comment(reply)
        st.markdown('</div>', unsafe_allow_html=True)


def add_comment(page_id: int, content: str) -> None:
    """Add a comment to a page."""
    try:
        db = next(get_db())
        from modules.wiki.collaboration import CollaborationService
        cs = CollaborationService(db)

        cs.add_comment(
            page_id=page_id,
            author_id=st.session_state.current_user_id,
            content=content
        )

        db.commit()
        st.success("Comment added!")
    except Exception as e:
        logger.error(f"Error adding comment: {e}")
        st.error("Failed to add comment")
    finally:
        db.close()


# ============================================================================
# ANALYTICS VIEW
# ============================================================================

def render_analytics() -> None:
    """Render analytics dashboard."""
    st.markdown("# 📊 Wiki Analytics")

    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", datetime.now())

    st.markdown("---")

    db = next(get_db())
    try:
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        total_pages = db.query(WikiPage).filter(
            WikiPage.is_deleted == False
        ).count()

        total_views = db.query(func.sum(WikiPage.view_count)).filter(
            WikiPage.is_deleted == False
        ).scalar() or 0

        from modules.wiki.models import WikiComment
        total_comments = db.query(WikiComment).filter(
            WikiComment.is_deleted == False
        ).count()

        from modules.wiki.models import WikiHistory
        total_edits = db.query(WikiHistory).count()

        with col1:
            st.markdown(
                f'<div class="analytics-card">'
                f'<div class="analytics-value">{total_pages}</div>'
                f'<div class="analytics-label">Total Pages</div>'
                f'</div>',
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(
                f'<div class="analytics-card">'
                f'<div class="analytics-value">{total_views}</div>'
                f'<div class="analytics-label">Total Views</div>'
                f'</div>',
                unsafe_allow_html=True
            )

        with col3:
            st.markdown(
                f'<div class="analytics-card">'
                f'<div class="analytics-value">{total_comments}</div>'
                f'<div class="analytics-label">Comments</div>'
                f'</div>',
                unsafe_allow_html=True
            )

        with col4:
            st.markdown(
                f'<div class="analytics-card">'
                f'<div class="analytics-value">{total_edits}</div>'
                f'<div class="analytics-label">Total Edits</div>'
                f'</div>',
                unsafe_allow_html=True
            )

        st.markdown("---")

        # Popular pages
        st.markdown("### 🔥 Most Popular Pages")
        popular_pages = db.query(WikiPage).filter(
            WikiPage.is_deleted == False
        ).order_by(WikiPage.view_count.desc()).limit(10).all()

        for i, page in enumerate(popular_pages, 1):
            col1, col2, col3 = st.columns([0.5, 3, 1])
            with col1:
                st.markdown(f"**{i}.**")
            with col2:
                st.markdown(f"**{page.title}**")
            with col3:
                st.metric("Views", page.view_count)

        st.markdown("---")

        # Recent activity
        st.markdown("### 📈 Recent Activity")
        recent_edits = db.query(WikiHistory).order_by(
            WikiHistory.changed_at.desc()
        ).limit(10).all()

        for edit in recent_edits:
            st.markdown(
                f"- **{edit.change_type.value}** on page {edit.page_id} "
                f"by User {edit.changed_by} "
                f"at {edit.changed_at.strftime('%Y-%m-%d %H:%M')}"
            )

    finally:
        db.close()


# ============================================================================
# SETTINGS VIEW
# ============================================================================

def render_settings() -> None:
    """Render wiki settings."""
    st.markdown("# ⚙️ Wiki Settings")

    tab1, tab2, tab3 = st.tabs(["General", "Permissions", "Advanced"])

    with tab1:
        st.markdown("### General Settings")

        wiki_name = st.text_input("Wiki Name", value="NEXUS Wiki")
        wiki_description = st.text_area(
            "Description",
            value="Your central knowledge repository"
        )

        enable_comments = st.checkbox("Enable Comments", value=True)
        enable_versioning = st.checkbox("Enable Version History", value=True)
        enable_ai = st.checkbox("Enable AI Assistant", value=True)

        if st.button("Save General Settings"):
            st.success("Settings saved!")

    with tab2:
        st.markdown("### Default Permissions")

        default_read = st.checkbox("Public Read Access", value=True)
        default_comment = st.checkbox("Public Comment Access", value=False)
        default_edit = st.checkbox("Public Edit Access", value=False)

        if st.button("Save Permission Settings"):
            st.success("Permission settings saved!")

    with tab3:
        st.markdown("### Advanced Settings")

        max_upload_size = st.number_input(
            "Max Upload Size (MB)",
            min_value=1,
            max_value=100,
            value=10
        )

        page_cache_duration = st.number_input(
            "Page Cache Duration (seconds)",
            min_value=0,
            max_value=3600,
            value=300
        )

        enable_analytics = st.checkbox("Enable Analytics Tracking", value=True)

        if st.button("Save Advanced Settings"):
            st.success("Advanced settings saved!")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def render_page_card(page: WikiPage, highlight_query: Optional[str] = None) -> None:
    """Render a page as a card."""
    # Extract preview
    preview = page.content[:200] + "..." if len(page.content) > 200 else page.content

    # Highlight search query
    if highlight_query:
        preview = preview.replace(
            highlight_query,
            f"<mark>{highlight_query}</mark>"
        )

    st.markdown(
        f'<div class="page-card">'
        f'<div class="page-title">{page.title}</div>'
        f'<div style="margin: 10px 0;">{preview}</div>'
        f'<div class="page-meta">'
        f'👁️ {page.view_count} views | '
        f'💬 {page.comment_count} comments | '
        f'📅 {page.updated_at.strftime("%Y-%m-%d")}'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    if st.button(f"View", key=f"view_{page.id}"):
        st.session_state.current_page_id = page.id
        st.session_state.wiki_view = 'view'
        st.rerun()


def render_page_list_item(page: WikiPage) -> None:
    """Render a page as a list item."""
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        if st.button(page.title, key=f"list_{page.id}"):
            st.session_state.current_page_id = page.id
            st.session_state.wiki_view = 'view'
            st.rerun()

    with col2:
        st.markdown(f"👁️ {page.view_count}")

    with col3:
        st.markdown(page.updated_at.strftime("%Y-%m-%d"))


def render_page_tree(pages: List[WikiPage]) -> None:
    """Render pages as a tree structure."""
    # Group by parent
    root_pages = [p for p in pages if not p.parent_page_id]

    for page in root_pages:
        render_page_tree_node(page, pages, 0)


def render_page_tree_node(page: WikiPage, all_pages: List[WikiPage], depth: int) -> None:
    """Render a page tree node recursively."""
    indent = "&nbsp;" * depth * 4

    st.markdown(
        f'{indent}<div class="category-item">{page.title}</div>',
        unsafe_allow_html=True
    )

    if st.button(f"View", key=f"tree_{page.id}"):
        st.session_state.current_page_id = page.id
        st.session_state.wiki_view = 'view'
        st.rerun()

    # Render children
    children = [p for p in all_pages if p.parent_page_id == page.id]
    for child in children:
        render_page_tree_node(child, all_pages, depth + 1)


def show_ai_assistant() -> None:
    """Show AI assistant dialog."""
    st.info("AI Assistant integration coming soon!")


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main() -> None:
    """Main wiki application entry point."""
    st.set_page_config(
        page_title="NEXUS Wiki",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Apply custom CSS
    apply_wiki_css()

    # Initialize session state
    init_session_state()

    # Render sidebar
    render_sidebar()

    # Route to appropriate view
    view = st.session_state.wiki_view

    if view == 'home':
        render_home()
    elif view == 'browse':
        render_browse()
    elif view == 'create':
        render_create_edit_page()
    elif view == 'view':
        render_page_viewer()
    elif view == 'history':
        render_history()
    elif view == 'categories':
        render_categories()
    elif view == 'tags':
        render_tags()
    elif view == 'search':
        render_search()
    elif view == 'analytics':
        render_analytics()
    elif view == 'settings':
        render_settings()
    else:
        render_home()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Wiki UI error: {str(e)}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")
