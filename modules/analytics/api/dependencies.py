"""
FastAPI Dependencies

Dependency injection for FastAPI routes.
"""

import logging
from typing import Generator

from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from modules.analytics.storage.cache import RedisCache, get_cache
from modules.analytics.storage.database import Database, get_database

logger = logging.getLogger(__name__)


def get_db_session() -> Generator[Session, None, None]:
    """
    Get database session dependency.

    Yields:
        Database session
    """
    db = get_database()
    with db.session() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}", exc_info=True)
            raise


def get_cache_client() -> RedisCache:
    """
    Get cache client dependency.

    Returns:
        Cache client
    """
    try:
        return get_cache()
    except Exception as e:
        logger.error(f"Cache client error: {e}", exc_info=True)
        raise


def get_current_user(authorization: str = Header(None)) -> dict:
    """
    Get current user from authorization header.

    Args:
        authorization: Authorization header

    Returns:
        User dict

    Raises:
        HTTPException: If authentication fails
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # TODO: Implement actual authentication
    # For now, return a mock user
    return {"id": "user123", "email": "user@example.com"}


def verify_api_key(x_api_key: str = Header(None)) -> bool:
    """
    Verify API key.

    Args:
        x_api_key: API key header

    Returns:
        True if valid

    Raises:
        HTTPException: If API key invalid
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )

    # TODO: Implement actual API key validation
    # For now, accept any non-empty key
    return True
