"""
Registration page for NEXUS Platform.
"""
import streamlit as st
from modules.database import get_db
from modules.auth import (
    register_user,
    UserAlreadyExistsError,
    check_password_strength,
    StreamlitSessionManager
)

# Page configuration
st.set_page_config(
    page_title="Register - NEXUS Platform",
    page_icon="📝",
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
    .password-strength-weak {
        color: #dc3545;
        font-weight: bold;
    }
    .password-strength-medium {
        color: #ffc107;
        font-weight: bold;
    }
    .password-strength-strong {
        color: #28a745;
        font-weight: bold;
    }
    .password-strength-very_strong {
        color: #155724;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)


def display_password_strength(password: str):
    """Display password strength indicator."""
    if not password:
        return

    strength, score = check_password_strength(password)

    # Progress bar for password strength
    progress_color = {
        "weak": "#dc3545",
        "medium": "#ffc107",
        "strong": "#28a745",
        "very_strong": "#155724"
    }

    st.progress(score / 100, text=f"Password Strength: {strength.replace('_', ' ').title()} ({score}/100)")

    # Show strength indicator
    color = progress_color.get(strength, "#6c757d")
    st.markdown(
        f'<div style="text-align: center; color: {color}; font-weight: bold;">'
        f'{strength.replace("_", " ").upper()}'
        f'</div>',
        unsafe_allow_html=True
    )


def main():
    """Main registration page function."""
    # Initialize session state
    StreamlitSessionManager.init_session_state()

    # Check if already logged in
    if StreamlitSessionManager.is_authenticated():
        st.info("ℹ️ You are already logged in!")
        user = StreamlitSessionManager.get_current_user()
        if user:
            st.success(f"✅ Logged in as: **{user['full_name']}** (@{user['username']})")

        if st.button("🏠 Go to Home", use_container_width=True):
            st.switch_page("app.py")
        return

    # Registration page header
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("# 📝 Create Account")
        st.markdown("### Join NEXUS Platform Today")
        st.markdown("---")

        # Registration form
        with st.form("registration_form", clear_on_submit=False):
            full_name = st.text_input(
                "👤 Full Name *",
                placeholder="Enter your full name",
                key="reg_full_name"
            )

            email = st.text_input(
                "📧 Email Address *",
                placeholder="Enter your email address",
                key="reg_email"
            )

            username = st.text_input(
                "🏷️ Username *",
                placeholder="Choose a username",
                key="reg_username",
                help="Username can only contain letters, numbers, underscores, and hyphens"
            )

            password = st.text_input(
                "🔑 Password *",
                type="password",
                placeholder="Create a strong password",
                key="reg_password"
            )

            # Password strength indicator
            if password:
                display_password_strength(password)

            confirm_password = st.text_input(
                "🔑 Confirm Password *",
                type="password",
                placeholder="Re-enter your password",
                key="reg_confirm_password"
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

            terms_accepted = st.checkbox(
                "I agree to the Terms & Conditions and Privacy Policy *",
                value=False,
                key="reg_terms"
            )

            st.markdown("<br>", unsafe_allow_html=True)
            submit_button = st.form_submit_button("📝 Create Account", use_container_width=True)

            if submit_button:
                # Validation
                errors = []

                if not full_name:
                    errors.append("Full name is required")
                elif len(full_name.strip()) < 2:
                    errors.append("Full name must be at least 2 characters")

                if not email:
                    errors.append("Email is required")

                if not username:
                    errors.append("Username is required")

                if not password:
                    errors.append("Password is required")

                if not confirm_password:
                    errors.append("Password confirmation is required")

                if not terms_accepted:
                    errors.append("You must accept the Terms & Conditions")

                if errors:
                    for error in errors:
                        st.error(f"❌ {error}")
                else:
                    # Get database session
                    db = next(get_db())
                    try:
                        with st.spinner("Creating your account..."):
                            # Register user
                            user, verification_token = register_user(
                                db=db,
                                email=email.strip(),
                                username=username.strip(),
                                full_name=full_name.strip(),
                                password=password,
                                confirm_password=confirm_password,
                                default_role="user"
                            )

                            st.success("✅ Account created successfully!")
                            st.balloons()

                            # Show verification message
                            st.info(
                                "📧 A verification email has been sent to your email address. "
                                "Please verify your email before logging in."
                            )

                            # Show verification token (in production, this would be sent via email)
                            with st.expander("🔗 Email Verification (Development Only)"):
                                st.code(f"Verification Token: {verification_token}")
                                st.caption(
                                    "In production, this token would be sent to your email. "
                                    "For development, you can use this token to verify your account."
                                )

                            st.info("👉 Please proceed to the Login page")

                            # Clear form
                            if st.button("🔐 Go to Login", use_container_width=True):
                                st.switch_page("pages/1_🔐_Login.py")

                    except UserAlreadyExistsError as e:
                        st.error(f"❌ {str(e)}")
                    except ValueError as e:
                        st.error(f"❌ {str(e)}")
                    except Exception as e:
                        st.error(f"❌ Registration failed: {str(e)}")
                    finally:
                        db.close()

        # Login link
        st.markdown("---")
        st.markdown(
            '<div style="text-align: center;">'
            'Already have an account? '
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
