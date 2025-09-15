from pydantic import BaseModel

from .common import Interval, TransportType, TransportSubtype
from .carrier import Carrier

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