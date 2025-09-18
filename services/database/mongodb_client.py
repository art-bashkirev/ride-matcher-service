"""MongoDB storage service implementation."""

import logging
from typing import Any, Dict, List, Optional
from pymongo import AsyncMongoClient
from pymongo.errors import PyMongoError
from bson import ObjectId

from .base import StorageService
from config.settings import get_config

logger = logging.getLogger(__name__)


class MongoDBStorageService(StorageService):
    """MongoDB-based storage service implementation."""

    def __init__(self, uri: Optional[str] = None, database: str = "ride_matcher"):
        self.uri = uri or get_config().mongodb_uri
        self.database_name = database
        self._client: Optional[AsyncMongoClient] = None
        self._db = None

    async def _get_client(self) -> AsyncMongoClient:
        """Get or create MongoDB client."""
        if self._client is None:
            if not self.uri:
                raise ValueError("MongoDB URI not configured")
            # Use AsyncMongoClient with compression
            self._client = AsyncMongoClient(
                self.uri,
                compressors="snappy,zstd,zlib",
                zlibCompressionLevel=6
            )
        return self._client

    async def _get_database(self):
        """Get or create database instance."""
        if self._db is None:
            client = await self._get_client()
            self._db = client[self.database_name]
        return self._db

    async def _get_collection(self, collection: str):
        """Get collection instance."""
        db = await self._get_database()
        return db[collection]

    async def insert_one(self, collection: str, document: Dict[str, Any]) -> str:
        """Insert a single document and return its ID."""
        try:
            coll = await self._get_collection(collection)
            result = await coll.insert_one(document)
            return str(result.inserted_id)
        except PyMongoError as e:
            logger.error(f"MongoDB insert_one error in collection {collection}: {e}")
            raise

    async def insert_many(self, collection: str, documents: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple documents and return their IDs."""
        try:
            coll = await self._get_collection(collection)
            result = await coll.insert_many(documents)
            return [str(oid) for oid in result.inserted_ids]
        except PyMongoError as e:
            logger.error(f"MongoDB insert_many error in collection {collection}: {e}")
            raise

    async def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document matching the query."""
        try:
            coll = await self._get_collection(collection)
            document = await coll.find_one(query)
            if document:
                # Convert ObjectId to string for JSON serialization
                document['_id'] = str(document['_id'])
            return document
        except PyMongoError as e:
            logger.error(f"MongoDB find_one error in collection {collection}: {e}")
            raise

    async def find_many(self, collection: str, query: Dict[str, Any],
                       skip: int = 0, limit: Optional[int] = None,
                       sort: Optional[List[tuple]] = None) -> List[Dict[str, Any]]:
        """Find multiple documents matching the query with pagination and sorting."""
        try:
            coll = await self._get_collection(collection)
            cursor = coll.find(query)

            if sort:
                cursor = cursor.sort(sort)

            if skip > 0:
                cursor = cursor.skip(skip)

            if limit is not None:
                cursor = cursor.limit(limit)

            documents = await cursor.to_list(length=None)

            # Convert ObjectId to string for JSON serialization
            for doc in documents:
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])

            return documents
        except PyMongoError as e:
            logger.error(f"MongoDB find_many error in collection {collection}: {e}")
            raise

    async def update_one(self, collection: str, query: Dict[str, Any],
                        update: Dict[str, Any]) -> bool:
        """Update a single document matching the query."""
        try:
            coll = await self._get_collection(collection)
            result = await coll.update_one(query, {"$set": update})
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"MongoDB update_one error in collection {collection}: {e}")
            raise

    async def update_many(self, collection: str, query: Dict[str, Any],
                         update: Dict[str, Any]) -> int:
        """Update multiple documents matching the query. Returns count of updated documents."""
        try:
            coll = await self._get_collection(collection)
            result = await coll.update_many(query, {"$set": update})
            return result.modified_count
        except PyMongoError as e:
            logger.error(f"MongoDB update_many error in collection {collection}: {e}")
            raise

    async def delete_one(self, collection: str, query: Dict[str, Any]) -> bool:
        """Delete a single document matching the query."""
        try:
            coll = await self._get_collection(collection)
            result = await coll.delete_one(query)
            return result.deleted_count > 0
        except PyMongoError as e:
            logger.error(f"MongoDB delete_one error in collection {collection}: {e}")
            raise

    async def delete_many(self, collection: str, query: Dict[str, Any]) -> int:
        """Delete multiple documents matching the query. Returns count of deleted documents."""
        try:
            coll = await self._get_collection(collection)
            result = await coll.delete_many(query)
            return result.deleted_count
        except PyMongoError as e:
            logger.error(f"MongoDB delete_many error in collection {collection}: {e}")
            raise

    async def count_documents(self, collection: str, query: Dict[str, Any]) -> int:
        """Count documents matching the query."""
        try:
            coll = await self._get_collection(collection)
            return await coll.count_documents(query)
        except PyMongoError as e:
            logger.error(f"MongoDB count_documents error in collection {collection}: {e}")
            raise

    async def create_index(self, collection: str, keys: List[tuple],
                          unique: bool = False) -> None:
        """Create an index on the collection."""
        try:
            coll = await self._get_collection(collection)
            await coll.create_index(keys, unique=unique)
        except PyMongoError as e:
            logger.error(f"MongoDB create_index error in collection {collection}: {e}")
            raise

    async def close(self) -> None:
        """Close storage connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()