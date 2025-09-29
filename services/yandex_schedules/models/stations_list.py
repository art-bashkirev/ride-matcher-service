from pydantic import BaseModel, field_validator

from .common import TransportType, SearchCodes, StationType


class StationsListRequest(BaseModel):
    pass


class Station(BaseModel):
    direction: str | None = None
    codes: SearchCodes | None = None
    station_type: StationType | None = None
    title: str | None = None
    longitude: float | str | None = None
    latitude: float | str | None = None
    transport_type: TransportType | None = None

    @field_validator("station_type", mode="before")
    def empty_str_to_unknown(cls, v):
        if v == "":
            return "unknown"
        return v


class Settlement(BaseModel):
    title: str | None = None
    codes: SearchCodes | None = None
    stations: list[Station] | None = None


class Region(BaseModel):
    settlements: list[Settlement] | None = None
    codes: SearchCodes | None = None
    title: str | None = None


class Country(BaseModel):
    regions: list[Region] | None = None
    codes: SearchCodes | None = None
    title: str | None = None


class StationsListResponse(BaseModel):
    countries: list[Country] | None = None
