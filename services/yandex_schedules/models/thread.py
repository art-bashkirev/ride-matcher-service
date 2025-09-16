from pydantic import BaseModel

from .common import Interval, TransportType, TransportSubtype, ShowSystems
from .carrier import Carrier

# Thread UID may change over time.
# Therefore it is needed to fetch the latest thread UID from Search or Schedule responses
class ThreadCodes(BaseModel):
    express: str | None = None
    yandex: str | None = None
    esr: str | None = None

class Station(BaseModel):
    codes: ThreadCodes
    title: str | None
    station_type: object  # TODO
    station_type_name: str | None
    popular_title: str | None
    short_title: str | None
    code: str | None
    type: str | None

class Stop(BaseModel):
    arrival: str | None
    departure: str | None
    duration: float | None
    stop_time: float | None
    station: Station | None
    terminal: str | None
    platform: str | None

class Thread(BaseModel):
    uid: str | None = None
    title: str | None = None
    interval: Interval | None = None
    number: str | None = None
    short_title: str | None = None
    thread_method_link: str | None = None
    carrier: Carrier | None = None
    transport_type: TransportType | None = None
    vehicle: str | None = None
    transport_subtype: TransportSubtype | None = None
    express_type: str | None = None

class ThreadRequest(BaseModel):
    uid: str
    from_: str | None = None
    to: str | None = None
    date: str | None = None
    show_systems: ShowSystems | None = None

class ThreadResponse(BaseModel):
    except_days: str | None = None
    arrival_date: str | None = None
    from_: str | None = None
    uid: str | None = None
    to: str | None = None
    title: str | None = None
    interval: Interval | None = None
    departure_date: str | None = None
    start_time: str | None = None
    number: str | None = None
    short_title: str | None = None
    days: str | None = None
    carrier: Carrier | None = None
    transport_type: TransportType | None = None
    stops: list[object] #! TODO
    vehicle: str | None = None
    start_date: str | None = None
    transport_subtype: TransportSubtype | None = None
    express_type: str | None = None