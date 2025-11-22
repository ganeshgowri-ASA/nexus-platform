"""
Redis caching service for Testing module
"""
import redis
import json
import os
from typing import Any, Optional
from datetime import timedelta


class RedisCache:
    """Redis cache manager"""

    def __init__(
        self,
        host: str = None,
        port: int = None,
        db: int = 0,
        password: str = None
    ):
        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = port or int(os.getenv("REDIS_PORT", "6379"))
        self.db = db
        self.password = password or os.getenv("REDIS_PASSWORD")

        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            decode_responses=True
        )

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        expire: int = None
    ) -> bool:
        """Set value in cache"""
        try:
            serialized = json.dumps(value)
            if expire:
                return self.client.setex(key, expire, serialized)
            else:
                return self.client.set(key, serialized)
        except Exception as e:
            print(f"Redis set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False

    def cache_test_results(
        self,
        test_run_id: int,
        results: dict,
        expire: int = 3600
    ) -> bool:
        """Cache test run results"""
        key = f"test_run:{test_run_id}:results"
        return self.set(key, results, expire)

    def get_cached_test_results(self, test_run_id: int) -> Optional[dict]:
        """Get cached test run results"""
        key = f"test_run:{test_run_id}:results"
        return self.get(key)

    def cache_test_analytics(
        self,
        analytics: dict,
        expire: int = 300
    ) -> bool:
        """Cache test analytics"""
        key = "test_analytics"
        return self.set(key, analytics, expire)

    def get_cached_analytics(self) -> Optional[dict]:
        """Get cached test analytics"""
        key = "test_analytics"
        return self.get(key)

    def clear_cache(self, pattern: str = "*") -> int:
        """Clear cache by pattern"""
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Redis clear cache error: {e}")
            return 0


# Global cache instance
cache = RedisCache()
