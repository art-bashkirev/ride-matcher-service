"""Cache services package."""

from .redis import CacheInterface, RedisCache, ModelCache, create_cache, create_model_cache, lru_cache_async

# Re-export legacy cache classes for backward compatibility
import importlib.util
import os

# Import the legacy cache module  
legacy_cache_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache.py')
spec = importlib.util.spec_from_file_location("legacy_cache", legacy_cache_path)
legacy_cache = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy_cache)

# Export legacy classes
CacheService = legacy_cache.CacheService
CacheSerializer = legacy_cache.CacheSerializer
CacheKeyGenerator = legacy_cache.CacheKeyGenerator
RedisClientManager = legacy_cache.RedisClientManager

__all__ = [
    "CacheInterface",
    "RedisCache", 
    "ModelCache",
    "create_cache",
    "create_model_cache",
    "lru_cache_async",
    # Legacy exports
    "CacheService",
    "CacheSerializer",
    "CacheKeyGenerator", 
    "RedisClientManager"
]