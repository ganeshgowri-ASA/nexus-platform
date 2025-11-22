"""Email Client Application"""


def main():
    import streamlit as st

    try:
        # Lazy import database
        from database import init_database
        init_database()

        st.set_page_config(
            page_title="Email - NEXUS",
            page_icon="📧",
            layout="wide"
        )

        st.title("📧 Email Client")

        # Session state
        if 'emails' not in st.session_state:
            st.session_state.emails = []
        if 'compose_mode' not in st.session_state:
            st.session_state.compose_mode = False
        if 'view_mode' not in st.session_state:
            st.session_state.view_mode = 'inbox'

        # Sidebar
        st.sidebar.title("📧 Email")

        if st.sidebar.button("✍️ Compose", use_container_width=True):
            st.session_state.compose_mode = True
            st.rerun()

        st.sidebar.divider()
        st.sidebar.subheader("Folders")

        for label, folder in [("📥 Inbox", "inbox"), ("⭐ Starred", "starred"), ("📤 Sent", "sent"), ("📝 Drafts", "drafts")]:
            if st.sidebar.button(label, key=folder, use_container_width=True):
                st.session_state.view_mode = folder
                st.session_state.compose_mode = False
                st.rerun()

        # Main content
        if st.session_state.compose_mode:
            st.subheader("✍️ Compose Email")
            recipients = st.text_input("To", placeholder="email@example.com")
            subject = st.text_input("Subject")
            body = st.text_area("Message", height=300)

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📤 Send", type="primary"):
                    if recipients and subject:
                        st.session_state.emails.append({'to': recipients, 'subject': subject, 'body': body, 'sent': True})
                        st.success("Email sent!")
                        st.session_state.compose_mode = False
                        st.rerun()
                    else:
                        st.error("Please fill in required fields")
            with col2:
                if st.button("💾 Save Draft"):
                    st.success("Draft saved!")
            with col3:
                if st.button("❌ Cancel"):
                    st.session_state.compose_mode = False
                    st.rerun()
        else:
            st.subheader(f"📥 {st.session_state.view_mode.title()}")
            st.text_input("🔍 Search emails", placeholder="Search...")

            if st.session_state.emails:
                for idx, email in enumerate(st.session_state.emails):
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        st.write(f"**{email.get('subject', 'No Subject')}**")
                    with col2:
                        st.caption(f"To: {email.get('to', '')}")
                    with col3:
                        if st.button("🗑️", key=f"del_{idx}"):
                            st.session_state.emails.pop(idx)
                            st.rerun()
                    st.divider()
            else:
                st.info("No emails. Compose a new email to get started!")

    except Exception as e:
        import streamlit as st
        st.error(f"Error loading module: {str(e)}")
        with st.expander("Technical Details"):
            import traceback
            st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
