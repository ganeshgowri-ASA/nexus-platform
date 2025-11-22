"""Chat / Real-time Messaging Application"""


def main():
    import streamlit as st
    from datetime import datetime

    try:
        # Lazy import database
        from database import init_database
        init_database()

        st.set_page_config(
            page_title="Chat - NEXUS",
            page_icon="💬",
            layout="wide"
        )

        st.title("💬 Chat")

        # Session state
        if 'rooms' not in st.session_state:
            st.session_state.rooms = []
        if 'current_room' not in st.session_state:
            st.session_state.current_room = None
        if 'messages' not in st.session_state:
            st.session_state.messages = {}
        if 'current_user' not in st.session_state:
            st.session_state.current_user = "User"

        # Sidebar
        st.sidebar.title("💬 Chat")
        st.session_state.current_user = st.sidebar.text_input("Username", value=st.session_state.current_user)

        st.sidebar.divider()

        with st.sidebar.expander("➕ Create Room"):
            room_name = st.text_input("Room Name")
            room_type = st.selectbox("Type", ["Public", "Private", "Direct Message"])
            if st.button("Create", type="primary"):
                if room_name:
                    st.session_state.rooms.append({'name': room_name, 'type': room_type, 'members': [st.session_state.current_user]})
                    st.session_state.messages[room_name] = []
                    st.rerun()

        st.sidebar.divider()
        st.sidebar.subheader("Rooms")

        for idx, room in enumerate(st.session_state.rooms):
            room_icon = "🔒" if room['type'] == "Direct Message" else "👥"
            if st.sidebar.button(f"{room_icon} {room['name']}", key=f"room_{idx}", use_container_width=True):
                st.session_state.current_room = idx
                st.rerun()

        # Main content
        if st.session_state.current_room is not None and st.session_state.current_room < len(st.session_state.rooms):
            room = st.session_state.rooms[st.session_state.current_room]
            st.subheader(f"💬 {room['name']}")

            # Messages
            room_messages = st.session_state.messages.get(room['name'], [])

            messages_container = st.container()
            with messages_container:
                if room_messages:
                    for msg in room_messages:
                        is_own = msg['sender'] == st.session_state.current_user
                        with st.chat_message("user" if is_own else "assistant"):
                            st.write(f"**{msg['sender']}**: {msg['message']}")
                            st.caption(msg['time'])
                else:
                    st.info("No messages yet. Start the conversation!")

            # Input
            col1, col2 = st.columns([5, 1])
            with col1:
                message_input = st.text_input("Message", key="msg_input", placeholder="Type your message...")
            with col2:
                if st.button("📤 Send", type="primary"):
                    if message_input:
                        if room['name'] not in st.session_state.messages:
                            st.session_state.messages[room['name']] = []
                        st.session_state.messages[room['name']].append({
                            'sender': st.session_state.current_user,
                            'message': message_input,
                            'time': datetime.now().strftime("%H:%M")
                        })
                        st.rerun()
        else:
            st.info("Select a room from the sidebar or create a new one to start chatting!")
            st.metric("Active Rooms", len(st.session_state.rooms))

    except Exception as e:
        import streamlit as st
        st.error(f"Error loading module: {str(e)}")
        with st.expander("Technical Details"):
            import traceback
            st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
