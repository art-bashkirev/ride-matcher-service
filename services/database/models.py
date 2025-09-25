"""Database models for MongoDB storage."""

from typing import Optional
from pydantic import BaseModel, Field

from services.yandex_schedules.models.common import TransportType, SearchCodes, StationType


class FlatStation(BaseModel):
    """Flattened station model for MongoDB storage and search."""
    
    # Core station data
    title: str = Field(..., description="Station title")
    codes: SearchCodes = Field(..., description="Station codes (yandex_code required)")
    station_type: Optional[StationType] = Field(None, description="Station type")
    transport_type: TransportType = Field(..., description="Transport type")
    
    # Location data
    longitude: Optional[float] = Field(None, description="Station longitude")
    latitude: Optional[float] = Field(None, description="Station latitude")
    direction: Optional[str] = Field(None, description="Station direction")
    
    # Hierarchy context for search
    settlement_title: str = Field(..., description="Settlement title")
    settlement_codes: SearchCodes = Field(..., description="Settlement codes")
    region_title: str = Field(..., description="Region title")
    region_codes: SearchCodes = Field(..., description="Region codes")
    country_title: str = Field(..., description="Country title")
    country_codes: SearchCodes = Field(..., description="Country codes")
    
    # Search helpers
    search_text: str = Field(..., description="Combined search text for full-text search")
    
    class Config:
        """MongoDB configuration."""
        arbitrary_types_allowed = True


class StationSearchResult(BaseModel):
    """Station search result with relevance."""
    
    station: FlatStation
    relevance_score: float = Field(default=0.0, description="Search relevance score")