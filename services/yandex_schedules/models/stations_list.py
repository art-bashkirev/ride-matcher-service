from pydantic import BaseModel

from .common import TransportType


class StationsListRequest(BaseModel):
    pass

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
