"""Redis caching utilities for NEXUS platform.

This module provides Redis connection management and caching utilities.
"""

import json
import os
from typing import Any, Optional

import redis.asyncio as aioredis
import structlog
from redis import Redis

logger = structlog.get_logger(__name__)

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default

# Sync Redis client
redis_client: Optional[Redis] = None

# Async Redis client
async_redis_client: Optional[aioredis.Redis] = None


def get_redis() -> Redis:
    """Get synchronous Redis client.

    Returns:
        Redis client instance
    """
    global redis_client
    if redis_client is None:
        redis_client = Redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
        )
        logger.info("Redis client initialized")
    return redis_client


async def get_async_redis() -> aioredis.Redis:
    """Get asynchronous Redis client.

    Returns:
        Async Redis client instance
    """
    global async_redis_client
    if async_redis_client is None:
        async_redis_client = await aioredis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
        )
        logger.info("Async Redis client initialized")
    return async_redis_client


def cache_get(key: str) -> Optional[Any]:
    """Get value from cache.

    Args:
        key: Cache key

    Returns:
        Cached value or None if not found
    """
    try:
        client = get_redis()
        value = client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        logger.error("Cache get error", key=key, error=str(e))
        return None


async def async_cache_get(key: str) -> Optional[Any]:
    """Get value from cache asynchronously.

    Args:
        key: Cache key

    Returns:
        Cached value or None if not found
    """
    try:
        client = await get_async_redis()
        value = await client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        logger.error("Async cache get error", key=key, error=str(e))
        return None


def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Set value in cache.

    Args:
        key: Cache key
        value: Value to cache
        ttl: Time to live in seconds (default: CACHE_TTL)

    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_redis()
        serialized = json.dumps(value, default=str)
        client.setex(key, ttl or CACHE_TTL, serialized)
        return True
    except Exception as e:
        logger.error("Cache set error", key=key, error=str(e))
        return False


async def async_cache_set(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Set value in cache asynchronously.

    Args:
        key: Cache key
        value: Value to cache
        ttl: Time to live in seconds (default: CACHE_TTL)

    Returns:
        True if successful, False otherwise
    """
    try:
        client = await get_async_redis()
        serialized = json.dumps(value, default=str)
        await client.setex(key, ttl or CACHE_TTL, serialized)
        return True
    except Exception as e:
        logger.error("Async cache set error", key=key, error=str(e))
        return False


def cache_delete(key: str) -> bool:
    """Delete value from cache.

    Args:
        key: Cache key

    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_redis()
        client.delete(key)
        return True
    except Exception as e:
        logger.error("Cache delete error", key=key, error=str(e))
        return False


async def async_cache_delete(key: str) -> bool:
    """Delete value from cache asynchronously.

    Args:
        key: Cache key

    Returns:
        True if successful, False otherwise
    """
    try:
        client = await get_async_redis()
        await client.delete(key)
        return True
    except Exception as e:
        logger.error("Async cache delete error", key=key, error=str(e))
        return False


def cache_invalidate_pattern(pattern: str) -> int:
    """Invalidate all cache keys matching pattern.

    Args:
        pattern: Key pattern (e.g., "contract:*")

    Returns:
        Number of keys deleted
    """
    try:
        client = get_redis()
        keys = list(client.scan_iter(match=pattern))
        if keys:
            return client.delete(*keys)
        return 0
    except Exception as e:
        logger.error("Cache invalidate pattern error", pattern=pattern, error=str(e))
        return 0


async def async_cache_invalidate_pattern(pattern: str) -> int:
    """Invalidate all cache keys matching pattern asynchronously.

    Args:
        pattern: Key pattern (e.g., "contract:*")

    Returns:
        Number of keys deleted
    """
    try:
        client = await get_async_redis()
        keys = []
        async for key in client.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            return await client.delete(*keys)
        return 0
    except Exception as e:
        logger.error("Async cache invalidate pattern error", pattern=pattern, error=str(e))
        return 0
