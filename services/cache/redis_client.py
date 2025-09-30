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
                        cls._redis = AsyncRedis(
                            host=config.redis_host,
                            port=config.redis_port,
                            db=config.redis_db,
                            username=config.redis_username,
                            password=config.redis_password,
                            decode_responses=True,
                            socket_timeout=10,
                            socket_connect_timeout=10,
                            health_check_interval=30,
                        )
                        await cls._redis.ping()
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