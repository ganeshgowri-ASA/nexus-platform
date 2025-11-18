"""
Redis configuration and caching utilities.

Provides Redis connection management, caching decorators,
and utilities for cache operations.
"""

import json
from functools import wraps
from typing import Any, Callable, Optional

import redis.asyncio as redis
from loguru import logger

from .settings import get_settings


class RedisManager:
    """
    Manages Redis connections and caching operations.

    Provides methods for caching, key management, and Redis operations.
    """

    def __init__(self) -> None:
        """Initialize Redis manager."""
        self.settings = get_settings()
        self._client: Optional[redis.Redis] = None

    async def get_client(self) -> redis.Redis:
        """
        Get or create Redis client.

        Returns:
            redis.Redis: Async Redis client
        """
        if self._client is None:
            self._client = await redis.from_url(
                self.settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50,
            )
        return self._client

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            client = await self.get_client()
            value = await client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: from settings)

        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self.get_client()
            ttl = ttl or self.settings.redis_cache_ttl
            serialized = json.dumps(value, default=str)
            await client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self.get_client()
            await client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        try:
            client = await self.get_client()
            return bool(await client.exists(key))
        except Exception as e:
            logger.error(f"Error checking cache key {key}: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.

        Args:
            pattern: Redis key pattern (e.g., "seo:*")

        Returns:
            Number of keys deleted
        """
        try:
            client = await self.get_client()
            keys = []
            async for key in client.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                return await client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Error clearing cache pattern {pattern}: {e}")
            return 0

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client is not None:
            await self._client.close()
            self._client = None


# Global Redis manager instance
redis_manager = RedisManager()


def cache(
    ttl: Optional[int] = None,
    key_prefix: str = "seo",
) -> Callable:
    """
    Decorator to cache function results in Redis.

    Args:
        ttl: Cache time to live in seconds
        key_prefix: Prefix for cache keys

    Returns:
        Decorated function

    Example:
        @cache(ttl=3600, key_prefix="keywords")
        async def get_keywords(domain: str):
            # Expensive operation
            return keywords
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [key_prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)

            # Try to get from cache
            cached_value = await redis_manager.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_value

            # Execute function and cache result
            logger.debug(f"Cache miss for key: {cache_key}")
            result = await func(*args, **kwargs)
            await redis_manager.set(cache_key, result, ttl=ttl)
            return result

        return wrapper

    return decorator
