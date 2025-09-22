"""Cache abstraction layer with Redis implementation."""
from typing import Optional, Any, TypeVar, Type, Generic
from abc import ABC, abstractmethod
from functools import wraps
import json
import redis
from pydantic import BaseModel

from config.settings import get_config

T = TypeVar('T', bound=BaseModel)


class CacheInterface(ABC):
    """Abstract cache interface."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> bool:
        """Set value with optional TTL."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key."""
        pass
    
    @abstractmethod
    async def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern."""
        pass


class RedisCache(CacheInterface):
    """Redis implementation of cache interface."""
    
    def __init__(self):
        self._client = None
        
    def _get_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._client is None:
            config = get_config()
            self._client = redis.Redis(
                host=config.redis_host,
                port=config.redis_port,
                username=config.redis_username,
                password=config.redis_password,
                decode_responses=True
            )
        return self._client
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        try:
            client = self._get_client()
            return client.get(key)
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    async def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> bool:
        """Set value with optional TTL."""
        try:
            client = self._get_client()
            if ttl_seconds:
                client.setex(key, ttl_seconds, value)
            else:
                client.set(key, value)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key."""
        try:
            client = self._get_client()
            return bool(client.delete(key))
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern."""
        try:
            client = self._get_client()
            keys = client.keys(pattern)
            if keys:
                return client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache clear error: {e}")
            return 0


class ModelCache(Generic[T]):
    """Cache wrapper for Pydantic models."""
    
    def __init__(self, cache: CacheInterface, key_prefix: str = "model"):
        self.cache = cache
        self.key_prefix = key_prefix
    
    def _make_key(self, identifier: str, model_name: str) -> str:
        """Generate cache key."""
        return f"{self.key_prefix}:{model_name}:{identifier}"
    
    async def get_model(self, identifier: str, model_class: Type[T]) -> Optional[T]:
        """Get cached model."""
        key = self._make_key(identifier, model_class.__name__)
        cached_json = await self.cache.get(key)
        
        if cached_json:
            try:
                data = json.loads(cached_json)
                return model_class(**data)
            except Exception as e:
                print(f"Model deserialization error: {e}")
        
        return None
    
    async def set_model(self, identifier: str, model: BaseModel, ttl_seconds: Optional[int] = None) -> bool:
        """Cache model."""
        key = self._make_key(identifier, model.__class__.__name__)
        
        try:
            json_str = model.model_dump_json()
            return await self.cache.set(key, json_str, ttl_seconds)
        except Exception as e:
            print(f"Model serialization error: {e}")
            return False


def lru_cache_async(maxsize: int = 128, ttl_seconds: int = 3600):
    """LRU cache decorator for async functions (placeholder)."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # TODO: Implement LRU cache logic with Redis
            # For now, just call the function
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Factory functions
def create_cache() -> CacheInterface:
    """Create cache instance."""
    return RedisCache()


def create_model_cache(key_prefix: str = "model") -> ModelCache:
    """Create model cache instance."""
    cache = create_cache()
    return ModelCache(cache, key_prefix)