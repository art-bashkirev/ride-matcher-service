import asyncio
import json

from services.yandex_schedules.client import YandexSchedules
from services.yandex_schedules.models.schedule import ScheduleRequest
from services.yandex_schedules.models.search import SearchRequest
from services.yandex_schedules.models.thread import ThreadRequest
from config import get_config

# Let's try using Search and Schedule endpoints to get the latest thread UIDs
from_ = "s9600731"
to = "s9600891"
date = "2025-09-16"


async def main():
    # Get configuration from the centralized config module
    # This replaces direct environment variable access with a production-ready config system
    config = get_config()
    
    print("Using configuration:")
    print(f"  - Environment: {config.environment}")
    print(f"  - Timezone: {config.result_timezone}")
    print(f"  - Is Production: {config.is_production}")
    print(f"  - API Key configured: {'Yes' if config.yandex_schedules_api_key else 'No'}")
    print()
    
    search_request = SearchRequest(
        from_=from_,
        to=to,
        date=date,
        result_timezone=config.result_timezone,
        limit=300,
    )

    import random

    # Let's select a random Thread UID from the search results
    async with YandexSchedules(config.yandex_schedules_api_key) as client:
        search_resp = await client.get_search_results(search_request)
        with open("test_search_results.json", "w", encoding="utf-8") as f:
            f.write(search_resp.model_dump_json(indent=2))

        if not search_resp.segments:
            print("No segments found in search results.")
            return

        random_segment = random.choice(search_resp.segments)
        if not random_segment.thread or not random_segment.thread.uid:
            print("Selected segment has no thread UID.")
            return

        thread_uid = random_segment.thread.uid
        print(f"Selected Thread UID: {thread_uid}")

        # Finally, let's fetch the thread details using the Thread endpoint
        thread_request = ThreadRequest(
            uid=thread_uid,
            from_=from_,
            to=to,
            date=date,
        )
        thread_resp = await client.get_thread(thread_request)
        with open("thread_result.json", "w", encoding="utf-8") as f:
            f.write(thread_resp.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
