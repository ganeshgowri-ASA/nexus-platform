"""Streamlit authentication middleware."""
import streamlit as st
from functools import wraps
from typing import Callable, Any
from .service import AuthService
from core.database.session import get_db_session


def require_auth(func: Callable) -> Callable:
    """
    Decorator to require authentication for Streamlit pages.

    Args:
        func: Function to wrap

    Returns:
        Wrapped function that requires authentication

    Example:
        >>> @require_auth
        ... def my_page():
        ...     st.write("Protected content")
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Check if user is authenticated
        if 'user_id' not in st.session_state or 'user_email' not in st.session_state:
            render_login_page()
            return None
        return func(*args, **kwargs)
    return wrapper


def render_login_page() -> None:
    """Render login/signup page."""
    st.markdown("""
    <style>
        .login-header {
            text-align: center;
            color: #1f77b4;
            font-size: 3rem;
            font-weight: bold;
            margin-bottom: 2rem;
        }
        .login-container {
            max-width: 500px;
            margin: 0 auto;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-header">🚀 NEXUS Platform</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-container">', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔑 Login", "✨ Sign Up"])

    with tab1:
        _render_login_form()

    with tab2:
        _render_signup_form()

    st.markdown('</div>', unsafe_allow_html=True)


def _render_login_form() -> None:
    """Render login form."""
    with st.form("login_form", clear_on_submit=False):
        st.subheader("Login to Your Account")
        email = st.text_input("Email", placeholder="your.email@example.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        submit = st.form_submit_button("Login", use_container_width=True)

        if submit:
            if not email or not password:
                st.error("Please enter both email and password")
                return

            with get_db_session() as db:
                user = AuthService.authenticate(db, email, password)
                if user:
                    # Set session state
                    st.session_state.user_id = user.id
                    st.session_state.user_email = user.email
                    st.session_state.user_name = user.full_name or user.email
                    st.session_state.is_admin = user.is_admin

                    # Create token
                    token = AuthService.create_token(user.id)
                    st.session_state.auth_token = token

                    st.success(f"Welcome back, {user.full_name or user.email}!")
                    st.rerun()
                else:
                    st.error("Invalid email or password")


def _render_signup_form() -> None:
    """Render signup form."""
    with st.form("signup_form", clear_on_submit=False):
        st.subheader("Create New Account")
        full_name = st.text_input("Full Name", placeholder="John Doe")
        email = st.text_input("Email", placeholder="your.email@example.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        password_confirm = st.text_input("Confirm Password", type="password", placeholder="••••••••")
        submit = st.form_submit_button("Sign Up", use_container_width=True)

        if submit:
            # Validation
            if not email or not password:
                st.error("Email and password are required")
                return

            if password != password_confirm:
                st.error("Passwords do not match")
                return

            if len(password) < 8:
                st.error("Password must be at least 8 characters long")
                return

            try:
                with get_db_session() as db:
                    user = AuthService.register_user(db, email, password, full_name)
                    st.success(f"Account created successfully! Welcome, {user.full_name or user.email}!")

                    # Auto-login after signup
                    st.session_state.user_id = user.id
                    st.session_state.user_email = user.email
                    st.session_state.user_name = user.full_name or user.email
                    st.session_state.is_admin = user.is_admin

                    # Create token
                    token = AuthService.create_token(user.id)
                    st.session_state.auth_token = token

                    st.rerun()
            except ValueError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")


def logout() -> None:
    """Logout current user."""
    # Clear session state
    keys_to_clear = ['user_id', 'user_email', 'user_name', 'is_admin', 'auth_token']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

    st.rerun()
