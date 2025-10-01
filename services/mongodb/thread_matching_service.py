"""MongoDB service for thread matching with TTL support."""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from pymongo import AsyncMongoClient
from pymongo.database import Database as AsyncDatabase

from config.log_setup import get_logger
from config.settings import get_config

logger = get_logger(__name__)


class CandidateThread(BaseModel):
    """Candidate thread for a user."""
    thread_uid: str
    departure_time: str
    arrival_time: str
    from_station_code: str
    to_station_code: str
    from_station_title: str
    to_station_title: str


class UserSearchResults(BaseModel):
    """User's search results with candidate threads."""
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    from_station_code: str
    to_station_code: str
    from_station_title: str
    to_station_title: str
    candidate_threads: List[CandidateThread]
    created_at: datetime
    expires_at: datetime


class ThreadMatch(BaseModel):
    """Matched users for a thread."""
    thread_uid: str
    departure_time: str
    arrival_time: str
    users: List[Dict[str, Any]]  # List of user info dicts
    created_at: datetime


class ThreadMatchingService:
    """Service for MongoDB operations on thread matching."""

    def __init__(self):
        self.config = get_config()
        self._client: Optional[AsyncMongoClient] = None
        self._db: Optional[AsyncDatabase] = None
        # Default TTL: 1 hour (60 minutes) to match the search time window
        self.default_ttl_minutes = 60

    async def _get_client(self) -> AsyncMongoClient:
        """Get MongoDB client."""
        if self._client is None:
            if not all([self.config.mongodb_host, self.config.mongodb_user, self.config.mongodb_password]):
                raise ValueError("MongoDB configuration incomplete")
            uri = f"mongodb+srv://{self.config.mongodb_user}:{self.config.mongodb_password}@{self.config.mongodb_host}/?retryWrites=true&w=majority"
            self._client = AsyncMongoClient(uri)
            logger.info("MongoDB client created for thread matching service")
        return self._client

    async def _get_db(self) -> AsyncDatabase:
        """Get database."""
        if self._db is None:
            client = await self._get_client()
            self._db = client["ride_matcher"]
            logger.debug("Using ride_matcher database")
        return self._db

    async def get_search_results_collection(self):
        """Get search results collection with TTL index."""
        db = await self._get_db()
        collection = db["user_search_results"]
        
        # Create TTL index on expires_at field (if not exists)
        try:
            await collection.create_index("expires_at", expireAfterSeconds=0)
            await collection.create_index("telegram_id")
            await collection.create_index("candidate_threads.thread_uid")
            logger.debug("TTL and query indexes ensured on user_search_results collection")
        except Exception as e:
            logger.warning("Failed to create indexes on user_search_results: %s", e)
        
        return collection

    async def store_search_results(
        self,
        telegram_id: int,
        username: Optional[str],
        first_name: Optional[str],
        last_name: Optional[str],
        from_station_code: str,
        to_station_code: str,
        from_station_title: str,
        to_station_title: str,
        candidate_threads: List[CandidateThread],
        ttl_minutes: Optional[int] = None
    ) -> bool:
        """Store user's search results with candidate threads.
        
        Args:
            telegram_id: User's Telegram ID
            username: User's username
            first_name: User's first name
            last_name: User's last name
            from_station_code: From station code
            to_station_code: To station code
            from_station_title: From station title
            to_station_title: To station title
            candidate_threads: List of candidate threads
            ttl_minutes: TTL in minutes (default: 60 minutes / 1 hour)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            collection = await self.get_search_results_collection()
            
            ttl = ttl_minutes or self.default_ttl_minutes
            now = datetime.utcnow()
            expires_at = now + timedelta(minutes=ttl)
            
            search_results = UserSearchResults(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                from_station_code=from_station_code,
                to_station_code=to_station_code,
                from_station_title=from_station_title,
                to_station_title=to_station_title,
                candidate_threads=candidate_threads,
                created_at=now,
                expires_at=expires_at
            )
            
            # Upsert: replace existing search results for this user
            await collection.replace_one(
                {"telegram_id": telegram_id},
                search_results.model_dump(),
                upsert=True
            )
            
            logger.info(
                "Stored search results for user %s with %d candidate threads (TTL: %d min)",
                telegram_id, len(candidate_threads), ttl
            )
            return True
            
        except Exception as e:
            logger.error("Failed to store search results for user %s: %s", telegram_id, e)
            return False

    async def find_matches(self, telegram_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """Find matches for a user's candidate threads.
        
        Args:
            telegram_id: User's Telegram ID
            
        Returns:
            Dict mapping thread_uid to list of matched users
        """
        try:
            collection = await self.get_search_results_collection()
            
            # Get current user's search results
            user_doc = await collection.find_one({"telegram_id": telegram_id})
            if not user_doc:
                logger.warning("No search results found for user %s", telegram_id)
                return {}
            
            user_threads = {ct["thread_uid"] for ct in user_doc.get("candidate_threads", [])}
            if not user_threads:
                logger.info("User %s has no candidate threads", telegram_id)
                return {}
            
            logger.info("Finding matches for user %s with %d candidate threads", 
                       telegram_id, len(user_threads))
            
            # Find all other users with overlapping thread UIDs
            matches: Dict[str, List[Dict[str, Any]]] = {}
            
            # Query for documents with matching thread UIDs
            cursor = collection.find({
                "candidate_threads.thread_uid": {"$in": list(user_threads)},
                "telegram_id": {"$ne": telegram_id}  # Exclude current user
            })
            
            async for other_doc in cursor:
                other_telegram_id = other_doc["telegram_id"]
                other_threads = other_doc.get("candidate_threads", [])
                
                # Find which threads match
                for thread in other_threads:
                    thread_uid = thread.get("thread_uid")
                    if thread_uid in user_threads:
                        user_info = {
                            "telegram_id": other_telegram_id,
                            "username": other_doc.get("username"),
                            "first_name": other_doc.get("first_name"),
                            "last_name": other_doc.get("last_name"),
                            "from_station_code": other_doc.get("from_station_code"),
                            "to_station_code": other_doc.get("to_station_code"),
                            "from_station_title": other_doc.get("from_station_title"),
                            "to_station_title": other_doc.get("to_station_title"),
                            "departure_time": thread.get("departure_time"),
                            "arrival_time": thread.get("arrival_time")
                        }
                        
                        if thread_uid not in matches:
                            matches[thread_uid] = []
                        matches[thread_uid].append(user_info)
            
            # Only return threads with at least one other user
            result = {uid: users for uid, users in matches.items() if len(users) >= 1}
            
            logger.info("Found %d matching threads for user %s", len(result), telegram_id)
            return result
            
        except Exception as e:
            logger.error("Failed to find matches for user %s: %s", telegram_id, e)
            return {}

    async def find_users_to_notify(
        self, 
        new_user_telegram_id: int,
        new_user_threads: List[str]
    ) -> List[Dict[str, Any]]:
        """Find existing users who should be notified about a new matching user.
        
        When a new user stores their search results, this method finds all existing
        users whose candidate threads overlap with the new user's threads.
        
        Args:
            new_user_telegram_id: The telegram ID of the new user who just searched
            new_user_threads: List of thread UIDs for the new user
            
        Returns:
            List of user info dicts for users who should be notified
        """
        try:
            if not new_user_threads:
                return []
            
            collection = await self.get_search_results_collection()
            
            # Get the new user's document to include in notifications
            new_user_doc = await collection.find_one({"telegram_id": new_user_telegram_id})
            if not new_user_doc:
                logger.warning("No document found for new user %s", new_user_telegram_id)
                return []
            
            # Find all users who have any of the same thread UIDs
            cursor = collection.find({
                "candidate_threads.thread_uid": {"$in": new_user_threads},
                "telegram_id": {"$ne": new_user_telegram_id}  # Exclude the new user
            })
            
            users_to_notify = []
            notified_telegram_ids = set()  # Avoid duplicate notifications
            
            async for other_doc in cursor:
                other_telegram_id = other_doc["telegram_id"]
                
                # Skip if already added
                if other_telegram_id in notified_telegram_ids:
                    continue
                
                # Check if this user has any overlapping threads
                other_threads = other_doc.get("candidate_threads", [])
                matching_thread_uids = [
                    thread.get("thread_uid") 
                    for thread in other_threads 
                    if thread.get("thread_uid") in new_user_threads
                ]
                
                if matching_thread_uids:
                    # Build user info with the new user's details
                    user_info = {
                        "telegram_id": other_telegram_id,
                        "matching_threads": matching_thread_uids,
                        "new_user_name": (
                            new_user_doc.get("first_name") or 
                            new_user_doc.get("username") or 
                            "Пользователь"
                        ),
                        "new_user_from_title": new_user_doc.get("from_station_title"),
                        "new_user_to_title": new_user_doc.get("to_station_title"),
                    }
                    users_to_notify.append(user_info)
                    notified_telegram_ids.add(other_telegram_id)
            
            logger.info(
                "Found %d existing users to notify about new user %s", 
                len(users_to_notify), new_user_telegram_id
            )
            return users_to_notify
            
        except Exception as e:
            logger.error(
                "Failed to find users to notify for new user %s: %s", 
                new_user_telegram_id, e
            )
            return []

    async def get_user_search_results(self, telegram_id: int) -> Optional[UserSearchResults]:
        """Get user's search results.
        
        Args:
            telegram_id: User's Telegram ID
            
        Returns:
            UserSearchResults if found, None otherwise
        """
        try:
            collection = await self.get_search_results_collection()
            doc = await collection.find_one({"telegram_id": telegram_id})
            
            if doc:
                return UserSearchResults(**doc)
            return None
            
        except Exception as e:
            logger.error("Failed to get search results for user %s: %s", telegram_id, e)
            return None

    async def clear_search_results(self, telegram_id: int) -> bool:
        """Clear user's search results (for cancel functionality).
        
        Args:
            telegram_id: User's Telegram ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            collection = await self.get_search_results_collection()
            result = await collection.delete_one({"telegram_id": telegram_id})
            
            if result.deleted_count > 0:
                logger.info("Cleared search results for user %s", telegram_id)
                return True
            else:
                logger.debug("No search results to clear for user %s", telegram_id)
                return False
                
        except Exception as e:
            logger.error("Failed to clear search results for user %s: %s", telegram_id, e)
            return False

    async def close(self):
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoDB thread matching service connection closed")


# Global service instance
_service_instance: Optional[ThreadMatchingService] = None


def get_thread_matching_service() -> ThreadMatchingService:
    """Get or create the global thread matching service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ThreadMatchingService()
        logger.debug("Created thread matching service instance")
    return _service_instance
