import asyncio
import os
import json
from datetime import datetime, time
import pytz
from typing import List, Dict, NamedTuple

# Assuming your ORM classes are in this structure
from services.yandex_schedules.client import YandexSchedules
from services.yandex_schedules.models.search import SearchRequest, SearchResponse
from services.yandex_schedules.models.search import SearchSegment

# --- Configuration & Setup ---

# IMPORTANT: Make sure your YANDEX_SCHEDULES_API_KEY is set as an environment variable
YANDEX_SCHEDULES_API_KEY = os.environ.get("YANDEX_SCHEDULES_API_KEY")
if not YANDEX_SCHEDULES_API_KEY:
    raise ValueError("YANDEX_SCHEDULES_API_KEY environment variable not set.")

RESULT_TIMEZONE_STR = "Europe/Moscow"
RESULT_TIMEZONE = pytz.timezone(RESULT_TIMEZONE_STR)

# Use today's date in the correct format for the API
# In production, this would be the date you are fetching the schedule for (e.g., tomorrow)
PROD_LIKE_DATE = datetime.now(RESULT_TIMEZONE).strftime('%Y-%m-%d')


# --- Data Structures for Our Application ---

class UserIntent(NamedTuple):
    """Represents a user actively looking for a ride."""
    user_id: str
    from_station_code: str
    to_station_code: str
    # We use time objects for clean, timezone-unaware comparisons within the same day
    arrive_by_start: time
    arrive_by_end: time

# --- Mock User Data (Simulating N users) ---
# Using real station codes for Podolsk, Silikatnaya, Shcherbinka, and Tsaritsyno
# This represents the `users` collection in your database.
MOCK_USER_INTENTS = [
    UserIntent(
        user_id="Anna (Podolsk)",
        from_station_code="s9600731", # Podolsk
        to_station_code="s9600891",   # Tsaritsyno
        arrive_by_start=time(8, 30),
        arrive_by_end=time(9, 0)
    ),
    UserIntent(
        user_id="Boris (Silikatnaya)",
        from_station_code="s9602273", # Silikatnaya
        to_station_code="s9600891",   # Tsaritsyno
        arrive_by_end=time(9, 0),
        arrive_by_start=time(8, 30)
    ),
    UserIntent(
        user_id="Charlie (Podolsk)",
        from_station_code="s9600731", # Podolsk
        to_station_code="s9600891",   # Tsaritsyno
        arrive_by_start=time(9, 15),
        arrive_by_end=time(10, 0)
    ),
    UserIntent(
        user_id="Diana (Shcherbinka)",
        from_station_code="s9600951", # Shcherbinka
        to_station_code="s9600891",   # Tsaritsyno
        arrive_by_start=time(8, 45),
        arrive_by_end=time(9, 15)
    ),
     UserIntent(
        user_id="Eva (Podolsk, late)",
        from_station_code="s9600731", # Podolsk
        to_station_code="s9600891",   # Tsaritsyno
        arrive_by_start=time(9, 15),
        arrive_by_end=time(10, 0)
    ),
]


# --- Core Logic Implementation ---

async def fetch_and_cache_schedules(client: YandexSchedules, intents: List[UserIntent]) -> Dict[str, SearchResponse]:
    """
    Simulates the overnight job. Fetches schedules for all unique routes required by active users.
    """
    print("--- 1. Starting Proactive Cache Fetch ---")
    cached_schedules = {}
    unique_routes = {(intent.from_station_code, intent.to_station_code) for intent in intents}

    for from_code, to_code in unique_routes:
        route_key = f"{from_code}_{to_code}"
        print(f"Fetching schedule for route: {route_key}...")
        request = SearchRequest(
            from_=from_code,
            to=to_code,
            date=PROD_LIKE_DATE,
            result_timezone=RESULT_TIMEZONE_STR,
            limit=300 # Get all trains for the day
        )
        cached_schedules[route_key] = await client.get_search_results(request)
    
    print("--- Cache fetch complete. ---\n")
    return cached_schedules


def find_candidate_trains(intent: UserIntent, cached_schedules: Dict[str, SearchResponse]) -> List[SearchSegment]:
    """
    Filters the cached schedule to find all trains that match a single user's time window.
    """
    route_key = f"{intent.from_station_code}_{intent.to_station_code}"
    full_schedule = cached_schedules.get(route_key)
    if not full_schedule or not full_schedule.segments:
        return []

    candidate_trains = []
    for segment in full_schedule.segments:
        # The API returns timezone-aware ISO 8601 strings. We need to parse them.
        arrival_dt = datetime.fromisoformat(segment.arrival)
        # Convert to a simple time object for comparison
        arrival_time = arrival_dt.astimezone(RESULT_TIMEZONE).time()

        if intent.arrive_by_start <= arrival_time <= intent.arrive_by_end:
            candidate_trains.append(segment)
            
    return candidate_trains


def find_matches(intents: List[UserIntent], cached_schedules: Dict[str, SearchResponse]) -> Dict[str, List[UserIntent]]:
    """
    The smart O(n) matching algorithm.
    Groups users by the unique ID (thread.uid) of the trains they can potentially take.
    """
    print("--- 2. Running Matching Algorithm ---")
    potential_matches: Dict[str, List[UserIntent]] = {}

    # O(n) pass: Iterate through each active user once
    for intent in intents:
        candidate_trains = find_candidate_trains(intent, cached_schedules)
        print(f"User '{intent.user_id}' has {len(candidate_trains)} candidate trains in their time window.")
        
        # Populate the dictionary with this user's possible trains
        for train in candidate_trains:
            if train.thread and train.thread.uid:
                uid = train.thread.uid
                # Use setdefault to initialize the list if the key is new
                potential_matches.setdefault(uid, []).append(intent)

    print("--- Match analysis complete. ---\n")
    
    # Filter for actual matches (groups of 2 or more)
    final_matches = {uid: users for uid, users in potential_matches.items() if len(users) >= 2}
    return final_matches


def present_results(matches: Dict[str, List[UserIntent]], cached_schedules: Dict[str, SearchResponse]):
    """
    Formats and prints the final match proposals.
    """
    print("--- 3. Final Match Proposals ---")
    if not matches:
        print("No matches found for any users.")
        return

    match_num = 1
    for uid, users in matches.items():
        print(f"\n--- Match #{match_num} (Train UID: {uid}) ---")
        print(f"Users Matched: {[user.user_id for user in users]}")

        # To propose the plan, we need to find the specific segment for each user on this train
        for user in users:
            route_key = f"{user.from_station_code}_{user.to_station_code}"
            full_schedule = cached_schedules[route_key]
            
            # Find the exact train segment that corresponds to this UID for this user's route
            matched_segment = next((s for s in full_schedule.segments if s.thread and s.thread.uid == uid), None)
            
            if matched_segment:
                departure_time = datetime.fromisoformat(matched_segment.departure).astimezone(RESULT_TIMEZONE).strftime('%H:%M')
                arrival_time = datetime.fromisoformat(matched_segment.arrival).astimezone(RESULT_TIMEZONE).strftime('%H:%M')
                print(f"  - Proposal for {user.user_id}: Depart at {departure_time}, Arrive at {arrival_time}")
        
        match_num += 1


async def main():
    """Main execution function."""
    async with YandexSchedules(YANDEX_SCHEDULES_API_KEY) as client:
        # Step 1: Simulate the overnight job fetching all necessary data
        cached_schedules = await fetch_and_cache_schedules(client, MOCK_USER_INTENTS)
        
        # Step 2: Run the matching algorithm on the active users using the cached data
        final_matches = find_matches(MOCK_USER_INTENTS, cached_schedules)

        # Step 3: Present the results in a human-readable format
        present_results(final_matches, cached_schedules)


if __name__ == "__main__":
    asyncio.run(main())