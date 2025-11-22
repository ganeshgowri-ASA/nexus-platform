"""Redis client utilities."""
import redis
from functools import lru_cache
from shared.config import get_settings

settings = get_settings()


@lru_cache()
def get_redis_client() -> redis.Redis:
    """Get Redis client instance."""
    return redis.from_url(settings.REDIS_URL, decode_responses=True)
