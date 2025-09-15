from pydantic import BaseModel
from enum import Enum


class System(Enum):
    YANDEX = "yandex"
    IATA = "iata"
    SIRENA = "sirena"
    EXPRESS = "express"
    ESR = "esr"

class TransportType(Enum):
    PLANE = "plane"
    TRAIN = "train"
    SUBURBAN = "suburban"
    BUS = "bus"
    WATER = "water"
    HELICOPTER = "helicopter"


class StationType(Enum):
    STATION = "station"
    SETTLEMENT = "settlement"
