#!/usr/bin/env python3
"""Script to populate MongoDB with stations from Yandex Schedules API."""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import get_config
from services.yandex_schedules.client import YandexSchedules
from services.mongodb.stations_service import get_stations_service


async def main():
    """Populate stations in MongoDB."""
    config = get_config()

    if not config.yandex_schedules_api_key:
        print("YANDEX_SCHEDULES_API_KEY not set")
        return

    print("Fetching stations list from Yandex API...")
    async with YandexSchedules(config.yandex_schedules_api_key) as client:
        try:
            stations_response = await client.get_stations_list()
            stations_data = stations_response.model_dump()
        except Exception as e:
            print(f"Failed to fetch stations: {e}")
            return

    print("Populating MongoDB...")
    service = get_stations_service()
    try:
        await service.populate_stations(stations_data)
        print("Stations populated successfully!")
    except Exception as e:
        print(f"Failed to populate stations: {e}")
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(main())
