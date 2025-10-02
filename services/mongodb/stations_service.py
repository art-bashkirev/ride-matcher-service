"""MongoDB service for stations data."""

import asyncio
from typing import List, Optional

from pydantic import BaseModel
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from config.log_setup import get_logger
from config.settings import get_config


COND_KEY = "$cond"


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


def _build_station_documents(response) -> list[dict]:
    documents: list[dict] = []
    for station_ctx in _iter_station_entries(response):
        document = _build_single_station_document(*station_ctx)
        if document:
            documents.append(document)
    return documents


def _iter_station_entries(response):
    for country in getattr(response, "countries", None) or []:
        country_title = getattr(country, "title", "") or ""
        yield from _iter_region_entries(country, country_title)


def _iter_region_entries(country, country_title: str):
    for region in getattr(country, "regions", None) or []:
        region_title = getattr(region, "title", "") or ""
        yield from _iter_settlement_entries(region, country_title, region_title)


def _iter_settlement_entries(region, country_title: str, region_title: str):
    for settlement in getattr(region, "settlements", None) or []:
        settlement_title = getattr(settlement, "title", "") or ""
        for station in getattr(settlement, "stations", None) or []:
            yield station, country_title, region_title, settlement_title


def _build_single_station_document(
    station, country_title: str, region_title: str, settlement_title: str
) -> dict | None:
    codes = getattr(station, "codes", None)
    if not codes:
        return None

    primary_code = getattr(codes, "yandex_code", None) or getattr(
        codes, "esr_code", None
    )
    if not primary_code:
        return None

    all_codes: list[str] = []
    if getattr(codes, "yandex_code", None):
        all_codes.append(codes.yandex_code)
    if getattr(codes, "esr_code", None):
        all_codes.append(codes.esr_code)

    station_type = getattr(station, "station_type", None)
    transport_type = getattr(station, "transport_type", None)

    doc = StationDocument(
        code=primary_code,
        title=getattr(station, "title", "") or "",
        station_type=station_type.value if station_type else None,
        transport_type=transport_type.value if transport_type else "",
        direction=getattr(station, "direction", None),
        longitude=(
            float(station.longitude) if getattr(station, "longitude", None) else None
        ),
        latitude=(
            float(station.latitude) if getattr(station, "latitude", None) else None
        ),
        settlement_title=settlement_title,
        region_title=region_title,
        country_title=country_title,
        all_codes=all_codes,
    )
    return doc.model_dump()


class StationsService:
    """Service for MongoDB operations on stations."""

    def __init__(self):
        self.config = get_config()
        self._client: Optional[AsyncMongoClient] = None
        self._db: Optional[AsyncDatabase] = None
        self._logger = get_logger(__name__)

    async def _get_client(self) -> AsyncMongoClient:
        """Get MongoDB client."""
        if self._client is None:
            uri = self._build_connection_uri()
            self._client = AsyncMongoClient(uri)
            self._logger.info(
                "MongoDB client created for stations service using %s",
                self._sanitize_uri(uri),
            )
            await asyncio.sleep(0)
        return self._client

    def _build_connection_uri(self) -> str:
        if self.config.mongodb_url:
            return self.config.mongodb_url

        host = self.config.mongodb_host
        user = self.config.mongodb_user
        password = self.config.mongodb_password

        if not host:
            raise ValueError(
                "MongoDB configuration incomplete: provide MONGODB_URL or host credentials"
            )

        if host.startswith("mongodb://") or host.startswith("mongodb+srv://"):
            base = host
        else:
            base = f"mongodb://{host}"

        if user and password and "@" not in base.split("://", 1)[1]:
            scheme, remainder = base.split("://", 1)
            return f"{scheme}://{user}:{password}@{remainder}"

        return base

    @staticmethod
    def _sanitize_uri(uri: str) -> str:
        if "@" in uri:
            scheme, remainder = uri.split("://", 1)
            if "@" in remainder:
                host_part = remainder.split("@", 1)[1]
                return f"{scheme}://***:***@{host_part}"
        return uri

    async def _get_db(self) -> AsyncDatabase:
        """Get database."""
        if self._db is None:
            client = await self._get_client()
            self._db = client[self.config.mongodb_database or "ride_matcher"]
        return self._db

    async def get_stations_collection(self):
        """Get stations collection."""
        db = await self._get_db()
        collection_name = self.config.mongodb_stations_collection or "stations"
        return db[collection_name]

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
                        COND_KEY: {
                            "if": {
                                "$eq": [
                                    {"$toLower": {"$trim": {"input": "$title"}}},
                                    norm_query,
                                ]
                            },
                            "then": 5,  # Exact title match (case-insensitive, trimmed)
                            "else": {
                                COND_KEY: {
                                    "if": {"$in": [query, "$all_codes"]},
                                    "then": 4,  # Exact code match
                                    "else": {
                                        COND_KEY: {
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

        documents = _build_station_documents(response)
        documents = _build_station_documents(response)

        if documents:
            await collection.insert_many(documents)
            # Create indexes
            await collection.create_index("code", unique=True)
            await collection.create_index("title")
            await collection.create_index("all_codes")
            self._logger.info("Inserted %d stations into MongoDB", len(documents))

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
