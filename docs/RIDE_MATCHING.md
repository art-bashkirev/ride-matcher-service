# Ride Matching Flow Documentation

## Overview

The ride matching system allows users to find potential travel companions ("попутчики") who are taking the same train within a similar time window.

## Commands

### `/goto` - Search from Base to Destination
Searches for trains from the user's base station to destination station within the next 2.5 hours and finds other users who might take the same train.

### `/goback` - Search from Destination to Base
Searches for trains from the user's destination station back to base station (reverse direction) within the next 2.5 hours.

### `/cancelride` - Cancel Active Search
Cancels the user's active ride matching search and removes their candidate threads from the matching pool.

## How It Works

### 1. User Initiates Search

When a user runs `/goto` or `/goback`:

1. **Validate User Setup**: Check that the user has configured their base and destination stations via `/setstations`
2. **Show Loading Message**: Display "⏳ Ищу поезда и попутчиков..."
3. **Calculate Time Window**: Set the search window to the next 2.5 hours from now

### 2. Fetch Train Schedules

1. **Create Search Request**: Build a search request for the route (base → destination or vice versa)
2. **Query Yandex API**: Use the cached client to get search results (hits cache if available)
3. **Filter Trains**: Filter trains to only those departing within the 2.5-hour window

### 3. Store Candidate Threads

For each train found:

1. **Extract Thread Info**: Get the thread UID, departure time, arrival time
2. **Create CandidateThread**: Build a candidate thread object with all relevant information
3. **Store in MongoDB**: Save all candidate threads to MongoDB with:
   - User's telegram_id, username, first_name, last_name
   - From/To station codes and titles
   - List of candidate threads
   - TTL of 150 minutes (2.5 hours) for automatic expiration

### 4. Find Matches and Notify Existing Users

The matching algorithm:

1. **Query MongoDB**: Find all other users whose candidate threads share the same thread UID
2. **Build Match Map**: Create a dictionary mapping thread_uid → list of matched users
3. **Filter Results**: Only return threads where at least one other user is found
4. **Notify Existing Users**: When a new user stores their search results, find all existing users who have matching threads and send them a notification about the new match

### 5. Display Results

Show the user:
- How many candidate trains were found
- If matches exist:
  - Thread information (UID preview, departure time)
  - Matched users (name, route)
- If no matches:
  - "Пока попутчиков не найдено. Мы уведомим вас, когда кто-то найдется!"

## MongoDB Schema

### Collection: `user_search_results`

```javascript
{
  telegram_id: 123456789,           // User's Telegram ID (indexed)
  username: "user123",              // Telegram username
  first_name: "Ivan",               // User's first name
  last_name: "Ivanov",              // User's last name
  from_station_code: "s9600731",    // From station code
  to_station_code: "s9600891",      // To station code
  from_station_title: "Podolsk",    // From station title
  to_station_title: "Tsaritsyno",   // To station title
  candidate_threads: [              // List of candidate threads
    {
      thread_uid: "RU_723Y_...",    // Thread UID (indexed)
      departure_time: "2025-01-15T08:30:00+03:00",
      arrival_time: "2025-01-15T09:15:00+03:00",
      from_station_code: "s9600731",
      to_station_code: "s9600891",
      from_station_title: "Podolsk",
      to_station_title: "Tsaritsyno"
    },
    // ... more threads
  ],
  created_at: ISODate("2025-01-15T08:00:00Z"),
  expires_at: ISODate("2025-01-15T10:30:00Z")  // TTL index on this field
}
```

### Indexes

- `telegram_id` - For quick user lookups
- `candidate_threads.thread_uid` - For finding matches across users
- `expires_at` (TTL) - Automatic document expiration after 2.5 hours

## Matching Algorithm

The algorithm is O(n) where n is the number of active users:

1. **Store Phase**: When a user searches, their candidate threads are stored in MongoDB
2. **Match Phase**: Query for other documents that have overlapping thread UIDs
3. **Result Phase**: Return all users grouped by shared thread UID

### Example

User A searches `/goto` and has candidate threads: [T1, T2, T3]
User B searches `/goto` and has candidate threads: [T2, T4, T5]
User C searches `/goback` and has candidate threads: [T2, T6]

Result: All three users are matched on thread T2 because:
- They all have T2 in their candidate threads
- T2 represents the same physical train
- The system notifies all three that they may ride together

## Logging

All operations are logged comprehensively:

- User command invocations (telegram_id, username)
- Search parameters (from/to stations, time window)
- Cache hits/misses
- Number of candidate threads found
- Number of matches found
- MongoDB operations (store, query, delete)
- Errors with full stack traces

## Automatic Cleanup

MongoDB's TTL index automatically removes expired search results after 2.5 hours, ensuring:
- No stale data accumulates
- Storage is automatically managed
- Users see only current matches

## Integration with Existing System

The ride matching system integrates with:

- **User Service**: Fetches user data by telegram_id
- **Cached Client**: Uses existing Yandex Schedules cache
- **Message System**: Uses localized Russian messages
- **Handler Registry**: Auto-discovered via the existing registry pattern
