"""Redis cache service implementation."""

import json
import logging
from typing import Any, Optional
from redis.asyncio import Redis
from redis.exceptions import RedisError

from .base import CacheService
from config.settings import get_config

logger = logging.getLogger(__name__)


class RedisCacheService(CacheService):
    """Redis-based cache service implementation."""

    def __init__(self, uri: Optional[str] = None):
        self.uri = uri or get_config().redis_uri
        self._client: Optional[Redis] = None

    async def _get_client(self) -> Redis:
        """Get or create Redis client."""
        if self._client is None:
            if not self.uri:
                raise ValueError("Redis URI not configured")
            self._client = Redis.from_url(self.uri, decode_responses=True)
        return self._client

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache by key."""
        try:
            client = await self._get_client()
            value = await client.get(key)
            if value is not None:
                return json.loads(value)
            return None
        except RedisError as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL in seconds."""
        try:
            client = await self._get_client()
            json_value = json.dumps(value)
            if ttl is not None:
                await client.setex(key, ttl, json_value)
            else:
                await client.set(key, json_value)
            return True
        except RedisError as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False
        except (TypeError, ValueError) as e:
            logger.error(f"JSON encode error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache by key."""
        try:
            client = await self._get_client()
            result = await client.delete(key)
            return result > 0
        except RedisError as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            client = await self._get_client()
            result = await client.exists(key)
            return result > 0
        except RedisError as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for key in seconds."""
        try:
            client = await self._get_client()
            result = await client.expire(key, ttl)
            return result
        except RedisError as e:
            logger.error(f"Redis expire error for key {key}: {e}")
            return False

    async def close(self) -> None:
        """Close cache connection."""
        if self._client:
            await self._client.close()
            self._client = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()