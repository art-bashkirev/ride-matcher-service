from pydantic import BaseModel

from .carrier import Carrier
from .common import TransportType, TransportSubtype, System, SegmentType, StationType


class Interval(BaseModel):
    density: str
    begin_time: str
    end_time: str


class Price(BaseModel):
    cents: int
    whole: int


class Place(BaseModel):
    currency: str
    price: Price
    name: str


class TicketsInfo(BaseModel):
    et_marker: bool
    places: list[Place]


class Thread(BaseModel):
    uid: str
    title: str
    interval: Interval
    number: str
    short_title: str
    thread_method_link: str
    carrier: Carrier
    transport: TransportType
    vehicle: str
    transport_subtype: TransportSubtype
    express_type: str | None


class SegmentPoint(BaseModel):
    code: str
    title: str
    station_type: StationType
    station_type_name: str
    popular_title: str
    short_title: str
    transport_type: TransportType
    type: SegmentType


class Segment(BaseModel):
    arrival: str
    from_: SegmentPoint  # ! OBJECT
    to: SegmentPoint  # ! OBJECT
    thread: Thread
    departure_platform: str | None
    departure: str
    stops: str
    departure_terminal: str | None
    has_transfers: bool
    tickets_info: object  # ! OBJECT
    duration: int
    arrival_terminal: str | None
    start_date: str
    arrival_platform: str | None


class SearchPoint(BaseModel):
    code: str
    type: SegmentType
    popular_title: str
    short_title: str
    title: str


class SearchSegment(BaseModel):
    arrival: str
    thread: Thread


class Pagination(BaseModel):
    total: int
    limit: int
    offset: int


class SearchClarification(BaseModel):
    date: str
    to: SearchPoint
    from_: SearchPoint


class SearchRequest(BaseModel):
    from_: str
    to: str
    date: str
    transport_types: TransportType | None
    system: System | None
    offset: int = 0
    limit: int = 100
    add_days_mask: bool = False
    result_timezone: str
    transfers: bool = False


class SearchResponse(BaseModel):
    pagination: Pagination
    interval_segments: list
    segments: list
    search: SearchClarification
