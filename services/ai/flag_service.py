"""AI flag management service backed by Postgres with Redis caching."""

from typing import Optional

from redis.asyncio import Redis as AsyncRedis
from redis.exceptions import RedisError

from config.log_setup import get_logger
from services.cache.redis_client import BaseRedisClient
from services.database.feature_flag_service import FeatureFlagService

logger = get_logger(__name__)


class AIFlagService(BaseRedisClient):
    """Feature flag manager with Redis cache and Postgres persistence."""

    FLAG_KEY = "ai_mode"
    CACHE_KEY = "ai:mode_enabled"
    CACHE_TTL_SECONDS = 300

    async def is_ai_mode_enabled(self) -> bool:
        """Check if AI mode is currently enabled."""
        redis_client = await self._get_redis_safe()

        if redis_client:
            try:
                cached_value = await redis_client.get(self.CACHE_KEY)
                if cached_value is not None:
                    return cached_value == "true"
            except RedisError as e:
                logger.warning("Redis error when reading AI mode cache: %s", e)

        # Fall back to Postgres and populate the cache
        try:
            flag_value = await FeatureFlagService.get_flag_value(self.FLAG_KEY)
        except Exception as e:  # pragma: no cover - defensive logging
            logger.error("Failed to read AI mode flag from Postgres: %s", e)
            return False

        if redis_client:
            await self._write_cache(redis_client, flag_value)

        return flag_value

    async def set_ai_mode(self, enabled: bool) -> bool:
        """Persist AI mode flag and refresh Redis cache."""
        try:
            new_value = await FeatureFlagService.set_flag_value(self.FLAG_KEY, enabled)
        except Exception as e:  # pragma: no cover - defensive logging
            logger.error("Failed to persist AI mode flag in Postgres: %s", e)
            return False

        redis_client = await self._get_redis_safe()
        if redis_client:
            await self._write_cache(redis_client, new_value)

        return new_value == enabled

    async def _get_redis_safe(self) -> Optional[AsyncRedis]:
        """Try to get a Redis connection without raising."""
        try:
            return await self._get_redis()
        except RedisError as e:
            logger.warning("Redis unavailable for AI flag cache: %s", e)
            return None
        except Exception as e:  # pragma: no cover - defensive
            logger.warning("Unexpected error acquiring Redis for AI flag cache: %s", e)
            return None

    async def _write_cache(self, redis_client, value: bool) -> None:
        """Write the cached value, swallowing Redis errors."""
        try:
            await redis_client.set(
                self.CACHE_KEY,
                "true" if value else "false",
                ex=self.CACHE_TTL_SECONDS,
            )
        except RedisError as e:
            logger.warning("Failed to update AI mode cache in Redis: %s", e)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Keep Redis connections open for reuse within the process.
        return False