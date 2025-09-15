class SearchStation(BaseModel):
    code: str
    type: StationType
    popular_title: str
    short_title: str
    title: str


class Pagination(BaseModel):
    total: int
    limit: int
    offset: int


class Search(BaseModel):
    date: str
    to: SearchStation
    from_: SearchStation


class SearchRequest(BaseModel):
    from_: str
    to: str
    date: str
    transport_types: TransportTypes | None
    system: System | None
    offset: int = 0
    limit: int = 100
    add_days_mask: bool = False
    result_timezone: str
    transfers: bool = False


class SearchResponse(BaseModel):
    pagination: Pagination
    interval_segments: list
    segments: list
    search: Search
