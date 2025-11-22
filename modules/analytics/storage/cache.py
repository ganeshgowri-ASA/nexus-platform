"""
Redis Cache

Redis caching layer with decorators and TTL management.
"""

import functools
import hashlib
import json
import logging
import pickle
from typing import Any, Callable, Optional, Union

import redis
from redis import asyncio as aioredis

from shared.constants import (
    CACHE_TTL_SHORT,
    CACHE_TTL_MEDIUM,
    CACHE_TTL_LONG,
    CACHE_TTL_DAY,
)

logger = logging.getLogger(__name__)


class CacheConfig:
    """Redis cache configuration."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        ssl: bool = False,
        decode_responses: bool = False,
        max_connections: int = 50,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5,
        retry_on_timeout: bool = True,
    ):
        """
        Initialize cache configuration.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            ssl: Use SSL connection
            decode_responses: Decode byte responses to strings
            max_connections: Maximum connection pool size
            socket_timeout: Socket timeout in seconds
            socket_connect_timeout: Socket connect timeout in seconds
            retry_on_timeout: Retry on timeout
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.ssl = ssl
        self.decode_responses = decode_responses
        self.max_connections = max_connections
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self.retry_on_timeout = retry_on_timeout


class RedisCache:
    """Redis cache manager."""

    def __init__(self, config: CacheConfig, key_prefix: str = "nexus:analytics"):
        """
        Initialize Redis cache.

        Args:
            config: Cache configuration
            key_prefix: Prefix for all cache keys
        """
        self.config = config
        self.key_prefix = key_prefix
        self._client: Optional[redis.Redis] = None
        self._async_client: Optional[aioredis.Redis] = None

        logger.info(f"Redis cache initialized with prefix: {key_prefix}")

    def get_client(self) -> redis.Redis:
        """
        Get or create Redis client.

        Returns:
            Redis client
        """
        if self._client is None:
            self._client = redis.Redis(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                ssl=self.config.ssl,
                decode_responses=self.config.decode_responses,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                retry_on_timeout=self.config.retry_on_timeout,
            )
            logger.info(f"Created Redis client: {self.config.host}:{self.config.port}")

        return self._client

    def get_async_client(self) -> aioredis.Redis:
        """
        Get or create async Redis client.

        Returns:
            Async Redis client
        """
        if self._async_client is None:
            self._async_client = aioredis.Redis(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                ssl=self.config.ssl,
                decode_responses=self.config.decode_responses,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                retry_on_timeout=self.config.retry_on_timeout,
            )
            logger.info(f"Created async Redis client: {self.config.host}:{self.config.port}")

        return self._async_client

    def _make_key(self, key: str) -> str:
        """
        Create full cache key with prefix.

        Args:
            key: Key name

        Returns:
            Full cache key
        """
        return f"{self.key_prefix}:{key}"

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.

        Args:
            key: Cache key
            default: Default value if not found

        Returns:
            Cached value or default

        Example:
            >>> cache.get("user:123")
        """
        try:
            client = self.get_client()
            full_key = self._make_key(key)
            value = client.get(full_key)

            if value is None:
                logger.debug(f"Cache miss: {key}")
                return default

            logger.debug(f"Cache hit: {key}")
            return pickle.loads(value)

        except Exception as e:
            logger.error(f"Cache get error for {key}: {e}", exc_info=True)
            return default

    async def async_get(self, key: str, default: Any = None) -> Any:
        """
        Asynchronously get value from cache.

        Args:
            key: Cache key
            default: Default value if not found

        Returns:
            Cached value or default
        """
        try:
            client = self.get_async_client()
            full_key = self._make_key(key)
            value = await client.get(full_key)

            if value is None:
                logger.debug(f"Cache miss: {key}")
                return default

            logger.debug(f"Cache hit: {key}")
            return pickle.loads(value)

        except Exception as e:
            logger.error(f"Cache get error for {key}: {e}", exc_info=True)
            return default

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = CACHE_TTL_MEDIUM,
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds

        Returns:
            True if successful, False otherwise

        Example:
            >>> cache.set("user:123", user_data, ttl=3600)
        """
        try:
            client = self.get_client()
            full_key = self._make_key(key)
            serialized = pickle.dumps(value)

            if ttl:
                client.setex(full_key, ttl, serialized)
            else:
                client.set(full_key, serialized)

            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True

        except Exception as e:
            logger.error(f"Cache set error for {key}: {e}", exc_info=True)
            return False

    async def async_set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = CACHE_TTL_MEDIUM,
    ) -> bool:
        """
        Asynchronously set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            client = self.get_async_client()
            full_key = self._make_key(key)
            serialized = pickle.dumps(value)

            if ttl:
                await client.setex(full_key, ttl, serialized)
            else:
                await client.set(full_key, serialized)

            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True

        except Exception as e:
            logger.error(f"Cache set error for {key}: {e}", exc_info=True)
            return False

    def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False otherwise

        Example:
            >>> cache.delete("user:123")
        """
        try:
            client = self.get_client()
            full_key = self._make_key(key)
            result = client.delete(full_key)
            logger.debug(f"Cache delete: {key}")
            return result > 0

        except Exception as e:
            logger.error(f"Cache delete error for {key}: {e}", exc_info=True)
            return False

    async def async_delete(self, key: str) -> bool:
        """
        Asynchronously delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False otherwise
        """
        try:
            client = self.get_async_client()
            full_key = self._make_key(key)
            result = await client.delete(full_key)
            logger.debug(f"Cache delete: {key}")
            return result > 0

        except Exception as e:
            logger.error(f"Cache delete error for {key}: {e}", exc_info=True)
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.

        Args:
            pattern: Key pattern (supports wildcards)

        Returns:
            Number of keys deleted

        Example:
            >>> cache.delete_pattern("user:*")
        """
        try:
            client = self.get_client()
            full_pattern = self._make_key(pattern)
            keys = client.keys(full_pattern)

            if keys:
                count = client.delete(*keys)
                logger.info(f"Cache pattern delete: {pattern} ({count} keys)")
                return count

            return 0

        except Exception as e:
            logger.error(f"Cache pattern delete error for {pattern}: {e}", exc_info=True)
            return 0

    async def async_delete_pattern(self, pattern: str) -> int:
        """
        Asynchronously delete all keys matching pattern.

        Args:
            pattern: Key pattern (supports wildcards)

        Returns:
            Number of keys deleted
        """
        try:
            client = self.get_async_client()
            full_pattern = self._make_key(pattern)
            keys = []

            async for key in client.scan_iter(full_pattern):
                keys.append(key)

            if keys:
                count = await client.delete(*keys)
                logger.info(f"Cache pattern delete: {pattern} ({count} keys)")
                return count

            return 0

        except Exception as e:
            logger.error(f"Cache pattern delete error for {pattern}: {e}", exc_info=True)
            return 0

    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if exists, False otherwise

        Example:
            >>> if cache.exists("user:123"):
            ...     print("User cached")
        """
        try:
            client = self.get_client()
            full_key = self._make_key(key)
            return client.exists(full_key) > 0

        except Exception as e:
            logger.error(f"Cache exists error for {key}: {e}", exc_info=True)
            return False

    async def async_exists(self, key: str) -> bool:
        """
        Asynchronously check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if exists, False otherwise
        """
        try:
            client = self.get_async_client()
            full_key = self._make_key(key)
            result = await client.exists(full_key)
            return result > 0

        except Exception as e:
            logger.error(f"Cache exists error for {key}: {e}", exc_info=True)
            return False

    def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """
        Increment numeric value in cache.

        Args:
            key: Cache key
            amount: Amount to increment
            ttl: Optional TTL for the key

        Returns:
            New value after increment

        Example:
            >>> cache.increment("page_views", 1)
        """
        try:
            client = self.get_client()
            full_key = self._make_key(key)
            value = client.incrby(full_key, amount)

            if ttl and client.ttl(full_key) == -1:
                client.expire(full_key, ttl)

            logger.debug(f"Cache increment: {key} by {amount} = {value}")
            return value

        except Exception as e:
            logger.error(f"Cache increment error for {key}: {e}", exc_info=True)
            return 0

    async def async_increment(
        self, key: str, amount: int = 1, ttl: Optional[int] = None
    ) -> int:
        """
        Asynchronously increment numeric value in cache.

        Args:
            key: Cache key
            amount: Amount to increment
            ttl: Optional TTL for the key

        Returns:
            New value after increment
        """
        try:
            client = self.get_async_client()
            full_key = self._make_key(key)
            value = await client.incrby(full_key, amount)

            if ttl:
                current_ttl = await client.ttl(full_key)
                if current_ttl == -1:
                    await client.expire(full_key, ttl)

            logger.debug(f"Cache increment: {key} by {amount} = {value}")
            return value

        except Exception as e:
            logger.error(f"Cache increment error for {key}: {e}", exc_info=True)
            return 0

    def flush(self) -> bool:
        """
        Flush all keys with prefix.

        Warning:
            This will delete all cached data for this prefix.

        Returns:
            True if successful

        Example:
            >>> cache.flush()
        """
        try:
            count = self.delete_pattern("*")
            logger.warning(f"Cache flushed: {count} keys deleted")
            return True

        except Exception as e:
            logger.error(f"Cache flush error: {e}", exc_info=True)
            return False

    async def async_flush(self) -> bool:
        """
        Asynchronously flush all keys with prefix.

        Returns:
            True if successful
        """
        try:
            count = await self.async_delete_pattern("*")
            logger.warning(f"Cache flushed: {count} keys deleted")
            return True

        except Exception as e:
            logger.error(f"Cache flush error: {e}", exc_info=True)
            return False

    def health_check(self) -> bool:
        """
        Perform cache health check.

        Returns:
            True if healthy, False otherwise

        Example:
            >>> if cache.health_check():
            ...     print("Cache is healthy")
        """
        try:
            client = self.get_client()
            client.ping()
            logger.info("Cache health check passed")
            return True

        except Exception as e:
            logger.error(f"Cache health check failed: {e}", exc_info=True)
            return False

    async def async_health_check(self) -> bool:
        """
        Asynchronously perform cache health check.

        Returns:
            True if healthy, False otherwise
        """
        try:
            client = self.get_async_client()
            await client.ping()
            logger.info("Cache health check passed")
            return True

        except Exception as e:
            logger.error(f"Cache health check failed: {e}", exc_info=True)
            return False

    def close(self) -> None:
        """Close Redis connections."""
        if self._client:
            self._client.close()
            logger.info("Redis client closed")

    async def async_close(self) -> None:
        """Close async Redis connections."""
        if self._async_client:
            await self._async_client.close()
            logger.info("Async Redis client closed")


def _make_cache_key(func: Callable, args: tuple, kwargs: dict) -> str:
    """
    Generate cache key from function and arguments.

    Args:
        func: Function
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        Cache key
    """
    # Create key from function name and arguments
    key_parts = [func.__module__, func.__name__]

    # Add args
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))
        else:
            key_parts.append(hashlib.md5(str(arg).encode()).hexdigest()[:8])

    # Add kwargs
    for k, v in sorted(kwargs.items()):
        if isinstance(v, (str, int, float, bool)):
            key_parts.append(f"{k}={v}")
        else:
            key_parts.append(f"{k}={hashlib.md5(str(v).encode()).hexdigest()[:8]}")

    return ":".join(key_parts)


def cached(ttl: int = CACHE_TTL_MEDIUM, key_prefix: Optional[str] = None):
    """
    Decorator to cache function results.

    Args:
        ttl: Time to live in seconds
        key_prefix: Optional key prefix

    Example:
        >>> @cached(ttl=3600)
        ... def get_user(user_id):
        ...     return fetch_user(user_id)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get cache instance (assumes it's passed as first arg or in kwargs)
            cache = kwargs.get("cache") or (args[0] if args and isinstance(args[0], RedisCache) else None)

            if not cache or not isinstance(cache, RedisCache):
                # No cache available, execute function
                return func(*args, **kwargs)

            # Generate cache key
            cache_key = _make_cache_key(func, args[1:] if args else (), kwargs)
            if key_prefix:
                cache_key = f"{key_prefix}:{cache_key}"

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl)

            return result

        return wrapper

    return decorator


def async_cached(ttl: int = CACHE_TTL_MEDIUM, key_prefix: Optional[str] = None):
    """
    Decorator to cache async function results.

    Args:
        ttl: Time to live in seconds
        key_prefix: Optional key prefix

    Example:
        >>> @async_cached(ttl=3600)
        ... async def get_user(user_id):
        ...     return await fetch_user(user_id)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get cache instance
            cache = kwargs.get("cache") or (args[0] if args and isinstance(args[0], RedisCache) else None)

            if not cache or not isinstance(cache, RedisCache):
                # No cache available, execute function
                return await func(*args, **kwargs)

            # Generate cache key
            cache_key = _make_cache_key(func, args[1:] if args else (), kwargs)
            if key_prefix:
                cache_key = f"{key_prefix}:{cache_key}"

            # Try to get from cache
            cached_value = await cache.async_get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.async_set(cache_key, result, ttl=ttl)

            return result

        return wrapper

    return decorator


# Global cache instance
_cache_instance: Optional[RedisCache] = None


def init_cache(config: CacheConfig, key_prefix: str = "nexus:analytics") -> RedisCache:
    """
    Initialize global cache instance.

    Args:
        config: Cache configuration
        key_prefix: Key prefix

    Returns:
        Cache instance

    Example:
        >>> config = CacheConfig(host="localhost")
        >>> cache = init_cache(config)
    """
    global _cache_instance
    _cache_instance = RedisCache(config, key_prefix)
    logger.info("Global cache instance initialized")
    return _cache_instance


def get_cache() -> RedisCache:
    """
    Get global cache instance.

    Returns:
        Cache instance

    Raises:
        RuntimeError: If cache not initialized

    Example:
        >>> cache = get_cache()
        >>> cache.set("key", "value")
    """
    if _cache_instance is None:
        raise RuntimeError("Cache not initialized. Call init_cache() first.")
    return _cache_instance
