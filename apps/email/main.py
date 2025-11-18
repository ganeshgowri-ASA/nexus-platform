"""Email Client Application"""
import streamlit as st
from datetime import datetime
from pathlib import Path
import sys
import json
sys.path.append(str(Path(__file__).parent.parent.parent))

from database.connection import SessionLocal, init_db
from database.models import EmailMessage, EmailDraft
from ai.claude_client import ClaudeClient
from config.settings import settings
from config.constants import EMAIL_CATEGORIES
from utils.exporters import export_to_pdf
from utils.formatters import format_relative_time
from utils.validators import validate_email

def initialize_session_state():
    """Initialize session state variables"""
    if 'current_email' not in st.session_state:
        st.session_state.current_email = None
    if 'compose_mode' not in st.session_state:
        st.session_state.compose_mode = False
    if 'reply_mode' not in st.session_state:
        st.session_state.reply_mode = False
    if 'view_mode' not in st.session_state:
        st.session_state.view_mode = 'inbox'

def render_sidebar():
    """Render sidebar with navigation"""
    st.sidebar.title("📧 Email")

    # Compose button
    if st.sidebar.button("✍️ Compose", use_container_width=True):
        st.session_state.compose_mode = True
        st.session_state.current_email = None
        st.session_state.reply_mode = False
        st.rerun()

    st.sidebar.divider()

    # Folders
    st.sidebar.subheader("Folders")

    folders = [
        ("📥 Inbox", "inbox"),
        ("⭐ Starred", "starred"),
        ("📤 Sent", "sent"),
        ("📝 Drafts", "drafts"),
    ]

    for label, folder in folders:
        if st.sidebar.button(label, key=folder, use_container_width=True):
            st.session_state.view_mode = folder
            st.session_state.compose_mode = False
            st.rerun()

    st.sidebar.divider()

    # Categories
    st.sidebar.subheader("Categories")
    for category in EMAIL_CATEGORIES:
        if st.sidebar.button(f"🏷️ {category}", key=f"cat_{category}", use_container_width=True):
            st.session_state.view_mode = f"category_{category}"
            st.rerun()

def render_inbox(db):
    """Render inbox view"""
    st.subheader("📥 Inbox")

    # Search and filter
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        search_query = st.text_input("🔍 Search emails", placeholder="Search by subject, sender...")
    with col2:
        filter_read = st.selectbox("Status", ["All", "Unread", "Read"])
    with col3:
        sort_by = st.selectbox("Sort by", ["Date (Newest)", "Date (Oldest)", "Sender"])

    # Get emails based on view mode
    query = db.query(EmailMessage)

    if st.session_state.view_mode == 'inbox':
        query = query.filter(EmailMessage.is_sent == False, EmailMessage.is_draft == False)
    elif st.session_state.view_mode == 'starred':
        query = query.filter(EmailMessage.is_starred == True)
    elif st.session_state.view_mode == 'sent':
        query = query.filter(EmailMessage.is_sent == True)
    elif st.session_state.view_mode == 'drafts':
        query = query.filter(EmailMessage.is_draft == True)
    elif st.session_state.view_mode.startswith('category_'):
        category = st.session_state.view_mode.replace('category_', '')
        query = query.filter(EmailMessage.category == category)

    # Apply filters
    if filter_read == "Unread":
        query = query.filter(EmailMessage.is_read == False)
    elif filter_read == "Read":
        query = query.filter(EmailMessage.is_read == True)

    if search_query:
        query = query.filter(
            (EmailMessage.subject.contains(search_query)) |
            (EmailMessage.sender.contains(search_query)) |
            (EmailMessage.body.contains(search_query))
        )

    # Apply sorting
    if sort_by == "Date (Newest)":
        query = query.order_by(EmailMessage.created_at.desc())
    elif sort_by == "Date (Oldest)":
        query = query.order_by(EmailMessage.created_at.asc())
    else:
        query = query.order_by(EmailMessage.sender)

    emails = query.all()

    # Display emails
    if emails:
        for email in emails:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])

                with col1:
                    # Subject line
                    subject_style = "font-weight: bold;" if not email.is_read else ""
                    if st.button(
                        f"{'🔵 ' if not email.is_read else ''}**{email.subject}**" if not email.is_read else email.subject,
                        key=f"email_{email.id}",
                        use_container_width=True
                    ):
                        st.session_state.current_email = email.id
                        # Mark as read
                        email.is_read = True
                        db.commit()
                        st.rerun()

                with col2:
                    st.caption(f"From: {email.sender}")

                with col3:
                    st.caption(format_relative_time(email.created_at))

                with col4:
                    col_star, col_delete = st.columns(2)
                    with col_star:
                        if st.button("⭐" if not email.is_starred else "⭐", key=f"star_{email.id}"):
                            email.is_starred = not email.is_starred
                            db.commit()
                            st.rerun()
                    with col_delete:
                        if st.button("🗑️", key=f"del_{email.id}"):
                            db.delete(email)
                            db.commit()
                            st.rerun()

                st.divider()
    else:
        st.info("No emails found")

def render_email_view(db, email_id):
    """Render single email view"""
    email = db.query(EmailMessage).filter(EmailMessage.id == email_id).first()

    if not email:
        st.error("Email not found")
        return

    # Back button
    if st.button("← Back to Inbox"):
        st.session_state.current_email = None
        st.rerun()

    # Email header
    st.title(email.subject)

    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"**From:** {email.sender}")
        if email.recipients:
            st.write(f"**To:** {', '.join(email.recipients)}")
        if email.cc:
            st.write(f"**CC:** {', '.join(email.cc)}")
    with col2:
        st.caption(format_relative_time(email.created_at))

    st.divider()

    # Email body
    if email.html_body:
        st.markdown(email.html_body, unsafe_allow_html=True)
    else:
        st.write(email.body)

    # Attachments
    if email.attachments:
        st.subheader("📎 Attachments")
        for attachment in email.attachments:
            st.write(f"• {attachment}")

    st.divider()

    # Actions
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("↩️ Reply"):
            st.session_state.reply_mode = True
            st.session_state.compose_mode = True
            st.rerun()

    with col2:
        if st.button("↪️ Forward"):
            st.session_state.compose_mode = True
            st.rerun()

    with col3:
        if st.button("⭐ Star" if not email.is_starred else "⭐ Unstar"):
            email.is_starred = not email.is_starred
            db.commit()
            st.rerun()

    with col4:
        if st.button("🗑️ Delete"):
            db.delete(email)
            db.commit()
            st.session_state.current_email = None
            st.rerun()

    # Thread view
    if email.thread_id or email.replies:
        st.divider()
        st.subheader("💬 Thread")

        # Get all emails in thread
        thread_emails = db.query(EmailMessage).filter(
            (EmailMessage.thread_id == email.thread_id) |
            (EmailMessage.parent_id == email.id)
        ).order_by(EmailMessage.created_at).all()

        for thread_email in thread_emails:
            with st.expander(f"{thread_email.sender} - {format_relative_time(thread_email.created_at)}"):
                st.write(thread_email.body)

    # AI Smart Reply
    if settings.ENABLE_AI_FEATURES:
        st.divider()
        with st.expander("🤖 AI Smart Reply"):
            col1, col2 = st.columns([3, 1])
            with col1:
                reply_context = st.text_input("Context (optional)", placeholder="e.g., Agree and schedule meeting")
            with col2:
                if st.button("Generate Reply", type="primary"):
                    try:
                        with st.spinner("Generating reply..."):
                            ai_client = ClaudeClient()
                            reply = ai_client.generate_email_reply(email.body, reply_context)
                            st.text_area("Suggested Reply", value=reply, height=150)
                            st.info("Copy this reply to compose window")
                    except Exception as e:
                        st.error(f"Error generating reply: {e}")

def render_compose(db):
    """Render compose email view"""
    st.subheader("✍️ Compose Email")

    # Email form
    recipients_input = st.text_input("To", placeholder="email@example.com, another@example.com")
    cc_input = st.text_input("CC (optional)", placeholder="email@example.com")
    bcc_input = st.text_input("BCC (optional)", placeholder="email@example.com")
    subject = st.text_input("Subject")

    # Rich text editor (using text area as placeholder)
    body = st.text_area("Message", height=300)

    # Attachments (placeholder)
    uploaded_files = st.file_uploader("Attachments", accept_multiple_files=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📤 Send", type="primary"):
            # Validate
            recipients = [r.strip() for r in recipients_input.split(',') if r.strip()]
            if not recipients or not subject or not body:
                st.error("Please fill in all required fields")
            else:
                # Create email
                email = EmailMessage(
                    subject=subject,
                    sender=settings.SMTP_USER or "me@nexus.local",
                    recipients=recipients,
                    cc=[c.strip() for c in cc_input.split(',') if c.strip()] if cc_input else [],
                    bcc=[b.strip() for b in bcc_input.split(',') if b.strip()] if bcc_input else [],
                    body=body,
                    is_sent=True,
                    is_draft=False
                )

                if st.session_state.reply_mode and st.session_state.current_email:
                    email.parent_id = st.session_state.current_email
                    original = db.query(EmailMessage).filter(
                        EmailMessage.id == st.session_state.current_email
                    ).first()
                    if original:
                        email.thread_id = original.thread_id or original.id

                db.add(email)
                db.commit()

                st.success("Email sent!")
                st.session_state.compose_mode = False
                st.session_state.reply_mode = False
                st.rerun()

    with col2:
        if st.button("💾 Save Draft"):
            recipients = [r.strip() for r in recipients_input.split(',') if r.strip()]
            email = EmailMessage(
                subject=subject or "No Subject",
                sender=settings.SMTP_USER or "me@nexus.local",
                recipients=recipients,
                body=body,
                is_draft=True,
                is_sent=False
            )
            db.add(email)
            db.commit()
            st.success("Draft saved!")

    with col3:
        if st.button("❌ Cancel"):
            st.session_state.compose_mode = False
            st.session_state.reply_mode = False
            st.rerun()

def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="Email - NEXUS",
        page_icon="📧",
        layout="wide"
    )

    # Initialize database
    init_db()

    # Initialize session state
    initialize_session_state()

    # Render sidebar
    render_sidebar()

    # Render main content
    st.title("📧 Email Client")

    db = SessionLocal()

    if st.session_state.compose_mode:
        render_compose(db)
    elif st.session_state.current_email:
        render_email_view(db, st.session_state.current_email)
    else:
        render_inbox(db)

    db.close()

if __name__ == "__main__":
    main()
