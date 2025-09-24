# Caching Layer Documentation

This document describes the Redis-based caching layer implemented for the Yandex Schedules API.

## Overview

The caching layer provides automatic caching of API responses to minimize Yandex API calls and improve response times. It uses Redis with built-in TTL (Time To Live) expiration.

## Architecture

### Components

1. **`YandexSchedulesCache`** (`services/cache/redis_cache.py`)
   - Core cache manager using Redis
   - Handles cache key generation, storage, and retrieval
   - Uses Redis TTL for automatic expiration

2. **`CachedYandexSchedules`** (`services/yandex_schedules/cached_client.py`)
   - Wrapper around the original `YandexSchedules` client
   - Implements cache-first strategy
   - Transparent to the caller

### Cache Strategy

- **Cache First**: Always check cache before making API calls
- **Write Through**: Cache successful API responses immediately
- **TTL-based Expiration**: Uses Redis built-in expiration (no manual fields)
- **Error Handling**: Gracefully degrades when Redis is unavailable

## Configuration

Add these environment variables (or update `.env`):

```bash
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_USERNAME=  # optional
REDIS_PASSWORD=  # optional

# Cache TTL Settings
CACHE_TTL_SEARCH=3600    # 1 hour for search results
CACHE_TTL_SCHEDULE=1800  # 30 minutes for schedule results
```

## Usage

### Basic Usage

```python
from services.yandex_schedules.cached_client import CachedYandexSchedules
from services.yandex_schedules.models.schedule import ScheduleRequest

# Use exactly like the regular client
async with CachedYandexSchedules() as client:
    request = ScheduleRequest(
        station="s9600213",
        date="2024-01-01",
        result_timezone="Europe/Moscow"
    )
    
    # First call: fetches from API, caches result
    response = await client.get_schedule(request)
    
    # Second call: served from cache (if within TTL)
    response = await client.get_schedule(request)
```

### Telegram Bot Integration

The `/schedule` command automatically uses caching:

```
/schedule s9600213
```

The bot will indicate whether data came from cache or fresh API call.

## Cache Keys

Cache keys are generated using MD5 hashes of request parameters:

- **Schedule**: `schedule:<md5(request_params)>`
- **Search**: `search:<md5(request_params)>`

## Monitoring

### Cache Statistics

```python
from services.cache.redis_cache import get_cache

cache = get_cache()
stats = await cache.get_cache_stats()
print(stats)
```

### Logging

The system logs cache hits/misses at INFO level:

```
INFO: Schedule results served from cache for station s9600213
INFO: Cache miss, fetching schedule from API for station s9600213
```

## Cache Management

### Clear Cache

```python
# Clear all cache
await cache.clear_cache()

# Clear specific pattern
await cache.clear_cache("schedule:*")  # Only schedule entries
await cache.clear_cache("search:*")    # Only search entries
```

## Error Handling

The cache is designed to be resilient:

- **Redis Down**: Falls back to direct API calls
- **Cache Corruption**: Automatically removes bad entries
- **API Errors**: Does not cache failed responses
- **Network Issues**: Logs errors but continues operation

## Performance Considerations

### Memory Usage

- Each cached response is stored as JSON
- Typical schedule response: ~5-50KB
- Monitor Redis memory usage in production

### TTL Settings

- **Schedule TTL (30 min)**: Balances freshness with API savings
- **Search TTL (60 min)**: Search results change less frequently
- Adjust based on your usage patterns

### Redis Configuration

For production, consider:

```bash
# Redis persistence
save 900 1
save 300 10
save 60 10000

# Memory optimization
maxmemory 256mb
maxmemory-policy allkeys-lru
```

## Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   ```
   ERROR: Failed to connect to Redis: Error 111 connecting to localhost:6379
   ```
   - Check if Redis server is running
   - Verify Redis host/port configuration

2. **Cache Always Misses**
   - Check Redis memory limits
   - Verify TTL settings aren't too short
   - Look for request parameter variations

3. **High Memory Usage**
   - Reduce TTL values
   - Implement memory limits in Redis
   - Monitor cache statistics

### Debug Commands

```bash
# Check Redis status
redis-cli ping

# Monitor cache keys
redis-cli --scan --pattern "schedule:*" | head -10

# Check memory usage
redis-cli info memory
```

## Best Practices

1. **Monitor Cache Hit Rate**: Aim for >70% hit rate
2. **Set Appropriate TTLs**: Balance freshness vs performance
3. **Handle Redis Failures**: Always have fallback to direct API
4. **Regular Monitoring**: Watch Redis memory and performance
5. **Cache Invalidation**: Clear cache when data changes significantly

## Testing

The system includes comprehensive tests:

```bash
# Run cache tests
python /tmp/test_cache.py

# Run integration tests  
python /tmp/test_integration.py
```

Tests work even without Redis server (graceful degradation).