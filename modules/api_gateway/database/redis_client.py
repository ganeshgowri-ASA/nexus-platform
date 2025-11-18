import redis
import os
from typing import Optional
import json


class RedisClient:
    """Redis client for caching and rate limiting"""

    def __init__(self):
        self.host = os.getenv("NEXUS_REDIS_HOST", "localhost")
        self.port = int(os.getenv("NEXUS_REDIS_PORT", "6379"))
        self.db = int(os.getenv("NEXUS_REDIS_DB", "0"))
        self.password = os.getenv("NEXUS_REDIS_PASSWORD", None)

        self._client: Optional[redis.Redis] = None

    def connect(self):
        """Connect to Redis"""
        try:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
            )
            # Test connection
            self._client.ping()
            print(f"Connected to Redis at {self.host}:{self.port}")
        except Exception as e:
            print(f"Failed to connect to Redis: {e}")
            self._client = None

    @property
    def client(self) -> Optional[redis.Redis]:
        """Get Redis client, connecting if necessary"""
        if self._client is None:
            self.connect()
        return self._client

    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        try:
            if self._client:
                self._client.ping()
                return True
        except:
            pass
        return False

    # Cache operations
    def cache_get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        try:
            if self.client:
                return self.client.get(f"cache:{key}")
        except Exception as e:
            print(f"Cache get error: {e}")
        return None

    def cache_set(self, key: str, value: str, ttl: int = 300):
        """Set value in cache with TTL"""
        try:
            if self.client:
                self.client.setex(f"cache:{key}", ttl, value)
        except Exception as e:
            print(f"Cache set error: {e}")

    def cache_delete(self, key: str):
        """Delete value from cache"""
        try:
            if self.client:
                self.client.delete(f"cache:{key}")
        except Exception as e:
            print(f"Cache delete error: {e}")

    # Rate limiting operations
    def rate_limit_check(self, identifier: str, limit: int, window: int) -> tuple[bool, int]:
        """
        Check if request is within rate limit.

        Returns:
            (is_allowed, remaining_requests)
        """
        try:
            if not self.client:
                return True, limit  # Allow if Redis unavailable

            key = f"ratelimit:{identifier}"

            # Increment counter
            current = self.client.incr(key)

            # Set expiry on first request
            if current == 1:
                self.client.expire(key, window)

            # Check if over limit
            if current > limit:
                return False, 0

            return True, limit - current

        except Exception as e:
            print(f"Rate limit check error: {e}")
            return True, limit  # Allow if error

    def rate_limit_reset(self, identifier: str):
        """Reset rate limit for identifier"""
        try:
            if self.client:
                self.client.delete(f"ratelimit:{identifier}")
        except Exception as e:
            print(f"Rate limit reset error: {e}")

    # Metrics operations
    def increment_metric(self, metric_name: str, value: int = 1):
        """Increment a metric counter"""
        try:
            if self.client:
                self.client.incrby(f"metric:{metric_name}", value)
        except Exception as e:
            print(f"Metric increment error: {e}")

    def get_metric(self, metric_name: str) -> int:
        """Get metric value"""
        try:
            if self.client:
                val = self.client.get(f"metric:{metric_name}")
                return int(val) if val else 0
        except Exception as e:
            print(f"Metric get error: {e}")
        return 0


# Global Redis client instance
redis_client = RedisClient()


def get_redis() -> RedisClient:
    """Dependency function to get Redis client"""
    return redis_client
