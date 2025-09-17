# Ride Matcher Service

A service for matching ride requests with train schedules using the Yandex Schedules API.

## Configuration

This project uses Pydantic BaseSettings for configuration management.

### Quick Start

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your API key:
   ```bash
   YANDEX_SCHEDULES_API_KEY=your_api_key_here
   ```

3. Use the config in your code:
   ```python
   from config import get_config
   
   config = get_config()
   api_key = config.yandex_schedules_api_key
   timezone = config.result_timezone
   ```

### Environment Variables

- `YANDEX_SCHEDULES_API_KEY` (required): Your Yandex Schedules API key
- `RESULT_TIMEZONE` (optional): Timezone for results (default: "Europe/Moscow")  
- `ENVIRONMENT` (optional): Environment name (default: "development")

### Running

```bash
python main.py
```