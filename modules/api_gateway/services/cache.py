import hashlib
import json
from typing import Optional

from modules.api_gateway.database import redis_client


class CacheService:
    """Service for caching API responses"""

    @staticmethod
    def generate_cache_key(method: str, path: str, query_params: dict, headers: dict = None) -> str:
        """Generate a unique cache key for a request"""

        # Create key from method, path, and sorted query params
        key_parts = [method, path]

        if query_params:
            sorted_params = sorted(query_params.items())
            key_parts.append(json.dumps(sorted_params))

        # Optionally include specific headers (e.g., Accept, Accept-Language)
        if headers:
            relevant_headers = {
                k: v for k, v in headers.items()
                if k.lower() in ["accept", "accept-language", "accept-encoding"]
            }
            if relevant_headers:
                sorted_headers = sorted(relevant_headers.items())
                key_parts.append(json.dumps(sorted_headers))

        # Generate hash
        key_string = "|".join(key_parts)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()

        return f"response:{key_hash}"

    @staticmethod
    def get_cached_response(cache_key: str) -> Optional[dict]:
        """Get cached response"""

        try:
            cached = redis_client.cache_get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            print(f"Cache get error: {e}")

        return None

    @staticmethod
    def cache_response(cache_key: str, response_data: dict, ttl: int = 300):
        """Cache a response"""

        try:
            response_json = json.dumps(response_data)
            redis_client.cache_set(cache_key, response_json, ttl)
        except Exception as e:
            print(f"Cache set error: {e}")

    @staticmethod
    def invalidate_cache(pattern: str = None):
        """Invalidate cache entries matching pattern"""

        try:
            if pattern:
                # Delete keys matching pattern
                if redis_client.client:
                    keys = redis_client.client.keys(f"cache:{pattern}*")
                    if keys:
                        redis_client.client.delete(*keys)
            else:
                # Clear all cache
                if redis_client.client:
                    keys = redis_client.client.keys("cache:*")
                    if keys:
                        redis_client.client.delete(*keys)
        except Exception as e:
            print(f"Cache invalidation error: {e}")
