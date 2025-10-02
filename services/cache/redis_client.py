"""Shared Redis client base class."""

from typing import Optional

import asyncio
from redis.asyncio import Redis as AsyncRedis
from redis.exceptions import RedisError

from config.log_setup import get_logger
from config.settings import get_config

logger = get_logger(__name__)


class BaseRedisClient:
    """Base Redis client that can be shared across services."""

    _redis: Optional[AsyncRedis] = None
    _redis_lock: Optional[asyncio.Lock] = None

    def __init__(self):
        """Cache configuration reference."""
        self.config = get_config()

    @classmethod
    async def _get_redis(cls) -> AsyncRedis:
        """Get or create a shared Redis connection."""
        if cls._redis is None:
            if cls._redis_lock is None:
                cls._redis_lock = asyncio.Lock()
            async with cls._redis_lock:
                if cls._redis is None:
                    try:
                        config = get_config()
                        redis_options = config.redis_connection_kwargs

                        if redis_options["url"]:
                            redis_client = AsyncRedis.from_url(
                                redis_options["url"],
                                **redis_options["kwargs"],
                            )
                        else:
                            redis_client = AsyncRedis(
                                **redis_options["kwargs"],
                            )
                        await redis_client.ping()
                        cls._redis = redis_client
                        logger.info("Redis connection established successfully")
                    except RedisError as e:
                        logger.error("Failed to connect to Redis: %s", e)
                        raise
        return cls._redis

    @classmethod
    async def close_connection(cls):
        """Close the shared Redis connection."""
        if cls._redis:
            await cls._redis.close()
            cls._redis = None

    async def close(self):
        """Close Redis connection (alias for compatibility)."""
        await self.close_connection()
