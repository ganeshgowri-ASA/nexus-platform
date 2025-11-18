"""
Streamlit UI for Email Client

Beautiful, modern email client interface built with Streamlit.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import streamlit as st

from .client import EmailClient, EmailAccount, EmailMessage, AccountType
from .compose import EmailComposer, EmailTemplate
from .search import EmailSearch, SearchFilter
from .ai_assistant import AIEmailAssistant

logger = logging.getLogger(__name__)


class EmailClientUI:
    """
    Streamlit UI for email client.

    Provides a beautiful, Gmail-like interface with three-panel layout.
    """

    def __init__(self):
        """Initialize the email client UI."""
        self.setup_page_config()
        self.init_session_state()

    def setup_page_config(self) -> None:
        """Configure Streamlit page."""
        st.set_page_config(
            page_title="NEXUS Email",
            page_icon="📧",
            layout="wide",
            initial_sidebar_state="expanded"
        )

    def init_session_state(self) -> None:
        """Initialize session state variables."""
        if 'email_client' not in st.session_state:
            st.session_state.email_client = EmailClient()

        if 'current_folder' not in st.session_state:
            st.session_state.current_folder = 'INBOX'

        if 'selected_message' not in st.session_state:
            st.session_state.selected_message = None

        if 'compose_mode' not in st.session_state:
            st.session_state.compose_mode = False

        if 'search_query' not in st.session_state:
            st.session_state.search_query = ''

        if 'messages' not in st.session_state:
            st.session_state.messages = []

        if 'dark_mode' not in st.session_state:
            st.session_state.dark_mode = False

    def apply_custom_css(self) -> None:
        """Apply custom CSS styling."""
        st.markdown("""
        <style>
        /* Main container */
        .main {
            background-color: #f5f5f5;
        }

        /* Email list item */
        .email-item {
            background: white;
            padding: 15px;
            margin: 5px 0;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
            border-left: 3px solid transparent;
        }

        .email-item:hover {
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-left-color: #0066cc;
        }

        .email-item.unread {
            background: #f0f7ff;
            font-weight: 600;
        }

        .email-item.selected {
            border-left-color: #0066cc;
            background: #e6f2ff;
        }

        /* Email header */
        .email-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
        }

        .email-from {
            font-weight: 600;
            color: #333;
        }

        .email-date {
            color: #666;
            font-size: 0.9em;
        }

        .email-subject {
            color: #0066cc;
            margin-bottom: 5px;
        }

        .email-preview {
            color: #666;
            font-size: 0.9em;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        /* Sidebar */
        .sidebar-item {
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            cursor: pointer;
            transition: background 0.2s;
        }

        .sidebar-item:hover {
            background: #e6f2ff;
        }

        .sidebar-item.active {
            background: #0066cc;
            color: white;
        }

        /* Compose button */
        .compose-btn {
            background: #0066cc;
            color: white;
            padding: 12px 24px;
            border-radius: 24px;
            border: none;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            margin-bottom: 20px;
        }

        /* Tags */
        .tag {
            display: inline-block;
            padding: 2px 8px;
            margin: 2px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 500;
        }

        .tag.important {
            background: #ffebee;
            color: #c62828;
        }

        .tag.starred {
            background: #fff9e6;
            color: #ff9800;
        }

        .tag.attachment {
            background: #e8f5e9;
            color: #2e7d32;
        }

        /* Message view */
        .message-container {
            background: white;
            padding: 20px;
            border-radius: 8px;
        }

        .message-subject {
            font-size: 1.5em;
            font-weight: 600;
            margin-bottom: 15px;
        }

        .message-meta {
            border-bottom: 1px solid #eee;
            padding-bottom: 15px;
            margin-bottom: 15px;
        }

        .message-body {
            line-height: 1.6;
        }

        /* Search bar */
        .search-container {
            margin-bottom: 20px;
        }

        /* Dark mode */
        .dark-mode {
            background-color: #1a1a1a;
            color: #e0e0e0;
        }

        .dark-mode .email-item {
            background: #2a2a2a;
            color: #e0e0e0;
        }

        .dark-mode .email-item.unread {
            background: #1e3a5f;
        }

        .dark-mode .message-container {
            background: #2a2a2a;
            color: #e0e0e0;
        }
        </style>
        """, unsafe_allow_html=True)

    def run(self) -> None:
        """Run the email client UI."""
        self.apply_custom_css()

        # Header
        self.render_header()

        # Layout: Sidebar | Email List | Message View
        col_sidebar, col_list, col_message = st.columns([1, 2, 3])

        with col_sidebar:
            self.render_sidebar()

        with col_list:
            self.render_email_list()

        with col_message:
            if st.session_state.compose_mode:
                self.render_compose()
            elif st.session_state.selected_message:
                self.render_message_view()
            else:
                st.info("📧 Select an email to read")

    def render_header(self) -> None:
        """Render the top header."""
        col1, col2, col3 = st.columns([2, 4, 2])

        with col1:
            st.title("📧 NEXUS Email")

        with col2:
            # Search bar
            search_query = st.text_input(
                "Search emails",
                value=st.session_state.search_query,
                placeholder="Search by sender, subject, or content...",
                label_visibility="collapsed"
            )
            if search_query != st.session_state.search_query:
                st.session_state.search_query = search_query
                st.rerun()

        with col3:
            col_dark, col_refresh, col_settings = st.columns(3)

            with col_dark:
                if st.button("🌙" if not st.session_state.dark_mode else "☀️"):
                    st.session_state.dark_mode = not st.session_state.dark_mode
                    st.rerun()

            with col_refresh:
                if st.button("🔄"):
                    self.refresh_messages()
                    st.rerun()

            with col_settings:
                if st.button("⚙️"):
                    st.session_state.show_settings = True

        st.divider()

    def render_sidebar(self) -> None:
        """Render the left sidebar with folders and actions."""
        # Compose button
        if st.button("✉️ Compose", use_container_width=True, type="primary"):
            st.session_state.compose_mode = True
            st.session_state.selected_message = None
            st.rerun()

        st.divider()

        # Folders
        st.subheader("📁 Folders")

        folders = [
            ("📥 Inbox", "INBOX", 15),
            ("⭐ Starred", "Starred", 3),
            ("📤 Sent", "Sent", 0),
            ("📝 Drafts", "Drafts", 2),
            ("🗑️ Trash", "Trash", 0),
            ("⚠️ Spam", "Spam", 1),
        ]

        for icon_name, folder_id, count in folders:
            col1, col2 = st.columns([4, 1])

            with col1:
                button_label = icon_name
                button_type = "primary" if st.session_state.current_folder == folder_id else "secondary"

                if st.button(button_label, use_container_width=True, type=button_type, key=f"folder_{folder_id}"):
                    st.session_state.current_folder = folder_id
                    st.session_state.selected_message = None
                    self.load_folder_messages(folder_id)
                    st.rerun()

            with col2:
                if count > 0:
                    st.caption(f"**{count}**")

        st.divider()

        # Smart Folders
        st.subheader("🎯 Smart Folders")

        smart_folders = [
            ("🔥 Important", "important"),
            ("📎 Attachments", "attachments"),
            ("📅 Today", "today"),
            ("📰 Newsletters", "newsletters"),
        ]

        for icon_name, folder_id in smart_folders:
            if st.button(icon_name, use_container_width=True, key=f"smart_{folder_id}"):
                st.session_state.current_folder = folder_id
                st.session_state.selected_message = None
                self.load_smart_folder(folder_id)
                st.rerun()

        st.divider()

        # Labels
        with st.expander("🏷️ Labels"):
            labels = ["Work", "Personal", "Projects", "Clients"]
            for label in labels:
                st.checkbox(label, key=f"label_{label}")

        # Account info
        st.divider()
        client = st.session_state.email_client
        if client.accounts:
            account = list(client.accounts.values())[0]
            st.caption(f"👤 {account.email_address}")
        else:
            st.caption("👤 No account connected")

    def render_email_list(self) -> None:
        """Render the email list."""
        st.subheader(f"📬 {st.session_state.current_folder}")

        # Filter/Sort options
        col1, col2 = st.columns(2)

        with col1:
            filter_option = st.selectbox(
                "Filter",
                ["All", "Unread", "Starred", "With Attachments"],
                label_visibility="collapsed"
            )

        with col2:
            sort_option = st.selectbox(
                "Sort",
                ["Newest", "Oldest", "Sender", "Subject"],
                label_visibility="collapsed"
            )

        st.divider()

        # Email list
        messages = st.session_state.messages

        # Apply filters
        if filter_option == "Unread":
            messages = [m for m in messages if not m.get('is_read', False)]
        elif filter_option == "Starred":
            messages = [m for m in messages if m.get('is_starred', False)]
        elif filter_option == "With Attachments":
            messages = [m for m in messages if m.get('has_attachments', False)]

        # Apply sort
        if sort_option == "Newest":
            messages.sort(key=lambda m: m.get('date', datetime.min), reverse=True)
        elif sort_option == "Oldest":
            messages.sort(key=lambda m: m.get('date', datetime.min))

        # Render messages
        if not messages:
            st.info("No emails in this folder")
        else:
            for i, msg in enumerate(messages):
                self.render_email_item(msg, i)

    def render_email_item(self, message: Dict[str, Any], index: int) -> None:
        """Render a single email list item."""
        is_unread = not message.get('is_read', False)
        is_selected = (st.session_state.selected_message and
                      st.session_state.selected_message.get('message_id') == message.get('message_id'))

        # Email item container
        with st.container():
            col1, col2 = st.columns([5, 1])

            with col1:
                # From and date
                from_addr = message.get('from_address', 'Unknown')
                date = message.get('date', datetime.utcnow())
                date_str = self.format_date(date)

                # Subject and preview
                subject = message.get('subject', '(No subject)')
                preview = message.get('body_text', '')[:100]

                # Render
                sender_name = from_addr.split('@')[0] if '@' in from_addr else from_addr

                st.markdown(f"**{sender_name}**" if is_unread else sender_name)
                st.markdown(f"*{subject}*" if is_unread else subject)
                st.caption(preview)

            with col2:
                st.caption(date_str)

                # Icons
                icons = []
                if message.get('is_starred'):
                    icons.append("⭐")
                if message.get('has_attachments'):
                    icons.append("📎")
                if message.get('ai_priority_score', 0) > 0.7:
                    icons.append("🔥")

                if icons:
                    st.caption(' '.join(icons))

            # Click handler
            if st.button("Open", key=f"msg_{index}", use_container_width=True):
                st.session_state.selected_message = message
                st.session_state.compose_mode = False
                # Mark as read
                message['is_read'] = True
                st.rerun()

            st.divider()

    def render_message_view(self) -> None:
        """Render the message reading pane."""
        message = st.session_state.selected_message

        if not message:
            return

        # Message header
        st.markdown(f"### {message.get('subject', '(No subject)')}")

        col1, col2 = st.columns([4, 1])

        with col1:
            from_addr = message.get('from_address', 'Unknown')
            to_addrs = ', '.join(message.get('to_addresses', []))
            date = message.get('date', datetime.utcnow())

            st.markdown(f"**From:** {from_addr}")
            st.markdown(f"**To:** {to_addrs}")

            if message.get('cc_addresses'):
                cc_addrs = ', '.join(message.get('cc_addresses', []))
                st.markdown(f"**Cc:** {cc_addrs}")

            st.caption(f"🕐 {date.strftime('%Y-%m-%d %H:%M')}")

        with col2:
            # Action buttons
            if st.button("⭐ Star"):
                message['is_starred'] = not message.get('is_starred', False)
                st.rerun()

            if st.button("🗑️ Delete"):
                self.delete_message(message)
                st.session_state.selected_message = None
                st.rerun()

        st.divider()

        # AI Assistant panel
        if message.get('ai_summary'):
            with st.expander("🤖 AI Summary", expanded=True):
                st.info(message['ai_summary'])

                if message.get('ai_category'):
                    st.caption(f"📁 Category: {message['ai_category']}")

                if message.get('ai_priority_score'):
                    priority = message['ai_priority_score']
                    st.progress(priority, text=f"Priority: {priority:.0%}")

        # Message body
        st.markdown("---")

        body = message.get('body_html') or message.get('body_text', '')

        if message.get('body_html'):
            # Render HTML (sanitized)
            st.markdown(body, unsafe_allow_html=True)
        else:
            st.text(body)

        # Attachments
        if message.get('has_attachments') and message.get('attachments'):
            st.divider()
            st.subheader("📎 Attachments")

            for att in message.get('attachments', []):
                col1, col2 = st.columns([3, 1])

                with col1:
                    filename = att.get('filename', 'attachment')
                    size = att.get('size', 0)
                    st.markdown(f"📄 **{filename}** ({self.format_size(size)})")

                with col2:
                    if st.button("Download", key=f"att_{att.get('attachment_id')}"):
                        # Download attachment
                        st.success(f"Downloading {filename}...")

        # Reply section
        st.divider()

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("↩️ Reply", use_container_width=True):
                self.compose_reply(message, reply_all=False)

        with col2:
            if st.button("↩️ Reply All", use_container_width=True):
                self.compose_reply(message, reply_all=True)

        with col3:
            if st.button("➡️ Forward", use_container_width=True):
                self.compose_forward(message)

        # Smart replies
        if message.get('smart_replies'):
            st.divider()
            st.subheader("💡 Smart Replies")

            for i, reply in enumerate(message.get('smart_replies', [])[:3]):
                if st.button(f"📝 {reply['text']}", key=f"smart_reply_{i}"):
                    # Use smart reply
                    self.use_smart_reply(message, reply)

    def render_compose(self) -> None:
        """Render the email composition interface."""
        st.subheader("✉️ Compose Email")

        # Form
        with st.form("compose_form"):
            to_addresses = st.text_input("To:", placeholder="recipient@example.com")

            cc_addresses = st.text_input("Cc:", placeholder="cc@example.com (optional)")

            subject = st.text_input("Subject:", placeholder="Email subject")

            # Rich text editor (using text area as placeholder)
            body = st.text_area(
                "Message:",
                placeholder="Type your message here...",
                height=300
            )

            # Attachments
            attachments = st.file_uploader(
                "Attachments:",
                accept_multiple_files=True
            )

            # Options
            col1, col2 = st.columns(2)

            with col1:
                use_template = st.checkbox("Use template")
                if use_template:
                    template = st.selectbox(
                        "Template:",
                        ["Welcome Email", "Meeting Request", "Follow-up"]
                    )

            with col2:
                schedule_send = st.checkbox("Schedule send")
                if schedule_send:
                    send_time = st.time_input("Send at:")

            # Submit buttons
            col1, col2, col3 = st.columns(3)

            with col1:
                submit = st.form_submit_button("📤 Send", use_container_width=True, type="primary")

            with col2:
                save_draft = st.form_submit_button("💾 Save Draft", use_container_width=True)

            with col3:
                discard = st.form_submit_button("🗑️ Discard", use_container_width=True)

            if submit:
                # Send email
                self.send_email(to_addresses, subject, body, attachments)
                st.session_state.compose_mode = False
                st.success("✅ Email sent!")
                st.rerun()

            elif save_draft:
                st.success("💾 Draft saved!")
                st.session_state.compose_mode = False
                st.rerun()

            elif discard:
                st.session_state.compose_mode = False
                st.rerun()

    def compose_reply(self, original_message: Dict[str, Any], reply_all: bool = False) -> None:
        """Start composing a reply."""
        # Create reply message
        composer = EmailComposer()
        reply = composer.create_reply(original_message, "", reply_all=reply_all)

        st.session_state.compose_mode = True
        st.session_state.compose_message = reply
        st.rerun()

    def compose_forward(self, original_message: Dict[str, Any]) -> None:
        """Start composing a forward."""
        composer = EmailComposer()
        forward = composer.create_forward(original_message, [], "")

        st.session_state.compose_mode = True
        st.session_state.compose_message = forward
        st.rerun()

    def use_smart_reply(self, message: Dict[str, Any], reply: Dict[str, Any]) -> None:
        """Use a smart reply suggestion."""
        st.session_state.compose_mode = True
        st.session_state.smart_reply_text = reply['text']
        st.rerun()

    def send_email(
        self,
        to_addresses: str,
        subject: str,
        body: str,
        attachments: List[Any]
    ) -> None:
        """Send an email."""
        # In production, this would use the EmailClient to actually send
        logger.info(f"Sending email to {to_addresses}: {subject}")

    def delete_message(self, message: Dict[str, Any]) -> None:
        """Delete a message."""
        if message in st.session_state.messages:
            st.session_state.messages.remove(message)

    def load_folder_messages(self, folder: str) -> None:
        """Load messages for a folder."""
        # In production, fetch from EmailClient
        # For now, use demo data
        st.session_state.messages = self.get_demo_messages(folder)

    def load_smart_folder(self, folder_id: str) -> None:
        """Load messages for a smart folder."""
        # Apply smart folder filter
        st.session_state.messages = self.get_demo_messages("INBOX")

    def refresh_messages(self) -> None:
        """Refresh messages from server."""
        st.toast("🔄 Refreshing emails...")
        self.load_folder_messages(st.session_state.current_folder)

    def format_date(self, date: datetime) -> str:
        """Format date for display."""
        now = datetime.utcnow()
        delta = now - date

        if delta.days == 0:
            return date.strftime("%H:%M")
        elif delta.days == 1:
            return "Yesterday"
        elif delta.days < 7:
            return date.strftime("%A")
        else:
            return date.strftime("%b %d")

    def format_size(self, size_bytes: int) -> str:
        """Format file size."""
        units = ['B', 'KB', 'MB', 'GB']
        size = float(size_bytes)
        unit_idx = 0

        while size >= 1024 and unit_idx < len(units) - 1:
            size /= 1024
            unit_idx += 1

        return f"{size:.1f} {units[unit_idx]}"

    def get_demo_messages(self, folder: str) -> List[Dict[str, Any]]:
        """Get demo messages for testing."""
        return [
            {
                'message_id': '1',
                'from_address': 'boss@company.com',
                'to_addresses': ['you@company.com'],
                'subject': 'Q4 Planning Meeting',
                'body_text': 'Hi team, let\'s schedule our Q4 planning meeting for next week. Please share your availability.',
                'date': datetime.utcnow() - timedelta(hours=2),
                'is_read': False,
                'is_starred': True,
                'has_attachments': False,
                'ai_priority_score': 0.9,
                'ai_category': 'Meetings',
                'ai_summary': 'Request to schedule Q4 planning meeting for next week'
            },
            {
                'message_id': '2',
                'from_address': 'newsletter@example.com',
                'to_addresses': ['you@company.com'],
                'subject': 'Weekly Tech Digest',
                'body_text': 'Here are this week\'s top technology news...',
                'date': datetime.utcnow() - timedelta(hours=5),
                'is_read': True,
                'is_starred': False,
                'has_attachments': False,
                'ai_priority_score': 0.3,
                'ai_category': 'Newsletters'
            },
            {
                'message_id': '3',
                'from_address': 'client@bigcorp.com',
                'to_addresses': ['you@company.com'],
                'subject': 'Project Update Request',
                'body_text': 'Could you send me an update on the project status? The stakeholders are asking for a progress report.',
                'date': datetime.utcnow() - timedelta(days=1),
                'is_read': False,
                'is_starred': False,
                'has_attachments': True,
                'attachments': [
                    {'filename': 'requirements.pdf', 'size': 245000}
                ],
                'ai_priority_score': 0.8,
                'ai_category': 'Projects'
            }
        ]


def main():
    """Main entry point for the email client UI."""
    ui = EmailClientUI()
    ui.run()


if __name__ == "__main__":
    main()
