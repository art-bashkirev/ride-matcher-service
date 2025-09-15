from enum import EnumType

from pydantic import BaseModel
from enum import Enum

from .common import TransportType


class StationsListRequest(BaseModel):
    pass

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

class SearchCodes(BaseModel):
    yandex_code: str | None
    esr_code: str | None

class Station(BaseModel):
    direction: str | None
    codes: SearchCodes
    station_type: StationType
    title: str
    longitude: float
    latitude: float
    transport_type: TransportType

class Settlement(BaseModel):
    title: str
    codes: SearchCodes
    stations: list[Station]

class Region(BaseModel):
    settlements: list[Settlement]
    codes: SearchCodes
    title: str

class Countries(BaseModel):
    regions: list[Region]
    codes: SearchCodes
    title: str

class StationsListResponse(BaseModel):
    countries: Countries