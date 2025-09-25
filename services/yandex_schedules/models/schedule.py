from pydantic import BaseModel

from .common import ThreadFilter, CodingSystem, Pagination, StationType, SearchCodes, TransportType, ShowSystems
from .thread import Thread


class ScheduleRequest(BaseModel):
    station: str
    date: str | None = None
    transport_types: TransportType | None = None
    direction: str | None = None
    event: ThreadFilter | None = None
    system: CodingSystem | None = None
    show_systems: ShowSystems | None = None
    result_timezone: str | None = None
    # DOES SUPPORT 'limit'??? YES, but not documented
    limit: int | None = None
    offset: int | None = 0


class Schedule(BaseModel):
    except_days: str | None
    arrival: str | None = None
    thread: Thread
    is_fuzzy: bool
    days: str
    stops: str
    departure: str
    terminal: str | None
    platform: str | None


class ScheduleDirection(BaseModel):
    code: str
    title: str


class Station(BaseModel):
    code: str
    station_type: StationType
    station_type_name: str
    title: str
    popular_title: str | None = None
    short_title: str | None = None
    codes: SearchCodes | None = None
    transport_type: TransportType
    type: str


class ScheduleResponse(BaseModel):
    date: str | None = None
    pagination: Pagination
    station: Station
    schedule: list[Schedule]
    schedule_direction: ScheduleDirection | None = None
    directions: list[ScheduleDirection] | None = None
