"""High-level service abstractions for database operations."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from .redis_client import RedisCacheService
from .mongodb_client import MongoDBStorageService
from .tortoise_client import TortoiseORMService
from .models import User
from config.settings import get_config

logger = logging.getLogger(__name__)


class CacheManager:
    """Manager for cache operations."""

    def __init__(self):
        self._cache: Optional[RedisCacheService] = None

    async def _get_cache(self) -> RedisCacheService:
        """Get or create cache service."""
        if self._cache is None:
            self._cache = RedisCacheService()
        return self._cache

    async def get_schedule_cache(self, station: str, date: str) -> Optional[Dict[str, Any]]:
        """Get cached schedule data."""
        cache = await self._get_cache()
        cache_key = f"schedule:{station}:{date}"
        return await cache.get(cache_key)

    async def set_schedule_cache(self, station: str, date: str, data: Dict[str, Any], ttl: int = 3600) -> bool:
        """Cache schedule data with TTL."""
        cache = await self._get_cache()
        cache_key = f"schedule:{station}:{date}"
        return await cache.set(cache_key, data, ttl)

    async def invalidate_schedule_cache(self, station: str, date: str) -> bool:
        """Invalidate cached schedule data."""
        cache = await self._get_cache()
        cache_key = f"schedule:{station}:{date}"
        return await cache.delete(cache_key)

    async def close(self) -> None:
        """Close cache connection."""
        if self._cache:
            await self._cache.close()


class StorageManager:
    """Manager for storage operations (MongoDB)."""

    def __init__(self):
        self._storage: Optional[MongoDBStorageService] = None

    async def _get_storage(self) -> MongoDBStorageService:
        """Get or create storage service."""
        if self._storage is None:
            self._storage = MongoDBStorageService()
        return self._storage

    async def get_stations(self, query: Optional[Dict[str, Any]] = None,
                          skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get stations from storage."""
        storage = await self._get_storage()
        return await storage.find_many("stations", query or {}, skip=skip, limit=limit)

    async def add_station(self, station_data: Dict[str, Any]) -> str:
        """Add a station to storage."""
        storage = await self._get_storage()
        return await storage.insert_one("stations", station_data)

    async def search_stations(self, search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search stations by title or code."""
        storage = await self._get_storage()
        query = {
            "$or": [
                {"title": {"$regex": search_term, "$options": "i"}},
                {"code": {"$regex": search_term, "$options": "i"}}
            ]
        }
        return await storage.find_many("stations", query, limit=limit)

    async def get_user_trips(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's recent trips."""
        storage = await self._get_storage()
        return await storage.find_many(
            "trips",
            {"user_id": user_id},
            sort=[("created_at", -1)],
            limit=limit
        )

    async def add_user_trip(self, trip_data: Dict[str, Any]) -> str:
        """Add a user trip to storage."""
        storage = await self._get_storage()
        return await storage.insert_one("trips", trip_data)

    async def close(self) -> None:
        """Close storage connection."""
        if self._storage:
            await self._storage.close()


class DatabaseManager:
    """Manager for ORM operations (PostgreSQL)."""

    def __init__(self):
        self._orm: Optional[TortoiseORMService] = None

    async def _get_orm(self) -> TortoiseORMService:
        """Get or create ORM service."""
        if self._orm is None:
            self._orm = TortoiseORMService()
        return self._orm

    async def get_or_create_user(self, telegram_id: int, **user_data) -> tuple:
        """Get or create a user."""
        orm = await self._get_orm()
        return await orm.get_or_create_user(telegram_id, **user_data)

    async def update_user_preferences(self, telegram_id: int, **preferences) -> None:
        """Update user preferences."""
        orm = await self._get_orm()
        user = await orm.get(User, telegram_id=telegram_id)
        await orm.update(user, **preferences)

    async def create_trip_record(self, telegram_id: int, from_station: str,
                                trip_date: date, **trip_data) -> Any:
        """Create a trip record for a user."""
        orm = await self._get_orm()
        user = await orm.get(User, telegram_id=telegram_id)
        return await orm.create_trip(user.id, from_station, trip_date.isoformat(), **trip_data)

    async def get_user_trip_history(self, telegram_id: int, limit: int = 10) -> List[Any]:
        """Get user's trip history."""
        orm = await self._get_orm()
        user = await orm.get(User, telegram_id=telegram_id)
        return await orm.get_user_trips(user.id, limit)

    async def search_stations_orm(self, query: str, limit: int = 20) -> List[Any]:
        """Search stations using ORM."""
        orm = await self._get_orm()
        return await orm.search_stations(query, limit)

    async def close(self) -> None:
        """Close ORM connection."""
        if self._orm:
            await self._orm.close()


class DatabaseService:
    """Unified database service providing access to all storage backends."""

    def __init__(self):
        self.cache = CacheManager()
        self.storage = StorageManager()
        self.database = DatabaseManager()

    async def close(self) -> None:
        """Close all database connections."""
        await self.cache.close()
        await self.storage.close()
        await self.database.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Global database service instance
_db_service = None


async def get_database_service() -> DatabaseService:
    """Get the global database service instance."""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service