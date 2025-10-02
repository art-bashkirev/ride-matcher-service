"""MongoDB service for stations data."""

import asyncio
from typing import List, Optional

from pydantic import BaseModel
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from config.settings import get_config


class StationDocument(BaseModel):
    """Station document for MongoDB."""

    code: str  # Primary code from codes.yandex_code or similar
    title: str
    station_type: Optional[str]
    transport_type: str
    direction: Optional[str]
    longitude: Optional[float]
    latitude: Optional[float]
    settlement_title: str
    region_title: str
    country_title: str
    all_codes: List[str]  # All codes for searching


class StationsService:
    """Service for MongoDB operations on stations."""

    def __init__(self):
        self.config = get_config()
        self._client: Optional[AsyncMongoClient] = None
        self._db: Optional[AsyncDatabase] = None

    async def _get_client(self) -> AsyncMongoClient:
        """Get MongoDB client."""
        if self._client is None:
            if not all(
                [
                    self.config.mongodb_host,
                    self.config.mongodb_user,
                    self.config.mongodb_password,
                ]
            ):
                raise ValueError("MongoDB configuration incomplete")
            uri = f"mongodb+srv://{self.config.mongodb_user}:{self.config.mongodb_password}@{self.config.mongodb_host}/?retryWrites=true&w=majority"
            self._client = AsyncMongoClient(uri)
        return self._client

    async def _get_db(self) -> AsyncDatabase:
        """Get database."""
        if self._db is None:
            client = await self._get_client()
            self._db = client["ride_matcher"]
        return self._db

    async def get_stations_collection(self):
        """Get stations collection."""
        db = await self._get_db()
        return db["stations"]

    async def search_stations(
        self, query: str, limit: int = 10
    ) -> List[StationDocument]:
        """Search stations by title or code."""
        collection = await self.get_stations_collection()

        # Use aggregation pipeline to score and sort results
        # Normalize query for exact title match (case-insensitive, trimmed)
        norm_query = query.strip().lower()
        pipeline = [
            {
                "$match": {
                    "$and": [
                        {
                            "$or": [
                                {"title": {"$regex": query, "$options": "i"}},
                                {"all_codes": {"$in": [query]}},
                            ]
                        },
                        {"direction": {"$ne": None}},
                        {"direction": {"$ne": ""}},
                        {"region_title": {"$ne": None}},
                        {"region_title": {"$ne": ""}},
                    ]
                }
            },
            {
                "$addFields": {
                    "score": {
                        "$cond": {
                            "if": {
                                "$eq": [
                                    {"$toLower": {"$trim": {"input": "$title"}}},
                                    norm_query,
                                ]
                            },
                            "then": 5,  # Exact title match (case-insensitive, trimmed)
                            "else": {
                                "$cond": {
                                    "if": {"$in": [query, "$all_codes"]},
                                    "then": 4,  # Exact code match
                                    "else": {
                                        "$cond": {
                                            "if": {
                                                "$regexMatch": {
                                                    "input": "$title",
                                                    "regex": query,
                                                    "options": "i",
                                                }
                                            },
                                            "then": 2,  # Partial title match
                                            "else": 1,  # Other
                                        }
                                    },
                                }
                            },
                        }
                    }
                }
            },
            {"$sort": {"score": -1, "title": 1}},
            {"$limit": limit},
        ]
        cursor = await collection.aggregate(pipeline)
        results = await cursor.to_list(length=limit)
        return [StationDocument(**doc) for doc in results]

    async def get_station_by_code(self, code: str) -> Optional[StationDocument]:
        """Get station by code."""
        collection = await self.get_stations_collection()
        doc = await collection.find_one({"code": code})
        return StationDocument(**doc) if doc else None

    async def populate_stations(self, stations_data):
        """Populate MongoDB with stations from Yandex API response."""
        from services.yandex_schedules.models.stations_list import StationsListResponse

        response = StationsListResponse(**stations_data)
        collection = await self.get_stations_collection()

        # Clear existing data
        await collection.drop()

        documents = []
        for country in response.countries:
            for region in country.regions:
                for settlement in region.settlements:
                    for station in settlement.stations:
                        # Use yandex_code as primary code, fallback to esr_code
                        primary_code = (
                            station.codes.yandex_code or station.codes.esr_code
                        )
                        if not primary_code:
                            continue  # Skip stations without codes

                        all_codes = []
                        if station.codes.yandex_code:
                            all_codes.append(station.codes.yandex_code)
                        if station.codes.esr_code:
                            all_codes.append(station.codes.esr_code)

                        doc = StationDocument(
                            code=primary_code,
                            title=station.title,
                            station_type=(
                                station.station_type.value
                                if station.station_type
                                else None
                            ),
                            transport_type=station.transport_type.value,
                            direction=station.direction,
                            longitude=(
                                float(station.longitude) if station.longitude else None
                            ),
                            latitude=(
                                float(station.latitude) if station.latitude else None
                            ),
                            settlement_title=settlement.title,
                            region_title=region.title,
                            country_title=country.title,
                            all_codes=all_codes,
                        )
                        documents.append(doc.model_dump())

        if documents:
            await collection.insert_many(documents)
            # Create indexes
            await collection.create_index("code", unique=True)
            await collection.create_index("title")
            await collection.create_index("all_codes")
            print(f"Inserted {len(documents)} stations into MongoDB")

    async def close(self):
        """Close MongoDB connection."""
        if self._client:
            await self._client.close()


# Global instance
_stations_service: Optional[StationsService] = None


def get_stations_service() -> StationsService:
    """Get global stations service instance."""
    global _stations_service
    if _stations_service is None:
        _stations_service = StationsService()
    return _stations_service
