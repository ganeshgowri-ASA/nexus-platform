"""
Sidebar Component

Renders the sidebar with document tree, AI assistant, and other features.
"""

import streamlit as st
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime


def render_sidebar(
    current_doc_id: Optional[str] = None,
    on_document_select: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    Render the main sidebar.

    Args:
        current_doc_id: Currently active document ID
        on_document_select: Callback when document is selected

    Returns:
        Dictionary containing sidebar actions
    """
    actions = {}

    with st.sidebar:
        st.title("📝 Word Editor")

        # Document management section
        st.markdown("### 📂 Documents")

        if st.button("➕ New Document", use_container_width=True):
            actions['new_document'] = True

        if st.button("📁 Browse Documents", use_container_width=True):
            actions['browse_documents'] = True

        st.markdown("---")

        # Recent documents
        render_recent_documents(current_doc_id, on_document_select)

        st.markdown("---")

        # Templates section
        render_templates_section()

        st.markdown("---")

        # Settings and options
        render_settings_section()

    return actions


def render_recent_documents(
    current_doc_id: Optional[str] = None,
    on_select: Optional[Callable] = None
) -> None:
    """
    Render recent documents list.

    Args:
        current_doc_id: Currently active document ID
        on_select: Callback when document is selected
    """
    with st.expander("📋 Recent Documents", expanded=True):
        # In production, load from database
        recent_docs = [
            {"id": "doc1", "title": "Project Proposal", "modified": "2 hours ago"},
            {"id": "doc2", "title": "Meeting Notes", "modified": "Yesterday"},
            {"id": "doc3", "title": "Technical Report", "modified": "3 days ago"},
        ]

        if not recent_docs:
            st.info("No recent documents")
        else:
            for doc in recent_docs:
                is_current = doc['id'] == current_doc_id

                col1, col2 = st.columns([4, 1])

                with col1:
                    label = f"**{doc['title']}**" if is_current else doc['title']
                    if st.button(
                        label,
                        key=f"doc_{doc['id']}",
                        use_container_width=True,
                        type="primary" if is_current else "secondary"
                    ):
                        if on_select:
                            on_select(doc['id'])

                with col2:
                    st.caption(doc['modified'])


def render_templates_section() -> Optional[str]:
    """
    Render templates section.

    Returns:
        Selected template ID or None
    """
    with st.expander("📄 Templates", expanded=False):
        st.markdown("Start with a template:")

        templates = {
            "Business Letter": "business_letter",
            "Resume / CV": "resume",
            "Report": "report",
            "Proposal": "proposal",
            "Meeting Notes": "meeting_notes",
            "Essay": "essay",
            "Invoice": "invoice",
            "Blog Post": "blog_post",
            "Technical Doc": "technical_doc",
        }

        for name, template_id in templates.items():
            if st.button(name, key=f"template_{template_id}", use_container_width=True):
                return template_id

    return None


def render_settings_section() -> Dict[str, Any]:
    """
    Render settings section.

    Returns:
        Dictionary of settings
    """
    settings = {}

    with st.expander("⚙️ Settings", expanded=False):
        # Auto-save settings
        auto_save = st.checkbox("Enable Auto-save", value=True, key="auto_save")
        settings['auto_save'] = auto_save

        if auto_save:
            interval = st.slider(
                "Auto-save interval (seconds)",
                min_value=10,
                max_value=300,
                value=30,
                step=10,
                key="auto_save_interval"
            )
            settings['auto_save_interval'] = interval

        # Display settings
        st.markdown("**Display**")
        dark_mode = st.checkbox("Dark Mode", value=False, key="dark_mode")
        settings['dark_mode'] = dark_mode

        show_line_numbers = st.checkbox("Show Line Numbers", value=False, key="line_numbers")
        settings['show_line_numbers'] = show_line_numbers

        # Collaboration settings
        st.markdown("**Collaboration**")
        track_changes = st.checkbox("Track Changes", value=False, key="track_changes")
        settings['track_changes'] = track_changes

        show_cursors = st.checkbox("Show User Cursors", value=True, key="show_cursors")
        settings['show_cursors'] = show_cursors

    return settings


def render_ai_assistant_sidebar() -> Dict[str, Any]:
    """
    Render AI assistant sidebar.

    Returns:
        Dictionary containing AI actions
    """
    actions = {}

    st.markdown("### ✨ AI Writing Assistant")

    # AI feature selector
    feature = st.selectbox(
        "Select AI Feature",
        [
            "Autocomplete",
            "Grammar Check",
            "Spell Check",
            "Style Suggestions",
            "Tone Adjustment",
            "Summarize",
            "Expand Text",
            "Shorten Text",
            "Rewrite",
            "Translate",
            "Continue Writing",
        ],
        key="ai_feature"
    )

    # Feature-specific options
    if feature == "Tone Adjustment":
        tone = st.selectbox(
            "Target Tone",
            ["Formal", "Casual", "Friendly", "Professional", "Academic", "Creative"],
            key="target_tone"
        )
        actions['tone'] = tone

    elif feature == "Translate":
        language = st.selectbox(
            "Target Language",
            [
                "Spanish", "French", "German", "Italian", "Portuguese",
                "Chinese", "Japanese", "Korean", "Arabic", "Russian"
            ],
            key="target_language"
        )
        actions['language'] = language

    elif feature in ["Expand Text", "Shorten Text", "Summarize"]:
        target_length = st.number_input(
            "Target Word Count",
            min_value=10,
            max_value=5000,
            value=200,
            step=50,
            key="target_length"
        )
        actions['target_length'] = target_length

    # Apply button
    if st.button(f"Apply {feature}", key="apply_ai", use_container_width=True):
        actions['feature'] = feature
        actions['apply'] = True

    # AI suggestions display
    if 'ai_suggestions' in st.session_state:
        st.markdown("---")
        st.markdown("**Suggestions:**")

        for i, suggestion in enumerate(st.session_state.ai_suggestions):
            with st.expander(f"Suggestion {i + 1}", expanded=i == 0):
                st.write(suggestion.get('text', ''))

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("✅ Accept", key=f"accept_{i}"):
                        actions['accept_suggestion'] = i

                with col2:
                    if st.button("❌ Reject", key=f"reject_{i}"):
                        actions['reject_suggestion'] = i

    return actions


def render_comments_sidebar(comments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Render comments and suggestions sidebar.

    Args:
        comments: List of document comments

    Returns:
        Dictionary containing comment actions
    """
    actions = {}

    st.markdown("### 💬 Comments")

    if st.button("➕ Add Comment", key="add_comment_btn", use_container_width=True):
        actions['add_comment'] = True

    st.markdown("---")

    if not comments:
        st.info("No comments yet")
    else:
        for comment in comments:
            render_comment(comment, actions)

    return actions


def render_comment(comment: Dict[str, Any], actions: Dict[str, Any]) -> None:
    """
    Render a single comment.

    Args:
        comment: Comment data
        actions: Actions dictionary to update
    """
    with st.container():
        # Comment header
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"**{comment.get('author_name', 'Unknown')}**")

        with col2:
            st.caption(comment.get('created_at', ''))

        # Comment content
        st.write(comment.get('content', ''))

        # Comment actions
        action_cols = st.columns(3)

        with action_cols[0]:
            if st.button("💬 Reply", key=f"reply_{comment['comment_id']}"):
                actions[f"reply_{comment['comment_id']}"] = True

        with action_cols[1]:
            if st.button("✅ Resolve", key=f"resolve_{comment['comment_id']}"):
                actions[f"resolve_{comment['comment_id']}"] = True

        with action_cols[2]:
            if st.button("🗑️ Delete", key=f"delete_{comment['comment_id']}"):
                actions[f"delete_{comment['comment_id']}"] = True

        # Replies
        if comment.get('replies'):
            with st.expander(f"View {len(comment['replies'])} replies"):
                for reply in comment['replies']:
                    st.markdown(f"**{reply.get('author_name', 'Unknown')}:** {reply.get('content', '')}")
                    st.caption(reply.get('created_at', ''))

        st.markdown("---")


def render_version_history_sidebar(versions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Render version history sidebar.

    Args:
        versions: List of document versions

    Returns:
        Dictionary containing version actions
    """
    actions = {}

    st.markdown("### 🕐 Version History")

    if not versions:
        st.info("No version history")
    else:
        for version in versions:
            with st.container():
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"**Version {version.get('version_number', 0)}**")
                    st.caption(version.get('description', 'No description'))

                with col2:
                    st.caption(version.get('created_at', ''))

                if st.button(
                    "Restore",
                    key=f"restore_{version.get('version_id')}",
                    use_container_width=True
                ):
                    actions['restore_version'] = version.get('version_number')

                st.markdown("---")

    return actions


def render_collaboration_sidebar(active_users: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Render collaboration sidebar.

    Args:
        active_users: List of active users

    Returns:
        Dictionary containing collaboration actions
    """
    actions = {}

    st.markdown("### 👥 Collaboration")

    # Share button
    if st.button("🔗 Share Document", key="share_btn", use_container_width=True):
        actions['share_document'] = True

    st.markdown("---")

    # Active users
    st.markdown("**Active Users:**")

    if not active_users:
        st.info("No active users")
    else:
        for user in active_users:
            color = user.get('avatar_color', '#000000')
            username = user.get('username', 'Unknown')

            st.markdown(
                f'<span style="color: {color}; font-weight: bold; font-size: 18px;">●</span> {username}',
                unsafe_allow_html=True
            )

    st.markdown("---")

    # Permissions
    st.markdown("**Permissions:**")

    permission = st.selectbox(
        "Default Permission",
        ["View", "Comment", "Edit"],
        key="default_permission"
    )
    actions['default_permission'] = permission

    # Public link
    public_link = st.checkbox("Allow public access", value=False, key="public_link")
    actions['public_link'] = public_link

    if public_link:
        st.text_input(
            "Public Link",
            value="https://nexus.app/doc/[doc_id]",
            key="public_link_url",
            disabled=True
        )

        if st.button("📋 Copy Link", key="copy_link"):
            st.success("Link copied to clipboard!")

    return actions


def render_document_info_sidebar(metadata: Dict[str, Any]) -> None:
    """
    Render document information sidebar.

    Args:
        metadata: Document metadata
    """
    st.markdown("### ℹ️ Document Info")

    with st.expander("Details", expanded=True):
        st.markdown(f"**Title:** {metadata.get('title', 'Untitled')}")
        st.markdown(f"**Author:** {metadata.get('author', 'Unknown')}")
        st.markdown(f"**Created:** {metadata.get('created_at', 'Unknown')}")
        st.markdown(f"**Modified:** {metadata.get('modified_at', 'Unknown')}")
        st.markdown(f"**Version:** {metadata.get('version', 1)}")

        # Tags
        st.markdown("**Tags:**")
        tags = metadata.get('tags', [])

        if tags:
            tag_string = ", ".join(tags)
            st.write(tag_string)
        else:
            st.info("No tags")

        # Description
        st.markdown("**Description:**")
        description = metadata.get('description', '')

        if description:
            st.write(description)
        else:
            st.info("No description")

    # Edit metadata button
    if st.button("✏️ Edit Metadata", key="edit_metadata", use_container_width=True):
        st.session_state.edit_metadata_modal = True
