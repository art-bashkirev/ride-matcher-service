"""MongoDB service for stations management."""

import re
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase

from config.log_setup import get_logger
from config.settings import get_config
from services.yandex_schedules.models.stations_list import StationsListResponse, Country, Region, Settlement, Station
from .models import FlatStation, StationSearchResult

logger = get_logger(__name__)

# Constants
PARSE_ERROR_MESSAGE = "Failed to parse station from MongoDB: %s"


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
    
    def _is_valid_coordinate(self, coord) -> bool:
        """Check if coordinate is valid for conversion to float."""
        if not coord:
            return False
        coord_str = str(coord).replace('.', '').replace('-', '')
        return coord_str.isdigit()
    
    def _create_search_text(self, station: Station, settlement: Settlement, region: Region, country: Country) -> str:
        """Create search text from station and location components."""
        search_parts = [station.title, settlement.title, region.title, country.title]
        if station.direction:
            search_parts.append(station.direction)
        return " ".join(filter(None, search_parts))
    
    def _create_flat_station(self, station: Station, settlement: Settlement, region: Region, country: Country) -> FlatStation:
        """Create a FlatStation from hierarchical components."""
        search_text = self._create_search_text(station, settlement, region, country)
        
        return FlatStation(
            title=station.title.strip(),
            codes=station.codes,
            station_type=station.station_type,
            transport_type=station.transport_type,
            longitude=float(station.longitude) if self._is_valid_coordinate(station.longitude) else None,
            latitude=float(station.latitude) if self._is_valid_coordinate(station.latitude) else None,
            direction=station.direction,
            settlement_title=settlement.title,
            settlement_codes=settlement.codes,
            region_title=region.title,
            region_codes=region.codes,
            country_title=country.title,
            country_codes=country.codes,
            search_text=search_text
        )
    
    def _is_station_valid(self, station: Station) -> bool:
        """Check if station has valid title."""
        return bool(station.title and station.title.strip())
    
    def _process_station(self, station: Station, settlement: Settlement, region: Region, country: Country, flat_stations: list, seen_codes: set) -> None:
        """Process a single station and add to flat_stations if valid and not duplicate."""
        if not self._is_station_valid(station):
            logger.warning(
                "Skipping station with empty title: %s", 
                station.codes.yandex_code if station.codes else "unknown"
            )
            return
        
        # Check for duplicate codes
        yandex_code = station.codes.yandex_code
        if yandex_code and yandex_code in seen_codes:
            logger.debug("Skipping duplicate station code: %s", yandex_code)
            return
        
        if yandex_code:
            seen_codes.add(yandex_code)
        
        flat_station = self._create_flat_station(station, settlement, region, country)
        flat_stations.append(flat_station.model_dump())
    
    async def flatten_and_store_stations(self, stations_response: StationsListResponse) -> int:
        """Flatten the hierarchical stations list and store in MongoDB.
        
        Args:
            stations_response: The hierarchical stations response from Yandex API
            
        Returns:
            Number of stations stored
        """
        collection = await self._get_collection()
        flat_stations = []
        seen_codes = set()  # Track seen station codes for deduplication
        
        # Flatten the hierarchy
        for country in stations_response.countries:
            for region in country.regions:
                for settlement in region.settlements:
                    for station in settlement.stations:
                        self._process_station(station, settlement, region, country, flat_stations, seen_codes)
        
        if not flat_stations:
            logger.warning("No valid stations to store")
            return 0
        
        # Clear existing data and insert new
        await collection.delete_many({})
        result = await collection.insert_many(flat_stations)
        
        logger.info("Stored %d unique stations in MongoDB (deduplicated)", len(result.inserted_ids))
        return len(result.inserted_ids)
    
    def _parse_station_document(self, doc: dict) -> Optional[StationSearchResult]:
        """Parse a MongoDB document into a StationSearchResult."""
        try:
            # Extract score if present
            score = doc.pop("score", 0.0)
            station = FlatStation(**doc)
            return StationSearchResult(station=station, relevance_score=score)
        except Exception as e:
            logger.warning(PARSE_ERROR_MESSAGE, e)
            return None
    
    async def _perform_text_search(self, query: str, limit: int) -> List[StationSearchResult]:
        """Perform MongoDB text search."""
        collection = await self._get_collection()
        cursor = collection.find(
            {"$text": {"$search": query.strip()}},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(limit)
        
        results = []
        async for doc in cursor:
            result = self._parse_station_document(doc)
            if result:
                results.append(result)
        
        return results
    
    async def _perform_fuzzy_search(self, query: str, limit: int) -> List[StationSearchResult]:
        """Perform fuzzy search as fallback."""
        collection = await self._get_collection()
        pattern = re.compile(re.escape(query.strip()), re.IGNORECASE)
        cursor = collection.find({"title": pattern}).limit(limit)
        
        results = []
        async for doc in cursor:
            result = self._parse_station_document(doc)
            if result:
                # Override score for fuzzy matches
                result.relevance_score = 0.5
                results.append(result)
        
        return results
    
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
        
        # Try text search first
        results = await self._perform_text_search(query, limit)
        
        # If no results, try fuzzy matching
        if not results:
            results = await self._perform_fuzzy_search(query, limit)
        
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
                logger.warning(PARSE_ERROR_MESSAGE, e)
        
        return None
    
    async def get_stations_count(self) -> int:
        """Get total number of stations stored.
        
        Returns:
            Number of stations
        """
        collection = await self._get_collection()
        return await collection.count_documents({})
    
    async def ensure_stations_loaded(self) -> bool:
        """Ensure stations are loaded, fetch if not present.
        
        Returns:
            True if stations are available, False if fetch failed
        """
        stations_count = await self.get_stations_count()
        if stations_count > 0:
            logger.info("Stations already loaded: %d stations available", stations_count)
            return True
        
        logger.info("No stations found, attempting to fetch from Yandex API...")
        try:
            from services.yandex_schedules.cached_client import CachedYandexSchedules
            from services.yandex_schedules.models.stations_list import StationsListRequest
            
            async with CachedYandexSchedules() as client:
                stations_response = await client.get_stations_list(StationsListRequest())
            
            stored_count = await self.flatten_and_store_stations(stations_response)
            logger.info("Successfully auto-fetched and stored %d stations", stored_count)
            return stored_count > 0
            
        except Exception as e:
            logger.error("Failed to auto-fetch stations: %s", e)
            return False
    
    def close(self):
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