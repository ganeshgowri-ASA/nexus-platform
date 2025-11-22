"""
Streamlit UI - Beautiful chat interface for NEXUS.

Provides a complete chat experience with:
- Channel sidebar
- Message feed
- Compose box
- File uploads
- Emoji picker
- User profiles
- Settings
"""

import streamlit as st
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4
import asyncio

# Import chat components
try:
    from .chat_engine import ChatEngine
    from .models import (
        User, Message, Channel, ChannelType, UserStatus,
        MessageType, CreateChannelRequest, SendMessageRequest
    )
except ImportError:
    # Fallback for direct execution
    pass


# Page configuration
def configure_page():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="NEXUS Chat",
        page_icon="💬",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for beautiful UI
    st.markdown("""
        <style>
        /* Main chat area */
        .main-chat {
            background-color: #f5f5f5;
            border-radius: 10px;
            padding: 20px;
            height: 70vh;
            overflow-y: auto;
        }

        /* Message bubble */
        .message-bubble {
            background-color: white;
            border-radius: 15px;
            padding: 12px 16px;
            margin: 8px 0;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            max-width: 70%;
        }

        .message-bubble.own {
            background-color: #0084ff;
            color: white;
            margin-left: auto;
        }

        /* Channel item */
        .channel-item {
            padding: 12px;
            border-radius: 8px;
            margin: 4px 0;
            cursor: pointer;
            transition: background-color 0.2s;
        }

        .channel-item:hover {
            background-color: #e8e8e8;
        }

        .channel-item.active {
            background-color: #0084ff;
            color: white;
        }

        /* Compose box */
        .compose-box {
            background-color: white;
            border-radius: 25px;
            padding: 10px 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        /* User avatar */
        .user-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background-color: #0084ff;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }

        /* Online indicator */
        .online-indicator {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background-color: #44b700;
            display: inline-block;
        }

        /* Unread badge */
        .unread-badge {
            background-color: #ff3b30;
            color: white;
            border-radius: 10px;
            padding: 2px 6px;
            font-size: 12px;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)


# Initialize session state
def init_session_state():
    """Initialize Streamlit session state."""
    if 'engine' not in st.session_state:
        st.session_state.engine = None

    if 'current_user' not in st.session_state:
        st.session_state.current_user = User(
            id=uuid4(),
            username="demo_user",
            email="demo@nexus.com",
            display_name="Demo User",
            status=UserStatus.ONLINE
        )

    if 'current_channel' not in st.session_state:
        st.session_state.current_channel = None

    if 'messages' not in st.session_state:
        st.session_state.messages = []

    if 'channels' not in st.session_state:
        st.session_state.channels = []

    if 'show_emoji_picker' not in st.session_state:
        st.session_state.show_emoji_picker = False

    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False


def render_sidebar():
    """Render left sidebar with channels and DMs."""
    with st.sidebar:
        st.title("💬 NEXUS Chat")

        # User profile section
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(
                f'<div class="user-avatar">{st.session_state.current_user.display_name[0]}</div>',
                unsafe_allow_html=True
            )
        with col2:
            st.write(f"**{st.session_state.current_user.display_name}**")
            status_emoji = "🟢" if st.session_state.current_user.status == UserStatus.ONLINE else "⚫"
            st.caption(f"{status_emoji} {st.session_state.current_user.status.value}")

        st.divider()

        # Search
        search_query = st.text_input("🔍 Search messages", placeholder="Search...")

        st.divider()

        # Channel tabs
        tab1, tab2, tab3 = st.tabs(["Channels", "DMs", "Settings"])

        with tab1:
            render_channels()

        with tab2:
            render_dms()

        with tab3:
            render_settings()


def render_channels():
    """Render channels list."""
    st.subheader("Channels")

    # Create channel button
    if st.button("➕ Create Channel", use_container_width=True):
        st.session_state.show_create_channel = True

    # Channel list
    if st.session_state.channels:
        for channel in st.session_state.channels:
            channel_icon = "🔒" if channel.channel_type == ChannelType.PRIVATE else "#"

            col1, col2 = st.columns([4, 1])

            with col1:
                if st.button(
                    f"{channel_icon} {channel.name}",
                    key=f"channel_{channel.id}",
                    use_container_width=True
                ):
                    st.session_state.current_channel = channel
                    st.rerun()

            with col2:
                # Unread count
                st.markdown('<span class="unread-badge">3</span>', unsafe_allow_html=True)
    else:
        st.info("No channels yet. Create one to get started!")


def render_dms():
    """Render direct messages list."""
    st.subheader("Direct Messages")

    # Mock DM list
    dms = [
        {"user": "Alice", "last_msg": "Hey, how are you?", "unread": 2},
        {"user": "Bob", "last_msg": "Check this out!", "unread": 0},
        {"user": "Carol", "last_msg": "Meeting at 3pm", "unread": 1},
    ]

    for dm in dms:
        col1, col2 = st.columns([4, 1])

        with col1:
            st.button(
                f"👤 {dm['user']}",
                key=f"dm_{dm['user']}",
                use_container_width=True
            )
            st.caption(dm['last_msg'])

        with col2:
            if dm['unread'] > 0:
                st.markdown(
                    f'<span class="unread-badge">{dm["unread"]}</span>',
                    unsafe_allow_html=True
                )


def render_settings():
    """Render settings panel."""
    st.subheader("Settings")

    # Notification settings
    st.checkbox("🔔 Enable notifications", value=True)
    st.checkbox("🔕 Do Not Disturb", value=False)
    st.checkbox("📧 Email notifications", value=True)

    st.divider()

    # Appearance
    st.session_state.dark_mode = st.checkbox("🌙 Dark mode", value=st.session_state.dark_mode)

    st.divider()

    # AI Features
    st.checkbox("🤖 AI Smart Replies", value=True)
    st.checkbox("🌍 Auto-translate", value=False)

    st.divider()

    # Profile
    if st.button("👤 Edit Profile", use_container_width=True):
        pass

    if st.button("🚪 Logout", use_container_width=True):
        pass


def render_main_chat():
    """Render main chat area."""
    if not st.session_state.current_channel:
        st.info("👋 Welcome to NEXUS Chat! Select a channel to start messaging.")
        return

    # Channel header
    render_channel_header()

    # Messages area
    render_messages()

    # Compose box
    render_compose_box()


def render_channel_header():
    """Render channel header."""
    channel = st.session_state.current_channel

    col1, col2, col3 = st.columns([6, 1, 1])

    with col1:
        st.title(f"# {channel.name}")
        if channel.description:
            st.caption(channel.description)

    with col2:
        if st.button("👥 Members"):
            st.session_state.show_members = True

    with col3:
        if st.button("⚙️ Settings"):
            st.session_state.show_channel_settings = True

    st.divider()


def render_messages():
    """Render message feed."""
    # Mock messages for demo
    messages = [
        {
            "id": "1",
            "user": "Alice",
            "content": "Hey everyone! How's the project going?",
            "timestamp": "10:30 AM",
            "is_own": False,
            "reactions": ["👍", "❤️"]
        },
        {
            "id": "2",
            "user": "Demo User",
            "content": "Going great! Just finished the chat module.",
            "timestamp": "10:32 AM",
            "is_own": True,
            "reactions": ["🎉", "💯"]
        },
        {
            "id": "3",
            "user": "Bob",
            "content": "Awesome work! Can't wait to try it out.",
            "timestamp": "10:35 AM",
            "is_own": False,
            "reactions": ["👏"]
        }
    ]

    # Message container
    message_container = st.container()

    with message_container:
        for msg in messages:
            render_message(msg)


def render_message(msg: dict):
    """Render a single message."""
    # Message alignment based on sender
    if msg['is_own']:
        col1, col2 = st.columns([1, 3])
        with col2:
            render_message_bubble(msg, is_own=True)
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            render_message_bubble(msg, is_own=False)


def render_message_bubble(msg: dict, is_own: bool):
    """Render message bubble."""
    bubble_class = "own" if is_own else ""

    # User and timestamp
    if not is_own:
        st.caption(f"**{msg['user']}** • {msg['timestamp']}")

    # Message content
    st.markdown(
        f'<div class="message-bubble {bubble_class}">{msg["content"]}</div>',
        unsafe_allow_html=True
    )

    # Reactions
    if msg.get('reactions'):
        reaction_str = " ".join(msg['reactions'])
        st.caption(reaction_str)

    # Message actions
    col1, col2, col3, col4 = st.columns([1, 1, 1, 5])

    with col1:
        if st.button("😀", key=f"react_{msg['id']}", help="Add reaction"):
            pass

    with col2:
        if st.button("💬", key=f"reply_{msg['id']}", help="Reply"):
            pass

    with col3:
        if st.button("⋯", key=f"more_{msg['id']}", help="More options"):
            pass


def render_compose_box():
    """Render message compose box."""
    st.divider()

    # File upload
    uploaded_file = st.file_uploader(
        "📎 Attach file",
        type=['png', 'jpg', 'pdf', 'doc', 'txt'],
        key="file_upload"
    )

    # Message input
    col1, col2, col3 = st.columns([6, 1, 1])

    with col1:
        message_input = st.text_area(
            "Type a message...",
            key="message_input",
            height=100,
            placeholder="Type your message here... (Shift+Enter for new line)"
        )

    with col2:
        if st.button("😀", help="Emoji picker"):
            st.session_state.show_emoji_picker = not st.session_state.show_emoji_picker

    with col3:
        if st.button("📤", help="Send message", type="primary"):
            if message_input:
                # Send message logic here
                st.success("Message sent!")
                st.rerun()

    # Emoji picker
    if st.session_state.show_emoji_picker:
        render_emoji_picker()

    # AI Smart replies
    if message_input:
        with st.expander("🤖 AI Smart Replies"):
            st.button("Thanks for the update!")
            st.button("Sounds good to me.")
            st.button("I'll look into it.")


def render_emoji_picker():
    """Render emoji picker."""
    st.subheader("Select Emoji")

    emoji_categories = {
        "Smileys": ["😀", "😃", "😄", "😁", "😅", "😂", "🤣", "😊", "😇"],
        "Gestures": ["👍", "👎", "👏", "🙌", "👋", "🤝", "💪", "🙏"],
        "Hearts": ["❤️", "💙", "💚", "💛", "🧡", "💜", "🖤", "💕"],
        "Objects": ["🎉", "🎊", "🎈", "🎁", "⭐", "✨", "🔥", "💯"],
    }

    for category, emojis in emoji_categories.items():
        st.caption(category)
        cols = st.columns(9)
        for i, emoji in enumerate(emojis):
            with cols[i]:
                if st.button(emoji, key=f"emoji_{emoji}"):
                    # Add emoji to message
                    pass


def render_right_sidebar():
    """Render right sidebar with members/info."""
    with st.sidebar:
        st.subheader("Channel Members")

        # Mock members
        members = [
            {"name": "Alice", "status": "online"},
            {"name": "Bob", "status": "online"},
            {"name": "Carol", "status": "away"},
            {"name": "Dave", "status": "offline"},
        ]

        for member in members:
            status_emoji = {
                "online": "🟢",
                "away": "🟡",
                "offline": "⚫"
            }.get(member['status'], "⚫")

            st.write(f"{status_emoji} **{member['name']}**")

        st.divider()

        # Channel info
        st.subheader("Channel Info")

        if st.session_state.current_channel:
            channel = st.session_state.current_channel

            st.write(f"**Name:** {channel.name}")
            st.write(f"**Type:** {channel.channel_type.value}")
            st.write(f"**Members:** {channel.member_count}")

            if channel.description:
                st.write(f"**Description:** {channel.description}")

            st.divider()

            # Channel actions
            if st.button("📌 Pinned Messages", use_container_width=True):
                pass

            if st.button("📁 Files & Media", use_container_width=True):
                pass

            if st.button("🔍 Search in Channel", use_container_width=True):
                pass


def render_create_channel_modal():
    """Render create channel modal."""
    with st.form("create_channel_form"):
        st.subheader("Create New Channel")

        name = st.text_input("Channel Name *")
        description = st.text_area("Description")

        channel_type = st.selectbox(
            "Channel Type",
            options=[ChannelType.PUBLIC, ChannelType.PRIVATE],
            format_func=lambda x: "Public" if x == ChannelType.PUBLIC else "Private"
        )

        # Member selection (mock)
        members = st.multiselect(
            "Add Members",
            options=["Alice", "Bob", "Carol", "Dave"]
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.form_submit_button("Create", type="primary", use_container_width=True):
                if name:
                    # Create channel logic
                    st.success(f"Channel '{name}' created!")
                    st.session_state.show_create_channel = False
                    st.rerun()
                else:
                    st.error("Please enter a channel name")

        with col2:
            if st.form_submit_button("Cancel", use_container_width=True):
                st.session_state.show_create_channel = False
                st.rerun()


def main():
    """Main application entry point."""
    configure_page()
    init_session_state()

    # Layout
    render_sidebar()

    # Main content area
    col1, col2 = st.columns([3, 1])

    with col1:
        render_main_chat()

    with col2:
        render_right_sidebar()

    # Modals
    if st.session_state.get('show_create_channel'):
        render_create_channel_modal()


# Run the app
if __name__ == "__main__":
    main()
