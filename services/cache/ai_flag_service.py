"""AI chat bot flag service using Redis."""

from typing import Optional

from redis.asyncio import Redis as AsyncRedis
from redis.exceptions import RedisError

from config.log_setup import get_logger
from config.settings import get_config

logger = get_logger(__name__)


class AIChatBotFlagService:
    """Service for managing AI chat bot mode flag in Redis."""
    
    FLAG_KEY = "ai_chatbot_mode"

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
                logger.info("Redis connection established successfully for AI flag service")
            except RedisError as e:
                logger.error("Failed to connect to Redis for AI flag service: %s", e)
                raise
        return self._redis

    async def is_enabled(self) -> bool:
        """Check if AI chat bot mode is enabled."""
        try:
            redis_client = await self._get_redis()
            value = await redis_client.get(self.FLAG_KEY)
            result = value == "true" if value else False
            logger.debug("AI chat bot mode status: %s", result)
            return result
        except RedisError as e:
            logger.error("Redis error when checking AI chat bot flag: %s", e)
            return False
        except Exception as e:
            logger.error("Unexpected error when checking AI chat bot flag: %s", e)
            return False

    async def enable(self) -> bool:
        """Enable AI chat bot mode."""
        try:
            redis_client = await self._get_redis()
            result = await redis_client.set(self.FLAG_KEY, "true")
            if result:
                logger.info("AI chat bot mode enabled")
            else:
                logger.warning("Failed to enable AI chat bot mode")
            return bool(result)
        except RedisError as e:
            logger.error("Redis error when enabling AI chat bot mode: %s", e)
            return False
        except Exception as e:
            logger.error("Unexpected error when enabling AI chat bot mode: %s", e)
            return False

    async def disable(self) -> bool:
        """Disable AI chat bot mode."""
        try:
            redis_client = await self._get_redis()
            result = await redis_client.set(self.FLAG_KEY, "false")
            if result:
                logger.info("AI chat bot mode disabled")
            else:
                logger.warning("Failed to disable AI chat bot mode")
            return bool(result)
        except RedisError as e:
            logger.error("Redis error when disabling AI chat bot mode: %s", e)
            return False
        except Exception as e:
            logger.error("Unexpected error when disabling AI chat bot mode: %s", e)
            return False

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None