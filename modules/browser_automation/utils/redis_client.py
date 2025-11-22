"""Redis client for caching and session management"""
import json
from typing import Any, Optional
import redis.asyncio as redis
from modules.browser_automation.config import settings


class RedisClient:
    """Redis client wrapper"""

    def __init__(self):
        self.redis: Optional[redis.Redis] = None

    async def connect(self):
        """Connect to Redis"""
        self.redis = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        if not self.redis:
            await self.connect()

        value = await self.redis.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """Set value in Redis"""
        if not self.redis:
            await self.connect()

        if isinstance(value, (dict, list)):
            value = json.dumps(value)

        if expire:
            return await self.redis.setex(key, expire, value)
        else:
            return await self.redis.set(key, value)

    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        if not self.redis:
            await self.connect()

        return await self.redis.delete(key) > 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        if not self.redis:
            await self.connect()

        return await self.redis.exists(key) > 0

    async def cache_workflow_result(
        self,
        workflow_id: int,
        result: dict,
        expire: int = 3600
    ):
        """Cache workflow execution result"""
        key = f"workflow_result:{workflow_id}"
        await self.set(key, result, expire)

    async def get_cached_workflow_result(
        self,
        workflow_id: int
    ) -> Optional[dict]:
        """Get cached workflow result"""
        key = f"workflow_result:{workflow_id}"
        return await self.get(key)

    async def increment_counter(self, key: str) -> int:
        """Increment counter"""
        if not self.redis:
            await self.connect()

        return await self.redis.incr(key)

    async def rate_limit_check(
        self,
        identifier: str,
        max_requests: int = 60,
        window: int = 60
    ) -> bool:
        """Check rate limiting"""
        if not self.redis:
            await self.connect()

        key = f"rate_limit:{identifier}"
        current = await self.redis.get(key)

        if current is None:
            await self.redis.setex(key, window, 1)
            return True

        if int(current) >= max_requests:
            return False

        await self.redis.incr(key)
        return True


# Global Redis client instance
redis_client = RedisClient()
