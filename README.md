# ride-matcher-service

Concurrent aiohttp API server + Telegram bot service.

## Components

* `ApiServerService` (aiohttp) with middleware + `/healthz` (includes uptime & request_id) and structured request
  logging.
* `TelegramBotService` wraps `python-telegram-bot` with clean async lifecycle (only starts if `TELEGRAM_BOT_TOKEN`
  present).

## Features

### AI Chat Bot Mode
The service includes an AI chat bot feature with admin-only access:

- **Admin Management**: Only users with `is_admin=true` in the database can use AI features
- **Global Flag**: AI mode can be enabled/disabled globally via Redis flag (no TTL)
- **NVIDIA AI Integration**: Uses NVIDIA's AI API for chat completions
- **Telegram Commands**:
  - `/ai <prompt>` - Chat with AI (admin only)
  - `/aimode [enable|disable|status]` - Manage AI mode (admin only)  
  - `/setadmin <telegram_id> <true|false>` - Grant/revoke admin privileges (admin only)

### Other Features
- Yandex Schedules API integration with caching
- User station preferences management
- Health check endpoint
- Structured logging with request IDs

## Running

Set environment variables as needed (create a `.env` file for local dev):

```env
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
LOG_LEVEL=DEBUG
HTTP_PORT=8000
```

Start the service:

```bash
python -m main
```

Health check:

```bash
curl http://localhost:8000/healthz
```

Graceful shutdown via Ctrl+C (SIGINT) or SIGTERM stops bot then API server.

## Structure

* `main.py` orchestrates startup & shutdown.
* `app/api/` modular API server: `service.py`, `routes/health.py`, `middleware/logging.py`.
* `app/api_server.py` deprecated shim.
* `app/telegram/` modular bot: `service.py`, `config.py`, `handlers/`.
* `app/telegram_bot.py` deprecated shim.
* `config/settings.py` Pydantic settings.
* `config/log_setup.py` basic logging config.

## Development

Install requirements:

```bash
pip install -r requirements.txt
```

Run with hot reload (optional suggestion – e.g. using `watchfiles`): add `watchfiles` to requirements and run:

```bash
watchfiles 'python main.py'
```

## Future ideas

* Add structured logging (JSON) for production.
* Add tests for handlers & lifecycle.
* Add more API endpoints.

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
- `NVIDIA_AI_API_KEY` (optional): NVIDIA AI API key for AI chat bot functionality
- `RESULT_TIMEZONE` (optional): Timezone for results (default: "Europe/Moscow")
- `ENVIRONMENT` (optional): Environment name (default: "development")
- `LOG_LEVEL` (optional): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) default: INFO
- `HTTP_HOST` / `HTTP_PORT` (optional): Host/port for health & future HTTP endpoints (defaults: 0.0.0.0:8000)
- `TELEGRAM_BOT_TOKEN` (optional): If provided, the Telegram bot will start; omitted disables bot
- `REDIS_HOST` / `REDIS_PORT` (optional): Redis connection for caching and AI flag storage (defaults: localhost:6379)
- `POSTGRESQL_URI` (optional): PostgreSQL database connection for user management

### Running (HTTP health + Telegram bot)

Run both services with a single command:

```bash
python main.py
```

The aiohttp health endpoint will be available at: `http://localhost:8000/healthz` (adjust port via `HTTP_PORT`).

If `TELEGRAM_BOT_TOKEN` is set in the environment, the bot will start polling concurrently; otherwise it is skipped.

Graceful shutdown: press Ctrl+C (SIGINT) and both the HTTP server and the bot polling loop will stop cleanly.

On startup you'll see a single consolidated line summarizing runtime config, e.g.:

```text
2025-09-18 20:00:00,123 | INFO | __main__ | Starting service | env=development | timezone=Europe/Moscow | log_level=DEBUG | http=0.0.0.0:8000 | bot=enabled
```

### Architecture

The entrypoint (`main.py`) is intentionally thin: it configures logging, logs environment context, and delegates
lifecycle management to `ServiceManager` (`app/runtime.py`). This keeps startup/shutdown logic isolated from business
code.

### Example `.env` snippet

```dotenv
ENVIRONMENT=development
LOG_LEVEL=DEBUG
HTTP_PORT=8080
TELEGRAM_BOT_TOKEN=123456:ABC-DEF_your_token_here
```

Remove or comment `TELEGRAM_BOT_TOKEN` to disable the bot locally.
