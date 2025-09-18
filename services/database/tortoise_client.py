"""PostgreSQL ORM service implementation using TortoiseORM."""

import logging
from typing import Any, Dict, List, Optional, Type
from tortoise import Tortoise
from tortoise.exceptions import DoesNotExist, IntegrityError

from .base import ORMService
from .models import User, Trip, Station
from config.settings import get_config

logger = logging.getLogger(__name__)


class TortoiseORMService(ORMService):
    """TortoiseORM-based ORM service implementation for PostgreSQL."""

    def __init__(self, uri: Optional[str] = None):
        self.uri = uri or get_config().postgresql_uri
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Ensure TortoiseORM is initialized."""
        if not self._initialized:
            if not self.uri:
                raise ValueError("PostgreSQL URI not configured")

            # Configure TortoiseORM with transaction pooler connection
            await Tortoise.init(
                db_url=self.uri,
                modules={"models": ["services.database.models"]},
                # Use connection pooling for better performance with multiple clients
                use_tz=True,
            )

            # Generate schema (only in development, in production use migrations)
            if get_config().is_development:
                await Tortoise.generate_schemas()

            self._initialized = True

    async def create(self, model_class: Type[Any], **kwargs) -> Any:
        """Create a new model instance."""
        await self._ensure_initialized()
        try:
            instance = await model_class.create(**kwargs)
            return instance
        except IntegrityError as e:
            logger.error(f"Integrity error creating {model_class.__name__}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating {model_class.__name__}: {e}")
            raise

    async def get(self, model_class: Type[Any], **kwargs) -> Any:
        """Get a single model instance."""
        await self._ensure_initialized()
        try:
            return await model_class.get(**kwargs)
        except DoesNotExist:
            raise ValueError(f"{model_class.__name__} not found with criteria: {kwargs}")
        except Exception as e:
            logger.error(f"Error getting {model_class.__name__}: {e}")
            raise

    async def get_or_none(self, model_class: Type[Any], **kwargs) -> Optional[Any]:
        """Get a single model instance or None if not found."""
        await self._ensure_initialized()
        try:
            return await model_class.get_or_none(**kwargs)
        except Exception as e:
            logger.error(f"Error getting {model_class.__name__}: {e}")
            raise

    async def filter(self, model_class: Type[Any], **kwargs) -> List[Any]:
        """Filter model instances."""
        await self._ensure_initialized()
        try:
            return await model_class.filter(**kwargs)
        except Exception as e:
            logger.error(f"Error filtering {model_class.__name__}: {e}")
            raise

    async def update(self, instance: Any, **kwargs) -> None:
        """Update a model instance."""
        await self._ensure_initialized()
        try:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            await instance.save()
        except Exception as e:
            logger.error(f"Error updating {instance.__class__.__name__}: {e}")
            raise

    async def delete(self, instance: Any) -> None:
        """Delete a model instance."""
        await self._ensure_initialized()
        try:
            await instance.delete()
        except Exception as e:
            logger.error(f"Error deleting {instance.__class__.__name__}: {e}")
            raise

    async def bulk_create(self, model_class: Type[Any], instances: List[Dict[str, Any]]) -> List[Any]:
        """Bulk create model instances."""
        await self._ensure_initialized()
        try:
            return await model_class.bulk_create([
                model_class(**data) for data in instances
            ])
        except Exception as e:
            logger.error(f"Error bulk creating {model_class.__name__}: {e}")
            raise

    async def bulk_update(self, instances: List[Any], fields: List[str]) -> None:
        """Bulk update model instances."""
        await self._ensure_initialized()
        try:
            await model_class.bulk_update(instances, fields)
        except Exception as e:
            logger.error(f"Error bulk updating {instances[0].__class__.__name__ if instances else 'Unknown'}: {e}")
            raise

    async def count(self, model_class: Type[Any], **kwargs) -> int:
        """Count model instances matching criteria."""
        await self._ensure_initialized()
        try:
            return await model_class.filter(**kwargs).count()
        except Exception as e:
            logger.error(f"Error counting {model_class.__name__}: {e}")
            raise

    async def exists(self, model_class: Type[Any], **kwargs) -> bool:
        """Check if model instances exist matching criteria."""
        await self._ensure_initialized()
        try:
            return await model_class.filter(**kwargs).exists()
        except Exception as e:
            logger.error(f"Error checking existence of {model_class.__name__}: {e}")
            raise

    async def close(self) -> None:
        """Close ORM connection."""
        if self._initialized:
            await Tortoise.close_connections()
            self._initialized = False

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_initialized()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    # Convenience methods for specific models
    async def get_or_create_user(self, telegram_id: int, **defaults) -> tuple[User, bool]:
        """Get or create a user by telegram_id."""
        await self._ensure_initialized()
        user, created = await User.get_or_create(
            telegram_id=telegram_id,
            defaults=defaults
        )
        return user, created

    async def create_trip(self, user_id: int, from_station: str,
                         trip_date: str, **kwargs) -> Trip:
        """Create a trip for a user."""
        await self._ensure_initialized()
        return await Trip.create(
            user_id=user_id,
            from_station=from_station,
            trip_date=trip_date,
            **kwargs
        )

    async def get_user_trips(self, user_id: int, limit: int = 10) -> List[Trip]:
        """Get recent trips for a user."""
        await self._ensure_initialized()
        return await Trip.filter(user_id=user_id).order_by("-created_at").limit(limit)

    async def search_stations(self, query: str, limit: int = 20) -> List[Station]:
        """Search stations by title."""
        await self._ensure_initialized()
        return await Station.filter(
            title__icontains=query
        ).limit(limit).order_by("title")