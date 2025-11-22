"""Redis client for caching and state management."""

import json
from typing import Any, Optional
import redis.asyncio as redis
from ..config.settings import settings


class RedisClient:
    """Redis client for caching and state management."""

    def __init__(self):
        self.redis: Optional[redis.Redis] = None

    async def connect(self):
        """Connect to Redis."""
        self.redis = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
        )

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis."""
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
        self, key: str, value: Any, expire: Optional[int] = None
    ) -> bool:
        """
        Set value in Redis.

        Args:
            key: Redis key
            value: Value to store
            expire: Expiration time in seconds
        """
        if not self.redis:
            await self.connect()

        if isinstance(value, (dict, list)):
            value = json.dumps(value)

        return await self.redis.set(key, value, ex=expire)

    async def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        if not self.redis:
            await self.connect()

        return bool(await self.redis.delete(key))

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        if not self.redis:
            await self.connect()

        return bool(await self.redis.exists(key))

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment value in Redis."""
        if not self.redis:
            await self.connect()

        return await self.redis.incrby(key, amount)

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for a key."""
        if not self.redis:
            await self.connect()

        return await self.redis.expire(key, seconds)

    async def get_workflow_state(self, workflow_id: int) -> Optional[dict]:
        """Get workflow execution state."""
        key = f"workflow:{workflow_id}:state"
        return await self.get(key)

    async def set_workflow_state(
        self, workflow_id: int, state: dict, expire: int = 3600
    ) -> bool:
        """Set workflow execution state."""
        key = f"workflow:{workflow_id}:state"
        return await self.set(key, state, expire)

    async def get_task_result(self, task_execution_id: int) -> Optional[dict]:
        """Get task execution result from cache."""
        key = f"task:{task_execution_id}:result"
        return await self.get(key)

    async def set_task_result(
        self, task_execution_id: int, result: dict, expire: int = 3600
    ) -> bool:
        """Cache task execution result."""
        key = f"task:{task_execution_id}:result"
        return await self.set(key, result, expire)

    async def acquire_lock(
        self, resource: str, timeout: int = 10
    ) -> Optional[str]:
        """
        Acquire distributed lock.

        Args:
            resource: Resource name
            timeout: Lock timeout in seconds

        Returns:
            Lock identifier if acquired, None otherwise
        """
        if not self.redis:
            await self.connect()

        import uuid
        lock_id = str(uuid.uuid4())
        key = f"lock:{resource}"

        # Try to acquire lock
        acquired = await self.redis.set(key, lock_id, nx=True, ex=timeout)

        return lock_id if acquired else None

    async def release_lock(self, resource: str, lock_id: str) -> bool:
        """
        Release distributed lock.

        Args:
            resource: Resource name
            lock_id: Lock identifier

        Returns:
            True if released, False otherwise
        """
        if not self.redis:
            await self.connect()

        key = f"lock:{resource}"

        # Lua script for atomic release
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """

        result = await self.redis.eval(lua_script, 1, key, lock_id)
        return bool(result)


# Global Redis client instance
redis_client = RedisClient()
