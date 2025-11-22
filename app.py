"""
NEXUS Platform - Main Application
Authentication & Authorization System
"""
import streamlit as st
from modules.auth import StreamlitSessionManager

# Page configuration
st.set_page_config(
    page_title="NEXUS Platform",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    </style>
""", unsafe_allow_html=True)


def main():
    """Main application function."""
    # Initialize session state
    StreamlitSessionManager.init_session_state()

    # Sidebar
    with st.sidebar:
        st.markdown("# 🚀 NEXUS Platform")
        st.markdown("---")

        # User info if authenticated
        if StreamlitSessionManager.is_authenticated():
            user = StreamlitSessionManager.get_current_user()
            if user:
                st.markdown("### 👤 User Info")

                if user.get('avatar_url'):
                    st.image(user['avatar_url'], width=100)

                st.markdown(f"**{user['full_name']}**")
                st.caption(f"@{user['username']}")

                roles = user.get('roles', [])
                if roles:
                    st.caption(f"🎭 {', '.join([r.title() for r in roles])}")

                st.markdown("---")

                # Navigation
                st.markdown("### 📍 Navigation")
                if st.button("👤 Profile", use_container_width=True):
                    st.switch_page("pages/3_👤_Profile.py")

                # Admin section
                if StreamlitSessionManager.is_admin():
                    st.markdown("### ⚙️ Admin")
                    st.button("🛠️ Settings", use_container_width=True, disabled=True)
                    st.button("👥 Users", use_container_width=True, disabled=True)
                    st.button("🎭 Roles", use_container_width=True, disabled=True)

                st.markdown("---")

                # Logout
                if st.button("🚪 Logout", use_container_width=True):
                    from modules.database import get_db
                    from modules.auth import logout_user

                    db = next(get_db())
                    try:
                        token = StreamlitSessionManager.get_access_token()
                        if token:
                            logout_user(db, token)
                    finally:
                        db.close()

                    StreamlitSessionManager.logout()
                    st.success("✅ Logged out successfully!")
                    st.rerun()
        else:
            st.markdown("### 🔐 Authentication")
            if st.button("🔐 Login", use_container_width=True):
                st.switch_page("pages/1_🔐_Login.py")

            if st.button("📝 Register", use_container_width=True):
                st.switch_page("pages/2_📝_Register.py")

        st.markdown("---")
        st.caption("© 2024 NEXUS Platform")

    # Main content
    st.markdown(
        '<div class="main-header">'
        '<h1>🚀 Welcome to NEXUS Platform</h1>'
        '<p style="font-size: 1.2rem;">Complete Authentication & Authorization System</p>'
        '</div>',
        unsafe_allow_html=True
    )

    # Check authentication status
    if StreamlitSessionManager.is_authenticated():
        user = StreamlitSessionManager.get_current_user()

        st.success(f"✅ Welcome back, **{user['full_name']}**!")

        # User dashboard
        st.header("📊 Dashboard")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(
                '<div class="feature-card">'
                '<h3>👤 Profile</h3>'
                '<p>View and edit your profile information</p>'
                '</div>',
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(
                '<div class="feature-card">'
                '<h3>🔑 Security</h3>'
                '<p>Manage your security settings</p>'
                '</div>',
                unsafe_allow_html=True
            )

        with col3:
            st.markdown(
                '<div class="feature-card">'
                '<h3>📊 Activity</h3>'
                '<p>View your recent activity</p>'
                '</div>',
                unsafe_allow_html=True
            )

        # Features section
        st.header("✨ Platform Features")

        st.markdown("### 🔐 Authentication")
        st.markdown("""
        - ✅ Email/Password registration with validation
        - ✅ Secure password hashing (bcrypt)
        - ✅ Login with "Remember me" option
        - ✅ JWT token generation (access + refresh)
        - ✅ Session persistence
        - ✅ Password reset workflow
        - ✅ Email verification
        - ✅ Account lockout protection
        """)

        st.markdown("### 🎭 Authorization (RBAC)")
        st.markdown("""
        - ✅ Role-based access control
        - ✅ Roles: admin, manager, user, guest
        - ✅ Permission decorators
        - ✅ Granular permissions per module
        - ✅ Role-based UI customization
        """)

        st.markdown("### 🔒 Security")
        st.markdown("""
        - ✅ CSRF protection
        - ✅ Rate limiting
        - ✅ Password strength validation
        - ✅ Secure session cookies
        - ✅ HTTP-only, Secure, SameSite flags
        """)

        # Admin features
        if StreamlitSessionManager.is_admin():
            st.markdown("---")
            st.header("⚙️ Admin Features")
            st.info("👑 You have administrator privileges!")

    else:
        # Guest view
        st.header("🎯 Get Started")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                '<div class="feature-card">'
                '<h3>🔐 Sign In</h3>'
                '<p>Already have an account? Sign in to access your dashboard</p>'
                '</div>',
                unsafe_allow_html=True
            )
            if st.button("Go to Login", key="login_btn", use_container_width=True):
                st.switch_page("pages/1_🔐_Login.py")

        with col2:
            st.markdown(
                '<div class="feature-card">'
                '<h3>📝 Create Account</h3>'
                '<p>New to NEXUS? Create an account to get started</p>'
                '</div>',
                unsafe_allow_html=True
            )
            if st.button("Go to Register", key="register_btn", use_container_width=True):
                st.switch_page("pages/2_📝_Register.py")

        st.markdown("---")
        st.header("✨ Platform Features")

        feature_col1, feature_col2, feature_col3 = st.columns(3)

        with feature_col1:
            st.markdown("### 🔐 Secure")
            st.markdown("""
            - Bcrypt password hashing
            - JWT token authentication
            - Account lockout protection
            - Session management
            """)

        with feature_col2:
            st.markdown("### 🎭 Role-Based")
            st.markdown("""
            - Admin, Manager, User roles
            - Granular permissions
            - Access control
            - Role hierarchy
            """)

        with feature_col3:
            st.markdown("### 🚀 Modern")
            st.markdown("""
            - Beautiful UI
            - Real-time validation
            - OAuth integration
            - Responsive design
            """)


if __name__ == "__main__":
    main()
