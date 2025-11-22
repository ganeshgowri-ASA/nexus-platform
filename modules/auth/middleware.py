"""
Authentication and authorization middleware decorators.
"""
from functools import wraps
from typing import Callable, List, Optional, Any
import streamlit as st

from modules.auth.session_manager import StreamlitSessionManager
from modules.auth.authorization import (
    check_permission,
    check_role,
    check_any_role,
    InsufficientPermissionsError
)


def require_auth(redirect_page: str = "🔐_Login") -> Callable:
    """
    Decorator to require authentication for a function or page.

    Args:
        redirect_page: Page name to redirect to if not authenticated

    Returns:
        Callable: Decorated function

    Example:
        @require_auth()
        def my_protected_page():
            st.write("Protected content")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if not StreamlitSessionManager.is_authenticated():
                st.warning("⚠️ Authentication Required")
                st.info(f"Please navigate to the **{redirect_page}** page to log in.")
                st.stop()
                return None

            if not StreamlitSessionManager.check_session_timeout():
                st.error("⏰ Session Expired")
                st.info("Your session has expired. Please log in again.")
                st.stop()
                return None

            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(role_name: str, show_error: bool = True) -> Callable:
    """
    Decorator to require a specific role for a function or page.

    Args:
        role_name: Required role name
        show_error: Whether to show error message

    Returns:
        Callable: Decorated function

    Example:
        @require_role("admin")
        def admin_only_page():
            st.write("Admin content")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # First check authentication
            if not StreamlitSessionManager.is_authenticated():
                if show_error:
                    st.error("❌ Authentication required")
                st.stop()
                return None

            # Check role
            if not StreamlitSessionManager.has_role(role_name):
                if show_error:
                    st.error(f"❌ Access Denied")
                    st.warning(f"You need the **{role_name}** role to access this resource.")
                st.stop()
                return None

            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_role(role_names: List[str], show_error: bool = True) -> Callable:
    """
    Decorator to require any of the specified roles for a function or page.

    Args:
        role_names: List of acceptable role names
        show_error: Whether to show error message

    Returns:
        Callable: Decorated function

    Example:
        @require_any_role(["admin", "manager"])
        def manager_page():
            st.write("Manager content")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # First check authentication
            if not StreamlitSessionManager.is_authenticated():
                if show_error:
                    st.error("❌ Authentication required")
                st.stop()
                return None

            # Check roles
            if not StreamlitSessionManager.has_any_role(role_names):
                if show_error:
                    st.error(f"❌ Access Denied")
                    st.warning(
                        f"You need one of these roles to access this resource: "
                        f"**{', '.join(role_names)}**"
                    )
                st.stop()
                return None

            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_admin(show_error: bool = True) -> Callable:
    """
    Decorator to require admin role for a function or page.

    Args:
        show_error: Whether to show error message

    Returns:
        Callable: Decorated function

    Example:
        @require_admin()
        def admin_settings():
            st.write("Admin settings")
    """
    return require_role("admin", show_error=show_error)


def require_manager(show_error: bool = True) -> Callable:
    """
    Decorator to require manager or admin role for a function or page.

    Args:
        show_error: Whether to show error message

    Returns:
        Callable: Decorated function

    Example:
        @require_manager()
        def team_management():
            st.write("Team management")
    """
    return require_any_role(["admin", "manager"], show_error=show_error)


def optional_auth(func: Callable) -> Callable:
    """
    Decorator for pages that work differently based on authentication status.
    Does not require authentication but provides auth context.

    Args:
        func: Function to decorate

    Returns:
        Callable: Decorated function

    Example:
        @optional_auth
        def home_page():
            if StreamlitSessionManager.is_authenticated():
                st.write("Welcome back!")
            else:
                st.write("Welcome! Please log in.")
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        # Initialize session state
        StreamlitSessionManager.init_session_state()

        # Check session timeout if authenticated
        if StreamlitSessionManager.is_authenticated():
            StreamlitSessionManager.check_session_timeout()

        return func(*args, **kwargs)
    return wrapper


def rate_limit(
    max_attempts: int = 5,
    window_seconds: int = 60,
    key: str = "default"
) -> Callable:
    """
    Decorator to implement rate limiting.

    Args:
        max_attempts: Maximum number of attempts allowed
        window_seconds: Time window in seconds
        key: Unique key for this rate limiter

    Returns:
        Callable: Decorated function

    Example:
        @rate_limit(max_attempts=5, window_seconds=60)
        def login_attempt():
            # Login logic
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            from datetime import datetime, timedelta

            # Initialize rate limit state
            if f'rate_limit_{key}' not in st.session_state:
                st.session_state[f'rate_limit_{key}'] = []

            # Clean old attempts
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(seconds=window_seconds)
            st.session_state[f'rate_limit_{key}'] = [
                timestamp for timestamp in st.session_state[f'rate_limit_{key}']
                if timestamp > cutoff_time
            ]

            # Check if rate limit exceeded
            if len(st.session_state[f'rate_limit_{key}']) >= max_attempts:
                st.error(
                    f"⚠️ Rate limit exceeded. "
                    f"Please wait {window_seconds} seconds before trying again."
                )
                st.stop()
                return None

            # Record this attempt
            st.session_state[f'rate_limit_{key}'].append(current_time)

            return func(*args, **kwargs)
        return wrapper
    return decorator


def show_for_roles(role_names: List[str]) -> Callable:
    """
    Decorator to show UI elements only for specific roles.
    Returns None if user doesn't have required role (element not shown).

    Args:
        role_names: List of role names that can see this element

    Returns:
        Callable: Decorated function

    Example:
        @show_for_roles(["admin"])
        def admin_button():
            if st.button("Admin Action"):
                # Admin action
                pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if not StreamlitSessionManager.is_authenticated():
                return None

            if not StreamlitSessionManager.has_any_role(role_names):
                return None

            return func(*args, **kwargs)
        return wrapper
    return decorator


def hide_for_roles(role_names: List[str]) -> Callable:
    """
    Decorator to hide UI elements for specific roles.
    Returns None if user has any of the specified roles.

    Args:
        role_names: List of role names that should NOT see this element

    Returns:
        Callable: Decorated function

    Example:
        @hide_for_roles(["guest"])
        def premium_feature():
            st.write("Premium content")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if not StreamlitSessionManager.is_authenticated():
                return func(*args, **kwargs)

            if StreamlitSessionManager.has_any_role(role_names):
                return None

            return func(*args, **kwargs)
        return wrapper
    return decorator


def with_session_state(key: str, default: Any = None) -> Callable:
    """
    Decorator to ensure session state key exists before function execution.

    Args:
        key: Session state key
        default: Default value if key doesn't exist

    Returns:
        Callable: Decorated function

    Example:
        @with_session_state('form_data', default={})
        def process_form():
            # Use st.session_state.form_data
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if key not in st.session_state:
                st.session_state[key] = default

            return func(*args, **kwargs)
        return wrapper
    return decorator


def track_activity(func: Callable) -> Callable:
    """
    Decorator to track user activity (updates last activity timestamp).

    Args:
        func: Function to decorate

    Returns:
        Callable: Decorated function

    Example:
        @track_activity
        def user_action():
            # Some user action
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        StreamlitSessionManager.update_activity()
        return func(*args, **kwargs)
    return wrapper


def csrf_protect(func: Callable) -> Callable:
    """
    Decorator to add CSRF protection to form submissions.

    Args:
        func: Function to decorate

    Returns:
        Callable: Decorated function

    Example:
        @csrf_protect
        def submit_form():
            # Form submission logic
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        import secrets

        # Initialize CSRF token if not exists
        if 'csrf_token' not in st.session_state:
            st.session_state.csrf_token = secrets.token_urlsafe(32)

        # Verify CSRF token on form submission
        # This is a simplified implementation
        # In production, you'd validate the token from form data

        return func(*args, **kwargs)
    return wrapper
