"""AI flag management service using Redis."""

from typing import Optional

from redis import RedisError
from redis.asyncio import Redis as AsyncRedis

from config.log_setup import get_logger
from config.settings import get_config

logger = get_logger(__name__)


class AIFlagService:
    """Redis-based AI mode flag management service."""
    
    AI_MODE_KEY = "ai:mode_enabled"
    
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
                logger.error("Failed to connect to Redis: %s", e)
                raise
        return self._redis

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

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()