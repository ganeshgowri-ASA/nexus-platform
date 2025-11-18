"""
AI Response Caching System

Implements LRU (Least Recently Used) caching with TTL expiration to reduce
API costs by up to 80% for repeated queries.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from collections import OrderedDict
import hashlib
import json


class CacheManager:
    """
    LRU cache with TTL for AI responses.

    Features:
    - LRU eviction policy
    - TTL-based expiration
    - Configurable max size
    - Cache hit/miss statistics
    - Automatic cleanup of expired entries
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 3600  # 1 hour in seconds
    ):
        """
        Initialize cache manager.

        Args:
            max_size: Maximum number of cached items
            default_ttl: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()

        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def _generate_key(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate a unique cache key for a request.

        Args:
            model: AI model name
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Model temperature
            max_tokens: Maximum tokens
            **kwargs: Additional parameters

        Returns:
            Unique cache key (SHA-256 hash)
        """
        # Create a canonical representation of the request
        cache_input = {
            "model": model,
            "prompt": prompt,
            "system_prompt": system_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }

        # Sort dict for consistent hashing
        canonical = json.dumps(cache_input, sort_keys=True)

        # Generate hash
        return hashlib.sha256(canonical.encode()).hexdigest()

    def get(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached response if available and not expired.

        Args:
            model: AI model name
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Model temperature
            max_tokens: Maximum tokens
            **kwargs: Additional parameters

        Returns:
            Cached response or None if not found/expired
        """
        key = self._generate_key(
            model, prompt, system_prompt, temperature, max_tokens, **kwargs
        )

        if key not in self.cache:
            self.misses += 1
            return None

        entry = self.cache[key]

        # Check if expired
        if datetime.utcnow() > entry["expires_at"]:
            del self.cache[key]
            self.misses += 1
            return None

        # Move to end (most recently used)
        self.cache.move_to_end(key)
        self.hits += 1

        return entry["response"]

    def set(
        self,
        model: str,
        prompt: str,
        response: Dict[str, Any],
        system_prompt: Optional[str] = None,
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        ttl: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Store response in cache.

        Args:
            model: AI model name
            prompt: User prompt
            response: AI response to cache
            system_prompt: System prompt (optional)
            temperature: Model temperature
            max_tokens: Maximum tokens
            ttl: Time-to-live in seconds (uses default if None)
            **kwargs: Additional parameters

        Returns:
            Cache key
        """
        key = self._generate_key(
            model, prompt, system_prompt, temperature, max_tokens, **kwargs
        )

        # Set expiration time
        ttl = ttl or self.default_ttl
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)

        # Store entry
        entry = {
            "response": response,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "model": model,
        }

        self.cache[key] = entry

        # Move to end (most recently used)
        if key in self.cache:
            self.cache.move_to_end(key)

        # Evict oldest if over max size
        if len(self.cache) > self.max_size:
            self._evict_oldest()

        return key

    def _evict_oldest(self):
        """Evict the least recently used item."""
        if self.cache:
            self.cache.popitem(last=False)
            self.evictions += 1

    def invalidate(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> bool:
        """
        Invalidate a cached entry.

        Args:
            model: AI model name
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Model temperature
            max_tokens: Maximum tokens
            **kwargs: Additional parameters

        Returns:
            True if entry was found and removed, False otherwise
        """
        key = self._generate_key(
            model, prompt, system_prompt, temperature, max_tokens, **kwargs
        )

        if key in self.cache:
            del self.cache[key]
            return True

        return False

    def clear(self):
        """Clear all cached entries."""
        self.cache.clear()

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.

        Returns:
            Number of entries removed
        """
        now = datetime.utcnow()
        expired_keys = [
            key for key, entry in self.cache.items()
            if now > entry["expires_at"]
        ]

        for key in expired_keys:
            del self.cache[key]

        return len(expired_keys)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "evictions": self.evictions,
            "total_requests": total_requests,
        }

    def get_size_info(self) -> Dict[str, int]:
        """
        Get cache size information.

        Returns:
            Dictionary with size metrics
        """
        now = datetime.utcnow()

        active_entries = sum(
            1 for entry in self.cache.values()
            if now <= entry["expires_at"]
        )
        expired_entries = len(self.cache) - active_entries

        return {
            "total": len(self.cache),
            "active": active_entries,
            "expired": expired_entries,
            "capacity_used_percent": (len(self.cache) / self.max_size * 100),
        }

    def get_entries_by_model(self) -> Dict[str, int]:
        """
        Get count of cached entries per model.

        Returns:
            Dictionary mapping model names to entry counts
        """
        from collections import defaultdict
        model_counts = defaultdict(int)

        for entry in self.cache.values():
            model_counts[entry["model"]] += 1

        return dict(model_counts)

    def estimate_savings(self, cost_per_request: float = 0.01) -> float:
        """
        Estimate cost savings from cache hits.

        Args:
            cost_per_request: Average cost per API request

        Returns:
            Estimated savings in USD
        """
        return self.hits * cost_per_request

    def should_cache(
        self,
        model: str,
        task_type: str,
        temperature: float
    ) -> bool:
        """
        Determine if a request should be cached based on parameters.

        High temperature (>0.8) indicates creative/random output, which
        shouldn't be cached. Certain task types benefit more from caching.

        Args:
            model: AI model name
            task_type: Type of task
            temperature: Model temperature

        Returns:
            True if request should be cached
        """
        # Don't cache high-temperature requests (too random)
        if temperature > 0.8:
            return False

        # Task types that benefit from caching
        cacheable_tasks = {
            "translation",
            "grammar_check",
            "formula_generation",
            "code_explanation",
            "summarization",
            "data_analysis",
        }

        if task_type in cacheable_tasks:
            return True

        # Default: cache medium-low temperature requests
        return temperature <= 0.5

    def get_ttl_for_task(self, task_type: str) -> int:
        """
        Get recommended TTL based on task type.

        Args:
            task_type: Type of task

        Returns:
            TTL in seconds
        """
        ttl_map = {
            # Long TTL for static tasks
            "translation": 86400,  # 24 hours
            "grammar_check": 43200,  # 12 hours
            "code_explanation": 21600,  # 6 hours

            # Medium TTL for semi-static tasks
            "formula_generation": 7200,  # 2 hours
            "data_analysis": 3600,  # 1 hour

            # Short TTL for dynamic tasks
            "chat": 1800,  # 30 minutes
            "writing": 1800,  # 30 minutes
        }

        return ttl_map.get(task_type, self.default_ttl)


# Global cache manager instance
cache_manager = CacheManager()
