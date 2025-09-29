"""Shared Redis client base class."""

from typing import Optional

from redis.asyncio import Redis as AsyncRedis
from redis.exceptions import RedisError

from config.log_setup import get_logger
from config.settings import get_config

logger = get_logger(__name__)


class BaseRedisClient:
    """Base Redis client that can be shared across services."""

    def __init__(self):
        """Initialize Redis connection."""
        self.config = get_config()
        self._redis: Optional[AsyncRedis] = None

    async def _get_redis(self) -> AsyncRedis:
        """Get or create Redis connection."""
        if self._redis is None:
            try:
                self._redis = AsyncRedis(
                    host=self.config.redis_host,
                    port=self.config.redis_port,
                    db=self.config.redis_db,
                    username=self.config.redis_username,
                    password=self.config.redis_password,
                    decode_responses=True,
                    socket_timeout=10,
                    socket_connect_timeout=10,
                    health_check_interval=30
                )
                # Test connection
                await self._redis.ping()
                logger.info("Redis connection established successfully")
            except RedisError as e:
                logger.error("Failed to connect to Redis: %s", e)
                raise
        return self._redis

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()