"""Cached client wrapper for Yandex Schedules API."""

from config.log_setup import get_logger
from services.cache.redis_cache import get_cache
from .client import YandexSchedules
from .models.schedule import ScheduleRequest, ScheduleResponse
from .models.search import SearchRequest, SearchResponse

logger = get_logger(__name__)


class CachedYandexSchedules:
    """Cached wrapper for YandexSchedules client."""

    def __init__(self, api_key: str | None = None, timeout: int = 10):
        """Initialize with YandexSchedules client and cache."""
        self.client = YandexSchedules(api_key=api_key, timeout=timeout)
        self.cache = get_cache()

    async def start(self):
        """Start the underlying client."""
        await self.client.start()

    async def close(self):
        """Close the underlying client and cache."""
        await self.client.close()
        self.cache.close()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def get_search_results(self, req: SearchRequest) -> tuple[SearchResponse, bool]:
        """Get search results with caching.
        
        Returns:
            tuple: (SearchResponse, was_cached: bool)
        """
        # Try cache first
        cached_response = await self.cache.get_search_results(req)

        if cached_response:
            logger.info("Search results served from cache for route %s -> %s",
                        req.from_, req.to)
            return cached_response, True

        # Cache miss, fetch from API
        logger.info("Cache miss, fetching search results from API for route %s -> %s",
                    req.from_, req.to)

        response = await self.client.get_search_results(req)

        # Cache the response
        cache_success = await self.cache.set_search_results(req, response)
        if cache_success:
            logger.debug("Successfully cached search results for route %s -> %s",
                         req.from_, req.to)
        else:
            logger.warning("Failed to cache search results for route %s -> %s",
                           req.from_, req.to)

        return response, False

    async def get_schedule(self, req: ScheduleRequest) -> tuple[ScheduleResponse, bool]:
        """Get schedule results with caching.
        
        Returns:
            tuple: (ScheduleResponse, was_cached: bool)
        """
        # Try cache first
        cached_response = await self.cache.get_schedule_results(req)

        if cached_response:
            logger.info("Schedule results served from cache for station %s", req.station)
            return cached_response, True

        # Cache miss, fetch from API
        logger.info("Cache miss, fetching schedule from API for station %s", req.station)

        try:
            response = await self.client.get_schedule(req)
        except Exception as e:
            logger.error("Failed to fetch schedule from API for station %s: %s (%s)", 
                        req.station, str(e) or "No error message", type(e).__name__)
            import traceback
            logger.error("Full traceback: %s", traceback.format_exc())
            # Re-raise the exception to be handled by the caller
            raise

        # Cache the response only if it's valid
        if response and response.schedule:
            cache_success = await self.cache.set_schedule_results(req, response)
            if cache_success:
                logger.debug("Successfully cached schedule for station %s", req.station)
            else:
                logger.warning("Failed to cache schedule for station %s", req.station)
        else:
            logger.info("Not caching empty schedule response for station %s", req.station)

        return response, False

    async def get_schedule_for_dates(
        self,
        requests: list[ScheduleRequest]
    ) -> tuple[ScheduleResponse, list[bool], list[str]]:
        """Fetch and merge schedules for the provided requests in order.

        Args:
            requests: Ordered list of schedule requests (e.g., today, tomorrow).

        Returns:
            Tuple containing the merged schedule response, per-request cache flags,
            and the list of dates included in the response order.
        """
        if not requests:
            raise ValueError("At least one schedule request is required")

        responses: list[ScheduleResponse] = []
        cache_flags: list[bool] = []

        for request in requests:
            response, was_cached = await self.get_schedule(request)
            responses.append(response)
            cache_flags.append(was_cached)

        base_response = responses[0]

        if len(responses) == 1:
            source_dates = [resp_date for resp_date in [base_response.date] if resp_date]
            return base_response, cache_flags, source_dates

        combined_schedule = []
        for response in responses:
            combined_schedule.extend(response.schedule)

        total_items = len(combined_schedule)
        pagination = base_response.pagination.model_copy(update={
            "total": total_items
        })

        merged_response = base_response.model_copy(update={
            "schedule": combined_schedule,
            "pagination": pagination
        })

        seen_dates: set[str] = set()
        source_dates: list[str] = []
        for response in responses:
            if response.date and response.date not in seen_dates:
                seen_dates.add(response.date)
                source_dates.append(response.date)

        return merged_response, cache_flags, source_dates

    # Pass-through methods for other API calls (no caching needed for these)
    async def get_copyright(self):
        """Get copyright information (no caching)."""
        return await self.client.get_copyright()

    async def get_carrier(self, req):
        """Get carrier information (no caching)."""
        return await self.client.get_carrier(req)

    async def get_thread(self, req):
        """Get thread information (no caching)."""
        return await self.client.get_thread(req)

    async def get_stations_list(self, req=None):
        """Get stations list (no caching - large dataset fetched once)."""
        return await self.client.get_stations_list(req)

    async def clear_cache(self, pattern: str = "*") -> int:
        """Clear cache entries."""
        return await self.cache.clear_cache(pattern)

    async def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        return await self.cache.get_cache_stats()
