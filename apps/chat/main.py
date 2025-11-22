"""Chat / Real-time Messaging Application"""
import streamlit as st
from datetime import datetime

# Lazy imports
SessionLocal = None
ChatRoom = None
ChatMessage = None
settings = None
CHAT_ROOM_TYPES = None
format_relative_time = None


def _lazy_imports():
    """Import all dependencies lazily"""
    global SessionLocal, ChatRoom, ChatMessage, settings, CHAT_ROOM_TYPES, format_relative_time

    from database import init_database, get_session
    from database.models import ChatRoom as _ChatRoom, ChatMessage as _ChatMessage
    from config.settings import settings as _settings
    from config.constants import CHAT_ROOM_TYPES as _CHAT_ROOM_TYPES
    from utils.formatters import format_relative_time as _format_relative_time

    SessionLocal = get_session
    ChatRoom = _ChatRoom
    ChatMessage = _ChatMessage
    settings = _settings
    CHAT_ROOM_TYPES = _CHAT_ROOM_TYPES
    format_relative_time = _format_relative_time

    init_database()
    return get_session

def initialize_session_state():
    """Initialize session state variables"""
    if 'current_room' not in st.session_state:
        st.session_state.current_room = None
    if 'current_user' not in st.session_state:
        st.session_state.current_user = "User"  # In production, use actual auth
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = False

def render_sidebar():
    """Render sidebar with room list"""
    st.sidebar.title("💬 Chat")

    # Current user
    st.sidebar.text_input("Username", value=st.session_state.current_user, key="username_input",
                         on_change=lambda: setattr(st.session_state, 'current_user',
                                                  st.session_state.username_input))

    st.sidebar.divider()

    # New room button
    with st.sidebar.expander("➕ Create Room"):
        room_name = st.text_input("Room Name")
        room_type = st.selectbox("Room Type", CHAT_ROOM_TYPES)
        room_description = st.text_area("Description", height=80)

        if st.button("Create", type="primary"):
            if room_name:
                db = SessionLocal()
                room = ChatRoom(
                    name=room_name,
                    room_type=room_type,
                    description=room_description,
                    members=[st.session_state.current_user]
                )
                db.add(room)
                db.commit()
                st.session_state.current_room = room.id
                db.close()
                st.rerun()
            else:
                st.error("Please enter a room name")

    st.sidebar.divider()

    # List rooms
    st.sidebar.subheader("Rooms")

    db = SessionLocal()
    rooms = db.query(ChatRoom).filter(ChatRoom.is_active == True).order_by(ChatRoom.updated_at.desc()).all()

    for room in rooms:
        # Get unread count (simplified)
        message_count = db.query(ChatMessage).filter(ChatMessage.room_id == room.id).count()

        col1, col2 = st.sidebar.columns([4, 1])
        with col1:
            room_icon = "🔒" if room.room_type == "Direct Message" else "👥"
            if st.button(f"{room_icon} {room.name}", key=f"room_{room.id}", use_container_width=True):
                st.session_state.current_room = room.id
                st.rerun()
        with col2:
            if message_count > 0:
                st.caption(f"{message_count}")

    db.close()

    st.sidebar.divider()

    # Auto-refresh toggle
    st.sidebar.checkbox("🔄 Auto-refresh", value=st.session_state.auto_refresh,
                       key="auto_refresh_toggle",
                       on_change=lambda: setattr(st.session_state, 'auto_refresh',
                                                st.session_state.auto_refresh_toggle))

def render_chat_room(db, room_id):
    """Render chat room view"""
    room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()

    if not room:
        st.error("Room not found")
        return

    # Room header
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        st.subheader(f"💬 {room.name}")
        if room.description:
            st.caption(room.description)

    with col2:
        st.caption(f"{len(room.members or [])} members")

    with col3:
        if st.button("⚙️ Settings"):
            st.session_state.show_room_settings = True

    # Room settings (in expander)
    if hasattr(st.session_state, 'show_room_settings') and st.session_state.show_room_settings:
        with st.expander("Room Settings", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                new_name = st.text_input("Room Name", value=room.name)
                new_description = st.text_area("Description", value=room.description or "")

            with col2:
                new_type = st.selectbox("Room Type", CHAT_ROOM_TYPES,
                                       index=CHAT_ROOM_TYPES.index(room.room_type))

                members_input = st.text_area("Members (one per line)",
                                            value='\n'.join(room.members or []))

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save Changes"):
                    room.name = new_name
                    room.description = new_description
                    room.room_type = new_type
                    room.members = [m.strip() for m in members_input.split('\n') if m.strip()]
                    db.commit()
                    st.success("Room updated!")
                    st.session_state.show_room_settings = False
                    st.rerun()

            with col2:
                if st.button("Delete Room", type="secondary"):
                    db.query(ChatMessage).filter(ChatMessage.room_id == room.id).delete()
                    db.delete(room)
                    db.commit()
                    st.session_state.current_room = None
                    st.session_state.show_room_settings = False
                    st.rerun()

    st.divider()

    # Messages container
    messages_container = st.container()

    with messages_container:
        # Get messages
        messages = db.query(ChatMessage).filter(
            ChatMessage.room_id == room_id,
            ChatMessage.is_deleted == False
        ).order_by(ChatMessage.created_at.asc()).all()

        if messages:
            for msg in messages:
                # Message bubble
                is_own_message = msg.sender == st.session_state.current_user

                with st.container():
                    col1, col2 = st.columns([1, 5]) if is_own_message else st.columns([5, 1])

                    if not is_own_message:
                        with col1:
                            # Message content
                            st.markdown(f"**{msg.sender}**")
                            st.write(msg.message)

                            # Attachments
                            if msg.attachments:
                                for attachment in msg.attachments:
                                    st.caption(f"📎 {attachment}")

                            # Reactions
                            if msg.reactions:
                                reaction_text = " ".join([f"{emoji} {len(users)}"
                                                        for emoji, users in msg.reactions.items()])
                                st.caption(reaction_text)

                            st.caption(format_relative_time(msg.created_at))
                    else:
                        with col1:
                            # Right-aligned message
                            st.markdown(f"<div style='text-align: right'><b>{msg.sender}</b></div>",
                                      unsafe_allow_html=True)
                            st.markdown(f"<div style='text-align: right'>{msg.message}</div>",
                                      unsafe_allow_html=True)

                            # Attachments
                            if msg.attachments:
                                for attachment in msg.attachments:
                                    st.caption(f"📎 {attachment}")

                            # Reactions
                            if msg.reactions:
                                reaction_text = " ".join([f"{emoji} {len(users)}"
                                                        for emoji, users in msg.reactions.items()])
                                st.caption(reaction_text)

                            st.caption(format_relative_time(msg.created_at))

                    # Message actions
                    col_react, col_edit, col_delete = st.columns(3)

                    with col_react:
                        emoji_options = ["👍", "❤️", "😂", "😮", "😢", "🎉"]
                        selected_emoji = st.selectbox("React", [""] + emoji_options,
                                                     key=f"react_{msg.id}",
                                                     label_visibility="collapsed")
                        if selected_emoji:
                            reactions = msg.reactions or {}
                            if selected_emoji not in reactions:
                                reactions[selected_emoji] = []
                            if st.session_state.current_user not in reactions[selected_emoji]:
                                reactions[selected_emoji].append(st.session_state.current_user)
                            msg.reactions = reactions
                            db.commit()
                            st.rerun()

                    if is_own_message:
                        with col_edit:
                            if st.button("✏️", key=f"edit_{msg.id}"):
                                st.session_state.editing_message = msg.id

                        with col_delete:
                            if st.button("🗑️", key=f"del_msg_{msg.id}"):
                                msg.is_deleted = True
                                db.commit()
                                st.rerun()

                    st.divider()
        else:
            st.info("No messages yet. Start the conversation!")

    # Message input
    st.divider()

    col1, col2, col3 = st.columns([5, 1, 1])

    with col1:
        message_input = st.text_area("Message", height=100, key="message_input",
                                    placeholder="Type your message...")

    with col2:
        st.write("") # Spacing
        st.write("") # Spacing
        # Emoji picker
        common_emojis = ["😀", "😂", "❤️", "👍", "🎉", "🔥", "💯", "✨"]
        emoji_expander = st.expander("😀")
        with emoji_expander:
            for emoji in common_emojis:
                if st.button(emoji, key=f"emoji_{emoji}"):
                    # Append emoji to message
                    if 'message_input' in st.session_state:
                        st.session_state.message_input += emoji

    with col3:
        st.write("") # Spacing
        st.write("") # Spacing
        # File upload
        uploaded_file = st.file_uploader("📎", label_visibility="collapsed")

    # Send button
    if st.button("📤 Send", type="primary", use_container_width=True):
        if message_input:
            attachments = []
            if uploaded_file:
                # Save file
                file_path = settings.UPLOADS_DIR / f"{room_id}_{uploaded_file.name}"
                with open(file_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                attachments.append(str(file_path))

            # Create message
            msg = ChatMessage(
                room_id=room_id,
                sender=st.session_state.current_user,
                message=message_input,
                attachments=attachments if attachments else None
            )
            db.add(msg)

            # Update room timestamp
            room.updated_at = datetime.utcnow()
            db.commit()

            # Clear input
            st.session_state.message_input = ""
            st.rerun()

    # Auto-refresh
    if st.session_state.auto_refresh:
        st.rerun()

def render_welcome():
    """Render welcome screen"""
    st.title("💬 Chat")
    st.write("Select a room from the sidebar or create a new one to start chatting!")

    # Some stats
    db = SessionLocal()
    room_count = db.query(ChatRoom).filter(ChatRoom.is_active == True).count()
    message_count = db.query(ChatMessage).filter(ChatMessage.is_deleted == False).count()
    db.close()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Active Rooms", room_count)
    with col2:
        st.metric("Total Messages", message_count)

def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="Chat - NEXUS",
        page_icon="💬",
        layout="wide"
    )

    try:
        # Lazy import all dependencies
        get_session = _lazy_imports()

        # Initialize session state
        initialize_session_state()

        # Render sidebar
        render_sidebar()

        # Render main content
        db = get_session()

        if st.session_state.current_room:
            render_chat_room(db, st.session_state.current_room)
        else:
            render_welcome()

        db.close()

    except Exception as e:
        st.error(f"Error in Chat module: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
