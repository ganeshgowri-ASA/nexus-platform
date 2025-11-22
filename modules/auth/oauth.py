"""
OAuth integration for Google and Microsoft authentication.
"""
import os
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
import requests

from modules.database.models import User, Role
from modules.auth.authentication import create_access_token, create_refresh_token


class OAuthProvider:
    """OAuth provider enumeration."""
    GOOGLE = "google"
    MICROSOFT = "microsoft"


class OAuthError(Exception):
    """Base exception for OAuth errors."""
    pass


class OAuthConfigurationError(OAuthError):
    """Raised when OAuth is not properly configured."""
    pass


class OAuthAuthenticationError(OAuthError):
    """Raised when OAuth authentication fails."""
    pass


class GoogleOAuth:
    """Google OAuth 2.0 integration."""

    AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    def __init__(self):
        """Initialize Google OAuth configuration."""
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8501/oauth/google/callback")

        if not self.client_id or not self.client_secret:
            raise OAuthConfigurationError(
                "Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET "
                "environment variables."
            )

    def get_authorization_url(self, state: str) -> str:
        """
        Get Google OAuth authorization URL.

        Args:
            state: State parameter for CSRF protection

        Returns:
            str: Authorization URL
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent"
        }

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.AUTHORIZATION_URL}?{query_string}"

    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code

        Returns:
            Dict: Token response

        Raises:
            OAuthAuthenticationError: If token exchange fails
        """
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri
        }

        try:
            response = requests.post(self.TOKEN_URL, data=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise OAuthAuthenticationError(f"Failed to exchange code for token: {str(e)}")

    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information from Google.

        Args:
            access_token: Access token

        Returns:
            Dict: User information

        Raises:
            OAuthAuthenticationError: If user info retrieval fails
        """
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = requests.get(self.USERINFO_URL, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise OAuthAuthenticationError(f"Failed to get user info: {str(e)}")


class MicrosoftOAuth:
    """Microsoft OAuth 2.0 integration."""

    AUTHORIZATION_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
    TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    USERINFO_URL = "https://graph.microsoft.com/v1.0/me"

    def __init__(self):
        """Initialize Microsoft OAuth configuration."""
        self.client_id = os.getenv("MICROSOFT_CLIENT_ID")
        self.client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
        self.redirect_uri = os.getenv("MICROSOFT_REDIRECT_URI", "http://localhost:8501/oauth/microsoft/callback")

        if not self.client_id or not self.client_secret:
            raise OAuthConfigurationError(
                "Microsoft OAuth not configured. Set MICROSOFT_CLIENT_ID and "
                "MICROSOFT_CLIENT_SECRET environment variables."
            )

    def get_authorization_url(self, state: str) -> str:
        """
        Get Microsoft OAuth authorization URL.

        Args:
            state: State parameter for CSRF protection

        Returns:
            str: Authorization URL
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile User.Read",
            "state": state,
            "response_mode": "query"
        }

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.AUTHORIZATION_URL}?{query_string}"

    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code

        Returns:
            Dict: Token response

        Raises:
            OAuthAuthenticationError: If token exchange fails
        """
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri
        }

        try:
            response = requests.post(self.TOKEN_URL, data=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise OAuthAuthenticationError(f"Failed to exchange code for token: {str(e)}")

    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information from Microsoft Graph.

        Args:
            access_token: Access token

        Returns:
            Dict: User information

        Raises:
            OAuthAuthenticationError: If user info retrieval fails
        """
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = requests.get(self.USERINFO_URL, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise OAuthAuthenticationError(f"Failed to get user info: {str(e)}")


def authenticate_with_oauth(
    db: Session,
    provider: str,
    oauth_id: str,
    email: str,
    full_name: str,
    avatar_url: Optional[str] = None
) -> Tuple[User, str, str]:
    """
    Authenticate or create user with OAuth.

    Args:
        db: Database session
        provider: OAuth provider (google, microsoft)
        oauth_id: OAuth provider user ID
        email: User email
        full_name: User full name
        avatar_url: User avatar URL

    Returns:
        Tuple[User, str, str]: (user, access_token, refresh_token)
    """
    # Check if user exists with this OAuth provider
    user = db.query(User).filter(
        User.oauth_provider == provider,
        User.oauth_id == oauth_id
    ).first()

    if not user:
        # Check if user exists with this email
        user = db.query(User).filter(User.email == email).first()

        if user:
            # Link OAuth account to existing user
            user.oauth_provider = provider
            user.oauth_id = oauth_id
            if avatar_url and not user.avatar_url:
                user.avatar_url = avatar_url
        else:
            # Create new user
            # Generate username from email
            username = email.split('@')[0]
            base_username = username

            # Ensure username is unique
            counter = 1
            while db.query(User).filter(User.username == username).first():
                username = f"{base_username}{counter}"
                counter += 1

            user = User(
                email=email,
                username=username,
                full_name=full_name,
                oauth_provider=provider,
                oauth_id=oauth_id,
                avatar_url=avatar_url,
                is_verified=True,  # OAuth users are auto-verified
                is_active=True,
                hashed_password=None  # No password for OAuth users
            )

            # Assign default role
            default_role = db.query(Role).filter(Role.name == "user").first()
            if default_role:
                user.roles.append(default_role)

            db.add(user)

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)

    # Create JWT tokens
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "username": user.username,
        "roles": [role.name for role in user.roles]
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return user, access_token, refresh_token


def handle_google_oauth(db: Session, code: str) -> Tuple[User, str, str]:
    """
    Handle Google OAuth callback.

    Args:
        db: Database session
        code: Authorization code

    Returns:
        Tuple[User, str, str]: (user, access_token, refresh_token)

    Raises:
        OAuthAuthenticationError: If authentication fails
    """
    google = GoogleOAuth()

    # Exchange code for token
    token_response = google.exchange_code_for_token(code)
    access_token = token_response.get("access_token")

    if not access_token:
        raise OAuthAuthenticationError("Failed to get access token")

    # Get user info
    user_info = google.get_user_info(access_token)

    oauth_id = user_info.get("id")
    email = user_info.get("email")
    full_name = user_info.get("name", email)
    avatar_url = user_info.get("picture")

    if not oauth_id or not email:
        raise OAuthAuthenticationError("Failed to get user information")

    # Authenticate or create user
    return authenticate_with_oauth(
        db=db,
        provider=OAuthProvider.GOOGLE,
        oauth_id=oauth_id,
        email=email,
        full_name=full_name,
        avatar_url=avatar_url
    )


def handle_microsoft_oauth(db: Session, code: str) -> Tuple[User, str, str]:
    """
    Handle Microsoft OAuth callback.

    Args:
        db: Database session
        code: Authorization code

    Returns:
        Tuple[User, str, str]: (user, access_token, refresh_token)

    Raises:
        OAuthAuthenticationError: If authentication fails
    """
    microsoft = MicrosoftOAuth()

    # Exchange code for token
    token_response = microsoft.exchange_code_for_token(code)
    access_token = token_response.get("access_token")

    if not access_token:
        raise OAuthAuthenticationError("Failed to get access token")

    # Get user info
    user_info = microsoft.get_user_info(access_token)

    oauth_id = user_info.get("id")
    email = user_info.get("mail") or user_info.get("userPrincipalName")
    full_name = user_info.get("displayName", email)
    avatar_url = None  # Microsoft Graph doesn't provide avatar URL directly

    if not oauth_id or not email:
        raise OAuthAuthenticationError("Failed to get user information")

    # Authenticate or create user
    return authenticate_with_oauth(
        db=db,
        provider=OAuthProvider.MICROSOFT,
        oauth_id=oauth_id,
        email=email,
        full_name=full_name,
        avatar_url=avatar_url
    )


def is_oauth_configured(provider: str) -> bool:
    """
    Check if OAuth provider is configured.

    Args:
        provider: OAuth provider name

    Returns:
        bool: True if configured, False otherwise
    """
    if provider == OAuthProvider.GOOGLE:
        return bool(os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET"))
    elif provider == OAuthProvider.MICROSOFT:
        return bool(os.getenv("MICROSOFT_CLIENT_ID") and os.getenv("MICROSOFT_CLIENT_SECRET"))
    return False
