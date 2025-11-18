"""
Session management utilities for NEXUS Platform frontend.

This module handles user authentication and session state.
"""

import streamlit as st
from typing import Optional


def is_authenticated() -> bool:
    """Check if user is authenticated."""
    return "access_token" in st.session_state and st.session_state.access_token


def require_auth():
    """Require authentication to access page."""
    if not is_authenticated():
        st.warning("Please login to access this page")
        st.stop()


def login_user(access_token: str, refresh_token: str, user_data: dict):
    """Store login session data."""
    st.session_state.access_token = access_token
    st.session_state.refresh_token = refresh_token
    st.session_state.user = user_data


def logout_user():
    """Clear session data."""
    st.session_state.clear()


def get_current_user() -> Optional[dict]:
    """Get current user from session."""
    return st.session_state.get("user")
