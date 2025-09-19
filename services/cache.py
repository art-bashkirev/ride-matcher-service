"""Cache service using Redis JSON for storing schedule responses."""

import json
from datetime import datetime, timedelta
from typing import Optional, Any
from redis_om import JsonModel, Field
from redis_om import get_redis_connection

from config.settings import get_config


class CachedSchedule(JsonModel):
    """Redis JSON model for cached schedule data."""
    station_id: str = Field(index=True)
    date: str = Field(index=True)
    data: str  # JSON string of the schedule response
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime = Field(default_factory=lambda: datetime.now() + timedelta(hours=1))

    class Meta:
        database = get_redis_connection(
            host=get_config().redis_host,
            port=get_config().redis_port,
            db=get_config().redis_db,
            password=get_config().redis_password,
            decode_responses=True
        )


class CacheService:
    """Service for caching schedule responses using Redis JSON."""

    @staticmethod
    def _get_cache_key(station_id: str, date: str) -> str:
        """Generate a unique cache key for the schedule request."""
        return f"schedule:{station_id}:{date}"

    @staticmethod
    def get_cached_schedule(station_id: str, date: str) -> Optional[Any]:
        """Retrieve cached schedule if it exists and hasn't expired."""
        try:
            # Find existing cache entry
            cached = CachedSchedule.find(
                (CachedSchedule.station_id == station_id) &
                (CachedSchedule.date == date)
            ).first_or_none()

            if cached and cached.expires_at > datetime.now():
                # Return the parsed JSON data
                return json.loads(cached.data)
            elif cached:
                # Cache expired, delete it
                cached.delete()

        except Exception as e:
            print(f"Cache retrieval error: {e}")

        return None

    @staticmethod
    def set_cached_schedule(station_id: str, date: str, schedule_data: Any, ttl_hours: int = 1):
        """Cache the schedule response with TTL."""
        try:
            # Convert schedule data to JSON string
            data_str = json.dumps(schedule_data)

            # Create or update cache entry
            cached = CachedSchedule(
                station_id=station_id,
                date=date,
                data=data_str,
                expires_at=datetime.now() + timedelta(hours=ttl_hours)
            )
            cached.save()

        except Exception as e:
            print(f"Cache storage error: {e}")

    @staticmethod
    def clear_expired_cache():
        """Remove expired cache entries."""
        try:
            now = datetime.now()
            expired_entries = CachedSchedule.find(CachedSchedule.expires_at < now)
            for entry in expired_entries:
                entry.delete()
        except Exception as e:
            print(f"Cache cleanup error: {e}")