# Implementation Summary: Ride Matching System

## Overview

This implementation adds a complete ride matching system to the ride-matcher-service Telegram bot, allowing users to find travel companions ("попутчики") who are taking the same train.

## Files Added

### 1. MongoDB Service
**File**: `services/mongodb/thread_matching_service.py`

- **ThreadMatchingService**: Main service class for thread matching operations
- **CandidateThread**: Model for storing thread information
- **UserSearchResults**: Model for user search results with TTL
- **ThreadMatch**: Model for matched users

Key features:
- MongoDB TTL index for automatic cleanup after 1 hour
- Indexes on `telegram_id` and `candidate_threads.thread_uid` for fast queries
- O(n) matching algorithm
- Full error handling and logging

### 2. Command Handlers

**File**: `app/telegram/handlers/commands/goto.py`
- `/goto` command: Search from base station to destination
- Finds trains within next 1 hour
- Stores results in MongoDB
- Shows matches to user

**File**: `app/telegram/handlers/commands/goback.py`
- `/goback` command: Search from destination back to base (reverse)
- Same functionality as `/goto` but reversed direction
- Allows matching users traveling opposite directions

**File**: `app/telegram/handlers/commands/cancelride.py`
- `/cancelride` command: Cancel active ride search
- Removes user's search results from MongoDB
- Prevents matches with cancelled users

### 3. Documentation

**File**: `docs/RIDE_MATCHING.md`
- Complete documentation of the ride matching system
- Flow diagrams and explanations
- MongoDB schema documentation
- Integration details

**File**: `docs/ride_matching_demo.py`
- Executable demonstration script
- Shows example scenarios
- Explains the matching algorithm
- Visual representation of the flow

## Files Modified

### 1. Messages
**File**: `app/telegram/messages.py`

Added Russian messages for:
- Search titles and status messages
- Error messages
- Match notifications
- Cancel confirmations
- Updated help command to include new commands

### 2. User Service
**File**: `services/database/user_service.py`

Enhanced `get_or_create_user()` to:
- Update `first_name` and `last_name` if they've changed
- Ensures user data stays current
- Already uses `telegram_id` as primary key

### 3. Dependencies
**File**: `requirements.txt`

Added:
- `motor` - Async MongoDB driver for Python

## Key Features Implemented

### 1. Time Window Filtering (1 hour)
```python
now = datetime.now(config.timezone)
end_time = now + timedelta(hours=1)
# Filter trains: now <= departure_dt <= end_time
```

### 2. MongoDB TTL (60 minutes)
```python
ttl = 60  # minutes (1 hour)
expires_at = now + timedelta(minutes=ttl)
# MongoDB automatically deletes expired documents
```

### 3. Matching Algorithm
```python
# Find all users with overlapping thread UIDs
matches = await collection.find({
    "candidate_threads.thread_uid": {"$in": list(user_threads)},
    "telegram_id": {"$ne": telegram_id}
})
```

### 4. Comprehensive Logging
Every operation logs:
- User identification (telegram_id, username)
- Command parameters
- Search results (count, cached status)
- Match results
- MongoDB operations
- Errors with stack traces

### 5. Caching Integration
Uses existing `CachedYandexSchedules` client:
```python
cached_client = CachedYandexSchedules()
search_response, was_cached = await cached_client.get_search_results(search_req)
```

## Usage Flow

1. **User Setup** (one-time):
   ```
   /setstations
   ```
   User configures base and destination stations

2. **Search for Rides**:
   ```
   /goto      # Base → Destination
   /goback    # Destination → Base
   ```
   - Bot searches Yandex API (cached)
   - Filters trains in next 1 hour
   - Stores results in MongoDB
   - Finds and displays matches

3. **Cancel Search**:
   ```
   /cancelride
   ```
   Removes user from matching pool

4. **Automatic Cleanup**:
   MongoDB TTL expires records after 1 hour

## Technical Details

### MongoDB Schema
```javascript
{
  telegram_id: 123456789,
  username: "user123",
  first_name: "Ivan",
  last_name: "Ivanov",
  from_station_code: "s9600731",
  to_station_code: "s9600891",
  from_station_title: "Podolsk",
  to_station_title: "Tsaritsyno",
  candidate_threads: [
    {
      thread_uid: "RU_723Y_...",
      departure_time: "2025-01-15T08:30:00+03:00",
      arrival_time: "2025-01-15T09:15:00+03:00",
      from_station_code: "s9600731",
      to_station_code: "s9600891",
      from_station_title: "Podolsk",
      to_station_title: "Tsaritsyno"
    }
  ],
  created_at: ISODate("..."),
  expires_at: ISODate("...")  // TTL index
}
```

### Indexes
- `telegram_id` - User lookups
- `candidate_threads.thread_uid` - Match queries
- `expires_at` (TTL) - Automatic expiration

### Error Handling
All commands have try-catch blocks:
```python
try:
    # Operation
    logger.info("Success: ...")
except Exception as e:
    logger.error("Error: %s", e, exc_info=True)
    await update.message.reply_text(get_message("ride_search_error"))
```

## Integration

The system integrates seamlessly with existing components:

- ✅ **Handler Registry**: Commands auto-discovered via existing pattern
- ✅ **User Service**: Uses `telegram_id` consistently
- ✅ **Cache Service**: Leverages existing Yandex API cache
- ✅ **Message System**: Uses localized Russian messages
- ✅ **Database**: PostgreSQL for users, MongoDB for thread matching

## Testing

Run the demonstration:
```bash
python docs/ride_matching_demo.py
```

Verify imports:
```bash
python -c "
from services.mongodb.thread_matching_service import ThreadMatchingService
from app.telegram.handlers.commands import goto, goback, cancelride
print('✓ All imports successful')
"
```

## Requirements Fulfilled

✅ "Go To and Go Back buttons" → `/goto` and `/goback` commands  
✅ Fetch AND cache search results → Uses `CachedYandexSchedules`  
✅ Matching algorithm → O(n) implementation in `find_matches()`  
✅ Store thread IDs → `CandidateThread` model with `thread_uid`  
✅ 1 hour window → `timedelta(hours=1)` filtering  
✅ MongoDB with TTL → 60 minutes TTL index  
✅ Search both directions → `goto` and `goback`  
✅ Match users on same thread → Query by `thread_uid`  
✅ Let users know → Match display in responses  
✅ Cancel command → `/cancelride` implemented  
✅ Comprehensive logging → All operations logged  
✅ Fetch by telegram_id → All queries use `telegram_id`  

## Next Steps

To deploy:

1. Ensure MongoDB connection string in environment:
   ```bash
   MONGODB_HOST=your-cluster.mongodb.net
   MONGODB_USER=your-user
   MONGODB_PASSWORD=your-password
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the bot:
   ```bash
   python main.py
   ```

The ride matching system will be immediately available to users via the new commands.
