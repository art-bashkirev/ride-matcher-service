# Schedule and Ride Matching Feature Assessment

This document provides an assessment of the current ride-matcher-service functionality regarding:
1. Weekly/bi-weekly scheduling capabilities
2. Immediate/override ride matching functionality  
3. Past train display behavior in schedule views

## Current Architecture Overview

### User Data Model
The current `User` model (in `models/user.py`) stores:
- `telegram_id`: User's Telegram identifier
- `username`, `first_name`, `last_name`: User profile info
- `base_station_code/title`: User's home station
- `destination_code/title`: User's work/destination station
- `is_admin`: Admin privileges flag

### Ride Matching Flow
1. User invokes `/goto` (base → destination) or `/goback` (destination → base)
2. User provides desired arrival time window (e.g., "08:45" or "08:30-09:00")
3. System searches for trains matching the arrival window
4. Candidate trains are stored in MongoDB with a TTL
5. System matches users with overlapping train candidates
6. Both new user and existing matching users are notified

---

## Assessment 1: Weekly/Bi-Weekly Scheduling

### Current State
**No recurring schedule functionality exists.** 

Users must manually invoke `/goto` or `/goback` each time they want to find ride mates. There is no way to:
- Set a recurring commute schedule (e.g., "Monday-Friday at 08:30")
- Configure different schedules for different days
- Have the system automatically search for ride mates at scheduled times

### Implementation Possibility

Adding weekly/bi-weekly scheduling is **feasible** and would require:

#### Database Changes
```python
# New model: UserSchedule
class UserSchedule(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="schedules")
    
    # Schedule type
    schedule_type = fields.CharField(max_length=20)  # "weekly", "biweekly"
    
    # Day of week (0=Monday, 6=Sunday)
    day_of_week = fields.IntField()
    
    # Direction
    direction = fields.CharField(max_length=10)  # "forward", "reverse"
    
    # Arrival time window
    arrival_time_start = fields.TimeField()
    arrival_time_end = fields.TimeField()
    
    # For bi-weekly: which week (0 or 1)
    week_parity = fields.IntField(null=True)
    
    # Active status
    is_active = fields.BooleanField(default=True)
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
```

#### New Commands Required
- `/setschedule` - Set up recurring schedule
- `/viewschedule` - View configured schedules
- `/editschedule` - Modify existing schedules
- `/deleteschedule` - Remove schedules

#### Background Processing
A scheduled job (using `APScheduler` or similar) would need to:
1. Run periodically (e.g., every 30 minutes)
2. Check for users with schedules matching the current day/time
3. Automatically execute the ride search flow for those users
4. Store results and notify users of matches

### Estimated Effort
- **Database schema**: 2-4 hours
- **Telegram commands**: 4-8 hours
- **Background scheduler**: 4-6 hours
- **Testing and polish**: 4-8 hours
- **Total**: ~14-26 hours of development

---

## Assessment 2: Immediate/Override Ride Matching

### Current State
**Immediate ride matching is fully supported with grace period.**

The current `/goto` and `/goback` commands allow users to:
1. Specify any arrival time they want
2. Get matched with other users searching for the same trains
3. Change their search at any time by invoking the command again
4. **Find ride mates on trains they're already on** (within 30-minute grace period)

### Grace Period for "Already On Train" Scenarios

Users who are already on a recently departed train can still find ride mates on that same train. The system includes a **30-minute grace period** that allows:

- Searching for trains that departed up to 30 minutes ago
- Matching with other passengers on the same train
- Useful for users who boarded but want to find companions mid-journey

From `ride_intent.py`:
```python
# Grace period for trains that recently departed - allows users already on a train
# to still find ride mates on that same train
_PAST_DEPARTURE_GRACE_MINUTES = 30

# Only shift to next day if the entire window is before the grace threshold
grace_threshold = now - timedelta(minutes=_PAST_DEPARTURE_GRACE_MINUTES)
while end_dt < grace_threshold:
    start_dt += timedelta(days=1)
    end_dt += timedelta(days=1)
```

### How Override Works Today

When a user runs `/goto` or `/goback`:
1. Any existing search results for that user are **replaced** (upsert behavior)
2. The new arrival window is used for matching
3. Previous search is effectively "cancelled"

From `thread_matching_service.py`:
```python
# Upsert: replace existing search results for this user
await collection.replace_one(
    {"telegram_id": telegram_id}, 
    search_results.model_dump(), 
    upsert=True
)
```

### For Scheduled Rides (Future)

If weekly/bi-weekly scheduling is implemented, the override mechanism would be:

1. **Using existing commands**: Simply run `/goto` or `/goback` with the desired time
   - This already replaces any active search (scheduled or manual)
   - No additional development needed
   - Grace period ensures "already on train" scenarios are supported

2. **Quick override button** (optional enhancement):
   - Add inline keyboard buttons to scheduled notifications
   - "🚀 Search Now" - Immediately trigger with default time window
   - "⏰ Change Time" - Prompt for new arrival time

### Implementation for Override (if scheduling is added)
The existing `search_rides()` function handles all the logic. An override would simply call the same function with different parameters:

```python
# Example: Override handler
async def quick_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Immediately search using user's configured schedule parameters."""
    db_user = await UserService.get_user(telegram_id)
    schedule = await get_active_schedule(telegram_id)  # New function
    
    if schedule:
        # Use schedule's configured time window, but for today
        request = RideSearchRequest(
            profile=create_profile(db_user),
            intent=create_intent_from_schedule(schedule)
        )
        await search_rides(update, context, request)
```

---

## Assessment 3: Schedule Display - Past Trains

### Confirmed: Past Trains Are NOT Used for Ride Matching

The ride matching system only considers **future trains** that fall within the user's arrival window.

#### Evidence from `ride_search.py` (lines 160-165):
```python
# Only include trains where arrival is within the requested window
if not (
    request.intent.arrival_window_start
    <= arrival_dt  
    <= request.intent.arrival_window_end
):
    continue
```

The arrival window allows times within the **30-minute grace period** (see `ride_intent.py`):
```python
# Grace period allows users on recently departed trains to still find ride mates
_PAST_DEPARTURE_GRACE_MINUTES = 30

grace_threshold = now - timedelta(minutes=_PAST_DEPARTURE_GRACE_MINUTES)

# Only shift to next day if the entire window is before the grace threshold
while end_dt < grace_threshold:
    start_dt += timedelta(days=1)
    end_dt += timedelta(days=1)
```

This means:
- If a user searches for arrival at 08:30 and it's currently 08:45, the search proceeds for today
- Trains that departed within the last 30 minutes are included in matching
- The search only shifts to tomorrow if the entire window is more than 30 minutes in the past

#### Display Behavior

| Feature | Shows Past Trains | Used for Matching |
|---------|------------------|-------------------|
| `/schedule` command | **No** - filters to upcoming only | N/A (display only) |
| Route schedule previews | **Fallback only** - shows past if no upcoming | N/A (display only) |
| `/goto` / `/goback` ride search | **Within grace period** - includes trains departed ≤30 min ago | Yes |

### Schedule Command Filtering (utils.py)
```python
def filter_upcoming_departures(schedule, current_time=None):
    # Only returns trains where departure_dt > current_time
    if departure_dt > current_time:
        upcoming.append(item)
```

### Route Schedule Filtering (route_schedule.py)
```python
# 5-minute grace period for trains that just departed
grace_threshold = now_local - timedelta(minutes=_PAST_DEPARTURE_GRACE_MINUTES)
upcoming = [s for s in normalised if s.departure >= grace_threshold]

# Fallback: show past trains ONLY if no upcoming exist
return upcoming or normalised
```

**Note**: The fallback to past trains in route schedule is for display purposes only (helping users see "what they missed" if all trains have departed). This data is never used for ride matching.

---

## Summary

| Question | Answer |
|----------|--------|
| Can users set weekly/bi-weekly schedules? | **No** - Not currently implemented |
| Is it feasible to add? | **Yes** - Estimated 14-26 hours of development |
| Can users override to search immediately? | **Yes** - Already works via `/goto` or `/goback` |
| Can users find ride mates on a train they're already on? | **Yes** - 30-minute grace period for departed trains |
| Does schedule show past trains? | **Limited** - Only as fallback display, never for matching |
| Are past trains used for ride-matching? | **Within grace period** - Trains departed ≤30 min ago are included |

---

## Recommendations

1. **For weekly scheduling**: Consider implementing as a V2 feature with:
   - Simple database model for recurring schedules
   - Background job to trigger automatic searches
   - Inline keyboard for quick overrides

2. **For immediate override**: Already supported - document this in user-facing help

3. **For schedule display**: Consider adding a visual indicator to show which trains are "departing soon" vs "recently departed" (if the fallback is triggered)
