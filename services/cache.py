"""Cache service with proper separation of concerns using Redis JSON."""

import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Type, TypeVar, Generic
import redis
from pydantic import BaseModel

from config.settings import get_config

# Type variable for generic BaseModel support
T = TypeVar('T', bound=BaseModel)


class CacheSerializer(Generic[T]):
    """Helper class for serializing/deserializing any Pydantic BaseModel to/from JSON."""

    @staticmethod
    def serialize_model(model: BaseModel) -> str:
        """Convert any Pydantic BaseModel to JSON string."""
        return model.model_dump_json()

    @staticmethod
    def deserialize_model(json_str: str, model_class: Type[T]) -> T:
        """Convert JSON string back to specified Pydantic model."""
        data = json.loads(json_str)
        return model_class(**data)


class CacheKeyGenerator:
    """Helper class for generating cache keys."""

    @staticmethod
    def model_key(identifier: str, date: str, model_name: str) -> str:
        """Generate cache key for any model."""
        return f"cache:{model_name}:{identifier}:{date}"


class RedisClientManager:
    """Manager for Redis client connections."""

    _client = None

    @classmethod
    def get_client(cls) -> redis.Redis:
        """Get or create Redis client."""
        if cls._client is None:
            config = get_config()
            cls._client = redis.Redis(
                host=config.redis_host,
                port=config.redis_port,
                username=config.redis_username,
                password=config.redis_password,
                decode_responses=True
            )
        return cls._client


class CacheService:
    """Generic cache service using Redis TTL - no metadata overhead."""

    @staticmethod
    def get_cached_model(identifier: str, date: str, model_class: Type[T], model_name: Optional[str] = None) -> Optional[T]:
        """Retrieve cached model from Redis."""
        try:
            client = RedisClientManager.get_client()
            key = CacheKeyGenerator.model_key(identifier, date, model_name or model_class.__name__)

            cached_json = client.get(key)
            if cached_json:
                return CacheSerializer.deserialize_model(cached_json, model_class)

        except Exception as e:
            print(f"Cache retrieval error: {e}")

        return None

    @staticmethod
    def set_cached_model(identifier: str, date: str, model: BaseModel, ttl_hours: int = 3, model_name: Optional[str] = None):
        """Cache model in Redis with TTL."""
        try:
            client = RedisClientManager.get_client()
            key = CacheKeyGenerator.model_key(identifier, date, model_name or model.__class__.__name__)

            json_str = CacheSerializer.serialize_model(model)
            ttl_seconds = ttl_hours * 3600

            client.setex(key, ttl_seconds, json_str)

        except Exception as e:
            print(f"Cache storage error: {e}")

    @staticmethod
    def clear_cache_for_key(key_prefix: str) -> int:
        """Clear all cache entries with a specific key prefix."""
        try:
            client = RedisClientManager.get_client()
            pattern = f"cache:*:{key_prefix}*"
            keys = client.keys(pattern)

            if keys:
                return client.delete(*keys)
            return 0

        except Exception as e:
            print(f"Cache clear error: {e}")
            return 0