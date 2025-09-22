"""Schedule service abstraction layer."""
from typing import List, Optional
from datetime import date
from abc import ABC, abstractmethod

from services.yandex_schedules.client import YandexSchedules
from services.yandex_schedules.models.schedule import ScheduleRequest, ScheduleResponse
from services.yandex_schedules.models.search import SearchRequest, SearchResponse


class ScheduleServiceInterface(ABC):
    """Abstract interface for schedule services."""
    
    @abstractmethod
    async def get_station_schedule(self, station_id: str, date_str: Optional[str] = None) -> Optional[ScheduleResponse]:
        """Get schedule for a station on a specific date."""
        pass
    
    @abstractmethod
    async def search_routes(self, from_station: str, to_station: str, date_str: Optional[str] = None) -> Optional[SearchResponse]:
        """Search routes between two stations."""
        pass


class YandexScheduleService(ScheduleServiceInterface):
    """Yandex Schedules service implementation with normalization."""
    
    def __init__(self):
        self._client = None
    
    async def __aenter__(self):
        self._client = YandexSchedules()
        await self._client.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def get_station_schedule(self, station_id: str, date_str: Optional[str] = None) -> Optional[ScheduleResponse]:
        """Get normalized station schedule."""
        if not self._client:
            raise RuntimeError("Service not initialized. Use async context manager.")
            
        try:
            if not date_str:
                date_str = date.today().isoformat()
                
            request = ScheduleRequest(station=station_id, date=date_str)
            response = await self._client.get_schedule(request)
            
            # TODO: Add normalization logic here
            return response
            
        except Exception as e:
            # TODO: Add proper logging
            print(f"Error fetching schedule: {e}")
            return None
    
    async def search_routes(self, from_station: str, to_station: str, date_str: Optional[str] = None) -> Optional[SearchResponse]:
        """Get normalized search results."""
        if not self._client:
            raise RuntimeError("Service not initialized. Use async context manager.")
            
        try:
            if not date_str:
                date_str = date.today().isoformat()
                
            request = SearchRequest(from_=from_station, to=to_station, date=date_str)
            response = await self._client.get_search_results(request)
            
            # TODO: Add normalization logic here  
            return response
            
        except Exception as e:
            # TODO: Add proper logging
            print(f"Error searching routes: {e}")
            return None


# Factory function for creating schedule services
def create_schedule_service() -> ScheduleServiceInterface:
    """Create a schedule service instance."""
    return YandexScheduleService()