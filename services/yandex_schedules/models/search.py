from pydantic import BaseModel, Field

from .common import TransportType, Pagination, CodingSystem, SegmentType, StationType
from .thread import Thread




class Price(BaseModel):
    cents: int | None = None
    whole: int | None = None


class Place(BaseModel):
    currency: str | None = None
    price: Price | None = None
    name: str | None = None


class TicketsInfo(BaseModel):
    et_marker: bool | None = None
    places: list[Place] | None = None




class SegmentPoint(BaseModel):
    code: str | None = None
    title: str | None = None
    station_type: StationType | None = None
    station_type_name: str | None = None
    popular_title: str | None = None
    short_title: str | None = None
    transport_type: TransportType | None = None
    type: SegmentType | None = None


class Segment(BaseModel):
    arrival: str | None = None
    from_: SegmentPoint | None = Field(default=None, validation_alias='from', serialization_alias='from')
    to: SegmentPoint | None = None
    thread: Thread | None = None
    departure_platform: str | None = None
    departure: str | None = None
    stops: str | None = None
    departure_terminal: str | None = None
    has_transfers: bool | None = None
    tickets_info: TicketsInfo | None = None
    duration: int | None = None
    arrival_terminal: str | None = None
    start_date: str | None = None
    arrival_platform: str | None = None


class SearchPoint(BaseModel):
    code: str | None = None
    type: SegmentType | None = None
    popular_title: str | None = None
    short_title: str | None = None
    title: str | None = None


class SearchSegment(BaseModel):
    arrival: str | None = None
    thread: Thread | None = None


class SearchClarification(BaseModel):
    date: str | None = None
    to: SearchPoint | None = None
    from_: SearchPoint | None = Field(default=None, validation_alias='from', serialization_alias='from')


class SearchRequest(BaseModel):
    from_: str = Field(serialization_alias='from')
    to: str
    date: str | None = None
    transport_types: TransportType | None = None
    system: CodingSystem | None = None
    offset: int = 0
    limit: int = 100
    add_days_mask: bool = False
    result_timezone: str | None = None
    transfers: bool = False


class SearchResponse(BaseModel):
    pagination: Pagination | None = None
    interval_segments: list[Segment] | None = None
    segments: list[Segment] | None = None
    search: SearchClarification | None = None
