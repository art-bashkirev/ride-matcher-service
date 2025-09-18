"""Abstract base classes for database operations."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic
from datetime import datetime

T = TypeVar('T')


class CacheService(ABC):
    """Abstract base class for cache operations (Redis)."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache by key."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL in seconds."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache by key."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass

    @abstractmethod
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for key in seconds."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close cache connection."""
        pass


class StorageService(ABC):
    """Abstract base class for storage operations (MongoDB)."""

    @abstractmethod
    async def insert_one(self, collection: str, document: Dict[str, Any]) -> str:
        """Insert a single document and return its ID."""
        pass

    @abstractmethod
    async def insert_many(self, collection: str, documents: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple documents and return their IDs."""
        pass

    @abstractmethod
    async def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document matching the query."""
        pass

    @abstractmethod
    async def find_many(self, collection: str, query: Dict[str, Any],
                       skip: int = 0, limit: Optional[int] = None,
                       sort: Optional[List[tuple]] = None) -> List[Dict[str, Any]]:
        """Find multiple documents matching the query with pagination and sorting."""
        pass

    @abstractmethod
    async def update_one(self, collection: str, query: Dict[str, Any],
                        update: Dict[str, Any]) -> bool:
        """Update a single document matching the query."""
        pass

    @abstractmethod
    async def update_many(self, collection: str, query: Dict[str, Any],
                         update: Dict[str, Any]) -> int:
        """Update multiple documents matching the query. Returns count of updated documents."""
        pass

    @abstractmethod
    async def delete_one(self, collection: str, query: Dict[str, Any]) -> bool:
        """Delete a single document matching the query."""
        pass

    @abstractmethod
    async def delete_many(self, collection: str, query: Dict[str, Any]) -> int:
        """Delete multiple documents matching the query. Returns count of deleted documents."""
        pass

    @abstractmethod
    async def count_documents(self, collection: str, query: Dict[str, Any]) -> int:
        """Count documents matching the query."""
        pass

    @abstractmethod
    async def create_index(self, collection: str, keys: List[tuple],
                          unique: bool = False) -> None:
        """Create an index on the collection."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close storage connection."""
        pass


class ORMService(ABC):
    """Abstract base class for ORM operations (PostgreSQL via TortoiseORM)."""

    @abstractmethod
    async def create(self, model_class: Any, **kwargs) -> Any:
        """Create a new model instance."""
        pass

    @abstractmethod
    async def get(self, model_class: Any, **kwargs) -> Any:
        """Get a single model instance."""
        pass

    @abstractmethod
    async def get_or_none(self, model_class: Any, **kwargs) -> Optional[Any]:
        """Get a single model instance or None if not found."""
        pass

    @abstractmethod
    async def filter(self, model_class: Any, **kwargs) -> List[Any]:
        """Filter model instances."""
        pass

    @abstractmethod
    async def update(self, instance: Any, **kwargs) -> None:
        """Update a model instance."""
        pass

    @abstractmethod
    async def delete(self, instance: Any) -> None:
        """Delete a model instance."""
        pass

    @abstractmethod
    async def bulk_create(self, model_class: Any, instances: List[Dict[str, Any]]) -> List[Any]:
        """Bulk create model instances."""
        pass

    @abstractmethod
    async def bulk_update(self, instances: List[Any], fields: List[str]) -> None:
        """Bulk update model instances."""
        pass

    @abstractmethod
    async def count(self, model_class: Any, **kwargs) -> int:
        """Count model instances matching criteria."""
        pass

    @abstractmethod
    async def exists(self, model_class: Any, **kwargs) -> bool:
        """Check if model instances exist matching criteria."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close ORM connection."""
        pass