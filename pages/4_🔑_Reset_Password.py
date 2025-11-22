"""
Password Reset page for NEXUS Platform.
"""
import streamlit as st
from modules.database import get_db
from modules.auth import (
    request_password_reset,
    reset_password,
    StreamlitSessionManager
)

# Page configuration
st.set_page_config(
    page_title="Reset Password - NEXUS Platform",
    page_icon="🔑",
    layout="centered"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
    </style>
""", unsafe_allow_html=True)


def main():
    """Main password reset page function."""
    # Initialize session state
    StreamlitSessionManager.init_session_state()

    # Initialize reset state
    if 'reset_step' not in st.session_state:
        st.session_state.reset_step = 1
        st.session_state.reset_token = None

    # Page header
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("# 🔑 Reset Password")
        st.markdown("### Recover Your Account")
        st.markdown("---")

        # Step 1: Request reset token
        if st.session_state.reset_step == 1:
            st.markdown("### Step 1: Enter Your Email")
            st.info("Enter your email address to receive a password reset link.")

            with st.form("request_reset_form"):
                email = st.text_input(
                    "📧 Email Address",
                    placeholder="Enter your registered email",
                    key="reset_email"
                )

                submit_request = st.form_submit_button("📨 Send Reset Link", use_container_width=True)

                if submit_request:
                    if not email:
                        st.error("❌ Please enter your email address")
                    else:
                        db = next(get_db())
                        try:
                            with st.spinner("Sending reset link..."):
                                reset_token = request_password_reset(db, email.strip())

                                st.success("✅ Password reset link sent!")
                                st.info(
                                    "📧 If an account exists with this email, "
                                    "you will receive a password reset link."
                                )

                                # Show token in development (would be sent via email in production)
                                with st.expander("🔗 Reset Token (Development Only)"):
                                    st.code(f"Reset Token: {reset_token}")
                                    st.caption(
                                        "In production, this token would be sent to your email. "
                                        "For development, copy this token to reset your password."
                                    )

                                # Store token and move to next step
                                st.session_state.reset_token = reset_token
                                st.session_state.reset_step = 2
                                st.rerun()

                        except ValueError as e:
                            # Don't reveal if user exists
                            st.success("✅ Password reset link sent!")
                            st.info(
                                "📧 If an account exists with this email, "
                                "you will receive a password reset link."
                            )
                        except Exception as e:
                            st.error(f"❌ Failed to send reset link: {str(e)}")
                        finally:
                            db.close()

        # Step 2: Reset password with token
        elif st.session_state.reset_step == 2:
            st.markdown("### Step 2: Reset Your Password")
            st.info("Enter the reset token from your email and choose a new password.")

            with st.form("reset_password_form"):
                token = st.text_input(
                    "🔐 Reset Token",
                    placeholder="Enter the token from your email",
                    value=st.session_state.get('reset_token', ''),
                    key="reset_token_input"
                )

                new_password = st.text_input(
                    "🔑 New Password",
                    type="password",
                    placeholder="Enter your new password",
                    key="new_password"
                )

                confirm_password = st.text_input(
                    "🔑 Confirm New Password",
                    type="password",
                    placeholder="Re-enter your new password",
                    key="confirm_new_password"
                )

                # Password requirements
                with st.expander("📋 Password Requirements"):
                    st.markdown("""
                        - Minimum 8 characters (recommended 12+)
                        - At least one uppercase letter (A-Z)
                        - At least one lowercase letter (a-z)
                        - At least one digit (0-9)
                        - At least one special character (!@#$%^&*(),.?":{}|<>_-+=[]\\\/;~`)
                        - Avoid common passwords and patterns
                    """)

                col_a, col_b = st.columns(2)

                with col_a:
                    submit_reset = st.form_submit_button("🔄 Reset Password", use_container_width=True)

                with col_b:
                    cancel_reset = st.form_submit_button("❌ Cancel", use_container_width=True)

                if cancel_reset:
                    st.session_state.reset_step = 1
                    st.session_state.reset_token = None
                    st.rerun()

                if submit_reset:
                    if not token or not new_password or not confirm_password:
                        st.error("❌ All fields are required")
                    else:
                        db = next(get_db())
                        try:
                            with st.spinner("Resetting password..."):
                                reset_password(
                                    db=db,
                                    token=token.strip(),
                                    new_password=new_password,
                                    confirm_password=confirm_password
                                )

                                st.success("✅ Password reset successfully!")
                                st.balloons()
                                st.info("👉 You can now log in with your new password")

                                # Reset state
                                st.session_state.reset_step = 1
                                st.session_state.reset_token = None

                                # Redirect to login
                                if st.button("🔐 Go to Login", use_container_width=True):
                                    st.switch_page("pages/1_🔐_Login.py")

                        except ValueError as e:
                            st.error(f"❌ {str(e)}")
                        except Exception as e:
                            st.error(f"❌ Failed to reset password: {str(e)}")
                        finally:
                            db.close()

        # Back to login link
        st.markdown("---")
        st.markdown(
            '<div style="text-align: center;">'
            'Remember your password? '
            '<a href="/1_🔐_Login" target="_self"><strong>Sign In</strong></a>'
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
