"""
NEXUS Platform - Redis Client Configuration
"""
import json
from typing import Any, Optional
import redis
from redis.exceptions import RedisError

from backend.app.core.config import settings
from backend.app.core.exceptions import CacheException


class RedisClient:
    """Redis client wrapper for caching operations."""

    def __init__(self):
        """Initialize Redis client."""
        try:
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            self.client.ping()
        except RedisError as e:
            raise CacheException(
                message="Failed to connect to Redis",
                details={"error": str(e)}
            )

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found

        Raises:
            CacheException: If cache operation fails
        """
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except RedisError as e:
            raise CacheException(
                message="Failed to get value from cache",
                details={"key": key, "error": str(e)}
            )

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)

        Returns:
            True if successful

        Raises:
            CacheException: If cache operation fails
        """
        try:
            serialized_value = json.dumps(value)
            if ttl:
                return self.client.setex(key, ttl, serialized_value)
            return self.client.set(key, serialized_value)
        except (RedisError, TypeError) as e:
            raise CacheException(
                message="Failed to set value in cache",
                details={"key": key, "error": str(e)}
            )

    def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted

        Raises:
            CacheException: If cache operation fails
        """
        try:
            return bool(self.client.delete(key))
        except RedisError as e:
            raise CacheException(
                message="Failed to delete value from cache",
                details={"key": key, "error": str(e)}
            )

    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists

        Raises:
            CacheException: If cache operation fails
        """
        try:
            return bool(self.client.exists(key))
        except RedisError as e:
            raise CacheException(
                message="Failed to check key existence in cache",
                details={"key": key, "error": str(e)}
            )

    def clear_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Key pattern (e.g., "attribution:*")

        Returns:
            Number of keys deleted

        Raises:
            CacheException: If cache operation fails
        """
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except RedisError as e:
            raise CacheException(
                message="Failed to clear cache pattern",
                details={"pattern": pattern, "error": str(e)}
            )

    def ping(self) -> bool:
        """
        Test Redis connection.

        Returns:
            True if connection is alive

        Raises:
            CacheException: If connection fails
        """
        try:
            return self.client.ping()
        except RedisError as e:
            raise CacheException(
                message="Redis connection failed",
                details={"error": str(e)}
            )


# Global Redis client instance
redis_client = RedisClient()
