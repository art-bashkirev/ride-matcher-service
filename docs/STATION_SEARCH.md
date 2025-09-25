# Station Search Flow Documentation

This document describes the station search functionality implemented for the ride-matcher-service.

## Overview

The station search flow allows users to:
1. **Fetch and store** all stations from Yandex API once
2. **Search stations** by name, city, or region
3. **Get schedules** directly from search results
4. **Navigate seamlessly** between search and schedule views

## Architecture

### Components

1. **MongoDB Storage**: Flattened station data for efficient search
2. **Station Service**: Search and data management
3. **Telegram Commands**: User interface
4. **Integration**: Seamless connection with existing schedule system

### Data Flow

```
Yandex API → Station List → Flatten → MongoDB → Search → Schedule
     ↓            ↓           ↓          ↓        ↓        ↓
  Raw JSON   Hierarchical  Flat     Indexed   Results  Timetable
```

## MongoDB Schema

### FlatStation Model

```python
{
    # Core station data
    "title": "Moscow Yaroslavsky Terminal",
    "codes": {"yandex_code": "s2000006"},
    "station_type": "train_station", 
    "transport_type": "train",
    
    # Location
    "longitude": 37.6173,
    "latitude": 55.7558,
    "direction": "North",
    
    # Hierarchical context
    "settlement_title": "Moscow",
    "settlement_codes": {"yandex_code": "c213"},
    "region_title": "Moscow Region",  
    "region_codes": {"yandex_code": "r1"},
    "country_title": "Russia",
    "country_codes": {"yandex_code": "r225"},
    
    # Search optimization
    "search_text": "Moscow Yaroslavsky Terminal Moscow Moscow Region Russia North"
}
```

### Indexes

- **Text Index**: `search_text` for full-text search
- **Unique Index**: `codes.yandex_code` for fast lookups

## API Reference

### StationsService

```python
from services.database.stations_service import get_stations_service

service = get_stations_service()

# Fetch and store all stations (admin operation)
count = await service.flatten_and_store_stations(stations_response)

# Search stations
results = await service.search_stations("moscow airport", limit=10)

# Get station by code
station = await service.get_station_by_code("s9600213")

# Get statistics
total = await service.get_stations_count()
```

### Search Results

```python
# StationSearchResult
{
    "station": FlatStation(...),
    "relevance_score": 2.5  # Higher = more relevant
}
```

## Telegram Commands

### `/fetch_stations`

**Purpose**: Admin command to populate the stations database

**Usage**: `/fetch_stations`

**Response**: 
```
✅ Successfully fetched and stored stations!

📊 Statistics:
• Stations stored: 12,847
• Countries: 12
• Total regions: 157
• Total settlements: 3,421

You can now use /search_station to find stations!
```

### `/search_station <query>`

**Purpose**: Search for stations by name, city, or region

**Usage**: 
- `/search_station moscow`
- `/search_station domodedovo airport`
- `/search_station yaroslavsky`

**Response**:
```
🔍 Search results for: moscow

1. 🚆 Moscow Yaroslavsky Terminal (Moscow, Moscow Region)
   🆔 Code: s2000006
   📊 Relevance: 2.00

2. ✈️ Domodedovo Airport (Moscow, Moscow Region)  
   🆔 Code: s9600213
   📊 Relevance: 1.50

💡 Click a button below to get the schedule, or use /schedule s2000006 directly.
```

**Interactive Buttons**: Click any station to get its schedule immediately.

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=ride_matcher
MONGODB_STATIONS_COLLECTION=stations
```

### Settings

```python
# config/settings.py
mongodb_url: str = Field(default="mongodb://localhost:27017")
mongodb_database: str = Field(default="ride_matcher") 
mongodb_stations_collection: str = Field(default="stations")
```

## Search Features

### Full-Text Search

- **MongoDB Text Index**: Fast, relevance-scored search
- **Multi-field**: Searches station name, city, region, country
- **Language Support**: Handles Russian and English text
- **Fuzzy Matching**: Fallback for partial matches

### Search Strategies

1. **Primary**: MongoDB `$text` search with relevance scoring
2. **Fallback**: Regex pattern matching for partial text
3. **Scoring**: Higher scores for exact title matches

### Relevance Scoring

- **3.0**: Exact title match
- **2.0**: Title contains query
- **1.0**: Location/context contains query  
- **0.5**: Fuzzy/partial match

## Data Validation

### Station Title Validation

```python
# Empty titles are skipped during import
if not station.title or station.title.strip() == "":
    logger.warning("Skipping station with empty title: %s", station.codes.yandex_code)
    continue
```

### Coordinate Validation

```python
# Invalid coordinates set to None
longitude = float(station.longitude) if station.longitude and \
    str(station.longitude).replace('.', '').replace('-', '').isdigit() else None
```

## Performance Considerations

### MongoDB Optimization

- **Text Indexes**: Enable fast full-text search
- **Unique Constraints**: Prevent duplicate stations
- **Connection Pooling**: Motor handles connection reuse
- **Batch Operations**: Bulk insert for initial load

### Caching Strategy

- **Station Data**: Stored permanently in MongoDB (no TTL)
- **Search Results**: Not cached (fast enough from MongoDB)
- **Schedule Data**: Existing Redis cache system

### Memory Usage

- **Typical Station**: ~500-1000 bytes in MongoDB
- **Full Dataset**: ~10-20MB for all Russian stations
- **Search Response**: ~5-50KB depending on results

## Error Handling

### Graceful Degradation

```python
# MongoDB unavailable
if total_stations == 0:
    await update.message.reply_text(
        "❌ No stations data available.\n"
        "An administrator needs to run /fetch_stations first."
    )
```

### Connection Issues

- **MongoDB Down**: Clear error messages to users
- **API Failures**: Detailed logging for debugging
- **Timeout Handling**: Reasonable timeouts with retries

## Security Considerations

### Input Validation

- **Query Length**: Minimum 2 characters to prevent abuse
- **Rate Limiting**: Telegram bot handles rate limiting
- **Injection Prevention**: Pydantic model validation

### Access Control

- **Admin Commands**: `/fetch_stations` for administrators only
- **User Commands**: `/search_station` for all users
- **Data Exposure**: Only public station information

## Integration with Existing System

### Schedule Command

- **Seamless Integration**: Search results link to `/schedule <code>`
- **Callback Buttons**: Direct navigation from search to schedule
- **Consistent UX**: Same formatting and error handling

### Redis Cache

- **Fixed Connection Reuse**: No more connection per request
- **Global Singleton**: Proper connection management
- **Graceful Shutdown**: Clean disconnection support

## Monitoring and Maintenance

### Logging

```python
# Search operations
logger.info("Found %d stations for query: %s", len(results), query)

# Data operations  
logger.info("Stored %d stations in MongoDB", stored_count)

# Performance
logger.debug("Search completed in %dms", elapsed_time)
```

### Statistics

```python
# Get database statistics
service = get_stations_service()
total_stations = await service.get_stations_count()
```

### Maintenance Tasks

1. **Periodic Updates**: Re-run `/fetch_stations` monthly
2. **Index Maintenance**: MongoDB handles automatically
3. **Cleanup**: Remove old/invalid stations if needed

## Troubleshooting

### Common Issues

1. **"No stations data available"**
   - Run `/fetch_stations` to populate database
   - Check MongoDB connection

2. **Search returns no results**
   - Try shorter/different search terms
   - Check for typos in station names
   - Verify data was imported correctly

3. **MongoDB connection failed**
   - Check `MONGODB_URL` configuration
   - Ensure MongoDB server is running
   - Verify network connectivity

### Debug Commands

```bash
# Check MongoDB connection
python -c "from services.database.stations_service import get_stations_service; import asyncio; print(asyncio.run(get_stations_service().get_stations_count()))"

# Test station search
python -c "from services.database.stations_service import get_stations_service; import asyncio; results = asyncio.run(get_stations_service().search_stations('moscow')); print(f'Found {len(results)} results')"
```

## Future Enhancements

### Potential Improvements

1. **Geolocation Search**: Search by coordinates/distance
2. **Favorites**: User-specific station bookmarks  
3. **Recent Searches**: Quick access to previous queries
4. **Autocomplete**: Real-time search suggestions
5. **Multi-language**: Support for additional languages
6. **Analytics**: Track popular stations and search patterns

### API Extensions

1. **REST API**: HTTP endpoints for web interface
2. **GraphQL**: Flexible query interface
3. **WebSocket**: Real-time search suggestions
4. **Export**: Download station data in various formats

## Dependencies

### Required Packages

```
pymongo>=4.8.0         # MongoDB async driver (primary - replaces Motor)
motor>=3.7.1          # MongoDB async driver (legacy support)
pydantic>=2.0          # Data validation
telegram>=22.0         # Telegram bot framework
```

**Note**: This project has migrated from Motor to PyMongo's native async client (`AsyncMongoClient`) as PyMongo now provides official async support. Motor is kept for compatibility during transition.

### System Requirements

- **MongoDB**: 4.4+ recommended
- **Python**: 3.11+ required
- **Memory**: 512MB+ for full dataset
- **Storage**: 100MB+ for MongoDB data

---

*This documentation covers the complete station search flow implementation. For questions or issues, check the troubleshooting section or consult the system logs.*