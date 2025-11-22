"""
User Profile page for NEXUS Platform.
"""
import streamlit as st
from datetime import datetime
from modules.database import get_db
from modules.database.models import User
from modules.auth import (
    StreamlitSessionManager,
    change_password,
    InvalidCredentialsError
)

# Page configuration
st.set_page_config(
    page_title="Profile - NEXUS Platform",
    page_icon="👤",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .profile-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .stat-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .stat-value {
        font-size: 2rem;
        font-weight: bold;
        color: #667eea;
    }
    .stat-label {
        color: #6c757d;
        font-size: 0.9rem;
    }
    </style>
""", unsafe_allow_html=True)


def main():
    """Main profile page function."""
    # Require authentication
    StreamlitSessionManager.require_auth()

    # Get current user
    user_data = StreamlitSessionManager.get_current_user()
    if not user_data:
        st.error("❌ Unable to load user data")
        return

    # Get full user data from database
    db = next(get_db())
    try:
        user = db.query(User).filter(User.id == user_data['id']).first()
        if not user:
            st.error("❌ User not found")
            return

        # Profile header
        st.markdown(
            f'<div class="profile-header">'
            f'<h1>👤 {user.full_name}</h1>'
            f'<p style="font-size: 1.2rem;">@{user.username}</p>'
            f'<p>📧 {user.email}</p>'
            f'</div>',
            unsafe_allow_html=True
        )

        # Tab navigation
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Overview",
            "✏️ Edit Profile",
            "🔑 Change Password",
            "📜 Login History"
        ])

        # Overview Tab
        with tab1:
            st.header("Account Overview")

            # Account statistics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown(
                    '<div class="stat-card">'
                    f'<div class="stat-value">{len(user.roles)}</div>'
                    '<div class="stat-label">Roles</div>'
                    '</div>',
                    unsafe_allow_html=True
                )

            with col2:
                verified_icon = "✅" if user.is_verified else "⏳"
                st.markdown(
                    '<div class="stat-card">'
                    f'<div class="stat-value">{verified_icon}</div>'
                    '<div class="stat-label">Verified</div>'
                    '</div>',
                    unsafe_allow_html=True
                )

            with col3:
                status_icon = "🟢" if user.is_active else "🔴"
                st.markdown(
                    '<div class="stat-card">'
                    f'<div class="stat-value">{status_icon}</div>'
                    '<div class="stat-label">Status</div>'
                    '</div>',
                    unsafe_allow_html=True
                )

            with col4:
                login_count = len(user.login_history)
                st.markdown(
                    '<div class="stat-card">'
                    f'<div class="stat-value">{login_count}</div>'
                    '<div class="stat-label">Total Logins</div>'
                    '</div>',
                    unsafe_allow_html=True
                )

            st.markdown("<br>", unsafe_allow_html=True)

            # Account details
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📋 Account Information")
                st.write(f"**User ID:** {user.id}")
                st.write(f"**Username:** @{user.username}")
                st.write(f"**Email:** {user.email}")
                st.write(f"**Full Name:** {user.full_name}")

                if user.phone:
                    st.write(f"**Phone:** {user.phone}")

                if user.oauth_provider:
                    st.write(f"**OAuth Provider:** {user.oauth_provider.title()}")

            with col2:
                st.subheader("🎭 Roles & Permissions")
                if user.roles:
                    for role in user.roles:
                        st.write(f"**{role.name.title()}**")
                        st.caption(role.description or "No description")
                else:
                    st.info("No roles assigned")

                st.subheader("⏰ Account Dates")
                st.write(f"**Created:** {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                if user.last_login:
                    st.write(f"**Last Login:** {user.last_login.strftime('%Y-%m-%d %H:%M:%S')}")

        # Edit Profile Tab
        with tab2:
            st.header("✏️ Edit Profile")

            with st.form("edit_profile_form"):
                new_full_name = st.text_input(
                    "Full Name",
                    value=user.full_name,
                    key="edit_full_name"
                )

                new_phone = st.text_input(
                    "Phone Number",
                    value=user.phone or "",
                    placeholder="+1 (555) 123-4567",
                    key="edit_phone"
                )

                new_bio = st.text_area(
                    "Bio",
                    value=user.bio or "",
                    placeholder="Tell us about yourself...",
                    max_chars=500,
                    key="edit_bio"
                )

                # Avatar URL (in production, this would be a file upload)
                new_avatar_url = st.text_input(
                    "Avatar URL",
                    value=user.avatar_url or "",
                    placeholder="https://example.com/avatar.jpg",
                    key="edit_avatar"
                )

                submit_edit = st.form_submit_button("💾 Save Changes", use_container_width=True)

                if submit_edit:
                    try:
                        # Update user
                        user.full_name = new_full_name.strip()
                        user.phone = new_phone.strip() if new_phone.strip() else None
                        user.bio = new_bio.strip() if new_bio.strip() else None
                        user.avatar_url = new_avatar_url.strip() if new_avatar_url.strip() else None
                        user.updated_at = datetime.utcnow()

                        db.commit()
                        db.refresh(user)

                        # Update session state
                        st.session_state.user['full_name'] = user.full_name
                        st.session_state.user['avatar_url'] = user.avatar_url

                        st.success("✅ Profile updated successfully!")
                        st.rerun()

                    except Exception as e:
                        db.rollback()
                        st.error(f"❌ Failed to update profile: {str(e)}")

        # Change Password Tab
        with tab3:
            st.header("🔑 Change Password")

            # Only show password change for non-OAuth users
            if user.oauth_provider:
                st.info(
                    f"ℹ️ You are logged in with {user.oauth_provider.title()}. "
                    "Password change is not available for OAuth accounts."
                )
            else:
                with st.form("change_password_form"):
                    current_password = st.text_input(
                        "Current Password",
                        type="password",
                        key="current_password"
                    )

                    new_password = st.text_input(
                        "New Password",
                        type="password",
                        key="new_password"
                    )

                    confirm_new_password = st.text_input(
                        "Confirm New Password",
                        type="password",
                        key="confirm_new_password"
                    )

                    submit_password = st.form_submit_button(
                        "🔄 Change Password",
                        use_container_width=True
                    )

                    if submit_password:
                        if not current_password or not new_password or not confirm_new_password:
                            st.error("❌ All fields are required")
                        else:
                            try:
                                change_password(
                                    db=db,
                                    user_id=user.id,
                                    current_password=current_password,
                                    new_password=new_password,
                                    confirm_password=confirm_new_password
                                )

                                st.success("✅ Password changed successfully!")
                                st.info("Please log in again with your new password.")

                                # Logout user
                                StreamlitSessionManager.logout()
                                st.rerun()

                            except InvalidCredentialsError as e:
                                st.error(f"❌ {str(e)}")
                            except ValueError as e:
                                st.error(f"❌ {str(e)}")
                            except Exception as e:
                                st.error(f"❌ Failed to change password: {str(e)}")

        # Login History Tab
        with tab4:
            st.header("📜 Login History")

            if user.login_history:
                # Get recent login history (last 20 entries)
                recent_logins = sorted(
                    user.login_history,
                    key=lambda x: x.created_at,
                    reverse=True
                )[:20]

                # Display login history
                for login in recent_logins:
                    status_icon = "✅" if login.success else "❌"
                    status_text = "Success" if login.success else "Failed"

                    with st.expander(
                        f"{status_icon} {login.created_at.strftime('%Y-%m-%d %H:%M:%S')} - {status_text}"
                    ):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.write(f"**Status:** {status_text}")
                            st.write(f"**Date/Time:** {login.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

                        with col2:
                            if login.ip_address:
                                st.write(f"**IP Address:** {login.ip_address}")
                            if login.location:
                                st.write(f"**Location:** {login.location}")

                        if login.user_agent:
                            st.caption(f"**User Agent:** {login.user_agent}")

                        if not login.success and login.failure_reason:
                            st.warning(f"**Failure Reason:** {login.failure_reason}")
            else:
                st.info("No login history available")

    finally:
        db.close()


if __name__ == "__main__":
    main()
