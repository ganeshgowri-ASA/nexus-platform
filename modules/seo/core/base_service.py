"""
Base service class for all SEO services.

Provides common functionality for all SEO service implementations.
"""

from typing import Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from modules.seo.config.database import db_manager
from modules.seo.config.redis import redis_manager
from modules.seo.config.settings import Settings, get_settings
from modules.seo.utils.http_client import HTTPClient


class BaseService:
    """
    Base class for all SEO services.

    Provides common functionality including database access,
    caching, HTTP client, and settings.
    """

    def __init__(
        self,
        session: Optional[AsyncSession] = None,
        settings: Optional[Settings] = None,
    ):
        """
        Initialize service.

        Args:
            session: Database session (optional)
            settings: Application settings (optional)
        """
        self.session = session
        self.settings = settings or get_settings()
        self.redis = redis_manager
        self._http_client: Optional[HTTPClient] = None

    @property
    def http_client(self) -> HTTPClient:
        """
        Get HTTP client instance.

        Returns:
            HTTPClient: HTTP client for making requests
        """
        if self._http_client is None:
            self._http_client = HTTPClient()
        return self._http_client

    async def get_db_session(self) -> AsyncSession:
        """
        Get database session.

        Returns:
            AsyncSession: Database session

        Raises:
            RuntimeError: If session not available
        """
        if self.session is None:
            async with db_manager.get_session() as session:
                return session
        return self.session

    async def cache_get(self, key: str):
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        try:
            return await self.redis.get(key)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    async def cache_set(self, key: str, value, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds

        Returns:
            True if successful
        """
        try:
            return await self.redis.set(key, value, ttl=ttl)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def cache_delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if successful
        """
        try:
            return await self.redis.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self._http_client:
            await self._http_client.close()

    def log_info(self, message: str, **kwargs) -> None:
        """Log info message with context."""
        logger.info(f"[{self.__class__.__name__}] {message}", **kwargs)

    def log_error(self, message: str, **kwargs) -> None:
        """Log error message with context."""
        logger.error(f"[{self.__class__.__name__}] {message}", **kwargs)

    def log_debug(self, message: str, **kwargs) -> None:
        """Log debug message with context."""
        logger.debug(f"[{self.__class__.__name__}] {message}", **kwargs)
