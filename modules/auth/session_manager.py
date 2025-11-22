"""
Session manager for Streamlit integration.
Manages user sessions using st.session_state.
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import streamlit as st
from sqlalchemy.orm import Session

from modules.database.models import User, UserSession
from modules.auth.authentication import get_user_by_token, verify_token


class StreamlitSessionManager:
    """Manages user sessions in Streamlit."""

    SESSION_TIMEOUT_MINUTES = 60  # Default session timeout

    @staticmethod
    def init_session_state() -> None:
        """Initialize session state variables."""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False

        if 'user' not in st.session_state:
            st.session_state.user = None

        if 'access_token' not in st.session_state:
            st.session_state.access_token = None

        if 'refresh_token' not in st.session_state:
            st.session_state.refresh_token = None

        if 'last_activity' not in st.session_state:
            st.session_state.last_activity = None

        if 'remember_me' not in st.session_state:
            st.session_state.remember_me = False

    @staticmethod
    def login(
        user: User,
        access_token: str,
        refresh_token: str,
        remember_me: bool = False
    ) -> None:
        """
        Log in user and set session state.

        Args:
            user: User object
            access_token: JWT access token
            refresh_token: JWT refresh token
            remember_me: Remember me flag
        """
        StreamlitSessionManager.init_session_state()

        st.session_state.authenticated = True
        st.session_state.user = {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'full_name': user.full_name,
            'avatar_url': user.avatar_url,
            'roles': [role.name for role in user.roles],
            'is_verified': user.is_verified,
            'is_active': user.is_active
        }
        st.session_state.access_token = access_token
        st.session_state.refresh_token = refresh_token
        st.session_state.remember_me = remember_me
        st.session_state.last_activity = datetime.utcnow()

    @staticmethod
    def logout() -> None:
        """Log out user and clear session state."""
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.access_token = None
        st.session_state.refresh_token = None
        st.session_state.remember_me = False
        st.session_state.last_activity = None

    @staticmethod
    def is_authenticated() -> bool:
        """
        Check if user is authenticated.

        Returns:
            bool: True if authenticated, False otherwise
        """
        StreamlitSessionManager.init_session_state()
        return st.session_state.get('authenticated', False)

    @staticmethod
    def get_current_user() -> Optional[Dict[str, Any]]:
        """
        Get current authenticated user.

        Returns:
            Optional[Dict]: User data or None if not authenticated
        """
        StreamlitSessionManager.init_session_state()
        if not StreamlitSessionManager.is_authenticated():
            return None
        return st.session_state.get('user')

    @staticmethod
    def get_user_id() -> Optional[int]:
        """
        Get current user ID.

        Returns:
            Optional[int]: User ID or None if not authenticated
        """
        user = StreamlitSessionManager.get_current_user()
        return user['id'] if user else None

    @staticmethod
    def get_user_email() -> Optional[str]:
        """
        Get current user email.

        Returns:
            Optional[str]: User email or None if not authenticated
        """
        user = StreamlitSessionManager.get_current_user()
        return user['email'] if user else None

    @staticmethod
    def get_user_roles() -> list:
        """
        Get current user roles.

        Returns:
            list: List of role names
        """
        user = StreamlitSessionManager.get_current_user()
        return user['roles'] if user else []

    @staticmethod
    def has_role(role_name: str) -> bool:
        """
        Check if current user has a specific role.

        Args:
            role_name: Role name to check

        Returns:
            bool: True if user has role, False otherwise
        """
        roles = StreamlitSessionManager.get_user_roles()
        return role_name in roles

    @staticmethod
    def has_any_role(role_names: list) -> bool:
        """
        Check if current user has any of the specified roles.

        Args:
            role_names: List of role names to check

        Returns:
            bool: True if user has any role, False otherwise
        """
        user_roles = set(StreamlitSessionManager.get_user_roles())
        return bool(user_roles.intersection(set(role_names)))

    @staticmethod
    def is_admin() -> bool:
        """
        Check if current user is admin.

        Returns:
            bool: True if admin, False otherwise
        """
        return StreamlitSessionManager.has_role('admin')

    @staticmethod
    def is_manager() -> bool:
        """
        Check if current user is manager or admin.

        Returns:
            bool: True if manager or admin, False otherwise
        """
        return StreamlitSessionManager.has_any_role(['admin', 'manager'])

    @staticmethod
    def check_session_timeout() -> bool:
        """
        Check if session has timed out.

        Returns:
            bool: True if session is valid, False if timed out
        """
        StreamlitSessionManager.init_session_state()

        if not StreamlitSessionManager.is_authenticated():
            return False

        last_activity = st.session_state.get('last_activity')
        remember_me = st.session_state.get('remember_me', False)

        if not last_activity:
            return False

        # Calculate timeout duration
        if remember_me:
            timeout_minutes = 60 * 24 * 30  # 30 days for remember me
        else:
            timeout_minutes = StreamlitSessionManager.SESSION_TIMEOUT_MINUTES

        timeout_delta = timedelta(minutes=timeout_minutes)
        is_valid = datetime.utcnow() - last_activity < timeout_delta

        if not is_valid:
            # Session timed out, log out user
            StreamlitSessionManager.logout()
            return False

        # Update last activity
        st.session_state.last_activity = datetime.utcnow()
        return True

    @staticmethod
    def update_activity() -> None:
        """Update last activity timestamp."""
        if StreamlitSessionManager.is_authenticated():
            st.session_state.last_activity = datetime.utcnow()

    @staticmethod
    def get_access_token() -> Optional[str]:
        """
        Get access token.

        Returns:
            Optional[str]: Access token or None
        """
        StreamlitSessionManager.init_session_state()
        return st.session_state.get('access_token')

    @staticmethod
    def get_refresh_token() -> Optional[str]:
        """
        Get refresh token.

        Returns:
            Optional[str]: Refresh token or None
        """
        StreamlitSessionManager.init_session_state()
        return st.session_state.get('refresh_token')

    @staticmethod
    def validate_session(db: Session) -> bool:
        """
        Validate current session against database.

        Args:
            db: Database session

        Returns:
            bool: True if session is valid, False otherwise
        """
        StreamlitSessionManager.init_session_state()

        if not StreamlitSessionManager.is_authenticated():
            return False

        # Check session timeout
        if not StreamlitSessionManager.check_session_timeout():
            return False

        # Verify token
        access_token = StreamlitSessionManager.get_access_token()
        if not access_token:
            StreamlitSessionManager.logout()
            return False

        # Get user from token
        user = get_user_by_token(db, access_token)
        if not user:
            StreamlitSessionManager.logout()
            return False

        # Check if user is still active
        if not user.is_active:
            StreamlitSessionManager.logout()
            return False

        # Update activity
        StreamlitSessionManager.update_activity()
        return True

    @staticmethod
    def require_auth(page_name: str = "Login") -> bool:
        """
        Require authentication for a page.
        Redirects to login if not authenticated.

        Args:
            page_name: Name of login page to redirect to

        Returns:
            bool: True if authenticated, False otherwise
        """
        StreamlitSessionManager.init_session_state()

        if not StreamlitSessionManager.is_authenticated():
            st.warning("⚠️ Please log in to access this page")
            st.info(f"👉 Navigate to **{page_name}** page to log in")
            st.stop()
            return False

        if not StreamlitSessionManager.check_session_timeout():
            st.error("⏰ Your session has expired. Please log in again.")
            st.stop()
            return False

        return True

    @staticmethod
    def require_role(role_name: str) -> bool:
        """
        Require specific role for a page.

        Args:
            role_name: Required role name

        Returns:
            bool: True if user has role, False otherwise
        """
        if not StreamlitSessionManager.require_auth():
            return False

        if not StreamlitSessionManager.has_role(role_name):
            st.error(f"❌ Access Denied: You need the '{role_name}' role to access this page")
            st.stop()
            return False

        return True

    @staticmethod
    def require_any_role(role_names: list) -> bool:
        """
        Require any of specified roles for a page.

        Args:
            role_names: List of acceptable role names

        Returns:
            bool: True if user has any role, False otherwise
        """
        if not StreamlitSessionManager.require_auth():
            return False

        if not StreamlitSessionManager.has_any_role(role_names):
            st.error(
                f"❌ Access Denied: You need one of these roles to access this page: "
                f"{', '.join(role_names)}"
            )
            st.stop()
            return False

        return True

    @staticmethod
    def display_user_info(show_avatar: bool = True) -> None:
        """
        Display current user info in sidebar.

        Args:
            show_avatar: Whether to show avatar
        """
        if not StreamlitSessionManager.is_authenticated():
            return

        user = StreamlitSessionManager.get_current_user()
        if not user:
            return

        with st.sidebar:
            st.divider()

            if show_avatar and user.get('avatar_url'):
                st.image(user['avatar_url'], width=100)

            st.markdown(f"**👤 {user['full_name']}**")
            st.caption(f"@{user['username']}")
            st.caption(f"📧 {user['email']}")

            roles = user.get('roles', [])
            if roles:
                st.caption(f"🎭 Roles: {', '.join(roles)}")

            st.divider()
