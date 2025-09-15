from enum import Enum
from pydantic import BaseModel


class Interval(BaseModel):
    density: str | None = None
    begin_time: str | None = None
    end_time: str | None = None





class SearchCodes(BaseModel):
    yandex_code: str | None
    esr_code: str | None


class Pagination(BaseModel):
    total: int
    limit: int
    offset: int | None = None


class CodingSystem(Enum):
    YANDEX = "yandex"
    IATA = "iata"
    SIRENA = "sirena"
    EXPRESS = "express"
    ESR = "esr"


class ShowSystems(Enum):
    YANDEX = "yandex"
    ESR = "esr"
    ALL = "all"


class ThreadFilter(Enum):
    DEPARTURE = "departure"
    ARRIVAL = "arrival"


class TransportSubtype(BaseModel):
    color: str
    code: str
    title: str


class TransportType(Enum):
    PLANE = "plane"
    TRAIN = "train"
    SUBURBAN = "suburban"
    BUS = "bus"
    WATER = "water"
    HELICOPTER = "helicopter"


class StationType(Enum):
    STATION = "station"
    PLATFORM = "platform"
    STOP = "stop"
    CHECKPOINT = "checkpoint"
    POST = "post"
    CROSSING = "crossing"
    OVERTAKING_POINT = "overtaking_point"
    TRAIN_STATION = "train_station"
    AIRPORT = "airport"
    BUS_STATION = "bus_station"
    BUS_STOP = "bus_stop"
    UNKNOWN = "unknown"
    PORT = "port"
    PORT_POINT = "port_point"
    WHARF = "wharf"
    RIVER_PORT = "river_port"
    MARINE_STATION = "marine_station"


class SegmentType(Enum):
    STATION = "station"
    SETTLEMENT = "settlement"
