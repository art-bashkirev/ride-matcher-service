from pydantic import BaseModel

from .common import ThreadFilter, CodingSystem, Pagination, StationType, SearchCodes, TransportType, ShowSystems
from .thread import Thread


class ScheduleRequest(BaseModel):
    station: str | None = None
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
    except_days: str | None = None
    arrival: str | None = None
    thread: Thread | None = None
    is_fuzzy: bool | None = None
    days: str | None = None
    stops: str | None = None
    departure: str | None = None
    terminal: str | None = None
    platform: str | None = None


class ScheduleDirection(BaseModel):
    code: str | None = None
    title: str | None = None


class Station(BaseModel):
    code: str | None = None
    station_type: StationType | None = None
    station_type_name: str | None = None
    title: str | None = None
    popular_title: str | None = None
    short_title: str | None = None
    codes: SearchCodes | None = None
    transport_type: TransportType | None = None
    type: str | None = None


class ScheduleResponse(BaseModel):
    date: str | None = None
    pagination: Pagination | None = None
    station: Station | None = None
    schedule: list[Schedule] | None = None
    schedule_direction: ScheduleDirection | None = None
    directions: list[ScheduleDirection] | None = None
