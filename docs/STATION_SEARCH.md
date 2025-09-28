# Station Search Flow Documentation

This document describes the planned station search functionality for the ride-matcher-service.

## Overview

**NOTE: MongoDB-based station search has been removed. This functionality will be reimplemented using PostgreSQL.**

The station search flow will allow users to:
1. **Fetch and store** all stations from Yandex API once
2. **Search stations** by name, city, or region
3. **Get schedules** directly from search results
4. **Navigate seamlessly** between search and schedule views

## Planned Architecture

### Components

1. **PostgreSQL Storage**: Flattened station data for efficient search
2. **Station Service**: Search and data management (TODO: Implement)
3. **Telegram Commands**: User interface (search_station command removed, will be re-added)
4. **Integration**: Seamless connection with existing schedule system

### Planned Data Flow

```
Yandex API → Station List → Flatten → PostgreSQL → Search → Schedule
     ↓            ↓           ↓          ↓        ↓        ↓
  Raw JSON   Hierarchical  Flat     Indexed   Results  Timetable
```

## PostgreSQL Schema (Planned)

### FlatStation Model (TODO)

```sql
-- TODO: Define PostgreSQL schema for stations
CREATE TABLE stations (
    id SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    yandex_code VARCHAR UNIQUE NOT NULL,
    -- TODO: Add other fields
);
```

## Implementation Status

- ❌ MongoDB storage: Removed
- ❌ Station service: Removed
- ❌ Telegram search command: Removed
- ❌ Telegram fetch command: Removed
- ✅ Schedule command: Available (uses Yandex API directly)
- ✅ Cache system: Available

## Next Steps

1. Implement PostgreSQL models and service
2. Add station search functionality
3. Re-add Telegram commands for station management

## PostgreSQL Schema (Planned)

### FlatStation Model (TODO)

```sql
-- TODO: Define PostgreSQL schema for stations
CREATE TABLE stations (
    id SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    yandex_code VARCHAR UNIQUE NOT NULL,
    -- TODO: Add other fields
);
```

## Implementation Status

- ❌ MongoDB storage: Removed
- ❌ Station service: Removed
- ❌ Telegram search command: Removed
- ❌ Telegram fetch command: Removed
- ✅ Schedule command: Available (uses Yandex API directly)
- ✅ Cache system: Available

## Future Implementation

When PostgreSQL station search is implemented:

### Planned Telegram Commands

### `/fetch_stations` (TODO)

**Purpose**: Admin command to populate the stations database

### `/search_station <query>` (TODO)

**Purpose**: Search for stations by name, city, or region

## Configuration (Future)

### Environment Variables (TODO)

PostgreSQL configuration will be added when implemented.

## Dependencies (Updated)

### Required Packages

```
pydantic>=2.0          # Data validation
telegram>=22.0         # Telegram bot framework
# PostgreSQL driver will be added when implemented
```

---

*This documentation covers the planned station search flow. MongoDB implementation has been removed and will be replaced with PostgreSQL.*