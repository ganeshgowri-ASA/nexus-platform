"""
Caching manager for Nexus Platform
"""
import json
import hashlib
from typing import Any, Optional, Callable
from functools import wraps
import time
from loguru import logger


class CacheManager:
    """Simple in-memory cache with TTL support"""

    def __init__(self, default_ttl: int = 3600):
        self._cache: dict = {}
        self.default_ttl = default_ttl

    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = {
            "args": args,
            "kwargs": kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self._cache:
            value, expiry = self._cache[key]
            if expiry is None or time.time() < expiry:
                logger.debug(f"Cache hit for key: {key}")
                return value
            else:
                logger.debug(f"Cache expired for key: {key}")
                del self._cache[key]
        logger.debug(f"Cache miss for key: {key}")
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache with TTL"""
        expiry = None
        if ttl or self.default_ttl:
            expiry = time.time() + (ttl or self.default_ttl)
        self._cache[key] = (value, expiry)
        logger.debug(f"Cache set for key: {key}")

    def delete(self, key: str):
        """Delete key from cache"""
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache deleted for key: {key}")

    def clear(self):
        """Clear all cache"""
        self._cache.clear()
        logger.info("Cache cleared")

    def cached(self, ttl: Optional[int] = None):
        """Decorator to cache function results"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                key = f"{func.__name__}:{self._generate_key(*args, **kwargs)}"
                result = self.get(key)
                if result is not None:
                    return result
                result = func(*args, **kwargs)
                self.set(key, result, ttl)
                return result
            return wrapper
        return decorator

    def async_cached(self, ttl: Optional[int] = None):
        """Decorator to cache async function results"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                key = f"{func.__name__}:{self._generate_key(*args, **kwargs)}"
                result = self.get(key)
                if result is not None:
                    return result
                result = await func(*args, **kwargs)
                self.set(key, result, ttl)
                return result
            return wrapper
        return decorator
