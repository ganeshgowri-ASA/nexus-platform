"""
Redis configuration and client management.

This module provides Redis client configuration and caching utilities
for the NEXUS platform.
"""

import json
from typing import Any, Optional
import redis
from redis.exceptions import RedisError

from .settings import settings
from .logging_config import get_logger

logger = get_logger(__name__)


class RedisClient:
    """Redis client wrapper with caching utilities."""

    def __init__(self, url: str = settings.redis_url):
        """
        Initialize Redis client.

        Args:
            url: Redis connection URL.
        """
        try:
            self.client = redis.from_url(
                url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            # Test connection
            self.client.ping()
            logger.info("Redis client initialized successfully")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from Redis cache.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found.
        """
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except RedisError as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for key {key}: {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set value in Redis cache.

        Args:
            key: Cache key.
            value: Value to cache (will be JSON serialized).
            ttl: Time to live in seconds (default: from settings).

        Returns:
            True if successful, False otherwise.
        """
        try:
            ttl = ttl or settings.redis_cache_ttl
            serialized = json.dumps(value)
            self.client.setex(key, ttl, serialized)
            return True
        except (RedisError, TypeError, ValueError) as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete value from Redis cache.

        Args:
            key: Cache key.

        Returns:
            True if successful, False otherwise.
        """
        try:
            self.client.delete(key)
            return True
        except RedisError as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """
        Check if key exists in Redis cache.

        Args:
            key: Cache key.

        Returns:
            True if key exists, False otherwise.
        """
        try:
            return bool(self.client.exists(key))
        except RedisError as e:
            logger.error(f"Redis EXISTS error for key {key}: {e}")
            return False

    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment counter in Redis.

        Args:
            key: Counter key.
            amount: Amount to increment by.

        Returns:
            New counter value or None if error.
        """
        try:
            return self.client.incrby(key, amount)
        except RedisError as e:
            logger.error(f"Redis INCR error for key {key}: {e}")
            return None

    def set_with_expiry(
        self,
        key: str,
        value: Any,
        seconds: int,
    ) -> bool:
        """
        Set value with expiry time.

        Args:
            key: Cache key.
            value: Value to cache.
            seconds: Expiry time in seconds.

        Returns:
            True if successful, False otherwise.
        """
        return self.set(key, value, ttl=seconds)

    def get_or_set(
        self,
        key: str,
        default_func: callable,
        ttl: Optional[int] = None,
    ) -> Any:
        """
        Get value from cache or set it using default function.

        Args:
            key: Cache key.
            default_func: Function to call if key not found.
            ttl: Time to live in seconds.

        Returns:
            Cached or computed value.
        """
        value = self.get(key)
        if value is None:
            value = default_func()
            self.set(key, value, ttl=ttl)
        return value

    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern.

        Args:
            pattern: Key pattern (e.g., "user:*").

        Returns:
            Number of keys deleted.
        """
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except RedisError as e:
            logger.error(f"Redis CLEAR PATTERN error for {pattern}: {e}")
            return 0

    def ping(self) -> bool:
        """
        Test Redis connection.

        Returns:
            True if connected, False otherwise.
        """
        try:
            return self.client.ping()
        except RedisError:
            return False


# Global Redis client instance
redis_client = RedisClient()
