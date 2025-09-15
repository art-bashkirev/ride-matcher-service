from pydantic import BaseModel
from .common import System

class CarrierCodes(BaseModel):
    icao: str | None
    sirena: str | None
    iata: str | None

class Carrier(BaseModel):
    code: int
    contacts: str
    url: str
    title: str
    phone: str
    codes: CarrierCodes
    address: str
    logo: str
    email: str
    offices: list

class CarrierRequest(BaseModel):
    code: str
    system: System | None = None

class CarrierResponse(BaseModel):
    pass
