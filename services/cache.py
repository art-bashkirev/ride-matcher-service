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
    """Generic helper class for serializing/deserializing any Pydantic BaseModel."""

    @staticmethod
    def serialize_model(model: BaseModel) -> str:
        """Convert any Pydantic BaseModel to JSON string."""
        return model.model_dump_json()

    @staticmethod
    def deserialize_model(json_str: str, model_class: Type[T]) -> T:
        """Convert JSON string back to specified Pydantic model."""
        data = json.loads(json_str)
        return model_class(**data)

    @staticmethod
    def create_cache_metadata(station_id: str, date: str, ttl_hours: int) -> Dict[str, Any]:
        """Create metadata for cache entry."""
        return {
            'station_id': station_id,
            'date': date,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=ttl_hours)).isoformat(),
            'ttl_hours': ttl_hours
        }


class CacheKeyGenerator:
    """Helper class for generating cache keys."""

    @staticmethod
    def schedule_key(station_id: str, date: str) -> str:
        """Generate cache key for schedule data."""
        return f"schedule:{station_id}:{date}"

    @staticmethod
    def metadata_key(station_id: str, date: str) -> str:
        """Generate cache key for metadata."""
        return f"metadata:{station_id}:{date}"


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
    """Service for caching responses with clean separation of concerns."""

    @staticmethod
    def get_cached_model(station_id: str, date: str, model_class: Type[T]) -> Optional[T]:
        """Generic method to retrieve any cached Pydantic model."""
        try:
            client = RedisClientManager.get_client()
            key = CacheKeyGenerator.schedule_key(station_id, date)
            meta_key = CacheKeyGenerator.metadata_key(station_id, date)

            # Get both data and metadata
            cached_json = client.get(key)
            metadata_json = client.get(meta_key)

            if not cached_json or not metadata_json:
                return None

            # Check if expired
            metadata = json.loads(metadata_json)
            expires_at = datetime.fromisoformat(metadata['expires_at'])

            if datetime.now() > expires_at:
                # Clean up expired entries
                client.delete(key, meta_key)
                return None

            return CacheSerializer.deserialize_model(cached_json, model_class)

        except Exception as e:
            print(f"Cache retrieval error: {e}")
            return None

    @staticmethod
    def set_cached_model(station_id: str, date: str, model: BaseModel, ttl_hours: int = 1):
        """Generic method to cache any Pydantic model."""
        try:
            client = RedisClientManager.get_client()
            key = CacheKeyGenerator.schedule_key(station_id, date)
            meta_key = CacheKeyGenerator.metadata_key(station_id, date)

            # Serialize data
            model_json = CacheSerializer.serialize_model(model)
            metadata = CacheSerializer.create_cache_metadata(station_id, date, ttl_hours)
            metadata_json = json.dumps(metadata)

            # Store with TTL
            ttl_seconds = ttl_hours * 3600
            client.setex(key, ttl_seconds, model_json)
            client.setex(meta_key, ttl_seconds, metadata_json)

        except Exception as e:
            print(f"Cache storage error: {e}")

    @staticmethod
    def clear_cache_for_key(key_prefix: str) -> int:
        """Clear all cache entries with a specific key prefix. Returns number cleared."""
        try:
            client = RedisClientManager.get_client()
            deleted_count = 0

            # Find all metadata keys with prefix
            pattern = f"metadata:{key_prefix}*"
            meta_keys = client.keys(pattern)

            for meta_key in meta_keys:
                try:
                    metadata_json = client.get(meta_key)
                    if metadata_json:
                        metadata = json.loads(metadata_json)
                        # Extract the full key from metadata
                        station_id = metadata.get('station_id', '')
                        date = metadata.get('date', '')
                        data_key = CacheKeyGenerator.schedule_key(station_id, date)

                        client.delete(data_key, meta_key)
                        deleted_count += 1
                except Exception:
                    continue

            return deleted_count

        except Exception as e:
            print(f"Cache clear error: {e}")
            return 0