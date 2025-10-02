"""Redis-based caching layer for Yandex Schedules API responses."""

import hashlib
import json
from typing import Optional, Type, TypeVar

from pydantic import BaseModel
from redis.exceptions import RedisError

from config.log_setup import get_logger
from services.cache.redis_client import BaseRedisClient
from services.yandex_schedules.models.schedule import ScheduleRequest, ScheduleResponse
from services.yandex_schedules.models.search import SearchRequest, SearchResponse

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class YandexSchedulesCache(BaseRedisClient):
    """Redis cache manager for Yandex Schedules API responses."""

    def _generate_cache_key(self, prefix: str, request: BaseModel) -> str:
        """Generate a cache key from request parameters."""
        try:
            if self.config.cache_readable_keys:
                return self._generate_readable_cache_key(prefix, request)
            else:
                return self._generate_hashed_cache_key(prefix, request)
        except Exception as e:
            logger.error("Error generating cache key: %s", e)
            # Fallback to a basic key
            return f"{prefix}:error_{hash(str(request))}"

    def _generate_alternate_cache_key(self, prefix: str, request: BaseModel) -> str:
        """Generate the alternate cache key format (opposite of current setting)."""
        try:
            if self.config.cache_readable_keys:
                return self._generate_hashed_cache_key(prefix, request)
            else:
                return self._generate_readable_cache_key(prefix, request)
        except Exception as e:
            logger.error("Error generating alternate cache key: %s", e)
            # Fallback to a basic key
            return f"{prefix}:error_{hash(str(request))}"

    def _generate_hashed_cache_key(self, prefix: str, request: BaseModel) -> str:
        """Generate a hashed cache key (compact, collision-resistant)."""
        # Create a deterministic hash from the request parameters
        request_dict = request.model_dump(exclude_none=True, by_alias=True)

        # Ensure date is normalized for consistent caching
        if "date" in request_dict and request_dict["date"]:
            # Keep the date as-is for now, but could normalize to YYYY-MM-DD format
            pass

        request_json = json.dumps(request_dict, sort_keys=True)
        hash_digest = hashlib.md5(request_json.encode()).hexdigest()
        return f"{prefix}:{hash_digest}"

    def _generate_readable_cache_key(self, prefix: str, request: BaseModel) -> str:
        """Generate a human-readable cache key (easier to debug, potentially longer)."""
        request_dict = request.model_dump(exclude_none=True, by_alias=True)

        # Build readable key parts
        key_parts = [prefix]

        # Add station if present
        if "station" in request_dict:
            key_parts.append(f"station_{request_dict['station']}")

        # Add from/to if present (for search requests)
        if "from" in request_dict:
            key_parts.append(f"from_{request_dict['from']}")
        if "to" in request_dict:
            key_parts.append(f"to_{request_dict['to']}")

        # Add date if present
        if "date" in request_dict and request_dict["date"]:
            key_parts.append(f"date_{request_dict['date']}")

        # Add timezone if present (sanitize special characters)
        if "result_timezone" in request_dict:
            tz = request_dict["result_timezone"].replace("/", "_").replace(" ", "_")
            key_parts.append(f"tz_{tz}")

        # Add limit if different from default
        if "limit" in request_dict and request_dict["limit"] != 100:
            key_parts.append(f"limit_{request_dict['limit']}")

        # Add offset if non-zero
        if "offset" in request_dict and request_dict["offset"] != 0:
            key_parts.append(f"offset_{request_dict['offset']}")

        # Add other significant parameters
        for key, value in request_dict.items():
            if key not in [
                "station",
                "from",
                "to",
                "date",
                "result_timezone",
                "limit",
                "offset",
            ]:
                if value is not None:
                    # Sanitize the value for Redis key safety
                    sanitized_value = (
                        str(value).replace("/", "_").replace(" ", "_").replace(":", "_")
                    )
                    key_parts.append(f"{key}_{sanitized_value}")

        return ":".join(key_parts)

    async def get_search_results(
        self, request: SearchRequest, response_type: Type[T] = SearchResponse
    ) -> Optional[T]:
        """Get cached search results."""
        logger.info("get_search_results called with request: %s", request.model_dump())
        cache_key = self._generate_cache_key("search", request)
        logger.debug("Requesting cached search results with key: %s", cache_key)
        result = await self._get_cached_response(cache_key, response_type)
        if result is not None:
            logger.info("Cache hit for search results with key: %s", cache_key)
            return result

        alt_cache_key = self._generate_alternate_cache_key("search", request)
        if alt_cache_key != cache_key:
            logger.debug(
                "Trying alternate key format for search results: %s", alt_cache_key
            )
            result = await self._get_cached_response(alt_cache_key, response_type)
            if result is not None:
                logger.info(
                    "Cache hit for search results with alternate key: %s", alt_cache_key
                )
                return result

        logger.info(
            "Cache miss for search results with request: %s", request.model_dump()
        )
        return None

    async def set_search_results(
        self, request: SearchRequest, response: SearchResponse
    ) -> bool:
        """Cache search results."""
        logger.info("set_search_results called with request: %s", request.model_dump())
        cache_key = self._generate_cache_key("search", request)
        ttl = self.config.cache_ttl_search
        result = await self._set_cached_response(cache_key, response, ttl)
        if result:
            logger.info("Search results cached successfully for key: %s", cache_key)
        else:
            logger.warning("Failed to cache search results for key: %s", cache_key)
        return result

    async def get_schedule_results(
        self, request: ScheduleRequest, response_type: Type[T] = ScheduleResponse
    ) -> Optional[T]:
        """Get cached schedule results."""
        logger.info(
            "get_schedule_results called with request: %s", request.model_dump()
        )
        cache_key = self._generate_cache_key("schedule", request)
        logger.debug("Requesting cached schedule results with key: %s", cache_key)
        result = await self._get_cached_response(cache_key, response_type)
        if result is not None:
            logger.info("Cache hit for schedule results with key: %s", cache_key)
            return result

        alt_cache_key = self._generate_alternate_cache_key("schedule", request)
        if alt_cache_key != cache_key:
            logger.debug(
                "Trying alternate key format for schedule results: %s", alt_cache_key
            )
            result = await self._get_cached_response(alt_cache_key, response_type)
            if result is not None:
                logger.info(
                    "Cache hit for schedule results with alternate key: %s",
                    alt_cache_key,
                )
                return result

        logger.info(
            "Cache miss for schedule results with request: %s", request.model_dump()
        )
        return None

    async def set_schedule_results(
        self, request: ScheduleRequest, response: ScheduleResponse
    ) -> bool:
        """Cache schedule results."""
        logger.info(
            "set_schedule_results called with request: %s", request.model_dump()
        )
        cache_key = self._generate_cache_key("schedule", request)
        ttl = self.config.cache_ttl_schedule
        result = await self._set_cached_response(cache_key, response, ttl)
        if result:
            logger.info("Schedule results cached successfully for key: %s", cache_key)
        else:
            logger.warning("Failed to cache schedule results for key: %s", cache_key)
        return result

    async def _get_cached_response(
        self, cache_key: str, response_type: Type[T]
    ) -> Optional[T]:
        """Get cached response from Redis."""
        logger.debug("_get_cached_response called for key: %s", cache_key)
        try:
            redis_client = await self._get_redis()
            cached_data = await redis_client.get(cache_key)

            if cached_data is None:
                logger.debug("Cache miss for key: %s", cache_key)
                return None

            logger.debug("Cache hit for key: %s", cache_key)
            response_dict = json.loads(cached_data)
            logger.info("Deserialized cached response for key: %s", cache_key)
            return response_type(**response_dict)

        except RedisError as e:
            logger.error("Redis error when getting cache key %s: %s", cache_key, e)
            return None
        except (json.JSONDecodeError, ValueError) as e:
            logger.error("Error deserializing cached data for key %s: %s", cache_key, e)
            # Remove corrupted cache entry
            try:
                redis_client = await self._get_redis()
                await redis_client.delete(cache_key)
                logger.warning("Corrupted cache entry deleted for key: %s", cache_key)
            except RedisError:
                logger.error(
                    "Failed to delete corrupted cache entry for key: %s", cache_key
                )
            return None

    async def _set_cached_response(
        self, cache_key: str, response: BaseModel, ttl: int
    ) -> bool:
        """Set cached response in Redis with TTL."""
        logger.debug("_set_cached_response called for key: %s, ttl: %d", cache_key, ttl)
        try:
            redis_client = await self._get_redis()
            response_json = response.model_dump_json(by_alias=True)

            result = await redis_client.setex(cache_key, ttl, response_json)

            if result:
                logger.info("Cached response for key: %s (TTL: %ds)", cache_key, ttl)
            else:
                logger.warning("Failed to cache response for key: %s", cache_key)

            return bool(result)

        except RedisError as e:
            logger.error("Redis error when setting cache key %s: %s", cache_key, e)
            return False
        except Exception as e:
            logger.error("Unexpected error when caching key %s: %s", cache_key, e)
            return False

    async def clear_cache(self, pattern: str = "*") -> int:
        """Clear cache entries matching pattern."""
        logger.info("clear_cache called with pattern: %s", pattern)
        try:
            redis_client = await self._get_redis()
            keys = await redis_client.keys(pattern)
            logger.debug("Found %d keys matching pattern: %s", len(keys), pattern)
            if keys:
                deleted = await redis_client.delete(*keys)
                logger.info(
                    "Cleared %d cache entries matching pattern: %s", deleted, pattern
                )
                return deleted
            logger.info("No cache entries found matching pattern: %s", pattern)
            return 0
        except RedisError as e:
            logger.error("Redis error when clearing cache: %s", e)
            return 0

    async def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        logger.info("get_cache_stats called")
        try:
            redis_client = await self._get_redis()
            info = await redis_client.info()

            search_keys = len(await redis_client.keys("search:*"))
            schedule_keys = len(await redis_client.keys("schedule:*"))

            stats = {
                "total_keys": (
                    info.get("db0", {}).get("keys", 0) if "db0" in info else 0
                ),
                "search_keys": search_keys,
                "schedule_keys": schedule_keys,
                "memory_usage": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "redis_version": info.get("redis_version", "unknown"),
            }
            logger.info("Cache stats: %s", stats)
            return stats
        except RedisError as e:
            logger.error("Redis error when getting stats: %s", e)
            return {"error": str(e)}

    def close(self):
        """Close method for cached client compatibility.

        Since cache is a global singleton, we don't actually close the connection.
        Redis connections are managed globally and closed when the application shuts down.
        """
        logger.debug("close called on cache instance (no-op for global singleton)")

    async def shutdown(self):
        """Properly close Redis connection on application shutdown."""
        redis_client = type(self)._redis
        if redis_client:
            await redis_client.close()
            type(self)._redis = None
            logger.info("Redis connection closed gracefully")


# Global cache instance
_cache_instance: Optional[YandexSchedulesCache] = None


def get_cache() -> YandexSchedulesCache:
    """Get or create the global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = YandexSchedulesCache()
    return _cache_instance
