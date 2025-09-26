# Environment Variables Reference

This document provides a complete reference for all environment variables used in the ride-matcher-service project.

## Required Environment Variables

### API Keys

#### `YANDEX_SCHEDULES_API_KEY`
- **Required**: Yes
- **Type**: String
- **Description**: API key for Yandex Schedules service
- **Default**: None
- **Example**: `YANDEX_SCHEDULES_API_KEY=your_api_key_here`
- **How to get**: Register at https://tech.yandex.ru/rasp/

#### `TELEGRAM_BOT_TOKEN`
- **Required**: Yes (for Telegram bot functionality)
- **Type**: String  
- **Description**: Token for your Telegram bot
- **Default**: None
- **Example**: `TELEGRAM_BOT_TOKEN=123456:ABC-DEF_your_token_here`
- **How to get**: Create a bot with @BotFather on Telegram
- **Note**: If not provided, Telegram bot will be disabled

## Optional Environment Variables

### Application Configuration

#### `ENVIRONMENT`
- **Required**: No
- **Type**: String
- **Description**: Current environment (affects logging and behavior)
- **Default**: `development`
- **Valid values**: `production`, `prod`, `development`, `dev`
- **Example**: `ENVIRONMENT=production`

#### `LOG_LEVEL`
- **Required**: No
- **Type**: String
- **Description**: Logging level for application
- **Default**: `INFO`
- **Valid values**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Example**: `LOG_LEVEL=DEBUG`

#### `RESULT_TIMEZONE`
- **Required**: No
- **Type**: String
- **Description**: Timezone for displaying results
- **Default**: `Europe/Moscow`
- **Example**: `RESULT_TIMEZONE=America/New_York`
- **Valid values**: Any timezone from the [tz database](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

### HTTP Server Configuration

#### `HTTP_HOST`
- **Required**: No
- **Type**: String
- **Description**: Host address for HTTP server
- **Default**: `0.0.0.0`
- **Example**: `HTTP_HOST=127.0.0.1`

#### `HTTP_PORT`
- **Required**: No
- **Type**: Integer
- **Description**: Port for HTTP server (health checks and future endpoints)
- **Default**: `8000`
- **Example**: `HTTP_PORT=8080`

### Redis Configuration

#### `REDIS_HOST`
- **Required**: No
- **Type**: String
- **Description**: Redis server hostname
- **Default**: `localhost`
- **Example**: `REDIS_HOST=redis.example.com`

#### `REDIS_PORT`
- **Required**: No
- **Type**: Integer
- **Description**: Redis server port
- **Default**: `6379`
- **Example**: `REDIS_PORT=6380`

#### `REDIS_DB`
- **Required**: No
- **Type**: Integer
- **Description**: Redis database number
- **Default**: `0`
- **Example**: `REDIS_DB=1`

#### `REDIS_USERNAME`
- **Required**: No
- **Type**: String
- **Description**: Redis username for authentication
- **Default**: None
- **Example**: `REDIS_USERNAME=myuser`

#### `REDIS_PASSWORD`
- **Required**: No
- **Type**: String
- **Description**: Redis password for authentication
- **Default**: None
- **Example**: `REDIS_PASSWORD=mypassword`

### Cache Configuration

#### `CACHE_TTL_SEARCH`
- **Required**: No
- **Type**: Integer
- **Description**: Cache TTL for search results (in seconds)
- **Default**: `3600` (1 hour)
- **Example**: `CACHE_TTL_SEARCH=7200`

#### `CACHE_TTL_SCHEDULE`
- **Required**: No
- **Type**: Integer
- **Description**: Cache TTL for schedule results (in seconds)
- **Default**: `1800` (30 minutes)
- **Example**: `CACHE_TTL_SCHEDULE=3600`

#### `CACHE_READABLE_KEYS`
- **Required**: No
- **Type**: Boolean
- **Description**: Use human-readable cache keys instead of hashes
- **Default**: `false`
- **Example**: `CACHE_READABLE_KEYS=true`
- **Note**: Set to `true` for easier debugging, `false` for better performance

### MongoDB Configuration

#### `MONGODB_URL`
- **Required**: No
- **Type**: String
- **Description**: MongoDB connection URL
- **Default**: `mongodb://localhost:27017`
- **Example**: `MONGODB_URL=mongodb://user:pass@mongo.example.com:27017/dbname`

#### `MONGODB_DATABASE`
- **Required**: No
- **Type**: String
- **Description**: MongoDB database name
- **Default**: `ride_matcher`
- **Example**: `MONGODB_DATABASE=my_transport_db`

#### `MONGODB_STATIONS_COLLECTION`
- **Required**: No
- **Type**: String
- **Description**: MongoDB collection name for stations data
- **Default**: `stations`
- **Example**: `MONGODB_STATIONS_COLLECTION=transport_stations`

## Example .env File

```bash
# Required - API Keys
YANDEX_SCHEDULES_API_KEY=your_api_key_here
TELEGRAM_BOT_TOKEN=123456:ABC-DEF_your_token_here

# Optional - Application Configuration
ENVIRONMENT=development
LOG_LEVEL=DEBUG
RESULT_TIMEZONE=Europe/Moscow

# Optional - HTTP Server
HTTP_HOST=0.0.0.0
HTTP_PORT=8000

# Optional - Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
# REDIS_USERNAME=
# REDIS_PASSWORD=

# Optional - Cache Configuration
CACHE_TTL_SEARCH=3600
CACHE_TTL_SCHEDULE=1800
CACHE_READABLE_KEYS=false

# Optional - MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=ride_matcher
MONGODB_STATIONS_COLLECTION=stations
```

## Configuration Usage in Code

All environment variables are managed through the centralized configuration system in `config.settings`:

```python
from config.settings import get_config

config = get_config()
api_key = config.yandex_schedules_api_key
timezone = config.result_timezone
```

## Environment Variable Validation

- **Timezone validation**: The `RESULT_TIMEZONE` is validated against the pytz timezone database
- **Log level validation**: Invalid log levels default to `INFO`
- **Type conversion**: Pydantic automatically handles type conversion and validation

## Legacy Environment Variable Usage

Some legacy files still access environment variables directly:
- `services/yandex_schedules/client.py` - Uses `os.getenv("YANDEX_SCHEDULES_API_KEY")` as fallback
- `misc/main_stash.py` - Development/testing file with direct access

These should be migrated to use the centralized config system.

## Troubleshooting

### Common Issues

1. **Missing API Key**: Ensure `YANDEX_SCHEDULES_API_KEY` is set
2. **Invalid Timezone**: Check timezone name against [tz database list](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
3. **Redis Connection**: Verify Redis server is running and accessible
4. **MongoDB Connection**: Ensure MongoDB server is running and URL is correct

### Environment Loading Order

1. System environment variables
2. `.env` file in project root
3. Default values from `config/settings.py`

### Debugging Configuration

Enable debug logging to see configuration loading:

```bash
LOG_LEVEL=DEBUG python -m main
```

This will show which environment variables are loaded and their values (sensitive values are not logged).