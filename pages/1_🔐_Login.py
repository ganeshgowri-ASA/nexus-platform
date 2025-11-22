"""
Login page for NEXUS Platform.
"""
import streamlit as st
from modules.database import get_db
from modules.auth import (
    login_user,
    InvalidCredentialsError,
    AccountLockedError,
    AccountNotVerifiedError,
    StreamlitSessionManager,
    is_oauth_configured,
    OAuthProvider
)

# Page configuration
st.set_page_config(
    page_title="Login - NEXUS Platform",
    page_icon="🔐",
    layout="centered"
)

# Custom CSS for beautiful gradient design
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .login-container {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    .stButton>button {
        width: 100%;
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
    .oauth-button {
        width: 100%;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        border: 1px solid #ddd;
        background: white;
        cursor: pointer;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    .oauth-button:hover {
        background: #f8f9fa;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)


def main():
    """Main login page function."""
    # Initialize session state
    StreamlitSessionManager.init_session_state()

    # Check if already logged in
    if StreamlitSessionManager.is_authenticated():
        st.success("✅ You are already logged in!")
        user = StreamlitSessionManager.get_current_user()
        if user:
            st.info(f"👤 Logged in as: **{user['full_name']}** (@{user['username']})")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🏠 Go to Home", use_container_width=True):
                st.switch_page("app.py")
        with col2:
            if st.button("🚪 Logout", use_container_width=True):
                # Get database session for logout
                db = next(get_db())
                try:
                    from modules.auth import logout_user
                    token = StreamlitSessionManager.get_access_token()
                    if token:
                        logout_user(db, token)
                finally:
                    db.close()

                StreamlitSessionManager.logout()
                st.success("✅ Logged out successfully!")
                st.rerun()
        return

    # Login page header
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("# 🔐 NEXUS Platform")
        st.markdown("### Sign In to Your Account")
        st.markdown("---")

        # Login form
        with st.form("login_form", clear_on_submit=False):
            email_or_username = st.text_input(
                "📧 Email or Username",
                placeholder="Enter your email or username",
                key="login_email"
            )

            password = st.text_input(
                "🔑 Password",
                type="password",
                placeholder="Enter your password",
                key="login_password"
            )

            col_a, col_b = st.columns(2)
            with col_a:
                remember_me = st.checkbox("Remember me", value=False)

            with col_b:
                st.markdown(
                    '<div style="text-align: right; padding-top: 0.5rem;">'
                    '<a href="/4_🔑_Reset_Password" target="_self">Forgot password?</a>'
                    '</div>',
                    unsafe_allow_html=True
                )

            submit_button = st.form_submit_button("🔐 Sign In", use_container_width=True)

            if submit_button:
                if not email_or_username or not password:
                    st.error("❌ Please enter both email/username and password")
                else:
                    # Get database session
                    db = next(get_db())
                    try:
                        with st.spinner("Authenticating..."):
                            # Attempt login
                            user, access_token, refresh_token = login_user(
                                db=db,
                                email_or_username=email_or_username,
                                password=password,
                                remember_me=remember_me,
                                ip_address=st.session_state.get('client_ip', None),
                                user_agent=st.session_state.get('user_agent', None)
                            )

                            # Set session
                            StreamlitSessionManager.login(
                                user=user,
                                access_token=access_token,
                                refresh_token=refresh_token,
                                remember_me=remember_me
                            )

                            st.success(f"✅ Welcome back, {user.full_name}!")
                            st.balloons()

                            # Redirect to home
                            st.info("Redirecting to home page...")
                            st.rerun()

                    except InvalidCredentialsError as e:
                        st.error(f"❌ {str(e)}")
                    except AccountLockedError as e:
                        st.error(f"🔒 {str(e)}")
                    except AccountNotVerifiedError as e:
                        st.warning(f"⚠️ {str(e)}")
                        st.info("Please check your email for the verification link.")
                    except Exception as e:
                        st.error(f"❌ Login failed: {str(e)}")
                    finally:
                        db.close()

        # OAuth buttons
        st.markdown("---")
        st.markdown("### Or sign in with")

        # Google OAuth
        if is_oauth_configured(OAuthProvider.GOOGLE):
            if st.button("🔵 Continue with Google", use_container_width=True):
                st.info("🚧 Google OAuth integration requires additional setup")
                st.info("Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your environment")
        else:
            st.button(
                "🔵 Continue with Google (Not Configured)",
                use_container_width=True,
                disabled=True
            )

        # Microsoft OAuth
        if is_oauth_configured(OAuthProvider.MICROSOFT):
            if st.button("🔷 Continue with Microsoft", use_container_width=True):
                st.info("🚧 Microsoft OAuth integration requires additional setup")
                st.info("Please set MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET in your environment")
        else:
            st.button(
                "🔷 Continue with Microsoft (Not Configured)",
                use_container_width=True,
                disabled=True
            )

        # Register link
        st.markdown("---")
        st.markdown(
            '<div style="text-align: center;">'
            'Don\'t have an account? '
            '<a href="/2_📝_Register" target="_self"><strong>Sign Up</strong></a>'
            '</div>',
            unsafe_allow_html=True
        )

    # Footer
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        '<div style="text-align: center; color: white; padding: 1rem;">'
        '© 2024 NEXUS Platform. All rights reserved.'
        '</div>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
