import asyncio
import os

from services.yandex_schedules.client import YandexSchedules

YANDEX_SCHEDULES_API_KEY = os.environ.get("YANDEX_SCHEDULES_API_KEY")

async def main():

    async with YandexSchedules(YANDEX_SCHEDULES_API_KEY) as client:
        resp = await client.get_stations_list()
        print(resp)


if __name__ == "__main__":
    asyncio.run(main())
