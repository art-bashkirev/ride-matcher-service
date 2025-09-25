"""MongoDB service for stations management."""

import re
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase

from config.log_setup import get_logger
from config.settings import get_config
from services.yandex_schedules.models.stations_list import StationsListResponse, Country, Region, Settlement, Station
from .models import FlatStation, StationSearchResult

logger = get_logger(__name__)


class StationsService:
    """MongoDB service for stations storage and search."""
    
    def __init__(self):
        """Initialize MongoDB connection."""
        self.config = get_config()
        self._client: Optional[AsyncIOMotorClient] = None
        self._db: Optional[AsyncIOMotorDatabase] = None
        self._collection: Optional[AsyncIOMotorCollection] = None
    
    async def _get_collection(self) -> AsyncIOMotorCollection:
        """Get or create MongoDB collection."""
        if self._collection is None:
            self._client = AsyncIOMotorClient(self.config.mongodb_url)
            self._db = self._client[self.config.mongodb_database]
            self._collection = self._db[self.config.mongodb_stations_collection]
            
            # Create text index for search
            await self._collection.create_index([("search_text", "text")])
            # Create index on yandex_code for fast lookups
            await self._collection.create_index("codes.yandex_code", unique=True)
            
            logger.info("MongoDB connection established for stations")
        
        return self._collection
    
    async def flatten_and_store_stations(self, stations_response: StationsListResponse) -> int:
        """Flatten the hierarchical stations list and store in MongoDB.
        
        Args:
            stations_response: The hierarchical stations response from Yandex API
            
        Returns:
            Number of stations stored
        """
        collection = await self._get_collection()
        flat_stations = []
        
        # Flatten the hierarchy
        for country in stations_response.countries:
            for region in country.regions:
                for settlement in region.settlements:
                    for station in settlement.stations:
                        # Validate station title (skip empty titles)
                        if not station.title or station.title.strip() == "":
                            logger.warning(
                                "Skipping station with empty title: %s", 
                                station.codes.yandex_code if station.codes else "unknown"
                            )
                            continue
                        
                        # Create search text combining all relevant fields
                        search_parts = [
                            station.title,
                            settlement.title,
                            region.title,
                            country.title
                        ]
                        # Add direction if available
                        if station.direction:
                            search_parts.append(station.direction)
                        
                        search_text = " ".join(filter(None, search_parts))
                        
                        flat_station = FlatStation(
                            title=station.title.strip(),
                            codes=station.codes,
                            station_type=station.station_type,
                            transport_type=station.transport_type,
                            longitude=float(station.longitude) if station.longitude and str(station.longitude).replace('.', '').replace('-', '').isdigit() else None,
                            latitude=float(station.latitude) if station.latitude and str(station.latitude).replace('.', '').replace('-', '').isdigit() else None,
                            direction=station.direction,
                            settlement_title=settlement.title,
                            settlement_codes=settlement.codes,
                            region_title=region.title,
                            region_codes=region.codes,
                            country_title=country.title,
                            country_codes=country.codes,
                            search_text=search_text
                        )
                        flat_stations.append(flat_station.model_dump())
        
        if not flat_stations:
            logger.warning("No valid stations to store")
            return 0
        
        # Clear existing data and insert new
        await collection.delete_many({})
        result = await collection.insert_many(flat_stations)
        
        logger.info("Stored %d stations in MongoDB", len(result.inserted_ids))
        return len(result.inserted_ids)
    
    async def search_stations(self, query: str, limit: int = 10) -> List[StationSearchResult]:
        """Search stations by title and location.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of station search results with relevance scores
        """
        if not query or not query.strip():
            return []
        
        collection = await self._get_collection()
        
        # Use MongoDB text search
        cursor = collection.find(
            {"$text": {"$search": query.strip()}},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(limit)
        
        results = []
        async for doc in cursor:
            # Extract score and remove from doc
            score = doc.pop("score", 0.0)
            
            try:
                station = FlatStation(**doc)
                results.append(StationSearchResult(
                    station=station,
                    relevance_score=score
                ))
            except Exception as e:
                logger.warning("Failed to parse station from MongoDB: %s", e)
                continue
        
        # If no text search results, try fuzzy matching on title
        if not results:
            pattern = re.compile(re.escape(query.strip()), re.IGNORECASE)
            cursor = collection.find(
                {"title": pattern}
            ).limit(limit)
            
            async for doc in cursor:
                try:
                    station = FlatStation(**doc)
                    results.append(StationSearchResult(
                        station=station,
                        relevance_score=0.5  # Lower score for fuzzy matches
                    ))
                except Exception as e:
                    logger.warning("Failed to parse station from MongoDB: %s", e)
                    continue
        
        logger.info("Found %d stations for query: %s", len(results), query)
        return results
    
    async def get_station_by_code(self, yandex_code: str) -> Optional[FlatStation]:
        """Get station by Yandex code.
        
        Args:
            yandex_code: Station's Yandex code
            
        Returns:
            Station if found, None otherwise
        """
        collection = await self._get_collection()
        
        doc = await collection.find_one({"codes.yandex_code": yandex_code})
        if doc:
            try:
                return FlatStation(**doc)
            except Exception as e:
                logger.warning("Failed to parse station from MongoDB: %s", e)
        
        return None
    
    async def get_stations_count(self) -> int:
        """Get total number of stations stored.
        
        Returns:
            Number of stations
        """
        collection = await self._get_collection()
        return await collection.count_documents({})
    
    async def close(self):
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            logger.info("MongoDB connection closed")


# Global service instance
_stations_service: Optional[StationsService] = None


def get_stations_service() -> StationsService:
    """Get or create the global stations service instance."""
    global _stations_service
    if _stations_service is None:
        _stations_service = StationsService()
    return _stations_service