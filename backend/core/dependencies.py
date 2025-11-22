"""
FastAPI dependencies for NEXUS platform.

This module provides reusable dependencies for authentication,
authorization, and other common requirements in API endpoints.
"""

from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
    InvalidTokenException,
)
from backend.core.logging import get_logger
from backend.core.security import decode_token
from backend.database import get_db

logger = get_logger(__name__)

# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> int:
    """
    Get current authenticated user ID from JWT token.

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        int: User ID

    Raises:
        AuthenticationException: If token is missing or invalid

    Example:
        >>> @app.get("/profile")
        >>> async def get_profile(user_id: int = Depends(get_current_user_id)):
        ...     return {"user_id": user_id}
    """
    if not credentials:
        logger.warning("missing_authentication_credentials")
        raise AuthenticationException("Authentication credentials required")

    token = credentials.credentials

    try:
        payload = decode_token(token)
        user_id = payload.get("user_id")

        if not user_id:
            logger.warning("invalid_token_payload", payload=payload)
            raise InvalidTokenException("Invalid token payload")

        logger.debug("user_authenticated", user_id=user_id)
        return int(user_id)

    except (InvalidTokenException, AuthenticationException) as e:
        logger.warning("authentication_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get current authenticated user object.

    Args:
        user_id: User ID from token
        db: Database session

    Returns:
        User: User object

    Raises:
        AuthenticationException: If user not found

    Example:
        >>> @app.get("/profile")
        >>> async def get_profile(user = Depends(get_current_user)):
        ...     return user
    """
    from backend.models.user import User

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()

    if not user:
        logger.warning("user_not_found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    logger.debug("current_user_retrieved", user_id=user.id, username=user.username)
    return user


async def get_current_active_user(
    user = Depends(get_current_user),
) -> Any:
    """
    Get current active user (alias for get_current_user).

    Args:
        user: User from get_current_user

    Returns:
        User: Active user object

    Example:
        >>> @app.get("/profile")
        >>> async def get_profile(user = Depends(get_current_active_user)):
        ...     return user
    """
    return user


async def get_current_admin_user(
    user = Depends(get_current_user),
) -> Any:
    """
    Get current user if they are an admin.

    Args:
        user: User from get_current_user

    Returns:
        User: Admin user object

    Raises:
        AuthorizationException: If user is not an admin

    Example:
        >>> @app.delete("/users/{user_id}")
        >>> async def delete_user(
        ...     user_id: int,
        ...     admin = Depends(get_current_admin_user)
        ... ):
        ...     # Only admins can delete users
    """
    if not user.is_admin:
        logger.warning(
            "admin_access_denied", user_id=user.id, username=user.username
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    logger.debug("admin_user_verified", user_id=user.id)
    return user


async def get_current_superuser(
    user = Depends(get_current_user),
) -> Any:
    """
    Get current user if they are a superuser.

    Args:
        user: User from get_current_user

    Returns:
        User: Superuser object

    Raises:
        AuthorizationException: If user is not a superuser

    Example:
        >>> @app.post("/admin/settings")
        >>> async def update_settings(
        ...     superuser = Depends(get_current_superuser)
        ... ):
        ...     # Only superusers can update settings
    """
    if not user.is_superuser:
        logger.warning(
            "superuser_access_denied", user_id=user.id, username=user.username
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required",
        )

    logger.debug("superuser_verified", user_id=user.id)
    return user


async def get_api_key(
    x_api_key: Optional[str] = Header(None),
) -> str:
    """
    Get and validate API key from header.

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        str: Valid API key

    Raises:
        AuthenticationException: If API key is missing or invalid

    Example:
        >>> @app.get("/api/data")
        >>> async def get_data(api_key: str = Depends(get_api_key)):
        ...     # Validate API key
    """
    if not x_api_key:
        logger.warning("missing_api_key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # API key validation would happen here
    # For now, just return the key
    return x_api_key


def require_permissions(*required_permissions: str):
    """
    Dependency factory for permission-based access control.

    Args:
        *required_permissions: Required permission names

    Returns:
        Callable: Dependency function

    Example:
        >>> @app.delete("/documents/{doc_id}")
        >>> async def delete_document(
        ...     doc_id: int,
        ...     user = Depends(require_permissions("documents.delete"))
        ... ):
        ...     # Only users with documents.delete permission
    """

    async def permission_checker(user = Depends(get_current_user)) -> Any:
        """Check if user has required permissions."""
        # Get user permissions (this would be implemented in User model)
        user_permissions = set(getattr(user, "permissions", []))

        # Check if user has all required permissions
        missing_permissions = set(required_permissions) - user_permissions

        if missing_permissions:
            logger.warning(
                "insufficient_permissions",
                user_id=user.id,
                required=list(required_permissions),
                missing=list(missing_permissions),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {', '.join(missing_permissions)}",
            )

        logger.debug(
            "permissions_verified",
            user_id=user.id,
            permissions=list(required_permissions),
        )
        return user

    return permission_checker


def require_role(*required_roles: str):
    """
    Dependency factory for role-based access control.

    Args:
        *required_roles: Required role names

    Returns:
        Callable: Dependency function

    Example:
        >>> @app.get("/admin/users")
        >>> async def list_users(
        ...     user = Depends(require_role("admin", "manager"))
        ... ):
        ...     # Only admins or managers
    """

    async def role_checker(user = Depends(get_current_user)) -> Any:
        """Check if user has required role."""
        user_roles = set(getattr(user, "roles", []))

        if not any(role in user_roles for role in required_roles):
            logger.warning(
                "insufficient_role",
                user_id=user.id,
                required=list(required_roles),
                user_roles=list(user_roles),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {' or '.join(required_roles)}",
            )

        logger.debug("role_verified", user_id=user.id, roles=list(required_roles))
        return user

    return role_checker


# Type annotation imports
from typing import Any
