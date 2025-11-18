"""Redis caching for real-time performance."""

import json
from typing import Any, Optional

import redis.asyncio as redis
from loguru import logger

from modules.ab_testing.config import get_settings


class CacheService:
    """
    Redis cache service for A/B testing module.

    Provides caching for:
    - Variant assignments
    - Experiment configurations
    - Real-time statistics
    """

    def __init__(self) -> None:
        """Initialize cache service."""
        settings = get_settings()
        self.redis_url = str(settings.redis_url)
        self.max_connections = settings.redis_max_connections
        self._client: Optional[redis.Redis] = None

    async def connect(self) -> None:
        """
        Connect to Redis.

        Example:
            >>> cache = CacheService()
            >>> await cache.connect()
        """
        if self._client is None:
            self._client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=self.max_connections,
            )
            logger.info("Connected to Redis")

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Disconnected from Redis")

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Any: Cached value or None if not found

        Example:
            >>> value = await cache.get("experiment:1:config")
        """
        if not self._client:
            await self.connect()

        try:
            value = await self._client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = 3600,
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default 1 hour)

        Returns:
            bool: True if successful

        Example:
            >>> await cache.set("experiment:1:config", config_data, ttl=3600)
        """
        if not self._client:
            await self.connect()

        try:
            serialized = json.dumps(value)
            if ttl:
                await self._client.setex(key, ttl, serialized)
            else:
                await self._client.set(key, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            bool: True if successful
        """
        if not self._client:
            await self.connect()

        try:
            await self._client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Key pattern (e.g., "experiment:1:*")

        Returns:
            int: Number of keys deleted

        Example:
            >>> await cache.delete_pattern("experiment:1:*")
        """
        if not self._client:
            await self.connect()

        try:
            keys = []
            async for key in self._client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                await self._client.delete(*keys)
            return len(keys)
        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return 0

    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a counter.

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            int: New value

        Example:
            >>> count = await cache.increment("experiment:1:variant:2:conversions")
        """
        if not self._client:
            await self.connect()

        try:
            return await self._client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return 0

    async def get_assignment(
        self,
        experiment_id: int,
        participant_id: str,
    ) -> Optional[dict]:
        """
        Get cached variant assignment.

        Args:
            experiment_id: Experiment ID
            participant_id: Participant ID

        Returns:
            dict: Assignment data or None
        """
        key = f"assignment:{experiment_id}:{participant_id}"
        return await self.get(key)

    async def set_assignment(
        self,
        experiment_id: int,
        participant_id: str,
        variant_id: int,
        variant_name: str,
        config: Optional[dict] = None,
        ttl: int = 86400,  # 24 hours
    ) -> bool:
        """
        Cache variant assignment.

        Args:
            experiment_id: Experiment ID
            participant_id: Participant ID
            variant_id: Assigned variant ID
            variant_name: Variant name
            config: Variant configuration
            ttl: Time to live in seconds

        Returns:
            bool: True if successful
        """
        key = f"assignment:{experiment_id}:{participant_id}"
        value = {
            "variant_id": variant_id,
            "variant_name": variant_name,
            "config": config,
        }
        return await self.set(key, value, ttl)

    async def track_metric_event(
        self,
        experiment_id: int,
        variant_id: int,
        metric_name: str,
        value: float = 1.0,
    ) -> None:
        """
        Track a metric event in real-time cache.

        Args:
            experiment_id: Experiment ID
            variant_id: Variant ID
            metric_name: Metric name
            value: Metric value
        """
        # Increment conversion counter
        conversion_key = f"metrics:{experiment_id}:{variant_id}:{metric_name}:count"
        await self.increment(conversion_key)

        # Add to running sum for averages
        sum_key = f"metrics:{experiment_id}:{variant_id}:{metric_name}:sum"
        if not self._client:
            await self.connect()

        try:
            await self._client.incrbyfloat(sum_key, value)
        except Exception as e:
            logger.error(f"Error tracking metric event: {e}")

    async def get_real_time_stats(
        self,
        experiment_id: int,
    ) -> dict:
        """
        Get real-time statistics from cache.

        Args:
            experiment_id: Experiment ID

        Returns:
            dict: Real-time statistics

        Example:
            >>> stats = await cache.get_real_time_stats(1)
            >>> print(stats["variant_1"]["conversions"])
        """
        if not self._client:
            await self.connect()

        stats = {}
        pattern = f"metrics:{experiment_id}:*"

        try:
            async for key in self._client.scan_iter(match=pattern):
                parts = key.split(":")
                if len(parts) >= 5:
                    variant_id = parts[2]
                    metric_name = parts[3]
                    stat_type = parts[4]

                    if variant_id not in stats:
                        stats[variant_id] = {}
                    if metric_name not in stats[variant_id]:
                        stats[variant_id][metric_name] = {}

                    value = await self._client.get(key)
                    stats[variant_id][metric_name][stat_type] = (
                        float(value) if value else 0.0
                    )
        except Exception as e:
            logger.error(f"Error getting real-time stats: {e}")

        return stats


# Global cache instance
_cache_service: Optional[CacheService] = None


async def get_cache() -> CacheService:
    """
    Get global cache service instance.

    Returns:
        CacheService: Cache service instance
    """
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
        await _cache_service.connect()
    return _cache_service
