"""AI flag management service using Redis."""

from redis.exceptions import RedisError

from config.log_setup import get_logger
from services.cache.redis_client import BaseRedisClient

logger = get_logger(__name__)


class AIFlagService(BaseRedisClient):
    """Redis-based AI mode flag management service."""
    
    AI_MODE_KEY = "ai:mode_enabled"

    async def is_ai_mode_enabled(self) -> bool:
        """Check if AI mode is currently enabled."""
        try:
            redis_client = await self._get_redis()
            result = await redis_client.get(self.AI_MODE_KEY)
            return result == "true"
        except RedisError as e:
            logger.error("Redis error when checking AI mode flag: %s", e)
            return False
        except Exception as e:
            logger.error("Unexpected error when checking AI mode flag: %s", e)
            return False

    async def set_ai_mode(self, enabled: bool) -> bool:
        """Set AI mode flag (no TTL - persistent until changed)."""
        try:
            redis_client = await self._get_redis()
            value = "true" if enabled else "false"
            result = await redis_client.set(self.AI_MODE_KEY, value)
            
            if result:
                logger.info("AI mode flag set to: %s", enabled)
            else:
                logger.warning("Failed to set AI mode flag")
            
            return bool(result)
        except RedisError as e:
            logger.error("Redis error when setting AI mode flag: %s", e)
            return False
        except Exception as e:
            logger.error("Unexpected error when setting AI mode flag: %s", e)
            return False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()