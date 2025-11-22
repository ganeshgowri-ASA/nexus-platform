"""
Document Management System - Streamlit UI Module

Comprehensive UI for document management including:
- File explorer with tree view
- Drag-and-drop upload
- Document preview
- Search and filters
- Tag management
- Permission management
- Version history
- Comments
- Workflows
- Statistics
"""

import io
import json
import mimetypes
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
import streamlit as st
from PIL import Image

# Constants
API_BASE_URL = "http://localhost:8000/api/v1"
MIME_TYPE_ICONS = {
    "application/pdf": "📄",
    "application/msword": "📝",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "📝",
    "application/vnd.ms-excel": "📊",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "📊",
    "application/vnd.ms-powerpoint": "📊",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "📊",
    "image/": "🖼️",
    "video/": "🎥",
    "audio/": "🎵",
    "text/": "📋",
    "application/zip": "🗜️",
    "application/x-rar": "🗜️",
}


def get_file_icon(mime_type: str) -> str:
    """Get icon for file type based on MIME type."""
    if not mime_type:
        return "📄"

    for key, icon in MIME_TYPE_ICONS.items():
        if mime_type.startswith(key):
            return icon

    return "📄"


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def format_datetime(dt: datetime) -> str:
    """Format datetime in human-readable format."""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))

    now = datetime.now()
    diff = now - dt

    if diff.days == 0:
        if diff.seconds < 60:
            return "Just now"
        elif diff.seconds < 3600:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.days == 1:
        return "Yesterday"
    elif diff.days < 7:
        return f"{diff.days} days ago"
    else:
        return dt.strftime("%b %d, %Y")


def get_status_badge(status: str) -> str:
    """Get HTML badge for document status."""
    badge_classes = {
        "active": "status-active",
        "draft": "status-draft",
        "archived": "status-archived",
        "locked": "status-locked",
        "in_review": "status-warning",
        "approved": "status-active",
        "rejected": "status-locked"
    }

    badge_class = badge_classes.get(status.lower(), "status-draft")
    return f'<span class="status-badge {badge_class}">{status.upper()}</span>'


class DocumentAPIClient:
    """Client for Document Management API."""

    def __init__(self, base_url: str = API_BASE_URL, token: str = None):
        self.base_url = base_url
        self.token = token or st.session_state.get('api_token')
        self.headers = {
            "Authorization": f"Bearer {self.token}" if self.token else "",
        }

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make API request."""
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return {}

    def list_documents(
        self,
        folder_id: Optional[int] = None,
        status_filter: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """List documents."""
        params = {"skip": skip, "limit": limit}
        if folder_id is not None:
            params["folder_id"] = folder_id
        if status_filter:
            params["status_filter"] = status_filter

        return self._request("GET", "documents", params=params)

    def get_document(self, document_id: int) -> Dict[str, Any]:
        """Get document details."""
        return self._request("GET", f"documents/{document_id}")

    def upload_document(
        self,
        file,
        title: Optional[str] = None,
        description: Optional[str] = None,
        folder_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Upload a document."""
        files = {"file": file}
        data = {}
        if title:
            data["title"] = title
        if description:
            data["description"] = description
        if folder_id is not None:
            data["folder_id"] = folder_id

        return self._request("POST", "documents", files=files, data=data)

    def delete_document(self, document_id: int, permanent: bool = False) -> None:
        """Delete a document."""
        params = {"permanent": permanent}
        self._request("DELETE", f"documents/{document_id}", params=params)

    def search_documents(self, query: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Search documents."""
        search_query = {
            "query": query,
            "filters": filters or {},
        }
        return self._request("POST", "documents/search", json=search_query)

    def list_versions(self, document_id: int) -> List[Dict[str, Any]]:
        """List document versions."""
        return self._request("GET", f"documents/{document_id}/versions")

    def list_comments(self, document_id: int) -> List[Dict[str, Any]]:
        """List document comments."""
        return self._request("GET", f"documents/{document_id}/comments")

    def add_comment(self, document_id: int, content: str, parent_id: Optional[int] = None) -> Dict[str, Any]:
        """Add a comment."""
        comment_data = {"content": content}
        if parent_id is not None:
            comment_data["parent_id"] = parent_id

        return self._request("POST", f"documents/{document_id}/comments", json=comment_data)

    def list_permissions(self, document_id: int) -> List[Dict[str, Any]]:
        """List document permissions."""
        return self._request("GET", f"documents/{document_id}/permissions")

    def grant_permission(
        self,
        document_id: int,
        user_id: int,
        access_level: str,
        expires_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Grant document permission."""
        permission_data = {
            "user_id": user_id,
            "access_level": access_level,
        }
        if expires_at:
            permission_data["expires_at"] = expires_at.isoformat()

        return self._request("POST", f"documents/{document_id}/permissions", json=permission_data)

    def get_statistics(self) -> Dict[str, Any]:
        """Get document statistics."""
        return self._request("GET", "documents/stats/overview")


def render_folder_tree():
    """Render folder tree navigation."""
    st.markdown("### 📁 Folders")

    # Mock folder structure (in production, fetch from API)
    folders = [
        {"id": 1, "name": "My Documents", "icon": "📁", "children": [
            {"id": 2, "name": "Work", "icon": "💼", "children": []},
            {"id": 3, "name": "Personal", "icon": "👤", "children": []},
        ]},
        {"id": 4, "name": "Shared", "icon": "👥", "children": []},
        {"id": 5, "name": "Projects", "icon": "📊", "children": [
            {"id": 6, "name": "Project A", "icon": "📂", "children": []},
            {"id": 7, "name": "Project B", "icon": "📂", "children": []},
        ]},
    ]

    def render_folder_item(folder, level=0):
        """Render a single folder item."""
        indent = "  " * level
        is_selected = st.session_state.selected_folder == folder['id']

        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(
                f"{indent}{folder['icon']} {folder['name']}",
                key=f"folder_{folder['id']}",
                use_container_width=True,
                type="primary" if is_selected else "secondary"
            ):
                st.session_state.selected_folder = folder['id']
                st.rerun()

        with col2:
            if st.button("⋮", key=f"folder_menu_{folder['id']}"):
                st.session_state[f"show_folder_menu_{folder['id']}"] = True

        # Render children
        if folder.get('children'):
            for child in folder['children']:
                render_folder_item(child, level + 1)

    for folder in folders:
        render_folder_item(folder)

    st.divider()

    if st.button("➕ New Folder", use_container_width=True):
        st.session_state.show_new_folder_modal = True


def render_file_upload():
    """Render file upload section."""
    st.markdown("### 📤 Upload Files")

    with st.form("upload_form", clear_on_submit=True):
        uploaded_files = st.file_uploader(
            "Choose files",
            accept_multiple_files=True,
            help="Drag and drop files or click to browse",
            label_visibility="collapsed"
        )

        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input("Title (optional)", placeholder="Auto-generated from filename")
            description = st.text_area("Description (optional)", max_chars=500)

        with col2:
            tags = st.multiselect(
                "Tags",
                ["Important", "Urgent", "Draft", "Review", "Approved"],
                help="Add tags to organize your documents"
            )

            is_public = st.checkbox("Make public", help="Allow anyone with the link to view")

        submit_button = st.form_submit_button("Upload", type="primary", use_container_width=True)

        if submit_button and uploaded_files:
            api = DocumentAPIClient()
            progress_bar = st.progress(0)
            status_text = st.empty()

            total_files = len(uploaded_files)
            for idx, file in enumerate(uploaded_files):
                status_text.text(f"Uploading {file.name}...")

                try:
                    result = api.upload_document(
                        file=file,
                        title=title or file.name,
                        description=description,
                        folder_id=st.session_state.selected_folder
                    )

                    progress = (idx + 1) / total_files
                    progress_bar.progress(progress)

                except Exception as e:
                    st.error(f"Failed to upload {file.name}: {str(e)}")

            status_text.text("Upload complete!")
            st.success(f"Successfully uploaded {total_files} file(s)")
            st.balloons()


def render_document_grid(documents: List[Dict[str, Any]]):
    """Render documents in grid view."""
    if not documents:
        st.info("📭 No documents found in this folder")
        return

    # Create grid layout (3 columns)
    cols_per_row = 3
    for i in range(0, len(documents), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(documents):
                doc = documents[idx]
                with col:
                    render_document_card(doc)


def render_document_card(doc: Dict[str, Any]):
    """Render a single document card."""
    icon = get_file_icon(doc.get('mime_type', ''))
    status = doc.get('status', 'active')
    status_badge = get_status_badge(status)

    # Card container
    st.markdown(f"""
    <div class="custom-card" style="cursor: pointer; min-height: 200px;">
        <div style="text-align: center; font-size: 3rem; margin-bottom: 1rem;">
            {icon}
        </div>
        <h4 style="margin: 0.5rem 0; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">
            {doc.get('title', 'Untitled')}
        </h4>
        <p style="color: #6c757d; font-size: 0.875rem; margin: 0.5rem 0;">
            {format_file_size(doc.get('file_size', 0))}
        </p>
        <p style="color: #6c757d; font-size: 0.875rem; margin: 0.5rem 0;">
            {format_datetime(doc.get('updated_at', datetime.now()))}
        </p>
        <div style="margin-top: 0.5rem;">
            {status_badge}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Action buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("👁️", key=f"view_{doc['id']}", help="View", use_container_width=True):
            st.session_state.selected_document = doc['id']
            st.session_state.show_document_details = True

    with col2:
        if st.button("⬇️", key=f"download_{doc['id']}", help="Download", use_container_width=True):
            st.info(f"Downloading {doc.get('title', 'document')}...")

    with col3:
        if st.button("⋮", key=f"menu_{doc['id']}", help="More", use_container_width=True):
            st.session_state[f"show_doc_menu_{doc['id']}"] = True


def render_document_list(documents: List[Dict[str, Any]]):
    """Render documents in list view."""
    if not documents:
        st.info("📭 No documents found in this folder")
        return

    # Create DataFrame
    df_data = []
    for doc in documents:
        df_data.append({
            "📄": get_file_icon(doc.get('mime_type', '')),
            "Title": doc.get('title', 'Untitled'),
            "Size": format_file_size(doc.get('file_size', 0)),
            "Status": doc.get('status', 'active'),
            "Modified": format_datetime(doc.get('updated_at', datetime.now())),
            "Owner": doc.get('owner_id', 'Unknown'),
            "ID": doc['id']
        })

    df = pd.DataFrame(df_data)

    # Display table
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "📄": st.column_config.TextColumn(width="small"),
            "Title": st.column_config.TextColumn(width="large"),
            "Size": st.column_config.TextColumn(width="small"),
            "Status": st.column_config.TextColumn(width="small"),
            "Modified": st.column_config.TextColumn(width="medium"),
            "Owner": st.column_config.TextColumn(width="small"),
            "ID": None  # Hide ID column
        }
    )

    # Selection actions
    st.markdown("#### Bulk Actions")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📥 Download Selected"):
            st.info("Bulk download feature coming soon")

    with col2:
        if st.button("🗂️ Move Selected"):
            st.info("Bulk move feature coming soon")

    with col3:
        if st.button("🏷️ Tag Selected"):
            st.info("Bulk tag feature coming soon")

    with col4:
        if st.button("🗑️ Delete Selected"):
            st.warning("Bulk delete feature coming soon")


def render_document_details():
    """Render detailed document view."""
    if 'selected_document' not in st.session_state:
        return

    doc_id = st.session_state.selected_document
    api = DocumentAPIClient()

    try:
        doc = api.get_document(doc_id)
    except Exception as e:
        st.error(f"Failed to load document: {str(e)}")
        return

    # Header
    col1, col2 = st.columns([4, 1])

    with col1:
        st.markdown(f"## {get_file_icon(doc.get('mime_type', ''))} {doc.get('title', 'Untitled')}")

    with col2:
        if st.button("✖️ Close", use_container_width=True):
            st.session_state.show_document_details = False
            del st.session_state.selected_document
            st.rerun()

    st.divider()

    # Tabs for different sections
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 Details",
        "💬 Comments",
        "🕐 Versions",
        "🔐 Permissions",
        "🔄 Workflow",
        "📊 Activity"
    ])

    with tab1:
        render_document_info_tab(doc)

    with tab2:
        render_comments_tab(doc_id)

    with tab3:
        render_versions_tab(doc_id)

    with tab4:
        render_permissions_tab(doc_id)

    with tab5:
        render_workflow_tab(doc_id)

    with tab6:
        render_activity_tab(doc_id)


def render_document_info_tab(doc: Dict[str, Any]):
    """Render document information tab."""
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 📄 Document Preview")

        # Preview based on file type
        mime_type = doc.get('mime_type', '')

        if mime_type.startswith('image/'):
            st.info("🖼️ Image preview will be displayed here")
        elif mime_type == 'application/pdf':
            st.info("📄 PDF preview will be displayed here")
        elif mime_type.startswith('text/'):
            st.info("📋 Text preview will be displayed here")
        else:
            st.info("👁️ Preview not available for this file type")

        st.markdown("### 📝 Description")
        description = doc.get('description', 'No description')
        st.markdown(description)

        # Tags
        st.markdown("### 🏷️ Tags")
        tags = ["Important", "Q4-2025", "Client"]  # Mock tags
        for tag in tags:
            st.markdown(f'<span class="tag">{tag}</span>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Add new tag
        col_tag1, col_tag2 = st.columns([3, 1])
        with col_tag1:
            new_tag = st.text_input("Add tag", label_visibility="collapsed", placeholder="Enter tag name")
        with col_tag2:
            if st.button("Add", use_container_width=True):
                if new_tag:
                    st.success(f"Tag '{new_tag}' added!")

    with col2:
        st.markdown("### ℹ️ Information")

        info_items = [
            ("📄 Type", doc.get('mime_type', 'Unknown')),
            ("💾 Size", format_file_size(doc.get('file_size', 0))),
            ("📅 Created", format_datetime(doc.get('created_at', datetime.now()))),
            ("📝 Modified", format_datetime(doc.get('updated_at', datetime.now()))),
            ("👤 Owner", f"User {doc.get('owner_id', 'Unknown')}"),
            ("📁 Folder", f"Folder {doc.get('folder_id', 'Root')}"),
            ("🔢 Version", str(doc.get('current_version', 1))),
            ("👁️ Views", str(doc.get('view_count', 0))),
            ("⬇️ Downloads", str(doc.get('download_count', 0))),
            ("🔒 Status", doc.get('status', 'active')),
        ]

        for label, value in info_items:
            st.markdown(f"""
            <div style="margin-bottom: 1rem;">
                <div style="color: #6c757d; font-size: 0.875rem; margin-bottom: 0.25rem;">
                    {label}
                </div>
                <div style="font-weight: 600;">
                    {value}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        st.markdown("### ⚡ Actions")

        if st.button("⬇️ Download", use_container_width=True, type="primary"):
            st.success("Download started!")

        if st.button("✏️ Edit", use_container_width=True):
            st.info("Edit mode enabled")

        if st.button("📤 Share", use_container_width=True):
            st.session_state.show_share_modal = True

        if st.button("📋 Copy Link", use_container_width=True):
            st.success("Link copied to clipboard!")

        if st.button("🗑️ Delete", use_container_width=True):
            st.warning("Are you sure you want to delete this document?")


def render_comments_tab(doc_id: int):
    """Render comments tab."""
    st.markdown("### 💬 Comments")

    api = DocumentAPIClient()

    # Mock comments (in production, fetch from API)
    comments = [
        {
            "id": 1,
            "user_id": 1,
            "content": "This document looks good, but we need to review section 3.",
            "created_at": datetime.now() - timedelta(hours=2),
            "is_resolved": False,
            "replies": []
        },
        {
            "id": 2,
            "user_id": 2,
            "content": "I've made the requested changes. Please review when you have a chance.",
            "created_at": datetime.now() - timedelta(hours=1),
            "is_resolved": False,
            "replies": [
                {
                    "id": 3,
                    "user_id": 1,
                    "content": "Perfect! Thanks for the quick turnaround.",
                    "created_at": datetime.now() - timedelta(minutes=30),
                }
            ]
        }
    ]

    # Display comments
    for comment in comments:
        render_comment_item(comment, doc_id)

    st.divider()

    # Add new comment
    st.markdown("### ✍️ Add Comment")
    with st.form("add_comment_form", clear_on_submit=True):
        comment_content = st.text_area(
            "Your comment",
            placeholder="Type your comment here...",
            height=100,
            label_visibility="collapsed"
        )

        col1, col2 = st.columns([4, 1])
        with col2:
            submit = st.form_submit_button("Post", use_container_width=True, type="primary")

        if submit and comment_content:
            try:
                api.add_comment(doc_id, comment_content)
                st.success("Comment added successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to add comment: {str(e)}")


def render_comment_item(comment: Dict[str, Any], doc_id: int, is_reply: bool = False):
    """Render a single comment item."""
    indent = "margin-left: 2rem;" if is_reply else ""

    st.markdown(f"""
    <div class="custom-card" style="{indent}">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <div>
                <strong>👤 User {comment.get('user_id', 'Unknown')}</strong>
                <span style="color: #6c757d; font-size: 0.875rem; margin-left: 0.5rem;">
                    {format_datetime(comment.get('created_at', datetime.now()))}
                </span>
            </div>
            {f'<span class="tag" style="background-color: #d4edda; color: #155724;">✓ Resolved</span>' if comment.get('is_resolved') else ''}
        </div>
        <p style="margin: 0.5rem 0;">
            {comment.get('content', '')}
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 4])

    with col1:
        if st.button("💬 Reply", key=f"reply_{comment['id']}_{is_reply}"):
            st.session_state[f"replying_to_{comment['id']}"] = True

    with col2:
        if not comment.get('is_resolved'):
            if st.button("✓ Resolve", key=f"resolve_{comment['id']}_{is_reply}"):
                st.success("Comment marked as resolved!")

    # Show reply form if replying
    if st.session_state.get(f"replying_to_{comment['id']}", False):
        with st.form(f"reply_form_{comment['id']}", clear_on_submit=True):
            reply_content = st.text_input("Reply", label_visibility="collapsed")
            col_r1, col_r2 = st.columns([4, 1])
            with col_r2:
                if st.form_submit_button("Send", use_container_width=True):
                    if reply_content:
                        api = DocumentAPIClient()
                        api.add_comment(doc_id, reply_content, parent_id=comment['id'])
                        st.success("Reply added!")
                        del st.session_state[f"replying_to_{comment['id']}"]
                        st.rerun()

    # Render replies
    for reply in comment.get('replies', []):
        render_comment_item(reply, doc_id, is_reply=True)


def render_versions_tab(doc_id: int):
    """Render versions tab."""
    st.markdown("### 🕐 Version History")

    api = DocumentAPIClient()

    # Mock versions (in production, fetch from API)
    versions = [
        {
            "id": 3,
            "version_number": 3,
            "file_size": 245600,
            "change_summary": "Updated figures and conclusion section",
            "created_by_id": 1,
            "created_at": datetime.now() - timedelta(hours=1)
        },
        {
            "id": 2,
            "version_number": 2,
            "file_size": 243200,
            "change_summary": "Added new section on methodology",
            "created_by_id": 2,
            "created_at": datetime.now() - timedelta(days=1)
        },
        {
            "id": 1,
            "version_number": 1,
            "file_size": 240000,
            "change_summary": "Initial version",
            "created_by_id": 1,
            "created_at": datetime.now() - timedelta(days=3)
        }
    ]

    for version in versions:
        is_current = version['version_number'] == versions[0]['version_number']

        st.markdown(f"""
        <div class="custom-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h4 style="margin: 0;">
                        Version {version['version_number']}
                        {' <span class="tag" style="background-color: #667eea; color: white;">Current</span>' if is_current else ''}
                    </h4>
                    <p style="color: #6c757d; margin: 0.5rem 0 0 0;">
                        {version.get('change_summary', 'No description')}
                    </p>
                </div>
                <div style="text-align: right;">
                    <div style="font-weight: 600;">
                        {format_file_size(version['file_size'])}
                    </div>
                    <div style="color: #6c757d; font-size: 0.875rem;">
                        {format_datetime(version['created_at'])}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.button("⬇️ Download", key=f"download_v_{version['id']}"):
                st.info(f"Downloading version {version['version_number']}...")

        with col2:
            if not is_current:
                if st.button("↩️ Restore", key=f"restore_v_{version['id']}"):
                    st.warning(f"Restore version {version['version_number']}?")

        st.markdown("<br>", unsafe_allow_html=True)

    st.divider()

    # Upload new version
    st.markdown("### ⬆️ Upload New Version")
    with st.form("upload_version_form"):
        version_file = st.file_uploader("Choose file", label_visibility="collapsed")
        change_summary = st.text_area("What changed?", placeholder="Describe the changes in this version")

        if st.form_submit_button("Upload Version", type="primary"):
            if version_file and change_summary:
                st.success("New version uploaded successfully!")
            else:
                st.error("Please provide both file and change summary")


def render_permissions_tab(doc_id: int):
    """Render permissions tab."""
    st.markdown("### 🔐 Permissions")

    api = DocumentAPIClient()

    # Current permissions
    st.markdown("#### Current Access")

    # Mock permissions
    permissions = [
        {
            "id": 1,
            "user_id": 1,
            "access_level": "admin",
            "granted_by_id": 1,
            "created_at": datetime.now() - timedelta(days=10)
        },
        {
            "id": 2,
            "user_id": 2,
            "access_level": "edit",
            "granted_by_id": 1,
            "created_at": datetime.now() - timedelta(days=5)
        },
        {
            "id": 3,
            "user_id": 3,
            "access_level": "view",
            "granted_by_id": 1,
            "created_at": datetime.now() - timedelta(days=2),
            "expires_at": datetime.now() + timedelta(days=7)
        }
    ]

    for perm in permissions:
        access_icons = {
            "admin": "👑",
            "edit": "✏️",
            "comment": "💬",
            "view": "👁️"
        }

        icon = access_icons.get(perm['access_level'], "❓")
        expires = perm.get('expires_at')

        st.markdown(f"""
        <div class="custom-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h4 style="margin: 0;">
                        {icon} User {perm['user_id']}
                    </h4>
                    <p style="color: #6c757d; margin: 0.5rem 0 0 0;">
                        Access: <strong>{perm['access_level'].upper()}</strong>
                        {f' • Expires: {format_datetime(expires)}' if expires else ''}
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.button("✏️ Edit", key=f"edit_perm_{perm['id']}"):
                st.info("Edit permission modal would open here")

        with col2:
            if st.button("🗑️ Remove", key=f"remove_perm_{perm['id']}"):
                st.warning("Remove access?")

        st.markdown("<br>", unsafe_allow_html=True)

    st.divider()

    # Grant new permission
    st.markdown("### ➕ Grant Access")
    with st.form("grant_permission_form"):
        col1, col2 = st.columns(2)

        with col1:
            user_id = st.number_input("User ID", min_value=1, value=1)
            access_level = st.selectbox(
                "Access Level",
                ["view", "comment", "edit", "admin"]
            )

        with col2:
            expiration = st.checkbox("Set expiration")
            if expiration:
                expires_at = st.date_input("Expires on")

        if st.form_submit_button("Grant Access", type="primary"):
            st.success(f"Access granted to User {user_id}")


def render_workflow_tab(doc_id: int):
    """Render workflow tab."""
    st.markdown("### 🔄 Workflows")

    # Mock workflow
    workflows = [
        {
            "id": 1,
            "workflow_name": "Document Approval",
            "status": "in_progress",
            "current_step": 2,
            "total_steps": 3,
            "created_at": datetime.now() - timedelta(days=2),
            "steps": [
                {
                    "step_number": 1,
                    "step_name": "Initial Review",
                    "assignee_id": 1,
                    "status": "approved",
                    "completed_at": datetime.now() - timedelta(days=1)
                },
                {
                    "step_number": 2,
                    "step_name": "Technical Review",
                    "assignee_id": 2,
                    "status": "in_progress",
                    "completed_at": None
                },
                {
                    "step_number": 3,
                    "step_name": "Final Approval",
                    "assignee_id": 3,
                    "status": "pending",
                    "completed_at": None
                }
            ]
        }
    ]

    for workflow in workflows:
        st.markdown(f"""
        <div class="custom-card">
            <h3 style="margin: 0;">{workflow['workflow_name']}</h3>
            <p style="color: #6c757d; margin: 0.5rem 0;">
                Status: <strong>{workflow['status'].upper()}</strong> •
                Step {workflow['current_step']} of {workflow['total_steps']}
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Progress bar
        progress = workflow['current_step'] / workflow['total_steps']
        st.progress(progress)

        st.markdown("<br>", unsafe_allow_html=True)

        # Workflow steps
        for step in workflow['steps']:
            status_icons = {
                "approved": "✅",
                "in_progress": "🔄",
                "pending": "⏳",
                "rejected": "❌"
            }

            icon = status_icons.get(step['status'], "❓")

            st.markdown(f"""
            <div class="custom-card" style="margin-left: 1rem; border-left-color: {'#28a745' if step['status'] == 'approved' else '#6c757d'};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4 style="margin: 0;">
                            {icon} Step {step['step_number']}: {step['step_name']}
                        </h4>
                        <p style="color: #6c757d; margin: 0.5rem 0 0 0;">
                            Assigned to: User {step['assignee_id']} •
                            Status: {step['status'].upper()}
                        </p>
                    </div>
                    {f'<div style="color: #6c757d; font-size: 0.875rem;">Completed: {format_datetime(step["completed_at"])}</div>' if step['completed_at'] else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)

            if step['status'] == 'in_progress':
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Approve", key=f"approve_step_{step['step_number']}"):
                        st.success("Step approved!")
                with col2:
                    if st.button("❌ Reject", key=f"reject_step_{step['step_number']}"):
                        st.error("Step rejected!")

            st.markdown("<br>", unsafe_allow_html=True)

    st.divider()

    # Create new workflow
    st.markdown("### ➕ Create Workflow")
    if st.button("Create New Workflow", type="primary"):
        st.info("Workflow creation modal would open here")


def render_activity_tab(doc_id: int):
    """Render activity/audit log tab."""
    st.markdown("### 📊 Activity Log")

    # Mock activity log
    activities = [
        {
            "action": "viewed",
            "user_id": 1,
            "created_at": datetime.now() - timedelta(minutes=30),
            "details": "Viewed document"
        },
        {
            "action": "commented",
            "user_id": 2,
            "created_at": datetime.now() - timedelta(hours=1),
            "details": "Added a comment"
        },
        {
            "action": "updated",
            "user_id": 1,
            "created_at": datetime.now() - timedelta(hours=3),
            "details": "Updated document metadata"
        },
        {
            "action": "shared",
            "user_id": 1,
            "created_at": datetime.now() - timedelta(days=1),
            "details": "Shared with User 3"
        },
        {
            "action": "created",
            "user_id": 1,
            "created_at": datetime.now() - timedelta(days=3),
            "details": "Created document"
        }
    ]

    action_icons = {
        "viewed": "👁️",
        "commented": "💬",
        "updated": "✏️",
        "shared": "📤",
        "created": "➕",
        "deleted": "🗑️",
        "downloaded": "⬇️"
    }

    for activity in activities:
        icon = action_icons.get(activity['action'], "❓")

        st.markdown(f"""
        <div class="custom-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>{icon} {activity['action'].title()}</strong>
                    <p style="color: #6c757d; margin: 0.5rem 0 0 0;">
                        User {activity['user_id']} • {activity['details']}
                    </p>
                </div>
                <div style="color: #6c757d; font-size: 0.875rem; text-align: right;">
                    {format_datetime(activity['created_at'])}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)


def render_search_interface():
    """Render search interface with filters."""
    st.markdown("### 🔍 Search Documents")

    col1, col2 = st.columns([3, 1])

    with col1:
        search_query = st.text_input(
            "Search",
            placeholder="Search by title, content, tags...",
            label_visibility="collapsed",
            key="doc_search_query"
        )

    with col2:
        if st.button("Search", type="primary", use_container_width=True):
            if search_query:
                st.session_state.search_results = search_query

    # Filters
    with st.expander("🔧 Filters", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            file_type = st.multiselect("File Type", ["PDF", "Word", "Excel", "Image"])
            date_range = st.date_input("Date Range", value=())

        with col2:
            status = st.multiselect("Status", ["Active", "Draft", "Archived"])
            size_range = st.slider("Size (MB)", 0, 100, (0, 100))

        with col3:
            tags = st.multiselect("Tags", ["Important", "Urgent", "Reviewed"])
            owner = st.text_input("Owner")

    # Search results
    if st.session_state.get('search_results'):
        st.markdown(f"### Results for '{st.session_state.search_results}'")
        st.info("Search results would appear here")


def render_statistics_dashboard():
    """Render statistics dashboard."""
    st.markdown("### 📊 Statistics")

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Documents",
            value="1,234",
            delta="12 today"
        )

    with col2:
        st.metric(
            label="Storage Used",
            value="45.2 GB",
            delta="2.1 GB"
        )

    with col3:
        st.metric(
            label="Active Users",
            value="56",
            delta="8"
        )

    with col4:
        st.metric(
            label="Shared Files",
            value="89",
            delta="-3"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📈 Upload Trends (Last 7 Days)")
        chart_data = pd.DataFrame({
            'Day': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'Uploads': [12, 15, 10, 18, 20, 8, 14]
        })
        st.line_chart(chart_data.set_index('Day'))

    with col2:
        st.markdown("#### 📁 Documents by Type")
        type_data = pd.DataFrame({
            'Type': ['PDF', 'Word', 'Excel', 'Images', 'Other'],
            'Count': [450, 320, 180, 200, 84]
        })
        st.bar_chart(type_data.set_index('Type'))

    st.markdown("<br>", unsafe_allow_html=True)

    # Recent activity
    st.markdown("### 🕐 Recent Activity")
    activity_data = pd.DataFrame({
        'Time': ['10 min ago', '1 hour ago', '2 hours ago', '5 hours ago'],
        'User': ['John Doe', 'Jane Smith', 'Bob Wilson', 'Alice Brown'],
        'Action': ['Uploaded document', 'Shared document', 'Created folder', 'Downloaded document'],
        'Document': ['Q4 Report.pdf', 'Budget.xlsx', 'Projects', 'Invoice.pdf']
    })

    st.dataframe(activity_data, use_container_width=True, hide_index=True)


def render_document_management():
    """Main function to render the document management UI."""
    # Initialize session state
    if 'show_document_details' not in st.session_state:
        st.session_state.show_document_details = False

    # Check if showing document details
    if st.session_state.show_document_details:
        render_document_details()
        return

    # Main layout
    col_sidebar, col_main = st.columns([1, 3])

    with col_sidebar:
        render_folder_tree()

        st.divider()

        # Quick stats
        st.markdown("### 📊 Quick Stats")
        st.metric("Documents", "234")
        st.metric("Folders", "12")
        st.metric("Storage", "15.2 GB")

    with col_main:
        # Action bar
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            search_query = st.text_input(
                "🔍 Search documents...",
                placeholder="Search by name, content, or tags",
                label_visibility="collapsed",
                key="main_search"
            )

        with col2:
            sort_by = st.selectbox(
                "Sort by",
                ["Name", "Date Modified", "Size", "Type"],
                label_visibility="collapsed"
            )

        with col3:
            if st.button("📤 Upload", use_container_width=True, type="primary"):
                st.session_state.show_upload_modal = True

        st.divider()

        # Upload modal
        if st.session_state.get('show_upload_modal', False):
            with st.expander("📤 Upload Files", expanded=True):
                render_file_upload()
                if st.button("✖️ Close Upload"):
                    st.session_state.show_upload_modal = False
                    st.rerun()

        # Breadcrumbs
        st.markdown("""
        <div class="breadcrumb">
            <span class="breadcrumb-item">📁 My Documents</span>
            <span class="breadcrumb-item">Work</span>
        </div>
        """, unsafe_allow_html=True)

        # Mock documents
        mock_documents = [
            {
                "id": 1,
                "title": "Q4 2025 Report.pdf",
                "file_size": 2456000,
                "mime_type": "application/pdf",
                "status": "active",
                "updated_at": datetime.now() - timedelta(hours=2),
                "owner_id": 1,
                "folder_id": 2,
                "view_count": 15,
                "download_count": 3,
                "current_version": 2
            },
            {
                "id": 2,
                "title": "Budget Proposal.xlsx",
                "file_size": 1234000,
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "status": "draft",
                "updated_at": datetime.now() - timedelta(days=1),
                "owner_id": 1,
                "folder_id": 2,
                "view_count": 8,
                "download_count": 1,
                "current_version": 1
            },
            {
                "id": 3,
                "title": "Meeting Notes.docx",
                "file_size": 567000,
                "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "status": "active",
                "updated_at": datetime.now() - timedelta(days=2),
                "owner_id": 2,
                "folder_id": 2,
                "view_count": 22,
                "download_count": 5,
                "current_version": 3
            },
            {
                "id": 4,
                "title": "Presentation.pptx",
                "file_size": 4567000,
                "mime_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "status": "in_review",
                "updated_at": datetime.now() - timedelta(hours=5),
                "owner_id": 1,
                "folder_id": 2,
                "view_count": 12,
                "download_count": 2,
                "current_version": 1
            },
            {
                "id": 5,
                "title": "Image001.png",
                "file_size": 890000,
                "mime_type": "image/png",
                "status": "active",
                "updated_at": datetime.now() - timedelta(days=3),
                "owner_id": 1,
                "folder_id": 2,
                "view_count": 45,
                "download_count": 12,
                "current_version": 1
            },
            {
                "id": 6,
                "title": "Archive.zip",
                "file_size": 15678000,
                "mime_type": "application/zip",
                "status": "archived",
                "updated_at": datetime.now() - timedelta(days=7),
                "owner_id": 1,
                "folder_id": 2,
                "view_count": 5,
                "download_count": 2,
                "current_version": 1
            }
        ]

        # Filter documents based on search
        filtered_docs = mock_documents
        if search_query:
            filtered_docs = [
                doc for doc in mock_documents
                if search_query.lower() in doc['title'].lower()
            ]

        # Document count
        st.markdown(f"**{len(filtered_docs)}** documents")

        st.markdown("<br>", unsafe_allow_html=True)

        # Render documents
        view_mode = st.session_state.get('view_mode', 'grid')

        if view_mode == 'grid':
            render_document_grid(filtered_docs)
        else:
            render_document_list(filtered_docs)

        st.markdown("<br>", unsafe_allow_html=True)

        # Pagination
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            st.markdown("""
            <div style="text-align: center;">
                <button style="margin: 0 0.5rem;">Previous</button>
                <span style="margin: 0 1rem;">Page 1 of 1</span>
                <button style="margin: 0 0.5rem;">Next</button>
            </div>
            """, unsafe_allow_html=True)


# Export main render function
__all__ = ['render_document_management']
