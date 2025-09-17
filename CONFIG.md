# Configuration Module

This project uses a production-ready configuration system that centralizes environment variable management and provides type safety and validation.

## Features

- **Centralized Configuration**: All settings are managed in one place
- **Environment Variable Support**: Reads from environment variables with defaults
- **Type Safety**: Provides typed configuration objects
- **Validation**: Validates configuration values at startup
- **Production Ready**: Supports both development and production environments
- **Legacy Compatibility**: Provides backward-compatible functions

## Usage

### Basic Usage

```python
from config import get_config

# Get the configuration object
config = get_config()

# Access configuration values
api_key = config.yandex_schedules_api_key
timezone = config.result_timezone
is_prod = config.is_production
current_date = config.get_current_date()
```

### Legacy Compatibility

For backward compatibility, the module also provides individual getter functions:

```python
from config import get_yandex_api_key, get_result_timezone, get_timezone

api_key = get_yandex_api_key()
timezone_str = get_result_timezone()
timezone_obj = get_timezone()
```

## Environment Variables

### Required

- `YANDEX_SCHEDULES_API_KEY`: Your Yandex Schedules API key

### Optional

- `RESULT_TIMEZONE`: Timezone for results (default: "Europe/Moscow")
- `ENVIRONMENT`: Environment name (default: "development")

## Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your values:
   ```bash
   YANDEX_SCHEDULES_API_KEY=your_actual_api_key_here
   RESULT_TIMEZONE=Europe/Moscow
   ENVIRONMENT=production
   ```

3. Load environment variables (if using python-dotenv):
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

## Configuration Object

The `Config` class provides the following properties:

### Basic Properties
- `yandex_schedules_api_key`: The API key for Yandex Schedules
- `result_timezone`: Timezone string for API results
- `environment`: Current environment (development/production)

### Computed Properties
- `is_production`: True if running in production
- `is_development`: True if running in development
- `timezone`: PyTZ timezone object
- `get_current_date()`: Current date formatted for API usage

## Validation

The configuration module validates:
- Required environment variables are present
- Timezone strings are valid PyTZ timezones
- API key is not empty

If validation fails, a descriptive `ValueError` is raised with guidance on how to fix the issue.

## Testing

Run the configuration tests:

```bash
python test_config.py
```

This will test all scenarios including:
- Valid configuration
- Missing required variables
- Invalid timezones
- Default values
- Legacy compatibility functions