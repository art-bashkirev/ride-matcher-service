import asyncio
import os
import json

from services.yandex_schedules.client import YandexSchedules
from services.yandex_schedules.models.schedule import ScheduleRequest
from services.yandex_schedules.models.search import SearchRequest

YANDEX_SCHEDULES_API_KEY = os.environ.get("YANDEX_SCHEDULES_API_KEY")
RESULT_TIMEZONE = os.environ.get("RESULT_TIMEZONE", "Europe/Moscow")


async def main():
    request = ScheduleRequest(
        station="s9600731",
        date="2025-09-16",
        result_timezone=RESULT_TIMEZONE
    )

    async with YandexSchedules(YANDEX_SCHEDULES_API_KEY) as client:
        resp = await client.get_schedule(request)
        with open("schedule_results.json", "w", encoding="utf-8") as f:
            f.write(resp.model_dump_json())


if __name__ == "__main__":
    asyncio.run(main())
