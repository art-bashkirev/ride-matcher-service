# Schedule Pagination Documentation

## Overview

The schedule command now supports pagination to handle large numbers of departures with intuitive navigation controls.

## Features

### 🔄 Automatic Pagination

- Results are automatically paginated to **10 departures per page**
- Only **future departures** are shown (past departures are filtered out)
- Page information is displayed in the header: `(Page X of Y)`

### 🎮 Navigation Controls

- **Next ▶️** button: Navigate to the next page
- **◀️ Previous** button: Navigate to the previous page
- **Page X/Y** indicator: Shows current page (non-clickable)
- Buttons automatically hide when not applicable (e.g., no "Previous" on first page)

## Usage

### Basic Command

```
/schedule s9600213
```

The bot will show:

1. First page of results (up to 10 departures)
2. Inline keyboard with navigation buttons (if multiple pages exist)
3. Station information and data source

### Navigation

- Click **Next ▶️** to go to the next page
- Click **◀️ Previous** to go to the previous page
- The page indicator shows your current position

## Example Flow

```
User: /schedule s9600213

Bot: 📅 Schedule for station s9600213 (Moscow Yaroslavsky) on 2024-01-01 (Page 1/3):

🚂 001A (Express to St. Petersburg)
🕒 Departs: 14:30 (Platform 1)
📍 Stops: Moscow - Tver - St. Petersburg

🚂 003B (Regional Service)
🕒 Departs: 15:00 (Platform 3)
...

[Page 1/3] [Next ▶️]

💾 Data from cache
🏛️ Station: Moscow Yaroslavsky (railway station)
```

Click "Next ▶️":

```
Bot: 📅 Schedule for station s9600213 (Moscow Yaroslavsky) on 2024-01-01 (Page 2/3):

🚂 011C (High-speed Express)
🕒 Departs: 18:30 (Platform 2)
...

[◀️ Previous] [Page 2/3] [Next ▶️]

💾 Data from cache
🏛️ Station: Moscow Yaroslavsky (railway station)
```

## Technical Details

### Pagination Logic

- **Per Page**: 10 items maximum
- **Page Calculation**: Automatic based on total filtered results
- **Page Bounds**: Pages are clamped to valid range (1 to total_pages)

### Callback Data Format

- Format: `schedule_page:{station_id}:{page_number}`
- Example: `schedule_page:s9600213:2`

### Future-Only Filtering

- Compares departure times with the configured result timezone
- Applies a configurable future window (default **8 hours**, via `SCHEDULE_FUTURE_WINDOW_HOURS`)
- Only shows departures that are inside this window
- Invalid times are excluded for safety

### Cross-Day Coverage

- After the local hour reaches `SCHEDULE_FETCH_NEXT_DAY_AFTER_HOUR` (default **22:00**), the bot fetches both today and tomorrow
- Results are merged and automatically tagged with a **“(next day)”** suffix when applicable
- The footer lists all source dates (e.g., `Combined dates: 2025-09-28, 2025-09-29`)

### Caching Integration

- Maintains existing caching behavior
- Shows data source transparency ("Cache" vs "Fresh API")
- Pagination works with cached data for performance

## Error Handling

- **Invalid station ID**: Shows format error message
- **No departures**: Shows "No departures found" message
- **API errors**: Shows generic error with retry suggestion
- **Invalid page**: Automatically clamps to valid page range

## Performance

- **Efficient**: Fetches large dataset once, paginates in memory
- **Cached**: Subsequent page requests use cached data when possible
- **Responsive**: Immediate page navigation without API delays