"""
Translation Cache

Redis-based caching for translations.
"""

from typing import Optional, Dict, Any
import hashlib
import json
from config.settings import settings
from config.logging import get_logger
from nexus.core.exceptions import CacheError

logger = get_logger(__name__)


class TranslationCache:
    """
    Redis-based translation cache.

    Features:
    - Fast lookups
    - TTL support
    - Cache statistics
    - Multiple cache strategies
    """

    def __init__(self, ttl: Optional[int] = None):
        """
        Initialize translation cache.

        Args:
            ttl: Time-to-live in seconds (default from settings)
        """
        self.ttl = ttl or settings.TRANSLATION_CACHE_TTL
        self.redis_client = None
        self.enabled = True

        self._initialize_redis()

    def _initialize_redis(self) -> None:
        """Initialize Redis connection."""
        try:
            import redis
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            self.enabled = False

    def _generate_key(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> str:
        """
        Generate cache key.

        Args:
            text: Source text
            source_lang: Source language
            target_lang: Target language

        Returns:
            Cache key
        """
        # Create hash of text for consistent key
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        return f"translation:{source_lang}:{target_lang}:{text_hash}"

    def get(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get translation from cache.

        Args:
            text: Source text
            source_lang: Source language
            target_lang: Target language

        Returns:
            Cached translation or None
        """
        if not self.enabled or not self.redis_client:
            return None

        try:
            key = self._generate_key(text, source_lang, target_lang)
            cached_data = self.redis_client.get(key)

            if cached_data:
                logger.debug(f"Cache hit for key: {key}")
                return json.loads(cached_data)
            else:
                logger.debug(f"Cache miss for key: {key}")
                return None

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        translation: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Set translation in cache.

        Args:
            text: Source text
            source_lang: Source language
            target_lang: Target language
            translation: Translated text
            metadata: Additional metadata

        Returns:
            True if successful
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            key = self._generate_key(text, source_lang, target_lang)

            cache_data = {
                "translation": translation,
                "source_language": source_lang,
                "target_language": target_lang,
                "metadata": metadata or {},
            }

            self.redis_client.setex(
                key,
                self.ttl,
                json.dumps(cache_data),
            )

            logger.debug(f"Cached translation for key: {key}")
            return True

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def delete(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> bool:
        """
        Delete translation from cache.

        Args:
            text: Source text
            source_lang: Source language
            target_lang: Target language

        Returns:
            True if successful
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            key = self._generate_key(text, source_lang, target_lang)
            self.redis_client.delete(key)
            logger.debug(f"Deleted cache key: {key}")
            return True

        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def clear_all(self) -> bool:
        """
        Clear all translation cache.

        Returns:
            True if successful
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            # Delete all keys matching translation pattern
            pattern = "translation:*"
            keys = self.redis_client.keys(pattern)

            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries")

            return True

        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Cache statistics
        """
        if not self.enabled or not self.redis_client:
            return {"enabled": False}

        try:
            info = self.redis_client.info()
            pattern = "translation:*"
            keys = self.redis_client.keys(pattern)

            return {
                "enabled": True,
                "total_entries": len(keys),
                "memory_used": info.get("used_memory_human"),
                "hit_rate": info.get("keyspace_hits", 0)
                / max(
                    info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0),
                    1,
                ),
            }

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"enabled": True, "error": str(e)}


class CacheStrategy:
    """Cache invalidation and management strategies."""

    @staticmethod
    def should_cache(
        text: str,
        quality_score: Optional[float] = None,
        min_length: int = 10,
        min_quality: float = 0.7,
    ) -> bool:
        """
        Determine if translation should be cached.

        Args:
            text: Source text
            quality_score: Quality score of translation
            min_length: Minimum text length to cache
            min_quality: Minimum quality score to cache

        Returns:
            True if should be cached
        """
        # Don't cache very short texts
        if len(text) < min_length:
            return False

        # Don't cache low-quality translations
        if quality_score is not None and quality_score < min_quality:
            return False

        return True

    @staticmethod
    def calculate_ttl(
        text_length: int,
        quality_score: Optional[float] = None,
        base_ttl: int = 86400,
    ) -> int:
        """
        Calculate dynamic TTL based on translation characteristics.

        Args:
            text_length: Length of text
            quality_score: Quality score
            base_ttl: Base TTL in seconds

        Returns:
            TTL in seconds
        """
        ttl = base_ttl

        # Longer texts get longer TTL
        if text_length > 1000:
            ttl *= 2
        elif text_length > 500:
            ttl *= 1.5

        # Higher quality gets longer TTL
        if quality_score and quality_score > 0.9:
            ttl *= 1.5

        return int(ttl)


class CacheManager:
    """Advanced cache management functionality."""

    def __init__(self, cache: TranslationCache):
        """
        Initialize cache manager.

        Args:
            cache: Translation cache instance
        """
        self.cache = cache

    def warm_cache(self, translations: list) -> int:
        """
        Pre-populate cache with common translations.

        Args:
            translations: List of (text, source_lang, target_lang, translation) tuples

        Returns:
            Number of translations cached
        """
        count = 0

        for item in translations:
            text, source_lang, target_lang, translation = item
            if self.cache.set(text, source_lang, target_lang, translation):
                count += 1

        logger.info(f"Warmed cache with {count} translations")
        return count

    def cleanup_expired(self) -> int:
        """
        Clean up expired cache entries.

        Returns:
            Number of entries cleaned
        """
        # Redis handles TTL automatically, but this can be used for manual cleanup
        logger.info("Cache cleanup triggered (Redis handles TTL automatically)")
        return 0
