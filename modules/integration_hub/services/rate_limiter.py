"""Rate limiting service using Redis."""
from typing import Optional
import time
from shared.utils.redis_client import get_redis_client
from shared.utils.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Rate limiter using Redis."""

    def __init__(self):
        self.redis = get_redis_client()
        self.logger = logger

    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
        identifier: Optional[str] = None,
    ) -> tuple[bool, dict]:
        """
        Check if rate limit is exceeded.

        Args:
            key: Base rate limit key (e.g., 'api_key:123')
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
            identifier: Optional additional identifier

        Returns:
            Tuple of (allowed, info_dict)
        """
        try:
            # Construct full key
            full_key = f"rate_limit:{key}"
            if identifier:
                full_key = f"{full_key}:{identifier}"

            # Current timestamp
            now = time.time()
            window_start = now - window_seconds

            # Remove old entries
            self.redis.zremrangebyscore(full_key, 0, window_start)

            # Count requests in current window
            current_requests = self.redis.zcard(full_key)

            # Check if limit exceeded
            if current_requests >= max_requests:
                # Get oldest request timestamp to calculate retry_after
                oldest = self.redis.zrange(full_key, 0, 0, withscores=True)
                if oldest:
                    retry_after = int(oldest[0][1] + window_seconds - now)
                else:
                    retry_after = window_seconds

                return False, {
                    "allowed": False,
                    "limit": max_requests,
                    "remaining": 0,
                    "reset_at": int(now + retry_after),
                    "retry_after": retry_after,
                }

            # Add current request
            self.redis.zadd(full_key, {str(now): now})
            self.redis.expire(full_key, window_seconds)

            remaining = max_requests - current_requests - 1

            return True, {
                "allowed": True,
                "limit": max_requests,
                "remaining": remaining,
                "reset_at": int(now + window_seconds),
            }

        except Exception as e:
            self.logger.error(f"Error checking rate limit: {e}")
            # On error, allow the request (fail open)
            return True, {"allowed": True, "error": str(e)}

    def reset_rate_limit(self, key: str, identifier: Optional[str] = None) -> bool:
        """Reset rate limit for a key."""
        try:
            full_key = f"rate_limit:{key}"
            if identifier:
                full_key = f"{full_key}:{identifier}"

            self.redis.delete(full_key)
            return True

        except Exception as e:
            self.logger.error(f"Error resetting rate limit: {e}")
            return False

    def get_rate_limit_info(self, key: str, identifier: Optional[str] = None) -> dict:
        """Get current rate limit status."""
        try:
            full_key = f"rate_limit:{key}"
            if identifier:
                full_key = f"{full_key}:{identifier}"

            count = self.redis.zcard(full_key)
            ttl = self.redis.ttl(full_key)

            return {"current_requests": count, "ttl_seconds": ttl}

        except Exception as e:
            self.logger.error(f"Error getting rate limit info: {e}")
            return {"error": str(e)}
