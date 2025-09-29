from pydantic import BaseModel

from .common import CodingSystem


class CarrierCodes(BaseModel):
    icao: str | None = None
    sirena: str | None = None
    iata: str | None = None


class Carrier(BaseModel):
    code: int | None = None
    contacts: str | None = None
    url: str | None = None
    title: str | None = None
    phone: str | None = None
    codes: CarrierCodes | None = None
    address: str | None = None
    logo: str | None = None
    email: str | None = None
    offices: list | None = None


class CarrierRequest(BaseModel):
    code: str | None = None
    system: CodingSystem | None = None


class CarrierResponse(BaseModel):
    pass
