# Ride Matching System - Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          USER INITIATES SEARCH                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                          ┌───────────┴───────────┐
                          │   /goto  or  /goback  │
                          └───────────┬───────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          VALIDATE USER SETUP                                │
│  • Check user has base_station_code & destination_code set via /setstations│
│  • If not configured → Show error message                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       FETCH TRAIN SCHEDULES                                 │
│  • Create SearchRequest (from=base, to=dest OR reverse for /goback)        │
│  • Query CachedYandexSchedules (hits cache if available)                   │
│  • Get all trains for the route                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     FILTER TRAINS IN TIME WINDOW                            │
│  • now = current time                                                       │
│  • end_time = now + 2.5 hours (150 minutes)                                │
│  • Filter: now ≤ departure_time ≤ end_time                                 │
│  • Build list of CandidateThread objects                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STORE IN MONGODB WITH TTL                                │
│  • Collection: user_search_results                                          │
│  • Document contains:                                                       │
│    - telegram_id (indexed)                                                  │
│    - username, first_name, last_name                                        │
│    - from/to station codes and titles                                       │
│    - candidate_threads[] (each with thread_uid, times, stations)           │
│    - created_at, expires_at (TTL: 150 minutes)                             │
│  • Upsert: replaces existing search for this user                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FIND MATCHES                                        │
│  • Query: Find all users with candidate_threads.thread_uid in my threads   │
│  • Exclude current user (telegram_id != my_id)                             │
│  • Group results by thread_uid                                              │
│  • Return: Dict[thread_uid -> List[matched_users]]                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DISPLAY RESULTS TO USER                                │
│  • Show count of candidate trains found                                     │
│  • If matches exist:                                                        │
│    - For each matched thread:                                               │
│      • Show thread info (uid preview, departure time)                       │
│      • List matched users (name, route)                                     │
│  • If no matches:                                                           │
│    - "Пока попутчиков не найдено. Мы уведомим вас, когда кто-то найдется!" │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                          MATCHING ALGORITHM                                 │
└─────────────────────────────────────────────────────────────────────────────┘

User A searches:
├─ candidate_threads: [T1, T2, T3]
└─ Stored in MongoDB with TTL

User B searches:
├─ candidate_threads: [T2, T4, T5]
├─ Stored in MongoDB with TTL
└─ Query: Find users with threads in [T2, T4, T5]
    └─ MATCH: User A has T2
        └─ Result: User B sees "User A can ride T2 with you!"

User C searches:
├─ candidate_threads: [T2, T6]
├─ Stored in MongoDB with TTL
└─ Query: Find users with threads in [T2, T6]
    └─ MATCHES: User A has T2, User B has T2
        └─ Result: User C sees "User A & User B can ride T2 with you!"

Now when User A searches again:
└─ Query: Find users with threads in [T1, T2, T3]
    └─ MATCHES: User B has T2, User C has T2
        └─ Result: User A sees "User B & User C can ride T2 with you!"


┌─────────────────────────────────────────────────────────────────────────────┐
│                        CANCEL FLOW (/cancelride)                            │
└─────────────────────────────────────────────────────────────────────────────┘

User invokes /cancelride
    │
    ▼
Delete document from MongoDB
    │
    ├─ Success → "✅ Ваш поиск попутчиков отменен."
    └─ Not found → "У вас нет активных поисков попутчиков."

Effect: User no longer appears in other users' match results


┌─────────────────────────────────────────────────────────────────────────────┐
│                      AUTOMATIC TTL CLEANUP                                  │
└─────────────────────────────────────────────────────────────────────────────┘

t=0:     User searches → Document created with expires_at = t+150min
t=10min: User still in matching pool
t=30min: User still in matching pool
t=60min: User still in matching pool
t=90min: User still in matching pool
t=120min: User still in matching pool
t=150min: MongoDB TTL process automatically deletes document
t=151min: User no longer in matching pool (automatic cleanup)


┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA FLOW SUMMARY                                   │
└─────────────────────────────────────────────────────────────────────────────┘

Telegram Bot
    │
    ├─ Commands: /goto, /goback, /cancelride
    │
    ▼
Handler Functions (goto.py, goback.py, cancelride.py)
    │
    ├─ Read: UserService.get_user(telegram_id) → PostgreSQL
    ├─ Read: CachedYandexSchedules → Redis Cache → Yandex API
    │
    ▼
ThreadMatchingService
    │
    ├─ Write: store_search_results() → MongoDB
    ├─ Read: find_matches() → MongoDB
    └─ Delete: clear_search_results() → MongoDB
    │
    ▼
MongoDB: user_search_results collection
    │
    ├─ TTL Index on expires_at
    ├─ Index on telegram_id
    └─ Index on candidate_threads.thread_uid
```

## Key Points

1. **Time Window**: Searches only include trains departing in the next 2.5 hours
2. **TTL**: Search results automatically expire after 2.5 hours (150 minutes)
3. **Matching**: Users are matched when they have the same thread_uid in their candidate_threads
4. **Cross-Route**: Works even if users have different base/destination stations
5. **Bidirectional**: /goto and /goback create separate searches (different directions)
6. **Cancellation**: Users can remove themselves from the matching pool anytime
7. **Automatic**: No manual cleanup needed - MongoDB TTL handles it
8. **Logged**: Every operation is logged with user details and parameters
