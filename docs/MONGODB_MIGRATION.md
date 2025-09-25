# MongoDB Driver Migration: Motor to PyMongo

This document explains the migration from Motor to PyMongo's native async client.

## Background

As of PyMongo 4.8+, MongoDB's official Python driver includes native async support via `AsyncMongoClient`. This eliminates the need for Motor (a third-party async wrapper) in most use cases. Motor was essential when PyMongo was sync-only, but now PyMongo provides first-class async support.

## Migration Changes

### Before (Motor)
```python
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase

class StationsService:
    def __init__(self):
        self._client: Optional[AsyncIOMotorClient] = None
        self._db: Optional[AsyncIOMotorDatabase] = None
        self._collection: Optional[AsyncIOMotorCollection] = None
    
    async def _get_collection(self) -> AsyncIOMotorCollection:
        if self._collection is None:
            self._client = AsyncIOMotorClient(self.config.mongodb_url)
            # ... rest of setup
```

### After (PyMongo)
```python
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.asynchronous.collection import AsyncCollection

class StationsService:
    def __init__(self):
        self._client: Optional[AsyncMongoClient] = None
        self._db: Optional[AsyncDatabase] = None
        self._collection: Optional[AsyncCollection] = None
    
    async def _get_collection(self) -> AsyncCollection:
        if self._collection is None:
            self._client = AsyncMongoClient(self.config.mongodb_url)
            # ... rest of setup
```

## Key Differences

### Import Changes
- `AsyncIOMotorClient` → `AsyncMongoClient`
- `AsyncIOMotorDatabase` → `AsyncDatabase` 
- `AsyncIOMotorCollection` → `AsyncCollection`

### Module Paths
- Motor: `motor.motor_asyncio`
- PyMongo: `pymongo` and `pymongo.asynchronous.*`

### API Compatibility
The async API is largely identical between Motor and PyMongo's async client:
- All CRUD operations work the same way
- Index operations are identical
- Connection handling is very similar

## Benefits of Migration

1. **Official Support**: PyMongo async is maintained by MongoDB directly
2. **Reduced Dependencies**: One less third-party package to maintain
3. **Better Performance**: Native implementation may have performance benefits
4. **Future-Proof**: Official MongoDB driver will have the latest features first

## Compatibility

- **Breaking Changes**: None for our use case - the API is nearly identical
- **Dependencies**: Motor is kept in requirements.txt for backward compatibility during transition
- **Minimum Version**: Requires PyMongo >= 4.8.0 for full async support

## Testing

After migration, all existing functionality continues to work:
- Database connections
- CRUD operations
- Index management  
- Error handling

## Rollback Plan

If issues arise, the migration can be easily reverted by changing the imports back to Motor. The functional code remains identical.

## Further Reading

- [PyMongo Async Tutorial](https://pymongo.readthedocs.io/en/stable/tutorial.html#asynchronous-framework-integration)
- [PyMongo 4.8 Release Notes](https://pymongo.readthedocs.io/en/stable/changelog.html)
- [Motor Documentation](https://motor.readthedocs.io/) (for reference)