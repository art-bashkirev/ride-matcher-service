import json
import os
from typing import List, Union

import aiohttp

from .models.carrier import Carrier, CarrierRequest
from .models.copyright import CopyrightRequest, CopyrightResponse
from .models.search import SearchRequest, SearchResponse
from .models.schedule import ScheduleRequest, ScheduleResponse
from .models.thread import ThreadRequest, ThreadResponse


class YandexSchedules:
    BASE_URL = "https://api.rasp.yandex.net/v3.0/"

    def __init__(self, api_key: str | None = None, timeout: int = 10):
        self.api_key = api_key or os.getenv("YANDEX_SCHEDULES_API_KEY")
        if not self.api_key:
            raise RuntimeError("YANDEX_SCHEDULES_API_KEY not provided")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession(base_url=self.BASE_URL, timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

    async def _get(self, endpoint: str, **params) -> dict:
        if not self._session:
            raise RuntimeError("Client session not initialized. Use 'async with YandexSchedules()'.")
        params["apikey"] = self.api_key
        # Convert all params to strings for yarl compatibility
        params = {k: str(v) for k, v in params.items()}
        # params.setdefault("format", "json")
        async with self._session.get(endpoint, params=params) as resp:
            resp.raise_for_status()

            # Check the response headers to confirm the issue
            print(f"Status: {resp.status}")
            print(f"Content-Type: {resp.headers.get('Content-Type')}")

            try:
                # Tell aiohttp to ignore the Content-Type header and parse the body as JSON.
                data = await resp.json(content_type=None)
                return data
            except aiohttp.ContentTypeError as e:
                # This block will now likely not be triggered
                print(f"Failed to decode JSON: {e}")
                raise

    async def get_copyright(self, req: CopyrightRequest | None = None) -> CopyrightResponse:
        data = await self._get("copyright")
        return CopyrightResponse(**data)

    async def get_carrier(self, req: CarrierRequest) -> Union[Carrier, List[Carrier]]:
        # The API's endpoint for a single carrier is "carrier".
        # You need to pass the parameters from the request object.
        params = req.model_dump(mode='json', exclude_none=True, by_alias=True)  # Converts the Pydantic model to a dictionary.
        data = await self._get("carrier", **params)

        # The API returns a dictionary with keys 'carrier' and 'carriers'.
        # We need to check which one exists to decide the return type.
        if "carrier" in data:
            return Carrier(**data["carrier"])
        elif "carriers" in data:
            return [Carrier(**carrier_data) for carrier_data in data["carriers"]]
        else:
            raise ValueError("Unexpected response format from Yandex Schedules API.")

    async def get_search_results(self, req: SearchRequest) -> SearchResponse:
        params = req.model_dump(mode='json', exclude_none=True, by_alias=True)
        data = await self._get("search", **params)

        return SearchResponse(**data)

    async def get_schedule(self, req: ScheduleRequest) -> ScheduleResponse:
        params = req.model_dump(mode='json', exclude_none=True, by_alias=True)
        data = await self._get("schedule", **params)
        return ScheduleResponse(**data)

    async def get_thread(self, req: ThreadRequest) -> ThreadResponse:
        params = req.model_dump(mode='json', exclude_none=True, by_alias=True)
        data = await self._get("thread", **params)
        return ThreadResponse(**data)

    # async def get_stations_list(self, req: StationsListRequest | None = None) -> StationsListResponse:
    #     """
    #     Retrieves the complete list of stations.
    #
    #     This endpoint returns a large dataset and is not intended for frequent use.
    #     """
    #     endpoint = "stations_list"
    #     data = await self._get(endpoint)
    #     return StationsListResponse(**data)
