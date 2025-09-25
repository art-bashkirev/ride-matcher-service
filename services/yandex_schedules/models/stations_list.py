from pydantic import BaseModel, field_validator

from .common import TransportType, SearchCodes, StationType


class StationsListRequest(BaseModel):
    pass


class Station(BaseModel):
    direction: str | None = None
    codes: SearchCodes
    station_type: StationType | None
    title: str
    longitude: float | str | None = None
    latitude: float | str | None = None
    transport_type: TransportType

    @field_validator("station_type", mode="before")
    def empty_str_to_unknown(cls, v):
        if v == "":
            return "unknown"
        return v


class Settlement(BaseModel):
    title: str
    codes: SearchCodes
    stations: list[Station]


class Region(BaseModel):
    settlements: list[Settlement]
    codes: SearchCodes
    title: str


class Country(BaseModel):
    regions: list[Region]
    codes: SearchCodes
    title: str


class StationsListResponse(BaseModel):
    countries: list[Country]
